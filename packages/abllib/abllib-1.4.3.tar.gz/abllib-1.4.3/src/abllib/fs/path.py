"""A module containing path-modification functions."""

import pathlib

def absolute(*paths: str | pathlib.Path) -> str:
    """
    Return an absolute path, regardless of what is input.

    Additionally, the path is resolved, removing any symlinks on the way.
    """

    if len(paths) == 0:
        raise ValueError()
    for item in paths:
        if not isinstance(item, (str, pathlib.Path)):
            raise TypeError()

    path = pathlib.Path(*paths)

    if path.is_absolute():
        return str(path.resolve())

    return str(path.absolute().resolve())
