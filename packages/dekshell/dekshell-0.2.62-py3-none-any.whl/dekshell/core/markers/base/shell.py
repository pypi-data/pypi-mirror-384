from dektools.shell import shell_command
from . import MarkerShellBase


class ShellCommand:
    shell_call = shell_command

    def __init__(self, kwargs):
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        kwargs = {**kwargs, **self.kwargs}
        return self.shell(*args, **kwargs)

    def shell(self, *args, **kwargs):
        return shell_command(*args, **kwargs)


class MarkerShell(MarkerShellBase):
    tag_head = ""
    shell_cls = ShellCommand
