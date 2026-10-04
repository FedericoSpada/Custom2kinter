CTkRadioButton
==============

.. image:: images/CTkRadioButton.png
   :alt: CTkRadioButton examples
   :align: center
   :height: 80px

The ``CTkRadioButton`` widget represents one option in a group of mutually exclusive choices.

Use several radio buttons with the same :py:attr:`variable` when exactly
one value must be selected and all options should be visible at once.

For a compact group of a few mutually exclusive options, :doc:`/widgets/CTkSegmentedButton`
can provide the same selection model with less vertical space.
For independent choices, use :doc:`/widgets/CTkCheckBox`, :doc:`/widgets/CTkSwitch`
or :doc:`/widgets/CTkToggleButton` instead.


Example Code
------------

.. code:: python

   def callback(new_value: int) -> None:
       print("radiobutton toggled, current value:", new_value)

   var = ctk.IntVar(value=1)
   radiobutton_1 = ctk.CTkRadioButton(app,
                                      text="option 1",
                                      value=1,
                                      variable=var,
                                      command=callback)
   radiobutton_2 = ctk.CTkRadioButton(app,
                                      text="option 2",
                                      value=2,
                                      variable=var,
                                      command=callback)


.. py:class:: CTkRadioButton
   :hidden:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/master.rst
   .. include:: /arguments/theme_key.rst

   Functionality
   ~~~~~~~~~~~~~

   .. include:: /arguments/state.rst

   .. py:attribute:: value
      :type: int | float | str | bool
      :value: 0

      Value assigned to the :py:attr:`variable` when the widget's internal state is "on".


   .. py:attribute:: variable
      :type: IntVar | DoubleVar | StringVar | BooleanVar | None
      :value: None

      Allows linking this widget to an ``IntVar``, ``DoubleVar``, ``StringVar`` or ``BooleanVar`` object
      that can be shared among many widgets.

      |variable_description|

      The widget internal state is "on" if the ``variable`` content is exactly equal to :py:attr:`value`;
      otherwise, it is "off".

   .. include:: /arguments/textvariable.rst

   .. py:attribute:: pre_command
      :type: ((int | float | str | bool) -> ('break' | None)) | None
      :value: None

      Function that is invoked when the user clicks on the widget,
      but **before** the widget changes the internal state to "on".
      It receives :py:attr:`value` as its only parameter.

      If the function returns exactly ``"break"``, the state change is not performed
      and :py:attr:`command` is not invoked at all.

   .. py:attribute:: command
      :type: ((int | float | str | bool) -> None) | None
      :value: None

      Function that is invoked when the user clicks on the widget,
      but **after** the widget changed the internal state to "on".
      It receives :py:attr:`value` as its only parameter.

      If the function specified by :py:attr:`pre_command` returned ``"break"``,
      this function is not invoked.

   Themed
   ~~~~~~

   .. include:: /arguments/widtheight.rst
   .. include:: /arguments/box_widtheight.rst
   .. include:: /arguments/corner_radius.rst

   .. py:attribute:: border_width_checked
      :type: int

      Width of the widget's border in |unscaled pixels| when the internal state is "on".

   .. py:attribute:: border_width_unchecked
      :type: int

      Width of the widget's border in |unscaled pixels| when the internal state is "off".

   .. py:attribute:: internal_spacing
      :type: int

      Space in |unscaled pixels| between the label and the graphical element displaying the selection state.

      .. note::
         If no text is shown, this argument has no effect.

   .. include:: /arguments/bg_color.rst
   .. include:: /arguments/fg_color.rst
   .. include:: /arguments/border_color.rst
   .. include:: /arguments/hover_color.rst
   .. include:: /arguments/text_color.rst
   .. include:: /arguments/text_color_disabled.rst
   .. include:: /arguments/hover.rst
   .. include:: /arguments/text.rst
   .. include:: /arguments/font.rst
   .. include:: /arguments/anchor.rst
   .. include:: /arguments/justify.rst

   .. py:attribute:: compound
      :type: 'left' | 'right' | 'top' | 'bottom'

      Specifies the graphical element's position relative to the text label.

      .. note::
         If no text is shown, this argument has no effect.


   Methods
   -------

   .. py:method:: get() -> bool:

      Returns the current internal state of the widget.

      :returns:
         Whether the internal state is "on".



   .. py:method:: invoke() -> None:

      Changes the internal status to "on"
      if the widget's :py:attr:`state` is not ``"disabled"``
      and the :py:attr:`pre_command` doesn't return ``"break"``.

      It can be called to simulate the user who clicks on the widget.



   .. py:method:: set(value | state) -> None:

      Allows changing the internal state programmatically by providing
      either a value to be compared with :py:attr:`value`,
      or a boolean state where ``True`` is "on" and ``False`` is "off".

      The change is performed regardless of the widget's :py:attr:`state`.

      |no_callbacks|

      :type value: int | float | str | bool | None
      :param value:
         The new internal state will be "on" if this parameter is equal to :py:attr:`value`, "off" otherwise.

         Do not provide this parameter or set it to ``None`` if you want to use the ``state`` parameter.

      :type state: bool | None
      :param state:
         The new internal state will be "on" if this parameter is ``True``, "off" otherwise.



   .. py:method:: select() -> None:

      Syntactic sugar for :py:meth:`set()` invoked with ``state=True``.



   .. py:method:: deselect() -> None:

      Syntactic sugar for :py:meth:`set()` invoked with ``state=False``.


   Inherited
   ~~~~~~~~~

   .. include:: /methods/widget.rst
   .. include:: /methods/geometry_manager.rst
