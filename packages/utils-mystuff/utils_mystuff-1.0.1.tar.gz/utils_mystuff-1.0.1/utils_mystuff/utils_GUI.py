# utilities - GUI related, advanced version with singleton GUI wrapper class to allow switching GUI framework

"""
Module provides a wrapped access to different GUI frameworks for basic GUI functions (message box etc.).
Calling is via module routines or a singleton GUI framework wrapper class.
Supported GUI frameworks are 'easygui', 'pymsgbox', 'freesimplegui' (as FOSS predecessor of 'PySimpleGUI').


Example / doctest:
```
>>> import utils_mystuff as Utils
>>>
>>> # test singleton mechanism
>>> GUIwrapper2 = Utils.utils_GUI.GUIwrapperClass()
>>> print(Utils.GUIwrapper == GUIwrapper2)
True
>>>
>>> # test listbox single-select mode
>>> test1 = Utils.listbox("Single selection test", "Test Listbox", ["option 1", "option 2", "option 3", "option 4"], multiselect=False)
>>> Utils.alertbox(test1, "Test Listbox - single selection")
>>>
>>> # test listbox multi-select mode
>>> test2 = Utils.listbox("Multiple selection mode test", "Test Listbox", ["option 1", "option 2", "option 3", "option 4"], multiselect=True)
>>> Utils.alertbox(test2, "Test Listbox - multiple selection")
>>>
>>> # test alertbox and inputbox
>>> Utils.alertbox("Test alert text", "Alert Title")
>>> testinput = Utils.inputbox("Test input prompt:", "Input Title")
>>> if testinput is not None:
...    Utils.alertbox(testinput, "Test input display")
... else:
...     Utils.alertbox("keine Eingabe!", "Test input display")
>>>
>>> # test yes-No
>>> testYN = Utils.confirmYesNo("Test confirm Yes/No:", "Confirm YN Title", ["Ja", "Nein"])
>>> Utils.alertbox(testYN, "Test input Display")

```
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: B006, E501, F841, PLW3301, RUF022
#
# disable mypy errors
# - errors occur when attributes of dynamically (re)loaded module(s)
# - mypy error "Returning Any from function ..."
# mypy: disable-error-code = "attr-defined, union-attr, no-any-return"

# fmt: off



from typing import Any, Union

import sys
import os.path
import importlib



# block direct calling especially wrapper class
__all__ = ['GUIwrapper', 'set_gui', 'setGUI', 'alertbox', 'confirm_yes_no', 'confirmYesNo', 'inputbox', 'listbox',
    'exit_finished', 'exitFinished'
]



# singleton wrapper class for different GUI frameworks
class GUIwrapperClass:
    """
    GUIwrapperClass - singleton wrapper class for different GUI frameworks
    """

    _guiID: str = ""
    _gui_module = None

    # singleton constructor
    def __new__(cls):
        """
        __new__ - constructor for GUI wrapper class singleton object
        """

        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    # set GUI framework
    def setGUI(self, gui: str) -> None:
        """
        setGUI - set GUI framework

        currently supported GUI frameworks are 'easygui', 'pymsgbox', 'freesimplegui'
        (as FOSS predecessor of 'PySimpleGUI')

        Args:
            gui (str): GUI framework selector

        Raises:
            Exception: Exception if invalid GUI framework selector provided.
        """

        if gui != self._guiID:
            if gui.lower() == "easygui":
                self._guiID = gui
                self._gui_module = importlib.import_module("easygui")
            elif gui.lower() == "pymsgbox":
                self._guiID = gui
                self._gui_module = importlib.import_module("pymsgbox")
                # font size adjustment for PyMsgBox
                self._gui_module.PROPORTIONAL_FONT_SIZE = 10
                self._gui_module.TEXT_ENTRY_FONT_SIZE = 10
            elif gui.lower() == "freesimplegui" or gui.lower() == "pysimplegui":
                self._guiID = gui
                self._gui_module = importlib.import_module("FreeSimpleGUI")
                # set theme
                self._gui_module.theme("Default1")
            else:
                err_msg = "GUI parameter invalid."
                raise Exception(err_msg)

    def set_gui(self, gui: str) -> None:
        """
        set_gui - set GUI framework

        currently supported GUI frameworks are 'easygui', 'pymsgbox', 'freesimplegui'
        (as FOSS predecessor of 'PySimpleGUI')

        Args:
            gui (str): GUI framework selector

        Raises:
            Exception: Exception if invalid GUI framework selector provided.
        """
        self.setGUI(gui)

    # generalized message box for alerts
    def alertbox(self, text: str, title: str = "") -> None:
        """
        alertbox - display alert box

        Args:
            text (str): prompt text
            title (str): title for popup. Defaults to empty string.
        """

        if title == "":
            title = os.path.basename(sys.argv[0])
        if self._guiID.lower() == "easygui":
            self._gui_module.msgbox(text, title)
        elif self._guiID.lower() == "pymsgbox":
            self._gui_module.alert(text, title)
        elif self._guiID.lower() in {"freesimplegui", "pysimplegui"}:
            # https://github.com/PySimpleGUI/PySimpleGUI/issues/5879
            self._gui_module.popup(text, title=title, drop_whitespace=False, button_justification="LEFT")
            pass

    # generalized prompt for input
    def inputbox(self, text: str, title: str = "", default: str = "") -> Any:
        """
        inputbox - input box

        Args:
            text (str): prompt text
            title (str): title for popup. Defaults to empty string.
            default (str): default value. Defaults to empty string.

        Returns:
            Any: entered value
        """

        if title == "":
            title = os.path.basename(sys.argv[0])
        if self._guiID.lower() == "easygui":
            return self._gui_module.enterbox(text, title, default)
        elif self._guiID.lower() == "pymsgbox":
            return self._gui_module.prompt(text, title, default)
        elif self._guiID.lower() in {"freesimplegui", "pysimplegui"}:
            return self._gui_module.popup_get_text(message=text, title=title, default_text=default)

    # generalized selection box
    def listbox(  # type: ignore
        self,
        text: str,
        title: str = "",
        choices: list[str] = [],
        multiselect: bool = False
    ) -> Union[str, list[str]]:
        """
        listbox - display listbox with single or multiple selection option

        Args:
            text (str): prompt text
            title (str): title for popup. Defaults to empty string.
            choices (List[str]): choices for listbox. Defaults to [].
            multiselect (bool): flag for multi-select mode. Defaults to False.

        Returns:
            Union[str, List[str]]: selected option(s)
        """
        retval: Union[str, list[str]] = ""  # dummy assignment for mypy

        if title == "":
            title = os.path.basename(sys.argv[0])
        if choices == []:
            err_msg = "No choices provided"
            raise Exception(err_msg)
        if self._guiID.lower() == "easygui":
            if multiselect:
                return self._gui_module.multchoicebox(text, title, choices)
            else:
                return self._gui_module.choicebox(text, title, choices)
        elif self._guiID.lower() == "pymsgbox":
            err_msg = "'pymsgbox' does not support listbox. Wrapper aborted."
            raise Exception(err_msg)
        elif self._guiID.lower() in {"freesimplegui", "pysimplegui"}:
            if multiselect:
                selectmode = self._gui_module.LISTBOX_SELECT_MODE_MULTIPLE
            else:
                selectmode = self._gui_module.LISTBOX_SELECT_MODE_SINGLE
            layout = [
                [self._gui_module.Text(text)],
                [self._gui_module.Listbox(
                    choices, [0], size=(max(max(map(len, choices)), len(text) + 5) , min(len(choices), 10)),
                    key='-LISTBOX-', enable_events=True, bind_return_key=True, select_mode=selectmode
                )],
                [self._gui_module.OK(), self._gui_module.Cancel()]]
            window = self._gui_module.Window(title, layout, finalize=True)
            listbox = window['-LISTBOX-']
            retval = ""
            while True:
                event, values = window.read()
                if event in {self._gui_module.WIN_CLOSED, "Cancel"}:
                    retval = [] if multiselect else ""
                    break
                elif event == "OK":
                    if multiselect:
                        retval = values["-LISTBOX-"]
                    else:
                        try:
                            retval = values["-LISTBOX-"][0]
                        except BaseException:
                            retval = ""
                    break
                elif 'LISTBOX':
                    pass
                if not multiselect and values["-LISTBOX-"]:
                    try:
                        retval = values["-LISTBOX-"][0]
                    except BaseException:
                        retval = ""
                    break
            window.close()
            return retval

    # generalized message box for confirmations
    def confirmYesNo(  # type: ignore
        self,
        text: str,
        title: str = "",
        buttons: list = ['Yes', 'No']
    ) -> str:
        """
        confirmYesNo - display simple Yes/No dialog box (optinally with alternative buttons)

        Args:
            text (str): prompt text
            title (str): title for popup. Defaults to empty string.
            buttons (list): label for buttons. Defaults to ['Yes', 'No'].

        Returns:
            str: label of pressed button
        """

        if title == "":
            title = os.path.basename(sys.argv[0])
        if self._guiID.lower() == "easygui":
            return self._gui_module.buttonbox(text, title, buttons)
        elif self._guiID.lower() == "pymsgbox":
            return self._gui_module.confirm(text, title, buttons)
        elif self._guiID.lower() == "freesimplegui" or self._guiID.lower() == "pysimplegui":
            # return self._gui_module.popup_yes_no(text, title=title)
            return self._gui_module.popup(text, title=title, custom_text=(buttons[0], buttons[1]))

    def confirm_yes_no(self, text: str, title: str = "", buttons: list = ['Yes', 'No']) -> str:
        """
        confirm_yes_no - display simple Yes/No dialog box (optinally with alternative buttons)

        Args:
            text (str): prompt text
            title (str): title for popup. Defaults to empty string.
            buttons (list): label for buttons. Defaults to ['Yes', 'No'].

        Returns:
            str: label of pressed button
        """
        return self.confirmYesNo(text, title, buttons)


# initialize GUIwrapper with default GUI framework
GUIwrapper = GUIwrapperClass()
GUIwrapper.setGUI("freesimplegui")


# module level caller stubs for GUIwrapperClass singleton object

# set GUI framework
def setGUI(gui: str) -> None:
    """
    setGUI - caller stub for singleton GUIwrapperClass object method to set GUI framework

    currently supported GUI frameworks are 'easygui', 'pymsgbox', 'freesimplegui' (as FOSS predecessor of 'PySimpleGUI')

    Args:
        gui (str): GUI framework selector

    Raises:
        Exception: Exception if invalid GUI framework selector provided.
    """
    GUIwrapper.setGUI(gui)

def set_gui(gui: str) -> None:
    """
    set_gui - caller stub for singleton GUIwrapperClass object method to set GUI framework

    currently supported GUI frameworks are 'easygui', 'pymsgbox', 'freesimplegui' (as FOSS predecessor of 'PySimpleGUI')

    Args:
        gui (str): GUI framework selector

    Raises:
        Exception: Exception if invalid GUI framework selector provided.
    """
    GUIwrapper.setGUI(gui)

# generalized message box for alerts
def alertbox(text: str, title: str = "") -> None:
    """
    alertbox - caller stub for singleton GUIwrapperClass object method

    Args:
        text (str): prompt text
        title (str): title for popup. Defaults to empty string.
    """
    GUIwrapper.alertbox(text, title)

# generalized prompt for input
def inputbox(text: str, title: str = "", default: str = "") -> Any:
    """
    inputbox - caller stub for singleton GUIwrapperClass object method

    Args:
        text (str): prompt text
        title (str): title for popup. Defaults to empty string.
        default (str): default value. Defaults to empty string.

    Returns:
        Any: entered value
    """
    return GUIwrapper.inputbox(text, title, default)

# generalized selection box
def listbox(
    text: str,
    title: str = "",
    choices: list[str] = [],
    multiselect: bool = False
) -> Union[str, list[str]]:
    """
    listbox - caller stub for singleton GUIwrapperClass object method

    Args:
        text (str): prompt text
        title (str): title for popup. Defaults to empty string.
        choices (List[str]): Choices for listbox. Defaults to [].
        multiselect (bool): Flag for multi-select mode. Defaults to False.

    Returns:
        Union[str, List[str]]: selected option(s)
    """
    return GUIwrapper.listbox(text, title, choices, multiselect)

# generalized message box for confirmations
def confirmYesNo(text: str, title: str = "", buttons: list = ['Yes', 'No']) -> str:
    """
    confirmYesNo - caller stub for singleton GUIwrapperClass object method

    Args:
        text (str): prompt text
        title (str): title for popup. Defaults to empty string.
        buttons (list): label for buttons. Defaults to ['Yes', 'No'].

    Returns:
        str: label of pressed button
    """
    return GUIwrapper.confirmYesNo(text, title, buttons)

def confirm_yes_no(text: str, title: str = "", buttons: list = ['Yes', 'No']) -> str:
    """
    confirm_yes_no - caller stub for singleton GUIwrapperClass object method

    Args:
        text (str): prompt text
        title (str): title for popup. Defaults to empty string.
        buttons (list): label for buttons. Defaults to ['Yes', 'No'].

    Returns:
        str: label of pressed button
    """
    return confirmYesNo(text, title, buttons)


# standard call stubs used throughout programs

# template for ready
def exitFinished(title: str = "") -> None:
    """
    exitFinished - dummy finished message box.

    Args:
        title (str): title for message box. Defaults to empty string.
    """
    msg: str = "Fertig."

    GUIwrapper.alertbox(msg, title)

def exit_finished(title: str = "") -> None:
    """
    exit_finished - dummy finished message box.

    Args:
        title (str): title for message box. Defaults to empty string.
    """
    exitFinished(title)
