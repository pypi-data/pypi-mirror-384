import time
import typing
import random
import string
import ipaddress


def get_ip_address(base_ip: str, esxi_client, ping: bool = False, disabled_ips: typing.List[str] = []) -> str:
    """
    Queries esxi for available IPs and then returns an available one for use.
    :param base_ip:
        An IP of the form '192.168.1.x' where the character 'x' represents the byte to find available.
    :param esxi_client:
        The ESXi client instance
    :param ping:
        Ping for available IPs instead of collecting them from ESXi (default=False)
    :param disabled_ips:
        A list of IPs that you don't want assigned to the VM
    :return:
        An available IP address as a string or the originally provided 'base_ip' if it doesn't end in '.x'
    """
    if str(base_ip).lower().endswith(".x"):
        import ping3

        base_ip = str(base_ip).lower().replace("x", "").strip()
        used_ips = set()
        already_generated = set()
        for ip in disabled_ips:
            already_generated.add(ipaddress.IPv4Address(ip))
        # collect from ESXi
        if not ping:
            used_ips = get_all_connected_ips(esxi_client)
        while True:
            r_int = random.choice(list(set([x for x in range(3, 253)]) - set(already_generated)))
            if r_int in already_generated:
                continue
            temp_ip = base_ip + str(r_int)
            if ping:
                if not ping3.ping(temp_ip):
                    return temp_ip
            elif temp_ip not in used_ips:
                return temp_ip
            already_generated.add(r_int)
            if len(already_generated) > 250:
                raise Exception("ERROR: All IPs in range: 3-253 have been taken! Cannot dynamically assign an IP!")
    return base_ip


def get_all_connected_ips(esxi_client) -> typing.Set[str]:
    """
    Uses ESXi to query for IP addresses that are already assigned and connected.
    This will not find IP addresses for VMs that are powered off.
    :param esxi_client:
        The ESXi client instance
    :return:
        A set of found IP addresses
    """
    ips = set()
    for vm in esxi_client.vms:
        try:
            for nic in vm.nics:
                try:
                    if nic.connected and nic.ip:
                        ips.add(nic.ip)
                except Exception:
                    continue
        except Exception:
            continue
    return ips


def generate_id(seed: str, length: int = 4) -> str:
    """
    Creates an ID that is a combination of the current time since unix epoch (in nanoseconds) +
    a randomly generated value seeded with the 'seed' and 'length' parameters.
    (The length of the current time is currently 19 characters)
    :param seed: The seed to use when creating the ID
    :param length: The random string's length to append to the current time.
    :return: The generated ID. The length will be ~19 + length + 1
    """
    # create a unique identifier for this networking based on nanoseconds since unix epoch + random seed
    alphabet = string.ascii_lowercase + string.digits
    ns_since_unix_epoch = str(time.time_ns())  # 19 characters (28 Mar 2023)
    random.seed(seed)
    return ns_since_unix_epoch + "_" + "".join(random.choices(alphabet, k=length))
