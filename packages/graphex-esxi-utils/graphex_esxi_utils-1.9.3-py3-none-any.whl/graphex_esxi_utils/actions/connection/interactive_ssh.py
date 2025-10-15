from graphex import Boolean, String, Number, Node, InputSocket, OptionalInputSocket, OutputSocket, VariableOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
import typing


class OpenInteractiveSSHConnection(Node):
    name: str = "Open Interactive SSH Connection"
    description: str = "Open an Interactive SSH Connection. This class simulates an actual SSH session opened by running the `ssh` command on a CLI, rather than implementing the SSH protocol in code (i.e from the host's point of view, it looks just like someone typed the text from a terminal)."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    ip = InputSocket(datatype=String, name="IP", description="The IP of an interface on the VM to connect to.")
    username = InputSocket(datatype=String, name="Username", description="The username of the user to login through SSH as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in via SSH.")
    prompt = OptionalInputSocket(
        datatype=String,
        name="Prompt",
        description="The console prompt, if known. Specifying the console prompt here exactly will improve performance as it avoids having to auto-detect the prompt. This should be specified as a regex unless 'Prompt Exact?' is True. This prompt is used to determine the boundaries between commands and to determine when a command finishes.",
    )
    prompt_exact = OptionalInputSocket(
        datatype=Boolean,
        name="Prompt Exact?",
        description="Whether or not the 'Prompt' parameter should be treated as a literal or as a regular expression. Setting this to True will treat the prompt as a literal to be matched exactly, and False will treat the prompt as a regex string.",
    )
    encoding = InputSocket(datatype=String, name="Encoding", description="Encoding to use for reading the SSH output.", input_field="utf-8")
    retries = InputSocket(datatype=Number, name="Retries", description="The maximum number of SSH connection attempts to make.", input_field=10)
    delay = InputSocket(datatype=Number, name="Delay", description="The time to wait between each SSH connection attempt.", input_field=5)
    error_on_failure = InputSocket(
        datatype=Boolean, name="Error on Failure?", description="Whether to raise an error when an SSH connection could not be established.", input_field=True
    )
    keep_open = InputSocket(
        datatype=Boolean,
        name="Keep Connection Open",
        description="Whether to keep the connection open so that a usable SSH connection object is returned. If this is False, the 'ESXi SSH Connection' output will be disabled.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Connection Available", description="Whether a connection could be established to the virtual machine.")
    connection = VariableOutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH Connection",
        description="A reusable SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.username}@{self.ip}] "

    def run(self):
        self.disable_output_socket("Interactive SSH Connection")
        try:
            conn = datatypes.InteractiveSSHConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.retries, self.delay, self.keep_open, self.encoding, self.prompt, self.prompt_exact)
            self.success = True
            # assigning a value to self.connection will re-enable it, so we only do that if the connection successfully connects
            self.connection = conn
        except RuntimeError as e:
            self.logger.add_azure_build_tag('interactive-ssh-connection-error')
            self.success = False
            if self.error_on_failure:
                raise e


class CloseInteractiveSSHConnection(Node):
    name: str = "Close Interactive SSH Connection"
    description: str = "Close an open Interactive SSH connection. The connection object will no longer be usable for operations. If the object is already closed, this will do nothing."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        if self.sshobj._proc:
            self.debug(f"Closing connection.")
            self.sshobj.close()


class InteractiveSSHWaitForString(Node):
    name: str = "Interactive SSH: Wait For String"
    description: str = "Wait for an exact string to be present in the output of the Interactive SSH connection."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    target_string = InputSocket(datatype=String, name="String", description="The string to wait for.")
    timeout = InputSocket(
        datatype=Number, name="Timeout", description="The maximum amount of time to wait (in seconds) before raising an error.", input_field=30
    )

    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.log(f"Waiting for string: {self.target_string}")
        self.sshobj.wait_for_string(s=self.target_string, timeout=int(self.timeout))


class InteractiveSSHWaitForPattern(Node):
    name: str = "Interactive SSH: Wait For Pattern"
    description: str = "Wait for regex pattern to be present in the output of the Interactive SSH connection."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    pattern = InputSocket(datatype=String, name="Pattern", description="The regex pattern to wait for.")
    timeout = InputSocket(
        datatype=Number, name="Timeout", description="The maximum amount of time to wait (in seconds) before raising an error.", input_field=30
    )

    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.log(f"Waiting for pattern: {self.pattern}")
        self.sshobj.wait_for_pattern(pattern=self.pattern, timeout=int(self.timeout))


class InteractiveSSHWaitForPrompt(Node):
    name: str = "Interactive SSH: Wait For Prompt"
    description: str = "Wait for the prompt to be present in the output of the Interactive SSH connection."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    timeout = InputSocket(
        datatype=Number, name="Timeout", description="The maximum amount of time to wait (in seconds) before raising an error.", input_field=30
    )

    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.log(f"Waiting for prompt")
        self.sshobj.wait_for_prompt(timeout=int(self.timeout))


class InteractiveSSHWrite(Node):
    name: str = "Interactive SSH: Write Text"
    description: str = "Write text (simulate keystrokes) over an Interactive SSH connection."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    text = InputSocket(datatype=String, name="Text", description="The text to write.")
    is_line = InputSocket(datatype=Boolean, name="Enter", description="Whether to press the 'Enter' key after writing the text.", input_field=False)

    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        if self.is_line:
            self.log(f"Writing line: {self.text}")
            self.sshobj.writeline(self.text)
        else:
            self.log(f"Writing text: {self.text}")
            self.sshobj.write(self.text)


class InteractiveSSHCommand(Node):
    name: str = "Interactive SSH: Execute Command"
    description: str = "Perform a command over an Interactive SSH connection. This will write the command text and then wait for the next prompt."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    command = InputSocket(datatype=String, name="Command", description="The text to write to execute the command.")
    timeout = InputSocket(
        datatype=Number,
        name="Timeout",
        description="The maximum amount of time to wait (in seconds) for the command to complete before raising an error.",
        input_field=30,
    )

    output = OutputSocket(
        datatype=String,
        name="Output",
        description="The output text of the command.",
    )
    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.log(f"Executing command: {self.command}")
        self.output = self.sshobj.command(command=self.command, timeout=int(self.timeout))
        self.debug(f"Output:\n{self.output}")


class InteractiveSSHGetOutput(Node):
    name: str = "Interactive SSH: Get Output"
    description: str = "Get the output of the most recently run command or sequence of operations within this Interactive SSH session."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )

    output = OutputSocket(
        datatype=String,
        name="Output",
        description="The output text.",
    )
    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.output = self.sshobj.get_output()


class InteractiveSSHLogOutput(Node):
    name: str = "Interactive SSH: Log Output"
    description: str = "Log the output of the most recently run command or sequence of operations within this Interactive SSH session."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    level = InputSocket(datatype=String, name="Level", description="The log level (debug, info, notice, warning, error).", input_field="info")

    output = OutputSocket(
        datatype=String,
        name="Output",
        description="The output text.",
    )
    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.output = self.sshobj.get_output()
        self.log("\n" + self.output, level=self.level)


class InteractiveSSHGetAllOutput(Node):
    name: str = "Interactive SSH: Get All Output"
    description: str = "Get the entire output of this Interactive SSH session since its initialization."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )

    output = OutputSocket(
        datatype=String,
        name="Output",
        description="The output text.",
    )
    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.output = self.sshobj.get_all_output()


class InteractiveSSHLogAllOutput(Node):
    name: str = "Interactive SSH: Log All Output"
    description: str = "Log the entire output of this Interactive SSH session since its initialization."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Interactive"]
    color: str = esxi_constants.COLOR_INTERACTIVE_SSH

    sshobj = InputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="A previously opened Interactive SSH connection object to execute over.",
    )
    level = InputSocket(datatype=String, name="Level", description="The log level (debug, info, notice, warning, error).", input_field="info")

    output = OutputSocket(
        datatype=String,
        name="Output",
        description="The output text.",
    )
    connection = OutputSocket(
        datatype=datatypes.InteractiveSSHConnection,
        name="Interactive SSH",
        description="The Interactive SSH Connection (same as input). This maybe be used to 'chain' multiple operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj.hostname}] "

    def run(self):
        self.connection = self.sshobj
        self.output = self.sshobj.get_all_output()
        self.log("\n" + self.output, level=self.level)
