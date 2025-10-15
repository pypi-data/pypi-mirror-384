from graphex import String, Number, Boolean, DataContainer, InputSocket, Node, OptionalInputSocket, OutputSocket, ListOutputSocket, VariableOutputSocket
from graphex_esxi_utils import datatypes, esxi_constants, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
from graphex import exceptions as graphex_exceptions
from graphex_esxi_utils.utils import misc as misc_utils
from graphex_esxi_utils.utils import palo_alto as palo_alto_util_fns
from graphex_esxi_utils import panos_constants
import esxi_utils
import ipaddress
import requests
import typing
import time
import json
import re
import os


class EsxiTestPanosApiConnection(Node):
    name: str = "ESXi Test PAN-OS API Connection"
    description: str = "Check if an PAN-OS API connection can be established to a virtual machine by continuously retrying a connection. This effectively waits for a connection to be available. Only valid for PAN-OS Virtual Machines."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    ip = InputSocket(datatype=String, name="IP", description="The IP of an interface on the VM to connect to.")
    username = InputSocket(datatype=String, name="Username", description="The username of the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    retries = InputSocket(datatype=Number, name="Retries", description="The maximum number of connection attempts to make.", input_field=10)
    delay = InputSocket(datatype=Number, name="Delay", description="The time to wait between each connection attempt.", input_field=5)
    error_on_failure = InputSocket(
        datatype=Boolean, name="Error on Failure?", description="Whether to raise an error when a connection could not be established.", input_field=False
    )
    keep_open = InputSocket(
        datatype=Boolean,
        name="Keep Connection Open",
        description="Whether to keep the connection open so that a usable connection object is returned. If this is False, the 'PAN-OS API Connection' output will be disabled.",
        input_field=False,
    )

    success = OutputSocket(datatype=Boolean, name="Connection Available", description="Whether a connection could be established to the virtual machine.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="A reusable PAN-OS API connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), f"Not a Palo-Alto Firewall Virtual Machine! Name is: {self.vm.name} and OS type is: {self.vm.ostype}"
        self.disable_output_socket("PAN-OS API Connection")
        ipAddr = str(ipaddress.IPv4Address(self.ip))
        self.log(f'Testing PAN-OS API connection using IP "{ipAddr}" and username "{self.username}"')
        conn: esxi_utils.util.connect.PanosAPIConnection = self.vm.api(ipAddr, self.username, self.password)

        error = None
        try:
            if not conn.wait(retries=int(self.retries), delay=int(self.delay), keep_open=self.keep_open):
                raise RuntimeError(f"Max attempts reached")
        except Exception as e:
            error = RuntimeError(
                f'PAN-OS API connection could not be established to virtual machine "{self.vm.name}" using IP "{ipAddr}" and username "{self.username}": {str(e)}'
            )

        if error:
            self.success = False
            conn.close()
            self.debug(str(error))
            if self.error_on_failure:
                raise error
        else:
            self.success = True
            self.debug(f'PAN-OS API connection OK using IP "{ipAddr}" and username "{self.username}"')
        
            if self.keep_open:

                def close_connection():
                    if conn._connection:
                        self.debug(f"Closing connection.")
                        conn.close()

                self.defer(close_connection)
                self.connection = conn


class EsxiOpenPanosApiConnection(Node):
    name: str = "ESXi Open PAN-OS API Connection"
    description: str = "Attempts to establish a PAN-OS API connection. You can reuse this object when making executing PAN-OS API commands."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    ip = InputSocket(datatype=String, name="IP", description="The IP of an interface on the VM to connect to.")
    username = InputSocket(datatype=String, name="Username", description="The username of the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    output = VariableOutputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A reusable PAN-OS API connection to execute commands over."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.output = datatypes.PanosAPIConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.vm)


class EsxiClosePanosApiConnection(Node):
    name: str = "ESXi Close PAN-OS API Connection"
    description: str = "Close an open PAN-OS API connection. The connection object will no longer be usable for PAN-OS API operations. If the PAN-OS API object is already closed, this will do nothing."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        if self.apiobj._connection:
            self.debug(f"Closing connection.")
            self.apiobj.close()


class EsxiPanosApiExec(Node):
    name: str = "ESXi PAN-OS API Exec"
    description: str = "Use a PAN-OS API connection to execute a command on the remote end of this connection. This will block until the associated command has finished. Acceptable commands can be found use https://<firewall ip>/api under operations"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )
    cmd = InputSocket(datatype=String, name="Command", description="The command to execute on the VM using the PAN-OS API.")
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    assert_success = OptionalInputSocket(
        datatype=Boolean,
        name="Assert Success",
        description="Assert that the command completes without error. If not value is provided, no assertion is made and checking the status is left to the caller.",
    )

    output = OutputSocket(datatype=String, name="Output", description="The command response.")
    success = OutputSocket(datatype=Boolean, name="Success", description="Whether the command completed successfully.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.apiobj._ip}] "
        else:
            return f"[{self.name} - {self.apiobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        self.log(f"Executing command: {self.cmd}")
        command_response = self.apiobj.exec(cmd=self.cmd)

        self.success = command_response.status == 0
        self.output = command_response.stdout

        if self.assert_success is not None and not self.success:
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            raise exceptions.PanosApiExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        self.connection = self.apiobj
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


class EsxiPanosApiShowAllInterfaces(Node):
    name: str = "ESXi PAN-OS API Show Interfaces"
    description: str = "Use a PAN-OS API connection to execute the 'show interface all' command on a PAN-OS Virtual Machine. This command provides information about the interfaces on the firewall."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    logical_interfaces = ListOutputSocket(datatype=DataContainer, name="Logical Interfaces", description="Data about the logical interfaces on the firewall.")
    hardware_interfaces = ListOutputSocket(
        datatype=DataContainer, name="Hardware Interfaces", description="Data about the hardware interfaces on the firewall."
    )
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        self.connection = self.apiobj
        error = None
        self.log(f"Getting Interface Information")
        for i in range(4):
            try:
                data = self.apiobj.show_all_interfaces()
                self.logical_interfaces = data["logical_interfaces"]
                self.hardware_interfaces = data["hardware_interfaces"]
                self.debug(f"Logical Interfaces:\n" + re.sub("^", "  │  ", json.dumps(self.logical_interfaces, indent=2), flags=re.MULTILINE))
                self.debug(f"Hardware Interfaces:\n" + re.sub("^", "  │  ", json.dumps(self.hardware_interfaces, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class EsxiPanosApiGetNetflowServerProfiles(Node):
    name: str = "ESXi PAN-OS API Get Netflow Server Profiles"
    description: str = "Use a PAN-OS API connection to execute the 'show config running xpath shared/server-profile/netflow' command on a PAN-OS Virtual Machine. This command provides information about the Netflow server settings."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    data = ListOutputSocket(datatype=DataContainer, name="Data", description="Data about the Netflow server settings on the firewall.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        self.connection = self.apiobj
        error = None
        self.log(f"Getting Netflow Server Settings")
        for i in range(4):
            try:
                self.data = self.apiobj.get_netflow_server_profiles()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.data, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class EsxiPanosApiGetRoutingOSPF(Node):
    name: str = "ESXi PAN-OS API Get Routing OSPF"
    description: str = "Use a PAN-OS API connection to execute the 'show routing route type ospf' command on a PAN-OS Virtual Machine. This command provides information about OSPF routing on the firewall."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    data = OutputSocket(datatype=DataContainer, name="Data", description="Data about OSPF routing on the firewall.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        self.connection = self.apiobj
        error = None
        self.log(f"Getting OSPF Routing Data")
        for i in range(4):
            try:
                self.data = self.apiobj.show_routing_ospf()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.data, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class EsxiPanosApiGetPanoramaStatus(Node):
    name: str = "ESXi PAN-OS API Get Panorama Status"
    description: str = "Use a PAN-OS API connection to execute the 'show panorama-status' command on a PAN-OS Virtual Machine. This command provides information about connected Panorama server."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    data = ListOutputSocket(datatype=DataContainer, name="Data", description="Data about connected Panorama server on the firewall.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        self.connection = self.apiobj
        error = None
        self.log(f"Getting Panorama Server Data")
        for i in range(4):
            try:
                self.data = self.apiobj.get_panorama_status()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.data, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class EsxiPanosApiGetSyslogSettings(Node):
    name: str = "ESXi PAN-OS API Get Syslog Settings"
    description: str = "Use a PAN-OS API connection to execute the 'show config running xpath panorama/log-settings/syslog' command on a PAN-OS Virtual Machine. This command provides information about syslog forwarding."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    apiobj = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PAN-OS API Connection", description="A previously opened PAN-OS API connection object to execute over."
    )

    data = ListOutputSocket(datatype=DataContainer, name="Data", description="Data about syslog forwarding on the firewall.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.apiobj._ip}] "

    def run(self):
        self.connection = self.apiobj
        error = None
        self.log(f"Getting Syslog Data")
        for i in range(4):
            try:
                self.data = self.apiobj.get_panorama_syslog_settings()
                self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.data, indent=2), flags=re.MULTILINE))
                return  # OK
            except Exception as e:
                error = e
        if error:
            raise error


class EsxiVirtualMachinePanoramaAssignSerialNumber(Node):
    name: str = "ESXi Panos VM Assign (Set) Panorama Serial Number"
    description: str = "Gives the Palo Alto VM a serial number. This is only tested on Panorama devices and not recommended for use on firewalls."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    # Inputs
    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    serial_no = InputSocket(datatype=String, name="Serial Number", description="The serial number to assign to this Panorama VM.")
    use_api = InputSocket(datatype=Boolean, name="Use API?", description="When True: use the API. When False: use SSH.", input_field=True)
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8 * 60)

    # Outputs
    stdout = OutputSocket(datatype=String, name="Response Text", description="The text from the command response (either HTTP for API or stdout for SSH).")

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))

        self.log(f"Setting Panorama Serial Number...")

        start_time = time.time()
        if self.use_api:
            while True:
                try:
                    http_res = self.panos_api.assign_serial_number(self.serial_no)
                    if 'response status="success"' not in http_res.text:
                        raise exceptions.PaloAltoApiError("Serial Assignment via HTTP", f"ERROR: failed to set the device serial number!: {str(http_res.text)}")
                    command_response = http_res
                    break
                except Exception as e:
                    if misc_utils.timeout(start_time, self.timeout):
                        raise exceptions.PaloAltoApiError(
                            "Serial Assignment via HTTP", f"ERROR: timeout while waiting to set the device serial number! {str(e)}"
                        )
                    self.log("Failed to connect... retrying...")
                    time.sleep(10)
            self.stdout = command_response.text
            self.debug(f"API Response:\n" + re.sub(r"^\s*", "  │  ", command_response.text, flags=re.MULTILINE))
        else:  # use SSH
            while True:
                try:
                    with esxi_utils.util.connect.PanosSSHConnection(ip_addr, self.panos_api._username, self.panos_api._password) as conn:
                        command_response = conn.exec(f"set serial-number {self.serial_no}")
                        break
                except Exception:
                    if misc_utils.timeout(start_time, self.timeout):
                        raise exceptions.PaloAltoApiError(f"set serial-number {self.serial_no}", f"ERROR: timeout while setting serial number via SSH!")
                    self.log("Failed to connect... retrying...")
                    time.sleep(10)
            self.stdout = command_response.stdout
            self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachinePaloAltoShutdown(Node):
    name: str = "ESXi Panos VM Shutdown"
    description: str = "Perform a graceful shutdown of the VM using `request shutdown system`. This may take longer than usual and the connection may be severed in the process."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    timeout = InputSocket(
        datatype=Number, name="Timeout", description="How many seconds to retry the shutdown for before throwing a timeout error.", input_field=15 * 60
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        self.log(f"Performing graceful shutdown...")
        str(ipaddress.IPv4Address(self.panos_api._ip))
        start_time = time.time()
        # Loop until return or timeout
        while True:
            try:
                cmd = "request shutdown system"
                res = self.panos_api.exec(cmd)
                res_msg = str(res.stdout)
                if "invalid password" in res_msg.lower():
                    raise exceptions.PaloAltoApiError(cmd, f'ERROR: "Invalid password" response from VM... This may be the wrong VM. Response: {res.stdout}')
                if palo_alto_util_fns.api_conn_refused(res_msg):
                    if misc_utils.timeout(start_time, self.timeout):
                        raise exceptions.PaloAltoApiError(cmd, "ERROR: timeout while trying to shutdown VM!")
                    self.log("failed to connect to shutdown... retrying...")
                    self.debug(f"Error response from VM: {res_msg}")
                    time.sleep(10)
                    continue
                return res
            except Exception as e:
                self.log("Shutdown command was interrupted. Manually check that the VM is shutting down (or already powered off).")
                self.debug(f"The Exception: {str(e)}")
                return None


class EsxiVirtualMachinePaloAltoTime(Node):
    name: str = "ESXi Panos VM Time"
    description: str = "Get the current time set on the remote host by executing 'show clock'. There used to be a duplicate node for this called 'ESXi Palo Alto VM Get Clock'."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    output = OutputSocket(datatype=String, name="Datetime String", description="A 'datetime' representation of the set clock time.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def run(self):
        self.output = str(self.panos_api.time())
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoImportConfigurationFile(Node):
    name: str = "ESXi Panos VM Import Configuration File"
    description: str = "Import a configuration file to the VM via HTTP. You will still have to install it separately afterward (this can be automated using Palo Alto Guest Tools)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    path_to_file = InputSocket(
        datatype=String, name="Path to File", description="The configuration file you want to import into the VM. Will be read in and transferred as binary."
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8 * 60)

    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))
        self.log(f"Importing Configuraton {self.path_to_file}")
        start_time = time.time()
        while True:
            try:
                command_response: requests.Response = self.panos_api.import_configuration_file(os.path.abspath(self.path_to_file))
                if 'response status="success"' not in command_response.text:
                    raise exceptions.PaloAltoImportError("configuration", str(command_response.text))
                break
            except Exception as e:
                if misc_utils.timeout(start_time, self.timeout):
                    raise exceptions.PaloAltoImportError("configuration", f"Timeout while waiting to import configuration file!: {str(e)}")
                self.log(f"Failed to connect to {ip_addr}... retrying...")
                time.sleep(10)
        self.debug(f"API Response:\n" + re.sub(r"^\s*", "  │  ", command_response.text, flags=re.MULTILINE))
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoImportSoftwareFile(Node):
    name: str = "ESXi Panos VM Import Software File"
    description: str = "Import a software file to the VM via HTTP. You will still have to install it separately afterward."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    path_to_file = InputSocket(
        datatype=String, name="Path to File", description="The software file you want to import into the VM. Will be read in and transferred as binary."
    )
    import_category = InputSocket(
        datatype=String,
        name="Import Category",
        description="The category is what 'type' of software this is, frequent examples are: for anti-virus use: 'anti-virus' (or antivirus), for apps or content use: 'content' (or application_contents), for primary software version use: 'software'. Other values are allowed but there is no guarentee that they will work.",
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8 * 60)

    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))
        self.log(f"Importing Software File {self.path_to_file}")
        start_time = time.time()
        try:
            software_type = panos_constants.import_category_dict[self.import_category]
        except Exception:
            software_type = self.import_category
        while True:
            http_res = None
            try:
                http_res = self.panos_api.import_software_file(self.path_to_file, software_type)
                if 'response status="success"' not in http_res.text:
                    raise exceptions.PaloAltoImportError(f"software ({software_type})", str(http_res.text))
                break
            except Exception as e:
                if misc_utils.timeout(start_time, self.timeout):
                    raise exceptions.PaloAltoImportError("configuration", f"Timeout while waiting to import software ({software_type}) file!: {str(e)}")
                self.debug(f"Failed to import software file. Credentials used were hostname: {str(ip_addr)} ... username: {str(self.panos_api._username)}")
                self.debug(f"Caught exception: {str(e)}")
                if http_res:
                    self.debug(f"HTTP response: {str(http_res)}")
                self.log("Failed to connect... retrying...")
                time.sleep(10)
        self.debug(f"API Response:\n" + re.sub(r"^\s*", "  │  ", http_res.text, flags=re.MULTILINE))
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoInstallLicenseFile(Node):
    name: str = "ESXi Panos VM Install License File"
    description: str = "Install a license file on the VM via HTTP."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    path_to_file = InputSocket(
        datatype=String, name="Path to File", description="The license file you want to install. Will be sent as URL encoded plaintext to the VM via HTTP."
    )
    primary_fw_license = InputSocket(
        datatype=Boolean,
        name="Primary Firewall License?",
        description="Set this parameter to True if you are installing the Firewall license (NOT Panorama) that contains the serial number (PA-VM). All other license files (including supporting licenses for firewalls [such as threats]) should set this to False",
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8 * 60)

    http_res = OutputSocket(datatype=String, name="Response Text", description="A response description of the attempted operation.")

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        self.log(f"Importing License File {self.path_to_file} (Primary={self.primary_fw_license})")
        start_time = time.time()
        connected = False
        http_res = None
        while not connected:
            try:
                http_res = self.panos_api.install_license_file(self.path_to_file)
                connected = True
                break
            except Exception as e:
                if self.primary_fw_license:
                    http_res = None
                    break
                if misc_utils.timeout(start_time, self.timeout):
                    raise exceptions.PaloAltoImportError(f"license", f"timeout while waiting to import license file! {str(e)}")
                self.log("Failed to connect... retrying...")
                time.sleep(10)
        if (http_res is not None and "Successfully installed license key" not in http_res.text) or (http_res is None and not self.primary_fw_license):
            error_msg = http_res.text if http_res else "No HTTP response from VM, the http_res variable is None"
            raise exceptions.PaloAltoImportError(f"license", f"ERROR: Failed to install license key at path: {self.path_to_file} ... {error_msg}")
        self.http_res = http_res.text if http_res else ""
        if http_res:
            self.debug(f"API Response:\n" + re.sub(r"^\s*", "  │  ", http_res.text, flags=re.MULTILINE))


class EsxiVirtualMachinePaloAltoGetLicenseInfo(Node):
    name: str = "ESXi Panos VM Get License Info"
    description: str = "Returns the licenses currently installed on this device as a list of PaloAltoLicenseInfo objects."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=15 * 60)

    output = ListOutputSocket(
        datatype=datatypes.PaloAltoLicenseInfo,
        name="Installed License Files",
        description="A list of licenses that are currently installed on the provided VM.",
    )
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        list_of_named_tuples = palo_alto_util_fns.get_license_info(api=self.panos_api, logger_function=self.log, timeout=int(self.timeout))
        """
        :return:
        A list of namedtuple objects. The list will be empty if no licenses are installed.
        The namedtuple attributes (in order) are:
        - feature (str)
        - description (str)
        - serial (str)
        - issued (datetime.date/None)
        - expires (datetime.date/None)
        - expired (bool)
        - authcode (str/None)
        """
        found_licenses = []
        for namedtpl in list_of_named_tuples:
            temp = dict()
            temp["feature"] = namedtpl[0]
            temp["description"] = namedtpl[1]
            temp["serial"] = namedtpl[2]
            temp["issued"] = namedtpl[3]
            temp["expires"] = namedtpl[4]
            temp["expired"] = namedtpl[5]
            temp["authcode"] = namedtpl[6]
            found_licenses.append(temp)
        self.output = found_licenses
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoReboot(Node):
    name: str = "ESXi Panos VM Graceful Restart / Reboot"
    description: str = "Gracefully restarts the given vm instance. Uses the 'request restart system' command via the Palo Alto API."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    wait_for_boot = InputSocket(
        datatype=Boolean,
        name="Wait for Boot?",
        description="Whether to wait for VM to boot and be ready for interaction or not (highly recommended you leave this set to True).",
        input_field=True,
    )

    interaction_timeout = InputSocket(
        datatype=Number,
        name="Interaction Timeout",
        description="After the VM reboots, how long to wait (in seconds) for the VM connection to become 'available' before throwing a timeout error",
        input_field=20 * 60,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        self.log(f"Gracefully Rebooting...")
        palo_alto_util_fns.restart_vm(
            api=self.panos_api, logger_function=self.log, wait_for_boot=self.wait_for_boot, connect_wait_time=int(self.interaction_timeout)
        )


class EsxiVirtualMachinePaloAltoGetInstalledSwVersion(Node):
    name: str = "ESXi Panos VM Get Installed Software Version"
    description: str = "Parses out the 'show system info' command to find the current software version of this VM. Will raise an 'PaloAltoVersionError' exception if this fails in any way."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    swv = OutputSocket(datatype=String, name="Software Version", description="The software version assigned to this VM.")
    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        sw_version = palo_alto_util_fns.get_software_version(api=self.panos_api, logger_function=self.log)

        if sw_version is None:
            raise exceptions.PaloAltoVersionError("ERROR: Unable to determine the currently installed software version!")

        self.swv = sw_version
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoDownloadSoftwareFile(Node):
    name: str = "ESXi Panos VM Download Software File"
    description: str = "Downloads the requested software type from Palo Alto's servers. The command run depends on the 'Software Type' given. Valid inputs are 'antivirus', 'application_contents',  'apps', 'wildfire', 'global-protect-client', and 'global-protect-clientless-vpn'. You can also provide 'software' for the primary software version. Note that 'latest' cannot be provided as a software version for 'global-protect-client'."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    sw_type = InputSocket(datatype=String, name="Software Type", description="The type of software to download.")
    sw_version = InputSocket(datatype=String, name="Software Version", description="The software version to download.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=6 * 60)

    connection = OutputSocket(
        datatype=datatypes.PanosAPIConnection,
        name="PAN-OS API Connection",
        description="The PAN-OS API Connection (same as input). This maybe be used to 'chain' multiple PAN-OS API operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        sw_type = self.sw_type.lower()
        valid_types = ["antivirus", "application_contents", "apps", "wildfire", "global-protect-client", "global-protect-clientless-vpn", "software"]
        if sw_type not in valid_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Software Type", sw_type, valid_types)

        self.log(f"Downloading Software File: Type={sw_type}, Version={self.sw_version}...")
        retried = False
        status = False
        version = self.sw_version
        software_type = self.sw_type
        if version == "latest":
            cmd = panos_constants.download_software_dict[software_type]
        elif software_type == panos_constants.SOFTWARE_KEY or software_type == panos_constants.GLOBAL_PROTECT_CLIENT_KEY:
            cmd = f'{panos_constants.download_software_dict[software_type]} "{version}"'
        else:
            cmd = panos_constants.download_software_dict[software_type].replace("latest", f'"{version}"')
        while not status:
            res = palo_alto_util_fns.wait_for_api_resp(
                api=self.panos_api,
                api_cmd=cmd,
                timeout_time=self.timeout,
                timeout_msg="ERROR: timeout while waiting to download software file!",
                logger_function=self.log,
            )
            res_msg = str(res.stdout)
            if "version" in res_msg and "not available" in res_msg:
                self.log_warning("WARN: Palo Alto claims version: {version} is unavailable for download... Retrying...")
                palo_alto_util_fns.check_software_versions(api=self.panos_api, logger_function=self.log)
                res = palo_alto_util_fns.wait_for_api_resp(
                    api=self.panos_api,
                    api_cmd=cmd,
                    timeout_time=self.timeout,
                    timeout_msg="ERROR: timeout while waiting to download software file!",
                    logger_function=self.log,
                )
            if software_type in panos_constants.import_category_dict:
                import_category = panos_constants.import_category_dict[software_type]
            else:
                import_category = "support"  # this really only changes the parsing
            job_number = palo_alto_util_fns.parse_job_number(res_msg, import_category, software_type)
            # wait for the install to finish
            self.log(f'"{software_type}" download enqueued job #{job_number} on VM... Awaiting completion...')
            status = palo_alto_util_fns.installing_wait_loop(
                software_name=software_type,
                job_number=job_number,
                api=self.panos_api,
                msg_name=f"online download of version {version}",
                exit_on_fail=False,
                logger_function=self.log,
            )
            if not status and retried:
                raise exceptions.PaloAltoInstallError(f"ERROR: Failed to download software twice for software type: {software_type}")
            elif not status and not retried:
                self.log_warning("WARN: Retrying software download...")
                retried = True
        self.log(f"Downloaded Software File: Type={sw_type}, Version={self.sw_version}")
        self.connection = self.panos_api


class EsxiVirtualMachinePaloAltoInstallSoftwareVersion(Node):
    name: str = "ESXi Panos VM Install Software Version"
    description: str = "Installs the requested software type that was previously downloaded from Palo Alto's servers (or primary 'software' types imported via the API [e.g. NOT support software]). The command run depends on the 'Software Type' given. Valid inputs are 'antivirus', 'application_contents',  'apps', 'wildfire', 'global-protect-client', and 'global-protect-clientless-vpn'. You can also provide 'software' for the primary software version. Note that 'latest' cannot be provided as a software version for 'global-protect-client'. This will not work for 'supporting' software files imported via the API."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    sw_type = InputSocket(datatype=String, name="Software Type", description="The type of software to install.")
    sw_version = InputSocket(datatype=String, name="Software Version", description="The software version to install.")

    timeout = InputSocket(
        datatype=Number,
        name="Confirmation Timeout",
        description="How long to wait for a confirmation of the start of the install before throwing a timeout error",
        input_field=6 * 60,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        sw_type = self.sw_type.lower()
        valid_types = ["antivirus", "application_contents", "apps", "wildfire", "global-protect-client", "global-protect-clientless-vpn", "software"]
        if sw_type not in valid_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Software Type", sw_type, valid_types)

        self.log(f"Installing Software File: Type={sw_type}, Version={self.sw_version}...")
        version = self.sw_version
        software_type = self.sw_type
        if version == "latest":
            cmd = panos_constants.online_software_install_dict[software_type]
        elif software_type == panos_constants.SOFTWARE_KEY or software_type == panos_constants.GLOBAL_PROTECT_CLIENT_KEY:
            cmd = f'{panos_constants.online_software_install_dict[software_type]} "{version}"'
        else:
            cmd = panos_constants.online_software_install_dict[software_type].replace("latest", f'"{version}"')
        res = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd=cmd,
            timeout_time=self.timeout,
            timeout_msg="ERROR: timeout while waiting to install software file!",
            logger_function=self.log,
        )
        if "Failed to schedule" in str(res.stdout):
            self.log_warning("WARN: Failed to schedule install job. Waiting 60 seconds and trying again...")
            time.sleep(60)
            self.log("Retrying software install...")
            res = palo_alto_util_fns.wait_for_api_resp(
                api=self.panos_api,
                api_cmd=cmd,
                timeout_time=self.timeout,
                timeout_msg="ERROR: timeout while waiting to install software file!",
                logger_function=self.log,
            )
        if software_type in panos_constants.import_category_dict:
            import_category = panos_constants.import_category_dict[software_type]
        else:
            import_category = "support"  # this really only changes the parsing
        job_number = palo_alto_util_fns.parse_job_number(str(res.stdout), import_category, software_type)
        # wait for the install to finish
        self.log(f'"{software_type}" online install enqueued job #{job_number} on VM... Awaiting completion...')
        palo_alto_util_fns.installing_wait_loop(
            software_name=software_type, job_number=job_number, api=self.panos_api, msg_name=f"online install of version {version}", logger_function=self.log
        )

        self.debug(f"Installed Software File: Type={sw_type}, Version={self.sw_version}")


class EsxiVirtualMachinePaloAltoInstallSupportSoftwareFileOffline(Node):
    name: str = "ESXi Panos VM (Offline) Install Support Software File"
    description: str = "Installs the requested software type that was previously imported via the Palo Alto API (via filename). The primary 'software' type can't be used here (even if you imported it via the API: installs via version instead of filename). The command run depends on the 'Software Type' given. Valid inputs are 'antivirus', 'application_contents',  'apps', 'wildfire', 'global-protect-client', and 'global-protect-clientless-vpn'."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS"]
    color: str = esxi_constants.COLOR_PANOS_API_CONNECTION

    panos_api = InputSocket(
        datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object."
    )

    sw_type = InputSocket(datatype=String, name="Software Type", description="The type of software to install.")
    filename = InputSocket(datatype=String, name="Filename", description="The name (basename, no path) of the software file to install on the Palo Alto VM.")

    timeout = InputSocket(
        datatype=Number,
        name="Confirmation Timeout",
        description="How long to wait for a confirmation of the start of the install before throwing a timeout error",
        input_field=6 * 60,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.panos_api._ip}] "

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        sw_type = self.sw_type.lower()
        valid_types = [
            "antivirus",
            "anti-virus",
            "content",
            "application_contents",
            "apps",
            "wildfire",
            "global-protect-client",
            "global-protect-clientless-vpn",
        ]
        if sw_type not in valid_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Software Type", sw_type, valid_types)

        self.log(f"Installing Software File: Type={sw_type}, Filename={self.filename}...")
        software_type = self.sw_type
        filename = self.filename
        # check that we have a key that will be accessable via dict
        if software_type == "anti-virus" or software_type == "antivirus":
            software_type = "antivirus"
        elif software_type == "content" or software_type == "apps" or software_type == "application_contents":
            software_type = "application_contents"
        elif software_type != "wildfire" and software_type != "global-protect-client" and software_type != "global-protect-clientless-vpn":
            raise exceptions.PaloAltoInstallError(f"Invalid support software type given to install: {software_type}")

        cmd = f'{panos_constants.install_software_dict[software_type]} "{filename}"'

        res = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd=cmd,
            timeout_time=self.timeout,
            timeout_msg="ERROR: timeout while waiting to install support software file!",
            logger_function=self.log,
        )

        if "Failed to schedule" in str(res.stdout) or "A commit is in progress" in str(res.stdout):
            self.log_warning(f"WARN: Unable to start install right now: {str(res.stdout)}. Waiting 60 seconds and trying again...")
            time.sleep(60)
            self.log("Retrying software install...")
            res = palo_alto_util_fns.wait_for_api_resp(
                api=self.panos_api,
                api_cmd=cmd,
                timeout_time=self.timeout,
                timeout_msg="ERROR: timeout while waiting to install software file!",
                logger_function=self.log,
            )

        if software_type in panos_constants.import_category_dict:
            import_category = panos_constants.import_category_dict[software_type]
        else:
            import_category = "support"  # this really only changes the parsing
        job_number = palo_alto_util_fns.parse_job_number(str(res.stdout), import_category, software_type)

        # wait for the install to finish
        self.log(f'"{software_type}" offline (support) install enqueued job #{job_number} on VM... Awaiting completion...')

        palo_alto_util_fns.installing_wait_loop(
            software_name=software_type, job_number=job_number, api=self.panos_api, msg_name=f"offline install of file {filename}", logger_function=self.log
        )
        self.debug(f"Installed Software File: Type={sw_type}, Filename={self.filename}")
