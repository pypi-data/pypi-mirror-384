from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, ListOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
import typing


class EsxiSwitchExists(Node):
    name: str = "ESXi vSwitch Exists"
    description: str = "Outputs True if the queried switch name exists."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Switch Name", description="The name of the switch to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.vswitches.exists(self.name_value)


class EsxiSwitchAdd(Node):
    name: str = "ESXi Add vSwitch"
    description: str = "Adds (Creates) a new virtual switch with the given name. The name must be unique with respect to other virtual switches on the host and is limited to 32 characters."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Switch Name", description="The name for the new switch.")
    mtu = InputSocket(datatype=Number, name="MTU", description="The maximum transmission unit (MTU) of the virtual switch in bytes.", input_field=1500)
    ports = InputSocket(
        datatype=Number,
        name="Number of Ports",
        description="The number of ports that this virtual switch is configured to use. The maximum value is 1024, although other constraints, such as memory limits, may establish a lower effective limit.",
        input_field=128,
    )

    output = OutputSocket(datatype=datatypes.Switch, name="vSwitch", description="The added vSwitch Object")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        self.log(f'Adding vSwitch "{self.name_value}" (MTU={self.mtu}, Number of Ports={self.ports})')
        self.output = self.esxi_client.vswitches.add(name=self.name_value, mtu=int(self.mtu), ports=int(self.ports))


class EsxiSwitchName(Node):
    name: str = "ESXi vSwitch Name"
    description: str = "Outputs the name of the vSwitch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=String, name="Name", description="The name of the virtual switch.")

    def run(self):
        self.output = self.switch.name


class EsxiSwitchPortgroups(Node):
    name: str = "ESXi vSwitch Get Portgroups"
    description: str = "Outputs the Portgroups configured/associated with this vswitch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = ListOutputSocket(datatype=datatypes.Portgroup, name="Portgroups", description="The Portgroups configured/associated with this vswitch.")

    def run(self):
        self.output = self.switch.portgroups


class EsxiSwitchPhysicalNics(Node):
    name: str = "ESXi vSwitch Get Physical NICs"
    description: str = "Outputs the set of physical network adapters associated with this virtual switch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = ListOutputSocket(
        datatype=datatypes.PhysicalNIC, name="Physical NICs", description="The set of physical network adapters associated with this virtual switch."
    )

    def run(self):
        self.output = self.switch.physicalnics


class EsxiSwitchNumPorts(Node):
    name: str = "ESXi vSwitch Get Number of Ports"
    description: str = "The number of ports that this virtual switch currently has."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="Number of Ports", description="The number of ports that this virtual switch currently has.")

    def run(self):
        self.output = self.switch.numports


class EsxiSwitchNumPortsAvailable(Node):
    name: str = "ESXi vSwitch Get Number of Ports Available"
    description: str = "Outputs the number of ports that are available on this virtual switch. There are a number of networking services that utilize a port on the virtual switch and are not accounted for in the Port array of a PortGroup. For example, each physical NIC attached to a virtual switch consumes one port."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="Number of Ports Available", description="The number of ports that are available on this virtual switch.")

    def run(self):
        self.output = self.switch.numports_available


class EsxiSwitchNumPortsConfigured(Node):
    name: str = "ESXi vSwitch Get Number of Ports Configured"
    description: str = "The number of ports that this virtual switch is configured to use. The maximum value is 1024, although other constraints, such as memory limits, may establish a lower effective limit."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="Number of Ports Configured", description="The number of ports that this virtual switch is configured to use.")

    def run(self):
        self.output = self.switch.configured_ports


class EsxiSwitchMtu(Node):
    name: str = "ESXi vSwitch Get MTU"
    description: str = "Outputs the maximum transmission unit (MTU) associated with this virtual switch in bytes."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="MTU", description="The maximum transmission unit (MTU) associated with this virtual switch in bytes.")

    def run(self):
        self.output = self.switch.mtu


class EsxiSwitchBeacon(Node):
    name: str = "ESXi vSwitch Beacon"
    description: str = "The beacon configuration to probe for the validity of a link. This is the beacon interval (how often, in seconds, a beacon should be sent). If this is -1: beacon probing is disabled."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="Beacon Interval", description="How often, in seconds, a beacon should be sent")

    def run(self):
        result = self.switch.beacon
        self.output = result if result else -1


class EsxiSwitchLinkDisProto(Node):
    name: str = "ESXi vSwitch Link Discovery Protocol"
    description: str = "The link discovery protocol configuration for the virtual switch. If this does not have a link discovery protocol: will output the empty string. This is either `cdp` (Cisco Discovery Protocol) or `lldp` (Link Layer Discovery Protocol) otherwise."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=String, name="Protocol", description="The link discovery protocol configuration for the virtual switch.")

    def run(self):
        result = self.switch.link_discovery_protocol
        self.output = result if result else ""


class EsxiSwitchLinkDisOp(Node):
    name: str = "ESXi vSwitch Link Discovery Operation"
    description: str = "The link discovery operation configuration for the virtual switch. If this does not have a link discovery protocol: outputs the empty string. Otherwise, this is one of the following: `advertise`: Sent discovery packets for the switch, but don't listen for incoming discovery packets. `listen`: Listen for incoming discovery packets but don't sent discovery packet for the switch. `both`: Sent discovery packets for the switch and listen for incoming discovery packets. `none`: Don't listen for incoming discovery packets and don't sent discover packets for the switch either."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")

    output = OutputSocket(datatype=String, name="Protocol", description="The link discovery operation configuration for the virtual switch.")

    def run(self):
        result = self.switch.link_discovery_operation
        self.output = result if result else ""


class EsxiSwitchAddPg(Node):
    name: str = "ESXi vSwitch Add Portgroup"
    description: str = "Add a port group to this virtual switch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to use.")
    pg_name = InputSocket(datatype=String, name="Name", description="The name of the port group")
    vlan = InputSocket(
        datatype=Number,
        name="VLAN",
        description="The VLAN ID for ports using this port group. Possible values: a value of 0 specifies that you do not want the port group associated with a VLAN, a value from 1 to 4094 specifies a VLAN ID for the port group, a value of 4095 specifies that the port group should use trunk mode, which allows the guest operating system to manage its own VLAN tags.",
    )

    output = OutputSocket(datatype=datatypes.Portgroup, name="Added Portgroup", description="The Portgroup object added to the switch.")

    def log_prefix(self):
        return f"[{self.name} - {self.switch.name}] "

    def run(self):
        self.log(f'Adding Port Group "{self.pg_name}" (VLAN={self.vlan})')
        self.output = self.switch.add(name=self.pg_name, vlan=int(self.vlan))


class EsxiSwitchRemove(Node):
    name: str = "ESXi Remove vSwitch"
    description: str = "Remove this virtual switch from the system."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch"]
    color: str = esxi_constants.COLOR_SWITCH

    switch = InputSocket(datatype=datatypes.Switch, name="vSwitch", description="The vSwitch object to remove.")

    def log_prefix(self):
        return f"[{self.name} - {self.switch.name}] "

    def run(self):
        self.log(f"Removing vSwitch...")
        self.switch.remove()


class EsxiDistributedSwitchExists(Node):
    name: str = "ESXi Distributed vSwitch Exists"
    description: str = "Outputs True if the queried distributed switch name exists."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Distributed Switch Name", description="The name of the switch to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.distributed_vswitches.exists(self.name_value)


class EsxiDistributedSwitchName(Node):
    name: str = "ESXi Distributed vSwitch Name"
    description: str = "Outputs the name of the Distributed vSwitch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(datatype=String, name="Name", description="The name of the distributed virtual switch.")

    def run(self):
        self.output = self.switch.name


class EsxiDistributedSwitchPortgroups(Node):
    name: str = "ESXi Distributed vSwitch Portgroups"
    description: str = "Outputs the DistributedPortgroups configured associated with this distributed vswitch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(
        datatype=datatypes.DistributedPortgroup,
        name="Distributed Portgroups",
        description="The DistributedPortgroups configured associated with this distributed vswitch.",
    )

    def run(self):
        self.output = self.switch.portgroups


class EsxiDistributedSwitchPhysicalNics(Node):
    name: str = "ESXi Distributed vSwitch Physical NICs"
    description: str = "The set of physical network adapters associated with this distributed virtual switch."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(
        datatype=datatypes.PhysicalNIC, name="PhysicalNICs", description="The set of physical network adapters associated with this distributed virtual switch."
    )

    def run(self):
        self.output = self.switch.physicalnics


class EsxiDistributedSwitchNumPorts(Node):
    name: str = "ESXi Distributed vSwitch Number of Ports"
    description: str = "The number of ports that this distributed virtual switch currently has."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(datatype=Number, name="Number of Ports", description="The number of ports that this distributed virtual switch currently has.")

    def run(self):
        self.output = self.switch.numports


class EsxiDistributedSwitchNumPortsAvailable(Node):
    name: str = "ESXi Distributed vSwitch Number of Ports Available"
    description: str = "The number of ports that are available on this distributed virtual switch. There are a number of networking services that utilize a port on the virtual switch and are not accounted for in the Port array of a PortGroup. For example, each physical NIC attached to a virtual switch consumes one port."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(
        datatype=Number, name="Number of Ports Available", description="The number of ports that are available on this distributed virtual switch."
    )

    def run(self):
        self.output = self.switch.numports_available


class EsxiDistributedSwitchMtu(Node):
    name: str = "ESXi Distributed vSwitch MTU"
    description: str = "The maximum transmission unit (MTU) associated with this distributed virtual switch in bytes."
    categories: typing.List[str] = ["ESXi", "Network", "vSwitch", "Distributed"]
    color: str = esxi_constants.COLOR_DIS_SWITCH

    switch = InputSocket(datatype=datatypes.DistributedSwitch, name="Distributed vSwitch", description="The distributed vSwitch object to use.")

    output = OutputSocket(
        datatype=Number, name="MTU", description="The maximum transmission unit (MTU) associated with this distributed virtual switch in bytes."
    )

    def run(self):
        self.output = self.switch.mtu
