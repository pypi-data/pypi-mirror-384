import os
from dektools.file import normal_path
from dektools.py import get_inner_vars
from ...utils.cmd import pack_context_full
from .base import MarkerBase


class MarkerInvokerBase(MarkerBase):
    def execute(self, context, command, marker_node, marker_set):
        self.execute_core(context, marker_set, self.split_raw(command, 1, self.tag_head)[-1])

    @classmethod
    def execute_core(cls, context, marker_set, s):
        filepath, args, kwargs = cls.cmd_call_parse(context, s, False)
        return cls.execute_file(marker_set, filepath, args, kwargs)

    @classmethod
    def execute_file(cls, marker_set, filepath, args, kwargs):
        if marker_set is None:
            marker_set = get_inner_vars('__inner_marker_set__')
        return cls._run_file(marker_set, normal_path(filepath), pack_context_full(args, kwargs))

    @classmethod
    def _run_file(cls, marker_set, filepath, attrs):
        raise NotImplementedError


class GotoMarker(MarkerInvokerBase):
    tag_head = "goto"

    @classmethod
    def _run_file(cls, marker_set, filepath, attrs):
        return marker_set.shell_exec(filepath, attrs).result


class InvokeMarker(MarkerInvokerBase):
    tag_head = "invoke"

    @classmethod
    def _run_file(cls, marker_set, filepath, attrs):
        cwd = os.getcwd()
        os.chdir(os.path.dirname(filepath))
        ret_value = marker_set.shell_exec(filepath, attrs).result
        os.chdir(cwd)
        return ret_value


class Closure:
    def __init__(self, shell_result):
        self.__variables__ = shell_result.context.variables

    def __getattr__(self, item):
        return self.__variables__.get_item(item)

    def __getitem__(self, item):
        return self.__variables__.get_item(item, None)


class ImportMarker(MarkerInvokerBase):
    tag_head = "import"
    closure_cls = Closure

    @classmethod
    def _run_file(cls, marker_set, filepath, attrs):
        return cls.closure_cls(marker_set.shell_exec(filepath, attrs))
