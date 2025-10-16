import sys

key_arg = '__arg'
key_args = f'{key_arg}s'
key_kwargs = '__kwargs'
key_argv = f'{key_arg}v'


def pack_context(args, kwargs):
    return {
        **{f'{key_arg}{i}': arg for i, arg in enumerate(args)}, **{key_args: tuple(args), key_kwargs: kwargs}, **kwargs}


def pack_context_argv():
    return {**{f"{key_argv}{i}": x for i, x in enumerate(sys.argv)}, **{key_argv: sys.argv}}


def pack_context_full(args=None, kwargs=None):
    return {**pack_context(args or [], kwargs or {}), **pack_context_argv()}
