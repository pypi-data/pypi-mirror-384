from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, ListOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
import typing


class EsxiPortgroupExists(Node):
    name: str = "ESXi Portgroup Exists"
    description: str = "Outputs True if the queried portgroup name exists."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Portgroup Name", description="The name of the portgroup to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.portgroups.exists(self.name_value)


class EsxiPortgroupGetName(Node):
    name: str = "ESXi Get Portgroup Name"
    description: str = "Gets the name for the provided Portgroup."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = OutputSocket(datatype=String, name="Portgroup Name", description="The name for the provided Portgroup.")

    def run(self):
        self.output = self.pg.name


class EsxiPortgroupGetVlan(Node):
    name: str = "ESXi Get Portgroup VLAN"
    description: str = "The VLAN ID for ports using this port group. Possible values: A value of 0 specifies that you do not want the port group associated with a VLAN, a value from 1 to 4094 specifies a VLAN ID for the port group, a value of 4095 specifies that the port group should use trunk mode, which allows the guest operating system to manage its own VLAN tags. "
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = OutputSocket(datatype=Number, name="VLAN", description="The VLAN number for the provided Portgroup.")

    def run(self):
        self.output = self.pg.vlan


class EsxiPortgroupActiveClients(Node):
    name: str = "ESXi Portgroup Active Clients"
    description: str = "The number of active clients of this port group (the number of connections to powered-on virtual machines)."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = OutputSocket(datatype=Number, name="Number of Connections", description="The number of active clients of this port group.")

    def run(self):
        self.output = self.pg.active_clients


class EsxiPortgroupVswitch(Node):
    name: str = "ESXi Portgroup Get vSwitch"
    description: str = "The VSwitch that this port group belongs to."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = OutputSocket(datatype=datatypes.Switch, name="vSwitch", description="The VSwitch that this port group belongs to.")

    def run(self):
        self.output = self.pg.vswitch


class EsxiPortgroupGetVmKernelNic(Node):
    name: str = "ESXi Portgroup Get VMKernel NIC"
    description: str = "Get the VMKernel NIC assigned to this port group. Will raise a 'EsxiObjectDoesNotExistError' exception if this portgroup doesn't have a VMKernelNIC object. Check ahead of time with 'ESXi Portgroup has VMKernel NIC'"
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = OutputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernel NIC assigned to this port group")

    def run(self):
        result = self.pg.vmkernelnic
        if result is None:
            raise exceptions.EsxiObjectDoesNotExistError(f'Portgroup: "{self.pg.name}" ... Doesn\'t have a "VMKernelNIC" object!')
        self.output = result


class EsxiPortgroupHasVmKernelNic(Node):
    name: str = "ESXi Portgroup has VMKernel NIC"
    description: str = "Outputs True if the portgroup has a VMKernelNIC object."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    exists = OutputSocket(
        datatype=Boolean,
        name="Exists?",
        description="Outputs True if the VMKernelNIC field is populated with an object. False if there is no VMKernel NIC associated with this portgroup.",
    )

    def run(self):
        self.exists = False if self.pg.vmkernelnic is None else True


class EsxiPortgroupVms(Node):
    name: str = "ESXi Portgroup Get VMs"
    description: str = "Gets a list of the virtual machines attached to this port group."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = ListOutputSocket(
        datatype=datatypes.VirtualMachine, name="Virtual Machines", description="A list of the virtual machines attached to this port group."
    )

    def run(self):
        self.debug(f'Querying Port Group "{self.pg.name}" for Virtual Machines...')
        self.output = self.pg.vms


class EsxiPortgroupRemove(Node):
    name: str = "ESXi Remove Portgroup"
    description: str = "Remove this port group from the system."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to remove.")

    def log_prefix(self):
        return f"[{self.name} - {self.pg.name}] "

    def run(self):
        self.log(f"Removing Port Group...")
        self.pg.remove()


class EsxiPortgroupPorts(Node):
    name: str = "ESXi Portgroup Get Ports"
    description: str = "The ports that currently exist and are used on this port group. Returns a list of PortgroupPort objects."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup"]
    color: str = esxi_constants.COLOR_PG

    pg = InputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The Portgroup to use.")
    output = ListOutputSocket(datatype=datatypes.PortgroupPort, name="Portgroup Ports", description="A list of PortgroupPort objects.")

    def run(self):
        self.output = self.pg.ports


class EsxiPortgroupPortGetMac(Node):
    name: str = "ESXi PortgroupPort Get MAC Address"
    description: str = "Gets the MAC address from a PortgroupPort object."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Port"]
    color: str = esxi_constants.COLOR_PG

    pgp = InputSocket(datatype=datatypes.PortgroupPort, name="PortgroupPort", description="The PortgroupPort to use.")
    output = OutputSocket(datatype=String, name="MAC Address", description="The MAC address for the PortgroupPort object.")

    def run(self):
        self.output = self.pgp["mac"]


class EsxiPortgroupPortGetType(Node):
    name: str = "ESXi PortgroupPort Get Type"
    description: str = "Gets the type of connection from a PortgroupPort object."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Port"]
    color: str = esxi_constants.COLOR_PG

    pgp = InputSocket(datatype=datatypes.PortgroupPort, name="PortgroupPort", description="The PortgroupPort to use.")
    output = OutputSocket(datatype=String, name="Connection Type", description="The type of connection for the PortgroupPort object.")

    def run(self):
        self.output = self.pgp["type"]


class EsxiDistributedPortgroupExists(Node):
    name: str = "ESXi Distributed Portgroup Exists"
    description: str = "Outputs True if the queried distributed portgroup name exists."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Distributed Portgroup Name", description="The name of the distributed portgroup to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.distributed_portgroups.exists(self.name_value)


class EsxiDistributedPortgroupGetName(Node):
    name: str = "ESXi Get Distributed Portgroup Name"
    description: str = "Gets the name for the provided Distributed Portgroup."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_PG

    dpg = InputSocket(datatype=datatypes.Portgroup, name="Distributed Portgroup", description="The Distributed Portgroup to use.")
    output = OutputSocket(datatype=String, name="Distributed Portgroup Name", description="The name for the provided DistributedPortgroup.")

    def run(self):
        self.output = self.dpg.name


class EsxiDistributedPortgroupVlan(Node):
    name: str = "ESXi Get Distributed Portgroup VLAN"
    description: str = "The VLAN ID for ports using this port group. Possible values: A value of 0 specifies that you do not want the port group associated with a VLAN, a value from 1 to 4094 specifies a VLAN ID for the port group, a value of 4095 specifies that the port group should use trunk mode (which allows the guest operating system to manage its own VLAN tags), or a value of -1 representing a range of available ports (contains a 'start' and an 'end' value to mark the range)"
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_PG

    dpg = InputSocket(datatype=datatypes.Portgroup, name="Distributed Portgroup", description="The Distributed Portgroup to use.")
    output = OutputSocket(datatype=Number, name="VLAN", description="The VLAN for the provided DistributedPortgroup.")
    start = OutputSocket(datatype=Number, name="Start", description="The first possible value in the range or the only value.")
    end = OutputSocket(datatype=Number, name="End", description="The last possible value in the range or the only value.")

    def run(self):
        result = self.dpg.vlan
        if isinstance(result, int):
            self.output = self.start = self.end = result
        else:
            self.output = -1
            self.start = result.start
            self.end = result.end


class EsxiDistributedPortgroupGetSwitch(Node):
    name: str = "ESXi Get Distributed Portgroup vSwitch"
    description: str = "The Distributed VSwitch that this distributed port group belongs to."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_PG

    dpg = InputSocket(datatype=datatypes.Portgroup, name="Distributed Portgroup", description="The Distributed Portgroup to use.")
    output = OutputSocket(
        datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The Distributed VSwitch that this distributed port group belongs to."
    )

    def run(self):
        self.output = self.dpg.vswitch


class EsxiDistributedPortgroupGetVms(Node):
    name: str = "ESXi Get Distributed Portgroup VMs"
    description: str = "A list of the virtual machines attached to this distributed port group."
    categories: typing.List[str] = ["ESXi", "Network", "Portgroup", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_PG

    dpg = InputSocket(datatype=datatypes.Portgroup, name="Distributed Portgroup", description="The Distributed Portgroup to use.")
    output = ListOutputSocket(
        datatype=datatypes.VirtualMachine, name="Distributed vSwitch", description="A list of the virtual machines attached to this distributed port group."
    )

    def run(self):
        self.debug(f'Querying Distributed Port Group "{self.dpg.name}" for Virtual Machines...')
        self.output = self.dpg.vms
