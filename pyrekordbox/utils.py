# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""This module contains common constants and methods used in other modules."""

import os
import warnings
import psutil

warnings.simplefilter("always", DeprecationWarning)


def warn_deprecated(name, new_name="", hint="", remove_in=""):
    s = f"'{name}' is deprecated"
    if remove_in:
        s += f" and will be removed in version '{remove_in}'"

    if new_name:
        s += f", use '{new_name}' instead!"
    else:
        s += "!"

    if hint:
        s += "\n" + hint

    warnings.warn(s, DeprecationWarning, stacklevel=3)


def get_process_id(name: str, raise_exec=False) -> int:
    """Returns the ID of a process if it exists.

    Parameters
    ----------
    name : str
        The name of the process, for example 'rekordbox'.
    raise_exec : bool, optional
        Raise an exception if the process can not be found.

    Returns
    -------
    pid : int
        The ID of the process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the application
        is not running.

    Examples
    --------
    >>> get_process_id("rekordbox")
    12345

    >>> get_process_id("rekordboxAgent")
    23456
    """
    for proc in psutil.process_iter():
        proc_name = os.path.splitext(proc.name())[0]  # needed on Windows (.exe)
        try:
            if proc_name == name:
                return proc.pid
        except psutil.AccessDenied:
            pass
    if raise_exec:
        raise RuntimeError("No process with name 'rekordbox' found!")
    return 0


def get_rekordbox_pid(raise_exec=False):
    """Returns the process ID of the Rekordbox application.

    Parameters
    ----------
    raise_exec : bool, optional
        Raise an exception if the Rekordbox process can not be found.

    Returns
    -------
    pid : int
        The ID of the Rekordbox process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the Rekordbox
        application is not running.

    Examples
    --------
    >>> get_rekordbox_pid()
    12345
    """
    return get_process_id("rekordbox", raise_exec)


def get_rekordbox_agent_pid(raise_exec=False):
    """Returns the process ID of the RekordboxAgent application.

    Parameters
    ----------
    raise_exec : bool, optional
        Raise an exception if the RekordboxAgent process can not be found.

    Returns
    -------
    pid : int
        The ID of the RekordboxAgent process if it exists, otherwise zero.

    Raises
    ------
    RuntimeError: If ``raise_exec=True``, raises a runtime error if the RekordboxAgent
        application is not running.

    Examples
    --------
    >>> get_rekordbox_agent_pid()
    23456
    """
    return get_process_id("rekordboxAgent", raise_exec)
