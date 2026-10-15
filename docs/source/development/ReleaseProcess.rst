Release Process
===============

Here is the list of steps to publish a new version of the Library.

It is here mainly for the maintainers to remember what to do.


Final Commit
------------

Commit any final changes and update the Changelog.


Create tag on GitHub
--------------------

After installing the ``tbump`` package::

   python -m pip install tbump

you can run the command
(add ``--dry-run`` or ``--only-patch`` for a test run without performing any permanent actions)::

   tbump X.X.X

where ``X.X.X`` is the new Library version.


Publish on PyPI
---------------

Make sure you have the latest versions installed::

   python -m pip install --upgrade pip
   python -m pip install --upgrade build
   python -m pip install --upgrade twine

Remove a previous build::

   rmdir /s /q custom2kinter.egg-info
   rmdir /s /q dist

Run the build command::

   python -m build

Upload the build
(add ``--repository testpypi`` to upload it to the TestPyPI server)::

   python -m twine upload dist/*

To download the library from ``TestPyPI``, you can run::

   python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ custom2kinter
