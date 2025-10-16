from ..plugin import get_markers_from_modules
from .base import EndMarker, BreakMarker, ContinueMarker
from .var import *
from .env import *
from .if_ import *
from .while_ import *
from .for_ import *
from .define import *
from .comment import *
from .invoke import *
from .function import *
from .exec import *
from .echo import *
from .pip_ import *
from .commands import *
from .redirect import *
from .input import *
from .shell import *
from .empty import *


def generate_markers(*args, **kwargs):
    return [
        *args,
        *get_markers_from_modules(**kwargs),
        ErrorEchoMarker, EchoNoWrapMarker, EchoMarker,
        InputMarker, InputOnceMarker,
        DelVarMarker,
        ExecLinesUpdateMarker, ExecLinesTranslatorMarker, ExecLinesMarker, ExecTranslatorMarker, ExecMarker,
        ExecCommandOutputChainMarker,
        ExecCmdcallSimpleLinesMarker, ExecCmdcallLinesMarker, ExecCmdcallMarker, ExecCmdcallChainMarker,
        EnvShellMarker, EnvMarker,
        IfMarker, IfElifMarker, IfElseMarker,
        WhileMarker, WhileElseMarker,
        ForMarker, ForElseMarker,
        DefineMarker,
        GotoMarker, InvokeMarker,
        RaiseMarker,
        FunctionMarker, CallMarker, ReturnMarker, EnvGlobalMarker, EnvNonlocalMarker,
        VarGlobalMarker, VarNonlocalMarker,
        EndMarker, BreakMarker, ContinueMarker,
        CommentMultiLineMarker, CommentMarker, CommentShebangMarker, CommentConfigMarker, TextContentMarker,
        PipMarker,
        CommandsMarker,
        RedirectMarker, ShiftMarker,
        TimeoutMarker, RetryMarker,
        IgnoreMarker,
        IgnoreErrorShellMarker, PrefixShellMarker,
        AssignCallMarker, AssignInvokerMarker, AssignGotoMarker, AssignImportMarker, AssignTimeoutMarker,
        AssignRetryMarker,
        AssignExecMarker, AssignTranslatorEvalMarker, AssignEvalMarker,
        AssignCommandRcSilenceMarker, AssignCommandRcMarker, AssignCommandOutputMarker,
        AssignDecodeMarker, AssignEncodeMarker,
        AssignEnvMarker, AssignEnvFullMarker, AssignCmdcallMarker, AssignCmdcallChainMarker,
        AssignMultiLineRawStrMarker, AssignMultiLineStrMarker, AssignRawStrMarker, AssignStrMarker, AssignUnpackMarker,
        EmptyMarker,  # must be at the tail
    ]
