from graphex import Boolean, InputSocket, ListInputSocket, ListOutputSocket, Node, Number, OptionalInputSocket, OutputSocket, String
from graphex_esxi_utils.utils.dynamic_networking import generate_id
from graphex_esxi_utils import esxi_constants, datatypes
import typing
import time
import uuid

TEMP_VSWITCH_PREFIX = "tmpvs-"
TEMP_PG_PREFIX = "tmppg-"


class EsxiCreateTemporaryNetwork(Node):
    name: str = "ESXi Create Temporary Network"
    description: str = f"Create a temporary network (VSwitch + Port Group) on an ESXi server. The created VSwitch and Port Group names will be randomly generated and prefixed with '{TEMP_VSWITCH_PREFIX}' and '{TEMP_PG_PREFIX}' respectively."
    categories: typing.List[str] = ["ESXi", "Network", "Temporary Network"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    vlan = InputSocket(datatype=Number, name="VLAN", description="The VLAN to assign to the temporary port group.")
    auto_remove = InputSocket(
        datatype=Boolean,
        name="Auto-remove?",
        description="Whether to automatically remove the temporary VSwitch/Port Group when the graph completes. If False, it is left up to the user to automatically remove the networking.",
        input_field=True,
    )

    network_id = OutputSocket(
        datatype=String,
        name="Network ID",
        description=f"The random ID used for this temporary network (everything after the '{TEMP_VSWITCH_PREFIX}'/'{TEMP_PG_PREFIX}' prefixes in the VSwitch/Port Group names).",
    )
    vswitch = OutputSocket(datatype=datatypes.Switch, name="VSwitch", description="A created temporary VSwitch.")
    pg = OutputSocket(datatype=datatypes.Portgroup, name="Port Group", description="A created temporary Port Group.")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        self.network_id = generate_id(str(uuid.uuid4()), length=3)
        vswitch_name = f"{TEMP_VSWITCH_PREFIX}{self.network_id}"
        self.log(f"Creating Temporary VSwitch '{vswitch_name}'")
        self.vswitch = self.esxi_client.vswitches.add(vswitch_name)

        if self.auto_remove:

            def auto_remove_vswitch():
                self.log(f"Removing Temporary VSwitch '{vswitch_name}'")
                self.vswitch.remove()

            self.defer(auto_remove_vswitch)

        for _ in range(5):
            # Need to retry adding the portgroup multiple times as sometimes there is a wait period between when the vswitch is added and a port group can be added
            try:
                pg_name = f"{TEMP_PG_PREFIX}{self.network_id}"
                self.log(f"Creating Temporary Port Group '{vswitch_name}'")
                self.pg = self.vswitch.add(pg_name, vlan=int(self.vlan))

                if self.auto_remove:

                    def auto_remove_pg():
                        for vm in self.esxi_client.vms:
                            for nic in vm.nics:
                                if nic.network == pg_name:
                                    self.log(f"Removing NIC '{pg_name}' from {vm.name}")
                                    nic.remove()
                        self.log(f"Removing Temporary Port Group '{pg_name}'")
                        self.pg.remove()

                    self.defer(auto_remove_pg)

                break
            except Exception:
                time.sleep(3)


class EsxiFindTemporaryNetwork(Node):
    name: str = "ESXi Find Temporary Networks on Virtual Machine"
    description: str = f"Find all temporary port groups connected to the given virtual machine. The temporary port groups are determined by finding the port groups with the prefix '{TEMP_PG_PREFIX}' connected to the virtual machine."
    categories: typing.List[str] = ["ESXi", "Network", "Temporary Network"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to search.")

    pgs = ListOutputSocket(datatype=datatypes.Portgroup, name="Port Groups", description="The temporary port groups found on the virtual machine")

    def run(self):
        temp_pgs = []
        for nic in self.vm.nics:
            if nic.network.startswith(TEMP_PG_PREFIX):
                temp_pgs.append(self.vm._client.portgroups.get(nic.network))
        self.pgs = temp_pgs


class EsxiRemoveTemporaryNetwork(Node):
    name: str = "ESXi Remove Temporary Network"
    description: str = (
        f"Find and remove a temporary network by name. This will remove all NICs associated with this temporary network, as well the Port Group and VSwitch."
    )
    categories: typing.List[str] = ["ESXi", "Network", "Temporary Network"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    temp_name = InputSocket(
        datatype=String,
        name="Temporary Network Name",
        description=f"The name of the temporary network. This can either be the name of the VSwitch for the temporary network, the name of the Port group for the temporary network, or simply the temporary network ID (name suffix; e.g. name minus '{TEMP_VSWITCH_PREFIX}' or '{TEMP_PG_PREFIX}')",
    )

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        network_suffix = self.temp_name
        if network_suffix.startswith(TEMP_PG_PREFIX):
            network_suffix = network_suffix[len(TEMP_PG_PREFIX) :]
        elif network_suffix.startswith(TEMP_VSWITCH_PREFIX):
            network_suffix = network_suffix[len(TEMP_VSWITCH_PREFIX) :]

        pg_name = f"{TEMP_PG_PREFIX}{network_suffix}"
        for vm in self.esxi_client.vms:
            for nic in vm.nics:
                if nic.network == pg_name:
                    self.log(f"Removing NIC '{nic.network}' from {vm.name}")
                    nic.remove()

        pg = self.esxi_client.portgroups.find(pg_name)
        if pg:
            self.log(f"Removing Temporary Port Group '{pg_name}'")
            pg.remove()

        vswitch = self.esxi_client.vswitches.find(f"{TEMP_VSWITCH_PREFIX}{network_suffix}")
        if vswitch:
            self.log(f"Removing Temporary VSwitch '{vswitch.name}'")
            vswitch.remove()


class EsxiRemoveTemporaryNetworkOnVM(Node):
    name: str = "ESXi Remove Temporary Networks on Virtual Machine"
    description: str = f"Find and remove all temporary networks connected to the given virtual machine. The temporary networks are determined by finding the port groups with the prefix '{TEMP_PG_PREFIX}' connected to the virtual machine."
    categories: typing.List[str] = ["ESXi", "Network", "Temporary Network"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to search.")
    remove_infrastructure = InputSocket(
        datatype=Boolean,
        name="Remove All Infrastructure?",
        description="Whether to remove all networking infrastructure (Port Groups and VSwitches) associated with the temporary networks on this virtual machine. If True, the NIC/Port Group/VSwitch for each temporary network will be removed from the server. If False, only the NICs will be removed from the virtual machine.",
        input_field=True,
    )

    def run(self):
        client = self.vm._client
        pgs_to_remove = []
        for nic in self.vm.nics:
            pg_name = nic.network
            if not pg_name.startswith(TEMP_PG_PREFIX):
                continue

            # Remove the NIC
            self.log(f"Removing NIC '{pg_name}' from {self.vm.name}")
            nic.remove()
            pgs_to_remove.append(pgs_to_remove)

        if not self.remove_infrastructure:
            return

        # Remove all networking
        for vm in client.vms:
            for nic in vm.nics:
                if nic.network in pgs_to_remove:
                    self.log(f"Removing NIC '{nic.network}' from {vm.name}")
                    nic.remove()

        for pg_name in pgs_to_remove:
            pg = client.portgroups.get(pg_name)
            parent_vswitch = pg.vswitch

            self.log(f"Removing Temporary Port Group '{pg_name}'")
            pg.remove()

            self.log(f"Removing Temporary VSwitch '{parent_vswitch.name}'")
            parent_vswitch.remove()
