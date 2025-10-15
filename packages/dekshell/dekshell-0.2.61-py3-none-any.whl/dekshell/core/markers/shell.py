import subprocess
from dektools.shell import shell_timeout, shell_wrapper, shell_retry
from .base.shell import ShellCommand
from .empty import MarkerShell


class TimeoutShellCommand(ShellCommand):
    def shell(self, command, timeout=None, env=None, **kwargs):
        try:
            if timeout > 0:
                return shell_timeout(command, timeout, env=env)
            else:
                return shell_wrapper(command, env=env)
        except subprocess.SubprocessError as e:
            return e


class TimeoutMarker(MarkerShell):
    tag_head = "timeout"

    shell_cls = TimeoutShellCommand

    def execute(self, context, command, marker_node, marker_set):
        _, timeout, command = self.split_raw(command, 2)
        if command:
            self.execute_core_timeout(context, command, marker_node, marker_set, timeout)

    @classmethod
    def execute_core_timeout(cls, context, command, marker_node, marker_set, timeout):
        return cls.execute_core(context, command, marker_node, marker_set, dict(timeout=int(float(timeout))))


class RetryShellCommand(ShellCommand):
    def shell(self, command, times=None, env=None, **kwargs):
        try:
            return shell_retry(command=command, times=times, env=env)
        except subprocess.SubprocessError as e:
            return e


class RetryMarker(MarkerShell):
    tag_head = "retry"

    shell_cls = RetryShellCommand

    def execute(self, context, command, marker_node, marker_set):
        _, times, command = self.split_raw(command, 2)
        if command:
            self.execute_core_retry(context, command, marker_node, marker_set, times)

    @classmethod
    def execute_core_retry(cls, context, command, marker_node, marker_set, times):
        try:
            times = int(float(times))
        except ValueError:
            times = None
        return cls.execute_core(context, command, marker_node, marker_set, dict(times=times))
