import os
import sys
from dektools.sys import sys_paths_relative
from dektools.file import normal_path, which
from dektools.venvx.tools import find_venv_path
from ..utils.shell import shell_name


def search_bin_by_path_tree(filepath, bin_name=None, skip_self=True):
    if not bin_name:
        bin_name = os.path.basename(sys.executable)
    filepath = normal_path(filepath)
    cursor = os.path.dirname(filepath) if os.path.isfile(filepath) else filepath
    while True:
        path_venv = find_venv_path(cursor)
        if path_venv:
            if skip_self and sys.prefix == path_venv:
                return None
            else:
                path_scripts = sys_paths_relative(path_venv)['scripts']
                path_exe = which(bin_name, path_scripts)
                if path_exe:
                    return path_exe
        dir_cursor = os.path.dirname(cursor)
        if dir_cursor == cursor:
            break
        cursor = dir_cursor


def redirect_shell_by_path_tree(filepath):
    return search_bin_by_path_tree(filepath, shell_name)
