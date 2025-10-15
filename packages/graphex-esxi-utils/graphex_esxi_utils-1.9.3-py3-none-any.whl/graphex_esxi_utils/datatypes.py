from graphex_esxi_utils.utils import interactive_ssh
from graphex_esxi_utils import esxi_constants, exceptions
from graphex import exceptions as graphex_exceptions
from graphex import String, DataContainer, Runtime, Boolean, Number
from graphex.datatype import DataType
from graphex.compositeGraphInput import CompositeGraphInput, subGraphInput, subGraphEnumInput
import ipaddress
import esxi_utils
import typing
import json


########################
## ESXi Client Object ##
########################
def construct_esxi_client(runtime: Runtime, logger_info: typing.Callable, host_ip: str, username: str, password: str, child_ip: typing.Optional[str], child_user: typing.Optional[str], child_pass: typing.Optional[str]) -> esxi_utils.ESXiClient:
    try:
        #host_ip = str(ipaddress.IPv4Address(host_ip))
        if not child_ip or not child_user or not child_pass:
            logger_info(f"Connecting to ESXi server at: {host_ip}")
            client = esxi_utils.ESXiClient(host_ip, username, password)
        else:
            #child_ip = str(ipaddress.IPv4Address(child_ip))
            logger_info(f'Connecting to vCenter master/parent at: "{host_ip}" and child server at "{child_ip}"')
            client = esxi_utils.ESXiClient(
                host_ip, username, password, child_hostname=child_ip, child_username=child_user, child_password=child_pass
            )
        logger_info("Connection to ESXi server established.")

        def close_client():
            logger_info("Closing connection to ESXi server.")
            client.close()

        runtime.defer(close_client)
        return client
    except Exception as e:
        raise exceptions.EsxiConnectionFailedError(str(e))

ESXiClient = DataType(
    true_type=esxi_utils.ESXiClient, name="ESXi Client", description="A connection to an ESXI instance.", color=esxi_constants.COLOR_CLIENT, categories=["ESXi"],
    constructor=construct_esxi_client
) 

class ESXiClientInput(CompositeGraphInput):
    datatype = ESXiClient

    ip = subGraphInput(name='EsxiIP',datatype=String,description='The IP of the ESXi server to login to (the top level host in vCenter).')
    user = subGraphInput(name='EsxiUsername',datatype=String,description='The username to login to (requires administrative rights)')
    password = subGraphInput(name='EsxiPassword',datatype=String,description='The password for the username.')
    child_ip = subGraphInput(name='ChildEsxiIP',datatype=String,description='The child system\'s IP to login to (vCenter only).', defaultValue="")
    child_user = subGraphInput(name='ChildEsxiUsername',datatype=String,description='The child system\'s username to login to (vCenter only, requires administrative rights).', defaultValue="")
    child_pass = subGraphInput(name='ChildEsxiPassword',datatype=String,description="The password for the child system's username.", defaultValue="")

    def constructInput(self):
        if self.child_ip.strip() == "" or self.child_user == "" or self.child_pass == "":
            return ESXiClient.construct(self._runtime, self._runtime.logger.info, self.ip, self.user, self.password, None, None, None)
        return ESXiClient.construct(self._runtime, self._runtime.logger.info, self.ip, self.user, self.password, self.child_ip, self.child_user, self.child_pass)
    
@ESXiClient.cast(to=String)
def EsxiClient_to_string(value: esxi_utils.ESXiClient) -> str:
    return str(value)
########################


########################
## VM Object ##
########################
def construct_virtual_machine(creation_source: str, debug_logger: typing.Callable, esxi_client: esxi_utils.ESXiClient, name_or_id_input: str, is_id: bool, os_type: typing.Optional[str] = None) -> esxi_utils.vm.VirtualMachine:
    valid_os_types = ["cisco", "linux", "unix", "panos", "paloalto", "palo alto", "windows"]
    os_type_str = os_type.strip().lower() if os_type and os_type.strip().lower() != "default" else None 
    os_type = None
    if os_type_str is not None:
        if os_type_str not in valid_os_types:
            raise graphex_exceptions.InvalidParameterError(creation_source, "OS Type", os_type_str, valid_os_types)
        if os_type_str == "cisco":
            os_type = esxi_utils.vm.OSType.Cisco
        elif os_type_str == "linux" or os_type_str == "unix":
            os_type = esxi_utils.vm.OSType.Linux
        elif os_type_str == "windows":
            os_type = esxi_utils.vm.OSType.Windows
        elif os_type_str == "panos" or os_type_str == "paloalto" or os_type_str == "palo alto":
            os_type = esxi_utils.vm.OSType.PanOs
        else:
            # this code should never execute
            os_type = esxi_utils.vm.OSType.Unknown
    debug_logger(f'Getting Virtual Machine "{name_or_id_input}" from Host {esxi_client.hostname}')
    search_type = "id" if is_id else "name"
    try:
        return esxi_client.vms.get(name_or_id_input, ostype=os_type, search_type=search_type)
    except esxi_utils.util.exceptions.VirtualMachineNotFoundError as ve:
        if is_id and 'not found' in str(ve):
            raise exceptions.EsxiObjectDoesNotExistError(f"Virtual Machine with ID: \"{name_or_id_input}\" not found")
        else:
            raise ve


VirtualMachine = DataType(
    true_type=esxi_utils.vm.VirtualMachine,
    name="ESXi VM",
    description="An ESXI Virtual Machine (VM) instance.",
    color=esxi_constants.COLOR_VM,
    categories=["ESXi"],
    constructor=construct_virtual_machine
)

class VirtualMachineInput(CompositeGraphInput):
    datatype = VirtualMachine

    # ESXiClient values
    # ip = subGraphInput(name='EsxiIP',datatype=String,description='The IP of the ESXi server to login to (the top level host in vCenter).')
    # user = subGraphInput(name='EsxiUsername',datatype=String,description='The username to login to (requires administrative rights)')
    # password = subGraphInput(name='EsxiPassword',datatype=String,description='The password for the username.')
    # child_ip = subGraphInput(name='ChildEsxiIP',datatype=String,description='The child system\'s IP to login to (vCenter only).', defaultValue="")
    # child_user = subGraphInput(name='ChildEsxiUsername',datatype=String,description='The child system\'s username to login to (vCenter only, requires administrative rights).', defaultValue="")
    # child_pass = subGraphInput(name='ChildEsxiPassword',datatype=String,description="The password for the child system's username.", defaultValue="")
    
    # VirtualMachine values
    name_or_id = subGraphInput(name='VirtualMachineNameOrID',datatype=String,description='The name or ID of the VM to get from the ESXi Instance.')
    is_id = subGraphInput(name='UseID',datatype=Boolean,description="When True: Look for VM by ID instead of name.", defaultValue=False)
    os_type = subGraphEnumInput(name='OperatingSystemType',datatype=String,description="A string to overwrite the default operating system type. Valid values are: 'Cisco', 'Linux' or 'Unix', 'PanOS' or 'PaloAlto', 'Windows'", defaultValue="Default", enumMap={
        'Default': 'Default',
        'Cisco': 'Cisco',
        'Unix': 'Unix',
        'PanOS': 'PanOS',
        'Windows': 'Windows'
    })

    esxi_client = subGraphInput(name='ESXiClient',datatype=ESXiClient,description='ESXi Client')

    def constructInput(self):
        return VirtualMachine.construct("Composite Graph Input", self._runtime.logger.debug, self.esxi_client, self.name_or_id, self.is_id, self.os_type)

@VirtualMachine.cast(to=String)
def VM_to_string(value: esxi_utils.vm.VirtualMachine) -> str:
    return str(value)
########################


########################
## Datastore Object ##
########################
def construct_esxi_datastore(debug_logger: typing.Callable, esxi_client: esxi_utils.ESXiClient, search_name: str) -> esxi_utils.Datastore:
    debug_logger(f'Getting Datastore "{search_name}" from Host {esxi_client.hostname}')
    return esxi_client.datastores.get(search_name)

Datastore = DataType(
    true_type=esxi_utils.Datastore, name="ESXi Datastore", description="An ESXI Datastore instance.", color=esxi_constants.COLOR_DATASTORE, categories=["ESXi"],
    constructor=construct_esxi_datastore
)

class DatastoreInput(CompositeGraphInput):
    datatype = Datastore

    # ESXiClient values
    # ip = subGraphInput(name='EsxiIP',datatype=String,description='The IP of the ESXi server to login to (the top level host in vCenter).')
    # user = subGraphInput(name='EsxiUsername',datatype=String,description='The username to login to (requires administrative rights)')
    # password = subGraphInput(name='EsxiPassword',datatype=String,description='The password for the username.')
    # child_ip = subGraphInput(name='ChildEsxiIP',datatype=String,description='The child system\'s IP to login to (vCenter only).', defaultValue="")
    # child_user = subGraphInput(name='ChildEsxiUsername',datatype=String,description='The child system\'s username to login to (vCenter only, requires administrative rights).', defaultValue="")
    # child_pass = subGraphInput(name='ChildEsxiPassword',datatype=String,description="The password for the child system's username.", defaultValue="")

    # Datastore values
    search_name = subGraphInput(name='DatastoreName',datatype=String,description="The name of the datastore to get.")

    esxi_client = subGraphInput(name='ESXiClient',datatype=ESXiClient,description='ESXi Client')
    
    def constructInput(self):
        # construct the ESXiClient object
        # construct the VirtualMachine object
        return Datastore.construct(self._runtime.logger.debug, self.esxi_client, self.search_name)

@Datastore.cast(to=String)
def Datastore_to_string(value: esxi_utils.Datastore) -> str:
    return str(value)
########################


########################
## DatastoreFile Object ##
########################
DatastoreFile = DataType(
    true_type=esxi_utils.DatastoreFile,
    name="ESXi Datastore File",
    description="An ESXI Datastore File instance.",
    color=esxi_constants.COLOR_DATASTORE_FILE,
    categories=["ESXi"],
)

@DatastoreFile.cast(to=String)
def DatastoreFile_to_string(value: esxi_utils.DatastoreFile) -> str:
    return str(value)
########################


########################
## Portgroup Object ##
########################
Portgroup = DataType(
    true_type=esxi_utils.networking.PortGroup,
    name="ESXi Portgroup",
    description="An ESXI Portgroup instance.",
    color=esxi_constants.COLOR_PG,
    categories=["ESXi"],
)

@Portgroup.cast(to=String)
def Portgroup_to_string(value: esxi_utils.networking.PortGroup) -> str:
    return str(value)
########################


########################
## DistributedPortgroup Object ##
########################
DistributedPortgroup = DataType(
    true_type=esxi_utils.networking.DistributedPortGroup,
    name="ESXi Distributed Portgroup",
    description="An ESXI Distributed Portgroup instance.",
    color=esxi_constants.COLOR_DIS_PG,
    categories=["ESXi"],
)

@DistributedPortgroup.cast(to=String)
def DistributedPortgroup_to_string(value: esxi_utils.networking.DistributedPortGroup) -> str:
    return str(value)
########################


########################
## Switch Object ##
########################
Switch = DataType(
    true_type=esxi_utils.networking.VSwitch,
    name="ESXi vSwitch",
    description="An ESXI vSwitch instance.",
    color=esxi_constants.COLOR_SWITCH,
    categories=["ESXi"],
)

@Switch.cast(to=String)
def Switch_to_string(value: esxi_utils.networking.VSwitch) -> str:
    return str(value)
########################


########################
## DistributedSwitch Object ##
########################
DistributedSwitch = DataType(
    true_type=esxi_utils.networking.DistributedVSwitch,
    name="ESXi Distributed vSwitch",
    description="An ESXI Distributed vSwitch instance.",
    color=esxi_constants.COLOR_DIS_SWITCH,
    categories=["ESXi"],
)

@DistributedSwitch.cast(to=String)
def DistributedSwitch_to_string(value: esxi_utils.networking.DistributedVSwitch) -> str:
    return str(value)
########################


########################
## PhysicalNIC Object ##
########################
PhysicalNIC = DataType(
    true_type=esxi_utils.networking.PhysicalNIC,
    name="ESXi Physical NIC",
    description="An ESXI Physical NIC instance.",
    color=esxi_constants.COLOR_PHYSICAL_NIC,
    categories=["ESXi"],
)

@PhysicalNIC.cast(to=String)
def PhysicalNIC_to_string(value: esxi_utils.networking.PhysicalNIC) -> str:
    return str(value)
########################


########################
## VMKernelNIC Object ##
########################
VMKernelNIC = DataType(
    true_type=esxi_utils.networking.VMKernelNIC,
    name="ESXi VM Kernel NIC",
    description="An ESXI VM Kernel NIC instance.",
    color=esxi_constants.COLOR_KERNEL_NIC,
    categories=["ESXi"],
)

@VMKernelNIC.cast(to=String)
def VMKernelNIC_to_string(value: esxi_utils.networking.VMKernelNIC) -> str:
    return str(value)
########################


########################
## VirtualDevice Object ##
########################
VirtualDevice = DataType(
    true_type=esxi_utils.vm.hardware.VirtualDevice,
    name="ESXi Virtual Device",
    description="An ESXI Virtual Device connected to a VM.",
    color=esxi_constants.COLOR_VIRT_DEVICE,
    categories=["ESXi"],
)

@VirtualDevice.cast(to=String)
def VirtualDevice_to_string(value: esxi_utils.vm.hardware.VirtualDevice) -> str:
    return str(value)
########################


########################
## SSHConnection Object ##
########################
def construct_ssh_connection(runtime: Runtime, info_logger: typing.Callable, debug_logger: typing.Callable, ip: str, username: str, password: str, retries: int, retry_delay: float, keep_open: bool, connection_subtype: str = ""):
    ipAddr = str(ipaddress.IPv4Address(ip))
    error = None

    # Create the proper subtype for SSHConnection subtypes if specified in the constructor
    # If empty string is provided (""), then it is assumed we don't know what type of OS we are connecting to
    # (Which is the default super class object: SSHConnection)
    if connection_subtype.lower() == "unix":
        info_logger(f'Opening SSH connection to a Unix machine with IP "{ipAddr}" and username "{username}"')
        conn = esxi_utils.util.connect.UnixSSHConnection(ipAddr, username, password)
    elif connection_subtype.lower() == "cisco":
        info_logger(f'Opening SSH connection to a Cisco machine with IP "{ipAddr}" and username "{username}"')
        conn = esxi_utils.util.connect.CiscoSSHConnection(ipAddr, username, password)
    else:
        info_logger(f'Opening SSH connection using IP "{ipAddr}" and username "{username}"')
        conn = esxi_utils.util.connect.SSHConnection(ipAddr, username, password)

    try:
        if not conn.wait(retries=int(retries), delay=int(retry_delay), keep_open=keep_open):
            raise RuntimeError(f"Max attempts reached")
    except Exception as e:
        error = RuntimeError(f'SSH connection could not be established using IP "{ipAddr}" and username "{username}": {str(e)}')

    if error:
        conn.close()
        debug_logger(str(error))
        raise error
    else:
        debug_logger(f"SSH connection OK")
        if keep_open:
            def close_connection():
                if conn._connection:
                    debug_logger(f"Closing {connection_subtype} SSH connection.")
                    conn.close()
            runtime.defer(close_connection)
        return conn
# end construct_ssh_connection()

SSHConnection = DataType(
    true_type=esxi_utils.util.connect.SSHConnection,
    name="ESXi SSH Connection",
    description="An ESXI SSH connection.",
    color=esxi_constants.COLOR_SSH_CONNECTION,
    categories=["ESXi"],
    constructor=construct_ssh_connection
)

class SSHConnectionInput(CompositeGraphInput):
    datatype = SSHConnection

    ip = subGraphInput(name='IP',datatype=String,description="The IP of the machine to connect to.")
    username = subGraphInput(name='Username',datatype=String,description="The username of the user to login as.")
    password = subGraphInput(name='Password',datatype=String,description="The password for the user that is logging in.")
    retries = subGraphInput(name='Retries',datatype=Number,description="The maximum number of SSH connection attempts to make before failing.", defaultValue=10)
    retry_delay = subGraphInput(name='RetryDelay',datatype=Number,description="The time to wait between each SSH connection attempt (in seconds).", defaultValue=5)

    def constructInput(self):
        return SSHConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.ip, self.username, self.password, int(self.retries), self.retry_delay, True, "")

@SSHConnection.cast(to=String)
def SSHConnection_to_string(value: esxi_utils.util.connect.SSHConnection) -> str:
    return str(value)
########################


########################
## UnixSSHConnection Object ##
########################
UnixSSHConnection = DataType(
    true_type=esxi_utils.util.connect.UnixSSHConnection,
    name="ESXi Unix SSH Connection",
    description="An ESXI SSH connection to a 'Unix' OS.",
    color=esxi_constants.COLOR_UNIX_SSH_CONNECTION,
    categories=["ESXi"],
    constructor=construct_ssh_connection
)

class UnixSSHConnectionInput(CompositeGraphInput):
    datatype = UnixSSHConnection

    ip = subGraphInput(name='IP',datatype=String,description="The IP of the Unix machine to connect to.")
    username = subGraphInput(name='Username',datatype=String,description="The username of the user to login as.")
    password = subGraphInput(name='Password',datatype=String,description="The password for the user that is logging in.")
    retries = subGraphInput(name='Retries',datatype=Number,description="The maximum number of SSH connection attempts to make before failing.", defaultValue=10)
    retry_delay = subGraphInput(name='RetryDelay',datatype=Number,description="The time to wait between each SSH connection attempt (in seconds).", defaultValue=5)

    def constructInput(self):
        return UnixSSHConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.ip, self.username, self.password, int(self.retries), self.retry_delay, True, "unix")

@UnixSSHConnection.cast(to=String)
def UnixSSHConnection_to_string(value: esxi_utils.util.connect.UnixSSHConnection) -> str:
    return str(value)

@UnixSSHConnection.cast(to=SSHConnection)
def UnixSSHConnection_to_SSHConnection(value: esxi_utils.util.connect.UnixSSHConnection) -> esxi_utils.util.connect.SSHConnection:
    # since UnixSSHConnection is a subclass of SSHConnection, I think this should work well enough to just show the type cast in the UI
    return value
########################


########################
## CiscoSSHConnection Object ##
########################
CiscoSSHConnection = DataType(
    true_type=esxi_utils.util.connect.CiscoSSHConnection,
    name="ESXi Cisco SSH Connection",
    description="An ESXI SSH connection to a 'Cisco' OS (typically a router).",
    color=esxi_constants.COLOR_CISCO_SSH_CONNECTION,
    categories=["ESXi"],
    constructor=construct_ssh_connection
)

class CiscoSSHConnectionInput(CompositeGraphInput):
    datatype = CiscoSSHConnection

    ip = subGraphInput(name='IP',datatype=String,description="The IP of the Cisco machine to connect to.")
    username = subGraphInput(name='Username',datatype=String,description="The username of the user to login as.")
    password = subGraphInput(name='Password',datatype=String,description="The password for the user that is logging in.")
    retries = subGraphInput(name='Retries',datatype=Number,description="The maximum number of SSH connection attempts to make before failing.", defaultValue=10)
    retry_delay = subGraphInput(name='RetryDelay',datatype=Number,description="The time to wait between each SSH connection attempt (in seconds).", defaultValue=5)

    def constructInput(self):
        return CiscoSSHConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.ip, self.username, self.password, int(self.retries), self.retry_delay, True, "cisco")

@CiscoSSHConnection.cast(to=String)
def CiscoSSHConnection_to_string(value: esxi_utils.util.connect.CiscoSSHConnection) -> str:
    return str(value)

@CiscoSSHConnection.cast(to=SSHConnection)
def CiscoSSHConnection_to_SSHConnection(value: esxi_utils.util.connect.CiscoSSHConnection) -> esxi_utils.util.connect.SSHConnection:
    # since CiscoSSHConnection is a subclass of SSHConnection, I think this should work well enough to just show the type cast in the UI
    return value
########################


########################
## InteractiveSSHConnection Object ##
########################
def construct_interactive_ssh(runtime: Runtime, info_logger: typing.Callable, debug_logger: typing.Callable, ip: str, username: str, password: str, retries: int, retry_delay: float, keep_open: bool, encoding: str = 'utf-8', prompt: typing.Optional[str] = None, prompt_exact: typing.Optional[bool] = None) -> interactive_ssh.InteractiveSSHSession:
    ipAddr = str(ipaddress.IPv4Address(ip))
    error = None

    info_logger(f'Opening Interactive SSH connection using IP "{ipAddr}" and username "{username}"')
    conn = interactive_ssh.InteractiveSSHSession(
        hostname=ip,
        username=username,
        password=password,
        prompt=prompt,
        prompt_exact=False if not prompt_exact else True,
        encoding=encoding,
    )

    try:
        if not conn.wait(retries=int(retries), delay=int(retry_delay), keep_open=keep_open):
            raise RuntimeError(f"Max attempts reached")
    except Exception as e:
        error = RuntimeError(f'Interactive SSH connection could not be established using IP "{ipAddr}" and username "{username}": {str(e)}')

    if error:
        conn.close()
        debug_logger(str(error))
        raise error
    else:
        debug_logger(f'Interactive SSH connection OK using IP "{ipAddr}" and username "{username}"')
        if keep_open:
            def close_connection():
                if conn._proc:
                    debug_logger(f"Closing Interactive SSH connection.")
                    conn.close()
            runtime.defer(close_connection)
        return conn
# end construct_interactive_ssh()

InteractiveSSHConnection = DataType(
    true_type=interactive_ssh.InteractiveSSHSession,
    name="ESXi Interactive SSH Connection",
    description="An ESXI Interactive SSH connection.",
    color=esxi_constants.COLOR_INTERACTIVE_SSH,
    categories=["ESXi"],
    constructor=construct_interactive_ssh
)

class InteractiveSSHConnectionInput(CompositeGraphInput):
    datatype = InteractiveSSHConnection

    ip = subGraphInput(name='IP',datatype=String,description="The IP of the machine to connect to.")
    username = subGraphInput(name='Username',datatype=String,description="The username of the user to login as.")
    password = subGraphInput(name='Password',datatype=String,description="The password for the user that is logging in.")
    retries = subGraphInput(name='Retries',datatype=Number,description="The maximum number of SSH connection attempts to make before failing.", defaultValue=10)
    retry_delay = subGraphInput(name='RetryDelay',datatype=Number,description="The time to wait between each SSH connection attempt (in seconds).", defaultValue=5)

    def constructInput(self):
        return InteractiveSSHConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.ip, self.username, self.password, int(self.retries), self.retry_delay, True, "utf-8", None, None)

@InteractiveSSHConnection.cast(to=String)
def InteractiveSSHSession_to_string(value: interactive_ssh.InteractiveSSHSession) -> str:
    return str(value)
########################


########################
## WinRMConnection Object ##
########################
def construct_win_connection(runtime: Runtime, info_logger: typing.Callable, debug_logger: typing.Callable, ip: str, username: str, password: str, retries: int, retry_delay: float, keep_open: bool, domain: typing.Optional[str] = None, transport: str = "NTLM") -> esxi_utils.util.connect.WinRMConnection:
    ipAddr = str(ipaddress.IPv4Address(ip))
    error = None

    info_logger(f'Opening WinRM connection using IP "{ipAddr}" and username "{username}"')
    conn = esxi_utils.util.connect.WinRMConnection(
        ip=ipAddr, username=username, password=password, domain=domain, transport=transport.lower()
    )
        
    try:
        if not conn.wait(retries=int(retries), delay=int(retry_delay), keep_open=keep_open):
            raise RuntimeError(f"Max attempts reached")
    except Exception as e:
        error = RuntimeError(f'WinRM connection could not be established using IP "{ipAddr}" and username "{username}": {str(e)}')

    if error:
        conn.close()
        debug_logger(str(error))
        raise error
    else:
        debug_logger(f"WinRM connection OK")
        if keep_open:
            def close_connection():
                if conn._connection:
                    debug_logger(f"Closing WinRM connection.")
                    conn.close()
            runtime.defer(close_connection)
        return conn
# end construct_win_connection()

WinRMConnection = DataType(
    true_type=esxi_utils.util.connect.WinRMConnection,
    name="ESXi WinRM Connection",
    description="An ESXI WinRM connection.",
    color=esxi_constants.COLOR_WINRM_CONNECTION,
    categories=["ESXi"],
    constructor=construct_win_connection
)

class WinRMConnectionInput(CompositeGraphInput):
    datatype = WinRMConnection

    ip = subGraphInput(name='IP',datatype=String,description="The IP of the Windows machine to connect to.")
    username = subGraphInput(name='Username',datatype=String,description="The username of the user to login as.")
    password = subGraphInput(name='Password',datatype=String,description="The password for the user that is logging in.")
    retries = subGraphInput(name='Retries',datatype=Number,description="The maximum number of WinRM connection attempts to make before failing.", defaultValue=10)
    retry_delay = subGraphInput(name='RetryDelay',datatype=Number,description="The time to wait between each WinRM connection attempt (in seconds).", defaultValue=5)

    def constructInput(self):
        return WinRMConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.ip, self.username, self.password, int(self.retries), self.retry_delay, True, None, "NTLM")

@WinRMConnection.cast(to=String)
def WinRMConnection_to_string(value: esxi_utils.util.connect.WinRMConnection) -> str:
    return str(value)
########################


########################
## PanosAPIConnection Object ##
########################
def construct_panos_conn(runtime: Runtime, info_logger: typing.Callable, debug_logger: typing.Callable, ip: str, username: str, password: str, vm: esxi_utils.vm.VirtualMachine) -> esxi_utils.util.connect.PanosAPIConnection:
    assert isinstance(vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), f"Not a Palo-Alto Firewall Virtual Machine! Name is: {vm.name} and OS type is: {vm.ostype}"
    ipAddr = str(ipaddress.IPv4Address(ip))
    info_logger(f'Attempting connection using IP "{ipAddr}" and username "{username}".')
    conn = vm.api(ipAddr, username, password)
    conn.open()

    def close_connection():
        if conn._connection:
            debug_logger(f"Closing PanOS API connection.")
            conn.close()

    runtime.defer(close_connection)
    return conn

PanosAPIConnection = DataType(
    true_type=esxi_utils.util.connect.PanosAPIConnection,
    name="ESXi PAN-OS API Connection",
    description="An ESXI PAN-OS API Connection.",
    color=esxi_constants.COLOR_PANOS_API_CONNECTION,
    categories=["ESXi"],
    constructor=construct_panos_conn
)

class PanosAPIConnectionInput(CompositeGraphInput):
    datatype = PanosAPIConnection

    # ESXiClient values
    # TODO automatically pull these values from ESXiClientInput somehow?
    esxi_ip = subGraphInput(name='EsxiIP',datatype=String,description='The IP of the ESXi server to login to (the top level host in vCenter).')
    esxi_user = subGraphInput(name='EsxiUsername',datatype=String,description='The username to login to (requires administrative rights)')
    esxi_password = subGraphInput(name='EsxiPassword',datatype=String,description='The password for the username.')
    child_ip = subGraphInput(name='ChildEsxiIP',datatype=String,description='The child system\'s IP to login to (vCenter only).', defaultValue="")
    child_user = subGraphInput(name='ChildEsxiUsername',datatype=String,description='The child system\'s username to login to (vCenter only, requires administrative rights).', defaultValue="")
    child_pass = subGraphInput(name='ChildEsxiPassword',datatype=String,description="The password for the child system's username.", defaultValue="")

    # VirtualMachine values
    name_or_id = subGraphInput(name='VirtualMachineNameOrID',datatype=String,description='The name or ID of the VM to get from the ESXi Instance.')
    is_id = subGraphInput(name='UseID',datatype=Boolean,description="When True: Look for VM by ID instead of name.", defaultValue=False)

    # PanOS values
    vm_ip = subGraphInput(name='vmIP',datatype=String,description='The IP of the PanOS VM.')
    vm_user = subGraphInput(name='vmUsername',datatype=String,description='The user on the PanOS VM to use through the API (administrative rights may be required)')
    vm_password = subGraphInput(name='vmPassword',datatype=String,description='The password for the PanOS VM username.')

    def constructInput(self):
        # construct the ESXiClient object
        if self.child_ip.strip() == "" or self.child_user == "" or self.child_pass == "":
            client = ESXiClient.construct(self._runtime, self._runtime.logger.info, self.esxi_ip, self.esxi_user, self.esxi_password, None, None, None)
        else:
            client = ESXiClient.construct(self._runtime, self._runtime.logger.info, self.esxi_ip, self.esxi_user, self.esxi_password, self.child_ip, self.child_user, self.child_pass)

        # construct the VirtualMachine object
        vm = VirtualMachine.construct("Composite Graph Input", self._runtime.logger.debug, client, self.name_or_id, self.is_id, "PanOS")

        # construct the PanOS API Object
        return PanosAPIConnection.construct(self._runtime, self._runtime.logger.info, self._runtime.logger.debug, self.vm_ip, self.vm_user, self.vm_password, vm)

@PanosAPIConnection.cast(to=String)
def PanosAPIConnection_to_String(value: esxi_utils.util.connect.PanosAPIConnection) -> str:
    return str(value)
########################


########################
## PortgroupPort Object ##
########################
PortgroupPort = DataType(
    true_type=dict, name="ESXi Portgroup Port", description="An ESXI Portgroup Port dictionary.", color=esxi_constants.COLOR_PG_PORT, categories=["ESXi"]
)

@PortgroupPort.cast(to=String)
def PortgroupPort_to_string(value: dict) -> str:
    return str(value)

@PortgroupPort.cast(to=DataContainer)
def PortgroupPort_to_DataContainer(value: dict) -> dict:
    return value
########################


########################
## OvfFile Object ##
########################
OvfFile = DataType(
    true_type=esxi_utils.file.OvfFile,
    name="ESXi OVF File",
    description="An ESXI object representing an OVF file.",
    color=esxi_constants.COLOR_OVF_FILE,
    categories=["ESXi"],
)

@OvfFile.cast(to=String)
def OvfFile_to_string(value: esxi_utils.file.OvfFile) -> str:
    return str(value)
########################


########################
## PaloAltoLicenseInfo Object ##
########################
PaloAltoLicenseInfo = DataType(
    true_type=dict,
    name="ESXi Palo Alto License Info",
    description="An object that contains information about a Palo Alto license file.",
    color=esxi_constants.COLOR_PANOS_LICENSE_INFO,
    categories=["ESXi"],
)

@PaloAltoLicenseInfo.cast(to=String)
def PaloAltoLicenseInfo_to_string(d: dict) -> str:
    return json.dumps(d, indent=2, default=lambda x: str(x))

@PaloAltoLicenseInfo.cast(to=DataContainer)
def PaloAltoLicenseInfo_to_DataContainer(d: dict) -> dict:
    return d
########################


########################
## PaloAltoSoftwareInfo Object ##
########################
PaloAltoSoftwareInfo = DataType(
    true_type=dict,
    name="ESXi Palo Alto Software Info",
    description="An object that contains information about Palo Alto software.",
    color=esxi_constants.COLOR_PANOS_SW_INFO,
    categories=["ESXi"],
)

@PaloAltoSoftwareInfo.cast(to=String)
def PaloAltoSoftwareInfo_to_str(d: dict) -> str:
    return json.dumps(d, indent=2, default=lambda x: str(x))

@PaloAltoSoftwareInfo.cast(to=DataContainer)
def PaloAltoSoftwareInfo_to_DataContainer(d: dict) -> dict:
    return d
########################


########################
## ESXiFirewallRuleset Object ##
########################
ESXiFirewallRuleset = DataType(
    true_type=esxi_utils.firewall.Ruleset,
    name="ESXi Firewall Ruleset",
    description="A ruleset on the ESXi Firewall.",
    color=esxi_constants.COLOR_FIREWALL_RULESET,
    categories=["ESXi"],
)

@ESXiFirewallRuleset.cast(to=String)
def ESXiFirewallRuleset_to_string(value: esxi_utils.firewall.Ruleset) -> str:
    return str(value)
########################


########################
## ESXiFirewallRule Object ##
########################
ESXiFirewallRule = DataType(
    true_type=esxi_utils.firewall.Rule,
    name="ESXi Firewall Rule",
    description="A rule on an ESXi Firewall Ruleset.",
    color=esxi_constants.COLOR_FIREWALL_RULE,
    categories=["ESXi"],
)

@ESXiFirewallRule.cast(to=String)
def ESXiFirewallRule_to_string(value: esxi_utils.firewall.Rule) -> str:
    return str(value)
########################
