import re
import functools
from dektools.str import deep_format, split_table_line, shlex_split, shlex_quote
from dektools.common import cached_classproperty
from dektools.shell import shell_output, shell_wrapper, shell_exitcode
from dektools.escape import str_escape_custom
from ....utils.serializer import serializer

cmd_call_prefix_simple = '>'
cmd_call_prefix = cmd_call_prefix_simple * 2
cmd_call_prefix_chain = '*'
cmd_call_eval_prefix = '='
cmd_call_eval_trans_prefix = cmd_call_eval_prefix + ':'
cmd_call_eval_escape = '\\'
cmd_call_sep = '--'


class MarkerBase:
    tag_head = None
    tag_head_args = None
    tag_head_re = None
    tag_head_re_args = None
    tag_tail = None
    stack_check = True
    branch_set = set()

    var_name_anonymous = '_'

    trans_marker_command_rc_silence = '<<<'
    trans_marker_command_rc = '<<'
    trans_marker_command_output = '<'
    trans_marker_decode = '//'
    trans_marker_encode = '/'
    trans_marker_env = '$$'
    trans_marker_env_full = '$'
    # trans_marker__set = '|'.join((re.escape(x) for x in [
    #     trans_marker_command_rc_silence,
    #     trans_marker_command_rc,
    #     trans_marker_command_output,
    #     trans_marker_decode,
    #     trans_marker_encode,
    #     trans_marker_env,
    #     trans_marker_env_full,
    # ]))
    trans_marker__as_var = '='
    trans_marker__ignore = '?'
    trans_marker__begin = "{"
    trans_marker__end = "}"
    trans_marker__escape = "\\"

    VALUE_UNSET = type('Unset', (), {})

    @classmethod
    def get_tag_match(cls):
        if cls.tag_head is not None:
            s = cls.tag_head if cls.tag_head_args is None else cls.tag_head % cls.tag_head_args
        else:
            s = None
        if cls.tag_head_re is not None:
            r = cls.tag_head_re if cls.tag_head_re_args is None else cls.tag_head_re % cls.tag_head_re_args
        else:
            r = None
        return s, r

    def recognize(self, command):
        command = self.strip(command)
        s, r = self.get_tag_match()
        if s is not None:
            if command.startswith(s):
                rule = re.compile('[0-9a-zA-Z_]')
                return not (s and rule.match(s[-1]) and rule.match(command[len(s):len(s) + 1]))
            return False
        elif r is not None:
            return bool(re.match(r, command))
        return False

    def text_content(self, command):
        return command

    def transform(self, parent):
        return self

    def bubble_continue(self, context, marker_set, marker_node_self, marker_node_target):
        return None

    def execute(self, context, command, marker_node, marker_set):
        pass

    def execute_result(self, result):
        pass

    def exit(self):
        raise ExitException()

    def ret(self, value):
        raise QuitContextException(value)

    def raise_(self, message):
        raise RaiseException(message)

    @classmethod
    def set_var(cls, context, array, index, value):
        cls.set_var_raw(context, cls.get_item(array, index, cls.var_name_anonymous), value)

    @staticmethod
    def set_var_raw(context, name, value):
        context.add_variable(name, value)

    @staticmethod
    def remove_var(context, name):
        context.remove_variable(name)

    @classmethod
    def cmd_call_split(cls, s, max_item=None):
        if max_item == 0:
            return [], s.lstrip()
        m = re.match(
            rf'''[ \t\f\r]*({cmd_call_prefix_simple}[{cmd_call_prefix_simple}]?)[ \t\f\r]*([^\W\d][\w.]*)'''
            , s)
        if not m:
            return [], s.lstrip()
        rest = s[m.span()[1]:]
        if max_item is not None:
            max_item -= 1
        items, body = cls.cmd_call_split(rest, max_item)
        items = [(m.group(2), m.group(1) == cmd_call_prefix_simple), *items]
        return items, body

    @classmethod
    def cmd_call_parse(cls, context, s, simple):
        s = s.lstrip()
        if simple:
            argv = re.split(r'[ \t\f\r]+', s, 1)
            args = argv[1:]
            kwargs = {}
        else:
            argv = cls.split(s)
            args, kwargs = cls.cmd2ak(argv[1:])
            args, kwargs = cls.cmd_trans_batch(context, *args, **kwargs)
        func = argv[0]
        return func, args, kwargs

    @classmethod
    def translate_case(cls, context, s, case=None):
        if case is None:
            return cls.translate(context, s)
        else:
            return cls._translate(context, s) if case else s

    @classmethod
    def translate(cls, context, s):
        return cls._translate(context, s)

    @classmethod
    def _translate(cls, context, s):
        def handler(expression, _, __):
            expression = expression.lstrip()
            as_var = False
            ignore_errors = False
            while True:
                change = 0
                if not as_var and expression.startswith(cls.trans_marker__as_var):
                    expression = expression[len(cls.trans_marker__as_var):].lstrip()
                    as_var = True
                    change += 1
                if not ignore_errors and expression.startswith(cls.trans_marker__ignore):
                    expression = expression[len(cls.trans_marker__ignore):].lstrip()
                    ignore_errors = True
                    change += 1
                if change in (0, 2):
                    break
            value = cls.parse_expression(context, expression, False, False, ignore_errors)
            if as_var:
                return context.add_variable_temp(value)
            return value

        return deep_format(
            s,
            # f"{re.escape(cls.trans_marker__begin)}({cls.trans_marker__set})?",
            f"{re.escape(cls.trans_marker__begin)}",
            re.escape(cls.trans_marker__end), handler, cls.trans_marker__escape)

    @classmethod
    def parse_expression(cls, context, expression, translate_eval=True, translate_others=True, ignore_errors=False):
        def evaluate(expr, default):
            try:
                return cls.eval_mixin(context, expr, translate_eval)
            except NameError:
                if ignore_errors:
                    return default
                else:
                    raise

        empty_value = object()
        default_value = ''

        if expression.startswith(cls.trans_marker_command_rc_silence):
            expression = expression[len(cls.trans_marker_command_rc_silence):]
            if translate_others:
                expression = cls.translate_case(context, expression, True)
            return shell_exitcode(expression, env=context.environ_full())
        elif expression.startswith(cls.trans_marker_command_rc):
            expression = expression[len(cls.trans_marker_command_rc):]
            if translate_others:
                expression = cls.translate_case(context, expression, True)
            return shell_wrapper(expression, check=False, env=context.environ_full())
        elif expression.startswith(cls.trans_marker_command_output):
            expression = expression[len(cls.trans_marker_command_output):]
            if translate_others:
                expression = cls.translate_case(context, expression, True)
            return shell_output(expression, env=context.environ_full())
        elif expression.startswith(cls.trans_marker_env):
            expression = expression[len(cls.trans_marker_env):]
            if translate_others:
                expression = cls.translate_case(context, expression, True)
            return context.get_env(expression.strip(), default_value)
        elif expression.startswith(cls.trans_marker_env_full):
            expression = expression[len(cls.trans_marker_env_full):]
            if translate_others:
                expression = cls.translate_case(context, expression, True)
            return context.get_env_full(expression.strip(), default_value)
        elif expression.startswith(cls.trans_marker_decode):
            expression = expression[len(cls.trans_marker_decode):]
            value = evaluate(expression, empty_value)
            if value is empty_value:
                return default_value
            return serializer.load(value)
        elif expression.startswith(cls.trans_marker_encode):
            expression = expression[len(cls.trans_marker_encode):]
            value = evaluate(expression, empty_value)
            if value is empty_value:
                return default_value
            return serializer.dump(value)
        else:
            return evaluate(expression, default_value)

    @cached_classproperty
    def final_branch_set(self):
        return {self if x is None else x for x in self.branch_set}

    @staticmethod
    def get_item(array, index, default=None):
        if array:
            try:
                return array[index]
            except IndexError:
                pass
        return default

    @staticmethod
    def strip(command):
        return command.strip()

    @staticmethod
    def split(command):
        return shlex_split(command)

    @staticmethod
    def split_raw(command, maxsplit=None, sep=None):
        return split_table_line(command, maxsplit, sep)

    @staticmethod
    def eval(context, s, v=None):
        if not s:
            return None
        return eval(s, {**context.variables_full(), **(v or {})})

    @classmethod
    def eval_mixin(cls, context, expression, translate=True):
        __inner_context__ = context  # noqa
        expression = expression.lstrip()
        if expression.startswith(cmd_call_prefix_chain):
            max_item = None
            expression = expression[len(cmd_call_prefix_chain):]
        else:
            max_item = 1
        if expression.startswith(cmd_call_prefix_simple):
            expression = cls.translate_case(context, expression, translate)
        funcs, body = cls.cmd_call_split(expression, max_item)
        if funcs:
            func, simple = funcs[-1]
            f = cls.eval(context, func)
            if simple:
                value = f(body)
            else:
                if body:
                    args, kwargs = cls.cmd2ak(cls.split(body))
                    args, kwargs = cls.cmd_trans_batch(context, *args, **kwargs)
                else:
                    args, kwargs = [], {}
                value = f(*args, **kwargs)
            for func, simple in reversed(funcs[:-1]):
                f = cls.eval(context, func)
                if simple:
                    value = f(value)
                else:
                    value = f(*value)
            return value
        else:
            if expression.startswith(cmd_call_eval_trans_prefix):
                expression = expression[len(cmd_call_eval_trans_prefix):]
                expression = cls.translate_case(context, expression, True)
            elif expression.startswith(cmd_call_eval_prefix):
                expression = expression[len(cmd_call_eval_prefix):]
            return cls.eval(context, expression)

    @staticmethod
    def eval_lines(context, s, v=None):
        globals_ = {**context.variables_full(), **(v or {})}
        locals_ = {}
        exec(s, globals_, locals_)
        return locals_

    @classmethod
    def cmd_trans(cls, context, s, trans_sep):
        if s.startswith(cmd_call_eval_prefix):
            return cls.eval(context, s[len(cmd_call_eval_prefix):])
        else:
            def skip(c, index):
                if trans_sep:
                    nonlocal sep_skip
                    if sep_skip:
                        return True
                    if c == cmd_call_sep:
                        if not re.fullmatch(r'[^\W\d]\w*', s[:index - len(cmd_call_eval_escape)]):
                            sep_skip = True
                            return True
                return False

            def process(mapping, index, x, y):
                if trans_sep:
                    if x == cmd_call_sep:
                        nonlocal sep_skip
                        sep_skip = True
                else:
                    nonlocal clear_eval
                    if not clear_eval and (x is None or x == cmd_call_eval_prefix):
                        clear_eval = True
                        mapping.pop(cmd_call_eval_prefix)

            clear_eval = False
            sep_skip = False
            targets = [cmd_call_eval_prefix]
            if trans_sep:
                targets.append(cmd_call_sep)
            return str_escape_custom(s, targets, cmd_call_eval_escape, keep=True, process=process, skip=skip)

    @classmethod
    def cmd_trans_batch(cls, context, *args, **kwargs):
        return (
            [cls.cmd_trans(context, x, True) for x in args],
            {k: cls.cmd_trans(context, v, False) for k, v in kwargs.items()}
        )

    @staticmethod
    def cmd2ak(argv):
        # arg0 =arg1-eval-value \=arg2 arg3\--not-kwarg
        # k0--v k1--=eval-value k2--\=v
        args = []
        kwargs = {}
        for x in argv:
            if re.match(r'[^\W\d]\w*' + cmd_call_sep, x):
                k, v = x.split(cmd_call_sep, 1)
                kwargs[k] = v
            else:
                args.append(x)
        return args, kwargs

    @staticmethod
    def ak2cmd(args=None, kwargs=None):
        result = []
        if args:
            for x in args:
                if isinstance(x, str):
                    m = re.match(r'[^\W\d]\w*' + cmd_call_sep, x)
                    if m:
                        index = m.span()[-1] - len(cmd_call_sep)
                        x = x[:index] + cmd_call_eval_escape + x[index:]
                else:
                    x = f"={repr(x)}"
                result.append(shlex_quote(x))
        if kwargs:
            for k, v in kwargs.items():
                if not isinstance(v, str):
                    v = f"={repr(v)}"
                result.append(shlex_quote(f'{k}--{v}'))
        return ' '.join(result)


class EndMarker(MarkerBase):
    tag_head = "end"


class BreakMarker(MarkerBase):
    tag_head = "break"


class ContinueMarker(MarkerBase):
    tag_head = "continue"


class TransformerMarker(MarkerBase):
    def __init__(self, targets):
        super().__init__()
        self.targets = targets

    def recognize(self, command):
        return self.targets[0].recognize(command)

    def transform(self, parent):
        for target in self.targets:
            if isinstance(target, tuple(parent.final_branch_set)):
                return target
        return self.targets[0]

    @classmethod
    def inject(cls, markers):
        records_markers = {}
        records_index = {}
        records_target = set()
        for i, marker in enumerate(markers):
            match = marker.get_tag_match()
            if match in records_markers:
                records_markers[match].append(marker)
            else:
                records_markers[match] = [marker]
            if len(records_markers[match]) > 1:
                records_target.add(match)
            if match not in records_index:
                records_index[match] = i
        offset = 0
        for match in sorted(records_target, key=lambda x: records_index[x]):
            index = records_index[match] + offset
            markers.insert(index, cls(records_markers[match]))
            offset += 1
        return markers


class MarkerWithEnd(MarkerBase):
    tag_tail = EndMarker

    def get_inner_content(self, context, marker_node, sep='\n', translate=None, code=False):
        def walk(node, depth):
            if depth != 0:
                commands.append(self.translate_case(context, node.text_content, translate))

        commands = []
        marker_node.walk(walk)
        if code:
            if commands:
                c = commands[0]
                cc = c.lstrip()
                tabs = c[:len(c) - len(cc)]
                result = []
                for index, line in enumerate(commands):
                    if not line.startswith(tabs) and line.lstrip():
                        raise ValueError(
                            f'Code block has indents error:\n'
                            f'translated-line=>{line}'
                            f'lineno=> {marker_node.line_number + index + 1}\n'
                        )
                    result.append(line[len(tabs):])
                commands = result
        return sep.join(commands)

    def eval_codes(self, context, code):
        if not code:
            return None
        codes = code.split('\n')
        codes[-1] = f"_ = {codes[-1]}"
        return self.eval_lines(context, '\n'.join(codes))['_']

    def find_node(self, marker_node_list, reverse=False, node_set=None):
        if node_set is None:
            node_set = self.final_branch_set
        if reverse:
            target = reversed(marker_node_list)
        else:
            target = marker_node_list
        index = None
        for i, child in enumerate(target):
            if reverse and child.is_type(self.tag_tail):
                break
            if child.is_type(*node_set):
                index = i
                break
        if index is not None and reverse:
            return len(marker_node_list) - 1 - index
        return index


class MarkerNoTranslator(MarkerBase):

    @classmethod
    def translate(cls, context, s):
        return s


class MarkerShellBase(MarkerBase):
    shell_cls = None

    def execute(self, context, command, marker_node, marker_set):
        command = self.strip(command)
        if command:
            self.execute_core(context, command, marker_node, marker_set)

    @classmethod
    def execute_core(cls, context, command, marker_node, marker_set, kwargs=None):
        kwargs = {**(marker_node.payload or {}), **(kwargs or {})}
        return marker_set.shell_cmd(command, cls.shell_cls(kwargs), env=context.environ_full())


class ExceptionShell(Exception):
    pass


class ExitException(ExceptionShell):
    pass


class QuitContextException(ExceptionShell):
    pass


class RaiseException(ExceptionShell):
    pass
