from .base import MarkerBase, MarkerWithEnd, MarkerNoTranslator, cmd_call_prefix_simple, \
    cmd_call_prefix_chain, cmd_call_eval_prefix, cmd_call_eval_trans_prefix
from .empty import EmptyMarker


class ExecMarker(MarkerNoTranslator):
    tag_head = cmd_call_eval_prefix

    def execute(self, context, command, marker_node, marker_set):
        args = self.split_raw(command, 1, self.tag_head)
        if args[1]:
            self.eval_lines(context, args[1])


class ExecTranslatorMarker(MarkerBase):
    tag_head = cmd_call_eval_trans_prefix

    def execute(self, context, command, marker_node, marker_set):
        args = self.split_raw(command, 1, self.tag_head)
        if args[1]:
            self.eval_lines(context, args[1])


class ExecLinesMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = cmd_call_eval_prefix * 2

    def execute(self, context, command, marker_node, marker_set):
        code = self.get_inner_content(context, marker_node, translate=False, code=True)
        self.eval_lines(context, code)
        return []


class ExecLinesTranslatorMarker(MarkerWithEnd):
    tag_head = cmd_call_eval_prefix + cmd_call_eval_trans_prefix

    def execute(self, context, command, marker_node, marker_set):
        code = self.get_inner_content(context, marker_node, translate=True, code=True)
        self.eval_lines(context, code)
        return []


class ExecLinesUpdateMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = cmd_call_eval_prefix * 3

    def execute(self, context, command, marker_node, marker_set):
        code = self.get_inner_content(context, marker_node, translate=False, code=True)
        context.update_variables(self.eval_lines(context, code))
        return []


class ExecCmdcallMarkerBase(MarkerBase):
    def execute(self, context, command, marker_node, marker_set):
        self.eval_mixin(context, command, False)


class ExecCmdcallMarker(ExecCmdcallMarkerBase):
    tag_head = cmd_call_prefix_simple


class ExecCmdcallChainMarker(ExecCmdcallMarkerBase):
    tag_head = cmd_call_prefix_chain + cmd_call_prefix_simple


class MarkerParseExprBase(MarkerBase):
    def execute(self, context, command, marker_node, marker_set):
        self.parse_expression(context, command.lstrip(), False, False)


class ExecCommandOutputChainMarker(MarkerParseExprBase):
    tag_head = MarkerBase.trans_marker_command_output


class ExecCmdcallSimpleLinesMarker(MarkerWithEnd):
    command_append_prefix = cmd_call_prefix_simple
    tag_head = cmd_call_prefix_simple * 3
    cmd_call_marker_cls = ExecCmdcallMarker
    targets_marker_cls = (EmptyMarker,)

    def execute(self, context, command, marker_node, marker_set):
        marker = marker_set.find_marker_by_cls(self.cmd_call_marker_cls)
        result = []
        for child in marker_node.children:
            if child.is_type(*self.targets_marker_cls):
                node = marker_set.node_cls(
                    marker,
                    self.command_append_prefix + ' ' + child.command,
                    child.index,
                    marker_node,
                    child.command
                )
                result.append(node)
            else:
                result.append(child)
        return result


class ExecCmdcallLinesMarker(ExecCmdcallSimpleLinesMarker):
    command_append_prefix = cmd_call_prefix_simple * 2
    tag_head = cmd_call_prefix_simple * 4
