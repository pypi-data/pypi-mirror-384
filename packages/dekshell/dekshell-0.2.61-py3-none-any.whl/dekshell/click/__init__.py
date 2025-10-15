import sys
import typer
from dektools.file import normal_path
from dektools.output import pprint
from dektools.escape import str_escape_unicode
from dektools.shell import associate_console_script, get_current_sys_exe
from dektools.typer import command_mixin, command_version
from dektools.plugin import iter_plugins
from ..core import shell_command_batch, shell_command_file, shell_command_file_cd
from ..core.markers.base import MarkerBase
from ..core.markers.base.core import MarkerContext
from ..core.contexts import get_all_context
from ..core.markers import generate_markers
from ..utils.serializer import serializer, SerializerException
from ..utils.cmd import pack_context_full

app = typer.Typer(add_completion=False)
command_version(app, __name__)


def get_argv(index=None):
    if index is not None:
        return sys.argv[index]
    else:
        return sys.argv


def get_kwargs(begin):
    args, kwargs = MarkerBase.cmd2ak(get_argv()[begin:])
    args, kwargs = MarkerBase.cmd_trans_batch(MarkerContext(), *args, **kwargs)
    return pack_context_full(args, kwargs)


@command_mixin(app)
def rs(args):
    try:
        args = serializer.load(args)
    except SerializerException:
        pass
    shell_command_batch(str_escape_unicode(args), context=pack_context_full())


@app.command(
    context_settings=dict(resilient_parsing=True)
)
def rf():
    shell_command_file(normal_path(get_argv(2)), context=get_kwargs(3))


@app.command(
    context_settings=dict(resilient_parsing=True)
)
def rfc():
    shell_command_file_cd(normal_path(get_argv(2)), context=get_kwargs(3))


@app.command()
def self():
    pprint(dict(
        context=get_all_context(),
        marker=generate_markers(),
        plugin=[str(x) for x in iter_plugins(__name__)]
    ), flush=True)


@app.command()
def assoc():
    path_bin = get_current_sys_exe()
    associate_console_script(
        '.pysh', __name__, 'Pysh',
        f"""from dektools.shell import shell_command_nt_as_admin;shell_command_nt_as_admin(r'"{path_bin}" rf %1')""",
        True)
