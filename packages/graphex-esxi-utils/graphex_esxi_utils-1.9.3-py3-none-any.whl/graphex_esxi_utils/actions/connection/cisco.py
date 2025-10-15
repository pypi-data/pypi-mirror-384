from graphex import Boolean, String, Number, DataContainer, Node, InputSocket, ListInputSocket, OutputSocket, ListOutputSocket, VariableOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex_esxi_utils.utils import misc as misc_utils
import esxi_utils
import typing
import json
import re


class OpenCiscoSSHConnection(Node):
    name: str = "Open Cisco SSH Connection"
    description: str = "Open an SSH connection to a Cisco host."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

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
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.ip}] "

    def run(self):
        self.disable_output_socket("Cisco SSH Connection")
        try:
            conn = datatypes.CiscoSSHConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.retries, self.delay, self.keep_open, "cisco")
            self.success = True
            # assigning a value to self.connection will re-enable it, so we only do that if the connection successfully connects
            self.connection = conn
        except RuntimeError as e:
            self.logger.add_azure_build_tag('cisco-ssh-connection-error')
            self.success = False
            if self.error_on_failure:
                raise e


class CiscoSshExec(Node):
    name: str = "Cisco SSH: Execute Command"
    description: str = "Use an SSH connection to execute a command on the remote end of this connection. This will block until the associated command has finished. Only valid for connections to Cisco hosts."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )
    cmd = InputSocket(datatype=String, name="Command", description="The command to execute over SSH.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    retries = InputSocket(
        datatype=Number,
        name="Retries",
        description="Number of times to retry the command on failure. Since Cisco commands do not report a status code, this is primarily used for errors caused by network issues.",
        input_field=0,
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
    remove_banner = InputSocket(
        datatype=Boolean,
        name="Remove Banner",
        description="Whether or not to auto-detect and remove login banners from the resulting output.",
        input_field=True,
    )

    output = OutputSocket(datatype=String, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True."
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.sshobj._ip}] "
        else:
            return f"[{self.name} - {self.sshobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"

        stdin = None
        if len(self.stdin_regexes) and len(self.stdin_responses):
            if len(self.stdin_regexes) != len(self.stdin_responses):
                raise RuntimeError(
                    f"The number of stdin regexes ({len(self.stdin_regexes)}) does not match the number of responses ({len(self.stdin_responses)})"
                )
            stdin = {self.stdin_regexes[i]: self.stdin_responses[i] for i in range(len(self.stdin_regexes))}

        self.log(f"Executing command: {self.cmd}")
        command_response = self.sshobj.exec(cmd=self.cmd, timeout=int(self.timeout), stdin=stdin, remove_banner=self.remove_banner)
        self.output = command_response.stdout
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
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
            self.logger.add_azure_build_tag('cisco-ssh-exec-failed')
            raise error


class CiscoShowIpInterfaceBrief(Node):
    name: str = "Cisco SSH: Show IP Interface Brief"
    description: str = "Use an SSH connection to execute the 'show ip interface brief' command on a Cisco host. This command can be used to view a summary of the router interfaces (IP address, interface status, and additional information)."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )

    output = ListOutputSocket(datatype=DataContainer, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
        self.connection = self.sshobj
        error = None
        self.log(f"Executing command: 'show ip interface brief'")
        for i in range(4):
            try:
                self.output = self.sshobj.show_ip_interface_brief()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.output, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class CiscoShowLicenseUsage(Node):
    name: str = "Cisco SSH: Show License Usage"
    description: str = (
        "Use an SSH connection to execute the 'show license usage' command on a Cisco host. This command provides information about the license on the host."
    )
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )

    output = OutputSocket(datatype=DataContainer, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
        self.connection = self.sshobj
        error = None
        self.log(f"Executing command: 'show license usage'")
        for i in range(4):
            try:
                self.output = self.sshobj.show_license_usage()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.output, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class CiscoShowFlowExporter(Node):
    name: str = "Cisco SSH: Show Flow Exporter"
    description: str = "Use an SSH connection to execute the 'show running-config flow exporter' command on a Cisco Virtual Machine. This command shows the configuration commands of the flow exporter (i.e. Netflow)."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )

    output = ListOutputSocket(datatype=DataContainer, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
        self.connection = self.sshobj
        error = None
        self.log(f"Executing command: 'show running-config flow exporter'")
        for i in range(4):
            try:
                self.output = self.sshobj.get_flow_exporter_info()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.output, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class CiscoShowIpOSPFNeighbor(Node):
    name: str = "Cisco SSH: Show IP OSPF Neighbor"
    description: str = "Use an SSH connection to execute the 'show ip ospf neighbor' command on a Cisco Virtual Machine. This command shows the IP Open Shortest Path First (OSPF) information."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )

    output = ListOutputSocket(datatype=DataContainer, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
        self.connection = self.sshobj
        error = None
        self.log(f"Executing command: 'show ip ospf neighbor'")
        for i in range(4):
            try:
                self.output = self.sshobj.show_ip_ospf_neighbor()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.output, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class CiscoShowLogging(Node):
    name: str = "Cisco SSH: Show Logging Trap Info"
    description: str = "Use an SSH connection to execute the 'show logging' command on a Cisco Virtual Machine and get the trap information. This command displays the state of logging (syslog)."
    categories: typing.List[str] = ["Remote Connections", "SSH", "Cisco"]
    color: str = esxi_constants.COLOR_CISCO_SSH_CONNECTION

    sshobj = InputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="SSH Connection",
        description="A previously opened SSH connection object to execute over. This must be an SSH connection to a Cisco host.",
    )

    output = ListOutputSocket(datatype=DataContainer, name="Output", description="The output from the command response.")
    connection = OutputSocket(
        datatype=datatypes.CiscoSSHConnection,
        name="Cisco SSH Connection",
        description="A reusable Cisco SSH connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.sshobj._ip}] "

    def run(self):
        assert isinstance(self.sshobj, esxi_utils.util.connect.CiscoSSHConnection), f"Not a Cisco SSH connection"
        self.connection = self.sshobj
        error = None
        self.log(f"Executing command: 'show logging'")
        for i in range(4):
            try:
                self.output = self.sshobj.get_logging_trap_info()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.output, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error
