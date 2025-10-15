import math
import os
import typing
import esxi_utils
import tempfile
from graphex import Boolean, InputSocket, ListInputSocket, ListOutputSocket, Node, Number, OptionalInputSocket, OutputSocket, String, DataContainer
from graphex import exceptions as graphex_exceptions
from graphex_esxi_utils import datatypes, esxi_constants


class EsxiVirtualMachineIsPoweredOn(Node):
    name: str = "ESXi Virtual Machine Is Powered On"
    description: str = "Outputs True if the Virtual Machine is Powered On"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Powered On", description="A Boolean value of True if the VM is powered on. The value is False if powered off."
    )

    def run(self):
        self.output = self.vm.powered_on


class EsxiVirtualMachineIsPoweredOff(Node):
    name: str = "ESXi Virtual Machine Is Powered Off"
    description: str = "Outputs True if the Virtual Machine is Powered Off"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Powered Off", description="A Boolean value of True if the VM is powered off. The value is False if powered on."
    )

    def run(self):
        self.output = self.vm.powered_off


class EsxiVirtualMachinePowerOn(Node):
    name: str = "ESXi Power On Virtual Machine"
    description: str = "Powers on the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    error_if_on = OptionalInputSocket(
        datatype=Boolean,
        name="Error if Already On?",
        description="When set to True: Will throw an exception (create an error) if the virtual machine is already powered on.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Powering on...")
        if self.error_if_on is not None and self.error_if_on:
            self.vm.power_on()
        else:
            self.vm.power_on(True)


class EsxiVirtualMachinePowerOff(Node):
    name: str = "ESXi Power Off Virtual Machine"
    description: str = "Powers off the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    error_if_off = OptionalInputSocket(
        datatype=Boolean,
        name="Error if Already Off?",
        description="When set to True: Will throw an exception (create an error) if the virtual machine is already powered off.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Powering off...")
        if self.error_if_off is not None and self.error_if_off:
            self.vm.power_off()
        else:
            self.vm.power_off(True)


class EsxiVirtualMachineGetDatastore(Node):
    name: str = "ESXi Get Datastore for VM"
    description: str = "Gets the datastore that the provided Virtual Machine is stored in."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=datatypes.Datastore, name="ESXi Datastore", description="The datastore where this VM lives.")

    def run(self):
        self.output = self.vm.datastore


class EsxiVirtualMachineGetId(Node):
    name: str = "ESXi Get VM ID"
    description: str = "Gets the ID for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=String, name="ID", description="The ID that represents this VM.")

    def run(self):
        self.output = self.vm.id


class EsxiVirtualMachineGetWorldId(Node):
    name: str = "ESXi Get VM World ID"
    description: str = "Gets the world (runtime (dynamic)) ID for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Number, name="World ID", description="The World ID that represents this VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.output = self.vm.get_world_id()
        self.debug(f"Found World ID: {self.output}")


class EsxiVirtualMachineGetGuestId(Node):
    name: str = "ESXi Get VM Guest ID"
    description: str = "Gets the guest ID for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=String, name="Guest ID", description="The Guest ID that represents this VM.")

    def run(self):
        self.output = self.vm.guestid


class EsxiVirtualMachineGetName(Node):
    name: str = "ESXi Get VM Name"
    description: str = "Gets the name for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=String, name="VM Name", description="The name for the provided VM.")

    def run(self):
        self.output = self.vm.name


class EsxiVirtualMachineGetUUID(Node):
    name: str = "ESXi Get VM UUID"
    description: str = "Gets the UUID for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=String, name="UUID", description="The UUID for the provided VM.")

    def run(self):
        self.output = self.vm.uuid


class EsxiVirtualMachineAmountOfCpus(Node):
    name: str = "ESXi VM vCPU Amount"
    description: str = "Outputs the number of vCPUs this Virtual Machine has."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Number, name="vCPU Amount", description="The number of vCPUs.")

    def run(self):
        self.output = self.vm.vcpus


class EsxiVirtualMachineAmountOfCpusPerSocket(Node):
    name: str = "ESXi VM vCPU Cores per Socket"
    description: str = "Outputs the number of vCPU cores this Virtual Machine has per socket."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Number, name="vCPU Cores per Socket", description="The number of vCPU cores per socket.")

    def run(self):
        self.output = self.vm.vcpu_cores_per_socket


class EsxiVirtualMachineAmountOfMemoryMB(Node):
    name: str = "ESXi VM Get Memory Amount (MB)"
    description: str = "Outputs the amount of memory (RAM) this Virtual Machine has (in Megabytes)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Number, name="Memory (MB)", description="The amount of memory this VM has.")

    def run(self):
        self.output = self.vm.memory


class GetAllVirtualDevices(Node):
    name: str = "Get All Virtual Devices from VM"
    description: str = "Gets a list of all the Virtual Devices connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual Devices", description="A list of all Virtual Devices objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual Devices...")
        self.output_devices = self.vm.devices.items
        self.debug(f"Virtual Devices: {str(self.output_devices)[1:-1]}")


class GetAllVirtualNICs(Node):
    name: str = "Get All Virtual NICs from VM"
    description: str = "Gets a list of all the Virtual NICs connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual NICs", description="A list of all Virtual NIC objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual NICs...")
        self.output_devices = self.vm.nics.items
        self.debug(f"Virtual NICs: {str(self.output_devices)[1:-1]}")


class GetAllVirtualDisks(Node):
    name: str = "Get All Virtual Disks from VM"
    description: str = "Gets a list of all the Virtual Disks connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual Disks", description="A list of all Virtual Disk objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual Disks...")
        self.output_devices = self.vm.disks.items
        self.debug(f"Virtual Disks: {str(self.output_devices)[1:-1]}")


class GetAllVirtualCdroms(Node):
    name: str = "Get All Virtual CD ROMs from VM"
    description: str = "Gets a list of all the Virtual CD ROMs connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual CD ROMs", description="A list of all Virtual CD ROM objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual CD-ROMs...")
        self.output_devices = self.vm.cdroms.items
        self.debug(f"Virtual CD-ROMs: {str(self.output_devices)[1:-1]}")


class GetAllVirtualFloppy(Node):
    name: str = "Get All Virtual Floppies from VM"
    description: str = "Gets a list of all the Virtual Floppies connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual Floppies", description="A list of all Virtual Floppy objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual Floppy Disks...")
        self.output_devices = self.vm.floppies.items
        self.debug(f"Virtual Floppy Disks: {str(self.output_devices)[1:-1]}")


class GetAllVirtualVideoCard(Node):
    name: str = "Get All Virtual Video Cards from VM"
    description: str = "Gets a list of all the Virtual Video Cards connected to the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_devices = ListOutputSocket(
        datatype=datatypes.VirtualDevice, name="Virtual Video Cards", description="A list of all Virtual Video Card objects connected to the VM."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting all Virtual Video Cards...")
        self.output_devices = self.vm.video_cards.items
        self.debug(f"Virtual Video Cards: {str(self.output_devices)[1:-1]}")


class EsxiVirtualMachineGetDatastoreFilePath(Node):
    name: str = "ESXi VM Get Filepath (as DatastoreFile)"
    description: str = "Gets the filepath to the VM's VMX file as a DatastoreFile object for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile object for the VM's VMX file.")

    def run(self):
        self.output = self.vm.filepath


class EsxiVirtualMachineFiles(Node):
    name: str = "ESXi VM Files"
    description: str = "Outputs a list of all files (including metadata) for the provided Virtual Machine's folder (stored in ESXi)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = ListOutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFiles", description="A DatastoreFile object for each file.")

    def run(self):
        self.output = self.vm.files


class EsxiVirtualMachineFolder(Node):
    name: str = "ESXi Get VM Folder"
    description: str = "Gets the folder as a DatastoreFile object for the provided Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="Folder", description="The DatastoreFile object for the VM's folder.")

    def run(self):
        self.output = self.vm.folder


class EsxiVirtualMachineUsedSpace(Node):
    name: str = "ESXi VM Used Space"
    description: str = "Outputs the amount of space used on disk used by this Virtual Machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    bytes_unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement. Must be one of: B, KB, MB, GB.", input_field="KB")
    output = OutputSocket(datatype=Number, name="Used Space", description="The amount of disk space consumed by this VM and its associated files.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        units = ["B", "KB", "MB", "GB"]
        used_unit = self.bytes_unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.debug(f"Calculating disk usage (in {used_unit})...")
        self.output = self.vm.used_space(used_unit)
        self.debug(f"Disk Usage: {self.output}{used_unit}")


class EsxiVirtualMachineSize(Node):
    name: str = "ESXi VM Size"
    description: str = "Get the total storage space occupied by the virtual machine across all datastores, that is not shared with any other virtual machine."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    bytes_unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement. Must be one of: B, KB, MB, GB.", input_field="KB")
    output = OutputSocket(datatype=Number, name="Size", description="Total storage space occupied by the virtual machine across all datastores.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        units = ["B", "KB", "MB", "GB"]
        used_unit = self.bytes_unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.debug(f"Calculating size of Virtual Machine (in {used_unit})...")
        self.output = self.vm.size(used_unit)
        self.debug(f"Size of Virtual Machine: {self.output}{used_unit}")


class EsxiVirtualMachineSetCpus(Node):
    name: str = "ESXi Set Number of vCPUs"
    description: str = "Sets the number of vCPUs to the provided value."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    input_value = InputSocket(datatype=Number, name="Number of vCPUs", description="The number of vCPUs to give to the VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting vCPUs to {int(self.input_value)}")
        self.vm.vcpus = int(self.input_value)


class EsxiVirtualMachineSetCoresPerSocket(Node):
    name: str = "ESXi Set Amount of CPU Cores per Socket"
    description: str = "Sets the number cores each vCPU should have per socket."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    input_value = InputSocket(datatype=Number, name="Cores per Socket", description="The number of cores each vCPU should have per socket on this VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting Cores-Per-Socket to {int(self.input_value)}")
        self.vm.vcpu_cores_per_socket = int(self.input_value)


class EsxiVirtualMachineSetMemoryMB(Node):
    name: str = "ESXi Set Memory Size (MB)"
    description: str = "Sets the amount of Memory (RAM) that this VM has."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    input_value = InputSocket(datatype=Number, name="Memory Size (MB)", description="The memory size to give to the VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting Memory to {int(self.input_value)}MB")
        self.vm.memory = int(self.input_value)


class EsxiVirtualMachineSetMemoryString(Node):
    name: str = "ESXi Set Memory Size from String"
    description: str = "Sets the amount of Memory (RAM) that this VM has via String. The string is expected to take the form <number><unit>, where <unit> is one of KB, MB, or GB (e.g. 8GB)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    input_value = InputSocket(
        datatype=String,
        name="Memory Size",
        description="The memory size to give to the VM. The string is expected to take the form <number><unit>, where <unit> is one of KB, MB, or GB (e.g. 8GB)",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting Memory to {self.input_value}")
        self.vm.memory = self.input_value


class EsxiVirtualMachineSetGuestId(Node):
    name: str = "ESXi Set Guest ID"
    description: str = (
        "Sets the name of this VM's guest ID/OS (See: https://developer.vmware.com/apis/358/vsphere/doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html)."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    input_value = InputSocket(datatype=String, name="New Guest ID", description="The new guest ID/OS name to give to this VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting Guest ID to {self.input_value}")
        self.vm.guestid = self.input_value


class EsxiVirtualMachineRename(Node):
    name: str = "ESXi Rename VM"
    description: str = "Renames the VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    new_name = InputSocket(datatype=String, name="New Name", description="The new name to give to the VM.")
    timeout = InputSocket(
        datatype=Number,
        name="Timeout",
        description="How long to wait for the rename to complete (in seconds) before throwing a RenameError exception.",
        input_field=30,
    )
    folder_name = OptionalInputSocket(
        datatype=String,
        name="Containing Folder",
        description="The folder to contain the VM. The default is the folder the VM was originally in. Will create a new folder if one is not found with a matching name. Will throw an esxi_utils 'MultipleFoldersFoundError' exception if more than one folder is found with the given name.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        folder_name = self.folder_name if self.folder_name else None
        if folder_name:
            self.log(f'Renaming Virtual Machine from "{self.vm.name}" to "{self.new_name}" (New Folder: {folder_name})...')
        else:
            self.log(f'Renaming Virtual Machine from "{self.vm.name}" to "{self.new_name}"...')
        self.vm.rename(self.new_name, folder_name=folder_name, timeout=self.timeout)


class EsxiVirtualMachineRemove(Node):
    name: str = "ESXi Remove (Delete) VM"
    description: str = "Removes the VM from ESXI by destroying/deleting it. This operation cannot be reversed."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to destroy.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Removing Virtual Machine...")
        self.vm.remove()


class EsxiVirtualMachineReset(Node):
    name: str = "ESXi Reset (Hard Reboot / Restart) VM"
    description: str = "Reboots the provided VM by 'hard' power cycling it."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Resetting (hard rebooting)...")
        self.vm.reset()


class EsxiVirtualMachineWait(Node):
    name: str = "ESXi Wait for VM Power State"
    description: str = "Waits for the VM to be either powered on or off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Power"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    powered_on = InputSocket(datatype=Boolean, name="Powered On?", description="When True: wait for power on. Else: wait for power off.", input_field=True)
    retries = InputSocket(
        datatype=Number,
        name="Retries",
        description="The number of retries. When exceeded the program continues as if the desired state was reached.",
        input_field=60,
    )
    retry_delay = InputSocket(datatype=Number, name="Retry Delay", description="How long in seconds to wait inbetween each retry.", input_field=2)

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        if self.powered_on:
            self.log(f"Waiting for VM to power on...")
        else:
            self.log(f"Waiting for VM to power off...")
        self.vm.wait(self.powered_on, int(self.retries), int(self.retry_delay))


class EsxiVirtualMachineReload(Node):
    name: str = "ESXi Reload VM"
    description: str = "Reloads the VM. This refreshes the VM to recognize any changes made to the local files (i.e. the VMX file)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f'Reloading Virtual Machine..."')
        self.vm.reload()


class EsxiVirtualMachineClone(Node):
    name: str = "ESXi Clone VM"
    description: str = "Clones the VM to a new VM. Snapshots will be preserved."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    new_name = InputSocket(datatype=String, name="New VM Name", description="The name to give to the cloned/new VM.")
    new_datastore = OptionalInputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to save the new VM to.")
    new_vm = OutputSocket(datatype=datatypes.VirtualMachine, name="New VM", description="The cloned/new VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        datastore_string = f' (DataStore "{self.new_datastore.name}")' if self.new_datastore else ""
        self.log(f'Cloning Virtual Machine to "{self.new_name}"{datastore_string}...')
        ds = self.new_datastore if self.new_datastore else None
        self.new_vm = self.vm.clone(self.new_name, datastore=ds)
        self.debug(f'Virtual Machine cloned to "{self.new_name}"{datastore_string}')


class EsxiVirtualMachineExport(Node):
    name: str = "ESXi Export VM"
    description: str = "Export this virtual machine to an OVF/OVA file. Note: The export progress shown on the ESXi UI may not reflect the actual progress."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_path = InputSocket(
        datatype=String,
        name="Export Path",
        description="The location on the server to export to. Default is the current directory (directory that this file was executed from).",
        input_field=".",
    )
    file_format = InputSocket(
        datatype=String, name="Format", description="The export format. Must be either 'ovf' or 'ova'. Defaults to 'ovf'.", input_field="ovf"
    )
    hash_type = InputSocket(
        datatype=String,
        name="Hash Type",
        description="Algorithm to use for generating manifest hashes. Must be one of: sha1, sha256, sha512. Defaults to 'sha1'",
        input_field="sha1",
    )
    include_image_files = InputSocket(
        datatype=Boolean, name="Include Image Files?", description="Whether to include the image files or not.", input_field=False
    )
    include_nvram = InputSocket(datatype=Boolean, name="Include nvram?", description="Whether to include the nvram file or not.", input_field=False)
    delete_existing_file = InputSocket(
        datatype=Boolean,
        name="Delete Existing File?",
        description="If a file already exists with the same path: should it be deleted? If set to False: will throw an exception if the file already exists.",
    )

    output = OutputSocket(datatype=datatypes.OvfFile, name="OVF File", description="An OVF File object for the exported VM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        formats = ["ovf", "ova"]
        hash_types = ["sha1", "sha256", "sha512"]
        used_format = self.file_format.lower()
        used_hash = self.hash_type.lower()
        if used_format not in formats:
            raise graphex_exceptions.InvalidParameterError(self.name, "Format", used_format, formats)
        if used_hash not in hash_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Hash Type", used_hash, hash_types)
        self.log(f"Exporting Virtual Machine to {self.output_path}")
        self.debug(
            f"Export of Virtual Machine started (Output Path={self.output_path}, File Format={self.file_format}, Hash Type={self.hash_type}, Include Image Files={self.include_image_files}, Include NVRAM={self.include_nvram})"
        )
        try:
            self.output = self.vm.export(
                path=self.output_path, format=used_format, hash_type=used_hash, include_image_files=self.include_image_files, include_nvram=self.include_nvram
            )
        except FileExistsError as fee:
            if not self.delete_existing_file:
                raise fee
            self.debug("Caught FileExistsError on export. Deleting existing file...")
            p = str(fee).split(" ")[0]
            if not os.path.exists(p):
                raise Exception(f"Cant find path: {str(p)} from exception: {str(fee)}")
            os.remove(p)
            self.output = self.vm.export(
                path=self.output_path, format=used_format, hash_type=used_hash, include_image_files=self.include_image_files, include_nvram=self.include_nvram
            )
        self.debug(f"Virtual Machine export to {self.output_path} complete.")


class EsxiVirtualMachineCaptureScreen(Node):
    name: str = "ESXi VM Capture Screen"
    description: str = "Capture a screenshot of the VM's screen."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Screen Capture"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    filepath = InputSocket(
        datatype=String,
        name="Filepath",
        description="Path to a file or directory where the screenshot should be captured. If a directory, the screenshot will be saved as `capture.png` in that directory.",
        input_field=".",
    )
    timeout = InputSocket(
        datatype=Number,
        name="Timeout",
        description="The maximum number of seconds to wait for the operation to complete before failing.",
        input_field=30.0,
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise a 'TimeoutError' error on failure. If False, the 'Success' boolean output will be populated instead.",
        input_field=True,
    )

    output = OutputSocket(
        datatype=String, name="Saved Path", description="The path to where the screenshot was saved. If the screenshot failed, this will be an empty string."
    )
    success = OutputSocket(
        datatype=Boolean,
        name="Success",
        description="Whether the screenshot was successfully captured. This is only applicable if 'Error on Failure?' is False (otherwise, a 'TimeoutError' will be raiesd).",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Saving screenshot of Virtual Machine to {self.filepath}")
        self.success = False
        self.output = ""
        error = None
        try:
            self.output = self.vm.screen_capture.capture_screen(self.filepath, self.timeout)
        except TimeoutError as e:
            error = e

        if error and self.error_on_failure:
            raise error

        if error:
            return

        self.success = True


class EsxiVirtualMachineExpectScreen(Node):
    name: str = "ESXi VM Expect Screen"
    description: str = "Wait until the virtual machine display (screen) matches a target image."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Screen Capture"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    filepath = InputSocket(datatype=String, name="Filepath", description="The image file to read and compare against")
    timeout = InputSocket(
        datatype=Number,
        name="Timeout",
        description="The maximum number of seconds to wait for the operation to complete before failing.",
        input_field=60.0,
    )
    match_score = InputSocket(
        datatype=Number,
        name="Match Score",
        description="The minimum score in range [0.0, 1.0] for images to be considered a match (higher is a closer match). A value of 1.0 indicates an exact match.",
        input_field=1.0,
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise a 'TimeoutError' error on failure. If False, the 'Success' boolean output will be populated instead.",
        input_field=True,
    )

    success = OutputSocket(
        datatype=Boolean,
        name="Success",
        description="Whether the expected image matched the virtual machine display before the 'Wait Time' completed. This is only applicable if 'Error on Failure?' is False (otherwise, a 'TimeoutError' will be raiesd).",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Waiting for screen match with image '{self.filepath}'...")
        self.success = False
        error = None
        try:
            self.vm.screen_capture.expect_screen(filename=self.filepath, timeout=int(self.timeout), match_score=self.match_score)
        except TimeoutError as e:
            error = e

        if error:
            self.log(f"Failed to match screen with image '{self.filepath}'")
            try:
                with tempfile.TemporaryDirectory() as tempdir:
                    path = self.vm.screen_capture.capture_screen(os.path.join(str(tempdir), "screenshot.png"))
                    self.log_image(base64_str=None, path_to_image=path)
            except Exception as e:
                self.log_warning(f"Failed to provide error screenshot due to error: {str(e)}")

            if self.error_on_failure:
                raise error
            return

        self.success = True
        self.log(f"Screen matches image '{self.filepath}'")


class EsxiVirtualMachinePressKey(Node):
    name: str = "ESXi VM Press Key"
    description: str = "Uses the ESXi API to simulate a key press on the remote VM. For non-alphanumeric keys, use 'Send USB Code' instead. The key is sent as if a user was writing over a UI. It is up to the user to ensure that the VM is in a state to properly receive the key press (i.e. the console is open if trying to write to a console)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Keyboard"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    key = InputSocket(datatype=String, name="Key", description="The key (as a string) to send through the ESXi API (e.g. 'a'). Note that case matters here.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Sending key: {self.key}")
        self.vm.usb.press_key(self.key)


class EsxiVirtualMachinePressCode(Node):
    name: str = "ESXi VM Send USB Code"
    description: str = "Uses the ESXi API to simulate a key press on the remote VM. This function expects a HEX value (e.g. '0x04' for 'a'). Use 'Press Key' if you would like the HEX values converted for you. The key is sent as if a user was writing over a UI. It is up to the user to ensure that the VM is in a state to properly receive the key press (i.e. the console is open if trying to write to a console)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Keyboard"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    key = InputSocket(datatype=String, name="Hex Keycode", description="The key to send through the ESXi API (as a hexidecimal string).")
    modifiers = ListInputSocket(
        datatype=String,
        name="Modifiers",
        description="A list of strings containing the names of the keys you wish to apply to another keypress. Valid options are: leftAlt, leftControl, leftGui, leftShift, rightAlt, rightControl, rightGui, and rightShift",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        allowed_modifiers = ["leftalt", "leftcontrol", "leftgui", "leftshift", "rightalt", "rightcontrol", "rightgui", "rightshift"]
        for used_modifier in self.modifiers:
            if used_modifier.lower() not in allowed_modifiers:
                raise graphex_exceptions.InvalidParameterError(self.name, "Modifiers", used_modifier, allowed_modifiers)
        self.debug(f"Sending hex key code: {self.key}")
        self.vm.usb.send_usb_code(self.key, self.modifiers)


class EsxiVirtualMachineWriteKeys(Node):
    name: str = "ESXi VM Keyboard Write"
    description: str = "Uses the ESXi API to simulate writing text on the remote VM. The key is sent as if a user was writing over a UI. It is up to the user to ensure that the VM is in a state to properly receive the key press (i.e. the console is open if trying to write to a console)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Keyboard"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    text = InputSocket(datatype=String, name="Text", description="The text to write through USB scan codes.")
    enter_boolean = InputSocket(
        datatype=Boolean, name="Enter?", description="When True: sends the code for the 'ENTER' key after writing the text to the VM.", input_field=False
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Writing text: {self.text}")
        self.vm.usb.write(self.text, self.enter_boolean)


class EsxiVirtualMachineGetScanCode(Node):
    name: str = "ESXi VM Get USB Scan Code"
    description: str = "Finds the scan code for the provided key_name (if one is known) using a table internal to the application. Throws a UsbScanCodeError exception if no key is found with that name."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Keyboard"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    key_name = InputSocket(datatype=String, name="Key Name", description="The name of the key to search for (e.g. 'A'). The case does not matter here.")
    output = OutputSocket(datatype=String, name="Hex Keycode", description="The USB Scan code as a HEX string")

    def run(self):
        self.output = self.vm.usb.get_usb_scan_code(self.key_name.upper())


class EsxiVirtualMachineGetKeyName(Node):
    name: str = "ESXi VM Get Key Name by USB Scan Code"
    description: str = "Finds the name for the provided scan code (if one is known). If the keycode represents a letter: the letter will be uppercase. Throws a UsbScanCodeError exception if no name is found with that code."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Keyboard"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    keycode = InputSocket(datatype=String, name="Hex Keycode", description="The name of the USB scan code to search for (as a hexidecimal string)")
    output = OutputSocket(
        datatype=String,
        name="Key Name",
        description="The name of the key with that scan code (e.g. 'a'). Different letter cases coorespond to different codes.",
    )

    def run(self):
        self.output = self.vm.usb.get_key_name_by_scan_code(self.keycode)


class EsxiVirtualMachineCreateSnapshot(Node):
    name: str = "ESXi VM Create Snapshot"
    description: str = "Creates a snapshot of this VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    snapshot_name = InputSocket(
        datatype=String, name="Name", description="The name to give to the screenshot. It is recommended to make each name unique for easier retrieval later."
    )
    snapshot_description = InputSocket(datatype=String, name="Description", description="A brief description of this snapshot.", input_field="")
    include_memory = InputSocket(
        datatype=Boolean,
        name="Include Memory?",
        description="If `True`, a dump of the internal state of the virtual machine (basically a memory dump) is included in the snapshot. Memory snapshots consume time and resources, and thus take longer to create. When `False`, the power state of the snapshot is set to powered off.",
        input_field=False,
    )
    quiesce = InputSocket(
        datatype=Boolean,
        name="Quiesce?",
        description="If `True` and the virtual machine is powered on when the snapshot is taken, VMware Tools is used to quiesce the file system in the virtual machine. This assures that a disk snapshot represents a consistent state of the guest file systems. If the virtual machine is powered off or VMware Tools are not available, the quiesce flag is ignored.",
        input_field=False,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f'Creating snapshot "{self.snapshot_name}"...')
        self.vm.snapshots.create(self.snapshot_name, self.snapshot_description, self.include_memory, self.quiesce)
        self.debug(
            f'Snapshot "{self.snapshot_name}" created (Include Memory={self.include_memory}, Quiesce={self.quiesce}, Description={self.snapshot_description})'
        )


class EsxiVirtualMachineHasSnapshot(Node):
    name: str = "ESXi VM Has Snapshot"
    description: str = "Outputs True if the VM has any snapshots (Snapshot exists). False otherwise."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Boolean, name="Has Snapshot?", description="Outputs True if the VM has any snapshots. False otherwise.")

    def run(self):
        self.output = self.vm.snapshots.exists


class EsxiVirtualMachineRemoveSnapshot(Node):
    name: str = "ESXi VM Remove Snapshot"
    description: str = "Attempts to get the provided snapshot name and remove that snapshot. Will raise a SnapshotNotFoundError if the snapshot doesn't exist or a MultipleSnapshotsFoundError if the provided name or id appears twice in the history."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    name_or_id = InputSocket(datatype=String, name="Snapshot Name or ID", description="The name or ID of the snapshot to revert to.")
    remove_children = InputSocket(
        datatype=Boolean,
        name="Remove Children?",
        description="If set to True, all child snapshots of the removed snapshot will also be removed.",
        input_field=False,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        noi = self.name_or_id
        try:
            noi = int(noi)
        except Exception:
            pass
        noi_string = f'"{noi}"' if isinstance(noi, str) else f"ID={noi}"
        self.log(f"Removing snapshot {noi_string}")
        snapshot = self.vm.snapshots.get(noi)

        snapshot_name = snapshot.name
        snapshot_id = snapshot.id
        snapshot.remove(remove_children=self.remove_children)
        self.debug(f'Successfully removed snapshot with name "{snapshot_name}" (ID {snapshot_id})')


class EsxiVirtualMachineDeleteAllSnapshots(Node):
    name: str = "ESXi VM Remove All Snapshots"
    description: str = "Removes (deletes) all snapshots for the provided VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Removing all snapshots...")
        self.vm.snapshots.remove_all()


class EsxiVirtualMachineRevertToSnapshot(Node):
    name: str = "ESXi VM Revert to Snapshot"
    description: str = "Attempts to get the provided snapshot name and reverts the VM to the state of that snapshot. Will raise a SnapshotNotFoundError if the snapshot doesn't exist or a MultipleSnapshotsFoundError if the provided name or id appears twice in the history."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    name_or_id = InputSocket(datatype=String, name="Snapshot Name or ID", description="The name or ID of the snapshot to revert to.")
    suppress_power_on = InputSocket(
        datatype=Boolean,
        name="Suppress Power On?",
        description="If set to true, the virtual machine will not be powered on regardless of the power state when the snapshot was created.",
        input_field=False,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        noi = self.name_or_id
        try:
            noi = int(noi)
        except Exception:
            pass
        noi_string = f'"{noi}"' if isinstance(noi, str) else f"ID={noi}"
        self.log(f"Reverting to snapshot {noi_string}")
        snapshot = self.vm.snapshots.get(noi)
        snapshot.revert()
        self.debug(f'Successfully reverted to snapshot with name "{snapshot.name}" (ID {snapshot.id})')


class EsxiVirtualMachineCurrentSnapshotInfo(Node):
    name: str = "ESXi VM Current Snapshot Information"
    description: str = "Outputs information about the most recent (current) snapshot. Output fields are: ID, name, description, creation time, creation power state, and whether the snapshot was provided the quiesced flag or not."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    # inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    # outputs
    output_id = OutputSocket(datatype=Number, name="ID", description="The ID of the snapshot.")
    output_name = OutputSocket(datatype=String, name="Name", description="The name of the snapshot.")
    output_description = OutputSocket(datatype=String, name="Description", description="The description of the snapshot.")
    output_creation_time = OutputSocket(datatype=String, name="Creation Time", description="The time the snapshot was created.")
    output_creation_state = OutputSocket(datatype=String, name="Creation Power State", description="The power state of the VM when this snapshot was created")
    output_q = OutputSocket(
        datatype=Boolean,
        name="Quiesced?",
        description="Flag to indicate whether or not the snapshot was created with the 'quiesce' option, ensuring a consistent state of the file system.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Querying current snapshot...")
        current_snapshot = self.vm.snapshots.current
        assert current_snapshot, "No snapshots available"
        self.output_id = current_snapshot.id
        self.output_name = current_snapshot.name
        self.output_description = current_snapshot.description
        self.output_creation_time = str(current_snapshot.createtime)
        self.output_creation_state = current_snapshot.state
        self.output_q = current_snapshot.quiesced
        self.debug(
            f"Current snapshot: ID={self.output_id}, Name={self.output_name}, Creation Time={self.output_creation_time}, State={self.output_creation_state}, Quiesced={self.output_q}, Description={self.output_description}"
        )


class EsxiVirtualMachineGetSnapshotInfo(Node):
    name: str = "ESXi VM Get Snapshot Information"
    description: str = "Outputs information about the provided snapshot. Output fields are: ID, name, description, creation time, creation power state, and whether the snapshot was provided the quiesced flag or not."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    # inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    name_or_id = InputSocket(datatype=String, name="Snapshot Name or ID", description="The name or ID of the snapshot.")
    # outputs
    output_id = OutputSocket(datatype=Number, name="ID", description="The ID of the snapshot.")
    output_name = OutputSocket(datatype=String, name="Name", description="The name of the snapshot.")
    output_description = OutputSocket(datatype=String, name="Description", description="The description of the snapshot.")
    output_creation_time = OutputSocket(datatype=String, name="Creation Time", description="The time the snapshot was created.")
    output_creation_state = OutputSocket(datatype=String, name="Creation Power State", description="The power state of the VM when this snapshot was created")
    output_q = OutputSocket(
        datatype=Boolean,
        name="Quiesced?",
        description="Flag to indicate whether or not the snapshot was created with the 'quiesce' option, ensuring a consistent state of the file system.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        noi = self.name_or_id
        try:
            noi = int(noi)
        except Exception:
            pass
        noi_string = f'"{noi}"' if isinstance(noi, str) else f"ID={noi}"
        self.log(f"Querying snapshot {noi_string}...")
        current_snapshot = self.vm.snapshots.get(noi)
        self.output_id = current_snapshot.id
        self.output_name = current_snapshot.name
        self.output_description = current_snapshot.description
        self.output_creation_time = str(current_snapshot.createtime)
        self.output_creation_state = current_snapshot.state
        self.output_q = current_snapshot.quiesced
        self.debug(
            f"Snapshot Information: ID={self.output_id}, Name={self.output_name}, Creation Time={self.output_creation_time}, State={self.output_creation_state}, Quiesced={self.output_q}, Description={self.output_description}"
        )


class EsxiVirtualMachineSnapshotList(Node):
    name: str = "ESXi VM List All Snapshots"
    description: str = (
        "Outputs two lists: one containing the names of all snapshots taken (as Strings) and the other containing all the IDs of the snapshots (as Numbers)"
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Snapshots"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output_names = ListOutputSocket(datatype=String, name="Snapshot Names", description="The names of all taken snapshots.")
    output_ids = ListOutputSocket(datatype=Number, name="Snapshot IDs", description="The ID of all taken snapshots")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Querying snapshots...")
        names: typing.List[str] = []
        ids: typing.List[int] = []
        root = self.vm.snapshots.root
        snapshots = root.flattened if root else []
        for snapshot in snapshots:
            names.append(snapshot.name)
            ids.append(snapshot.id)
        self.output_names = names
        self.output_ids = ids
        if len(names):
            self.debug(f"Snapshots: {str(names)[1:-1]}")
        else:
            self.debug(f"No snapshots available.")


class EsxiVmExists(Node):
    name: str = "ESXi VM Exists"
    description: str = "Outputs True if the queried Virtual Machine name exists."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="VM Name", description="The name of the VM to search for.")
    exists = OutputSocket(Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.vms.exists(self.name_value)


class EsxiVmNames(Node):
    name: str = "ESXi VM Names"
    description: str = "Outputs the name of every Virtual Machine on this client"
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    the_names = ListOutputSocket(datatype=String, name="Names", description="The names of of every VM on this client")

    def run(self):
        self.the_names = self.esxi_client.vms.names


class EsxiVmCreate(Node):
    name: str = "ESXi Create VM"
    description: str = "Create a pre-configured VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    vm_name = InputSocket(datatype=String, name="Name", description="The name of the new VM")
    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The datastore where the VM should be created.")
    vcpus = InputSocket(
        datatype=Number, name="vCPUs", description="The number of vCPUs to assign to this VM. Must be greater than or equal to 1.", input_field=1
    )
    memory = InputSocket(
        datatype=String,
        name="Memory",
        description="A string representing the amount of memory to assign to this VM. The string is expected to take the form <number><unit>, where <unit> is one of KB, MB, or GB (e.g. 8GB).",
        input_field="1GB",
    )
    guestid = InputSocket(
        datatype=String,
        name="Guest ID",
        description="Short guest operating system identifier (See: https://developer.vmware.com/apis/358/vsphere/doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html)",
        input_field="otherGuest",
    )
    version = OptionalInputSocket(
        datatype=String,
        name="Version",
        description="The version string for this virtual machine (e.g. ``vmx-10``). The default version for the ESXi host will be used otherwise.",
    )
    folder_name = OptionalInputSocket(
        datatype=String,
        name="Folder Name",
        description="The folder to contain the new VM. The default is the 'root' VMs folder. Will create a new folder if one is not found with a matching name. Will throw an esxi_utils 'MultipleFoldersFoundError' exception if more than one folder is found with the given name.",
    )

    # video card options
    video_auto_connect = OptionalInputSocket(
        datatype=Boolean, name="Auto Detect Video Settings", description="When 'True' sets the video card to 'Auto Detect' video settings. When 'False' (or unset) sets the video card to 'Specify Custom Settings'."
    )
    # video_mem_kb = OptionalInputSocket(
    #     datatype=Number, name="Video Memory Size KB", description="The size of virtual memory to assign to the video card in KiloBytes (default is 4MB (4096KB)). Do not give a value to this socket if you want to use 'Auto Detect Video Settings' instead."
    # )

    # BIOS or UEFI boot firmware
    use_uefi = OptionalInputSocket(
        datatype=Boolean, name="Use UEFI Firmware", description="When 'True' sets boot firmware to UEFI. When 'False' (or unset) sets the boot firmware to legacy BIOS mode."
    )

    output = OutputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="A `VirtualMachine` object for the new VM.")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        self.log(
            f'Creating Virtual Machine "{self.vm_name}" on DataStore "{self.datastore.name}" (vCPUs={self.vcpus}, Memory={self.memory}, GuestID={self.guestid}, Version={self.version})...'
        )
        version = self.version if self.version else None
        folder_name = self.folder_name if self.folder_name else None
        video_card_auto_detect = self.video_auto_connect if self.video_auto_connect else None
        uefi_boot = self.use_uefi if self.use_uefi else None
        # video_card_mem_kb = self.video_mem_kb if self.video_mem_kb else None
        self.output = self.esxi_client.vms.create(
            name=self.vm_name,
            datastore=self.datastore,
            vcpus=int(self.vcpus),
            memory=self.memory,
            guestid=self.guestid,
            version=version,
            folder_name=folder_name,
            video_card_auto_detect=video_card_auto_detect,
            uefi_boot=uefi_boot
        )
        self.debug(f'Created Virtual Machine "{self.vm_name}".')


class EsxiOsIsWindows(Node):
    name: str = "ESXi VM Operating System Is Windows"
    description: str = "Outputs True if the Virtual Machine is running Windows OS."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Windows?", description="A Boolean value of True if the VM is running Windows Operating System. The value is False otherwise."
    )

    def run(self):
        self.output = self.vm.ostype == esxi_utils.vm.OSType.Windows


class EsxiOsIsLinux(Node):
    name: str = "ESXi VM Operating System Is Linux"
    description: str = "Outputs True if the Virtual Machine is running Linux OS."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Linux?", description="A Boolean value of True if the VM is running Linux Operating System. The value is False otherwise."
    )

    def run(self):
        self.output = self.vm.ostype == esxi_utils.vm.OSType.Linux


class EsxiOsIsCisco(Node):
    name: str = "ESXi VM Operating System Is Cisco"
    description: str = "Outputs True if the Virtual Machine is running Cisco OS."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Cisco?", description="A Boolean value of True if the VM is running Cisco Operating System. The value is False otherwise."
    )

    def run(self):
        self.output = self.vm.ostype == esxi_utils.vm.OSType.Cisco


class EsxiOsIsPanos(Node):
    name: str = "ESXi VM Operating System Is PanOS"
    description: str = "Outputs True if the Virtual Machine is running PanOS (Palo Alto Firewall) OS."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Panos?", description="A Boolean value of True if the VM is running PanOS Operating System. The value is False otherwise."
    )

    def run(self):
        self.output = self.vm.ostype == esxi_utils.vm.OSType.PanOs


class EsxiOsIsUnknown(Node):
    name: str = "ESXi VM Operating System Is Unknown"
    description: str = "Outputs True if the Virtual Machine is running an Unknown OS."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(
        datatype=Boolean,
        name="Is Unknown?",
        description="A Boolean value of True if the VM is running an Unknown Operating System. The value is False otherwise.",
    )

    def run(self):
        self.output = self.vm.ostype == esxi_utils.vm.OSType.Unknown


class EsxiOsString(Node):
    name: str = "ESXi VM Operating System as String"
    description: str = "Outputs a String representing the type of Operating System this VM is running."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=String, name="OS Type", description="A String representing the type of Operating System this VM is running.")

    def run(self):
        self.output = str(self.vm.ostype)


class EsxiOsDetect(Node):
    name: str = "ESXi VM Guest ID String to OS Type String"
    description: str = "Attempt to detect the type of Operating System from the provided guest ID string."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "OS Type"]
    color: str = esxi_constants.COLOR_VM

    guest_id = InputSocket(datatype=String, name="Guest ID", description="The Guest ID you are attempting to figure out the operating system type for.")
    output = OutputSocket(datatype=String, name="OS Type", description="A String representing the type of Operating System this VM is running.")

    def run(self):
        self.output = str(esxi_utils.vm.OSType.detect(self.guest_id))


class EsxiVmUploadPath(Node):
    name: str = "ESXi Upload VM from Path"
    description: str = "Uploads a local OVF or OVA file to the provided datastore as a new VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")

    file_path = InputSocket(datatype=String, name="File Path", description="A path to a .ovf/.ova file (string)")
    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The datastore where the VM should be created.")
    upload_name = OptionalInputSocket(
        datatype=String, name="Name", description="The name of the new VM. If not provided, the name is based on the name defined in the OVF/OVA."
    )
    folder_name = OptionalInputSocket(
        datatype=String,
        name="Folder Name",
        description="The folder to contain the new VM. The default is the 'root' VMs folder. Will create a new folder if one is not found with a matching name. Will throw an esxi_utils 'MultipleFoldersFoundError' exception if more than one folder is found with the given name.",
    )
    network_map = OptionalInputSocket(
        datatype=DataContainer,
        name="Network Mappings",
        description="A Data Container of network mappings. This should be 'key: value' pairs mapping the old network name (in the OVF) to the new network name (on the server).",
    )

    output = OutputSocket(datatypes.VirtualMachine, name="VirtualMachine", description="A `VirtualMachine` object for the new VM.")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        ovf = esxi_utils.file.OvfFile(path=self.file_path)
        upload_name = self.upload_name if self.upload_name else ovf.vmname
        folder_name = self.folder_name if self.folder_name else None
        network_map = self.network_map if self.network_map else None
        folder_string = f" (Folder: {folder_name})" if folder_name else ""

        assert isinstance(network_map, dict) or network_map is None, "Network Mappings must be a dictionary."

        self.log(f"Uploading {self.file_path} as Virtual Machine {upload_name} to Datastore {self.datastore.name}{folder_string}...")
        if network_map:
            self.debug(f"Mapping networks for {self.file_path} using network map: {network_map}")

        try:
            self.output = self.esxi_client.vms.upload(
                file=self.file_path, datastore=self.datastore, name=upload_name, folder_name=folder_name, network_mappings=network_map
            )
        except Exception as e:
            self.logger.add_azure_build_tag('ovf-or-ova-failed-to-upload')
            raise e

        disk_strings = [str(math.ceil(disk.size / (1024 * 1024))) + "GB" for disk in self.output.disks]
        network_strings = [nic.network for nic in self.output.nics]
        self.debug(
            f"Created Virtual Machine {self.output.name} from file {self.file_path} (vCPUs={self.output.vcpus}, Memory={self.output.memory}MB, GuestID={self.output.guestid}, Disks={disk_strings}, Networks={network_strings})."
        )


class EsxiVmUploadOvfFile(Node):
    name: str = "ESXi Upload VM from OVF File"
    description: str = "Uploads a local OVF or OVA file to the provided datastore as a new VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")

    ovf_file = InputSocket(datatype=datatypes.OvfFile, name="OVF File", description="An `OvfFile` object.")
    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The datastore where the VM should be created.")
    upload_name = OptionalInputSocket(
        datatype=String, name="Name", description="The name of the new VM. If not provided, the name is based on the name defined in the OVF/OVA."
    )
    folder_name = OptionalInputSocket(
        datatype=String,
        name="Folder Name",
        description="The folder to contain the new VM. The default is the 'root' VMs folder. Will create a new folder if one is not found with a matching name. Will throw an esxi_utils 'MultipleFoldersFoundError' exception if more than one folder is found with the given name.",
    )
    network_map = OptionalInputSocket(
        datatype=DataContainer,
        name="Network Mappings",
        description="A Data Container of network mappings. This should be 'key: value' pairs mapping the old network name (in the OVF) to the new network name (on the server).",
    )

    output = OutputSocket(datatypes.VirtualMachine, name="VirtualMachine", description="A `VirtualMachine` object for the new VM.")

    def log_prefix(self):
        return f"[{self.name} - Host {self.esxi_client.hostname}] "

    def run(self):
        upload_name = self.upload_name if self.upload_name else None
        folder_name = self.folder_name if self.folder_name else None
        network_map = self.network_map if self.network_map else None
        folder_string = f" (Folder: {folder_name})" if folder_name else ""

        assert isinstance(network_map, dict) or network_map is None, "Network Mappings must be a dictionary."

        self.log(f"Uploading {self.ovf_file.path} as Virtual Machine {upload_name} to Datastore {self.datastore.name}{folder_string}...")
        if network_map:
            self.debug(f"Mapping networks for {self.ovf_file.path} using network map: {network_map}")

        try:
            self.output = self.esxi_client.vms.upload(
                file=self.ovf_file, datastore=self.datastore, name=upload_name, folder_name=folder_name, network_mappings=network_map
            )
        except Exception as e:
            self.logger.add_azure_build_tag('ovf-or-ova-failed-to-upload')
            raise e

        disk_strings = [str(math.ceil(disk.size / (1024 * 1024))) + "GB" for disk in self.output.disks]
        network_strings = [nic.network for nic in self.output.nics]
        self.debug(
            f"Created Virtual Machine {self.output.name} from file {self.ovf_file.path} (vCPUs={self.output.vcpus}, Memory={self.output.memory}MB, GuestID={self.output.guestid}, Disks={disk_strings}, Networks={network_strings})."
        )

# ESXi doesn't currently control this at the hardware level for the booted VM
# You will have to do this the hard way
# class EsxiVirtualMachineSetBootDisk(Node):
#     name: str = "ESXi VM Set Boot Disk"
#     description: str = "Sets the provided disk as the disk to boot when the VM powers on."
#     categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware"]
#     color: str = esxi_constants.COLOR_VM

#     vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
#     boot_disk = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Disk", description="The virtual disk to set as the first one to boot from on the VM.")

#     def log_prefix(self):
#         return f"[{self.name} - {self.vm.name}] "

#     def run(self):
#         disk_label = self.boot_disk.label
#         self.log(f"Setting '{disk_label}' as the first disk to boot...")
#         self.vm.set_boot_disk(disk_label)


class EsxiVirtualMachineEnforceBIOSmenu(Node):
    name: str = "ESXi VM Enforce BIOS Setup"
    description: str = "Forces the VM to enter the BIOS boot menu on the next boot of the VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    enforce = InputSocket(datatype=Boolean, name="Enforce", description="Whether to turn this setting on or not.", input_field=True)

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Setting enforce BIOS boot menu to '{self.enforce}'...")
        self.vm.force_bios_menu(self.enforce)
