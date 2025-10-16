from .base import MarkerWithEnd, BreakMarker, ContinueMarker, MarkerNoTranslator


class WhileElseMarker(MarkerWithEnd):
    tag_head = "else"


class WhileMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = "while"
    branch_set = {WhileElseMarker}

    def bubble_continue(self, context, marker_set, marker_node_self, marker_node_target):
        if marker_node_target.is_type(BreakMarker):
            return marker_node_self, []
        elif marker_node_target.is_type(ContinueMarker):
            return marker_node_self, [marker_node_self]
        return None

    def execute(self, context, command, marker_node, marker_set):
        index_else = self.find_node(marker_node.children, True)

        result = self.get_condition_result(context, command)
        if result:
            return [*marker_node.children[:index_else], marker_set.node_cls(ContinueMarker(), None, None, marker_node)]
        else:
            return marker_node.children[index_else:]

    def get_condition_result(self, context, command):
        expression = command.split(self.tag_head, 1)[-1].strip()
        if not expression:
            return True
        return self.parse_expression(context, expression)
