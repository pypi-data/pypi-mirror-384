from graphex import Number, String, Boolean, Node, InputSocket, OutputSocket, ListOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex import exceptions as graphex_exceptions
import typing
import esxi_utils

class GetEsxiServerCpuUsagePercent(Node):
    name: str = "Get ESXi Server CPU Usage Percent"
    description: str = "The amount of CPU currently being utilized by the host server as a percent (e.g. 34.54%). In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    result = OutputSocket(datatype=Number, name="CPU Utilization Percent", description="The amount of CPU being utilized as a percent.")

    def run(self):
        self.result = self.esxi_client.cpu_usage_percent()


class GetEsxiServerMemoryUsagePercent(Node):
    name: str = "Get ESXi Server Memory Usage Percent"
    description: str = "The amount of Memory (RAM) currently being utilized by the host server as a percent (e.g. 34.54%). In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")

    result = OutputSocket(datatype=Number, name="Memory Usage Percent", description="The amount of RAM being utilized as a percent.")

    def run(self):
        self.result = self.esxi_client.memory_usage_percent()


class GetEsxiServerCurrentMemoryUsage(Node):
    name: str = "Get Current ESXi Server Memory Usage"
    description: str = "Get the consumed memory (RAM) of this ESXi host server in the provided unit. In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")
    output = OutputSocket(datatype=Number, name="Used Memory Amount", description="The currently used memory (RAM) of the ESXi server host disk in the provided unit.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output = self.esxi_client.current_memory_usage(unit=used_unit)


class GetEsxiServerCurrentCpuUsage(Node):
    name: str = "Get Current ESXi Server CPU Usage"
    description: str = "Get the current CPU utilization of this ESXi host server in the provided unit. In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    unit = InputSocket(datatype=String, name="Hz Unit", description="The unit of measurement to use (one of: Hz, KHz, MHz, GHz).", input_field="Hz")
    output = OutputSocket(datatype=Number, name="CPU Utilization", description="The current CPU utilization of this ESXi host server in the provided unit.")

    def run(self):
        hz_unit_orders = ["Hz", "KHz", "MHz", "GHz"]
        # Capitalize all letters but the last one (force the last letter lowercase)
        used_unit = self.unit[:-1].upper() + self.unit[len(self.unit)-1].lower()
        if used_unit not in hz_unit_orders:
            raise graphex_exceptions.InvalidParameterError(self.name, "Hz Unit", used_unit, hz_unit_orders)
        self.output = self.esxi_client.current_cpu_usage(unit=used_unit)


class GetEsxiServerTotalMemory(Node):
    name: str = "Get ESXi Server Total Memory"
    description: str = "Get the total allocated/installed memory (RAM) of this ESXi host server in the provided unit. In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")
    output = OutputSocket(datatype=Number, name="Total Memory Amount", description="The total (max) memory (RAM) of the ESXi server host in the provided unit.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output = self.esxi_client.total_available_memory(unit=used_unit)


class GetEsxiServerTotalCpu(Node):
    name: str = "Get ESXi Server Max / Total CPU Utilization"
    description: str = "Get the maximum (total) CPU utilization possible of this ESXi host server in the provided unit. In vCenter, this represents the 'child' server and not the sum of all possible child hosts."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    unit = InputSocket(datatype=String, name="Hz Unit", description="The unit of measurement to use (one of: Hz, KHz, MHz, GHz).", input_field="Hz")
    output = OutputSocket(datatype=Number, name="CPU Utilization Maximum", description="The max (total) CPU utilization of this ESXi host server in the provided unit.")

    def run(self):
        hz_unit_orders = ["Hz", "KHz", "MHz", "GHz"]
        # Capitalize all letters but the last one (force the last letter lowercase)
        used_unit = self.unit[:-1].upper() + self.unit[len(self.unit)-1].lower()
        if used_unit not in hz_unit_orders:
            raise graphex_exceptions.InvalidParameterError(self.name, "Hz Unit", used_unit, hz_unit_orders)
        self.output = self.esxi_client.total_available_cpu_usage(unit=used_unit)


class GetEsxiParentHostName(Node):
    name: str = "Get ESXi Parent Hostname (vCenter)"
    description: str = "Returns the hostname of the parent server in this configuration. If this ESXi instance isn't a vCenter arrangement, this node will return the name of the only server in the configuration."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    result = OutputSocket(datatype=String, name="Parent Hostname", description="The parent hostname of this ESXi instance/cluster")

    def run(self):
        self.result = self.esxi_client._vcenter_hostname


class GetEsxiChildHostNames(Node):
    name: str = "Get ESXi Child Hostnames (vCenter)"
    description: str = "Returns the hostnames of all child servers in this configuration. If this ESXi instance isn't a vCenter arrangement, this node will return the name of the only server in the configuration (and the name may not be reusable in other nodes (e.g. localhost naming scheme))."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    result = ListOutputSocket(datatype=String, name="Child Hostnames", description="The child hostnames of this ESXi instance/cluster")

    def run(self):
        self.result = list(child.name for child in self.esxi_client._all_host_systems) #type:ignore


class GetEsxiVmInfoFromHost(Node):
    name: str = "Get ESXi VM Info From Host"
    description: str = "Returns the names, guest IPs, and power states of all VMs of the provided server. In vCenter, this must be the hostname of a 'child' server. An error will be raised if the hostname is not found. All output lists will be linked via index (e.g. name index 3 and guest IP index 3 refer to the same VM)"
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    child_name = InputSocket(datatype=String, name="ESXi Server Hostname/IP", description="The hostname or IP of the server to retrieve the VM names from (child server in vCenter).")
    vm_names = ListOutputSocket(datatype=String, name="VM Names", description="The VM names of this ESXi host")
    vm_power_states = ListOutputSocket(datatype=Boolean, name="VM Powered On", description="True if the VM is powered on, False if powered off.")
    vm_guest_ips = ListOutputSocket(datatype=String, name="VM Guest IPs", description="The Guest IPs of this ESXi host. If the IP is not assigned, this will be an empty string. The VM must be turned on (and guest tools installed?) in order for ESXi to identify the 'primary'/'guest' IP address.")

    def run(self):
        child = None
        if self.esxi_client._child_hostname and self.esxi_client._child_username and self.esxi_client._child_password:
            for server in self.esxi_client._all_host_systems: #type:ignore
                if server.name == self.child_name:
                    child = server
                    break
        elif self.child_name == self.esxi_client.hostname:
            child = self.esxi_client._host_system
        
        if child is None:
            raise Exception(f'No ESXi server found with hostname/IP: {self.child_name}')
        vm_names = []
        power_state_booleans = []
        vm_guest_ips = []
        for vm in child.vm:
            vm_names.append(vm.name)
            power_state_booleans.append(True if str(vm.runtime.powerState).lower() == "poweredon" else False)
            vm_guest_ips.append(vm.guest.ipAddress if (vm.guest and vm.guest.ipAddress) else "")
        self.vm_names = vm_names
        self.vm_power_states = power_state_booleans
        self.vm_guest_ips = vm_guest_ips


class GetEsxiServerUtilizationAll(Node):
    name: str = "Get Specified ESXi Server Utilization"
    description: str = "Get all available information on memory (RAM) and CPU utilization for a specific ESXi server host. In vCenter, this should be a 'child' ESXi host and not the master 'parent' server. The username+password combinations for the login will be reused from the existing client object."
    categories: typing.List[str] = ["ESXi", "Client", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to retrieve from.")
    child_name = InputSocket(datatype=String, name="ESXi Server Hostname/IP", description="The hostname or IP of the server to retrieve the utilization from (child server in vCenter).")

    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use for memory (must be one of: B, KB, MB, GB, TB).", input_field="B")
    hz_unit = InputSocket(datatype=String, name="Hz Unit", description="The unit of measurement to use for CPU utilization (one of: Hz, KHz, MHz, GHz).", input_field="Hz")

    output_used_memory = OutputSocket(datatype=Number, name="Used Memory Amount", description="The currently used memory (RAM) of the ESXi server host disk in the provided unit.")
    output_total_memory = OutputSocket(datatype=Number, name="Total Memory Amount", description="The total (max) memory (RAM) of the ESXi server host in the provided unit.")
    result_percent_memory = OutputSocket(datatype=Number, name="Memory Usage Percent", description="The amount of RAM being utilized as a percent.")

    output_used_cpu = OutputSocket(datatype=Number, name="CPU Utilization", description="The current CPU utilization of this ESXi host server in the provided unit.")
    output_total_cpu = OutputSocket(datatype=Number, name="CPU Utilization Maximum", description="The max (total) CPU utilization of this ESXi host server in the provided unit.")
    result_percent_cpu = OutputSocket(datatype=Number, name="CPU Utilization Percent", description="The amount of CPU being utilized as a percent.")
    

    def run(self):
        child_client = None
        if self.esxi_client._child_hostname and self.esxi_client._child_username and self.esxi_client._child_password:
            for server in self.esxi_client._all_host_systems: #type:ignore
                if server.name == self.child_name:
                    child_client = esxi_utils.ESXiClient(self.esxi_client._vcenter_hostname, self.esxi_client.username, self.esxi_client.password, child_hostname=self.child_name, child_username=self.esxi_client._child_username, child_password=self.esxi_client._child_password)
                    break
        else:
            child_client = esxi_utils.ESXiClient(self.child_name, self.esxi_client.username, self.esxi_client.password)
        if child_client is None:
            raise Exception(f'No ESXi server found with hostname/IP: {self.child_name}')
        
        ## input validation
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        hz_unit_orders = ["Hz", "KHz", "MHz", "GHz"]
        # Capitalize all letters but the last one (force the last letter lowercase)
        used_unit_hz = self.hz_unit[:-1].upper() + self.hz_unit[len(self.hz_unit)-1].lower()
        if used_unit_hz not in hz_unit_orders:
            raise graphex_exceptions.InvalidParameterError(self.name, "Hz Unit", used_unit, hz_unit_orders)
        ##

        self.output_used_memory = child_client.current_memory_usage(unit=used_unit)
        self.output_total_memory = child_client.total_available_memory(unit=used_unit)
        self.result_percent_memory = child_client.memory_usage_percent()

        self.output_used_cpu = child_client.current_cpu_usage(unit=used_unit_hz)
        self.output_total_cpu = child_client.total_available_cpu_usage(unit=used_unit_hz)
        self.result_percent_cpu = child_client.cpu_usage_percent()
