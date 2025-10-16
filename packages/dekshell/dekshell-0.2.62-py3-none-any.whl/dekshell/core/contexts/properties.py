import os
import sys
import shutil
import tempfile
import sysconfig
import platform
import getpass
from pathlib import Path
from sysconfig import get_paths
from importlib import metadata
from extra_platforms import current_os as extra_platforms_current_os
from dektools.module import ModuleProxy
from dektools.time import DateTime
from dektools.file import read_text
from dektools.env import is_on_cicd
from dektools.py import get_inner_vars
from dektools.ps.process import process_attrs
from dektools.context.utils import Method, MethodSimple, AttrProxy
from dektools.web.url import Url
from ...utils.serializer import serializer
from ..redirect import shell_name

current_shell = shutil.which(shell_name, path=get_paths()['scripts'])
current_os = extra_platforms_current_os()
user_is_root = "posix" in os.name and os.geteuid() == 0


def make_shell_properties(shell):
    return {
        'shell': shell,
        'sh': {
            'rf': f'{shell} rf',
            'rfc': f'{shell} rfc',
            'rs': f'{shell} rs',
            'ext': '.pysh',
            'version': metadata.version(__name__.partition(".")[0])
        },
    }


package_name = __name__.partition(".")[0]
path_home = os.path.expanduser('~')
is_on_win = os.name == "nt"
path_root = path_home[:path_home.find(os.sep)] if is_on_win else os.sep


class _EnvBase:
    __getenv__ = None

    def __getattr__(self, item):
        context = get_inner_vars('__inner_context__')
        return getattr(context, self.__getenv__)(item.upper(), '')

    def __getitem__(self, item):
        context = get_inner_vars('__inner_context__')
        default = object()
        ret = getattr(context, self.__getenv__)(item.upper(), default)
        if ret is default:
            raise KeyError(item)
        return ret

    def __contains__(self, item):
        context = get_inner_vars('__inner_context__')
        default = object()
        ret = getattr(context, self.__getenv__)(item.upper(), default)
        return ret is not default


class _Env(_EnvBase):
    __getenv__ = 'get_env'


class _EnvS(_EnvBase):
    __getenv__ = 'get_env_full'


default_properties = {
    'meta': {
        'name': package_name,
        'version': metadata.version(package_name)
    },
    'python': sys.executable,
    **make_shell_properties(current_shell),
    'os': {
        'pid': os.getpid(),
        'ps': os.pathsep,
        'cicd': is_on_cicd(),
        'username': getpass.getuser(),
    },
    'platform': {
        'cygwin': sys.platform == 'cygwin',
        'mingw': sysconfig.get_platform() == 'mingw',
        'msys': sys.platform == 'msys',
        'wsl': 'Microsoft' in read_text('/proc/version', default=''),
        'windows': platform.system() == 'Windows',
        'macos': platform.system() == 'Darwin',
        'linux': platform.system() == 'Linux',
        'name': {'Windows': 'windows', 'Darwin': 'macos', 'Linux': 'linux'}.get(platform.system()),
        'entry': current_os,
    },
    'path': {
        'root': Path(path_root),
        'home': Path(path_home),
        'temp': Path(tempfile.gettempdir()),
        'sep': os.sep
    },
    'pu': {
        'attrs': process_attrs
    },
    'Url': Url,
    'obj': serializer,
    'mp': ModuleProxy(),
    'date': DateTime(),
    'env': _Env(),
    'envs': _EnvS(),
    'm': Method(),
    'mm': MethodSimple(),
    'a': AttrProxy(),
}
