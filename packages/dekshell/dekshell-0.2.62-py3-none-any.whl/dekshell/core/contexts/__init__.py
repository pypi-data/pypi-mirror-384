import os
from dektools.dict import assign
from dektools.attr import DeepObjectCall
from ..plugin import get_contexts_from_modules
from .methods import default_methods
from .properties import default_properties


def get_all_context(**kwargs):
    return DeepObjectCall(assign(
        default_methods,
        default_properties,
        {
            'path': {
                'wd': os.getcwd(),
            }
        },
        *get_contexts_from_modules(**kwargs)[::-1]
    )).__dict__
