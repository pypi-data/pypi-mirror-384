# The purpose of this file was to validate ("lint") XML configurations to tell if they were
# valid or not. This file is likely in need of a decent amount of generalization.

import ipaddress
from os import path, listdir
from xml.sax.handler import ContentHandler
from xml.sax import make_parser

#
import time
import typing

#
import esxi_utils
from esxi_utils.util.response import Response

#
import graphex_esxi_utils.panos_constants as c
import graphex_esxi_utils.utils.misc as misc
from graphex_esxi_utils.utils.palo_alto import installing_wait_loop, wait_for_api_resp, parse_job_number
from graphex_esxi_utils import exceptions


def _parsefile(file) -> None:
    """
    Checks the contents of the provided file for a valid XML structure.
    Throws an error if the structure is invalid.

    :param file:
        An instance of a python3 file object
    """
    parser = make_parser()
    parser.setContentHandler(ContentHandler())
    parser.parse(file)


def check_syntax(file_path: str, logger_function: typing.Callable) -> None:
    """
    Opens the provided filepath and checks the XML file for valid structure.
    Will raise an error (ending the program) if the structure is invalid.
    The error message includes the line location of the error and short message on what the problem is.

    :param filepath:
        The absolute path to the file to check the XML structure of
    """
    logger_function(f"Testing configuration file with path: {file_path}")
    with open(file_path, "r") as file:
        try:
            _parsefile(file)
        except Exception as e:
            raise exceptions.PaloAltoXmlConfigError(f"ERROR: Syntax error in XML File!: {str(e)}")


def check_all_xml_configs(is_panorama: bool, logger_function: typing.Callable, xml_path: typing.Optional[str] = None) -> None:
    """
    Iterates through the 'xml_config' directory for either Panorama or firewall configuration files and 'lints'/checks each one.

    :param is_panorama:
        When True: looks through the 'panorama' directory. When False: looks through the 'firewall' directory.
    """
    list_of_paths = traverse_xml_directory(is_panorama=is_panorama, xml_path=xml_path)
    for p in list_of_paths:
        check_syntax(file_path=p, logger_function=logger_function)
    if is_panorama:
        vm_type = "panorama"
    else:
        vm_type = "firewalls"
    logger_function(f"Checked/linted all XML configuration files relating to {vm_type}! No 'structural' errors found.")


def traverse_xml_directory(is_panorama: bool, xml_path: typing.Optional[str] = None) -> typing.List:
    """
    Iterates through the 'xml_config' directory for either Panorama or firewall configuration files.

    :param is_panorama:
        When True: looks through the 'panorama' directory. When False: looks through the 'firewall' directory.
    :param xml_path:
        The path to the XML files on filesystem.

    :return:
        List of paths to all XML files based on the VM type
    """
    paths_list = []
    if xml_path:
        base_path = misc.create_abs_path(xml_path)
    else:
        if is_panorama:
            base_path = misc.create_abs_path(path.join(c.XML_CONFIG_START_DIR, c.XML_CONFIG_DIR_NAME, c.XML_CONFIG_PANORAMA_DIR_NAME))
        else:  # firewall
            base_path = misc.create_abs_path(path.join(c.XML_CONFIG_START_DIR, c.XML_CONFIG_DIR_NAME, c.XML_CONFIG_FIREWALL_DIR_NAME))
    dir_queue = [base_path]
    while True:
        if len(dir_queue) <= 0:
            break
        current_path = dir_queue.pop()
        for name in listdir(current_path):
            new_path = path.join(current_path, name)
            if path.isfile(new_path):
                if new_path.endswith(".xml"):
                    paths_list.append(new_path)
            else:  # is dir
                dir_queue.append(new_path)
    return paths_list


def import_configuration_file(
    vm: esxi_utils.vm.PaloAltoFirewallVirtualMachine, ip: str, username: str, password: str, filepath: str, logger_function: typing.Callable
):
    """
    Sends an HTTP request to the VM API to request the file be imported as a configuration file.
    This will allow future install of the configuration file on the VM.
    Will attempt for 8 minutes before timing out.

    :param vm:
        the Palo Alto VM instance.
    :param ip:
        the IP of the VM.
    :param username:
        the user to connect the VM as (the one commanding the configuration import)
    :param password:
        the password for the provided username.
    :param filepath:
        the absolute path to the file to import
    :return:
        a 'Request' response
    """
    timeout_time = 8 * 60  # 8 minutes
    start_time = time.time()
    while True:
        try:
            with vm.api(ip, username, password) as conn:
                http_res = conn.import_configuration_file(filepath)
            if 'response status="success"' not in http_res.text:
                raise exceptions.PaloAltoXmlConfigError(f"ERROR: failed to import configuration file!: {str(http_res.text)}")
            return http_res
        except Exception as e:
            if start_time + timeout_time <= time.time():
                raise exceptions.PaloAltoXmlConfigError(f"ERROR: timeout while waiting to import configuration file!: {str(e)}")
            logger_function(f"Failed to connect to {ip}... retrying...")
            time.sleep(10)


def load_configuration_file(
    filename: str, vm: esxi_utils.vm.PaloAltoFirewallVirtualMachine, non_default_username: str, password: str, logger_function: typing.Callable
) -> "Response":
    """
    Executes a series of Palo Alto CLI commands to load an XML configuration file.

    :param filename:
        The name of the file (NOT the path) to load.
    :param vm:
        the Palo Alto VM instance.
    :param non_default_username:
        The username of a VM 'superuser' that isn't the default user (typically 'admin').
        This is important because the default username typically has the password overwritten.
    :param password:
        The password for the 'non_default_username'.

    :return: A `types.Response` object for the executed command
    """
    res = vm.tools.load_configuration_file(non_default_username=non_default_username, password=password, filename=filename)
    if not res.ok:
        raise exceptions.PaloAltoXmlConfigError(
            f"ERROR: Failed to load configuration file: {filename} using account: {non_default_username} ... Response code is not 'OK' ... {str(res)}"
        )
    elif "does not exist" in str(res.stdout):
        raise exceptions.PaloAltoXmlConfigError(
            f"ERROR: Failed to load configuration file: {filename} using account: {non_default_username} ... Configuration file name not found on VM! ... {str(res)}"
        )
    logger_function(f"Loaded configuration file: {filename}")
    return res


def load_all_xml_configs(
    is_panorama: bool,
    vm: esxi_utils.vm.PaloAltoFirewallVirtualMachine,
    api: esxi_utils.util.connect.PanosAPIConnection,
    ip: str,
    gateway: str,
    username: str,
    password: str,
    logger_function: typing.Callable,
    netmask: str,
    hashed_password: typing.Optional[str] = None,
    hashed_secret: typing.Optional[str] = None,
    xml_path: typing.Optional[str] = None,
) -> typing.Dict:
    """
    Iterates through the 'xml_config' directory for either Panorama or firewall configuration files and tries to load each one.

    :param is_panorama:
        Set this to True if you are licensing a Panorama machine. Set to False to license a firewall.
    :param vm:
        The ESXi VM instance.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip.
    :param ip:
        The IP to replace in the config file
    :param gateway:
        The default gateway to replace in the config file
    :param username:
        The username of a VM 'superuser' to replace in the config file.
    :param password:
        The password for the provided 'username'.
    :param hashed_password:
        The Palo Alto 'phash' hash of the password to give to the admin user in the configuration file.
    :param hashed_secret:
        The Palo Alto 'secret' hash to assign to all secrets in the configuration file.
        This value cannot be generated in the same way as 'hashed_password' and must first be entered into the GUI.
        The value entered into the GUI can then be copied and pasted into this programs configuration file.
    :param netmask:
        The netmask for the provided 'ip' parameter to replace in the config file.

    :return:
        A dict of key=path to config file, value=result of configuration load
    """
    path_result_dict = dict()
    list_of_paths = traverse_xml_directory(is_panorama=is_panorama, xml_path=xml_path)
    p: str
    for p in list_of_paths:
        original_p = p
        logger_function(f"Testing configuration file with path: {p}")
        filename = p.split("/")[-1]

        if hashed_password is not None:
            logger_function("Replacing hashed password for 'admin' user, replacing \"dummy hashes\" and writing to temporary xml file...")
            with open(p, "r") as file:
                config_data = file.read()
            entry_index = config_data.find('<entry name="admin">')
            if hashed_secret and entry_index >= 0:
                # replace the current password hash
                current_hash = misc.extract_string_from_tag(config_data, "<phash>", "</phash>", start_index=entry_index)
                config_data = config_data.replace(current_hash, hashed_password, 1)
                # replace 'variables' in the file
                # the hash that you can create on the command line will NOT WORK for these values below.
                # You have to manually change the values in the GUI and then copy+paste the generated value
                # from the exported configuration file
                config_data = (
                    config_data.replace(c.XML_CONFIG_AUTH_PWD_KEY, hashed_secret)
                    .replace(c.XML_CONFIG_PRIV_PWD_KEY, hashed_secret)
                    .replace(c.XML_CONFIG_RADIUS_SECRET_KEY, hashed_secret)
                )
                logger_function("Replaced hashes.")
                config_data = _replace_management_ip(
                    data=config_data, desired_ip=ip, desired_netmask=netmask, desired_gateway=gateway, logger_function=logger_function
                )

                p = path.join(".", filename)
                with open(p, "w") as file:
                    file.write(config_data)
                logger_function("Temporary configuration written to disk.")
            else:
                logger_function('WARN: Hashed password was provided to overwrite XML configs but no "admin" user was found in XML config file!')
        # end of hashed password if statement

        logger_function("Importing the configuration file to the VM...")
        import_configuration_file(vm=vm, ip=ip, username=username, password=password, filepath=p, logger_function=logger_function)

        logger_function("Loading XML configuration file and recording output...")
        res = load_configuration_file(filename=filename, vm=vm, non_default_username=username, password=password, logger_function=logger_function)

        logger_function("Awaiting commit to verify load...")
        job_number = parse_job_number(text=str(res.stdout), import_category=c.COMMIT_JOB_KEY)
        successful_job, commit_information = installing_wait_loop(
            software_name=f"Commit configuration file with name: {filename}",
            job_number=job_number,
            api=api,
            logger_function=logger_function,
            msg_name="commit job",
            exit_on_fail=False,
            return_res=True,
            print_conn_refused=True
        ) # type: ignore
        if not successful_job:
            err_str = (
                f"ERROR: Failed to commit configuration(Job #{job_number})! Configuration load response: {res.stdout}\nCommit response:{commit_information}"
            )
            raise exceptions.PaloAltoXmlConfigError(f"ERROR: Failed to commit configuration!: {str(err_str)}")
        logger_function('Commit "OK!" ... Configuration file was successful.\n')

        # remove temporary file
        if hashed_password and p != original_p:
            misc.remove_file(p)

        login_msg_location = res.stdout.lower().find("number of failed attempts since last") # type: ignore
        if login_msg_location < 0:
            t = str(res.stdout)
        else:
            t = str(res.stdout[0:login_msg_location])
        if commit_information:
            t += "***\nCommit Information:\n" + str(commit_information.stdout) + "\n***"
        path_result_dict[original_p] = t
    # end of loop for all config file paths
    return path_result_dict


def _replace_management_ip(
    data: str, desired_ip: str, desired_netmask: str, desired_gateway: str, logger_function: typing.Callable, agent_ip: typing.Optional[str] = None
) -> str:
    """
    Replaces the current 'management IP' in the config file with the provided desired IP.

    :param data:
        The entire config file as a string
    :param desired_ip:
        The IP to overwrite the one in the config file 'data'
    :param netmask:
        The netmask for the provided 'ip' parameter to replace in the config file.
    :param desired_gateway:
        The default gateway to replace in the config file
    :param agent_ip:
        The IP of the agent to add as a 'permitted IP' (allowing access to panorama after config loads)
        If None (default): will use the 'desired_gateway' parameter as the IP to permit

    :return:
        The overwritten data if successful. If any XML tags can't be found: will return the original data that was input
    """
    logger_function("Replacing management IP and netmask in config with current IP...")
    # find deviceconfig 'parent'
    deviceconfig_index = data.find(c.XML_CONFIG_MANAGEMENT_IP_KEY_START)
    if deviceconfig_index < 0:
        logger_function(f'WARN: No "Management IP" found under a "{c.XML_CONFIG_MANAGEMENT_IP_KEY_START}" tag in the config file. IP will not be replaced!')
        return data

    # find ip tags
    ip_address_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR, deviceconfig_index)
    if ip_address_index < 0 or ip_address_index >= data.find(c.XML_CONFIG_MANAGEMENT_IP_KEY_END, deviceconfig_index):
        logger_function(
            f'WARN: No "{c.XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR}" tag found under a "{c.XML_CONFIG_MANAGEMENT_IP_KEY_START}" tag ... Management IP will not be replaced!'
        )
        return data
    # there has to be a closing tag next (otherwise the linter failed)
    ip_close_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR_END, ip_address_index)
    # replace ip address
    desired_ip_xml = c.XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR + desired_ip
    data = data[:ip_address_index] + desired_ip_xml + data[ip_close_index:]
    logger_function(f"Changed management IP in config to: {desired_ip}")

    # now find netmask
    netmask_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR, deviceconfig_index)
    if netmask_index < 0 or netmask_index >= data.find(c.XML_CONFIG_MANAGEMENT_IP_KEY_END, deviceconfig_index):
        logger_function(
            f'WARN: No "{c.XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR}" tag found under a "{c.XML_CONFIG_MANAGEMENT_IP_KEY_START}" tag ... Netmask will not be replaced!'
        )
        return data
    netmask_close_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR_END, netmask_index)
    # replace netmask
    desired_netmask_xml = c.XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR + desired_netmask
    data = data[:netmask_index] + desired_netmask_xml + data[netmask_close_index:]
    logger_function(f"Changed management IP netmask in config to: {desired_netmask}")

    # now find gateway
    gateway_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR, deviceconfig_index)
    if gateway_index < 0 or gateway_index >= data.find(c.XML_CONFIG_MANAGEMENT_IP_KEY_END, deviceconfig_index):
        logger_function(
            f'WARN: No "{c.XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR}" tag found under a "{c.XML_CONFIG_MANAGEMENT_IP_KEY_START}" tag ... Gateway will not be replaced!'
        )
        return data
    gateway_close_index = data.find(c.XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR_END, gateway_index)
    # replace gateway
    desired_gateway_xml = c.XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR + desired_gateway
    data = data[:gateway_index] + desired_gateway_xml + data[gateway_close_index:]
    logger_function(f"Changed default gateway in config to: {desired_gateway}")

    # now find permitted IPs
    permitted_ips_index = data.find(c.XML_CONFIG_DEFAULT_PERMITTED_IP_TAG, deviceconfig_index)
    if permitted_ips_index < 0 or permitted_ips_index >= data.find(c.XML_CONFIG_MANAGEMENT_IP_KEY_END, deviceconfig_index):
        logger_function(
            f'WARN: No "{c.XML_CONFIG_DEFAULT_PERMITTED_IP_TAG}" tag found under a "{c.XML_CONFIG_MANAGEMENT_IP_KEY_START}" tag ... Permitted IP will not be added!'
        )
        return data
    # add a permitted IP
    if agent_ip is None:
        agent_ip = desired_gateway
    # convert given values for IP and netmask into IP/cidr
    i = ipaddress.ip_interface(agent_ip + "/" + desired_netmask)
    desired_permitted_ip_xml = '<entry name="' + i.with_prefixlen + '"/>'
    # we aren't replacing here, so we have different indexes to find to make sure we include all the data
    data = (
        data[: permitted_ips_index + len(c.XML_CONFIG_DEFAULT_PERMITTED_IP_TAG)]
        + "\n"
        + desired_permitted_ip_xml
        + data[permitted_ips_index + len(c.XML_CONFIG_DEFAULT_PERMITTED_IP_TAG) :]
    )
    logger_function(f"Added permitted IP: {agent_ip}")

    return data


def write_out_xml_config_result(output_path: str, result_dict: typing.Dict, vm_name: str, logger_function: typing.Callable):
    """
    Writes out a file with the configuration file output for each config file loaded.

    :param output_path:
        The path to write to (will overwrite existing files)
    :param result_dict:
        The dictionary holding the config file load results (see load_all_xml_configs)
    """
    logger_function(f"Writing config file output to file path: {output_path}")
    with open(output_path, "w") as file:
        file.write(f"VM Name: {vm_name}\n")
        file.write(
            'Fields that were replaced temporarily for testing: admin\'s "phash", radius "secrets", "SNMP authpwd", "SNMP privpwd", and management IP address.\n'
        )
        file.write("Output from each loaded configuration file:\n")
        file.write("-" * 45)
        file.write("\n")
        file.write("-" * 45)
        file.write("\n\n")
        for path, result in result_dict.items():
            file.write("-" * 60)
            file.write("\n")
            file.write("File Path: " + path + "\n")
            file.write("-" * 60)
            file.write("\n")
            file.write(result + "\n")
    logger_function("Finished outputting config file results.")


def reset_configuration_to_factory(
    api: esxi_utils.util.connect.PanosAPIConnection, logger_function: typing.Callable, shutdown: bool = False
):
    """
    Uses the API to reset the VM to 'factory' (no configuration loaded). VM will reboot.
    Also will clear the logs.
    Will attempt for 8 minutes before timing out.

    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        the function to use to print output messages to
    :param shutdown:
        whether to provide the 'shutdown' parameter to the command or not

    :return:
        the Response from the API for 'request system private-data-reset'
    """
    cmd = "request system private-data-reset"
    if shutdown:
        cmd += " shutdown"
    res = wait_for_api_resp(
        api=api,
        api_cmd=cmd,
        timeout_time=8 * 60,  # 8 minutes
        timeout_msg="ERROR: timeout while waiting to reset configuration to factory!",
        print_connection_error=True,
        logger_function=logger_function,
    )
    return res
