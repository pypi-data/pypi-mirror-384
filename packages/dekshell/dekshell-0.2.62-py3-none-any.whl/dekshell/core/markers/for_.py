import re
from .base import MarkerWithEnd, BreakMarker, ContinueMarker, MarkerNoTranslator


class ForElseMarker(MarkerWithEnd):
    tag_head = "else"


def _iter_key(node):
    return f'__for__iter_{node.index}'


class ForMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = "for"
    branch_set = {ForElseMarker}

    def bubble_continue(self, context, marker_set, marker_node_self, marker_node_target):
        if marker_node_target.is_type(BreakMarker):
            marker_set.vars.remove_item(_iter_key(marker_node_self))
            return marker_node_self, []
        elif marker_node_target.is_type(ContinueMarker):
            return marker_node_self, [marker_node_self]
        return None

    def execute(self, context, command, marker_node, marker_set):
        index_else = self.find_node(marker_node.children, True)

        index_head = command.find(self.tag_head)
        index_in_left, index_in_right = re.search(r'\bin\b', command).span()
        item_unpack = command[index_head + len(self.tag_head):index_in_left].strip()

        var_temp_iter = _iter_key(marker_node)
        iter_value = marker_set.vars.get_item(var_temp_iter, self.VALUE_UNSET)
        if iter_value is self.VALUE_UNSET:
            expression = command[index_in_right:].strip()
            iter_value = iter(self.get_expression_value(context, expression))
            marker_set.vars.add_item(var_temp_iter, iter_value)

        item_value = next(iter_value, self.VALUE_UNSET)
        if item_value is self.VALUE_UNSET:
            marker_set.vars.remove_item(var_temp_iter)
            return [] if index_else is None else marker_node.children[index_else:]
        item_context = self.eval_lines(context, f"{item_unpack} = _", {'_': item_value})
        for k, v in item_context.items():
            self.set_var_raw(context, k, v)
        return [
            *(marker_node.children if index_else is None else marker_node.children[:index_else]),
            marker_set.node_cls(ContinueMarker(), None, None, marker_node)
        ]

    def get_expression_value(self, context, expression):
        return self.parse_expression(context, expression)
