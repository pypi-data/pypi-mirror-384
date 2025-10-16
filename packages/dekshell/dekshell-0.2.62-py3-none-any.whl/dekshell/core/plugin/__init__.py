from dektools.plugin import iter_plugins


def get_markers_from_modules(**kwargs):
    return get_attr_from_modules('markers', **kwargs)


def get_contexts_from_modules(**kwargs):
    return get_attr_from_modules('contexts', **kwargs)


def get_attr_from_modules(attr_name, **kwargs):
    result = []
    for plugin in iter_plugins(__name__, **kwargs):
        result.extend(plugin.value.get(attr_name) or [])
    return result
