# utilities - files and filesystem related

"""
Module contains filesystem related utilities.
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
# others
# ruff: noqa: E501, PLR1702, PLW1514, SIM102, SIM115, TID252, UP015

# fmt: off



from typing import Optional, Union

import sys
import os
import fnmatch
import datetime
import dateutil.tz
import pytz
import time

from .utils_GUI import alertbox

if os.name == "nt" or sys.platform == "win32":
    from .utils_win32 import close_app_windowtitle
else:
    err_msg = f"No implementation for your platform ('{os.name}') available"
    raise ImportError(err_msg)



# check if file is locked
def file_locked(filepath: str, waittime: float = 0.1) -> bool:
    """
    file_locked - check if file is locked

    Args:
        filepath (str): file to be checked
        waittime (float, optional): waiting time for check, defaults to 0.1.

    Returns:
        bool: lock indicator
    """

    if not (os.path.exists(filepath)):
        return False
    try:
        f = open(filepath, 'r')
        f.close()
    except OSError:
        return True

    lockfile = filepath + ".lckchk"
    if os.path.exists(lockfile):
        os.remove(lockfile)
    try:
        os.rename(filepath, lockfile)
        time.sleep(waittime)
        os.rename(lockfile, filepath)
        return False
    except OSError:
        return True

def is_file_locked(filepath: str, waittime: float = 0.1) -> bool:
    """
    is_file_locked - check if file is locked

    Args:
        filepath (str): file to be checked
        waittime (float, optional): waiting time for check. Defaults to 0.1.

    Returns:
        bool: lock indicator
    """
    return file_locked(filepath, waittime)


# find latest changed file in searchpath matching filename pattern provided as searchpattern
# timestamp referring to nanoseconds timestamp from filesystem, otherwise problems in rare cases
# (1 second resolution not sufficient)
def find_last_changed_file(
    searchpath: str,
    searchpattern: str,
    searchstart: Optional[datetime.datetime] = None,
    timeout_sec: int = 10
) -> str:
    """
    find_last_changed_file - find latest changed file in searchpath matching filename pattern provided as searchpattern

    Args:
        searchpath (str): path to search in
        searchpattern (str): file pattern
        searchstart (datetime.datetime, optional): search for files changed after 'searchstart' only. Defaults to None.
        timeout_sec (int, optional): timeout period. Defaults to 10.

    Returns:
        str: name of file found (if any)
    """

    timenow = datetime.datetime.now(dateutil.tz.tz.tzlocal())
    if searchstart is None:
        searchstart = timenow - datetime.timedelta(seconds=5)
    if searchstart.tzinfo is None:
        searchstart = pytz.utc.localize(searchstart)
    lastchangedfile = ""
    # lastchangedtimestamp = searchstart - datetime.timedelta(seconds=1)
    lastchangedtimestamp = searchstart.timestamp() - 1

    while (lastchangedfile == "") and (datetime.datetime.now(dateutil.tz.tz.tzlocal()) <= timenow + datetime.timedelta(seconds=timeout_sec)):

        with os.scandir(searchpath) as searchpathscan:
            scanentry: os.DirEntry    # overcome PyCharm IDE error - workaround derived from https://youtrack.jetbrains.com/issue/PY-46041
            for scanentry in searchpathscan:
                if fnmatch.fnmatch(scanentry.name, searchpattern):
                    filemodified = scanentry.stat().st_mtime_ns / 1000000000
                    if filemodified >= searchstart.timestamp():
                        pathfilename = os.path.join(searchpath, scanentry.name)
                        while os.path.isfile(pathfilename) and is_file_locked(pathfilename):
                            time.sleep(0.5)
                        if os.path.isfile(pathfilename) and not is_file_locked(pathfilename):
                            if filemodified > lastchangedtimestamp and scanentry.stat().st_size > 0:
                                lastchangedfile = scanentry.name
                                lastchangedtimestamp = filemodified
        searchpathscan.close()

    return lastchangedfile


# load text file
def load_textfile(txt_filename: str, mode: str = "str") -> Union[list[str], str]:
    """
    load_textfile - load textfile to list of strings or str

    Args:
        txt_filename (str): source text file
        mode (str, optional): return mode - 'list', 'str' or 'strcleaned'. Defaults to 'str'.

    Returns:
        Union[list[str], str]: content of textfile as list of string or string
    """

    txt: Union[list[str], str] = ""

    fileexists = os.path.isfile(txt_filename)

    # read to list of lines
    if mode == "list":
        if fileexists:
            # via pathlib
            # txt = pathlib.Path(txt_filename).read_text()
            # via normal open file
            with open(txt_filename, "r") as txt_file:
                txt = txt_file.readlines()
            txt_file.close()
        else:
            txt = []
    # read to single string incl. CR
    elif mode == "str":
        if fileexists:
            with open(txt_filename, "r") as txt_file:
                txt = txt_file.read()
            txt_file.close()
        else:
            txt = ""
    # read to single string without CR
    elif mode == "strcleaned":
        if fileexists:
            with open(txt_filename, "r") as txt_file:
                txt = txt_file.read().replace("\n", "")
            txt_file.close()
        else:
            txt = ""
    else:
        err_msg = "Invalid mode."
        raise Exception(err_msg)

    return txt


# close file
def close_app_file(filename: str, msg: str, title: str) -> None:
    """
    close_app_file - close data file opened by an application

    Args:
        filename (str): filename
        msg (str): message for alert box
        title (str): title for alert box
    """

    close_app_windowtitle(filename)
    if file_locked(filename):
        close_app_windowtitle(os.path.splitext(os.path.basename(filename))[0])
    while file_locked(filename):
        alertbox(msg, title)
