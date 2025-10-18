# utilities - CLI logging facility

"""
Module provides CLI logging facility. Logging is possible for CLI arguments and
parsed arguments structure.
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
# others
# ruff: noqa: E115, E501, RUF059, SIM102
#
# disable mypy errors
# - mypy error "'object' has no attribute 'xyz' [attr-defined]" when accessing attributes of
#   dynamically (re)bound objects
# mypy: disable-error-code = attr-defined

# fmt: off



import sys
import os.path
import tempfile
import types
import logging
import inspect



# log CLI parameters


# log handler switcher
# inspired by https://stackoverflow.com/questions/20111758/how-to-insert-newline-in-python-logging
def _logger_newline_switch_handler(self, how_many_lines: int = 1) -> None:
    """
    log_newline_switch_handler - method for standard logger object to insert empty line

    Args:
        self (cls): logger, needed as sub is assigned as logger object method.
        how_many_lines (int, optional): number of empty lines. Defaults to 1.
    """

    # switch handler, output a blank line
    self.removeHandler(self.handler_standard)
    self.addHandler(self.handler_newline)
    # output blank lines
    for i in range(how_many_lines):  # noqa: B007
        self.info("")
    # switch back
    self.removeHandler(self.handler_newline)
    self.addHandler(self.handler_standard)

def _logger_newline_switch_formatter(self, how_many_lines: int = 1) -> None:
    """
    log_newline_switch_formatter - method for standard logger object to insert empty line

    Args:
        self (cls): logger, needed as sub is assigned as logger object method.
        how_many_lines (int, optional): number of empty lines. Defaults to 1.
    """

    # switch handler, output a blank line
    self.handler.setFormatter(self.formatter_blank)
    # output blank lines
    for i in range(how_many_lines):  # noqa: B007
        self.info("")
    # switch back
    self.handler.setFormatter(self.formatter_standard)


def setup_CLI_logger(loggerNameCLIlog: str, *, switch_via_handler: bool = False) -> logging.Logger:
    """
    setup_CLI_logger - encapsulated setup of CLI logger object

    Args:
        loggerNameCLIlog (str): name of logger.
        switch_via_handler (bool): define switching mode. Defaults to False.

    Returns:
        Logger: logger object
    """

    # get logger
    loggerCLI = logging.getLogger(loggerNameCLIlog)

    # log file handler
    # log_filehandler = logging.FileHandler(os.path.join(tempfile.gettempdir(), loggerNameCLIlog + "_Py.txt"))

    # log formatter - normal & blank line
    formatter_standard = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s", datefmt="%d.%m.%Y %H:%M:%S")
    formatter_blank = logging.Formatter(fmt="")

    if switch_via_handler:

        # log handler for normal log entries
        # handlerCLI = log_filehandler
        handlerCLI = logging.FileHandler(os.path.join(tempfile.gettempdir(), loggerNameCLIlog + "_Py.txt"))
        handlerCLI.setFormatter(formatter_standard)
        handlerCLI.setLevel(logging.INFO)

        # log handler for blank lines
        # loghandlerNewline = log_filehandler
        handlerNewline = logging.FileHandler(os.path.join(tempfile.gettempdir(), loggerNameCLIlog + "_Py.txt"))
        handlerNewline.setFormatter(formatter_blank)
        handlerNewline.setLevel(logging.INFO)

        # set handler for log object
        loggerCLI.addHandler(handlerCLI)
        loggerCLI.setLevel(logging.INFO)

        # set own switching attributes
        loggerCLI.handler_standard = handlerCLI
        loggerCLI.handler_newline = handlerNewline
        loggerCLI.newline = types.MethodType(_logger_newline_switch_handler, loggerCLI)

    else:

        handler = logging.FileHandler(os.path.join(tempfile.gettempdir(), loggerNameCLIlog + "_Py.txt"))
        handler.setFormatter(formatter_standard)
        handler.setLevel(logging.INFO)

        # set handler for log object
        loggerCLI.addHandler(handler)
        loggerCLI.setLevel(logging.INFO)

        # set own switching attributes
        loggerCLI.handler = handler
        loggerCLI.formatter_standard = formatter_standard
        loggerCLI.formatter_blank = formatter_blank
        loggerCLI.newline = types.MethodType(_logger_newline_switch_formatter, loggerCLI)

    return loggerCLI


# init log
loggerNameCLIlog = "Log_Python_CLI"
loggerCLI = setup_CLI_logger(loggerNameCLIlog)


# logger routine for args
def logCLIargs() -> None:
    """
    logCLIargs - write command line interface parameters to specific CLI call log
    """

    if sys.argv[0] != "-c":
        loggerCLI.info(f"Name Python script: {sys.argv[0]}")
    else:
        stack = inspect.stack()
        loggerCLI.info(
            f"Name Python script: {stack[len(inspect.stack()) - 2].filename} (retrieved from call stack because call using switch -c)"
        )
    argcount = len(sys.argv)
    if argcount > 1:
        for i in range(1, argcount):
            loggerCLI.info(f"Arg {i}: {sys.argv[i]}")
        loggerCLI.info(f"Number of args passed: {argcount - 1}")
    else:
        loggerCLI.info("No args passed.")
    # loggerCLI.info("\n")
    loggerCLI.newline()

def log_cli_args() -> None:
    """
    log_cli_args - write command line interface parameters to specific CLI call log
    """
    logCLIargs()


# logger routine for parsed params (should be type dict)
def logCLIparams(params) -> None:
    """
    logCLIparams - write parsed parameters to specific call log

    Args:
        params (_type_): params
    """

    loggerCLI.info("Parsed arguments (from command line or via parameter injected into parse_args):")
    for param in vars(params):  # params is NamespaceObject of type TapType and not iterable
        if param in params.class_variables or param in params.argument_buffer:
            loggerCLI.info(f"{param}: {getattr(params, param)}")
    # loggerCLI.info("\n")
    loggerCLI.newline()

def log_cli_params(params) -> None:
    """
    log_cli_params - write parsed parameters to specific call log

    Args:
        params (_type_): params
    """
    logCLIparams(params)
