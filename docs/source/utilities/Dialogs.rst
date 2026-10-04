Dialogs
=======

The Dialogs utility module provides ready-made **blocking** functions for messages,
confirmations, simple questions, file, directory, color, and font selection.

Use these functions when the application needs a short, blocking interaction or
for important feedback or decisions that require the user's attention.

For persistent status information, routine feedback, or complex forms,
use :doc:`/widgets/CTkToast` or a dedicated :doc:`/containers/CTkToplevel` instead.


Basic Popup
-----------

.. py:function:: showinfo(title, message[, detail]) -> None:

   .. image:: images/showinfo.png
      :alt: showinfo examples
      :align: right
      :width: 200px

   Shows a popup with a message and the "info" icon.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|



.. py:function:: showwarning(title, message[, detail]) -> None:

   .. image:: images/showwarning.png
      :alt: showwarning examples
      :align: right
      :width: 200px

   Shows a popup with a message and the "warning" icon.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|



.. py:function:: showerror(title, message[, detail]) -> None:

   .. image:: images/showerror.png
      :alt: showerror examples
      :align: right
      :width: 200px

   Shows a popup with a message and the "error" icon.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|



.. py:function:: askquestion(answers, title, message[, detail][, default][, icon]) -> str:

   Opens a popup where the user can select among different answers;
   returns the selected answer.

   :type answers: 'abortretryignore' | 'ok' | 'okcancel' | 'retrycancel' | 'yesno' | 'yesnocancel'
   :param answers:
      Allows configuring the labels on the buttons that the user can click.

      It also changes the possible values that are returned by the function.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



.. py:function:: askokcancel(title, message[, detail][, default][, icon]) -> bool:

   .. image:: images/askokcancel.png
      :alt: askokcancel examples
      :align: center
      :width: 200px

   Opens a popup where the user can select between ``OK`` and ``Cancel``;
   returns ``True`` if the selected answer is ``OK``.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



.. py:function:: askyesno(title, message[, detail][, default][, icon]) -> bool:

   .. image:: images/askyesno.png
      :alt: askyesno examples
      :align: center
      :width: 200px

   Opens a popup where the user can select between ``Yes`` and ``No``;
   returns ``True`` if the selected answer is ``Yes``.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



.. py:function:: askyesnocancel(title, message[, detail][, default][, icon]) -> bool | None:

   .. image:: images/askyesnocancel.png
      :alt: askyesnocancel examples
      :align: center
      :width: 200px

   Opens a popup where the user can select between ``Yes``, ``No`` and ``Cancel``;
   returns ``True`` if the selected answer is ``Yes``, ``None`` in case of ``Cancel``.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



.. py:function:: askretrycancel(title, message[, detail][, default][, icon]) -> bool:

   .. image:: images/askretrycancel.png
      :alt: askretrycancel examples
      :align: center
      :width: 200px

   Opens a popup where the user can select between ``Retry`` and ``Cancel``;
   returns ``True`` if the selected answer is ``Retry``.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



.. py:function:: askabortretryignore(title, message[, detail][, default][, icon]) -> str:

   .. image:: images/askabortretryignore.png
      :alt: askabortretryignore examples
      :align: center
      :width: 200px

   Opens a popup where the user can select between ``Abort``, ``Retry`` and ``Ignore``;
   returns the selected answer.

   :param str title:
      |title_description|

   :param str message:
      |message_description|

   :type detail: str | None
   :param detail:
      |detail_description|

   :param str default:
      |default_description|

   :type icon: 'error' | 'info' | 'question' | 'warning'
   :param icon:
      |icon_description|

   :returns:
      |returns_description|



Files and Directories
---------------------

.. py:function:: askdirectory([title][, initialdir][, mustexist]) -> str:

   .. image:: images/askdirectory.png
      :alt: askdirectory examples
      :align: center
      :width: 300px

   Opens a popup where the user can select a directory;
   returns the full path or an empty string if the popup was closed.

   :param str title:
      |title_description|

   :param str initialdir:
      |initialdir_description|

   :param bool mustexist:
      If set to ``False``, allows the user to enter the name of a folder that doesn't exist.

   :returns:
      The path of the selected folder or ``""``.



.. py:function:: askopenfilename([title][, filetypes][, initialtype][, initialdir][, initialfile][, defaultextension]) -> str:

   .. image:: images/askopenfilename.png
      :alt: askopenfilename examples
      :align: center
      :width: 300px

   Opens a popup where the user can select **one file** to be read;
   returns the full path or an empty string if the popup was closed.

   :param str title:
      |title_description|

   :type filetypes: Iterable[tuple[str, str]]
   :param filetypes:
      .. include:: /arguments/filetypes.rst

   :param str initialtype:
      |initialtype_description|

   :param str initialdir:
      |initialdir_description|

   :param str initialfile:
      |initialfile_description|

   :param str defaultextension:
      |defaultextension_description|

   :returns:
      The path of the selected file or ``""``.



.. py:function:: askopenfilenames([title][, filetypes][, initialtype][, initialdir][, initialfile][, defaultextension]) -> tuple[str, ...]:

   Opens a popup where the user can select **multiple files** to be read;
   returns a tuple containing all selected full paths or an empty tuple if the popup was closed.

   :param str title:
      |title_description|

   :type filetypes: Iterable[tuple[str, str]]
   :param filetypes:
      .. include:: /arguments/filetypes.rst

   :param str initialtype:
      |initialtype_description|

   :param str initialdir:
      |initialdir_description|

   :param str initialfile:
      |initialfile_description|

   :param str defaultextension:
      |defaultextension_description|

   :returns:
      A tuple containing the selected file paths or ``()``.



.. py:function:: asksaveasfilename([title][, filetypes][, initialtype][, initialdir][, initialfile][, defaultextension][, confirmoverwrite]) -> str:

   .. image:: images/asksaveasfilename.png
      :alt: asksaveasfilename examples
      :align: center
      :width: 300px

   Opens a popup where the user can select a file to be written;
   returns the full path or an empty string if the popup was closed.

   :param str title:
      |title_description|

   :type filetypes: Iterable[tuple[str, str]]
   :param filetypes:
      .. include:: /arguments/filetypes.rst

   :param str initialtype:
      |initialtype_description|

   :param str initialdir:
      |initialdir_description|

   :param str initialfile:
      |initialfile_description|

   :param str defaultextension:
      |defaultextension_description|

   :param bool confirmoverwrite:
      If set to ``False``, allows suppressing the overwrite warning that appears
      if the user selects an already existing file.

   :returns:
      The path of the selected file or ``""``.



Colors
------

.. py:function:: askcolor([title][, initialcolor]) -> str | None:

   .. image:: images/askcolor.png
      :alt: askcolor examples
      :align: center
      :width: 300px

   Opens a popup where the user can select a color;
   returns the selected color as a hex-string (``"#RRGGBB"``)
   or ``None`` if the popup was closed.

   :param str title:
      |title_description|

   :type initialcolor: str | None
   :param initialcolor:
      |initialcolor_description|

   :returns:
      The hex-string of the selected color or ``None``.



.. py:function:: askrgbcolor([title][, initialcolor]) -> tuple[int, int, int] | None:

   Opens a popup where the user can select a color;
   returns the selected color as a tuple ``(R, G, B)``
   or ``None`` if the popup was closed.

   :param str title:
      |title_description|

   :type initialcolor: tuple[int, int, int] | None
   :param initialcolor:
      |initialcolor_description|

   :returns:
      The RGB-tuple of the selected color or ``None``.



Fonts
-----

.. py:function:: askfont([title][, initialfont][, master]) -> tuple[str, int, str] | None:

   .. image:: images/askfont.png
      :alt: askfont examples
      :align: center
      :width: 300px

   Opens a popup where the user can select a font;
   returns the selected font as a tuple ``(<name>, <size>, <modifiers>)``
   or ``None`` if the popup was closed.

   | On some platforms (mainly macOS), it doesn't wait for the popup to be closed before returning.
   | In that case, the popup behaves as a separate Toplevel that remains always visible until closed.

   On old Python versions, ``master`` must be provided.

   :param str title:
      |title_description|

   :type initialfont: tuple[str, int, str] | None
   :param initialfont:
      Font that will be pre-selected,
      so the user can just press ENTER to confirm it.

   :type master: tkinter.Misc | None
   :param master:
      Any widget that is used to invoke custom "tk/tlc" commands.

      On new Python versions, ``tkinter`` itself provides an API to get a widget,
      so you can omit this parameter.

   :returns:
      The tuple containing the elements of the selected font or ``None``.




.. |title_description| replace::
   Text to be displayed in the popup title bar.

.. |message_description| replace::
   Text to be displayed in the middle of the popup.

.. |detail_description| replace::
   Text to be displayed below the main message text.

.. |default_description| replace::
   Allows choosing which button will have the focus,
   so that if the user presses ENTER immediately,
   it will be the selected answer.

.. |icon_description| replace::
   The icon to be shown on the left of the message text.

.. |returns_description| replace::
   The label of the clicked button.

.. |initialdir_description| replace::
   Folder that will already be visible,
   from which the user can start their search.

.. |initialtype_description| replace::
   Since the selected "filetype" is always the first one provided,
   you can specify an extension with this parameter, and the corresponding
   type will be placed first so that it ends up being active.

.. |initialfile_description| replace::
   File that will be pre-selected,
   so the user can just press ENTER to confirm it.

.. |defaultextension_description| replace::
   Specifies a default file extension to add if the user types a filename without a period.
   It doesn't work well with ``filetypes``.

.. |initialcolor_description| replace::
   Color that will be pre-selected,
   so the user can just press ENTER to confirm it.
