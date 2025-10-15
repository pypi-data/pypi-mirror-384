import shutil
import subprocess
from base64 import b64encode
from typing import List, Union, Optional

from ..shell_lib import IS_WINDOWS, Template, quote_template, \
                        cr, print_cr, sh

__all__ = ("pwsh", "quote_pwsh")

if IS_WINDOWS and shutil.which("pwsh") is None:
    PS_CMD = "powershell"
else:
    PS_CMD = "pwsh"

def quote_pwsh(s: str) -> str:
    """
    Quote PowerShell argument.
    This function only works in shell-lib module.
    """
    # https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules
    s = s.replace("'", "''")
    s = s.replace("‘", "‘‘")
    s = s.replace("’", "’’")
    return f"'{s}'"

class PowerShell:
    def __call__(self, command: Union[str, Template], *,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 alternative_title: Optional[str] = None,
                 print_output: bool = True,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Run a PowerShell command.

        If command fails, by default, it raises a
        `subprocess.CalledProcessError` exception. For commands that may fail,
        use `fail_on_error=False`, then check the exit-code `ret.returncode`.

        If `print_output` is True, stdout and stderr will be printed to the
        console. If it's False, stdout and stderr will be saved in return
        value's .stdout / .stderr attributes.

        :param command: The command str.
        :param text: If True, output is decoded as text.
        :param input: Data to be sent to the child process.
        :param timeout: Timeout in seconds.
        :param alternative_title: Print this instead of the command.
        :param print_output: If True, print stdout and stderr to the console.
        :param fail_on_error: If True, raise a subprocess.CalledProcessError
                              on failure.
        :return: A subprocess.CompletedProcess object.
        """
        if isinstance(command, str):
            pass
        elif isinstance(command, Template):
            command = quote_template(command, quote_pwsh)
        else:
            raise TypeError("command should be a str object.")
        print_cr(cr("PowerShell:"), command
                                    if alternative_title is None
                                    else alternative_title)

        b = command.encode("utf_16_le")
        base64_cmd = b64encode(b).decode("ascii")
        cmd = f"{PS_CMD} -EncodedCommand {base64_cmd}"
        encoding = sh.get_locale_encoding() if text else None
        return subprocess.run(
                cmd,
                input=input,
                capture_output=not print_output,
                shell=False, # quote_pwsh only works for False
                timeout=timeout,
                check=fail_on_error,
                encoding=encoding)

    def run_file(self, command: List[str], *,
                 text: bool = True,
                 input: Union[str, bytes, None] = None,
                 timeout: Union[int, float, None] = None,
                 alternative_title: Optional[str] = None,
                 print_output: bool = True,
                 fail_on_error: bool = True) -> subprocess.CompletedProcess:
        """
        Run a PowerShell script file.

        If command fails, by default, it raises a
        `subprocess.CalledProcessError` exception. For commands that may fail,
        use `fail_on_error=False`, then check the exit-code `ret.returncode`.

        If `print_output` is True, stdout and stderr will be printed to the
        console. If it's False, stdout and stderr will be saved in return
        value's .stdout / .stderr attributes.

        :param command: A list of str, the first item is the script path, the
                        others are parameters passed to the script.
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
            raise TypeError("command should be a list object.")
        print_cr(cr("PowerShell file:"), command
                                         if alternative_title is None
                                         else alternative_title)

        cmd = [PS_CMD, "-File"] + command
        encoding = sh.get_locale_encoding() if text else None
        return subprocess.run(
                cmd,
                input=input,
                capture_output=not print_output,
                shell=False,
                timeout=timeout,
                check=fail_on_error,
                encoding=encoding)

pwsh = PowerShell()