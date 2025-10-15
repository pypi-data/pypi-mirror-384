from pexpect import pxssh
import typing
import time
import io
import re


class InteractiveSSHSession:
    """
    An iteractive session with a host over SSH.
    This class simulates an actual SSH session opened by running the `ssh` command on a CLI,
    rather than implementing the SSH protocol in code (i.e from the host's point of view,
    it looks just like someone typed the text from a terminal)
    This is performed through pexpect, which allows us to run `ssh` as a process and interact with it programmatically.
    Using this method over an in-code implementation of the SSH protocol allows us to simulate an SSH session exactly
    and avoids complications with certain types of inputs (i.e. password prompts), though we sacrifice the ability to
    receive status codes. The user is expected to parse outputs of commands (or use alternative methods such as `echo $?`)
    to determine to status of any command run.

    :param hostname: The IP or hostname of the host to connect to.
    :param username: The username to use over SSH.
    :param password: The password to use for the SSH user.
    :param prompt: The console prompt, if known. Specifying the console prompt here exactly will improve performance as it avoids
            having to auto-detect the prompt. This should be specified as a regex unless `prompt_exact=True`
            This prompt is used to determine the boundaries between commands and to determine when a command finishes.
    :param prompt_exact: Whether or not the `prompt` parameter should be treated as a literal or as a regular expression. Setting this
            to `True` will treat the prompt as a literal to be matched exactly, and `False` will treat the prompt as a regex string.
    :param encoding: Encoding to use for reading the SSH output.
    """

    def __init__(self, hostname: str, username: str, password: str, prompt: typing.Optional[str] = None, prompt_exact: bool = False, encoding: str = "utf-8"):
        self.username = username
        self.hostname = hostname
        self.password = password
        self.encoding = encoding
        self.output = io.StringIO()
        self.prompt = re.escape(prompt) if prompt and prompt_exact else prompt
        self._proc: typing.Optional[pxssh.pxssh] = None

    def open(self):
        self._proc = pxssh.pxssh(options={"StrictHostKeyChecking": "no", "UserKnownHostsFile": "/dev/null"}, encoding=self.encoding)
        self.output = io.StringIO()
        self._proc.logfile_read = self.output
        self._proc.force_password = True

        kwargs = {
            "server": self.hostname,
            "username": self.username,
            "password": self.password,
            "auto_prompt_reset": False if self.prompt else True,
            "sync_original_prompt": False if self.prompt else True,
        }
        if self.prompt:
            kwargs["original_prompt"] = self.prompt
            self._proc.PROMPT = self.prompt

        try:
            self._proc.login(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to log into interactive SSH session: {str(e)}")
        return self

    def close(self):
        if not self._proc:
            return
        try:
            self._proc.logout()
        except:
            pass
        self._proc.close()
        self.output.close()
        self._proc = None

    def wait(self, retries: int = 60, delay: int = 2, keep_open: bool = False) -> bool:
        """
        Waits until this connection can be established, and then establishes the connection.

        :param retries: How many times to retry connecting before exiting.
        :param delay: How long to pause between retries in seconds.
        :param keep_open: Whether or not the keep the connection open. If `True`, it is left to the user to close the connection.

        :return: Whether or not the connection could be established
        """
        for i in range(retries):
            if i != 0:
                time.sleep(delay)
            try:
                self.open()
                if not keep_open:
                    self.close()
                return True
            except Exception:
                continue
        return False

    def wait_for_string(self, s: str, timeout: int = 30):
        """
        Wait for an exact string to be present in the output.

        :param s: The string to expect.
        :param timeout: The maximum amount of time to wait before raising an error.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        try:
            self._proc.expect_exact(s, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to wait for string {s}: {str(e)}\nAvailable Output: {self.get_all_output()}")

    def wait_for_prompt(self, timeout: int = 30):
        """
        Wait for the prompt to be available.

        :param timeout: The maximum amount of time to wait before raising an error.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        try:
            if not self._proc.prompt(timeout=timeout):
                raise TimeoutError("Timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to wait for prompt: {str(e)}\nAvailable Output: {self.get_all_output()}")

    def wait_for_pattern(self, pattern: str, timeout: int = 30):
        """
        Wait for a regex pattern to be present in the output.

        :param pattern: The regex pattern as a string to expect.
        :param timeout: The maximum amount of time to wait before raising an error.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        try:
            self._proc.expect(pattern=pattern, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to wait for pattern {pattern}: {str(e)}\nAvailable Output: {self.get_all_output()}")

    def write(self, s: str):
        """
        Write a string to the session console.

        :param s: The string to write.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        self._proc.send(s)

    def writeline(self, s: str):
        """
        Write a string to the session console as a line (i.e. simulate an "enter" key press after writing).

        :param s: The string to write.

        :return: self
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        self._proc.sendline(s)

    def command(self, command: str, timeout: int = 60):
        """
        Utility function to run a single command and get the output.
        This is just a wrapper around calls to `writeline`, `wait_for_prompt`, and `get_output`

        :param command: The command to run.
        :param timeout: The maximum amount of time to wait for the prompt before raising an error.

        :return: The output of the command run.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")
        self.writeline(command)
        self.wait_for_prompt(timeout=timeout)
        return self.get_output()

    def get_output(self):
        """
        Get the output of the most recently run command or sequence of operations.

        :return: The most recent output from the session.
        """
        if not self._proc:
            raise RuntimeError(f"Interactive SSH session is not open.")

        # Attempt to parse between PROMPTs
        prompt_regex = re.compile(self._proc.PROMPT)
        all_output = self.get_all_output()
        if len(all_output) == 0 or prompt_regex.search(all_output) is None:
            return all_output
        lines = all_output.split("\n")
        lines.reverse()
        if prompt_regex.search(lines[0]):
            # Remove the last line if it's the prompt; this indicates the end of a recently run command
            # We want to get the contents of the command output, so we ignore this last line
            lines = lines[1:]
        output_lines = []
        for line in lines:
            if prompt_regex.search(line):
                # Found a match with the prompt, end here; this should be the start of the command
                break
            output_lines.append(line)
        output_lines.reverse()  # We added the lines in reverse order, so we have to reverse to get the correct order
        return "\n".join(output_lines)

    def get_all_output(self):
        """
        Get the entire output of the session since its initialization.

        :return: The entire output of the session.
        """
        return self.output.getvalue()

    def __str__(self):
        return f"<{type(self).__name__} {self.username}@{self.hostname}>"

    def __repr__(self):
        return str(self)
