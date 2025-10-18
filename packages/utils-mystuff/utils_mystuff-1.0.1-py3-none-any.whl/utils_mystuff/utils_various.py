# utilities - miscellaneous

"""
Module contains a collection of miscellaneous utilities.
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
# boolean-type arguments
# ruff: noqa: FBT001, FBT002, S101
# others
# ruff: noqa: B006, B905, DTZ007, E501, PLW0602, SIM102, SIM105, UP007, UP045
#
# disable mypy errors
# mypy: disable-error-code = "unused-ignore"

# docsig: disable=SIG501

# fmt: off



from typing import Any, Callable, Optional, TypeVar, Union
# importing ParamSpec in backwards compatible way
try:
    from typing import ParamSpec  # type: ignore
except ImportError:
    from typing_extensions import ParamSpec  # type: ignore

import sys
import os
import configparser
import logging
import tempfile

from functools import wraps

import threading
from contextlib import contextmanager

import locale
import datetime
import calendar
import dateutil.parser



# threadsafe access to locale setting
# https://stackoverflow.com/questions/18593661/how-do-i-strftime-a-date-object-in-a-different-locale
LOCALE_LOCK = threading.Lock()

# switch locale threadsafe
@contextmanager
def setlocale(locale_value: str):
    """
    setlocale - switch locale threadsafe

    Args:
        locale_value (str): target locale
    """

    with LOCALE_LOCK:
        saved_locale_value = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, locale_value)
        finally:
            locale.setlocale(locale.LC_ALL, saved_locale_value)



# find true application directory for frozen/bundled execution
# https://pyinstaller.readthedocs.io/en/stable/runtime-information.html#
# https://stackoverflow.com/questions/404744/determining-application-path-in-a-python-exe-generated-by-pyinstaller/48817163#48817163
def get_real_apppath() -> tuple[str, str]:
    """
    get_real_apppath - find true application directory for frozen/bundled execution

    Returns:
        str: application path
    """

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        running_mode = 'Frozen/executable'
    else:
        try:
            app_full_path = os.path.realpath(__file__)
            application_path = os.path.dirname(app_full_path)
            running_mode = "Non-interactive (e.g. 'python myapp.py')"
        except NameError:
            application_path = os.getcwd()
            running_mode = 'Interactive'

    return application_path, running_mode



# read config file with standardized boolean states into ConfigParser object
def readconfigfile(
    configfile: str,
    optionxform: Optional[Callable[[str], str]] = None,
    encoding: str = "utf-8"
) -> configparser.ConfigParser:
    """
    readconfigfile - read config file with standardized boolean states into ConfigParser object

    Args:
        configfile (str): config file
        optionxform (callable[[str], str]], optional): callable to pass on to ConfigParser.optionxform. Defaults to None.
        encoding (str, optional): file encoding. Defaults to "utf-8".

    Raises:
        Exception: file 'configfile' does not exist.

    Returns:
        configparser.ConfigParser: config parser object
    """

    # no path provided as part of name of configfile, only filename -> use execution directory as default
    if configfile == os.path.basename(configfile):
        configfile = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), configfile)

    if not os.path.isfile(configfile):
        err_msg = f"Error reading ini file '{configfile}'. File does not exist"
        raise Exception(err_msg)

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    if optionxform is not None:
        config.optionxform = optionxform  # type: ignore
    config.BOOLEAN_STATES = {  # type: ignore
        "1": True, "True": True, "true": True, "Yes": True, "yes": True,
        "0": False, "False": False, "false": False, "No": False, "no": False
    }

    config.read(configfile, encoding=encoding)

    return config

def read_configfile(
    configfile: str,
    optionxform: Optional[Callable[[str], str]] = None,
    encoding: str = "utf-8"
) -> configparser.ConfigParser:
    """
    read_configfile - read config file with standardized boolean states into ConfigParser object

    Args:
        configfile (str): config file
        optionxform (callable[[str], str]], optional): callable to pass on to ConfigParser.optionxform. Defaults to None.
        encoding (str, optional): file encoding. Defaults to "utf-8".

    Raises:
        Exception: file 'configfile' does not exist.

    Returns:
        configparser.ConfigParser: config parser object
    """
    return readconfigfile(configfile, optionxform, encoding)


# logging

loggers: dict[str, logging.Logger] = {}

# set up logger including logic to avoid double assignment
# https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
def initLogger(
    loggername: str,
    formatstr: str = "%(asctime)s\t%(levelname)s\t%(message)s",
    datefmtstr: str = "%d.%m.%Y %H:%M:%S",
    filename: str = ""
) -> logging.Logger:
    """
    initLogger - initialize standard logger object

    Args:
        loggername (str): name of logger
        formatstr (str, optional): format string for log entries. Defaults to "%(asctime)s\t%(levelname)s\t%(message)s".
        datefmtstr (str, optional): date format for log entries. Defaults to "%d.%m.%Y %H:%M:%S".
        filename (str, optional): name of log file. Defaults to "".

    Returns:
        logging.Logger: logger object
    """

    global loggers

    if loggers.get(loggername):
        logger = loggers.get(loggername)
    else:
        logger = logging.getLogger(loggername)
        logformatter = logging.Formatter(formatstr, datefmt=datefmtstr)
        if filename == "":
            loghandler = logging.FileHandler(os.path.join(tempfile.gettempdir(), loggername + "_Py.txt"))
        else:
            loghandler = logging.FileHandler(filename)
        loghandler.setFormatter(logformatter)
        loghandler.setLevel(logging.INFO)
        logger.addHandler(loghandler)
        logger.setLevel(logging.INFO)
        loggers[loggername] = logger

    assert logger is not None
    return logger

def init_logger(
    loggername: str,
    formatstr: str = "%(asctime)s\t%(levelname)s\t%(message)s",
    datefmtstr: str = "%d.%m.%Y %H:%M:%S",
    filename: str = ""
) -> logging.Logger:
    """
    init_logger - initialize standard logger object

    Args:
        loggername (str): name of logger
        formatstr (str, optional): format string for log entries. Defaults to "%(asctime)s\t%(levelname)s\t%(message)s".
        datefmtstr (str, optional): date format for log entries. Defaults to "%d.%m.%Y %H:%M:%S".
        filename (str, optional): name of log file. Defaults to "".

    Returns:
        logging.Logger: logger object
    """
    return initLogger(loggername, formatstr, datefmtstr, filename)


# set loglevel from config file
def setLogLevel(logger: logging.Logger, config: configparser.ConfigParser, section: str, optionLogLevel: str) -> None:
    """
    setLogLevel - set log level from configparser object

    Args:
        logger (logging.Logger): name of logger
        config (configparser): configparser object
        section (str): section in 'config'
        optionLogLevel (str): option in 'config'
    """

    if (logger is not None) and (config is not None):
        loglevelnum = getattr(logging, config[section][optionLogLevel].upper(), None)
        if isinstance(loglevelnum, int):
            logger.setLevel(loglevelnum)
        else:
            logger.setLevel(logging.INFO)

def set_loglevel(logger: logging.Logger, config: configparser.ConfigParser, section: str, optionLogLevel: str) -> None:
    """
    set_logLevel - set log level from cCallableonfigparser object

    Args:
        logger (logging.Logger): name of logger
        config (configparser): configparser object
        section (str): section in 'config'
        optionLogLevel (str): option in 'config'
    """
    setLogLevel(logger, config, section, optionLogLevel)

def set_loglevel_from_config(logger: logging.Logger, config: configparser.ConfigParser, section: str, optionLogLevel: str) -> None:
    """
    set_loglevel_from_config - set log level from configparser object

    Args:
        logger (logging.Logger): name of logger
        config (configparser): configparser object
        section (str): section in 'config'
        optionLogLevel (str): option in 'config'
    """
    setLogLevel(logger, config, section, optionLogLevel)



# convert to bool - useful for evaluation of CLI parameters
def to_bool(value: Union[str, int, float, bool], truevalues: list[str] = ["true", "yes", "x", "1", "-1"]) -> bool:
    """
    to_bool - convert basic scalar types to  bool

    Args:
        value (Union[str, int, float, bool]): value to be checked
        truevalues (list[str], optional): truthy str values. Defaults to ["true", "yes", "x", "1", "-1"].


    Returns:
        bool: truthiness of value
    """

    if type(value) is bool:
        return value
    elif type(value) in {int, float}:
        return value != 0
    elif type(value) is str:
        return value.lower() in truevalues
    else:
        return False

def to_boolean(value: Union[str, int, float, bool], truevalues: list[str] = ["true", "yes", "x", "1", "-1"]) -> bool:
    """
    to_boolean - convert basic scalar types to  bool

    Args:
        value (Union[str, int, float, bool]): value to be checked
        truevalues (list[str], optional): truthy str values. Defaults to ["true", "yes", "x", "1", "-1"].

    Returns:
        bool: truthiness of value
    """

    return to_bool(value, truevalues)


# create localized parserinfo object for dateutil.parser
# inspired by https://stackoverflow.com/questions/19927654/using-dateutil-parser-to-parse-a-date-in-another-language/62581811#62581811
class parserinfo_localized(dateutil.parser.parserinfo):
    """
    parserinfo_localized - create localized date parser object
    """

    def __init__(self, localeID: str, *args, **kwargs):
        """ initialize parserinfo localized """

        with setlocale(localeID):
            self.WEEKDAYS = zip(calendar.day_abbr, calendar.day_name)  # type: ignore[assignment]
            self.MONTHS = list(zip(calendar.month_abbr, calendar.month_name))[1:]  # type: ignore[assignment]
        super().__init__(*args, **kwargs)


# check date value
def isdate(checkvalue: Any, checkformat="%d.%m.%Y") -> bool:
    """
    isdate - check if checkvalue is a date value

    Args:
        checkvalue (Any): value to be checked
        checkformat (str, optional): dateformat for check of checkvalue of type str. Defaults to "%d.%m.%Y".

    Returns:
        bool: checkvalue is date or not
    """

    if checkvalue is None or checkvalue == "":
        return False
    # elif type(checkvalue).__name__ == "datetime" or type(checkvalue).__name__ == "date":
    elif isinstance(checkvalue, (datetime.datetime, datetime.date)):
        return True
    elif isinstance(checkvalue, str):
        try:
            check = bool(datetime.datetime.strptime(checkvalue, checkformat))
        except ValueError:
            check = False
        return check
    else:
        return False

def is_date(checkvalue: Any, checkformat="%d.%m.%Y") -> bool:
    """
    is_date - check if checkvalue is a date value

    Args:
        checkvalue (Any): value to be checked
        checkformat (str, optional): dateformat for check of checkvalue of type str. Defaults to "%d.%m.%Y".

    Returns:
        bool: checkvalue is date or not
    """
    return isdate(checkvalue, checkformat)



# copy fields from dict to target structure, can be used to copy same named fields to a data class from
# - TypedArgParser via <TypedArgParser object>.as_dict()
# - one dataclass to another via <dataclass>.asdict()
def copydictfields(source: dict, target: Any) -> None:
    """
    copydictfields - copy fields from dict to target structure

    can be used to copy same named fields to a data class from TypedArgParser via <TypedArgParser object>.as_dict() or
    one dataclass to another via <dataclass>.asdict()

    Args:
        source (dict): source dictionary
        target (Any): target dictionary
    """

    for key, value in source.items():
        if hasattr(target, key):
            target.key = value
        elif isinstance(target, dict):
            if key in target:
                target[key] = value

def copy_dictfields(source: dict, target: Any) -> None:
    """
    copy_dict_fields - copy fields from dict to target structure

    can be used to copy same named fields to a data class from TypedArgParser via <TypedArgParser object>.as_dict() or
    one dataclass to another via <dataclass>.asdict()

    Args:
        source (dict): source dictionary
        target (Any): target dictionary
    """
    copy_dictfields(source, target)



# decorator for ignoring exceptions
# https://stackoverflow.com/questions/5929107/decorators-with-parameters
# https://lemonfold.io/posts/2022/dbc/typed_decorator/


_P = ParamSpec('_P')
_R = TypeVar('_R')
_FuncT = TypeVar('_FuncT', bound=Callable[..., Any])

# parameterized decorator
# - definition of ignored exceptions in decorator parameter using closure
# - no change of signature of decorated function
# Note: Optional added for cases where exception is caught (hint from AI)
def ignore_exceptions_parameterized(ignored_exceptions: tuple[type[BaseException]]) -> Callable[[Callable[_P, _R]], Callable[_P, Optional[_R]]]:  # type: ignore
    """
    ignore_exceptions_parameterized - parameterized decorator for ignoring exceptions using closure

    Args:
        ignored_exceptions (tuple[BaseException]): exceptions to be ignored

    Returns:
        Callable: wrapped function
    """
    def ignore_exceptions_helper(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            if ignored_exceptions:
                try:
                    result = func(*args, **kwargs)
                except ignored_exceptions:
                    pass
            else:
                result = func(*args, **kwargs)
            return result

        return wrapper

    return ignore_exceptions_helper

# non-parameterized decorator
# - definition of ignored exceptions via parameter of decorated function
# - change of signature of decorated function, dependency between decorator and decorated function
def ignore_exceptions(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    ignore_exceptions - decorator for ignoring exceptions using parameter in decorated function

    Args:
        func (Callable): function to be decorated

    Returns:
        Callable: wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        ignored_exceptions = kwargs.get('ignored_exceptions')
        # if ignored_exceptions:
        if isinstance(ignored_exceptions, tuple) and all(issubclass(e, BaseException) for e in ignored_exceptions):
            try:
                result = func(*args, **kwargs)
            except ignored_exceptions:
                pass
        else:
            result = func(*args, **kwargs)
        return result

    return wrapper
