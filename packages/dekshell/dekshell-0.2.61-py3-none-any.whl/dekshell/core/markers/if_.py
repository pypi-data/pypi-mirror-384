from .base import MarkerWithEnd, MarkerNoTranslator


class MarkerWithJudge(MarkerWithEnd, MarkerNoTranslator):
    empty_expected_value = False

    def execute(self, context, command, marker_node, marker_set):
        index = next((i for i, child in enumerate(marker_node.children) if child.is_type(*self.final_branch_set)), None)
        result = self.get_condition_result(context, command.split(self.tag_head, 1)[-1].strip())
        if result:
            return marker_node.children[:index]
        else:
            if index is None:
                return []
            else:
                return marker_node.children[index:]

    def get_condition_result(self, context, expression):
        if not expression:
            return self.empty_expected_value
        return self.parse_expression(context, expression)


class IfElseMarker(MarkerWithJudge):
    tag_head = "else"
    empty_expected_value = True


class IfElifMarker(MarkerWithJudge):
    tag_head = "elif"
    branch_set = {None, IfElseMarker}


class IfMarker(MarkerWithJudge):
    tag_head = "if"
    branch_set = {IfElifMarker, IfElseMarker}
