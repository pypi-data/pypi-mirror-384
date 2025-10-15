from graphex import String, Boolean, Number, Node, InputSocket, OutputSocket, ListOutputSocket, ListInputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex_esxi_utils.utils import dynamic_networking as dynamic_networking_fns
import esxi_utils
import typing
import ipaddress


class FindAvailableIPaddress(Node):
    name: str = "ESXi Find Available IP Address"
    description: str = "Queries ESXi for available IPs and then returns an available one for use (randomly selected). An exception will be raised if an available IP cannot be found."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "IP Management"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    base_ip = InputSocket(
        datatype=String, name="Base IP", description="An IP of the form '192.168.1.x' where the character 'x' represents the byte to find available."
    )
    disabled_ips = ListInputSocket(datatype=String, name="Disabled IPs", description="A list of IPs that you don't want assigned to the VM")
    ping = InputSocket(
        datatype=Boolean, name="Ping?", description="Ping for available IP addresses instead of collecting them from ESXi (can be faster)", input_field=False
    )

    available_address = OutputSocket(
        datatype=String, name="Available IP", description="An available IP address as a string or the originally provided 'base_ip' if it doesn't end in '.x'"
    )

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname} | {self.base_ip}] "

    def run(self):
        self.log(f"Querying for available IPs...")
        self.available_address = str(
            ipaddress.IPv4Address(dynamic_networking_fns.get_ip_address(base_ip=self.base_ip, esxi_client=self.esxi_client, ping=self.ping))
        )
        self.debug(f"Found IP: {self.available_address}")


class GetAllConnectedIpAddresses(Node):
    name: str = "ESXi Get All Connected IP Addresses"
    description: str = (
        "Uses ESXi to query for IP addresses that are already assigned and connected. This will not find IP addresses for VMs that are powered off."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "IP Management"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")

    occupied_addresses = ListOutputSocket(datatype=String, name="Occupied IPs", description="A set of found IP addresses")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        self.log(f"Querying for assigned IPs...")
        self.occupied_addresses = list(dynamic_networking_fns.get_all_connected_ips(self.esxi_client))
        self.debug(f"Assigned IPs: {self.occupied_addresses}")


class GenerateIpId(Node):
    name: str = "ESXi Generate Dynamic Networking ID"
    description: str = "Creates an ID that is a combination of the current time since unix epoch (in nanoseconds) + a randomly generated value seeded with the 'seed' and 'length' parameters. (The length of the current time is currently 19 characters)"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "IP Management"]
    color: str = esxi_constants.COLOR_CLIENT

    seed = InputSocket(datatype=String, name="Seed", description="The seed to use when creating the ID")
    random_length = InputSocket(datatype=Number, name="Length", description="The random string's length to append to the current time.")

    gen_id = OutputSocket(datatype=String, name="ID", description="The generated ID. The length will be ~19 + length + 1")

    def run(self):
        self.gen_id = dynamic_networking_fns.generate_id(seed=self.seed, length=int(self.random_length))
        self.debug(f"Generated Dynamic Networking ID: {self.gen_id}")


class ESXiConnectLogger(Node):
    name: str = "ESXi Connect Debug Logger"
    description: str = "Connects the esxi_utils logger to the Graphex logger. This allows esxi_utils logs to get transmitted through the graphex logger."
    categories: typing.List[str] = ["ESXi", "Debugging"]
    color: str = esxi_constants.COLOR_CLIENT

    def run(self):
        self.debug(f"Enabling 'esxi_utils' logger...")
        esxi_utils.util.log.enable(self._runtime.logger)
