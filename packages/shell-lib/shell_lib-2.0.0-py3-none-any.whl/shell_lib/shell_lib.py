# Co-created with Google Gemini
import os
import re
import sys
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Generator, Union, Optional, overload

PathTypes = Union[str, bytes, Path]
FS_ENCODING = sys.getfilesystemencoding()
IS_WINDOWS = (sys.platform == "win32")

# Quote argument
if sys.version_info >= (3, 14, 0, 'beta', 1):
    from string.templatelib import Template, Interpolation
    def quote_template(t, quote_arg):
        parts = []
        for part in t:
            if isinstance(part, Interpolation):
                parts.append(quote_arg(part.value))
            else:
                parts.append(part)
        return "".join(parts)
else:
    class Template: # type: ignore [no-redef]
        pass
    def quote_template(t, quote_arg):
        pass

if IS_WINDOWS:
    # This doesn't work for many cases, but better than nothing.
    # If you encounter a problem, use shell_lib.powershell sub-module.
    def quote_sh(s: str) -> str:
        s = s.replace('"', '""')
        return f'"{s}"'
else:
    import shlex
    def quote_sh(s: str) -> str:
        return shlex.quote(s)

# Print colored message
class cr(str):
    pass

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    # Lazy define
    GetACP = None
    GetUserNameW = None
    IsUserAnAdmin = None

    # Get stdout/stderr handle
    GetStdHandle = ctypes.windll.kernel32.GetStdHandle
    GetStdHandle.argtypes = [wintypes.DWORD]
    GetStdHandle.restype = wintypes.HANDLE

    h_stdout = GetStdHandle(-11)
    if h_stdout == wintypes.HANDLE(-1):
        h_stdout = None

    h_stderr = GetStdHandle(-12)
    if h_stderr == wintypes.HANDLE(-1):
        h_stderr = None

    # Get console attribute
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes._COORD),
            ("dwCursorPosition", wintypes._COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", wintypes._COORD)]

    GetConsoleScreenBufferInfo = ctypes.windll.kernel32.GetConsoleScreenBufferInfo
    GetConsoleScreenBufferInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
    GetConsoleScreenBufferInfo.restype = wintypes.BOOL

    def _get_console_attrs(handle):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        if GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi)):
            return csbi.wAttributes
        else:
            return 7 # The default gray color

    # Set console attribute
    SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
    SetConsoleTextAttribute.argtypes = [wintypes.HANDLE, wintypes.WORD]
    SetConsoleTextAttribute.restype = wintypes.BOOL

    def print_cr(*args, sep=" ", end="\n", file=None):
        handle = None
        if file is None:
            file = sys.stdout
            # stdout, stderr, __stdout__, __stderr__ can be None. It's usually
            # the case for Windows GUI apps that aren't connected to a console
            # and Python apps started with pythonw.
            if file is sys.__stdout__ and file is not None:
                handle = h_stdout
        else:
            if file is sys.__stderr__:
                handle = h_stderr
            elif file is sys.__stdout__:
                handle = h_stdout

        if handle is None:
            print(*args, sep=sep, end=end, file=file, flush=True)
            return

        attrs = None
        for i, arg in enumerate(args):
            if i > 0:
                file.write(sep)
            if isinstance(arg, cr):
                file.flush()
                if attrs is None:
                    attrs = _get_console_attrs(handle)
                SetConsoleTextAttribute(handle, 6)
                file.write(arg)
                file.flush()
                SetConsoleTextAttribute(handle, attrs)
            else:
                arg = str(arg)
                file.write(arg)
        file.write(end)
        file.flush()
else:
    def _posix_cr(s):
        if isinstance(s, cr):
            return f"\033[93m{s}\033[0m"
        else:
            return s

    def print_cr(*args, sep=" ", end="\n", file=None):
        if file is None:
            if sys.stdout is sys.__stdout__:
                color = True
            else:
                color = False
        else:
            if file is sys.__stderr__ or file is sys.__stdout__:
                color = True
            else:
                color = False

        if color:
            args = [_posix_cr(arg) for arg in args]
        print(*args, sep=sep, end=end, file=file, flush=True)

class PathInfo:
    """
    A class that encapsulates information about a file or directory.
    """
    def __init__(self, path: PathTypes, size: int,
                 ctime: datetime, mtime: datetime, atime: datetime,
                 is_dir: bool, is_file: bool, is_link: bool,
                 is_readable: bool, is_writable: bool, is_executable: bool):
        self.path: str = path.decode(FS_ENCODING) \
                            if isinstance(path, bytes) \
                            else str(path)
        """
        Path, a str object.
        """
        self.size: int = size
        """
        If path is a file, file size.
        If path is a directory, space used by the directory entry itself.
        """
        self.ctime: datetime = ctime
        """
        On POSIX systems, it's the time of the last metadata change.
        On Windows, it's the creation time.
        """
        self.mtime: datetime = mtime
        """
        Time of last modification.
        """
        self.atime: datetime = atime
        """
        Time of last access.
        """
        self.is_dir: bool = is_dir
        """
        Path is a directory, or a symlink pointing to a directory.
        """
        self.is_file: bool = is_file
        """
        Path is a file, or a symlink pointing to a file.
        """
        self.is_link: bool = is_link
        """
        Path is a symlink.
        """
        self.is_readable: bool = is_readable
        """
        Path is readable for the current user.
        """
        self.is_writable: bool = is_writable
        """
        Path is writable for the current user.
        """
        self.is_executable: bool = is_executable
        """
        Path is executable for the current user.
        """

    def __repr__(self):
        s = (f"PathInfo(path={self.path}, size={self.size}, "
             f"ctime={self.ctime}, mtime={self.mtime}, atime={self.atime}, "
             f"is_dir={self.is_dir}, is_file={self.is_file}, is_link={self.is_link}, "
             f"is_readable={self.is_readable}, "
             f"is_writable={self.is_writable}, "
             f"is_executable={self.is_executable})")
        return s

class CDContextManager:
    def __init__(self, path: Union[PathTypes, None]) -> None:
        self.original_cwd = os.getcwd()
        if path is not None:
            print_cr(cr("Change directory to:"), path)
            os.chdir(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print_cr(cr("Restore directory to:"), self.original_cwd)
        os.chdir(self.original_cwd)

class SetEnvContextManager:
    def __init__(self, *args) -> None:
        if len(args) == 2:
            k = args[0]
            v = args[1]
            self.original_envs = [(k, self.reliable_getenv(k))]
            self._set_env(k, v, True)
        elif len(args) == 1 and isinstance(args[0], dict):
            self.original_envs = []
            for k, v in args[0].items():
                self.original_envs.append((k, self.reliable_getenv(k)))
                self._set_env(k, v, True)
        else:
            raise TypeError("Wrong arguments")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.original_envs:
            self._set_env(k, v, False)

    @staticmethod
    def _set_env(k, v, set):
        op = "Set" if set else "Restore"
        if v is None:
            print_cr(cr(f"{op} environment variable '"), k,
                     cr("' to none (remove)."), sep="")
            if k in os.environ:
                del os.environ[k]
            else:
                if IS_WINDOWS and sys.version_info < (3, 9):
                    os.putenv(k, "")
                else:
                    os.unsetenv(k)
        else:
            print_cr(cr(f"{op} environment variable '"), k,
                     cr("' to '"), v, cr("'."), sep="")
            os.environ[k] = v

    _getenv_fun = None

    # os.getenv() is unreliable:
    # 1. It gets environment variable from os.envrion object. But when using
    #    os.putenv(), os.unsetenv() or other unrecognized methods to modify
    #    environment variable, the changes will not be reflected in os.envrion.
    # 2. If user modifies environment variables through os.envrion object,
    #    then there is no problem. But can't guarantee user always do so.
    # reliable_getenv() can reliably get environment variable.
    @classmethod
    def reliable_getenv(cls, key: str) -> Union[str, None]:
        if not isinstance(key, str):
            raise TypeError("Environment variable name should be a str object.")

        try:
            if IS_WINDOWS:
                if cls._getenv_fun is None:
                    _fun = ctypes.windll.kernel32.GetEnvironmentVariableW
                    _fun.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    _fun.restype = wintypes.DWORD
                    cls._getenv_fun = _fun
                n = cls._getenv_fun(key, None, 0)
                if n == 0:
                    error = ctypes.GetLastError()
                    if error == 203: # ERROR_ENVVAR_NOT_FOUND
                        return None
                    raise RuntimeError(f"GetEnvironmentVariableW() error: {error}")
                buf = ctypes.create_unicode_buffer(n)
                if cls._getenv_fun(key, buf, n):
                    return buf.value
                else:
                    raise ctypes.WinError()
            else:
                if cls._getenv_fun is None:
                    from ctypes.util import find_library
                    from ctypes import CDLL, c_char_p
                    libc_path = find_library("c")
                    libc = CDLL(libc_path)
                    _fun = libc.getenv
                    _fun.argtypes = [c_char_p]
                    _fun.restype = c_char_p
                    cls._getenv_fun = _fun
                # os.getenv() also uses sys.getfilesystemencoding() and
                # "surrogateescape" for keys and values on Unix-like systems.
                result = cls._getenv_fun(key.encode(FS_ENCODING, "surrogateescape"))
                if result:
                    return result.decode(FS_ENCODING, "surrogateescape")
                else:
                    return None
        except Exception as e:
            print(f"SetEnvContextManager.reliable_getenv() error occurred: {e}", file=sys.stderr)

            py_code = ("import os,sys;v=os.getenv(sys.argv[1]);"
                       "print('N' if v is None else 'V',v,sep='',end='',flush=1)")
            v = subprocess.run(
                [sys.executable, "-c", py_code, key],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False, check=True,
                encoding=sh.get_locale_encoding()).stdout
            if v.startswith("V"):
                return v[1:]
            elif v.startswith("N"):
                return None
            raise RuntimeError("Impossible print")

class Shell:
    """
    A class that encapsulates file system operations, executing shell commands,
    user interactions, and obtaining runtime information.
    """
    def __setattr__(self, name, _):
        raise AttributeError(f"Can't set attribute {name!r}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, subprocess.CalledProcessError):
                exit_code = exc_val.returncode
                print_cr(cr(f"\nError: Command failed with exit code "), exit_code,
                         cr("."), sep="", file=sys.stderr)
            else:
                exit_code = 1

            import traceback
            traceback.print_exception(exc_type, exc_val, exc_tb, file=sys.stderr)
            self.exit(exit_code)

    # --- File and Directory Operations API ---
    def home_dir(self) -> Path:
        """
        Return the current user's home directory, a pathlib.Path object.
        """
        return Path.home()

    def path(self, path: PathTypes) -> Path:
        """
        Convert a str/bytes path to a pathlib.Path object.
        """
        if isinstance(path, bytes):
            path = path.decode(FS_ENCODING)
        return Path(path)

    def create_dir(self, path: PathTypes, *, exist_ok: bool = False) -> None:
        """
        Create directory, make all intermediate-level directories needed to
        contain the leaf directory.

        :param path: The path of the directory to create.
        :param exist_ok: If True, existing directory will not raise an error.
        """
        print_cr(cr("Create directory:"), path)
        os.makedirs(path, exist_ok=exist_ok)

    def remove_file(self, path: PathTypes, *, ignore_missing: bool = False) -> None:
        """
        Remove a file.

        :param path: The path of the file to remove.
        :param ignore_missing: If True, no error is raised if the file is
                               missing.
        """
        print_cr(cr("Remove file:"), path)
        if os.path.isdir(path):
            raise IsADirectoryError(f"File path '{path!s}' is a directory.")
        if ignore_missing and not os.path.isfile(path):
            return
        os.remove(path)

    def remove_dir(self, path: PathTypes, *, ignore_missing: bool = False) -> None:
        """
        Recursively remove a directory and its contents.

        :param path: The path of the directory to remove.
        :param ignore_missing: If True, no error is raised if the directory is
                               missing.
        """
        print_cr(cr("Remove directory:"), path)
        if ignore_missing and not os.path.isdir(path):
            return
        shutil.rmtree(path)

    def clear_dir(self, path: PathTypes) -> None:
        """
        Clear the contents of a directory.

        :param path: The path of the directory to clear.
        """
        print_cr(cr("Clear directory contents:"), path)
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        shutil.rmtree(entry.path)
                    else:
                        os.unlink(entry.path) # File or symlink
                except FileNotFoundError:
                    continue

    def copy_file(self, src: PathTypes, dst: PathTypes, *, remove_existing_dst: bool = False) -> None:
        """
        Copy a file.

        :param src: The source file path.
        :param dst: The destination file path.
        :param remove_existing_dst: If True, overwrites the destination if it
                                    exists.
        """
        print_cr(cr("Copy file from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isdir(src):
            raise IsADirectoryError(f"Source file '{src!s}' is a directory.")
        if not remove_existing_dst and os.path.isfile(dst):
            raise FileExistsError(f"Destination file '{dst!s}' already exists.")

        shutil.copy2(src, dst) # type: ignore

    def copy_dir(self, src: PathTypes, dst: PathTypes, *, remove_existing_dst: bool = False) -> None:
        """
        Copy a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        :param remove_existing_dst: If True, removes the exist destination
                                    before copying.
        """
        print_cr(cr("Copy directory from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isfile(src):
            raise NotADirectoryError(f"Source directory '{src!s}' is a file.")
        if os.path.isdir(dst):
            if not remove_existing_dst:
                raise FileExistsError(f"Destination directory '{dst!s}' already exists.")
            shutil.rmtree(dst)

        shutil.copytree(src, dst) # type: ignore

    def move_file(self, src: PathTypes, dst: PathTypes, *, remove_existing_dst: bool = False) -> None:
        """
        Move a file.

        :param src: The source file path.
        :param dst: The destination file path.
        :param remove_existing_dst: If True, overwrites the destination if it
                                    exists.
        """
        print_cr(cr("Move file from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isdir(src):
            raise IsADirectoryError(f"Source file '{src!s}' is a directory.")
        if os.path.isfile(dst):
            if not remove_existing_dst:
                raise FileExistsError(f"Destination file '{dst!s}' already exists.")
            os.remove(dst)

        # Fix bug in Python 3.8-, see bpo-32689.
        if sys.version_info < (3, 9) and isinstance(src, Path):
            src = str(src)

        shutil.move(src, dst) # type: ignore

    def move_dir(self, src: PathTypes, dst: PathTypes, *, remove_existing_dst: bool = False) -> None:
        """
        Move a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        :param remove_existing_dst: If True, removes the exist destination
                                    before moving.
        """
        print_cr(cr("Move directory from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isfile(src):
            raise NotADirectoryError(f"Source directory '{src!s}' is a file.")
        if os.path.isdir(dst):
            if not remove_existing_dst:
                raise FileExistsError(f"Destination directory '{dst!s}' already exists.")
            shutil.rmtree(dst)

        shutil.move(src, dst) # type: ignore

    def rename_file(self, src: PathTypes, dst: PathTypes) -> None:
        """
        Rename a file.

        :param src: The source file path.
        :param dst: The destination file path.
        """
        print_cr(cr("Rename file from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isdir(src):
            raise IsADirectoryError(f"Source file '{src!s}' is a directory.")
        if os.path.isdir(dst):
            raise FileExistsError(f"Destination file '{dst!s}' is an existing directory.")
        if os.path.isfile(dst):
            raise FileExistsError(f"Destination file '{dst!s}' already exists.")
        os.rename(src, dst)

    def rename_dir(self, src: PathTypes, dst: PathTypes) -> None:
        """
        Rename a directory.

        :param src: The source directory path.
        :param dst: The destination directory path.
        """
        print_cr(cr("Rename directory from '"), src, cr("' to '"), dst, cr("'."), sep="")
        if os.path.isfile(src):
            raise NotADirectoryError(f"Source directory '{src!s}' is a file.")
        if os.path.isfile(dst):
            raise FileExistsError(f"Destination directory '{dst!s}' is an existing file.")
        if os.path.isdir(dst):
            raise FileExistsError(f"Destination directory '{dst!s}' already exists.")
        os.rename(src, dst)

    def get_file_size(self, path: PathTypes) -> int:
        """
        Get the size of a file.

        :param path: The file path.
        :return: File size.
        """
        if os.path.isdir(path):
            raise IsADirectoryError(f"Path '{path!s}' is a directory.")
        return os.path.getsize(path)

    def get_path_info(self, path: PathTypes) -> PathInfo:
        """
        Retrieve detailed information about an existing file or directory.

        :param path: The path of the file or directory.
        :return: A PathInfo object containing detailed information.
        """
        stats = os.stat(path)
        mode = stats.st_mode
        if IS_WINDOWS and sys.version_info >= (3, 12, 0, 'beta', 1):
            ctime = stats.st_birthtime
        else:
            ctime = stats.st_ctime

        return PathInfo(
            path = path,
            size = stats.st_size,
            ctime = datetime.fromtimestamp(ctime),
            mtime = datetime.fromtimestamp(stats.st_mtime),
            atime = datetime.fromtimestamp(stats.st_atime),
            is_dir = stat.S_ISDIR(mode),
            is_file = stat.S_ISREG(mode),
            is_link = os.path.islink(path),
            is_readable = os.access(path, os.R_OK),
            is_writable = os.access(path, os.W_OK),
            is_executable = os.access(path, os.X_OK)
        )

    @overload
    def list_dir(self, path: Union[str, Path]) -> List[str]:
        ...

    @overload
    def list_dir(self, path: bytes) -> List[bytes]:
        ...

    def list_dir(self, path):
        """
        List all files and subdirectories within a directory.

        :param path: The directory path.
        :return: A list of all entry names.
        """
        return os.listdir(path)

    @overload
    def walk_dir(self, path: Union[str, Path],
                 top_down: bool = True) -> Generator[Tuple[str, str], None, None]:
        ...

    @overload
    def walk_dir(self, path: bytes,
                 top_down: bool = True) -> Generator[Tuple[bytes, bytes], None, None]:
        ...

    def walk_dir(self, path, top_down = True):
        """
        A generator that traverses a directory and all its subdirectories,
        yielding (directory_path, filename) tuples.

        :param path: The root directory to start walking from.
        :param top_down: Traverse direction.
        :yields: (dirpath, filename) tuples of str or bytes, depending on the
                 input type.
        """
        def _exception(exc):
            print_cr(cr("sh.walk_dir() failed for path:"), path, file=sys.stderr)
            raise exc

        for dirpath, dirnames, filenames in os.walk(path,
                                                    topdown=top_down,
                                                    onerror=_exception):
            for filename in filenames:
                yield (dirpath, filename)

    def cd(self, path: Union[PathTypes, None]):
        """
        Change the current working directory.

        It can be used as a context manager (`with` statement).
        The previous working directory will be restored automatically upon
        exiting the `with` block, even if an exception occurs.

        :param path: The path to the directory to change to.
                     None means no change, using the 'with' statement ensures
                     returning to the current directory.
        :return: A CDContextManager object.
        """
        return CDContextManager(path)

    def path_exists(self, path: PathTypes) -> bool:
        """
        Check if a path exists.

        :param path: The file or directory path.
        :return: True if the path exists, False otherwise.
        """
        return os.path.exists(path)

    def is_file(self, path: PathTypes) -> bool:
        """
        Check if a path is a file, or a symlink pointing to a file.

        :param path: The file path.
        :return: True if the path is a file, False otherwise.
        """
        return os.path.isfile(path)

    def is_dir(self, path: PathTypes) -> bool:
        """
        Check if a path is a directory, or a symlink pointing to a directory.

        :param path: The directory path.
        :return: True if the path is a directory, False otherwise.
        """
        return os.path.isdir(path)

    def is_link(self, path: PathTypes) -> bool:
        """
        Return True if path is a symbolic link.

        Always False if symbolic links are not supported by the Python
        runtime.
        """
        return os.path.islink(path)

    def split_path(self, path: PathTypes) -> Union[Tuple[str, str], Tuple[bytes, bytes]]:
        """
        Split a path into its directory name and file name.

        :param path: The file or directory path.
        :return: A 2-element tuple containing (directory name, file name).
        """
        return os.path.split(path)

    @overload
    def join_path(self, *paths: Union[str, Path]) -> str:
        ...

    @overload
    def join_path(self, *paths: bytes) -> bytes:
        ...

    def join_path(self, *paths):
        """
        Safely join path components.

        :param paths: Path components to join.
        :return: The joined path string.
        """
        return os.path.join(*paths)

    # --- Shell Command Execution API ---
    def __call__(self,
                 command: Union[str, Template], *,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 alternative_title: Optional[str] = None,
                 print_output: bool = True,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Run a shell command using `shell=True`. Command can use shell features
        like pipe and redirection.

        If command fails, by default, it raises a
        `subprocess.CalledProcessError` exception. For commands that may fail,
        use `fail_on_error=False`, then check the exit-code `ret.returncode`.

        If `print_output` is True, stdout and stderr will be printed to the
        console. If it's False, stdout and stderr will be saved in return
        value's .stdout / .stderr attributes.

        :param command: The command string to execute.
        :param text: If True, output is decoded as text.
        :param input: Data to be sent to the child process.
        :param timeout: Timeout in seconds.
        :param alternative_title: Print this instead of the command.
        :param print_output: If True, print stdout and stderr to the console.
        :param fail_on_error: If True, raise a subprocess.CalledProcessError
                              on failure.
        :return: A subprocess.CompletedProcess object.
        """
        if isinstance(command, Template):
            command = quote_template(command, quote_sh)
        print_cr(cr("Execute:"), command
                                 if alternative_title is None
                                 else alternative_title)
        encoding = self.get_locale_encoding() if text else None
        return subprocess.run(
                command,
                input=input,
                capture_output=not print_output,
                shell=True,
                timeout=timeout,
                check=fail_on_error,
                encoding=encoding)

    def safe_run(self,
                 command: List[str], *,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 alternative_title: Optional[str] = None,
                 print_output: bool = True,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Run a command safely, using `shell=False`. Used for commands containing
        external input to prevent shell injection.

        If command fails, by default, it raises a
        `subprocess.CalledProcessError` exception. For commands that may fail,
        use `fail_on_error=False`, then check the exit-code `ret.returncode`.

        If `print_output` is True, stdout and stderr will be printed to the
        console. If it's False, stdout and stderr will be saved in return
        value's .stdout / .stderr attributes.

        :param command: The command as a list of strings
                        (e.g., ['rm', 'file.txt']).
        :param text: If True, output is decoded as text.
        :param input: Data to be sent to the child process.
        :param timeout: Timeout in seconds.
        :param alternative_title: Print this instead of the command.
        :param print_output: If True, print stdout and stderr to the console.
        :param fail_on_error: If True, raise a subprocess.CalledProcessError
                              on failure.
        :return: A subprocess.CompletedProcess object.
        """
        if not isinstance(command, list):
            raise TypeError("command should be a list of str to ensure security.")

        print_cr(cr("Safely execute:"), command
                                        if alternative_title is None
                                        else alternative_title)
        encoding = self.get_locale_encoding() if text else None
        return subprocess.run(
                command,
                input=input,
                capture_output=not print_output,
                shell=False,
                timeout=timeout,
                check=fail_on_error,
                encoding=encoding)

    # --- Script Control API ---
    def pause(self, msg: Optional[str] = None) -> None:
        """
        Prompt the user to press any key to continue.

        :param msg: The message to print.
        """
        if msg:
            print_cr(cr(msg))
        print_cr(cr("Press any key to continue..."), end="")

        if IS_WINDOWS:
            import msvcrt
            msvcrt.getch()
        else:
            import termios, tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print()

    def ask_choice(self, title: str, *choices: str) -> int:
        """
        Display a menu and get the choice from user.

        :param title: The title for the menu.
        :param choices: The choices as a tuple of strings.
        :return: The 1-based index of the user's choice.
        """
        if not choices:
            raise ValueError("Must have at least one choice.")

        print_cr(cr(title))
        for i, choice in enumerate(choices, 1):
            print_cr(cr(f"{i},"), choice)

        while True:
            print_cr(cr("Please choose: "), end="")
            answer = input()
            try:
                index = int(answer)
            except ValueError:
                print_cr(cr("Invalid input. Please input a number."))
                continue

            if 1 <= index <= len(choices):
                return index
            print_cr(cr(f"Invalid choice. Please input a number from 1 to {len(choices)}."))

    def ask_yes_no(self, title: str) -> bool:
        """
        Ask user to answer yes or no.

        :param title: The message to display.
        :return: True for yes, False for no.
        """
        print_cr(cr(title))
        while True:
            print_cr(cr("Please answer yes(y) or no(n): "), end="")
            answer = input().strip().lower()
            if answer in ("yes", "y"):
                return True
            elif answer in ("no", "n"):
                return False
            print_cr(cr("Invalid answer. Please input yes/y/no/n."))

    def ask_regex_input(self, title: str, pattern: str, *,
                        print_pattern: bool = False) -> re.Match:
        """
        Ask user to input a string, and verify it with a regex pattern.

        :param title: The message to display.
        :param pattern: The regex pattern.
        :param print_pattern: Whether to print the regex pattern.
        :return: The re.Match object.
        """
        print_cr(cr(title))
        if print_pattern:
            print_cr(cr(f"Input for regex:"), pattern)

        while True:
            print_cr(cr("Please input: "), end="")
            answer = input()
            m = re.fullmatch(pattern, answer)
            if m:
                return m
            print_cr(cr("Invalid input. Please input for this regex:"), pattern)

    def ask_password(self, title: str = "Please input password") -> str:
        """
        Ask user to input a password, which is not echoed on the screen.

        :param title: The message to display, no ":" at the end.
        :return: The password str.
        """
        from getpass import getpass
        print_cr(cr(title + ": "), end="")
        return getpass("")

    def exit(self, exit_code: int = 0) -> None:
        """
        Exit the script with a specified exit code.

        :param exit_code: The exit code, defaults to 0 (no error).
                          Non-zero means an error occurred.
        """
        sys.exit(exit_code)

    # Host name type constants
    HOSTNAME_TYPE_Host = 1
    """
    Host name.
    """
    HOSTNAME_TYPE_FQDN = 2
    """
    Fully qualified domain name. If domain name is available, return
    HostName.DomainName. Otherwise, only return HostName.
    """

    def get_hostname(self, hostname_type: int = HOSTNAME_TYPE_Host) -> str:
        """
        Get the host name.

        :param hostname_type: Can be `sh.HOSTNAME_TYPE_Host` or
                              `sh.HOSTNAME_TYPE_FQDN`.
        :return: Host name.
        """
        import socket
        if hostname_type == self.HOSTNAME_TYPE_Host:
            return socket.gethostname()
        elif hostname_type == self.HOSTNAME_TYPE_FQDN:
            return socket.getfqdn()
        else:
            raise ValueError("Wrong hostname_type argument.")

    def get_username(self) -> str:
        """
        Get the current username.

        On POSIX:
        ```
        command              sh.get_username()  sh.home_dir().name
        ./script.py          username           username
        sudo -E ./script.py  root               username
        sudo ./script.py     root               root
        ```
        """
        try:
            if os.name == "posix":  # macOS, Linux, etc.
                import pwd
                uid = os.getuid()
                return pwd.getpwuid(uid).pw_name
            elif IS_WINDOWS:
                global GetUserNameW
                if GetUserNameW is None:
                    GetUserNameW = ctypes.windll.advapi32.GetUserNameW
                    GetUserNameW.argtypes = [wintypes.LPWSTR, wintypes.LPDWORD]
                    GetUserNameW.restype = wintypes.BOOL
                size = ctypes.c_uint32(0)
                GetUserNameW(None, ctypes.byref(size))
                win_un = ctypes.create_unicode_buffer(size.value)
                if GetUserNameW(win_un, ctypes.byref(size)):
                    return win_un.value
                else:
                    raise ctypes.WinError()
        except Exception as e:
            print(f"sh.get_username() error occurred: {e}", file=sys.stderr)

        # Fall back to environment variable
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            username = os.environ.get(name)
            if username:
                return username
        raise RuntimeError("Unable to get the current username.")

    def is_elevated(self) -> bool:
        """
        Check if the script is running with elevated (admin/root) privilege.
        """
        if os.name == "posix": # macOS, Linux, etc.
            return os.geteuid() == 0
        elif IS_WINDOWS:
            global IsUserAnAdmin
            if IsUserAnAdmin is None:
                IsUserAnAdmin = ctypes.windll.shell32.IsUserAnAdmin
                IsUserAnAdmin.argtypes = []
                IsUserAnAdmin.restype = wintypes.BOOL
            return bool(IsUserAnAdmin())

        raise RuntimeError(f"Unable to get privilege status.")

    def get_preferred_encoding(self) -> str:
        """
        Return the preferred encoding.

        This is used for decoding subprocess output or files that don't specify
        an encoding.

        If Python UTF-8 mode is enabled, return utf-8. Otherwise, return the
        system locale encoding.
        """
        import locale
        return locale.getpreferredencoding(False)

    def get_locale_encoding(self) -> str:
        """
        Return the system locale encoding.

        It's not affected by Python UTF-8 mode.
        """
        import locale
        if sys.version_info >= (3, 11, 0, 'beta', 1):
            return locale.getencoding()

        if IS_WINDOWS:
            global GetACP
            if GetACP is None:
                GetACP = ctypes.windll.kernel32.GetACP
                GetACP.argtypes = []
                GetACP.restype = wintypes.UINT
            code_page = GetACP()
            return f"cp{code_page}"
        elif sys.platform == "android":
            # On Android UTF-8 is always used in mbstowcs() and wcstombs()
            return "utf-8"
        else:
            # First try locale.nl_langinfo()
            try:
                encoding = locale.nl_langinfo(locale.CODESET)
                if not encoding:
                    raise ValueError("nl_langinfo() returns empty string.")
                return encoding
            except Exception as e:
                print(f"sh.get_locale_encoding() error occurred: {e}", file=sys.stderr)

            # Second try locale.getlocale()
            encoding = locale.getlocale()[1] # type: ignore
            if not encoding:
                raise RuntimeError("Can't get system locale encoding.")
            return encoding

    def get_filesystem_encoding(self) -> str:
        """
        Return the encoding used to convert between str filenames and bytes
        filenames.

        On Windows, return utf-8, unless use legacy mode, see PEP-529.
        """
        return FS_ENCODING

    def get_env(self, key: str, default: Optional[str] = None) -> Union[str, None]:
        """
        Return the value of an environment variable.

        :param key: Environment variable name.
        :param default: Return this if the environment variable doesn't exist.
        :return: Environment variable value (str) or default.
        """
        value = SetEnvContextManager.reliable_getenv(key)
        if value is not None:
            return value
        return default

    @overload
    def set_env(self, key: str, value: Union[str, None]):
        ...

    @overload
    def set_env(self, dict: Dict[str, Union[str, None]]):
        ...

    def set_env(self, *args):
        """
        Set or delete environment variable, the changes affect the current
        process and subprocesses.

        Can be used as a context manager for automatically restore.

        If value is None, delete the environment variable.

        It has two parameter forms:
        ```
        # single key-value pair
        with sh.set_env("KEY", "VALUE"):
            ...

        # multiple key-value pairs dict
        env_dict = {"KEY_1": "VALUE_1",
                    "KEY_2": "VALUE_2"}
        with sh.set_env(env_dict):
            ...
        ```
        :return: A SetEnvContextManager object.
        """
        return SetEnvContextManager(*args)

    # Operating system constants, use different values from HOSTNAME_TYPE_*.
    OS_Windows = 4
    OS_Cygwin = 8
    OS_Linux = 16
    OS_macOS = 32
    OS_Unix = 64
    OS_Unix_like = (OS_Linux | OS_macOS | OS_Unix | OS_Cygwin)
    """
    Unix-like systems, currently includes:
    OS_Linux, OS_macOS, OS_Unix, OS_Cygwin
    """
    _ALL_OS_BITS = (OS_Windows | OS_Unix_like)
    _CURRENT_OS = None

    @classmethod
    def _get_current_os(cls):
        if sys.platform == "win32":
            cls._CURRENT_OS = cls.OS_Windows
        elif sys.platform == "linux":
            cls._CURRENT_OS = cls.OS_Linux
        elif sys.platform == "darwin":
            cls._CURRENT_OS = cls.OS_macOS
        elif sys.platform == "cygwin":
            cls._CURRENT_OS = cls.OS_Cygwin
        else: # Unknown OS
            if os.name == "posix":
                cls._CURRENT_OS = cls.OS_Unix
            else:
                cls._CURRENT_OS = 0

    def is_os(self, os_mask: int) -> bool:
        """
        Test whether it's the operating system specified by the parameter.

        os_mask parameter supports bit OR (|) combination:
        ```
        if sh.is_os(sh.OS_Linux | sh.OS_macOS):
            ...
        elif sh.is_os(sh.OS_Windows):
            ...
        ```

        :param os_mask: Can be sh.OS_Windows, sh.OS_Cygwin, sh.OS_Linux,
                        sh.OS_macOS, sh.OS_Unix, sh.OS_Unix_like.
        """
        if os_mask & ~self._ALL_OS_BITS:
            raise ValueError("Wrong os_mask argument.")

        if self._CURRENT_OS is None:
            self._get_current_os()
        return bool(os_mask & self._CURRENT_OS) # type: ignore

sh = Shell()