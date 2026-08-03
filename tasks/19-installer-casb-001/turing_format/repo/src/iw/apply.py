# -*- coding: utf-8 -*-
"""Install a wheel into scheme directories.

See ``docs/installing.rst`` and the task prompt for the intended behaviour.
"""

from __future__ import annotations


def install_wheel(wheel_path, scheme_dirs):
    """Install the wheel at *wheel_path* into *scheme_dirs*.

    :param wheel_path: path to a ``.whl`` file.
    :param scheme_dirs: dict mapping scheme names (``"purelib"``, ``"platlib"``,
        ``"headers"``, ``"scripts"``, ``"data"``) to the directory each scheme
        installs into.
    :returns: a report of the installed files -- a list in which each installed
        file carries its ``path``, ``hash``, and ``size``.
    """
    raise NotImplementedError("install_wheel is not implemented yet")
