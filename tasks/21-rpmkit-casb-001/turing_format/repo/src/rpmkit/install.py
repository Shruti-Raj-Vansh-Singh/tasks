# -*- coding: utf-8 -*-
"""Unpack an RPM package into a staging root.

See ``docs/unpacking.md`` and the task prompt for the intended behaviour.
"""

from __future__ import annotations


def install_rpm(rpm_path, dest_dir):
    """Unpack the RPM at *rpm_path* into *dest_dir*.

    :param rpm_path: path to a ``.rpm`` file.
    :param dest_dir: directory to unpack the package's files into.
    :returns: a report of the installed files -- a list in which each installed
        file carries its ``path``, ``digest``, and ``size``.
    """
    raise NotImplementedError("install_rpm is not implemented yet")
