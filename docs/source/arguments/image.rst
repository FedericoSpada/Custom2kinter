.. py:attribute:: image
   :type: CTkImage | CTkImageArgs | tuple | str | None
   :value: None

   Image to be displayed.

   It can be a:

   - instance of :doc:`/utilities/CTkImage`;
   - dictionary containing valid :ref:`CTkImage arguments <image_arguments>`;
   - tuple with 3 elements ``(<path>, <width>, <height>)``;
   - tuple with 4 elements ``(<light_path>, <dark_path>, <width>, <height>)``;
   - string representing a custom theme key.
