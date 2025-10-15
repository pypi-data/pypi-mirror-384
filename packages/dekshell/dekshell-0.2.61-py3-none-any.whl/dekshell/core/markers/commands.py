import subprocess
from dektools.shell import shell_wrapper
from .base import MarkerWithEnd
from .base.shell import MarkerShell, ShellCommand
from .empty import EmptyMarker


class PrefixShellMarker(MarkerShell):
    tag_head = "@"

    def execute(self, context, command, marker_node, marker_set):
        _, command = self.split_raw(command, 1, self.tag_head)
        if command:
            self.execute_core(context, command, marker_node, marker_set)


class IgnoreErrorShellCommand(ShellCommand):
    def shell(self, *args, **kwargs):
        try:
            shell_wrapper(*args, **kwargs)
        except subprocess.SubprocessError:
            return None


class IgnoreErrorShellMarker(PrefixShellMarker):
    tag_head = "!"
    shell_cls = IgnoreErrorShellCommand


class CommandsMarker(MarkerWithEnd):
    tag_head = "@@"
    target_marker_cls = EmptyMarker

    def execute(self, context, command, marker_node, marker_set):
        argv = self.split_raw(command, 1)
        config = self.get_item(argv, 1, '').strip()
        if config:
            config = eval(f'dict({config})', {'environ': context.environ_full()})
        else:
            config = None
        marker = marker_set.find_marker_by_cls(self.target_marker_cls)
        result = []
        for child in marker_node.children:
            if child.is_type(self.target_marker_cls):
                node = marker_set.node_cls(
                    marker,
                    child.command,
                    child.index,
                    marker_node,
                    payload=config
                )
                result.append(node)
            else:
                result.append(child)
        return result
