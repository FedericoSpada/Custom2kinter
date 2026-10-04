An iterable of 2-element tuples where:

- The first element represents a basic name for the type
  that will be displayed in a dropdown menu.
- The second element reports all extensions associated
  with the common name, separated by spaces.

It is good practice to end the list with ``("All files", ".*")``.

e.g.: ``filetypes = [("Supported Images", ".jpg .jpeg .png .bmp"), ("Comma-separated values", ".csv"), ("All files", ".*")]``
