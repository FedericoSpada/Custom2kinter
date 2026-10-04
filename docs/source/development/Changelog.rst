Changelog
=========

All notable changes to this project are reported in the following.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`__,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`__.


[Unreleased]
------------

Added
~~~~~

-  Added new widgets: ``CTkFloatingFrame``, ``CTkToolTip``, ``CTkSpinBox``, ``CTkToggleButton``,
   ``CTkSymbolBox``, ``CTkGridView``, ``CTkSectionView``, ``CTkListBox``, and ``CTkToast``.
-  Added base classes ``CTkContainer``, ``CTkScrollable``, ``CTkToggleable``, ``EntryLike``,
   ``TextLike``, and ``CanvasWithLabel``.
-  Added ``apply_scaling`` parameter to all geometry methods to allow providing values already scaled.
-  Added ``orientation`` and managed negative ``border_width`` to ``CTkSwitch``.
-  Added ``default_value`` and ``values`` to ``CTkInputDialog``.
-  Added ``compound`` to ``CTkComboBox``, ``CTkOptionMenu``, ``CTkCheckBox``, ``CTkSwitch``,
   and ``CTkRadioButton``.
-  Added ``anchor`` and ``justify`` to ``CTkCheckBox``, ``CTkSwitch``, ``CTkRadioButton``,
   and ``CTkSegmentedButton``.
-  Added ``pre_command`` to all widgets that have ``command``.
-  Added ``scrollable_width``, ``scrollable_height``, ``fit_content``, ``see()`` and ``is_visible()``
   to ``CTkScrollableFrame``.
-  Added ``box_width`` and ``box_height`` to ``CTkSegmentedButton`` to specify the minimal
   dimensions of each button.
-  Added ``view()`` methods to ``CTkScrollbar`` and ``CTkScrollableFrame``.
-  Added ``scrollincrement`` to allow changing how much each widget scrolls.
-  Added ``"single_run"`` mode to ``CTkProgressBar``.
-  Added a method to retrieve buttons for ``CTkSegmentedButton`` and ``CTkTabview`` so as to
   configure them individually.
-  Added different modes for ``CTkComboBox`` and ``CTkSlider``.
-  Added some text in the middle of ``CTkProgressBar``.
-  Added a little "x" button to ``CTkEntry`` that the user can click to clear the content of the widget.
-  Added ``get_window_scaling()`` and ``get_widget_scaling()`` to return the values previously
   provided with the corresponding "set" methods.
-  Recreated tkinter dialogs with proper type hints and documentation.
-  Managed fonts assigned to tags for ``CTkTextbox``.
-  Managed ``orientation="both"`` for ``CTkScrollableFrame`` and made the scrollbars visible only
   when needed.
-  Allowed to specify ``0`` as width and height for a ``CTkImage``, which are then set so as to
   maintain the original aspect ratio.
-  Implemented a way to specify the value of a setting with a reference to another property.
-  Supported custom fonts on macOS.
-  Added many more themes.
-  Added Type hints to the whole project.

Changed
~~~~~~~

-  Reworked ``DrawEngine`` to be class-based.
-  Improved ``ThemeManager`` to output a dict that is created by combining multiple keys and
   additional values coming from the parameters.
-  Moved as many arguments as possible into the Theme files.
-  Improved the management of the windows' icons, allowing the use of a ``CTkImage`` too.
-  Better managed ``compound="center"`` for ``CTkLabel``.
-  Changed the ``bind()`` method to apply the binding wisely based on the type of the event
   (this solved rapid invocations of the ``_on_leave()`` and ``_on_enter()`` callbacks).
-  Changed ``unbind()`` methods to allow removing a single callback if ``funcid`` is provided
   (returned by the ``bind()`` method).
-  Allowed the use of ``bind_all()`` and ``unbind_all()`` methods, since they don't interfere
   with internal callbacks and they have always been enabled on ``CTk`` and ``CTkToplevel``.
-  Renamed ``CTkBaseClass`` to ``CTkWidget``.
-  Renamed ``fg_color`` and ``progress_color`` to ``fg_color_unchecked`` and ``fg_color_checked``
   for ``CTkSwitch``.
-  Renamed ``activate_scrollbars`` arguments to ``show_scrollbars`` for uniformity.
-  Renamed widget-specific arguments with generic names (e.g. ``checkbox_width`` |r_arrow| ``box_width``).
-  Reworked ``CTkProgressBar`` arguments to improve clarity.
-  Fixed appearance of multiple errors if the program doesn't terminate immediately after ``mainloop()``.

Removed
~~~~~~~

-  Removed the ability to change the Drawing Method for ``CTkFrame``.
-  Removed ``dynamic_resizing`` from ``CTkOptionMenu`` and ``CTkSegmentedButton``.
-  Removed ``button_corner_radius`` from ``CTkSlider`` in favor of a unique ``corner_radius``.
-  Removed private parameter ``from_variable_callback`` from public APIs.
-  Removed ``block_update_dimensions_event`` management since it used ``False``
   for both "block" and "unblock" methods.
-  Removed ``focus_set()`` in the management of the color titlebar on Windows.
   This solves the problem where the ``CTk`` raises above a newly opened ``CTkToplevel``.


[5.3.0] - 2026-04-12
--------------------

Added
~~~~~

-  Added Showroom App, immediately available with the library installation.
-  Added Gold theme.
-  Added ``set()``, ``index()``, ``len()`` for those widgets that were suitable to use them.
-  Added ``orientation`` to ``CTkSegmentedButton`` to make it vertically instead of horizontally.
-  Added an attribute to ``CTkTabview`` to configure the font for its ``CTkSegmentedButton``.
-  Added the possibility to add a border to ``CTkLabel``.
-  Added the Mouse Wheel detection to ``CTkSlider`` and improved it on ``CTkScrollbar``.

Changed
~~~~~~~

-  ``CTkButton`` triggers the command when the Mouse Button is released.
-  ``CTkEntry`` and ``CTkTextbox`` lose focus when you click somewhere else.
-  Clicking the Dropdown button again closes the menu for ``CTkComboBox`` and ``CTkOptionMenu``.
-  Improved/fixed ``configure()`` and ``cget()`` for all widgets.
-  Improved Tab renaming for ``CTkTabview``.
-  Improved drag behavior for ``CTkScrollbar``.
-  Properly managed borders for ``CTkScrollableFrame``.
-  Fixed a bug that prevented setting a custom icon for ``CTkToplevel``.
-  Fixed many bugs related to missing invocations or wrong names.


[5.2.0] - 2023-06-19
--------------------

Added
~~~~~

-  Mostly bug fixes.


[5.1.0] - 2023-02-05
--------------------

Added
~~~~~

-  Added ``CTkScrollableFrame``.

Changed
~~~~~~~

-  Changed license to MIT.


[5.0.0] - 2022-11-13
--------------------

Added
~~~~~

-  Added ``CTkTextbox`` with automatic x and y scrollbars, corner_radius,
   border_width, border_spacing.
-  Added ``CTkSegmentedButton``.
-  Added ``CTkTabview``.
-  Added ``cget()`` method to all widgets and windows.
-  Added ``bind()`` and ``focus()`` methods to almost all widgets.
-  Added anchor option to ``CTkButton`` to position image and text inside the button.
-  Added anchor option to ``CTkOptionMenu`` and justify option to ``CTkComboBox``.
-  Added ``CTkFont`` class.
-  Added ``CTkImage`` class to replace ``PIL.ImageTk.PhotoImage``:
   supports scaling and two images for appearance mode, supports configuring.
-  Added missing configure options for multiple widgets.

Changed
~~~~~~~

-  Changed value for transparent colors (same as background) from ``None``
   to ``"transparent"``.
-  Changed ``text_font`` attribute to ``font`` in all widgets, changed
   ``dropdown_text_font`` to ``dropdown_font``.
-  Changed ``dropdown_color`` to ``dropdown_fg_color`` for
   ``CTkComboBox`` and ``CTkOptionMenu``.
-  Changed ``orient`` to ``orientation`` for ``CTkProgressBar`` and ``CTkSlider``.
-  ``width`` and ``height`` of ``CTkCheckBox``, ``CTkRadioButton``, ``CTkSwitch``
   now describe the outer dimensions of the whole widget. The button/switch size
   is described by separate attributes like ``checkbox_width``, ``checkbox_height``.
-  ``font`` attribute must be a tuple or ``CTkFont`` now, all size values are
   measured in pixel now.
-  Changed dictionary key ``window_bg_color`` to ``window`` in theme files.
-  ``CTkInputDialog`` attributes completely changed.
-  Renamed ``scrollbar_color``, ``scrollbar_hover_color``
   to ``button_color``, ``button_hover_color`` for ``CTkScrollbar``.

Removed
~~~~~~~

-  Removed setter and getter functions like ``set_text()`` in ``CTkButton``.
-  Removed ``bg`` and ``background`` attributes from ``CTk`` and ``CTkToplevel``,
   always use ``fg_color``.
-  Removed ``Settings`` class and moved settings to widget and window classes.
-  Removed ``customtkinter.set_spacing_scaling()``, now ``set_widget_scaling()``
   is used for spacing too.


[4.6.0] - 2022-09-17
--------------------

Added
~~~~~

-  ``CTkProgressBar`` indeterminate mode, automatic progress loop with ``start()`` and ``stop()``.


[4.5.0] - 2022-06-23
--------------------

Added
~~~~~

-  ``CTkScrollbar`` (vertical, horizontal).


[4.4.0] - 2022-06-14
--------------------

Changed
~~~~~~~

-  Changed custom dropdown menu to normal tkinter.Menu because of
   multiple platform specific bugs.


[4.3.0] - 2022-06-01
--------------------

Added
~~~~~

-  Added ``CTkComboBox``.
-  Small fixes for new dropdown menu.


[4.2.0] - 2022-05-30
--------------------

Added
~~~~~

-  ``CTkOptionMenu`` with custom dropdown menu.
-  Support for clicking on labels of ``CTkCheckBox``, ``CTkRadioButton``, ``CTkSwitch``.


[4.1.0] - 2022-05-24
--------------------

Added
~~~~~

-  Configure width and height for ``CTkFrame``, ``CTkButton``, ``CTkLabel``,
   ``CTkProgressBar``, ``CTkSlider``, ``CTkEntry``.


[4.0.0] - 2022-05-22
--------------------

Added
~~~~~

-  This changelog file.
-  Adopted semantic versioning.
-  Added HighDPI scaling to all widgets and geometry managers (place, pack, grid).
-  Restructured ``CTkSettings`` and renamed a few manager classes.
-  Added ``orientation`` attribute to ``CTkSlider`` and ``CTkProgressBar``.

Removed
~~~~~~~

-  A few unnecessary tests.
