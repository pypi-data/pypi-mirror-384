from graphex import Boolean, String, Number, Node, InputSocket, OptionalInputSocket, ListInputSocket, OutputSocket, ListOutputSocket, VariableOutputSocket, EnumInputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
import esxi_utils
import typing
import time
import re
import os


class OpenUnixSSHConnection(Node):
    name: str = "Open Unix SSH Connection"
    description: str = "Open an SSH connection to a Unix-like host."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    ip = InputSocket(datatype=String, name="IP", description="The IP to connect to.")
    username = InputSocket(datatype=String, name="Username", description="The username of the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    retries = InputSocket(datatype=Number, name="Retries", description="The maximum number of SSH connection attempts to make before failing.", input_field=10)
    delay = InputSocket(datatype=Number, name="Delay", description="The time to wait between each SSH connection attempt.", input_field=5)
    error_on_failure = InputSocket(
        datatype=Boolean, name="Error on Failure?", description="Whether to raise an error when an SSH connection could not be established.", input_field=True
    )
    keep_open = InputSocket(
        datatype=Boolean,
        name="Keep Connection Open",
        description="Whether to keep the connection open so that a usable SSH connection object is returned. If this is False, the 'SSH Connection' output will be disabled.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Connection Available", description="Whether a connection could be established to the host.")
    connection = VariableOutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="A reusable SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True. This connection is expected to only be used on machines running 'Unix' operating systems (e.g. Linux).",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.ip}] "

    def run(self):
        self.disable_output_socket("Unix SSH Connection")
        try:
            conn = datatypes.UnixSSHConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.retries, self.delay, self.keep_open, "unix")
            self.success = True
            # assigning a value to self.connection will re-enable it, so we only do that if the connection successfully connects
            self.connection = conn
        except RuntimeError as e:
            self.logger.add_azure_build_tag('unix-ssh-connection-error')
            self.success = False
            if self.error_on_failure:
                raise e


class EsxiVirtualMachineSshExec(Node):
    name: str = "Unix SSH: Execute Bash Command"
    description: str = "Use an SSH connection to execute a bash command on the remote end of this connection (note that this may be some other shell depending on the system default, but bash is assumed). This will block until the associated command has finished. Only valid for connections to Unix-like hosts. You can respond to stdin requests using this node by specifying regexes to match (Stdin Regexes list) and send string responses to regex matches (Stdin Responses list). This regex to response relationship is one-to-one and each entry in one list assumes a cooresponding entry in the other list."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    cmd = InputSocket(datatype=String, name="Command", description="The command to execute over SSH. You can also specify paths to bash scripts to execute (e.g. /home/username/myscript.sh). Please give the scripts the proper permissions before attempting with new scripts.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. An exception (error) will be raised if the timeout time is reached and all retries have been exhausted.", input_field=120)
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    pty = InputSocket(datatype=Boolean, name="PTY?", description="Run the command in a pseudoterminal. When set to True this node 'emulates' a human running the command in a physical terminal. When set to False: this node will use the SSH protocol but no 'terminal' will be asserted by the connection (signifies a machine doing SSH instead of a human). When running as 'sudo': this should be 'True'. If you aren't sure what to choose here: leave this set to 'True'. Note that pseudoterminals have limited access to stdout/stderr and you will get better results from those output sockets if you set this to 'False'.", input_field=True)
    cwd = OptionalInputSocket(
        datatype=String,
        name="CWD",
        description="The directory that the command should run in. By default: runs in the default directory (e.g. usually the home directory).",
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )
    stdin_regexes = ListInputSocket(
        datatype=String,
        name="Stdin Regexes",
        description="Regexes for matching the SSH output to determine when to send responses over stdin. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the responses in 'Stdin Responses'. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': The terminal will ask for the password the 'otheruser' in order to transfer the file. You would provide a string regular expression in this list that looks something like this: '.*password:'. This regex would then match when the terminal prompts for 'otheruser@somehostname's password:' and it would look at the list for 'Stdin Responses' to determine what response to send to the scp command.",
    )
    stdin_responses = ListInputSocket(
        datatype=String,
        name="Stdin Responses",
        description="Text to send over stdin when the corresponding regex is matched from 'Stdin Regexes'. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the regexes in 'Stdin Regexes'. Please read the description for 'Stdin Regexes' above. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': In this list you would provide the password to respond with.",
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="Stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="Stderr", description="The stderr from the command response.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.sshobj._ip}] "
        else:
            return f"[{self.name} - {self.sshobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        cwd = self.cwd if self.cwd else None

        stdin = None
        if len(self.stdin_regexes) and len(self.stdin_responses):
            if len(self.stdin_regexes) != len(self.stdin_responses):
                raise RuntimeError(
                    f"The number of stdin regexes ({len(self.stdin_regexes)}) does not match the number of responses ({len(self.stdin_responses)})"
                )
            stdin = {self.stdin_regexes[i]: self.stdin_responses[i] + '\n' for i in range(len(self.stdin_regexes))}

        self.log(f"Executing command: {self.cmd}")
        command_response = self.sshobj.exec(cmd=self.cmd, timeout=int(self.timeout), pty=self.pty, cwd=cwd, sudo_password=self.sudo_password, stdin=stdin)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            self.logger.add_azure_build_tag('unix-command-failed')
            raise exceptions.SSHExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        self.attempt = 0
        error = None
        while self.attempt < int(self.retries) + 1:
            try:
                self.run_attempt()
                return  # OK
            except Exception as e:
                error = e
            self.attempt += 1

        if error:
            raise error


class SshExecScript(Node):
    name: str = "Unix SSH: Execute Bash Script"
    description: str = "Use an SSH connection to execute a script (one or more newline-separated commands) on the remote end of this connection. This will block until the associated script has finished. Only valid for connections to Unix-like hosts."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    script = InputSocket(datatype=String, name="Script", description="The script to execute over SSH. This should be a newline-separated list of commands.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    pty = InputSocket(datatype=Boolean, name="PTY?", description="Run the command in a pseudoterminal.", input_field=False)
    cwd = OptionalInputSocket(
        datatype=String, name="CWD", description="The directory that the command should run in. By default: runs in the default directory."
    )
    use_sudo = InputSocket(
        datatype=Boolean,
        name="Use Sudo?",
        description="Whether to run the entire script using sudo. Setting this to 'False' does not forgo the possibility of using sudo commands within the script itself.",
        input_field=False,
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )
    stdin_regexes = ListInputSocket(
        datatype=String,
        name="Stdin Regexes",
        description="Regexes for matching the SSH output to determine when to send responses over stdin. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the responses in 'Stdin Responses'. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': The terminal will ask for the password the 'otheruser' in order to transfer the file. You would provide a string regular expression in this list that looks something like this: '.*password:'. This regex would then match when the terminal prompts for 'otheruser@somehostname's password:' and it would look at the list for 'Stdin Responses' to determine what response to send to the scp command.",
    )
    stdin_responses = ListInputSocket(
        datatype=String,
        name="Stdin Responses",
        description="Text to send over stdin when the corresponding regex is matched from 'Stdin Regexes'. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the regexes in 'Stdin Regexes'. Please read the description for 'Stdin Regexes' above. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': In this list you would provide the password to respond with.",
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.sshobj._ip}] "
        else:
            return f"[{self.name} - {self.sshobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        cwd = self.cwd if self.cwd else None
        script_string = re.sub(r"^", "  │  ", self.script, flags=re.MULTILINE)

        stdin = None
        if len(self.stdin_regexes) and len(self.stdin_responses):
            if len(self.stdin_regexes) != len(self.stdin_responses):
                raise RuntimeError(
                    f"The number of stdin regexes ({len(self.stdin_regexes)}) does not match the number of responses ({len(self.stdin_responses)})"
                )
            stdin = {self.stdin_regexes[i]: self.stdin_responses[i] + '\n' for i in range(len(self.stdin_regexes))}

        self.log(f"Executing script:\n{script_string}")
        command_response = self.sshobj.exec_script(
            script=self.script, timeout=int(self.timeout), pty=self.pty, cwd=cwd, use_sudo=self.use_sudo, sudo_password=self.sudo_password, stdin=stdin
        )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            self.logger.add_azure_build_tag('unix-command-failed')
            raise exceptions.SSHExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        self.attempt = 0
        error = None
        while self.attempt < int(self.retries) + 1:
            try:
                self.run_attempt()
                return  # OK
            except Exception as e:
                error = e
            self.attempt += 1

        if error:
            raise error


class SshExecAnsible(Node):
    name: str = "Unix SSH: Execute Ansible Playbook"
    description: str = "Use SSH to execute an Ansible Playbook on the remote end of this connection. This includes additional handling for Ansible Playbooks not provided by standard SSH execution. Only valid for connections to Unix-like hosts."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    cmd = InputSocket(datatype=String, name="Command", description="The command to execute over SSH that triggers an Ansible Playbook.")
    retries = InputSocket(datatype=Number, name="Retries", description="Number of times to retry the playbook on failure.", input_field=0)
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds.", input_field=1800)
    cwd = OptionalInputSocket(
        datatype=String,
        name="CWD",
        description="The directory that the command should run in. By default: runs in the default directory. May not apply to non-Unix SSH connections.",
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )

    output = OutputSocket(datatype=String, name="Output", description="The Ansible Playbook output.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run_attempt(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        cwd = self.cwd if self.cwd else None

        if self.attempt == 0:
            self.log(f"Executing Ansible Playbook: {self.cmd}")
        else:
            self.log(f"Executing Ansible Playbook (Attempt {self.attempt+1} of {int(self.retries)+1}): {self.cmd}")

        header_regex = re.compile(r"^[A-Z]+\s\[[^\]]+\]\s\*+$", flags=re.MULTILINE)
        star_regex = re.compile(r"\*+$", flags=re.MULTILINE)
        output_buffer = ""

        def logfunc(s: str):
            self.log("\n\n" + re.sub(r"^", " " * 8, s.strip(), flags=re.MULTILINE) + "\n")

        def output_callback(s: str):
            nonlocal header_regex, output_buffer
            output_buffer += s
            matches = list(header_regex.finditer(output_buffer))
            while len(matches) > 1:
                start = matches[0].start(0)
                end = matches[1].start(0)
                playbook_block = output_buffer[start:end]
                output_buffer = output_buffer[end:]
                matches = list(header_regex.finditer(output_buffer))
                playbook_block = star_regex.sub("", playbook_block)
                logfunc(playbook_block)

        command_response = self.sshobj.exec(
            cmd=self.cmd, timeout=int(self.timeout), cwd=cwd, sudo_password=self.sudo_password, out_stream_callback=output_callback
        )

        recap_split = re.split(r"^PLAY RECAP\s\*+$", output_buffer, maxsplit=1, flags=re.MULTILINE)
        if recap_split[0].strip():
            logfunc(star_regex.sub("", recap_split[0]))
        logfunc("PLAY RECAP\n" + recap_split[1].strip())

        total_output = str(command_response.stdout)
        if command_response.status != 0 or re.search(r"^PLAY RECAP.*(failed=[^0]|unreachable=[^0])", total_output, flags=re.MULTILINE | re.DOTALL):
            raise RuntimeError(f"Playbook failed.")

        self.output = total_output
        self.log(f"Playbook Completed: {self.cmd}")
        self.debug(f"Output:\n{total_output}")

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        self.attempt = 0
        error = None
        while self.attempt < int(self.retries) + 1:
            try:
                self.run_attempt()
                return  # OK
            except Exception as e:
                error = e
            self.attempt += 1

        if error:
            raise error


class SshUpload(Node):
    name: str = "Unix SSH: Upload"
    description: str = "Use an SSH connection to upload files to the remote end of this connection. This behaves similarly to the Unix 'scp' command but uses the 'SFTP' protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    path = InputSocket(datatype=String, name="File Path", description="The file path to upload (file or directory).")
    dst = InputSocket(datatype=String, name="Remote Destination", description="The destination on the remote host to upload to.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only",
        description="When 'File Path' is a directory, upload the contents of a directory rather than the directory itself. This is similar to using 'directory/*' in scp.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite?", description="Overwrite existing files rather than raising an error.", input_field=False)

    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        username = self.sshobj._username
        dst = self.dst.replace('~', f'/home/{username}') if username != 'root' else self.dst.replace('~', '/root')
        src = os.path.expanduser(self.path)
        if not os.path.exists(src):
            raise RuntimeError(f"No such file or directory: {src}")

        log_string = ""
        if os.path.isdir(src) and not self.directory_contents_only:
            log_string = f"directory {src} to {dst}"
        elif os.path.isdir(src):
            log_string = f"directory (contents) {src} to {dst}"
        else:
            log_string = f"file {src} to {dst}"

        self.log(f"Uploading {log_string}")

        start_time = time.perf_counter()
        self.sshobj.upload(src=self.path, dst=dst, directory_contents_only=self.directory_contents_only, overwrite=self.overwrite)
        self.debug(f"Finished uploading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")


class SshDownload(Node):
    name: str = "Unix SSH: Download"
    description: str = "Use an SSH connection to download files from the remote end of this connection to the local machine. This behaves similarly to the Unix 'scp' command  but uses the 'SFTP' protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    remote_path = InputSocket(datatype=String, name="Remote Path", description="The absolute file path on the remote machine to download.")
    path = InputSocket(datatype=String, name="Local Destination", description="The destination on the local host to download to.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only",
        description="When 'Remote Path' is a directory, download the contents of a directory rather than the directory itself. This is similar to using 'directory/*' in scp.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite?", description="Overwrite existing files rather than raising an error.", input_field=False)

    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        username = self.sshobj._username
        remote = self.remote_path.replace('~', f'/home/{username}') if username != 'root' else self.remote_path.replace('~', '/root')
        
        log_string = ""
        log_string = f"{remote} (contents) to {self.path}" if self.directory_contents_only else f"{remote} to {self.path}"

        self.log(f"Downloading {log_string}")

        start_time = time.perf_counter()
        self.sshobj.download(path=remote, dst=self.path, directory_contents_only=self.directory_contents_only, overwrite=self.overwrite)
        self.debug(f"Finished downloading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")


class SshReadFile(Node):
    name: str = "Unix SSH: Read File"
    description: str = "Use an SSH connection to read a file on the remote end of this connection. By default, this will use the 'SFTP' protocol. When 'sudo' is specified this node will execute 'sudo -S cat' and return the stdout instead of using the SFTP protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    path = InputSocket(datatype=String, name="File Path", description="The file path on the remote machine to read.")
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use to read the file as a string. This setting is ignored when 'Use Sudo?' is set to True.", input_field="UTF-8")
    use_sudo = InputSocket(
        datatype=Boolean,
        name="Use Sudo?",
        description="Whether to run the entire script using sudo. Setting this to 'False' does not forgo the possibility of using sudo commands within the script itself.",
        input_field=False,
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )

    contents = OutputSocket(datatype=String, name="File Contents", description="The file contents.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        username = self.sshobj._username
        p = self.path.replace('~', f'/home/{username}') if username != 'root' else self.path.replace('~', '/root')
        self.log(f"Reading file: {p}")
        if self.use_sudo:
            self.contents = str(self.sshobj.read(path=p, sudo_dash_S=True, sudo_password=self.sudo_password))
        else:
            self.contents = str(self.sshobj.read(path=p, encoding=self.encoding))
        self.debug(f"File contents for {p}:\n" + re.sub(r"^", "  │  ", self.contents, flags=re.MULTILINE))


class SshWriteFile(Node):
    name: str = "Unix SSH: Write File"
    description: str = "Use an SSH connection to write a file on the remote end of this connection. The file will be created if it does not exist. By default, this will use the 'SFTP' protocol. When 'sudo' is specified this node will execute 'sudo -S echo' instead of using the SFTP protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    path = InputSocket(datatype=String, name="File Path", description="The file path on the remote machine to write.")
    contents = InputSocket(datatype=String, name="Contents", description="The contents to write to the file.")
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use to write the file. This value will be ignored when 'Use Sudo?' is set to True.", input_field="UTF-8")
    overwrite = InputSocket(datatype=Boolean, name="Overwrite?", description="Overwrite the file if it exists rather than raising an error.", input_field=True)
    use_sudo = InputSocket(
        datatype=Boolean,
        name="Use Sudo?",
        description="Whether to run the entire script using sudo. Setting this to 'False' does not forgo the possibility of using sudo commands within the script itself.",
        input_field=False,
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )

    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        username = self.sshobj._username
        p = self.path.replace('~', f'/home/{username}') if username != 'root' else self.path.replace('~', '/root')
        self.log(f"Writing file: {p}")
        self.debug(f"Writing to {p}:\n" + re.sub(r"^", "  │  ", self.contents, flags=re.MULTILINE))
        if self.use_sudo:
            self.sshobj.write(path=p, contents=self.contents, overwrite=self.overwrite, sudo_dash_S=True, sudo_password=self.sudo_password)
        else:
            self.sshobj.write(path=p, contents=self.contents.encode(encoding=self.encoding), overwrite=self.overwrite)


class SshListFiles(Node):
    name: str = "Unix SSH: List Files"
    description: str = "Use an SSH connection to list files in a directory on the remote end of this connection. By default, this will use the 'SFTP' protocol. When 'sudo' is specified this node will execute 'sudo -S ls -a' and return the stdout splitted on newlines instead of using the SFTP protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    path = InputSocket(datatype=String, name="File Path", description="The file path on the remote machine to write.")
    cwd = OptionalInputSocket(
        datatype=String, name="CWD", description="The directory that the command should run in. By default: runs in the default directory. This value is ignored when 'Use Sudo?' is set to True."
    )
    use_sudo = InputSocket(
        datatype=Boolean,
        name="Use Sudo?",
        description="Whether to run the entire script using sudo. Setting this to 'False' does not forgo the possibility of using sudo commands within the script itself.",
        input_field=False,
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )

    files = ListOutputSocket(datatype=String, name="Files", description="List of files (names only).")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        cwd = self.cwd if self.cwd else None
        username = self.sshobj._username
        p = self.path.replace('~', f'/home/{username}') if username != 'root' else self.path.replace('~', '/root')
        self.debug(f"Listing files in {p}")
        if self.use_sudo:
            self.files = [os.path.basename(file) for file in self.sshobj.ls(path=p, cwd=cwd, sudo_dash_S=True, sudo_password=self.sudo_password)]
        else:
            self.files = [os.path.basename(file) for file in self.sshobj.ls(path=p, cwd=cwd)]
        self.debug(f"Files in {p}: {str(self.files)[1:-1]}")


class SshRegexReplaceFile(Node):
    name: str = "Unix SSH: File Regex Replace"
    description: str = (
        "Use an SSH connection to apply a regex substitution to a file remote end of this connection. This will use the 'SFTP' protocol. Only valid for connections to Unix-like hosts. The tilde character '~' will be replaced with '/home/username' for normal users."
    )
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    path = InputSocket(datatype=String, name="File Path", description="The file path on the remote machine.")
    regex_string = InputSocket(datatype=String, name="Regex", description="The regex to apply to the string.")
    replacement = InputSocket(
        datatype=String,
        name="Replacement",
        description="The replacement string to replace regex matches with. \\g<number> will substitute in the substring matched by group 'number' (e.g., \\g<2> will reference and insert group 2). The backreference \\g<0> substitutes in the entire substring matched.",
    )
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use to read and write the file as a string.", input_field="UTF-8")
    num_replacements = InputSocket(
        datatype=Number,
        name="Maximum Replacements",
        description="The maximum number of replacements to make within the string. If 0, all matches will be replaced.",
        input_field=0,
    )
    multiline = InputSocket(
        datatype=Boolean,
        name="Multiline",
        description="When specified, the pattern character '^' matches at the beginning of the string and at the beginning of each line (immediately following each newline); and the pattern character '$' matches at the end of the string and at the end of each line (immediately preceding each newline).",
        input_field=True,
    )
    ignore_case = InputSocket(
        datatype=Boolean,
        name="Ignore Case",
        description="Perform case-insensitive matching; expressions like [A-Z] will also match lowercase letters.",
        input_field=False,
    )
    dot_all = InputSocket(
        datatype=Boolean,
        name="Dot-All",
        description="Make the '.' special character match any character at all, including a newline; without this flag, '.' will match anything except a newline.",
        input_field=False,
    )

    contents_before = OutputSocket(datatype=String, name="File Contents Before", description="The file contents before replacements.")
    contents_after = OutputSocket(datatype=String, name="File Contents After", description="The file contents after replacements.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        username = self.sshobj._username
        p = self.path.replace('~', f'/home/{username}') if username != 'root' else self.path.replace('~', '/root')
        self.log(f"Modifying file: {p}")

        escaped_replacement_string = self.replacement.replace("\n", "\\n")
        self.debug(f"{p}: Replacing regex {re.escape(self.regex_string)} with {escaped_replacement_string}")
        self.contents_before = str(self.sshobj.read(path=p, encoding=self.encoding))

        flags = 0
        if self.multiline:
            flags = flags | re.MULTILINE
        if self.ignore_case:
            flags = flags | re.IGNORECASE
        if self.dot_all:
            flags = flags | re.DOTALL
        regex = re.compile(self.regex_string, flags=flags)

        self.contents_after = regex.sub(self.replacement, self.contents_before, count=0 if self.num_replacements <= 0 else int(self.num_replacements))
        self.sshobj.write(path=p, contents=self.contents_after.encode(encoding=self.encoding), overwrite=True)

        formatted_contents_before = re.sub(r"^", "  │  ", self.contents_before, flags=re.MULTILINE)
        formatted_contents_after = re.sub(r"^", "  │  ", self.contents_after, flags=re.MULTILINE)
        self.debug(f"Before Replacement:\n{formatted_contents_before}\n\nAfter Replacement:\n{formatted_contents_after}")


class EsxiUnixSshCurl(Node):
    name: str = "Unix SSH: Execute curl Command"
    description: str = "Use an SSH connection to execute the command curl on the remote end of this connection. This is similar to the 'Network HTTP Request' node but allows you to execute a network request from a remote machine (as opposed to the server GraphEx is being run on). This will block until the associated command has finished. Only valid for connections to Unix-like hosts."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.UnixSSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over. This must be the 'UnixSSHConnection' flavor of object.")
    url = InputSocket(
        datatype=String,
        name="URL",
        description="The URL to cURL, including 'http://' or 'https://', the IP or hostname, the port number (if applicable) and the resource pathing. (e.g. https://x.x.x.x:8080/some/endpoint)",
    )
    request_type = EnumInputSocket(datatype=String,name="HTTP Request Type", description="The type of HTTP request being made (e.g. XGET is GET, XPOST is POST, etc.)",enum_members=['-XGET', '-XPOST', '-XPUT', '-XPATCH'], input_field="-XGET")
    k_arg = InputSocket(
        datatype=Boolean,
        name="(-k) Insecure Request?",
        description="Whether to append the flag -k to ignore certificates or not.",
        input_field=False,
    )
    s_arg = InputSocket(
        datatype=Boolean,
        name="(-s) Silent?",
        description="Whether to silence the downloading metadata that cURL shows on the terminal",
        input_field=True,
    )
    l_arg = InputSocket(
        datatype=Boolean,
        name="(-L) Follow Redirects?",
        description="Whether to follow redirects (e.g. if a website requests https instead of http)",
        input_field=False,
    )
    username_arg = OptionalInputSocket(
        datatype=String,
        name="(-u) Username",
        description="If a username+password is needed to complete the cURL request, add the username part here (e.g. the username part of -u username:'password' on the command line). Both the '(-u) Username' and '(-u) Password' fields must be filled in to send a -u argument.",
    )
    password_arg = OptionalInputSocket(
        datatype=String,
        name="(-u) Password",
        description="If a username+password is needed to complete the cURL request, add the password part here (e.g. the password part of -u username:'password' on the command line). Both the '(-u) Username' and '(-u) Password' fields must be filled in to send a -u argument.",
    )
    content_type_json = InputSocket(
        datatype=Boolean,
        name="(-H) Content-Type JSON?",
        description="When this checkbox is True, will add the header: Content-Type: application/json to your request.",
        input_field=False,
    )
    payload = OptionalInputSocket(
        datatype=String,
        name="(-d) Payload Data",
        description="When sending data to the URL: this is the data to send. If sending JSON: this field should be a JSON string and the '(-H) Content-Type JSON?' checkbox should be set to True. This string will be wrapped in single quotes ('your_payload_data'). Make sure to use the escape character (\) in front of any single quotes you wish to use in your payload.",
    )
    output_arg = OptionalInputSocket(
        datatype=String,
        name="(-o) Output to File",
        description="Give the name of a file here to save the response to (optional)",
    )
    verbosity = EnumInputSocket(datatype=String,name="(-v) Verbosity", description="The level of verbosity to execute the curl command under",enum_members=['None', '-v', '-vv', '-vvv'], input_field="None")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. An exception (error) will be raised if the timeout time is reached and all retries have been exhausted.", input_field=240)
    cwd = OptionalInputSocket(
        datatype=String,
        name="CWD",
        description="The directory that the command should run in. By default: runs in the default directory (e.g. usually the home directory).",
    )
    use_sudo = InputSocket(
        datatype=Boolean,
        name="Use Sudo?",
        description="Whether to run the entire script using sudo. Setting this to 'False' does not forgo the possibility of using sudo commands within the script itself. When sudo is used, stderr will be merged with stdout. The word sudo will be added to the front of the cURL command for you (i.e. sudo curl ...).",
        input_field=False,
    )
    sudo_password = OptionalInputSocket(
        datatype=String,
        name="Sudo Password",
        description="Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used.",
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="Stdout (Response)", description="The stdout from the command response. If sudo is used, this will also contain the stderr.")
    stderr = OutputSocket(datatype=String, name="Stderr", description="The stderr from the command response.")
    connection = OutputSocket(
        datatype=datatypes.UnixSSHConnection,
        name="Unix SSH Connection",
        description="The Unix SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.UnixSSHConnection), f"Not a Unix SSH connection"
        self.connection = self.sshobj
        cwd = self.cwd if self.cwd else None
        use_pty = False

        cmd: str = "curl"
        if self.k_arg:
            cmd += " -k"
        if self.s_arg:
            cmd += " -s"
        if self.username_arg and self.password_arg:
            cmd += f" -u {self.username_arg}:'{self.password_arg}'"

        if self.l_arg:
            cmd += " -L"

        cmd += f" {self.url} {self.request_type}"

        if self.content_type_json:
            cmd += " -H 'Content-Type: application/json'"

        if self.payload:
            cmd += f" -d '{self.payload}'"

        if self.verbosity != "None":
            cmd += f" {self.verbosity}"

        if self.output_arg:
            cmd += f" -o {self.output_arg}"

        if self.use_sudo:
            use_pty = True
            if not cmd.startswith('sudo'):
                cmd = "sudo " + cmd

        cmd_to_print = cmd
        if self.password_arg:
            cmd_to_print.replace(self.password_arg, '*' * len(self.password_arg), 1)

        self.debug(f"Executing command: {cmd_to_print}")

        command_response = self.sshobj.exec(cmd=cmd, timeout=int(self.timeout), pty=use_pty, cwd=cwd, sudo_password=self.sudo_password, stdin=None)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.logger.add_azure_build_tag('unix-command-failed')
            raise exceptions.SSHExecutionError(s)
