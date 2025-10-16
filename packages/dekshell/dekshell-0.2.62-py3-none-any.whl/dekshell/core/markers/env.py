import os
from .base import MarkerBase


class MarkerEnvBase(MarkerBase):

    def execute(self, context, command, marker_node, marker_set):
        argv = self.split_raw(command, 2)[1:]
        if len(argv) == 1:
            self.change_environ(context, argv[0], None)
        elif len(argv) == 2:
            self.change_environ(context, argv[0], str(argv[1]))
        else:
            self.change_environ(context, None, None)

    def change_environ(self, context, key, value):
        raise NotImplementedError


class EnvMarker(MarkerEnvBase):
    tag_head = "env"

    def change_environ(self, context, key, value):
        if key:
            key = key.upper()
            if value is None:
                context.remove_env(key)
            else:
                context.add_env(key, value)


class EnvShellMarker(MarkerEnvBase):
    tag_head = "envs"

    def change_environ(self, context, key, value):
        if key:
            key = key.upper()
            if value is None:
                context.environ.remove_item(key)
            else:
                context.environ.add_item(key, value)
        else:
            context.environ.clear()
