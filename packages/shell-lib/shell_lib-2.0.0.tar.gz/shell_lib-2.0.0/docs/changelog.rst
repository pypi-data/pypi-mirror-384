Links
~~~~~

`Documentation <https://shell-lib.readthedocs.io>`_ | `PyPI page <https://pypi.org/project/shell-lib>`_ | `Repository <https://bitbucket.org/wjssz/shell_lib>`_

shell-lib changelog
~~~~~~~~~~~~~~~~~~~

2.0.0 (2025 Oct 15)
^^^^^^^^^^^^^^^^^^^

1. Add ``shell_lib.powershell`` sub-module:

.. code:: python

   from shell_lib.powershell import pwsh
   pwsh("pip freeze | foreach-object { pip install --upgrade $_.split('==')[0] }")
   pwsh.run_file(["a.ps1"])
   pwsh.run_file(["a.ps1", "-param1", "value1", "-param2", "value2"])

2. Support quoting argument using
   `t-string <https://docs.python.org/3/whatsnew/3.14.html#pep-750-template-string-literals>`_
   on Python 3.14+:

.. code:: python

   package = input("Please input package name:")

   from shell_lib import sh
   # no command injection attack
   sh(t"pip install {package}")

   from shell_lib.powershell import pwsh
   # no command injection attack
   pwsh(t"pip install {package}")

1.2.12 (2025 Oct 7)
^^^^^^^^^^^^^^^^^^^

Fix ``sh.get_hostname()`` wrongly return cluster name on Windows.

1.2.9 (2025 Oct 6)
^^^^^^^^^^^^^^^^^^

Add ``sh.get_hostname()`` method.

1.2.8 (2025 Oct 2)
^^^^^^^^^^^^^^^^^^

On Windows 7+, print colored messages. Python 3.7/3.8 support Windows 7.

On POSIX, printing colored messages is more good-looking, and more
friendly to redirected stdout / stderr.

Fix ``os.unsetenv()`` doesn’t exist on Windows + Python 3.7/3.8.

Fix positional-only parameter doesn’t work on Python 3.7.

1.2.7 (2025 Sep 28)
^^^^^^^^^^^^^^^^^^^

1. On Windows and Python 3.12+, ``PathInfo.ctime`` uses
   ```.st_birthtime`` <https://docs.python.org/3/library/os.html#os.stat_result.st_ctime>`__.

2. Polish the code, unit-tests, doc.

1.2.6 (2025 Sep 23)
^^^^^^^^^^^^^^^^^^^

Fix ``sh()`` / ``sh.safe_run()`` wrongly always use “utf-8” for text
encoding/decoding when in Python UTF-8 mode. This mainly affects Python
UTF-8 mode on Windows.

1.2.5 (2025 Sep 22)
^^^^^^^^^^^^^^^^^^^

Improve ``sh.get_username()`` method, more reliable on Windows.

1.2.4 (2025 Sep 21)
^^^^^^^^^^^^^^^^^^^

Improve ``sh.get_locale_encoding()`` method again, more reliable.

.. _sep-21-1:

1.2.3 (2025 Sep 21)
^^^^^^^^^^^^^^^^^^^

Improve ``sh.get_locale_encoding()`` method, more reliable.

.. _sep-21-2:

1.2.2 (2025 Sep 21)
^^^^^^^^^^^^^^^^^^^

Add ``sh.get_locale_encoding()`` method, get the system locale encoding.

If Python is in UTF-8 mode, the existing ``sh.get_preferred_encoding()``
method always return \`utf-8’, so add this method.

.. _sep-21-3:

1.2.1 (2025 Sep 21)
^^^^^^^^^^^^^^^^^^^

Allow running in Python UTF-8 Mode.

.. _sep-21-4:

1.2.0 (2025 Sep 21)
^^^^^^^^^^^^^^^^^^^

1. Add ``sh.get_env()`` method, get an environment variable value. It’s
   more reliable than ``os.getenv()``.

2. Add ``sh.set_env()`` method, set environment variable(s), can be used
   as a context manager for automatically restore.

3. Can’t run in Python UTF-8 Mode. Many operations may be unreliable due
   to the mandatory use of UTF-8 encoding.

1.1.0 (2025 Sep 17)
^^^^^^^^^^^^^^^^^^^

1. Add ``sh.is_link(path)`` method, check if a path is a symlink.

2. Add ``sh.get_file_size(path)`` method, get file size.

3. ``sh.get_path_info()`` returns a ``PathInfo`` object. Remove
   ``PathInfo.permissions`` attribute. Add ``.is_readable``,
   ``.is_writable``, ``.is_executable`` attributes, represents the
   abilities to the current user.

1.0.3 (2025 Sep 16)
^^^^^^^^^^^^^^^^^^^

Polish doc and docstrings.

1.0.2 (2025 Sep 15)
^^^^^^^^^^^^^^^^^^^

1. ``sh()`` and ``sh.safe_run()`` always print “Execute:” or “Safely
   execute:”, the ``alternative_title=""`` can no longer turn off the
   printing.

2. Print path more clearly.

.. _sep-15-1:

1.0.1 (2025 Sep 15)
^^^^^^^^^^^^^^^^^^^

``sh.get_path_info(path)`` function returns a ``PathInfo`` object.

On Windows, ``PathInfo.permissions`` attribute now is a 1-character
``str``, it looks like “7”, which only represents the current user is
readable, writable, executable.

On other systems, it’s still a 3-character ``str``, looks like “755”.
