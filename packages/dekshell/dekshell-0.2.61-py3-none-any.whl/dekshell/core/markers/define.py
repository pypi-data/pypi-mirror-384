from .base import MarkerNoTranslator


class DefineMarker(MarkerNoTranslator):
    tag_head = "define"

    def execute(self, context, command, marker_node, marker_set):
        args = self.split_raw(command, 2)
        var_name = args[1]
        try:
            self.eval(context, var_name)
        except NameError:
            expression = self.get_item(args, 2)
            if expression:
                result = self.parse_expression(context, expression)
                self.set_var_raw(context, var_name, result)
