import ipaddress
import time
import typing
from datetime import datetime, timezone
from os import path as ospath

import esxi_utils
from graphex import (Boolean, InputSocket, ListOutputSocket, Node, Number,
                     OptionalInputSocket, OutputSocket, String)
from graphex import exceptions as graphex_exceptions

from graphex_esxi_utils import (datatypes, esxi_constants, exceptions,
                                panos_constants)
from graphex_esxi_utils.utils import misc as misc_utils
from graphex_esxi_utils.utils import palo_alto as palo_alto_util_fns
from graphex_esxi_utils.utils import palo_alto_xml as palo_alto_xml_fns


class PaloAltoGetSeriesSpec(Node):
    name: str = "ESXi Palo Alto Get Firewall Model Hardware Requirements"
    description: str = "Outputs the minimum vCPU, memory, and disk requirements for the provided PanOS VM series string. Will raise an exception if the provided VM series is not known."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    input_value = InputSocket(
        datatype=String,
        name="VM Series",
        description="The vm-series you want the information for. Options are: VM-50, VM-100, VM-200, VM-300, VM-1000-HV, VM-500, or VM-700",
    )

    vcpus = OutputSocket(datatype=Number, name="vCPUs", description="The number of vCPUs this series requires.")
    memory = OutputSocket(datatype=String, name="Memory", description="The amount of memory (RAM) this series requires (in the form of <number><byte_unit>)")
    disk_size = OutputSocket(datatype=Number, name="Disk Size GB", description="The amount of disk usage (storage) this series requires (in GB)")

    def run(self):
        series = self.input_value.upper()
        if not series in panos_constants.series_dict:
            raise exceptions.PaloAltoSeriesError(series, str(panos_constants.series_dict.keys()))
        self.vcpus = panos_constants.series_dict[series]["vcpus"]
        self.memory = panos_constants.series_dict[series]["memory"]
        self.disk_size = panos_constants.series_dict[series]["disk"]


class PaloAltoGetLicensingInfo(Node):
    name: str = "ESXi Palo Alto Get License Title (ID) Keywords"
    description: str = "Outputs the title keywords/substrings that identify the various license files that can be installed on a Palo Alto VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    gpgateway = OutputSocket(datatype=String, name="gpgateway", description="The Global Protect Gateway license ID.")
    pavm = OutputSocket(datatype=String, name="pa-vm", description="The firewall 'primary' license ID.")
    support = OutputSocket(datatype=String, name="support", description="The support level ID.")
    threats = OutputSocket(datatype=String, name="threats", description="The threat prevention license ID.")
    url3 = OutputSocket(datatype=String, name="url3", description="The pan-db url filtering license ID.")
    wildfire = OutputSocket(datatype=String, name="wildfire", description="The wildfire license ID.")
    panorama = OutputSocket(datatype=String, name="panorama", description="The panorama 'primary' license ID.")
    panorama_support = OutputSocket(datatype=String, name="panorama_support", description="The panroama support level license ID.")

    def run(self):
        self.gpgateway = panos_constants.licensing_dict["gpgateway"]
        self.pavm = panos_constants.licensing_dict["pa-vm"]
        self.support = panos_constants.licensing_dict["support"]
        self.threats = panos_constants.licensing_dict["threats"]
        self.url3 = panos_constants.licensing_dict["url3"]
        self.wildfire = panos_constants.licensing_dict["wildfire"]
        self.panorama = panos_constants.licensing_dict["panorama"]
        self.panorama_support = panos_constants.licensing_dict["panorama_support"]


class PaloAltoGetLicensingInfoByKey(Node):
    name: str = "ESXi Palo Alto Get License ID by Key"
    description: str = "Outputs the title keywords/substrings that identify the various license files that can be installed on a Palo Alto VM (via key). See 'ESXi Palo Alto Get License Title (ID) Keywords' for an output of every key."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    input_value = InputSocket(
        datatype=String,
        name="Key Name",
        description="The name of the key (e.g. gpgateway, pa-vm, support, threats, url3, wildfire, panorama, panorama_support)",
    )

    lic_id = OutputSocket(datatype=String, name="License ID", description="The license ID.")

    def run(self):
        self.lic_id = panos_constants.licensing_dict[self.input_value]


class PaloAltoLicenseInfoGetFeature(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Feature Name"
    description: str = "Outputs the feature/name of the License."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Feature/Name", description="The feature/name of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = d["feature"]


class PaloAltoLicenseInfoGetDescription(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Description"
    description: str = "Outputs the description of the License."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Description", description="The description of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = d["description"]


class PaloAltoLicenseInfoGetSerial(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Serial"
    description: str = "Outputs the serial of the License."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Serial", description="The serial of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = d["serial"]


class PaloAltoLicenseInfoGetIssueDate(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Issue Date"
    description: str = "Outputs the issue date of the License (as a String)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Issue Date", description="The issue date of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = str(d["issued"])


class PaloAltoLicenseInfoGetExpireDate(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Expiration Date"
    description: str = "Outputs the expiration date of the License (as a String)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Expiration Date", description="The expiration date of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = str(d["expires"])


class PaloAltoLicenseInfoIsExpired(Node):
    name: str = "ESXi PaloAltoLicenseInfo License Is Expired"
    description: str = "Outputs the whether the License is expired or not."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=Boolean, name="Is Expired?", description="True if the license has expired.")

    def run(self):
        d: dict = self.input_obj
        self.output_value = d["expired"]


class PaloAltoLicenseInfoGetAuthCode(Node):
    name: str = "ESXi PaloAltoLicenseInfo Get Authorization Code"
    description: str = "Outputs the auth code (authcode) of the License (as a String)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_LICENSE_INFO

    input_obj = InputSocket(
        datatype=datatypes.PaloAltoLicenseInfo, name="PaloAltoLicenseInfo Object", description="The object that represents information about the license."
    )

    output_value = OutputSocket(datatype=String, name="Auth Code", description="The authcode of the License")

    def run(self):
        d: dict = self.input_obj
        self.output_value = str(d["authcode"])


class PaloAltoGetSoftwareInfoCheck(Node):
    name: str = "ESXi Palo Alto Check Available Software Versions"
    description: str = "Checks and records the available software versions into a PaloAltoSoftwareInfo object. Does so by running 'request system software check'. This only looks for the 'primary' software version (e.g. not support software such as anti-virus). Use 'ESXi Palo Alto Check Latest Support Software' for support software."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_SW_INFO

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")

    software_info = OutputSocket(
        datatype=datatypes.PaloAltoSoftwareInfo,
        name="Software Info Object",
        description="An object containing information about the available software for download.",
    )

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        # get the xml response for all available primary software versions
        res = palo_alto_util_fns.check_software_versions(api=self.panos_api, logger_function=self.log)
        # create a dict to store a mapping of each version
        versions_dict = dict()
        entry_list = str(res.stdout).split("<entry>")
        firstValue = True
        for entry in entry_list:
            if firstValue:
                firstValue = False
                continue
            subdict = dict()
            entry = str(entry.split("</entry>")[0])
            version = misc_utils.extract_string_from_tag(entry, "<version>", "</version>")
            subdict["version"] = version
            subdict["filename"] = misc_utils.extract_string_from_tag(entry, "<filename>", "</filename>")
            subdict["released-on"] = misc_utils.extract_string_from_tag(entry, "<released-on>", "</released-on>")
            subdict["downloaded"] = misc_utils.extract_string_from_tag(entry, "<downloaded>", "</downloaded>")
            subdict["current"] = misc_utils.extract_string_from_tag(entry, "<current>", "</current>")
            subdict["latest"] = misc_utils.extract_string_from_tag(entry, "<latest>", "</latest>")
            versions_dict[version] = subdict
        self.software_info = versions_dict


class PaloAltoGetSoftwareGetLatest(Node):
    name: str = "ESXi Palo Alto Software Info Get Latest Version"
    description: str = "Searches the software info object for version tagged as 'latest'. Will throw an exception if latest can't be found or if latest isn't tagged by Palo Alto."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_SW_INFO

    obj = InputSocket(datatype=datatypes.PaloAltoSoftwareInfo, name="Software Info", description="The PaloAltoSoftwareInfo object to use.")

    latest = OutputSocket(datatype=String, name="Latest Version", description="The latest version for this software.")

    def run(self):
        available_versions_dict: dict = self.obj

        latest = None
        for v_metadata in available_versions_dict.values():
            if v_metadata["latest"] == "yes":
                latest = v_metadata["version"]
                break
        if latest is None:
            raise exceptions.PaloAltoVersionError("ERROR: No software version metadata found matching tag 'latest'")

        self.latest = latest


class PaloAltoGetSoftwareGetAll(Node):
    name: str = "ESXi Palo Alto Software Info Get All Versions"
    description: str = "Returns all versions found by the software info object."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_SW_INFO

    obj = InputSocket(datatype=datatypes.PaloAltoSoftwareInfo, name="Software Info", description="The PaloAltoSoftwareInfo object to use.")

    all_v = ListOutputSocket(datatype=String, name="All Versions", description="All available software versions.")

    def run(self):
        available_versions_dict: dict = self.obj
        self.all_v = available_versions_dict.keys()


class PaloAltoGetSoftwareGetVersionMetadata(Node):
    name: str = "ESXi Palo Alto Software Info Get Version Metadata"
    description: str = "Outputs all the metadata info for a specific version."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_SW_INFO

    obj = InputSocket(datatype=datatypes.PaloAltoSoftwareInfo, name="Software Info", description="The PaloAltoSoftwareInfo object to use.")
    v = InputSocket(datatype=String, name="Version", description="The version to get metadata about.")

    filename = OutputSocket(datatype=String, name="Filename", description="")
    released = OutputSocket(datatype=String, name="Released On", description="")
    downloaded = OutputSocket(datatype=String, name="Downloaded", description="")
    current = OutputSocket(datatype=String, name="Current", description="")
    latest = OutputSocket(datatype=Boolean, name="Latest?", description="Whether this is the latest software version or not.")

    def run(self):
        available_versions_dict: dict = self.obj
        subdict = available_versions_dict[self.v]
        self.filename = str(subdict["filename"])
        self.released = str(subdict["released-on"])
        self.downloaded = str(subdict["downloaded"])
        self.current = str(subdict["current"])
        self.latest = True if str(subdict["latest"]) == "yes" else False


class EsxiVirtualMachinePaloAltoCheckIfSoftwareVersionShouldInstall(Node):
    name: str = "ESXi Panos VM Check if Software is Valid Install"
    description: str = "Compares the two software versions provided to see if this is a valid 'upgrade path' / 'install path'. Outputs a string containing one of the following values: 'equal', 'valid', or 'invalid'. When the value is 'equal': you do not need to install the new software. Will raise an error if the version path can't be determined."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    current_version = InputSocket(datatype=String, name="Current Version", description="The current software version installed on the VM.")
    requested_version = InputSocket(datatype=String, name="Requested Version", description="The software version that you want to install on the VM.")

    output_v = OutputSocket(datatype=String, name="Query Result", description="A value of 'equal', 'valid', or 'invalid' for this software upgrade path.")

    def run(self):
        install_query = palo_alto_util_fns.check_version(self.current_version, self.requested_version, logger_function_error=self.log_error)
        if install_query == "error" or install_query == "unknown_z":
            raise exceptions.PaloAltoParsingError(
                "ERROR: Couldn't determine if this version is supposed to be installed. Check previous error for specific information."
            )
        self.output_v = install_query


class PaloAltoCheckSupportSoftwareInstalled(Node):
    name: str = "ESXi Palo Alto Check Support Software Installed"
    description: str = "Runs an 'op' command via the Palo Alti API to check if any support software is installed on the provided VM. The command run depends on the 'Software Type' given. Valid inputs are 'antivirus', 'application_contents',  'apps', 'wildfire', 'global-protect-client', and 'global-protect-clientless-vpn'. Will wait for up to 8 minutes waiting for a connection."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_SW_INFO

    software_type = InputSocket(
        datatype=String,
        name="Software Type",
        description="The type of software to check. Valid inputs are 'antivirus', 'application_contents',  'apps', 'wildfire', 'global-protect-client', and 'global-protect-clientless-vpn'",
    )

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")

    is_installed = OutputSocket(datatype=Boolean, name="Is Installed?", description="Outputs True if one version of this software is already installed.")

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        sw_type = self.software_type.lower()
        valid_types = ["antivirus", "application_contents", "apps", "wildfire", "global-protect-client", "global-protect-clientless-vpn"]
        if sw_type not in valid_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Software Type", sw_type, valid_types)

        command_response = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd=panos_constants.check_installed_commands_dict[sw_type],
            logger_function=self.log,
            timeout_time=8 * 60,
            timeout_msg="ERROR: timeout while waiting to check if support software is installed!"
        )
        self.is_installed = True if panos_constants.software_is_installed_online_dict["current"] in str(command_response.stdout) else False
        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class PaloAltoDelicenseVm(Node):
    name: str = "ESXi Palo Alto Remove Licenses (Delicense)"
    description: str = "Deactivates licenses on firewalls and removes license files from Panorama VMs."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")

    reboot = InputSocket(
        datatype=Boolean,
        name="Reboot?",
        description="If set to True: will restart the VM after removing licenses and verify that both the licenses and serial number have been removed.",
        input_field=True,
    )
    is_panorama = InputSocket(
        datatype=Boolean,
        name="Is Panorama?",
        description="Set this to True if you are licensing a Panorama machine. Set to False to license a firewall.",
        input_field=False,
    )

    panorama_delicense_serial_no = InputSocket(
        datatype=String,
        name="Panorama Delicense Serial#",
        description="The license number that gets assigned when delicensing a Panorama machine.",
        input_field="000000000000",
    )

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        is_panorama = self.is_panorama

        self.log("\nDelicensing VM...")

        lic_l = palo_alto_util_fns.get_license_info(api=self.panos_api, logger_function=self.log)

        # check if the VM needs to be delicensed
        if len(lic_l) <= 0:
            s_no = palo_alto_util_fns.get_serial_no(api=self.panos_api, logger_function=self.log)
            self.log(f"Serial number assigned to VM is: {str(s_no)}")
            if "unknown" in str(s_no) or str(s_no) == self.panorama_delicense_serial_no:
                self.log("VM has no serial number and all licenses are missing. Delicense is not required. Skipping!")
                return
            else:
                raise exceptions.PaloAltoDelicenseError(f"All licenses are missing but VM still has serial number!: {s_no}")

        # delicense
        if is_panorama:
            license_filenames = palo_alto_util_fns.extract_license_filenames(lic_l)
            for l_file in license_filenames or []:
                self.log(f"Deleting License File: {l_file}")
                res = palo_alto_util_fns.wait_for_api_resp(
                    api=self.panos_api,
                    api_cmd=f'delete license key "{l_file}"',
                    timeout_time=3 * 60,  # 3 minutes
                    timeout_msg="ERROR: timeout while waiting to delete license file!",
                    logger_function=self.log
                )
                if "<result>" in str(res.stdout):
                    self.log(f'Deletion response from VM: {misc_utils.extract_string_from_tag(str(res.stdout), "<result>", "</result>")}')
                else:
                    self.log(f"Deletion response from VM: {res.stdout}")
        else:  # is firewall
            self.log("Deactivating all licenses on firewall...")
            try:
                res = palo_alto_util_fns.wait_for_api_resp(
                    api=self.panos_api,
                    api_cmd='request license deactivate VM-Capacity mode "manual"',
                    timeout_time=6 * 60,  # 6 minutes
                    timeout_msg="ERROR: timeout while waiting to delicense firewall!",
                    logger_function=self.log
                )
                if "failed to generate encrypted token" in str(res.stdout).lower():
                    self.log_warning(f"WARNING: Strange message returned from VM: {res.stdout} ... retrying...")
                    time.sleep(20)
                    res = palo_alto_util_fns.wait_for_api_resp(
                        api=self.panos_api,
                        api_cmd='request license deactivate VM-Capacity mode "manual"',
                        timeout_time=6 * 60,  # 6 minutes
                        timeout_msg="ERROR: timeout while waiting to delicense firewall!",
                        logger_function=self.log
                    )

                self.log(f"Result of firewall delicense: {res.stdout}")
            except Exception:
                # here it appears normal for the VM API to kick us out after delicensing the VM
                self.log("VM severed connection after submitting license deactivate command.")

        # check that delicense was successful
        self.log("Checking all licenses were removed from VM...")
        lic_l = palo_alto_util_fns.get_license_info(api=self.panos_api, logger_function=self.log)
        if len(lic_l) > 0:
            raise exceptions.PaloAltoDelicenseError(f"ERROR: License files still exist after deleting! Manually remove the license files!: {str(lic_l)}")
        self.log("Successfully removed all license files from VM!")

        # reboot if the user chooses to
        if self.reboot:
            self.log("Rebooting as requested...")
            palo_alto_util_fns.restart_vm(api=self.panos_api, logger_function=self.log)
            time.sleep(6 * 60)
            self.log("Checking licenses and serial number after reboot...")
            lic_l = palo_alto_util_fns.get_license_info(api=self.panos_api, logger_function=self.log)
            if len(lic_l) > 0:
                raise exceptions.PaloAltoDelicenseError("ERROR: Failed to delicense VM! Licenses are still present after reboot!")
            s_no = palo_alto_util_fns.get_serial_no(api=self.panos_api, logger_function=self.log).strip()
            self.log(f"Serial assigned to VM is: {s_no}")
            if "unknown" != s_no and s_no != self.panorama_delicense_serial_no:
                raise exceptions.PaloAltoDelicenseError("ERROR: VM still has serial number after reboot!")

            self.log("Verified all licenses removed and serial number removed.")
        self.log("\nVM delicense complete!")


class PaloAltoLintXmlFile(Node):
    name: str = "ESXi Palo Alto Lint (Check) XML Files"
    description: str = "Check all configuration files residing in the XML directory for any errors in structure. This node will raise a 'PaloAltoXmlConfigError' Exception if the files aren't structured properly."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    is_panorama = InputSocket(
        datatype=Boolean,
        name="Is Panorama?",
        description="Set to True to check Panorama configuration files. Set to False to check firewall configuration files.",
    )
    xml_path = OptionalInputSocket(
        datatype=String,
        name="Path to XML files",
        description="The file path to the folder containing all XML files to lint/check. By default, assumes the files are located the './xml_config' path (+ /fwh_firewall or + /fwm_panorama).",
    )

    def run(self):
        fp = self.xml_path if self.xml_path else None
        palo_alto_xml_fns.check_all_xml_configs(is_panorama=self.is_panorama, logger_function=self.log, xml_path=fp)


class PaloAltoTestAllConfigurationFiles(Node):
    name: str = "ESXi Palo Alto Test Loading All XML Files"
    description: str = "Iterates through the 'xml_config' directory for either Panorama or firewall configuration files and tries to load each one. Will raise a 'PaloAltoXmlConfigError' Exception if any configuration file fails to load."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Palo Alto VM", description="The VM to use.")
    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")

    gateway = InputSocket(datatype=String, name="Gateway", description="The gateway IP to replace the value in the config file.")

    hashed_secret = InputSocket(
        datatype=String,
        name="Hashed Secret",
        description="The Palo Alto 'secret' hash to assign to all secrets in the configuration file. This value cannot be generated in the same way as 'hashed_password' and must first be entered into the GUI. The value entered into the GUI can then be copied and pasted into this programs configuration file.",
    )
    netmask = InputSocket(
        datatype=String, name="Netmask", description="The netmask for the provided 'ip' parameter to replace in the config file.", input_field="0.0.0.0"
    )

    is_panorama = InputSocket(
        datatype=Boolean,
        name="Is Panorama?",
        description="Set to True to check Panorama configuration files. Set to False to check firewall configuration files.",
    )

    output_path = InputSocket(
        datatype=String,
        name="Output Directory",
        description="Directory to save the text file containing the results of the configuration loading test.",
        input_field="/tmp/paloalto",
    )
    output_filename = InputSocket(
        datatype=String, name="Output Filename", description="What to call the file containing the results from loading all config files."
    )

    xml_path = OptionalInputSocket(
        datatype=String,
        name="Path to XML files",
        description="The file path to the folder containing all XML files to load. By default, assumes the files are located the './xml_config' path (+ /fwh_firewall or + /fwm_panorama).",
    )

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "VM is not a PaloAltoFirewallVirtualMachine"
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))
        gw = str(ipaddress.IPv4Address(self.gateway))
        nm = str(ipaddress.IPv4Address(self.netmask))
        fp = self.xml_path if self.xml_path else None

        self.log("\nStarting test of configuration files...")

        all_responses = palo_alto_xml_fns.load_all_xml_configs(
            is_panorama=self.is_panorama,
            vm=self.vm,
            api=self.panos_api,
            ip=ip_addr,
            gateway=gw,
            username=self.panos_api._username,
            password=self.panos_api._password,
            logger_function=self.log,
            hashed_password=palo_alto_util_fns.create_password_hash(
                api=self.panos_api, username=self.panos_api._username, password=self.panos_api._password, logger_function=self.log
            ),
            hashed_secret=self.hashed_secret,
            netmask=nm,
            xml_path=fp
        )
        misc_utils.create_dir_on_agent(self.output_path)
        palo_alto_xml_fns.write_out_xml_config_result(
            output_path=ospath.join(self.output_path, self.output_filename), result_dict=all_responses, vm_name=str(self.vm.name), logger_function=self.log
        )


class PaloAltoTraverseXmlFiles(Node):
    name: str = "ESXi Palo Alto Traverse XML Files"
    description: str = (
        "Iterates through the 'xml_config' directory for either Panorama or firewall configuration files and returns a list of paths to the files."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    is_panorama = InputSocket(
        datatype=Boolean,
        name="Is Panorama?",
        description="Set to True to check Panorama configuration files. Set to False to check firewall configuration files.",
    )
    xml_path = OptionalInputSocket(
        datatype=String,
        name="Path to XML files",
        description="The file path to the folder containing all XML files to lint/check. By default, assumes the files are located the './xml_config' path (+ /fwh_firewall or + /fwm_panorama).",
    )

    file_paths = ListOutputSocket(datatype=String, name="File Paths", description="All the files paths for the specified input parameters.")

    def run(self):
        fp = self.xml_path if self.xml_path else None
        self.file_paths = palo_alto_xml_fns.traverse_xml_directory(is_panorama=self.is_panorama, xml_path=fp)


class PaloAltoGetSystemMode(Node):
    name: str = "ESXi Palo Alto Get (Check) System Mode"
    description: str = "Runs the command 'show system info | match system-mode' on the Palo Alto CLI via SSH. Will wait up to 4 minutes for the connection to establish successfully."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Palo Alto VM", description="The VM to check the available software on.")
    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=4*60)

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "VM is not a PaloAltoFirewallVirtualMachine"
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))
        start_time = time.time()
        while True:
            try:
                with self.vm.ssh(ip_addr, self.panos_api._username, self.panos_api._password) as conn:
                    command_response = conn.exec("show system info | match system-mode")
                    break
            except Exception:
                if misc_utils.timeout(start_time, self.timeout):
                    raise exceptions.PaloAltoApiError("show system info | match system-mode", f"ERROR: timeout while checking for system-mode!")
                self.log(f'Failed to connect to:  "{ip_addr}"  as user: {self.panos_api._username}  ... retrying...')
                time.sleep(10)
        assert command_response, "No response"
        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f'Stdout: {self.stdout}')
        self.debug(f'Stderr: {self.stderr}')


class PaloAltoSetSystemMode(Node):
    name: str = "ESXi Palo Alto Request (Set) System Mode to Legacy"
    description: str = "Attempts to place the VM into legacy mode. This will only work if the primary software version is less than 9.y.z"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=4*60)

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        # see if this version has the option for legacy mode
        sw_version = str(palo_alto_util_fns.get_software_version(api=self.panos_api, logger_function=self.log))
        try:
            major = int(sw_version.split(".")[0])
            if major >= 9:
                raise exceptions.PaloAltoVersionError("Can't change VM to legacy mode because the major version is 9 or greater!")
        except Exception:
            self.log_warning("Exception when trying to parse major verison number... Unable to determine if legacy mode will succeed.")

        # attempt to enable legacy mode
        command_response = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd="request system system-mode legacy",
            timeout_time=self.timeout,
            timeout_msg="ERROR: timeout while waiting to set system-mode to legacy",
            logger_function=self.log
        )
        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class PaloAltoEnableDynamicUpdates(Node):
    name: str = "ESXi Palo Alto VM Enable Dynamic Updates"
    description: str = "Runs the command 'request batch license eligibility-check disable' on the Palo Alto CLI via SSH. Will wait up to 4 minutes for the connection to establish successfully."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Palo Alto VM", description="The VM to check the available software on.")
    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=4*60)

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.PaloAltoFirewallVirtualMachine), "VM is not a PaloAltoFirewallVirtualMachine"
        ip_addr = str(ipaddress.IPv4Address(self.panos_api._ip))
        start_time = time.time()
        while True:
            try:
                with self.vm.ssh(ip_addr, self.panos_api._username, self.panos_api._password) as conn:
                    command_response = conn.exec("request batch license eligibility-check disable")
                    if "Set to disabled" not in str(command_response.stdout):
                        raise exceptions.PaloAltoApiError(
                            "request batch license eligibility-check disable", f"ERROR: failed to enable dynamic updates from Panorama!: {str(command_response)}"
                        )
                    self.log("Enabled dynamic updates.")
                    break
            except Exception:
                if misc_utils.timeout(start_time, self.timeout):
                    raise exceptions.PaloAltoApiError("request batch license eligibility-check disable", f"ERROR: timeout while checking for system-mode!")
                self.log("Failed to connect... retrying...")
                time.sleep(10)
        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class PaloAltoSetUtcDate(Node):
    name: str = "ESXi Palo Alto VM Set Date for UTC Timezone"
    description: str = "Runs the command 'set clock date ...' on the Palo Alto CLI via API. The date chosen will be based on the UTC current date (when this node is run) (i.e. datetime.now(timezone.utc).strftime(%Y/%m/%d)). Will wait up to 4 minutes for the connection to establish successfully."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=4*60)

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        d = datetime.now(timezone.utc).strftime("%Y/%m/%d")  # example: 2017/11/17 ... e.g. YYYY/MM/DD
        command_response = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd=f'set clock date "{d}"',
            timeout_time=self.timeout,
            timeout_msg="ERROR: timeout while trying to set UTC date!",
            logger_function=self.log
        )
        if 'response status="success"' not in str(command_response.stdout):
            raise exceptions.PaloAltoApiError(f'set clock date "{str(d)}"', f"ERROR: failed to set UTC date!: {str(command_response)}")
        else:
            self.log(f"Successfully set date (UTC) to: {d}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class PaloAltoSetUtcTime(Node):
    name: str = "ESXi Palo Alto VM Set Time for UTC Timezone"
    description: str = "Runs the command 'set clock time ...' on the Palo Alto CLI via API. The time chosen will be based on the UTC current time (when this node is run) (i.e. datetime.now(timezone.utc).strftime(%H:%M:%S)). Will wait up to 4 minutes for the connection to establish successfully."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=4*60)

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        t = datetime.now(timezone.utc).strftime("%H:%M:%S")  # example: 01:37:45 ... e.g. HH:MM:SS
        command_response = palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api,
            api_cmd=f'set clock time "{t}"',
            timeout_time=self.timeout,  # 4 minutes
            timeout_msg="ERROR: timeout while trying to set UTC time!",
            logger_function=self.log
        )
        if 'response status="success"' not in str(command_response.stdout):
            raise exceptions.PaloAltoApiError(f'set clock time "{str(t)}"', f"ERROR: failed to set UTC time!: {str(command_response)}")
        else:
            self.log(f"Successfully set time (UTC) to: {t}")

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr


class PaloAltoGetSerialNumber(Node):
    name: str = "ESXi Palo Alto VM Get Serial Number"
    description: str = "Parses out the 'show system info' command to find the serial number of this VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    serial_no = OutputSocket(datatype=String, name="Serial Number", description="The serial number assigned to this VM.")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        self.serial_no = palo_alto_util_fns.get_serial_no(api=self.panos_api, logger_function=self.log)


class PaloAltoLatestSoftwareCheck(Node):
    name: str = "ESXi Palo Alto Check Latest Support Software"
    description: str = "Checks the available software versions for a support software (such as 'content'). This will refresh the 'latest' version. This is the equivalent of doing an apt-update on Debain Linux. Valid software types are: 'antivirus', 'application_contents', 'apps', 'anti-virus', 'content', 'wildfire', 'global-protect-client' and 'global-protect-clientless-vpn'. Use 'ESXi Palo Alto Check Available Software Versions' for the primary system software."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    software_type = InputSocket(
        datatype=String,
        name="Software Type",
        description="Valid software types are: 'antivirus', 'application_contents', 'apps' 'anti-virus', 'content', 'wildfire', 'global-protect-client' and 'global-protect-clientless-vpn'",
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8*60)

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        chosen_type = self.software_type.lower()
        valid_software_types = [
            "antivirus",
            "application_contents",
            "apps",
            "anti-virus",
            "content",
            "wildfire",
            "global-protect-client",
            "global-protect-clientless-vpn",
        ]

        if chosen_type not in valid_software_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Software Type", chosen_type, valid_software_types)

        if chosen_type == "application_contents" or chosen_type == "apps":
            chosen_type = "content"
        elif chosen_type == "antivirus":
            chosen_type = "anti-virus"

        if chosen_type != "global-protect-client":
            cmd = f"request {chosen_type} upgrade check"
        else:
            cmd = "request global-protect-client software check"
        palo_alto_util_fns.wait_for_api_resp(
            api=self.panos_api, api_cmd=cmd, logger_function=self.log, timeout_time=self.timeout
        )

class PaloAltoCreatePasswordHash(Node):
    name: str = "ESXi Palo Alto VM Create (Request) Password Hash"
    description: str = "Runs the 'op' command 'request password-hash...' via the Palo Alti API."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "PAN-OS", "Configuration"]
    color: str = esxi_constants.COLOR_PANOS_VM

    panos_api = InputSocket(datatype=datatypes.PanosAPIConnection, name="PanOS API Connection", description="A connection to the VM via a PanOS API Connection object.")
    username = InputSocket(datatype=String, name="Username", description="The username to use in the hash")
    password = InputSocket(datatype=String, name="Password", description="The password to use in the hash (for the provided username)")
    timeout = InputSocket(datatype=Number, name="Timeout", description="How many seconds to retry before throwing a timeout error.", input_field=8*60)

    hash = OutputSocket(datatype=String, name="Password Hash", description="The password hash for the provided username and password")

    def run(self):
        str(ipaddress.IPv4Address(self.panos_api._ip))
        self.hash = palo_alto_util_fns.create_password_hash(self.panos_api, username=self.username, password=self.password, logger_function=self.log, timeout=int(self.timeout))
