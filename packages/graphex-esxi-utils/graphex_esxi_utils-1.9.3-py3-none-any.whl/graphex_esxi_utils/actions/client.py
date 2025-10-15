from graphex import String, Boolean, DataContainer, Node, InputSocket, OptionalInputSocket, OutputSocket, ListOutputSocket, VariableOutputSocket, EnumInputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex import exceptions as graphex_exceptions
import esxi_utils
import typing
import json
import re


class ConnectToEsxi(Node):
    name: str = "Connect to ESXi"
    description: str = "Attempts to establish a connection to ESXi. Outputs a connection object instance for future reuse. The client will automatically disconnect at the end of the program."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    host_ip = InputSocket(datatype=String, name="Host/Master IP", description="The IP address or hostname of the ESXi server to login to.")
    username = InputSocket(datatype=String, name="Username", description="The username to login to (root is recommended)")
    password = InputSocket(datatype=String, name="Password", description="The password for the username.")
    child_ip = OptionalInputSocket(datatype=String, name="Child's IP (vCenter)", description="The child system's IP address or hostname to login to.")
    child_user = OptionalInputSocket(datatype=String, name="Child's Username (vCenter)", description="The child system's username to login to.")
    child_pass = OptionalInputSocket(datatype=String, name="Child's Password (vCenter)", description="The password for the child system's username.")

    output = VariableOutputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="A client object instance for a connection to ESXi.")

    def log_prefix(self):
        return f"[{self.name} - {self.child_user or self.username}@{self.child_ip or self.host_ip}] "

    def run(self):
        self.output = datatypes.ESXiClient.construct(self._runtime, self.log, self.host_ip, self.username, self.password, self.child_ip, self.child_user, self.child_pass)


class GetEsxiVm(Node):
    name: str = "Get ESXi VM"
    description: str = "Attempts to get a virtual machine from the ESXi Server. Will raise an exception if the virtual machine is not found."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the VM from.")
    name_or_id_input = InputSocket(datatype=String, name="VM Name or ID", description="The name or ID of the VM to get.")
    is_id = OptionalInputSocket(datatype=Boolean, name="Is ID?", description="When True: Look for VM by ID instead of name.")
    os_type = EnumInputSocket(
        datatype=String,
        name="OS Type",
        description="A string to overwrite the default operating system type. Valid values are: 'Cisco', 'Linux' or 'Unix', 'PanOS' or 'PaloAlto', 'Windows'. ESXi will only give you 'Unix' or 'Windows' if you choose 'Default' (e.g. if you want PanOS or Cisco: specifically select that in this dropdown). ",
        input_field='Default',
        enum_members=['Default', 'Cisco', 'Unix', 'PanOS', 'Windows']
    )
    output_vm = VariableOutputSocket(datatype=datatypes.VirtualMachine, name="ESXi VM", description="The object that represents the VM on the server.")

    def run(self):
        self.output_vm = datatypes.VirtualMachine.construct(self.name, self.debug, self.esxi_client, self.name_or_id_input, self.is_id, self.os_type)


class GetAllVms(Node):
    name: str = "Get All ESXi VMs"
    description: str = "Gets a list of all VMs on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the VMs from.")
    output_vms = ListOutputSocket(datatype=datatypes.VirtualMachine, name="ESXi VMs", description="A list of all VM objects on the server.")

    def run(self):
        self.debug(f"Getting all Virtual Machines from Host {self.esxi_client.hostname}")
        self.output_vms = self.esxi_client.vms.items


# class EsxiCloseClientConnection(Node):
#     name: str = "Disconnect From ESXi"
#     description: str = "Disconnects / closes connection to the provided ESXi server. The client will no longer be usable after calling this."
#     categories: typing.List[str] = ["ESXi", "Debugging"]
#     color: str = esxi_constants.COLOR_CLIENT

#     esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to disconnect from.")

#     def run(self):
#         client: esxi_utils.ESXiClient = self.esxi_client
#         self.log(f'Closing connection to {self.esxi_client}.')
#         client.close()


class GetAllDatastores(Node):
    name: str = "Get All ESXi Datastores"
    description: str = "Gets a list of all datastores on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the datastores from.")
    output_datastores = ListOutputSocket(datatype=datatypes.Datastore, name="ESXi Datastores", description="A list of all Datastore objects on the server.")

    def run(self):
        self.debug(f"Getting all Datastores from Host {self.esxi_client.hostname}")
        self.output_datastores = self.esxi_client.datastores.items


class GetEsxiDatastore(Node):
    name: str = "Get ESXi Datastore"
    description: str = "Attempts to get a Datastore from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="Datastore Name", description="The name of the datastore to get.")
    output = VariableOutputSocket(datatype=datatypes.Datastore, name="ESXi Datastore", description="The object that represents the Datastore on the server.")

    def run(self):
        self.output = datatypes.Datastore.construct(self.debug, self.esxi_client, self.search_name)


class GetAllPhysicalNics(Node):
    name: str = "Get All ESXi Physical Nics"
    description: str = "Gets a list of all physical NICs (Network Interface Cards) on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the NICs from.")
    output = ListOutputSocket(datatype=datatypes.PhysicalNIC, name="ESXi Physical NICs", description="A list of all Physical NICs objects on the server.")

    def run(self):
        self.debug(f"Getting all Physical NICs from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.physicalnics.items


class GetEsxiPhysicalNic(Node):
    name: str = "Get ESXi Physical NIC"
    description: str = "Attempts to get a Physical NIC from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="NIC Name", description="The name of the NIC to get.")
    output = OutputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The object that represents the Physical NIC on the server.")

    def run(self):
        self.debug(f'Getting Physical NIC "{self.search_name}" from Host {self.esxi_client.hostname}')
        self.output = self.esxi_client.physicalnics.get(self.search_name)


class GetAllPortgroups(Node):
    name: str = "Get All ESXi Portgroups"
    description: str = "Gets a list of all portgroups on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the NICs from.")
    output = ListOutputSocket(datatype=datatypes.Portgroup, name="ESXi Portgroups", description="A list of all portgroups objects on the server.")

    def run(self):
        self.debug(f"Getting all Port Groups from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.portgroups.items


class GetEsxiPortgroup(Node):
    name: str = "Get ESXi Portgroup"
    description: str = "Attempts to get a Portgroup from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="Portgroup Name", description="The name of the Portgroup to get.")
    output = OutputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The object that represents the Portgroup on the server.")

    def run(self):
        self.debug(f'Getting Port Group "{self.search_name}" from Host {self.esxi_client.hostname}.')
        self.output = self.esxi_client.portgroups.get(self.search_name)


class GetAllDistributedPortgroups(Node):
    name: str = "Get All ESXi Distributed Portgroups"
    description: str = "Gets a list of all distributed portgroups on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the NICs from.")
    output = ListOutputSocket(
        datatype=datatypes.DistributedPortgroup, name="ESXi Distributed Portgroups", description="A list of all distributed portgroups objects on the server."
    )

    def run(self):
        self.debug(f"Getting all Distributed Port Groups from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.distributed_portgroups.items


class GetEsxiDistributedPortgroup(Node):
    name: str = "Get ESXi Distributed Portgroup"
    description: str = "Attempts to get a Distributed Portgroup from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="Distributed PG Name", description="The name of the Distributed Portgroup to get.")
    output = OutputSocket(
        datatype=datatypes.DistributedPortgroup, name="Distributed PG", description="The object that represents the Distributed Portgroup on the server."
    )

    def run(self):
        self.debug(f'Getting Distributed Portgroup "{self.search_name}" from Host {self.esxi_client.hostname}.')
        self.output = self.esxi_client.distributed_portgroups.get(self.search_name)


class GetAllSwitches(Node):
    name: str = "Get All ESXi Virtual Switches"
    description: str = "Gets a list of all vSwitches on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the NICs from.")
    output = ListOutputSocket(datatype=datatypes.Switch, name="ESXi vSwitches", description="A list of all vSwitches objects on the server.")

    def run(self):
        self.debug(f"Getting all Virtual Switches from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.vswitches.items


class GetEsxiSwitch(Node):
    name: str = "Get ESXi Virtual Switch"
    description: str = "Attempts to get a vSwitch from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="vSwitch Name", description="The name of the Virtual Switch to get.")
    output = OutputSocket(datatype=datatypes.Switch, name="Virtual Switch", description="The object that represents the Virtual Switch on the server.")

    def run(self):
        self.debug(f'Getting Virtual Switch "{self.search_name}" from Host {self.esxi_client.hostname}.')
        self.output = self.esxi_client.vswitches.get(self.search_name)


class GetAllDistributedSwitches(Node):
    name: str = "Get All ESXi Distributed Virtual Switches"
    description: str = "Gets a list of all distributed vSwitches on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the NICs from.")
    output = ListOutputSocket(
        datatype=datatypes.DistributedSwitch, name="ESXi Distributed vSwitches", description="A list of all distributed vSwitches objects on the server."
    )

    def run(self):
        self.debug(f"Getting all Distributed Virtual Switches from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.distributed_vswitches.items


class GetEsxiDistributedSwitch(Node):
    name: str = "Get ESXi Distributed Virtual Switch"
    description: str = "Attempts to get a Distributed vSwitch from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="Distributed vSwitch Name", description="The name of the Distributed Virtual Switch to get.")
    output = OutputSocket(
        datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The object that represents the Distributed Virtual Switch on the server."
    )

    def run(self):
        self.debug(f'Getting Distributed Virtual Switch "{self.search_name}" from Host {self.esxi_client.hostname}.')
        self.output = self.esxi_client.distributed_vswitches.get(self.search_name)


class GetAllKernelNICs(Node):
    name: str = "Get All ESXi VM Kernel NICs"
    description: str = "Gets a list of all VM Kernel NICs on the ESXi server."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve the VM Kernel NICs from.")
    output = ListOutputSocket(datatype=datatypes.VMKernelNIC, name="ESXi VM Kernel NICs", description="A list of all VM Kernel NICs objects on the server.")

    def run(self):
        self.debug(f"Getting all VM Kernel NICs from Host {self.esxi_client.hostname}")
        self.output = self.esxi_client.vmkernelnics.items


class GetEsxiKernelNIC(Node):
    name: str = "Get ESXi VM Kernel NIC"
    description: str = "Attempts to get a VM Kernel NIC from the ESXi Server. Will raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    search_name = InputSocket(datatype=String, name="VM Kernel NIC Name", description="The name of the VM Kernel NIC to get.")
    output = OutputSocket(datatype=datatypes.VMKernelNIC, name="VM Kernel NIC", description="The object that represents the VM Kernel NIC on the server.")

    def run(self):
        self.debug(f'Getting VM Kernel NIC "{self.search_name}" from Host {self.esxi_client.hostname}.')
        self.output = self.esxi_client.vmkernelnics.get(self.search_name)


class GetEsxiClientHostname(Node):
    name: str = "Get ESXi Client Hostname"
    description: str = "Gets the hostname of the ESXi client. In vCenter configurations, this is the 'master' or 'parent' server."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    hostname = OutputSocket(datatype=String, name="Hostname", description="The hostname of the ESXi client")

    def run(self):
        self.hostname = self.esxi_client.hostname


class GetEsxiClientUsername(Node):
    name: str = "Get ESXi Client Username"
    description: str = "Gets the username of the user logged into the ESXi client. In vCenter configurations, this is the 'master' or 'parent' server."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    username = OutputSocket(datatype=String, name="Username", description="The username of the user logged into the ESXi client")

    def run(self):
        self.username = self.esxi_client.username


class GetEsxiClientPassword(Node):
    name: str = "Get ESXi Client Password"
    description: str = "Gets the password of the user logged into the ESXi client. In vCenter configurations, this is the 'master' or 'parent' server."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    password = OutputSocket(datatype=String, name="Password", description="The password of the user logged into the ESXi client")

    def run(self):
        self.password = self.esxi_client.password


class GetEsxiClientChildHostname(Node):
    name: str = "Get ESXi Client Child Hostname"
    description: str = "In vCenter configurations: Gets the child hostname of the ESXi client. This will return an empty string on non-vcenter systems."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    hostname = OutputSocket(datatype=String, name="Child Hostname", description="The hostname of the ESXi (child) client")

    def run(self):
        self.hostname = self.esxi_client._child_hostname if self.esxi_client._child_hostname else ""


class GetEsxiClientChildUsername(Node):
    name: str = "Get ESXi Client Child Username"
    description: str = "In vCenter configurations: Gets the child username of the ESXi client. This will return an empty string on non-vcenter systems."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    username = OutputSocket(datatype=String, name="Child Username", description="The username of the ESXi (child) client")

    def run(self):
        self.username = self.esxi_client._child_username if self.esxi_client._child_username else ""


class GetEsxiClientChildPassword(Node):
    name: str = "Get ESXi Client Child Password"
    description: str = "In vCenter configurations: Gets the child password of the ESXi client. This will return an empty string on non-vcenter systems."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    password = OutputSocket(datatype=String, name="Child Password", description="The password of the ESXi (child) client")

    def run(self):
        self.password = self.esxi_client._child_password if self.esxi_client._child_password else ""


class RunEsxcliCommand(Node):
    name: str = "ESXi Server Run Esxcli Command"
    description: str = "Executes an 'esxcli' command over SSH on the remote server (Note: 'esxcli' typically gives information about running VMs only)."
    categories: typing.List[str] = ["ESXi", "Client"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client for the ESXi server to run the command on.")
    command = InputSocket(
        datatype=String,
        name="Command",
        description="The esxcli command to run (Note: omit the 'esxcli' prefix. i.e. the desired command 'esxcli network ip connection list' should be provided as 'network ip connection list')",
    )
    force_parent = InputSocket(
        datatype=Boolean,
        name="Parent Server",
        description="When set to True and connected to a vCenter system, SSH into the vCenter hostname instead of the (default) child.",
    )
    raw_output = InputSocket(
        datatype=Boolean,
        name="Raw Output",
        description="Do not parse the output and instead get only the raw output. When this is True, 'Parsed Response' will be disabled and 'Raw Response' will be populated. When this is False, 'Parsed Response' will be populated and 'Raw Response' will be disabled.",
        input_field=False,
    )

    parsed_response = OutputSocket(
        datatype=DataContainer,
        name="Parsed Response",
        description="The response object for the esxcli command. This object can be used to parse out specific values. Only available when 'Raw Output' is False.",
    )
    raw_response = OutputSocket(
        datatype=String,
        name="Raw Response",
        description="The raw response object for the esxcli command. This is simply a string containing the output of the command. Only available when 'Raw Output' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.esxi_client.hostname} | {self.command}] "

    def run(self):
        self.disable_output_socket("Parsed Response")
        self.disable_output_socket("Raw Response")
        self.log(f"Running esxcli command{' on Parent Server' if self.force_parent else ''}: {self.command}")
        with self.esxi_client.ssh(force_parent=self.force_parent) as conn:
            if self.raw_output:
                self.raw_response = conn.esxcli(self.command, raw=True)
                self.debug(f"Raw Response:\n" + re.sub(r"^", "  │  ", str(self.raw_response), flags=re.MULTILINE))
            else:
                self.parsed_response = conn.esxcli(self.command, raw=False)
                self.debug(f"Parsed Response:\n" + re.sub(r"^", "  │  ", json.dumps(self.parsed_response, indent=2), flags=re.MULTILINE))
