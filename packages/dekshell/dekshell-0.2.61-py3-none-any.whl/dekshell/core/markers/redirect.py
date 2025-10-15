import os
from dektools.shell import shell_wrapper
from dektools.attr import DeepObjectCall
from ...core.redirect import redirect_shell_by_path_tree
from ...utils.cmd import key_args, key_kwargs
from ..contexts.properties import make_shell_properties, current_shell
from .base import MarkerBase


class MarkerRedirect(MarkerBase):
    def execute(self, context, command, marker_node, marker_set):
        filepath = self.split_raw(command, 1, self.tag_head)[1]
        if not filepath:
            filepath = self.get_filepath(context)
        path_shell = redirect_shell_by_path_tree(filepath)
        self.execute_core(context, marker_node, marker_set, path_shell)

    def execute_core(self, context, marker_node, marker_set, path_shell):
        raise NotImplementedError

    def get_filepath(self, context):
        try:
            return self.eval(context, "fp")
        except NameError:
            return os.getcwd()


class RedirectMarker(MarkerRedirect):
    tag_head = "redirect"
    stack_check = False

    def execute_core(self, context, marker_node, marker_set, path_shell):
        if path_shell:
            shell_properties = make_shell_properties(path_shell)
            if shell_properties['shell'] != current_shell:
                fp = self.get_filepath(context)
                fpp = os.path.dirname(fp).replace('/', os.sep)
                shell = shell_properties['sh']['rfc' if os.getcwd() == fpp else 'rf']
                args, kwargs = self.eval(context, f'({key_args}, {key_kwargs})')
                argv = self.ak2cmd(args, kwargs)
                shell_wrapper(f'{shell} {fp} {argv}', env=context.environ_full())
                return self.exit()
        marker_set.check_stack_error(marker_node)


class ShiftMarker(MarkerRedirect):
    tag_head = "shift"

    def execute_core(self, context, marker_node, marker_set, path_shell):
        if path_shell:
            context.update_variables(DeepObjectCall(make_shell_properties(path_shell)).__dict__)
