import subprocess
from dektools.shell import shell_with_input, shell_with_input_once
from .base import MarkerWithEnd, MarkerNoTranslator


class InputMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = 'inputs'

    def execute(self, context, command, marker_node, marker_set):
        command_text = self.get_inner_content(context, marker_node, sep='', translate=True).strip()
        expression = self.split_raw(command, 1, self.tag_head)[1]
        inputs = self.parse_expression(context, expression)
        rc = shell_with_input(command_text, inputs, env=context.environ_full())
        if rc:
            raise subprocess.CalledProcessError(rc, command_text)
        return []


class InputOnceMarker(MarkerWithEnd, MarkerNoTranslator):
    tag_head = 'input'

    def execute(self, context, command, marker_node, marker_set):
        command_text = self.get_inner_content(context, marker_node, sep='', translate=True).strip()
        inputs = self.split_raw(command, 1, self.tag_head)[1]
        rc = shell_with_input_once(command_text, inputs, env=context.environ_full())[0]
        if rc:
            raise subprocess.CalledProcessError(rc, command_text)
        return []
