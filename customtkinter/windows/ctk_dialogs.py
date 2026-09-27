from __future__ import annotations
import tkinter
from tkinter.commondialog import Dialog
from tkinter.filedialog import Directory, Open, SaveAs
from tkinter.colorchooser import Chooser
from typing import Callable, Iterable
from typing_extensions import Literal, TypeAlias, TypedDict, Unpack

from .widgets.utility import check_kwargs_empty


IconType: TypeAlias = Literal["error", "info", "question", "warning"]
AnswersType: TypeAlias = Literal["abortretryignore", "ok", "okcancel", "retrycancel", "yesno", "yesnocancel"]
ReplyType: TypeAlias = Literal["abort", "retry", "ignore", "ok", "cancel", "yes", "no"]


class CTkMessageDialogArgs(TypedDict, total=False, closed=True):
    icon: IconType
    type: AnswersType
    default: ReplyType
    title: str
    message: str
    detail: str


class CTkMessageDialog(Dialog):
    command  = "tk_messageBox"

    def __init__(self,
                 master: tkinter.Misc | None = None,
                 **kwargs: Unpack[CTkMessageDialogArgs]) -> None:
        super().__init__(master, **kwargs)

    def show(self, **kwargs: Unpack[CTkMessageDialogArgs]) -> ReplyType:
        res = super().show(**kwargs)

        # In some Tcl installations, yes/no is converted into a boolean.
        if isinstance(res, bool):
            return "yes" if res else "no"
        # In others we get a Tcl_Obj.
        else:
            return str(res)



class CTkFontDialogArgs(TypedDict, total=False, closed=True):
    title: str
    initialfont: tuple[str, int, str]
    command: Callable[[tuple[str, int, str]], None] | None


class CTkFontDialog():

    def __init__(self,
                 master: tkinter.Misc | None = None,
                 **kwargs: Unpack[CTkFontDialogArgs]) -> None:

        self.master: tkinter.Misc = tkinter._get_temp_root() if master is None else master
        self._command: Callable[[tuple[str, int, str]], None] | None = kwargs.pop("command", None)
        self._font: tuple[str, int, str] | None = None
        initialfont = kwargs.pop("initialfont", ("Arial", 12, ""))

        self.master.tk.call("tk", "fontchooser", "configure",
                            "-title", kwargs.pop("title", "Select Font"),
                            "-font", self._tuple2str(initialfont),
                            "-command", self.master.register(self._callback))

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

    def show(self) -> None:
        """ On some platforms (mainly macOS), it doesn't wait for the Popup to be closed before returning.\n
        In that case, it behaves as a separate TopLevel that remains always visible until closed. """
        self.master.tk.call("tk", "fontchooser", "show")

    def hide(self) -> None:
        """ Useful only on platforms where 'show' returns immediately. """
        self.master.tk.call("tk", "fontchooser", "hide")

    def get(self) -> tuple[str, int, str] | None:
        """ Returns the font the user selected or None if the Popus has been closed without a selection. """
        return self._font

    def _callback(self, font: str) -> None:
        self._font = self._str2tuple(font)
        if self._command is not None:
            self._command(self._font)

    @staticmethod
    def _tuple2str(font: tuple[str, int, str]) -> str:
        return f"{{{font[0]}}} {font[1]} {font[2]}"

    @staticmethod
    def _str2tuple(font: str) -> tuple[str, int, str]:
        font = font.strip()
        if font.startswith("{"):
            items = font.removeprefix("{").split("}", 1)
            name = items[0]
            items = items[1].strip().split(" ")
            items.insert(0, name)
        else:
            items = font.split(" ")
        return items[0], int(items[1]), " ".join(items[2:])



def showinfo(title: str, message: str, detail: str | None = None) -> None:
    """ Shows a Popup with a message and the 'info' icon. """
    CTkMessageDialog(type="ok", title=title, message=message, detail=detail, icon="info").show()


def showwarning(title: str, message: str, detail: str | None = None) -> None:
    """ Shows a Popup with a message and the 'warning' icon. """
    CTkMessageDialog(type="ok", title=title, message=message, detail=detail, icon="warning").show()


def showerror(title: str, message: str, detail: str | None = None) -> None:
    """ Shows a Popup with a message and the 'error' icon. """
    CTkMessageDialog(type="ok", title=title, message=message, detail=detail, icon="error").show()


def askquestion(answers: AnswersType,
                title: str,
                message: str,
                detail: str | None = None,
                default: ReplyType | None = None,
                icon: IconType = "question") -> ReplyType:
    """ Opens a Popup where the user can select among different answers;
    returns the selected answer. """
    return CTkMessageDialog(type=answers, title=title, message=message, detail=detail, default=default, icon=icon).show()


def askokcancel(title: str,
                message: str,
                detail: str | None = None,
                default: Literal["ok", "cancel"] = "ok",
                icon: IconType = "question") -> bool:
    """ Opens a Popup where the user can select between 'OK' and 'Cancel';
    returns True if the selected answer is 'OK'. """
    res = CTkMessageDialog(type="okcancel", title=title, message=message, detail=detail, default=default, icon=icon).show()
    return res == "ok"


def askyesno(title: str,
             message: str,
             detail: str | None = None,
             default: Literal["yes", "no"] = "yes",
             icon: IconType = "question") -> bool:
    """ Opens a Popup where the user can select between 'Yes' and 'No';
    returns True if the selected answer is 'Yes'. """
    res = CTkMessageDialog(type="yesno", title=title, message=message, detail=detail, default=default, icon=icon).show()
    return res == "yes"


def askyesnocancel(title: str,
                   message: str,
                   detail: str | None = None,
                   default: Literal["yes", "no", "cancel"] = "yes",
                   icon: IconType = "question") -> bool | None:
    """ Opens a Popup where the user can select among 'Yes', 'No', and 'Cancel';
    returns True if the selected answer is 'Yes', None in case of 'Cancel'. """
    res = CTkMessageDialog(type="yesnocancel", title=title, message=message, detail=detail, default=default, icon=icon).show()
    if res == "cancel":
        return None
    else:
        return res == "yes"


def askretrycancel(title: str,
                   message: str,
                   detail: str | None = None,
                   default: Literal["retry", "cancel"] = "retry",
                   icon: IconType = "question") -> bool:
    """ Opens a Popup where the user can select between 'Retry' and 'Cancel';
    returns True if the selected answer is 'Retry'. """
    res = CTkMessageDialog(type="retrycancel", title=title, message=message, detail=detail, default=default, icon=icon).show()
    return res == "retry"


def askabortretryignore(title: str,
                        message: str,
                        detail: str | None = None,
                        default: Literal["abort", "retry", "ignore"] = "retry",
                        icon: IconType = "question") -> Literal["abort", "retry", "ignore"]:
    """ Opens a Popup where the user can select among 'Abort', 'Retry', and 'Ignore';
    returns the selected answer. """
    return CTkMessageDialog(type="abortretryignore", title=title, message=message, detail=detail, default=default, icon=icon).show()


def askdirectory(title: str = "", initialdir: str = "", mustexist: bool = True) -> str:
    """ Opens a Popup where the user can select a directory;
    returns the full path or an empty string if the Popup was closed. """
    return Directory(title=title, initialdir=initialdir, mustexist=mustexist).show()


def askopenfilename(title: str = "",
                    filetypes: Iterable[tuple[str, str]] = (),
                    initialtype: str = "",
                    initialdir: str = "",
                    initialfile: str = "",
                    defaultextension: str = "") -> str:
    """ Opens a Popup where the user can select a file to be read;
    returns the full path or an empty string if the Popup was closed.\n
    'filetypes' is composed of 2-element tuples where the first element represents a basic name
    for the type that will be displayed in a dropdown menu.
    The second element reports all extensions associated with the common name, separated by spaces.
    It is good practice to terminate the list with '("All files", ".*")'.\n
    e.g.: filetypes = [("Supported Images", ".jpg .jpeg .png .bmp"), ("Comma-separated values", ".csv"), ("All files", ".*")]\n
    The selected 'filetype' is always the first one provided. You can specify an extension for 'initialtype',
    and the corresponding type will be placed first so that it results being active. """

    return Open(multiple=False,
                title=title,
                filetypes=_prioritize_filetypes(filetypes, initialtype),
                initialdir=initialdir,
                initialfile=initialfile,
                defaultextension=defaultextension).show()


def askopenfilenames(title: str = "",
                     filetypes: Iterable[tuple[str, str]] = (),
                     initialtype: str = "",
                     initialdir: str = "",
                     initialfile: str = "",
                     defaultextension: str = "") -> tuple[str, ...]:
    """ Opens a Popup where the user can select multiple files to be read;
    returns a tuple containing all selected full paths or an empty tuple if the Popup was closed.\n
    'filetypes' is composed of 2-element tuples where the first element represents a basic name
    for the type that will be displayed in a dropdown menu.
    The second element reports all extensions associated with the common name, separated by spaces.
    It is good practice to terminate the list with '("All files", ".*")'.\n
    e.g.: filetypes = [("Supported Images", ".jpg .jpeg .png .bmp"), ("Comma-separated values", ".csv"), ("All files", ".*")]\n
    The selected 'filetype' is always the first one provided. You can specify an extension for 'initialtype',
    and the corresponding type will be placed first so that it results being active. """

    res = Open(multiple=True,
               title=title,
               filetypes=_prioritize_filetypes(filetypes, initialtype),
               initialdir=initialdir,
               initialfile=initialfile,
               defaultextension=defaultextension).show()
    if isinstance(res, str):
        res = (res,) if res else ()
    return res


def asksaveasfilename(title: str = "",
                      filetypes: Iterable[tuple[str, str]] = (),
                      initialtype: str = "",
                      initialdir: str = "",
                      initialfile: str = "",
                      defaultextension: str = "",
                      confirmoverwrite: bool = True) -> str:
    """ Opens a Popup where the user can select a file to be written;
    returns the full path or an empty string if the Popup was closed.\n
    'filetypes' is composed of 2-element tuples where the first element represents a basic name
    for the type that will be displayed in a dropdown menu.
    The second element reports all extensions associated with the common name, separated by spaces.
    It is good practice to terminate the list with '("All files", ".*")'.\n
    e.g.: filetypes = [("Supported Images", ".jpg .jpeg .png .bmp"), ("Comma-separated values", ".csv"), ("All files", ".*")]\n
    The selected 'filetype' is always the first one provided. You can specify an extension for 'initialtype',
    and the corresponding type will be placed first so that it results being active. """

    return SaveAs(title=title,
                  filetypes=_prioritize_filetypes(filetypes, initialtype),
                  initialdir=initialdir,
                  initialfile=initialfile,
                  defaultextension=defaultextension,
                  confirmoverwrite=confirmoverwrite).show()


def askcolor(title: str = "",
             initialcolor: str | None = None) -> str | None:
    """ Opens a Popup where the user can select a color;
    returns the selected color as a hex-string ("#RRGGBB") or None if the Popup was closed. """
    return Chooser(title=title, initialcolor=initialcolor).show()[1]


def askrgbcolor(title: str = "",
                initialcolor: tuple[int, int, int] | None = None) -> tuple[int, int, int] | None:
    """ Opens a Popup where the user can select a color;
    returns the selected color as a tuple (R, G, B) or None if the Popup was closed. """
    return Chooser(title=title, initialcolor=initialcolor).show()[0]


def askfont(title: str = "",
            initialfont: tuple[str, int, str] | None = None,
            master: tkinter.Misc | None = None) -> tuple[str, int, str] | None:
    """ Opens a Popup where the user can select a font;
    returns the selected font as a tuple (name, size, modifiers) or None if the Popup was closed.\n
    On old Python versions, 'master' must be provided. """
    kwargs = {}
    if title:
        kwargs["title"] = title
    if initialfont:
        kwargs["initialfont"] = initialfont
    fp = CTkFontDialog(master, **kwargs)
    fp.show()
    return fp.get()



def _prioritize_filetypes(filetypes: Iterable[tuple[str, str]], initialtype: str) -> Iterable[tuple[str, str]]:
    if initialtype:
        retval: list[tuple[str, str]] = []
        for filetype in filetypes:
            if initialtype in filetype[1]:
                retval.insert(0, filetype)
            else:
                retval.append(filetype)
        return retval
    else:
        return filetypes
