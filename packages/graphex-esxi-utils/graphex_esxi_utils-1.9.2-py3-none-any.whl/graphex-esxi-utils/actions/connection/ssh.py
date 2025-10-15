from graphex import Boolean, String, Number, Node, InputSocket, OptionalInputSocket, ListInputSocket, OutputSocket, VariableOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
import typing


class OpenSSHConnection(Node):
    name: str = "Open SSH Connection"
    description: str = "Open an SSH connection to a host."
    categories: typing.List[str] = ["Remote Connections", "SSH"]
    color: str = esxi_constants.COLOR_SSH_CONNECTION

    # input sockets
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

    # output sockets
    success = OutputSocket(datatype=Boolean, name="Connection Available", description="Whether a connection could be established to the host.")
    connection = VariableOutputSocket(
        datatype=datatypes.SSHConnection,
        name="SSH Connection",
        description="A reusable SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.ip}] "

    def run(self):
        self.disable_output_socket("SSH Connection")
        try:
            conn = datatypes.SSHConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.retries, self.delay, self.keep_open, "")
            self.success = True
            # assigning a value to self.connection will re-enable it, so we only do that if the connection successfully connects
            self.connection = conn
        except RuntimeError as e:
            self.logger.add_azure_build_tag('generic-ssh-connection-error')
            self.success = False
            if self.error_on_failure:
                raise e


class CloseSSHConnection(Node):
    name: str = "Close SSH Connection"
    description: str = "Close an open SSH connection. The connection object will no longer be usable for SSH operations. If the SSH object is already closed, this will do nothing."
    categories: typing.List[str] = ["Remote Connections", "SSH"]
    color: str = esxi_constants.COLOR_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.SSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over.")

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        if self.sshobj._connection:
            self.debug(f"Closing connection.")
            self.sshobj.close()


class SshExec(Node):
    name: str = "SSH: Execute Command"
    description: str = "Use an SSH connection to execute a command on the remote end of this connection. This will block until the associated command has finished. The way this command is executed depends on the target operating system."
    categories: typing.List[str] = ["Remote Connections", "SSH"]
    color: str = esxi_constants.COLOR_SSH_CONNECTION

    sshobj = InputSocket(datatype=datatypes.SSHConnection, name="SSH Connection", description="A previously opened SSH connection object to execute over.")
    cmd = InputSocket(datatype=String, name="Command", description="The command to execute over SSH.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds.", input_field=120)
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    stdin_regexes = ListInputSocket(
        datatype=String,
        name="Stdin Regexes",
        description="Regexes for matching the SSH output to determine when to send responses over stdin. This is one-to-one with the responses in 'Stdin Responses'.",
    )
    stdin_responses = ListInputSocket(
        datatype=String,
        name="Stdin Responses",
        description="Text to send over stdin when the corresponding regex is matched from 'Stdin Regexes'. This is one-to-one with the regexes in 'Stdin Regexes'.",
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(
        datatype=Number, name="Status Code", description="The exit status code from the commands execution. May not be available on all operating systems."
    )
    stdout = OutputSocket(datatype=String, name="Stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="Stderr", description="The stderr from the command response. May not be available on all operating systems.")
    connection = OutputSocket(
        datatype=datatypes.SSHConnection,
        name="SSH Connection",
        description="The SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.sshobj._ip}] "
        else:
            return f"[{self.name} - {self.sshobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        stdin = None
        if len(self.stdin_regexes) and len(self.stdin_responses):
            if len(self.stdin_regexes) != len(self.stdin_responses):
                raise RuntimeError(
                    f"The number of stdin regexes ({len(self.stdin_regexes)}) does not match the number of responses ({len(self.stdin_responses)})"
                )
            stdin = {self.stdin_regexes[i]: self.stdin_responses[i] for i in range(len(self.stdin_regexes))}

        self.log(f"Executing command: {self.cmd}")
        command_response = self.sshobj.exec(cmd=self.cmd, timeout=int(self.timeout), stdin=stdin)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            raise exceptions.SSHExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
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
