from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
import typing


class EsxiPhysicalNicExists(Node):
    name: str = "ESXi Physical NIC Exists"
    description: str = "Outputs True if the queried physical NIC name exists."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Physical NIC Name", description="The name of the NIC to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.physicalnics.exists(self.name_value)


class EsxiPhysicalNicName(Node):
    name: str = "ESXi Physical NIC Name"
    description: str = "Outputs the device name of the physical network adapter."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=String, name="Name", description="The device name of the physical network adapter.")

    def run(self):
        self.output = self.nic.name


class EsxiPhysicalNicUp(Node):
    name: str = "ESXi Physical NIC Up"
    description: str = "Outputs whether or not this link is up."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=Boolean, name="Up?", description="Whether or not this link is up.")

    def run(self):
        self.output = self.nic.up


class EsxiPhysicalNicLinkspeed(Node):
    name: str = "ESXi Physical NIC Linkspeed"
    description: str = "Bit rate on the link, in megabits per second. If -1, then the link is down."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=Number, name="Bit Rate", description="Bit rate on the link, in megabits per second.")

    def run(self):
        result = self.nic.linkspeed
        self.output = result if result else -1


class EsxiPhysicalNicFullDuplex(Node):
    name: str = "ESXi Physical NIC is Full Duplex"
    description: str = "Outputs '1' if the link is capable of full-duplex, '0' if only half-duplex ('false'), or '-1' if the link is down."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(
        datatype=Number,
        name="Full Duplex Status",
        description="Is '1' if the link is capable of full-duplex, '0' if only half-duplex ('false'), or '-1' if the link is down.",
    )

    def run(self):
        status = self.nic.fullduplex
        if status is None:
            self.output = -1
        else:
            self.output = 1 if status else 0


class EsxiPhysicalNicMac(Node):
    name: str = "ESXi Physical NIC Get MAC Address"
    description: str = "Output the media access control (MAC) address of the physical network adapter."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=String, name="MAC Address", description="The media access control (MAC) address of the physical network adapter.")

    def run(self):
        self.output = self.nic.mac


class EsxiPhysicalNicPci(Node):
    name: str = "ESXi Physical NIC Get PCI Device String"
    description: str = "Output the device hash of the PCI device corresponding to this physical network adapter."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=String, name="Device Hash", description="The device hash of the PCI device corresponding to this physical network adapter.")

    def run(self):
        self.output = self.nic.pci


class EsxiPhysicalNicDriver(Node):
    name: str = "ESXi Physical NIC Get Driver Name"
    description: str = "Output the name of the driver."
    categories: typing.List[str] = ["ESXi", "Network", "Physical NIC"]
    color: str = esxi_constants.COLOR_PHYSICAL_NIC

    nic = InputSocket(datatype=datatypes.PhysicalNIC, name="Physical NIC", description="The PhysicalNIC object to use.")

    output = OutputSocket(datatype=String, name="Driver Name", description="The name of the driver.")

    def run(self):
        self.output = self.nic.driver


class EsxiVmKernelNicExists(Node):
    name: str = "ESXi VMKernelNIC Exists"
    description: str = "Outputs True if the queried VMKernel NIC name exists."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="VMKernel NIC Name", description="The name of the NIC to search for.")
    exists = OutputSocket(datatype=Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.vmkernelnics.exists(self.name_value)


class EsxiVmGetKernelNic(Node):
    name: str = "ESXi Get VMKernelNIC"
    description: str = "Attempts to get a VMKernelNIC object from the ESXi Server. Will raise an exception if the VM is not found."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    nic_name = InputSocket(datatype=String, name="VMKernel NIC Name", description="The name of the NIC to get.")
    output = OutputSocket(datatype=datatypes.VMKernelNIC, name="ESXi VM", description="The object that represents the VM on the server.")

    def run(self):
        self.debug(f'Grabbing VMKernelNIC with name: "{self.nic_name}" from "{self.esxi_client}".')
        self.output = self.esxi_client.vmkernelnics.get(self.nic_name)


class EsxiVmKernelNicName(Node):
    name: str = "ESXi VMKernel NIC Name"
    description: str = "Outputs the device name of this VMkernel NIC."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(datatype=String, name="Name", description="The device name of this VMkernel NIC.")

    def run(self):
        self.output = self.nic.name


class EsxiVmKernelNicGetPortgroup(Node):
    name: str = "ESXi VMKernel NIC Get Portgroup"
    description: str = "If the VMKernel NIC is connected to a vSwitch, this property is the `PortGroup` connected. Will raise a 'EsxiObjectDoesNotExistError' exception if this VMKernelNIC object doesn't have a portgroup. Check ahead of time with 'ESXi VMKernel NIC is Connected to vSwitch'"
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(datatype=datatypes.Portgroup, name="Portgroup", description="The portgroup connected.")

    def run(self):
        result = self.nic.portgroup
        if result is None:
            raise exceptions.EsxiObjectDoesNotExistError(f'VMKernelNIC: "{self.nic.name}" ... Doesn\'t have a "Portgroup" object!')
        self.output = result


class EsxiVmKernelNicIsConnectedToSwitch(Node):
    name: str = "ESXi VMKernel NIC is Connected to vSwitch"
    description: str = "Outputs True if the VMKernelNIC is connected to a vSwitch (implying the ability to have a portgroup)."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    portgroup_connected = OutputSocket(datatype=Boolean, name="Connected to vSwitch?", description="If False: the object is not connected to a vSwitch.")

    def run(self):
        self.portgroup_connected = False if self.nic.portgroup is None else True


class EsxiVmKernelNicMac(Node):
    name: str = "ESXi VMKernel NIC MAC Address"
    description: str = "Outputs the Media access control (MAC) address of the network adapter."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(datatype=String, name="Portgroup", description="The Media access control (MAC) address of the network adapter.")

    def run(self):
        self.output = self.nic.mac


class EsxiVmKernelNicIp(Node):
    name: str = "ESXi VMKernel NIC IP Address"
    description: str = "Outputs the IPv4 address currently used by the network adapter. Will output an empty string if no IP is assigned."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(
        datatype=String,
        name="IP Address",
        description="The IPv4 address currently used by the network adapter. Will output an empty string if nothing is assigned.",
    )

    def run(self):
        result = self.nic.ip
        self.output = result if result else ""


class EsxiVmKernelNicSubnetMask(Node):
    name: str = "ESXi VMKernel NIC Subnet Mask"
    description: str = "Outputs the subnet mask, specified specified using IPv4 dot notation. Will output an empty string if nothing is assigned."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(
        datatype=String,
        name="Subnet Mask",
        description="The subnet mask, specified specified using IPv4 dot notation. Will output an empty string if nothing is assigned.",
    )

    def run(self):
        result = self.nic.subnetmask
        self.output = result if result else ""


class EsxiVmKernelNicGateway(Node):
    name: str = "ESXi VMKernel NIC Gateway"
    description: str = "Outputs the default gateway address. Will output an empty string if nothing is assigned."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(datatype=String, name="Gateway", description="The default gateway address. Will output an empty string if nothing is assigned.")

    def run(self):
        result = self.nic.gateway
        self.output = result if result else ""


class EsxiVmKernelNicMtu(Node):
    name: str = "ESXi VMKernel NIC MTU"
    description: str = "Outputs the maximum transmission unit for packets size in bytes for the virtual NIC."
    categories: typing.List[str] = ["ESXi", "Network", "VMKernel NIC"]
    color: str = esxi_constants.COLOR_KERNEL_NIC

    nic = InputSocket(datatype=datatypes.VMKernelNIC, name="VMKernel NIC", description="The VMKernelNIC object to use.")

    output = OutputSocket(datatype=Number, name="MTU", description="Maximum transmission unit for packets size in bytes for the virtual NIC.")

    def run(self):
        self.output = self.nic.mtu
