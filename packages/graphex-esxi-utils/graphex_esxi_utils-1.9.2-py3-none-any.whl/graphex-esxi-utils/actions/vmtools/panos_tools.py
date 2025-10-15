from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, OptionalInputSocket, ListInputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
import esxi_utils
import typing
import ipaddress


class EsxiVirtualMachineToolsPaloAltoCommand(Node):
    name: str = "ESXi Panos VM Tools Execute Command"
    description: str = "Emulates sending commands on the Palo Alto CLI by piping a list of command strings into the Palo Alto CLI binary. Bash will be used as the underlying shell for interaction with the Palo Alto CLI binary. Systems without bash will fail. Sudo is not supported on Palo Alto machines."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    cmd_list = ListInputSocket(
        datatype=String,
        name="Command List",
        description="A list of 'Palo Alto CLI' commands to execute. This function will raise an exception if an empty list is given.",
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    retry_timeout_minutes = InputSocket(
        datatype=Number,
        name="Retry Timeout (m)",
        description="Certain exceptions can cause a 'retry' of the command: This value represents how many minutes to keep 'retrying' for.",
    )
    list_delimiter = OptionalInputSocket(
        datatype=String,
        name="List Delimiter",
        description="How to separate commands in the list. Default is 'newline' separation, which simulates pressing enter on the CLI itself.",
    )
    output_pipe_cmd = OptionalInputSocket(
        datatype=String,
        name="Output Pipe Bash Command",
        description="An optional command (or series of commands) to pipe the output of the CLI into. THESE ARE BASH COMMANDS. This will not be delimited.",
    )
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        list_delimiter = self.list_delimiter if self.list_delimiter else "%s\n"
        output_pipe_command = self.output_pipe_cmd if self.output_pipe_cmd else ""
        bash_path = self.bash_path if self.bash_path else "/bin/bash"

        self.log(f"Executing PanOS commands: {self.cmd_list}")
        command_response = self.vm.tools.execute_panos_cmd(
            username=self.username,
            password=self.password,
            cmd_list=self.cmd_list,
            list_delimiter=list_delimiter,
            output_pipe_cmd=output_pipe_command,
            bash_path=bash_path,
            timeout=int(self.timeout),
            retry_timeout_minutes=int(self.retry_timeout_minutes),
        )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachineToolsPaloAltoShowSystemInfo(Node):
    name: str = "ESXi Panos VM Tools Show System Info"
    description: str = "Executes the command 'show system info' on the Palo Alto CLI."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f"Getting System Information...")
        command_response = self.vm.tools.show_system_info(username=self.username, password=self.password)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachineToolsPaloAltoGetIpAddr(Node):
    name: str = "ESXi Panos VM Tools Get IP Address"
    description: str = "Executes the command 'show system info' on the Palo Alto CLI and then does a linux 'grep' for 'ip-address'."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.", input_field="admin")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f"Getting IP Address...")
        command_response = self.vm.tools.get_ip_address(username=self.username, password=self.password)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachineToolsPaloAltoEnableServerVerification(Node):
    name: str = "ESXi Panos VM Tools Enable Server Verification"
    description: str = "Executes a series of Palo Alto CLI commands to enable server-verification: Enters 'configure' mode, executes 'set deviceconfig system server-verification yes', commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    enable = InputSocket(
        datatype=Boolean,
        name="Enable?",
        description="When set to True: enables server-verification. When False: disables server-verification (not recommended)",
        input_field=False,
    )
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"

        self.log(f"Enabling Server Verification...")
        command_response = self.vm.tools.enable_server_verification(username=self.username, password=self.password, enable=self.enable)
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))
        if "Configuration committed successfully" not in str(command_response.stdout):
            if self.enable:
                msg = "Failed to enable server verification!"
            else:
                msg = "Failed to disable server verification!"
            raise exceptions.PaloAltoToolsExecError(command_response.cmd, f"{msg}: {str(command_response)}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoSetIpAddress(Node):
    name: str = "ESXi Panos VM Tools Set IP Address"
    description: str = "Executes a series of Palo Alto CLI commands to change the IP address of the VM: enters 'configure' mode, executes 'set deviceconfig system ip-address....' and provides the given values as arguments, commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    ip_address = InputSocket(datatype=String, name="IP Address", description="The IP address to assign to the VM.")
    netmask = InputSocket(datatype=String, name="Netmask", description="The netmask to apply to the VM.")
    default_gateway = InputSocket(datatype=String, name="Default Gateway", description="The default gateway to apply the VM (can be Empty).")
    ip_type = InputSocket(
        datatype=String, name="Type", description="Known good value is 'static' (as in 'static IP'). Change at your own risk.", input_field="static"
    )
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        gateway = str(ipaddress.IPv4Address(self.default_gateway)) if self.default_gateway != "" and not self.default_gateway.isspace() else None
        ip_addr = str(ipaddress.IPv4Address(self.ip_address))
        netmask = str(ipaddress.IPv4Address(self.netmask))
        self.log(f"Setting IP Address: IP={ip_addr}, Netmask={netmask}, Gateway={gateway}")
        try:
            command_response = self.vm.tools.set_ip_address(
                username=self.username, password=self.password, ip_address=ip_addr, netmask=netmask, default_gateway=gateway, type=self.ip_type
            )
            self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

            if "Configuration committed successfully" not in str(command_response.stdout):
                raise exceptions.PaloAltoToolsExecError(command_response.cmd, f"Failed to set/commit new IP!: {str(command_response)}")
        except TimeoutError:
            self.log_warning(f"Timeout while trying to change IP. Checking if IP changed...")
            command_response = self.vm.tools.execute_panos_cmd(
                username=self.username, password=self.password, cmd_list=["show system info | match ip-address"], timeout=360
            )
            self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

            if str(ip_addr) not in str(command_response.stdout):
                raise exceptions.PaloAltoToolsExecError(
                    command_response.cmd, f"Failed to set/commit new IP (could not verify change after timeout)!: {str(command_response)}"
                )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoSetPassword(Node):
    name: str = "ESXi Panos VM Tools Set Password"
    description: str = "Executes a series of Palo Alto CLI commands to chage the password for the given username: enters 'configure' mode, executes 'set mgt-config users admin password', inputs the new_password (twice), commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    old_password = InputSocket(datatype=String, name="Old Password", description="The password for the user that is logging in.")
    new_password = InputSocket(datatype=String, name="New Password", description="The password to give to the provided username.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f"Setting Password...")
        try:
            command_response = self.vm.tools.set_password(username=self.username, old_password=self.old_password, new_password=self.new_password)
            self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

            self.status = command_response.status
            self.stdout = command_response.stdout
            self.stderr = command_response.stderr
        except Exception as e:
            self.debug(f"Change Password raised an exception. This is expected as the connection is typically severed. The exception: {str(e)}")


class EsxiVirtualMachineToolsPaloAltoCreateNewUser(Node):
    name: str = "ESXi Panos VM Tools Create New User"
    description: str = "Executes a series of Palo Alto CLI commands to create a new user on the VM: enters 'configure' mode, executes 'set mgt-config users <username> password', inputs the new_password (twice), commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    existing_admin_username = InputSocket(
        datatype=String, name="Existing Admin Username", description="The username of the virtual machine user admin that already exists.", input_field="admin"
    )
    existing_admin_password = InputSocket(
        datatype=String, name="Existing Admin Password", description="The password of the virtual machine user admin that already exists."
    )
    new_username = InputSocket(datatype=String, name="New Username", description="The username of the virtual machine user to create.")
    new_password = InputSocket(datatype=String, name="New User Password", description="The password to give to the provided (new) username.")

    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f'Creating user "{self.new_username}"...')
        command_response = self.vm.tools.create_new_user(
            existing_admin_username=self.existing_admin_username,
            existing_admin_password=self.existing_admin_password,
            new_username=self.new_username,
            new_password=self.new_password,
        )
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

        if not command_response.ok:
            raise exceptions.PaloAltoToolsExecError(command_response.cmd, f"Failed to create new user with name: {self.new_username}: {str(command_response)}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoGiveUserSuperuser(Node):
    name: str = "ESXi Panos VM Tools Give User Superuser Rights"
    description: str = "Executes a series of Palo Alto CLI commands to give superuser rights to the provided username: enters 'configure' mode, executes 'set mgt-config users <username> permissions role-based super<user/reader> yes', commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    existing_admin_username = InputSocket(
        datatype=String, name="Existing Admin Username", description="The username of the virtual machine user admin that already exists.", input_field="admin"
    )
    existing_admin_password = InputSocket(
        datatype=String, name="Existing Admin Password", description="The password of the virtual machine user admin that already exists."
    )
    username_granting_rights = InputSocket(
        datatype=String, name="Username To Make Super", description="The username of the virtual machine user to give rights to"
    )
    readonly = InputSocket(datatype=Boolean, name="Read Only?", description="Assign the role 'superreader' instead of 'superuser'", input_field=False)

    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f'Granting Superuser rights to "{self.username_granting_rights}"...')
        command_response = self.vm.tools.give_user_superuser_rights(
            existing_admin_username=self.existing_admin_username,
            existing_admin_password=self.existing_admin_password,
            username_to_give_rights_to=self.username_granting_rights,
            readonly=self.readonly,
        )
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

        if not command_response.ok:
            raise exceptions.PaloAltoToolsExecError(
                command_response.cmd,
                f"Failed to give 'super' rights to user with name: {self.username_granting_rights} using account: {self.existing_admin_username}: {str(command_response)}",
            )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoLoadConfigurationFile(Node):
    name: str = "ESXi Panos VM Tools Load Configuration File"
    description: str = "Executes a series of Palo Alto CLI commands to load an XML configuration file: enters 'configure' mode, executes 'load config from <filename>', commits changes"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    non_default_username = InputSocket(
        datatype=String,
        name="Non Default Username",
        description="The username of a VM 'superuser' that isn't the default user (e.g. NOT 'admin'). This is important because the default username typically has the password overwritten. Providing the only superuser on the VM (failing to follow this instruction) can put the VM into an 'bricked' state.",
    )
    password = InputSocket(datatype=String, name="Password", description="The password for the 'non_default_username'.")
    filename = InputSocket(datatype=String, name="Filename", description="The name of the file (NOT the path) to load.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        self.log(f'Loading configuration file "{self.filename}"...')
        command_response = self.vm.tools.load_configuration_file(non_default_username=self.non_default_username, password=self.password, filename=self.filename)
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

        if not command_response.ok:
            raise exceptions.PaloAltoToolsExecError(
                command_response.cmd,
                f"Failed to load configuration file: {self.filename} using account: {self.non_default_username} ... Response code is not 'OK': {str(command_response)}",
            )
        elif "does not exist" in str(command_response.stdout):
            raise exceptions.PaloAltoToolsExecError(
                command_response.cmd,
                f"ERROR: Failed to load configuration file: {self.filename} using account: {self.non_default_username} ... Configuration filename not found on VM!: {str(command_response)}",
            )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoSetPrimaryDns(Node):
    name: str = "ESXi Panos VM Tools Set Primary DNS Server"
    description: str = "Set the IP address to the primary DNS server. This is required to get access to upgrades from the internet. Does this by entering configure mode, executing 'set deviceconfig system dns-setting servers primary ___', and committing changes."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    dns_ip = InputSocket(datatype=String, name="DNS IP", description="the IP to the DNS server")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        dns_ip = str(ipaddress.IPv4Address(self.dns_ip))
        cmd = f"set deviceconfig system dns-setting servers primary {dns_ip}"

        self.log(f'Setting Primary DNS Server to "{self.dns_ip}"...')
        command_response = self.vm.tools.execute_panos_cmd(username=self.username, password=self.password, cmd_list=["configure t", cmd, "commit"])
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

        if "Configuration committed successfully" not in str(command_response.stdout):
            raise exceptions.PaloAltoToolsExecError(cmd, f"Failed to set/commit DNS IP!: {str(command_response)}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class EsxiVirtualMachineToolsPaloAltoDeleteDefaultGateway(Node):
    name: str = "ESXi Panos VM Tools Delete (Remove) Default Gateway"
    description: str = "Deletes the default gateway from the machine. Does this by entering configure mode, executing 'delete deviceconfig system default-gateway', and force committing changes."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Palo Alto"]
    color: str = esxi_constants.COLOR_PANOS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.", input_field="admin")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "Not a PaloAltoFirewallVirtualMachine"
        cmd = "delete deviceconfig system default-gateway"

        self.log(f"Removing Default Gateway...")
        command_response = self.vm.tools.execute_panos_cmd(username=self.username, password=self.password, cmd_list=["configure t", cmd, "commit"])
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

        if "Configuration committed successfully" not in str(command_response.stdout):
            raise exceptions.PaloAltoToolsExecError(cmd, f"Failed to delete default gateway!: {str(command_response)}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
