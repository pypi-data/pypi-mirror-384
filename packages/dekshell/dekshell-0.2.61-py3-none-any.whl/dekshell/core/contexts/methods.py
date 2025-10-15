import os
import shutil
import sys
import time
import tempfile
import getpass
import operator
import base64
from importlib import import_module
from functools import reduce
from itertools import chain
from pathlib import Path
from io import BytesIO, StringIO
from dektools.file import sure_dir, write_file, read_text, remove_path, sure_parent_dir, normal_path, \
    format_path_desc, read_file, split_ext, path_ext, clear_dir, copy_recurse_ignore, path_is_empty, \
    read_lines, seek_py_module_path, come_real_path, status_of_dir, diff_of_dir, path_parent, \
    split_file, combine_split_files, remove_split_files, meta_split_file, tree, iglob, \
    iter_dir_type, iter_dir_type_one, rc4_file, iter_relative_path, \
    where, which, those
from dektools.venvx.active import activate_venv, is_venv_active
from dektools.venvx.tools import find_venv_path, is_venv_path
from dektools.venvx.constants import venv_list, venv_main
from dektools.crypto.rc4 import rc4
from dektools.hash import hash_file
from dektools.web.js.polyfill import atob, btoa
from dektools.zip import compress_files, decompress_files
from dektools.output import pprint, obj2str
from dektools.net import get_available_port, get_local_ip_list, get_interface_ip
from dektools.func import FuncAnyArgs
from dektools.fetch import download_file, download_content
from dektools.download import download_from_http
from dektools.ps.process import process_print_all, process_print_detail, process_detail, process_query, process_username
from dektools.time import now
from dektools.str import shlex_split, shlex_quote, str_split, split_table_line
from dektools.py import get_inner_vars
from dektools.format import format_duration
from dektools.shell import shell_wrapper, is_user_admin, shell_timeout, shell_retry, shell_command
from dektools.match import GeneralMatcher, glob2re, glob_compile, glob_match
from dektools.cmd.git import git_parse_modules, git_clean_dir, git_fetch_min, git_remove_tag, git_latest_tag, \
    git_list_remotes, git_apply, git_head
from ...utils.beep import sound_notify
from ..markers.base.core import MarkerBase
from ..markers.invoke import InvokeMarker, GotoMarker, ImportMarker
from ..redirect import search_bin_by_path_tree


def _is_true(x):
    if isinstance(x, str):
        x = x.lower()
    return x not in {'false', '0', 'none', 'null', '', ' ', False, 0, None, b'', b'\0'}


def _list_dir_one(path, file):
    path = normal_path(path)
    for item in os.listdir(path):
        result = os.path.join(path, item)
        if file is None:
            return result
        elif file:
            if os.path.isfile(result):
                return result
        else:
            if os.path.isdir(result):
                return result


def _iter_dir(path, file):
    path = normal_path(path)
    for item in os.listdir(path):
        result = os.path.join(path, item)
        if file is None:
            yield result
        elif file:
            if os.path.isfile(result):
                yield result
        else:
            if os.path.isdir(result):
                yield result


def _tree(*args):
    if len(args) == 1:
        if isinstance(args[0], int):
            tree(None, *args)
        else:
            tree(*args)
    else:
        tree(*args)
    return ''


def _sure_and_clear(path):
    path = normal_path(path)
    sure_dir(path)
    clear_dir(path)


def _remove_path(path):
    if isinstance(path, (str, os.PathLike)):
        remove_path(path)
    else:
        for item in path:
            _remove_path(item)


_default_value = object()


def _parse_expression(expression, default=_default_value, translate=False):
    context = get_inner_vars('__inner_context__')
    try:
        return MarkerBase.parse_expression(context, expression, translate)
    except NameError:
        if default is _default_value:
            raise
        else:
            return default


def _eval_mixin(expression, default=_default_value, translate=False):
    context = get_inner_vars('__inner_context__')
    try:
        return MarkerBase.eval_mixin(context, expression, translate)
    except NameError:
        if default is _default_value:
            raise
        else:
            return default


def _eval_lines(expression, default=_default_value):
    context = get_inner_vars('__inner_context__')
    try:
        return MarkerBase.eval_lines(context, expression)
    except NameError:
        if default is _default_value:
            raise
        else:
            return default


def _global_update(variables):
    context = get_inner_vars('__inner_context__')
    for k, v in variables.items():
        MarkerBase.set_var_raw(context, k, v)


def _env_update(variables):
    context = get_inner_vars('__inner_context__')
    for k, v in variables.items():
        context.add_env(k, v)


def _envs_update(variables):
    context = get_inner_vars('__inner_context__')
    for k, v in variables.items():
        context.environ.add_item(k, v)


def _defined(name):
    default = object()
    return _eval_mixin(name, default=default) is not default


def _install(name):
    def posix(exe):
        s = f"{exe} install -y {name}"
        if is_user_admin():
            s = 'sudo ' + command
        return s

    if shutil.which('apt-get'):
        command = posix('apt-get')
    elif shutil.which('yum'):
        command = posix('yum')
    elif shutil.which('brew'):
        command = f"brew install {name}"
    elif shutil.which('choco'):
        command = f"choco install -y {name}"
    else:
        raise FileNotFoundError(f"Can't find a valid installer to install {name}")
    shell_wrapper(command)


def _io(x=None):
    if x is None:
        x = b''
    return BytesIO(x) if isinstance(x, bytes) else StringIO(x)


def _cd(path=None):
    if path is None:
        path = os.path.expanduser('~')
    sure_dir(path)
    os.chdir(path)
    return path


def _pym(name):
    try:
        m = import_module(name)
        return m.__file__
    except ImportError:
        return None


def _pymd(name):
    r = _pym(name)
    if r:
        return os.path.dirname(r)
    return None


def _pyms(path=None):
    if not path:
        path = _eval_mixin('fp', None)
        if not path:
            path = os.getcwd()
    return seek_py_module_path(path)


def _time_mark(begin=True, name=None):
    var_prefix = '__time_marker__'
    if name is None:
        name = ''
    name = str(name).strip()
    marker_set = get_inner_vars('__inner_marker_set__')
    _now = time.time_ns()
    if begin:
        marker_set.vars.add_item(var_prefix + name, _now)
    else:
        t = marker_set.vars.get_item(var_prefix + name, None)
        if t is None:
            return ''
        else:
            return format_duration(int((_now - t) / 10 ** 6))


path_common_methods = {
    'cd': _cd,
    'cwd': lambda: os.getcwd(),
    'where': where,
    'which': lambda *x, **y: which(*x, **y) or '',
    'those': those,
    'pybin': lambda x=None, p=None: search_bin_by_path_tree(p or os.getcwd(), x, False),
    'pym': _pym,
    'pymd': _pymd,
    'pyms': _pyms,
}

default_methods = {
    'defined': _defined,
    'io': _io,
    'reduce': reduce,
    'chain': chain,
    'echo': lambda *x, **y: print(*x, **{**dict(flush=True), **y}),
    'echos': lambda *x, **y: print(*x, **{**dict(end='', flush=True), **y}),
    'echox': lambda *x, **y: print(*x, **{**dict(file=sys.stderr, flush=True), **y}),
    'pprint': pprint,
    'o2s': obj2str,
    'now': now,
    'getpass': getpass.getpass,
    'install': _install,
    'Path': Path,
    'split': {
        'str': lambda x, y=None: str_split(x, y),
        'tab': split_table_line,
    },
    'venv': {
        None: activate_venv,
        'items': venv_list,
        'main': venv_main,
        'active': is_venv_active,
        'find': find_venv_path,
        'valid': is_venv_path
    },
    'sh': {
        'admin': is_user_admin,
        'timeout': shell_timeout,
        'retry': shell_retry,
        'run': shell_wrapper,
        'cmd': shell_command,
        'env': {
            None: lambda k, v: _env_update({k: v}),
            'update': _env_update,
        },
        'envs': {
            None: lambda k, v: _envs_update({k: v}),
            'update': _envs_update,
        },
        'expr': _parse_expression,
        'eval': _eval_mixin,
        'exec': _eval_lines,
        'var': {
            None: lambda k, v: _global_update({k: v}),
            'update': _global_update,
        },
        'invoke': lambda __placeholder__filepath, *args, **kwargs: InvokeMarker.execute_file(
            None, __placeholder__filepath, args, kwargs),
        'goto': lambda __placeholder__filepath, *args, **kwargs: GotoMarker.execute_file(
            None, __placeholder__filepath, args, kwargs),
        'imp': lambda __placeholder__filepath, *args, **kwargs: ImportMarker.execute_file(
            None, __placeholder__filepath, args, kwargs),
    },
    'path': {
        **path_common_methods,
        'tree': _tree,
        'exists': os.path.exists,
        'empty': path_is_empty,
        'parent': path_parent,
        'abs': normal_path,
        'rel': os.path.relpath,
        'cr': come_real_path,
        'fullname': os.path.basename,
        'name': lambda x: split_ext(x)[0],
        'ext': path_ext,
        'desc': format_path_desc,
        'md': lambda x: sure_dir(normal_path(x)),
        'mdp': lambda x: sure_parent_dir(normal_path(x)),
        'mdt': lambda x=None: tempfile.mkdtemp(prefix=x),
        'mdc': _sure_and_clear,

        'lsa': iter_dir_type,
        'lso': lambda path='.', file=None: iter_dir_type_one(path, file, ''),
        'lsr': iter_relative_path,
        'ls': lambda x='.': os.listdir(x),

        'iglob': iglob,
        'glob': lambda *args, **kwargs: list(iglob(*args, **kwargs)),

        'rm': _remove_path,
        'wf': write_file,
        'rt': read_text,
        'rl': read_lines,
        'rf': read_file,
        'ci': copy_recurse_ignore,

        'sf': split_file,
        'sfr': remove_split_files,
        'sfm': meta_split_file,
        'sfc': combine_split_files,

        'sod': status_of_dir,
        'dod': diff_of_dir,

        'hash': lambda x, name='sha256', args=None: hash_file(name, x, args=args),
    },
    **path_common_methods,
    'time': {
        'now': now,
        'begin': lambda name=None: _time_mark(True, name),
        'end': lambda name=None: _time_mark(False, name),
    },
    'pu': {
        'ps': process_print_all,
        'pd': process_print_detail,
        'detail': process_detail,
        'username': process_username,
        'query': lambda x: list(process_query(x)),
    },

    'sys': {
        'utf8': lambda: sys.stdout.reconfigure(encoding='utf-8'),
        'ak': MarkerBase.ak2cmd,
    },

    'compress': compress_files,
    'decompress': decompress_files,

    'func': FuncAnyArgs,

    'me': lambda x: x,
    'first': lambda x, default=None: next(iter(x), default),

    'true': lambda x=True: _is_true(x),
    'false': lambda x=False: not _is_true(x),

    'not_': lambda x: not x,
    'or_': lambda *x: reduce(operator.or_, x),
    'and_': lambda *x: reduce(operator.and_, x),
    'eq': lambda x, y: x == y,
    'neq': lambda x, y: x != y,
    'is_': lambda x, y: x is y,
    'nis': lambda x, y: x is not y,

    'rc4': rc4,
    'rc4file': rc4_file,

    'b64e': lambda sb, encode='utf-8': base64.b64encode(sb.encode(encode) if isinstance(sb, str) else sb).decode(
        'latin-1'),
    'b64d': lambda sb: base64.b64decode(sb),
    'atob': atob,
    'btoa': btoa,

    'beep': lambda x=True: sound_notify(x),

    'glob': {
        're': glob2re,
        'compile': glob_compile,
        'match': glob_match,
        'matcher': GeneralMatcher,
    },

    'shlex': {
        'split': shlex_split,
        'quote': shlex_quote,
    },

    'net': {
        'ip': get_interface_ip,
        'ips': get_local_ip_list,
        'port': get_available_port,
        'fetch': download_file,
        'download': download_from_http,
        'content': download_content,
    },

    'git': {
        'modules': git_parse_modules,
        'clean': git_clean_dir,
        'fetch': git_fetch_min,
        'tag': {
            'rm': git_remove_tag,
            'latest': git_latest_tag
        },
        'remotes': git_list_remotes,
        'apply': git_apply,
        'head': git_head,
    }
}
