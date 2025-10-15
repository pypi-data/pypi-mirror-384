import re
from .base import MarkerBase, MarkerWithEnd, MarkerNoTranslator, cmd_call_prefix_simple, cmd_call_prefix_chain, \
    cmd_call_eval_prefix, cmd_call_eval_trans_prefix
from .function import CallMarker
from .shell import TimeoutMarker, RetryMarker
from .invoke import MarkerInvokerBase, InvokeMarker, GotoMarker, ImportMarker


class MarkerAssignBase(MarkerBase):
    tag_head_re = r"[^\W\d]\w*[ \t\f\r]*%s"

    def get_vr(self, command):
        command = command.lstrip()
        index = re.match(self.tag_head_re % '', command).span()[1]
        var_name = command[:index].rstrip()
        rest = command[index:]
        index = re.match(self.tag_head_re_args, rest).span()[1]
        return var_name, rest[index:].strip()


class MarkerAssignValueBase(MarkerAssignBase):
    def execute(self, context, command, marker_node, marker_set):
        var_name, rest = self.get_vr(command)
        return self.assign_value(context, marker_node, marker_set, var_name, rest)

    def assign_value(self, context, marker_node, marker_set, var_name, expression):
        self.set_var_raw(context, var_name, self.get_value(context, marker_node, marker_set, expression))

    def get_value(self, context, marker_node, marker_set, expression):
        pass


class AssignUnpackMarker(MarkerAssignBase):
    tag_head_re_args = ','

    def execute(self, context, command, marker_node, marker_set):
        var_names = []
        cursor = command
        while True:
            var_name, rest = self.get_vr(cursor)
            var_names.append(var_name)
            marker = marker_set.find_marker_by_command(rest)
            if isinstance(marker, MarkerAssignBase):
                if not isinstance(marker, AssignUnpackMarker):
                    var_name_final = marker.get_vr(rest)[0]
                    var_names.append(var_name_final)
                    node = marker_set.node_cls(marker, rest, marker_node.index)
                    marker.execute(context, rest, node, marker_set)
                    value = self.eval(context, var_name_final)
                    if len(var_names) != len(value):
                        raise ValueError(f'Wrong values to unpack (expected {len(var_names)}, got {len(value)})')
                    for i, name in enumerate(var_names):
                        self.set_var_raw(context, name, value[i])
                    break
                cursor = rest
            else:
                raise ValueError('Need a assignable expression')


class AssignStrMarker(MarkerAssignValueBase):
    tag_head_re_args = ':'

    def get_value(self, context, marker_node, marker_set, expression):
        return expression


class AssignRawStrMarker(AssignStrMarker, MarkerNoTranslator):
    tag_head_re_args = re.escape(r'\:')


class AssignMultiLineStrMarker(MarkerAssignBase, MarkerWithEnd):
    tag_head_re_args = '::'
    _translate_type = None

    def execute(self, context, command, marker_node, marker_set):
        text = self.get_inner_content(context, marker_node, translate=self._translate_type)
        var_name = command[:re.search(self.tag_head_re_args, command).span()[0]]
        self.set_var_raw(context, var_name.strip(), text)
        return []


class AssignMultiLineRawStrMarker(AssignMultiLineStrMarker, MarkerNoTranslator):
    tag_head_re_args = re.escape(r'\::')
    _translate_type = False


class AssignEvalMarker(MarkerAssignValueBase, MarkerNoTranslator):
    tag_head_re_args = cmd_call_eval_prefix

    def get_value(self, context, marker_node, marker_set, expression):
        return self.eval(context, expression)


class AssignTranslatorEvalMarker(MarkerAssignValueBase):
    tag_head_re_args = cmd_call_eval_trans_prefix

    def get_value(self, context, marker_node, marker_set, expression):
        return self.eval(context, expression)


class AssignExecMarker(MarkerAssignBase, MarkerWithEnd, MarkerNoTranslator):
    tag_head_re_args = cmd_call_eval_prefix * 2

    def execute(self, context, command, marker_node, marker_set):
        code = self.get_inner_content(context, marker_node, translate=False, code=True)
        result = self.eval_codes(context, code)
        args = self.split_raw(command, 1, self.tag_head_re_args)
        self.set_var(context, args, 0, result)
        return []


class MarkerAssignValueParseExprBase(MarkerAssignValueBase):
    tag_head_re_args_raw = None

    def get_value(self, context, marker_node, marker_set, expression):
        return self.parse_expression(context, self.tag_head_re_args_raw + expression, False, False)


class AssignCommandRcSilenceMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_command_rc_silence
    tag_head_re_args = re.escape(MarkerBase.trans_marker_command_rc_silence)


class AssignCommandRcMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_command_rc
    tag_head_re_args = re.escape(MarkerBase.trans_marker_command_rc)


class AssignCommandOutputMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_command_output
    tag_head_re_args = re.escape(MarkerBase.trans_marker_command_output)


class AssignDecodeMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_decode
    tag_head_re_args = re.escape(MarkerBase.trans_marker_decode)


class AssignEncodeMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_encode
    tag_head_re_args = re.escape(MarkerBase.trans_marker_encode)


class AssignEnvMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_env
    tag_head_re_args = re.escape(MarkerBase.trans_marker_env)


class AssignEnvFullMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = MarkerBase.trans_marker_env_full
    tag_head_re_args = re.escape(MarkerBase.trans_marker_env_full)


class AssignCmdcallMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = cmd_call_prefix_simple
    tag_head_re_args = re.escape(tag_head_re_args_raw)


class AssignCmdcallChainMarker(MarkerAssignValueParseExprBase):
    tag_head_re_args_raw = cmd_call_prefix_chain + cmd_call_prefix_simple
    tag_head_re_args = re.escape(tag_head_re_args_raw)


class AssignCallMarker(MarkerAssignValueBase, CallMarker):
    tag_head = None
    tag_head_re_args = r'call[ \t\f\r\n]+'

    def assign_value(self, context, marker_node, marker_set, var_name, expression):
        def callback(value):
            self.set_var_raw(context, var_name, self.real_return_value(value))

        return *self.execute_core(context, expression), callback


class AssignMarkerInvokerBase(MarkerAssignValueBase, MarkerInvokerBase):
    tag_head = None

    def assign_value(self, context, marker_node, marker_set, var_name, expression):
        self.set_var_raw(context, var_name, self.execute_core(context, marker_set, expression))


class AssignInvokerMarker(AssignMarkerInvokerBase, InvokeMarker):
    tag_head_re_args = r'invoke[ \t\f\r\n]+'


class AssignGotoMarker(AssignMarkerInvokerBase, GotoMarker):
    tag_head_re_args = r'goto[ \t\f\r\n]+'


class AssignImportMarker(AssignMarkerInvokerBase, ImportMarker):
    tag_head_re_args = r'import[ \t\f\r\n]+'


class AssignTimeoutMarker(MarkerAssignValueBase, TimeoutMarker):
    tag_head = None
    tag_head_re_args = r'timeout[ \t\f\r\n]+'

    def get_value(self, context, marker_node, marker_set, expression):
        timeout, expression = self.split_raw(expression, 1)
        return self.execute_core_timeout(context, expression, marker_node, marker_set, timeout)


class AssignRetryMarker(MarkerAssignValueBase, RetryMarker):
    tag_head = None
    tag_head_re_args = r'retry[ \t\f\r\n]+'

    def get_value(self, context, marker_node, marker_set, expression):
        times, expression = self.split_raw(expression, 1)
        return self.execute_core_retry(context, expression, marker_node, marker_set, times)


class DelVarMarker(MarkerBase):
    tag_head = "del"

    def execute(self, context, command, marker_node, marker_set):
        name = self.split_raw(command, 1, self.tag_head)[-1]
        if name:
            context.remove_variable(name)
