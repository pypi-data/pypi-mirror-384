### ### ###
# Licensing
### ### ###
licensing_dict = {
    "gpgateway": "GlobalProtect Gateway",
    "pa-vm": "PA-VM",  # firewall
    "support": "Put Your Support Type Here",
    "threats": "Threat Prevention",
    "url3": "PAN-DB URL Filtering",
    "wildfire": "WildFire License",
    "panorama": "Device Management License",
    "panorama_support": "Put Your Support Type Here",
}

### ### ###
# Software
### ### ###

# example panorama upgrade chain
# Panorama has a lot of version upgrades that must be completed in sequence
# This is done to retain the 'legacy mode' that is still in use from version 8
# 7 restarts * 8 minute reload time = 56 minutes just for this step
# PANO_SOFTWARE_UPGRADE_CHAIN = ["8.1.24", "restart", "9.0.0", "9.0.16-h3", "restart", "9.1.0", "9.1.15", "restart",
#                                 "10.0.0", "restart", "10.0.11-h1", "restart", "10.1.0", "restart", "10.1.8", "restart"]

ANTI_VIRUS_KEY = "antivirus"
CONTENT_KEY = "application_contents"
APPS_KEY = "apps"
FIREWALL_SOFTWARE_KEY = "firewall_version_"  # + version
FIREWALL_SOFTWARE_FILE_PREFIX = "PanOS_vm-"  # + version
PANO_SOFTWARE_KEY = "panorama_version_"  # + version
PANO_SOFTWARE_FILE_PREFIX = "Panorama_pc-"  # + version
SOFTWARE_KEY = "software"
GLOBAL_PROTECT_CLIENT_KEY = "global-protect-client"
GLOBAL_PROTECT_VPN_KEY = "global-protect-clientless-vpn"
WILDFIRE_KEY = "wildfire"

# contains a mapping of software type -> command to check if that software is upgraded
check_installed_commands_dict = {
    ANTI_VIRUS_KEY: "request anti-virus upgrade info",
    CONTENT_KEY: "request content upgrade info",
    APPS_KEY: "request content upgrade info",
    FIREWALL_SOFTWARE_KEY: "show system info",  # request system software info <- this will show files on the machine (not currently installed version)
    PANO_SOFTWARE_KEY: "show system info",
    SOFTWARE_KEY: "show system info",
    WILDFIRE_KEY: "request wildfire upgrade info",
    GLOBAL_PROTECT_CLIENT_KEY: "request global-protect-client software info",
    GLOBAL_PROTECT_VPN_KEY: "request global-protect-clientless-vpn upgrade info",
}

# contains a mapping of software type -> software is already installed substring
# this only works for offline installs ... Online will all possibilities instead of just the installed file
software_is_installed_offline_dict = {
    ANTI_VIRUS_KEY: "<version>",
    CONTENT_KEY: "<version>",
    APPS_KEY: "<version>",
    FIREWALL_SOFTWARE_KEY: "<sw-version>",  # + FIREWALL_SOFTWARE_UPGRADE_VERSION + '</sw-version>'
    WILDFIRE_KEY: "<version>",
    GLOBAL_PROTECT_CLIENT_KEY: "<version>",
    GLOBAL_PROTECT_VPN_KEY: "<version>",
}

# contains a mapping of software type -> import keys to whether this software is already installed
software_is_installed_online_dict = {"version": "<version>", "downloaded": "<downloaded>yes", "installing": "<installing>yes", "current": "<current>yes"}

BASE_URL_PATH = "https://"  # + ip + API_PATH
API_PATH = "/api/"
IMPORT_QUERY_STRING = "?type=import&category="
# contains a mapping of software type -> query string to import that software through the Palo Alto API
import_category_dict = {ANTI_VIRUS_KEY: "anti-virus", CONTENT_KEY: "content", APPS_KEY: "content", SOFTWARE_KEY: "software"}

# contains a mapping of software type -> command to install that type of software
install_software_dict = {
    ANTI_VIRUS_KEY: "request anti-virus upgrade install file ",
    CONTENT_KEY: 'request content upgrade install skip-content-validity-check "yes" file ',
    APPS_KEY: 'request content upgrade install skip-content-validity-check "yes" file ',
    FIREWALL_SOFTWARE_KEY: "request system software install version ",
    PANO_SOFTWARE_KEY: "request system software install version ",
    SOFTWARE_KEY: "request system software install version ",
    WILDFIRE_KEY: "request wildfire upgrade install file ",
    GLOBAL_PROTECT_VPN_KEY: "request global-protect-clientless-vpn upgrade install file ",
    GLOBAL_PROTECT_CLIENT_KEY: "request global-protect-client software activate file ",  # this one is a little strange
}

# contains a mapping of software type -> searchable filename substring
discovery_dict = {
    ANTI_VIRUS_KEY: "panup-all-antivirus-",  # antivirus file used by both firewall and panorama
    CONTENT_KEY: "panupv2-all-contents-",  # firewall only
    APPS_KEY: "panupv2-all-apps-",  # panorama only
}

# dictionaries for 'online' software installs
# is a 'check' command needed too?
download_software_dict = {  # enqueues job
    ANTI_VIRUS_KEY: "request anti-virus upgrade download latest",  # File successfully download
    CONTENT_KEY: "request content upgrade download latest",
    FIREWALL_SOFTWARE_KEY: "request system software download version ",
    PANO_SOFTWARE_KEY: "request system software download version ",
    SOFTWARE_KEY: "request system software download version ",
    GLOBAL_PROTECT_CLIENT_KEY: "request global-protect-client software download version ",
    GLOBAL_PROTECT_VPN_KEY: "request global-protect-clientless-vpn upgrade download latest",
    WILDFIRE_KEY: "request wildfire upgrade download latest",
}
online_software_install_dict = {  # enqueues job
    ANTI_VIRUS_KEY: 'request anti-virus upgrade install version "latest"',  # normal 'commited' message
    CONTENT_KEY: 'request content upgrade install version "latest"',
    FIREWALL_SOFTWARE_KEY: "request system software install version ",
    PANO_SOFTWARE_KEY: "request system software install version ",
    SOFTWARE_KEY: "request system software install version ",
    GLOBAL_PROTECT_VPN_KEY: 'request global-protect-clientless-vpn upgrade install version "latest"',
    GLOBAL_PROTECT_CLIENT_KEY: "request global-protect-client software activate version ",
    WILDFIRE_KEY: 'request wildfire upgrade install version "latest"',
}

### ### ###
# VM SERIES
### ### ###

# Example hardware specs for each type of firewall
series_dict = {
    "VM-50": {"vcpus": 2, "memory": "6GB", "disk": 62},
    "VM-100": {"vcpus": 2, "memory": "7GB", "disk": 62},
    "VM-200": {"vcpus": 2, "memory": "7GB", "disk": 62},
    "VM-300": {"vcpus": 4, "memory": "11GB", "disk": 62},
    "VM-1000-HV": {"vcpus": 4, "memory": "11GB", "disk": 62},
    "VM-500": {"vcpus": 8, "memory": "16GB", "disk": 62},
    "VM-700": {"vcpus": 16, "memory": "56GB", "disk": 62},
}

# XML Configuration files
XML_CONFIG_START_DIR = "./"
XML_CONFIG_DIR_NAME = "xml_config"
XML_CONFIG_FIREWALL_DIR_NAME = "fwh_firewall"
XML_CONFIG_PANORAMA_DIR_NAME = "fwm_panorama"

XML_CONFIG_AUTH_PWD_KEY = "PaloAlto.auth.hash"
XML_CONFIG_PRIV_PWD_KEY = "PaloAlto.priv.hash"
XML_CONFIG_RADIUS_SECRET_KEY = "PaloAlto.radius.hash"
XML_CONFIG_MANAGEMENT_IP_KEY_START = "<deviceconfig>"
XML_CONFIG_MANAGEMENT_IP_KEY_END = "</deviceconfig>"
XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR = "<ip-address>"
XML_CONFIG_DEFAULT_DEVICE_IP_XML_STR_END = "</ip-address>"
XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR = "<netmask>"
XML_CONFIG_DEFAULT_DEVICE_NETMASK_XML_STR_END = "</netmask>"
XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR = "<default-gateway>"
XML_CONFIG_DEFAULT_DEVICE_GATEWAY_XML_STR_END = "</default-gateway>"
XML_CONFIG_DEFAULT_PERMITTED_IP_TAG = "<permitted-ip>"  # <entry name="x.x.x.x/y"/>
XML_CONFIG_DEFAULT_PERMITTED_IP_TAG_END = "</permitted-ip>"

COMMIT_JOB_KEY = "commit"
