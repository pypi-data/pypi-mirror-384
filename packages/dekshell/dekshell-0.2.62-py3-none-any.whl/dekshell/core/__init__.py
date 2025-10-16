import os
import sys
import time
import codecs
import datetime
from collections import OrderedDict
from dektools.time import get_tz
from dektools.format import format_duration
from dektools.shell import shell_command, shell_wrapper
from dektools.file import normal_path, seek_py_module_path
from dektools.escape import str_escape_wrap
from .contexts import get_all_context
from .markers import generate_markers, CommentConfigMarker
from .markers.base.core import MarkerBase, MarkerSet
from ..utils.beep import sound_notify
from ..utils.shell import shell_bin
from ..utils.cmd import pack_context_full


def shell_file(__placeholder__filepath, *args, **kwargs):
    shell_wrapper(f'{shell_bin} rf "{__placeholder__filepath}" {MarkerBase.ak2cmd(args, kwargs)}')


def shell_file_cd(__placeholder__filepath, *args, **kwargs):
    shell_wrapper(f'{shell_bin} rfc "{__placeholder__filepath}" {MarkerBase.ak2cmd(args, kwargs)}')


def shell_command_file_cd(filepath, **kwargs):
    cwd = os.getcwd()
    os.chdir(os.path.dirname(filepath))
    ret_value = shell_command_file(filepath, **kwargs)
    os.chdir(cwd)
    return ret_value


def shell_command_file(filepath, **kwargs):
    filepath = normal_path(filepath, unix=True)
    with codecs.open(filepath, encoding='utf-8') as f:
        kwargs['source'] = dict(desc=filepath)
        kwargs['context'] = {**(kwargs.get('context') or {}), **dict(
            fp=filepath,
            fpp=os.path.dirname(filepath),
            fpy=seek_py_module_path(filepath),
        )}
        return shell_command_batch(f.read(), **kwargs)


def shell_command_file_common(filepath, *args, **kwargs):
    return shell_command_file(filepath, context=pack_context_full(args, kwargs))


default_configs = {
    'default': dict(),
    'beep': dict(beep_success=True, beep_failed=True),
    'deschead': dict(desc_begin=True, desc_took=True),
    'descper': dict(desc_begin_per=True, desc_took_per=True),
    'source': lambda src: dict(source=dict(desc=src))
}
default_configs = {
    **default_configs,
    'notify': {**default_configs['beep'], **default_configs['deschead']},
    'notifyper': {**default_configs['beep'], **default_configs['deschead'], **default_configs['descper']},
}


def shell_command_batch(commands, **kwargs):
    config_str = CommentConfigMarker.get_config_string(commands)
    if config_str:
        kwargs.update(eval(config_str, default_configs))
    return shell_command_batch_core(commands, **kwargs)


def shell_command_batch_core(
        commands,
        context=None,
        marker=None,
        desc_begin=False,
        desc_begin_per=False,
        desc_took=False,
        desc_took_per=False,
        beep_success=False,
        beep_failed=False,
        tz=None,
        ms_names=None,
        marker_set_cls=None,
        plugin_kwargs=None,
        source=None
):
    def shell_kwargs():
        return dict(
            marker=marker,
            ms_names=ms_names,
            marker_set_cls=marker_set_cls,
            plugin_kwargs=plugin_kwargs,
        )

    def shell_exec(filepath, c=None):
        return shell_command_file(
            filepath,
            context=c or {},
            **shell_kwargs()
        )

    def shell_cmd(cmd, execute=None, env=None):
        if desc_begin_per:
            _shell_desc_begin(cmd)
        ts_per_begin = time.time()
        err = (execute or shell_command)(cmd, env=env)
        if err:
            sys.stdout.write('\n')
            if beep_failed:
                sound_notify(False)
            raise err
        else:
            if desc_took_per:
                _shell_desc_took(cmd, int((time.time() - ts_per_begin) * 1000), ms_names, tz)
            return err

    marker_set = (marker_set_cls or MarkerSet)(
        generate_markers(*(marker or []), **(plugin_kwargs or {})),
        shell_exec, shell_cmd
    )
    context_final = {**get_all_context(), **(context or {})}
    tz = get_tz(tz)
    ts_begin = time.time()
    commands, ln = _get_commands(commands)
    commands_name = _get_commands_name(commands, source)
    if desc_begin:
        _shell_desc_begin(commands_name)

    ret_value = marker_set.execute(commands, context_final, ln)

    if desc_took:
        _shell_desc_took(commands_name, int((time.time() - ts_begin) * 1000), ms_names, tz)
    if beep_success:
        sound_notify(True)
    return ret_value


def _shell_desc_begin(desc):
    print(f'\n\n---------Running---------: {desc}\n\n', flush=True)


def _shell_desc_took(desc, ms, ms_names, tz):
    now = datetime.datetime.now(tz)
    print(f'\n\n---------Done------------: {desc}', flush=True)
    print(f'---------Took------------: {format_duration(ms, ms_names)} (now: {now})\n\n', flush=True)


def _get_commands(commands):
    result = []
    ln = OrderedDict()
    nowrap = False
    for i, command in enumerate(commands.split('\n')):
        if command.endswith('\r'):
            command = command[:-1]
        command, wrap = str_escape_wrap(command)
        if nowrap:
            result[-1] += command
            ln[len(result) - 1] = ln.get(len(result) - 1, 0) + 1
        else:
            result.append(command)
        nowrap = not wrap
    return result, ln


def _get_commands_name(commands, source):
    if source:
        desc = source.get('desc')
        if desc:
            return desc
    if not commands:
        return ''
    elif len(commands) == 1:
        return commands[0]
    else:
        suffix = ' ···' if len(commands) > 2 else ''
        return f"{commands[0]} ···  {commands[1]}{suffix}"
