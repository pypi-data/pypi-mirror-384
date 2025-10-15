# from pipdeptree._discovery import get_installed_distributions
from packaging.requirements import Requirement


def get_installed_distributions(
        local_only=False,  # noqa: FBT001, FBT002
        user_only=False,  # noqa: FBT001, FBT002
):
    try:
        from pip._internal.metadata import pkg_resources
    except ImportError:
        # For backward compatibility with python ver. 2.7 and pip
        # version 20.3.4 (the latest pip version that works with python
        # version 2.7)
        from pip._internal.utils import misc

        return misc.get_installed_distributions(  # type: ignore[no-any-return,attr-defined]
            local_only=local_only,
            user_only=user_only,
        )

    else:
        dists = pkg_resources.Environment.from_paths(None).iter_installed_distributions(
            local_only=local_only,
            skip=(),
            user_only=user_only,
        )
        return [d._dist for d in dists]  # type: ignore[attr-defined] # noqa: SLF001


def get_installed_distributions_map(**kwargs):
    return {dist.project_name: dist.version for dist in get_installed_distributions(**kwargs)}


def is_dist_installed(install_str, dist_map):
    req = Requirement(install_str)
    version = dist_map.get(req.name)
    if version:
        return version in req.specifier
    return False
