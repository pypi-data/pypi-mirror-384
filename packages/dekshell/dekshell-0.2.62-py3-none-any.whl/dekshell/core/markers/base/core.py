import os
import sys
from dektools.output import obj2str
from dektools.str import hex_random
from dektools.dict import MapChainContext
from dektools.typing import NoneType
from . import MarkerBase, TransformerMarker, ExitException, QuitContextException


class MarkerContext:
    def __init__(self, parent=None):
        self.variables = parent.variables.derive() if parent else MapChainContext()
        self.environ = parent.environ.derive() if parent else MapChainContext()
        self.variables_temp = set()

    def __str__(self):
        return obj2str(dict(variable=self.variables, environ=self.environ))

    def derive(self):
        return self.__class__(self)

    def variables_full(self):
        return self.variables.flat(dict(__inner_context__=self))

    def update_variables(self, context):
        self.variables.update(context)
        return self

    def remove_variable(self, name):
        if isinstance(name, str):
            self.variables.remove_item(name)
        else:
            for x in name:
                self.remove_variable(x)

    def add_variable(self, k, v):
        self.variables.add_item(k, v)

    def add_variable_temp(self, value):
        while True:
            name = f'_temp_var_{hex_random(16)}'
            if name not in self.variables:
                break
        self.add_variable(name, value)
        self.variables_temp.add(name)
        return name

    def clear_temp_variable(self):
        self.remove_variable(self.variables_temp)
        self.variables_temp.clear()

    def environ_full(self):
        environ = os.environ.copy()
        environ.update(self.environ.flat())
        return environ

    def get_env_full(self, name, default=None):
        empty = object()
        value = self.environ.get_item(name, empty)
        if value is not empty:
            return value
        return self.get_env(name, default)

    @staticmethod
    def get_env(name, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def add_env(key, value):
        os.environ[key] = value

    @staticmethod
    def remove_env(key):
        os.environ.pop(key, None)


class HiddenVarSet:
    def __init__(self):
        self._data = {}

    def add_item(self, k, v):
        self._data[k] = v

    def remove_item(self, name):
        if isinstance(name, str):
            self._data.pop(name, None)
        else:
            for x in name:
                self.remove_item(x)

    def get_item(self, name, default=None):
        return self._data.get(name, default)


class PlaceholderMarker(MarkerBase):
    tag_head = ""


class QuitContext:
    def __init__(self, context, value):
        self.context = context
        self.value = value

    @staticmethod
    def real(value):
        if isinstance(value, QuitContext):
            return value.value
        return value


class MarkerNode:
    def __init__(self, marker, command, index, parent=None, command_old=None, payload=None):
        self.marker = marker
        self.command = command
        self.command_old = command_old
        self.index = index
        self.parent = parent
        self.children = []
        self.payload = payload

    def __repr__(self):
        return f'Node({self.marker.__class__.__name__},line={self.line_number})'

    @property
    def text_content(self):
        return self.marker.text_content(self.command)

    @property
    def debug_info(self):
        def walk(node):
            return dict(
                marker=node.marker,
                command=node.command,
                index=node.index,
                children=[walk(child) for child in node.children]
            )

        return obj2str(walk(self))

    @property
    def ignore_stack_check(self):
        def walk(node):
            if not node.marker.stack_check:
                return node
            for child in node.children:
                r = walk(child)
                if r:
                    return r

        return walk(self)

    def is_type(self, *markers_cls):
        return isinstance(self.marker, markers_cls)

    def add_child(self, node):
        node.parent = self
        self.children.append(node)
        return node

    def bubble_continue(self, context, marker_set, node):
        cursor = self
        while cursor:
            # result is (x, [y]) -->  x: Depth of the location, [y]: Insert to loop
            result = cursor.marker.bubble_continue(context, marker_set, cursor, node)
            if result is None:
                cursor = cursor.parent
            else:
                return result
        return None

    @classmethod
    def execute_nodes(cls, context, marker_set, nodes):
        __inner_marker_set__ = marker_set  # noqa
        context_final = None
        while nodes:
            node = nodes.pop(0)
            result = node.bubble_continue(context, marker_set, node)
            if result is not None:
                return result, context
            else:
                try:
                    changes = node.marker.execute(
                        context,
                        node.marker.translate(context, node.command or ''),
                        node, marker_set
                    )
                except QuitContextException as e:
                    return QuitContext(context, e.args[0]), context
                except ExitException:
                    raise
                except Exception as e:
                    sys.stderr.write(f"Execute error {node.marker}:\n\
                    command=> {node.command if node.command_old is None else node.command_old}\n\
                    lineno=> {node.line_number}\n\
                    context=>\n\
                    {context}")
                    raise e from None
                finally:
                    context.clear_temp_variable()
                context_ = context
                nodes_ = None
                callback = None
                if isinstance(changes, dict):
                    context_ = context.derive().update_variables(changes)
                elif isinstance(changes, list):
                    nodes_ = changes
                elif callable(changes):
                    callback = changes
                elif isinstance(changes, tuple):
                    if len(changes) == 1:
                        variables = changes[0]
                    elif len(changes) == 2:
                        variables, nodes_ = changes
                    elif len(changes) == 3:
                        variables, nodes_, callback = changes
                    else:
                        raise TypeError(f"Unknown type of changes: {changes}")
                    if variables is not None:
                        context_ = context.derive().update_variables(variables)
                elif changes is not None:
                    raise TypeError(f"Unknown type of changes: {changes}")
                context_final = context_
                if nodes_ is None:
                    nodes_ = node.children[:]
                result, _ = cls.execute_nodes(
                    context_,
                    marker_set,
                    nodes_
                )
                if isinstance(result, tuple):
                    node_cursor, node_loop_list = result
                    if node is node_cursor:  # Depth of the location
                        nodes[:0] = node_loop_list
                    else:
                        return result, context_
                elif isinstance(result, QuitContext):
                    if result.context is context:
                        return result, context_
                    else:
                        if callback:
                            callback(result)
        if context_final is None:
            context_final = context
        return None, context_final

    def execute(self, context, marker_set):
        result, context = self.execute_nodes(context, marker_set, [self])
        return QuitContext.real(result), context

    def walk(self, cb, depth=0):
        cb(self, depth)
        for child in self.children:
            child.walk(cb, depth + 1)

    @classmethod
    def root(cls, children=None):
        ins = cls(PlaceholderMarker(), None, None)
        if children:
            ins.children = children
        return ins

    @property
    def line_number(self):
        if self.index is None:
            return None
        return self.index + 1


class ShellResult:
    def __init__(self, marker_set: 'MarkerSet', root: MarkerNode, context: MarkerContext, result):
        self.marker_set = marker_set
        self.root = root
        self.context = context
        self.result = result


class MarkerSet:
    node_cls = MarkerNode
    context_cls = MarkerContext
    transformer_cls = TransformerMarker
    hidden_var_set_cls = HiddenVarSet
    shell_result_cls = ShellResult

    def __init__(self, markers_cls, shell_exec, shell_cmd):
        markers = []
        self.markers_branch_set = set()
        for marker_cls in markers_cls:
            markers.append(marker_cls())
            for branch_cls in marker_cls.final_branch_set:
                self.markers_branch_set.add(branch_cls)
        self.vars = self.hidden_var_set_cls()
        self.markers = self.transformer_cls.inject(markers)
        self.shell_exec = shell_exec
        self.shell_cmd = shell_cmd
        self.stack_errors = {}

    def check_stack_error(self, node):
        error = self.stack_errors.get(node.index)
        if error:
            raise error

    def is_marker_branch(self, marker):
        return marker.__class__ in self.markers_branch_set

    def find_marker_by_cls(self, marker_cls):
        for marker in self.markers:
            if isinstance(marker, marker_cls):
                return marker

    def find_marker_by_command(self, command):
        for marker in self.markers:
            if marker.recognize(command):
                return marker

    def generate_tree(self, commands, ln=None):
        stack = [self.node_cls.root()]
        for index, command in enumerate(commands):
            marker = self.find_marker_by_command(command)
            while isinstance(marker, stack[-1].marker.tag_tail or NoneType):
                node_tail = stack.pop()
                if not self.is_marker_branch(node_tail.marker):
                    break
            parent = stack[-1]
            marker = marker.transform(parent.marker)
            offset = 0
            if ln:
                for i, c in ln.items():
                    if index > i:
                        offset += c
                    else:
                        break
            node = self.node_cls(marker, command, index + offset)
            parent.add_child(node)
            if marker.tag_tail is not None:  # block command
                stack.append(node)
        if len(stack) != 1:
            node = stack[0].ignore_stack_check
            error = ValueError(
                f'Stack should have just one root node in final, your scripts contains syntax errors: {stack}')
            if node:
                print(error)
                self.stack_errors[node.index] = error
            else:
                raise error
        return stack[0]

    def execute(self, commands, context, ln=None):
        try:
            root = self.generate_tree(commands, ln)
            result, context = root.execute(
                self.context_cls().update_variables({**(context or {}), **dict(__inner_marker_set__=self)}), self)
            return self.shell_result_cls(self, root, context, result)
        except ExitException:
            pass
