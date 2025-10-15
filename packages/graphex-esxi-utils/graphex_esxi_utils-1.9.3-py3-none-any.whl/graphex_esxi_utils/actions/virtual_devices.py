from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, ListOutputSocket, OptionalInputSocket, EnumInputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex import exceptions as graphex_exceptions
import esxi_utils
import typing


class EsxiVirtualDeviceGetKey(Node):
    name: str = "ESXi VirtualDevice Get Key"
    description: str = "A unique key that distinguishes this device from other devices in the same virtual machine. Keys are immutable but may be recycled; that is, a key does not change as long as the device is associated with a particular virtual machine. However, once a device is removed, its key may be used when another device is added. "
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(
        datatype=Number, name="Key", description="A unique key that distinguishes this device from other devices in the same virtual machine."
    )

    def run(self):
        self.output = self.vd.key


class EsxiVirtualDeviceGetLabel(Node):
    name: str = "ESXi VirtualDevice Get Label"
    description: str = "Get the device's label."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(datatype=String, name="Label", description="The device's label.")

    def run(self):
        self.output = self.vd.label


class EsxiVirtualDeviceConnectable(Node):
    name: str = "ESXi VirtualDevice is Connectable"
    description: str = "Whether or not this device is connectable. Certain functions will fail if a device is not connectable."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Connectable?", description="Whether or not this device is connectable.")

    def run(self):
        self.output = self.vd.connectable


class EsxiVirtualDeviceStartConnected(Node):
    name: str = "ESXi VirtualDevice will Start Connected"
    description: str = "Whether or not this device is set to start connected."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Start Connected?", description="Whether or not this device is set to start connected.")

    def run(self):
        self.output = self.vd.start_connected


class EsxiVirtualDeviceIsConnected(Node):
    name: str = "ESXi VirtualDevice is Connected"
    description: str = "Whether or not this device is connected."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Connected?", description="Whether or not this device is connected.")

    def run(self):
        self.output = self.vd.connected


class EsxiVirtualDeviceSetStartConnected(Node):
    name: str = "ESXi VirtualDevice Set Start Connected"
    description: str = "Set whether or not this device should start connected."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    input_value = InputSocket(datatype=Boolean, name="Start Connected?", description="Whether or not this device should start connected.")

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.debug(f"Setting 'Start Connected' to {str(self.input_value)}")
        self.vd.start_connected = self.input_value


class EsxiVirtualDeviceSetConnected(Node):
    name: str = "ESXi VirtualDevice Set Connected"
    description: str = "Connect or disconnect this device (set connection status)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    input_value = InputSocket(datatype=Boolean, name="Connected?", description="Set True to Connect or False to disconnect this device.")

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.debug(f"Setting 'Connected' to {str(self.input_value)}")
        self.vd.connected = self.input_value


class EsxiVirtualDeviceRemove(Node):
    name: str = "ESXi Remove VirtualDevice"
    description: str = "Remove this device. If removing a 'Disk', will delete the file from the datastore as well. If you want to retain the datastore file: see the action node 'ESXi Remove Disk VirtualDevice'."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.log(f"Removing Virtual Device...")
        self.vd.remove()


class EsxiVirtualDeviceFindType(Node):
    name: str = "ESXi VirtualDevice Find Device by Type String"
    description: str = "Find devices by their type. The type can be provided as its real value (e.g. 'VirtualDisk') or as its shorthand (e.g. 'disk')"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    dtype = InputSocket(
        datatype=String,
        name="Type",
        description="The type string to search for. The type can be provided as its real value (e.g. 'VirtualDisk') or as its shorthand (e.g. 'disk'",
    )

    output = ListOutputSocket(
        datatype=datatypes.VirtualDevice,
        name="Matching VirtualDevices",
        description="List of `VirtualDevice` objects for each device matching the provided type.",
    )

    def run(self):
        self.output = self.vm.devices.find_type(self.dtype)


class EsxiVirtualDeviceIsCd(Node):
    name: str = "ESXi VirtualDevice is CD ROM"
    description: str = "Outputs True if the Virtual Device is a CD ROM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "CD ROM"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is CD ROM?", description="A Boolean value of True if the Virtual Device is a CD ROM. The value is False otherwise."
    )

    def run(self):
        self.output = isinstance(self.vd, esxi_utils.vm.hardware.VirtualCdrom)


class EsxiVirtualDeviceIsDisk(Node):
    name: str = "ESXi VirtualDevice is Disk"
    description: str = "Outputs True if the Virtual Device is a Disk."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Disk?", description="A Boolean value of True if the Virtual Device is a Disk. The value is False otherwise."
    )

    def run(self):
        self.output = isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk)


class EsxiVirtualDeviceIsFloppy(Node):
    name: str = "ESXi VirtualDevice is Floppy"
    description: str = "Outputs True if the Virtual Device is a Floppy."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Floppy"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Floppy?", description="A Boolean value of True if the Virtual Device is a Floppy. The value is False otherwise."
    )

    def run(self):
        self.output = isinstance(self.vd, esxi_utils.vm.hardware.VirtualFloppy)


class EsxiVirtualDeviceIsNic(Node):
    name: str = "ESXi VirtualDevice is NIC"
    description: str = "Outputs True if the Virtual Device is a NIC."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Is NIC?", description="A Boolean value of True if the Virtual Device is a NIC. The value is False otherwise.")

    def run(self):
        self.output = isinstance(self.vd, esxi_utils.vm.hardware.VirtualNIC)


class EsxiVirtualDeviceIsVideoCard(Node):
    name: str = "ESXi VirtualDevice is Video Card"
    description: str = "Outputs True if the Virtual Device is a Video Card."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_DEVICE

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Virtual Device", description="The Virtual Device to use.")
    output = OutputSocket(
        datatype=Boolean, name="Is Video Card?", description="A Boolean value of True if the Virtual Device is a Video Card. The value is False otherwise."
    )

    def run(self):
        self.output = isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard)


class EsxiVirtualDeviceCDfile(Node):
    name: str = "ESXi CD-ROM VirtualDevice Get File"
    description: str = "Gets the file attached to this CD-ROM as a `DatastoreFile` object. Will raise a 'EsxiObjectDoesNotExistError' if there is no DatastoreFile assigned to the CD-ROM. Check ahead of time with 'Esxi CD-ROM VirtualDevice has File'"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "CD ROM"]
    color: str = esxi_constants.COLOR_VIRT_CD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="CD-ROM Virtual Device", description="The CD-ROM Virtual Device to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The file attached to this CD-ROM as a `DatastoreFile` object.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualCdrom), "Not a VirtualCdrom"
        result = self.vd.file
        if result is None:
            raise exceptions.EsxiObjectDoesNotExistError(f'CD-ROM VirtualDevice: "{self.vd.label}" ... Doesn\'t have a "DatastoreFile" object!')
        self.output = self.vd.file


class EsxiVirtualDeviceCDhasFile(Node):
    name: str = "ESXi CD-ROM VirtualDevice has File"
    description: str = "Checks if this CD-ROM has a `DatastoreFile` object associated with it."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "CD ROM"]
    color: str = esxi_constants.COLOR_VIRT_CD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="CD-ROM Virtual Device", description="The CD-ROM Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Has DatastoreFile?", description="Whether or not this CD-ROM has a `DatastoreFile` object.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualCdrom), "Not a VirtualCdrom"
        self.output = False if self.vd.file is None else True


class EsxiVirtualDeviceCDfileSetter(Node):
    name: str = "ESXi CD-ROM VirtualDevice Set File"
    description: str = (
        "Set the file for this CD-ROM. Provide a `DatastoreFile` object for a file in the datastore to add to the CD-ROM, or 'Nothing' to empty the CD-ROM."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "CD ROM"]
    color: str = esxi_constants.COLOR_VIRT_CD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="CD-ROM Virtual Device", description="The CD-ROM Virtual Device to use.")
    cd_input = OptionalInputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A `DatastoreFile` object for a file in the datastore to add to the CD-ROM"
    )

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        if self.cd_input:
            self.log(f"Setting CD-ROM File to {self.cd_input.path}")
        else:
            self.log(f"Removing file from CD-ROM.")
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualCdrom), "Not a VirtualCdrom"
        self.vd.file = self.cd_input if self.cd_input else None


class EsxiVirtualDeviceFloppyhasFile(Node):
    name: str = "ESXi Floppy VirtualDevice has File"
    description: str = "Checks if this Floppy has a `DatastoreFile` object associated with it."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Floppy"]
    color: str = esxi_constants.COLOR_VIRT_FLOPPY

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Floppy Virtual Device", description="The Floppy Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Has DatastoreFile?", description="Whether or not this Floppy has a `DatastoreFile` object.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualFloppy), "Not a VirtualFloppy"
        self.output = False if self.vd.file is None else True


class EsxiVirtualDeviceFloppyFile(Node):
    name: str = "ESXi Floppy VirtualDevice Get File"
    description: str = "Gets the file attached to this Floppy as a `DatastoreFile` object. Will raise a 'EsxiObjectDoesNotExistError' if there is no DatastoreFile assigned to the Floppy. Check ahead of time with 'Esxi Floppy VirtualDevice has File'"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Floppy"]
    color: str = esxi_constants.COLOR_VIRT_FLOPPY

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Floppy Virtual Device", description="The Floppy Virtual Device to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The file attached to this Floppy as a `DatastoreFile` object.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualFloppy), "Not a VirtualFloppy"
        result = self.vd.file
        if result is None:
            raise exceptions.EsxiObjectDoesNotExistError(f'CD-ROM VirtualDevice: "{self.vd.label}" ... Doesn\'t have a "DatastoreFile" object!')
        self.output = self.vd.file


class EsxiVirtualDeviceFloppyFileSetter(Node):
    name: str = "ESXi Floppy VirtualDevice Set File"
    description: str = "Set the file for this Floppy. Provide a `DatastoreFile` object for a file in the datastore to add to the Floppy."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Floppy"]
    color: str = esxi_constants.COLOR_VIRT_FLOPPY

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Floppy Virtual Device", description="The Floppy Virtual Device to use.")
    flop_input = InputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A `DatastoreFile` object for a file in the datastore to add to the Floppy"
    )

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.log(f"Setting Floppy Disk File to {self.flop_input.path}")
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualFloppy), "Not a VirtualFloppy"
        self.vd.file = self.flop_input


class EsxiVirtualDeviceAddCd(Node):
    name: str = "ESXi VirtualDevice Add CD ROM"
    description: str = "Add a new CD-ROM to the VM's devices. The VM must be powered off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "CD ROM"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    filepath = OptionalInputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A `DatastoreFile` object for a file in the datastore to add to the CD-ROM."
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="CD-ROM VirtualDevice", description="The `VirtualDevice` object for the newly added CD-ROM.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        filepath = self.filepath if self.filepath else None
        if self.filepath:
            self.log(f"Adding CD-ROM with file {self.filepath.path}")
        else:
            self.log(f"Adding empty CD-ROM")
        self.output = self.vm.cdroms.add(filepath=filepath)


class EsxiVirtualDeviceAddFloppy(Node):
    name: str = "ESXi VirtualDevice Add Floppy"
    description: str = "Add a new Floppy Disk to the VM's devices. The VM must be powered off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Floppy"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    filepath = InputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A `DatastoreFile` object for a file in the datastore to add to the Floppy."
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="Floppy VirtualDevice", description="The `VirtualDevice` object for the newly added Floppy.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Adding Floppy Disk with file {self.filepath.path}")
        self.output = self.vm.floppies.add(filepath=self.filepath)


class EsxiVirtualDeviceAddDisk(Node):
    name: str = "ESXi VirtualDevice Add Disk (Size String)"
    description: str = "Add a new Disk (HDD) to the VM's devices. The VM must be powered off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    size = InputSocket(
        datatype=String,
        name="Size",
        description="A string representing the size of the new disk. The string is expected to take the form <number><unit>, where <unit> is one of KB, MB, or GB (e.g. 32GB).",
    )
    scsi = InputSocket(datatype=Number, name="SCSI", description="The number for the SCSI controller to attach the new disk to.", input_field=0)
    thin = InputSocket(datatype=Boolean, name="Thin?", description="Whether nor not this new disk should be thin provisioned", input_field=True)
    unit_number = OptionalInputSocket(
        datatype=Number,
        name="Unit Number",
        description="The unit number to assign the disk to on the provided controller. If not provided, the next available unit number will be used.",
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="Disk VirtualDevice", description="The `VirtualDevice` object for the newly added Disk.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Adding new {self.size} disk.")
        self.output = self.vm.disks.add(size=self.size, scsi=int(self.scsi), unit_number=int(self.unit_number) if self.unit_number else None, thin=self.thin)
        self.debug(f"New disk ({self.output.label}): Size={self.size}, SCSI={self.scsi}, Thin Provisioned={self.thin}, Unit Number={self.unit_number}")


class EsxiVirtualDeviceAddDiskFromDatastore(Node):
    name: str = "ESXi VirtualDevice Add Disk From Datastore"
    description: str = "Add a Disk (HDD) that already exists in the datastore to the VM's devices. The VM must be powered off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    filepath = InputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A `DatastoreFile` object for a file in the datastore that represents the disk to use"
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="Disk VirtualDevice", description="The `VirtualDevice` object for the newly added Disk.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Adding virtual disk with datastore filepath: {self.filepath.path}")
        self.output = self.vm.disks.add_existing_disk(filepath=self.filepath)


class EsxiVirtualDeviceAddDiskNum(Node):
    name: str = "ESXi VirtualDevice Add Disk (Size KB)"
    description: str = "Add a new Disk (HDD) to the VM's devices. The VM must be powered off."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    size = InputSocket(datatype=Number, name="Size (KB)", description="A number representing the size of the new disk. The size should be in KB.")
    scsi = InputSocket(datatype=Number, name="SCSI", description="The number for the SCSI controller to attach the new disk to.", input_field=0)
    thin = InputSocket(datatype=Boolean, name="Thin?", description="Whether nor not this new disk should be thin provisioned", input_field=True)
    unit_number = OptionalInputSocket(
        datatype=Number,
        name="Unit Number",
        description="The unit number to assign the disk to on the provided controller. If not provided, the next available unit number will be used.",
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="Disk VirtualDevice", description="The `VirtualDevice` object for the newly added Disk.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Adding new {self.size}KB disk.")
        self.output = self.vm.disks.add(
            size=int(self.size), scsi=int(self.scsi), unit_number=int(self.unit_number) if self.unit_number else None, thin=self.thin
        )
        self.debug(f"New disk ({self.output.label}): Size (KB)={self.size}, SCSI={self.scsi}, Thin Provisioned={self.thin}, Unit Number={self.unit_number}")


class EsxiVirtualDeviceAddNic(Node):
    name: str = "ESXi VirtualDevice Add NIC"
    description: str = "Add a new NIC (Network Interface Card) to the VM's devices."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    network = InputSocket(datatype=String, name="Network", description="The name of the network (portgroup) to assign to the new NIC.")
    adapter_type = InputSocket(
        datatype=String,
        name="Adapter Type",
        description="The adapter type to use for the interface (Valid values: vmxnet, vmxnet2, vmxnet3, e1000, e1000e, pcnet32, sriov)",
        input_field="vmxnet3",
    )
    pci_slot = OptionalInputSocket(
        datatype=Number,
        name="PCI Slot",
        description="The PCI slot to use for the network interface. For some systems, the interface name is based on the PCI slot",
    )

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The `VirtualDevice` object for the newly added NIC.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f'Adding NIC "{self.network}"')
        valid_adapter_types = ["vmxnet", "vmxnet2", "vmxnet3", "e1000", "e1000e", "pcnet32", "sriov"]
        selected_adapter = self.adapter_type.lower()
        if selected_adapter not in valid_adapter_types:
            raise graphex_exceptions.InvalidParameterError(self.name, "Adapter Type", selected_adapter, valid_adapter_types)
        self.output = self.vm.nics.add(network=self.network, adapter_type=selected_adapter, pci_slot=int(self.pci_slot) if self.pci_slot else None)
        self.debug(f"New NIC ({self.output.label}): Network={self.network}, Adapter Type={self.adapter_type}, PCI Slot={self.pci_slot}")


class EsxiVirtualDeviceDiskSize(Node):
    name: str = "ESXi Disk VirtualDevice Get Size"
    description: str = "Get the size of this disk in KB."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DISK

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Disk Virtual Device", description="The Disk Virtual Device to use.")
    output = OutputSocket(datatype=Number, name="Size (KB)", description="The size of this disk in KB.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk), "Not a VirtualDisk"
        self.output = self.vd.size


class EsxiVirtualDeviceDiskFilepath(Node):
    name: str = "ESXi Disk VirtualDevice Get Filepath"
    description: str = "Get the path to this disk's file as a `DatastoreFile` object."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DISK

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Disk Virtual Device", description="The Disk Virtual Device to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The path to this disk's file as a `DatastoreFile` object.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk), "Not a VirtualDisk"
        self.output = self.vd.filepath


class EsxiVirtualDeviceDiskRemove(Node):
    name: str = "ESXi Remove Disk VirtualDevice"
    description: str = "Remove this disk from this virtual machine. The only difference between this action node and 'ESXi Remove VirtualDevice': This action node provides the ability to retain the file in the datastore after deletion."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DISK

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Disk Virtual Device", description="The Disk Virtual Device to remove.")
    delete_file = InputSocket(datatype=Boolean, name="Delete File?", description="Deletes the file from the datastore when set to True.", input_field=True)

    def log_prefix(self):
        return f"[{self.name} - {self.vd._vm.name}] "

    def run(self):
        self.log(f'Removing Disk "{self.vd.label}"')
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk), "Not a VirtualDisk"
        self.vd.remove(delete_file=self.delete_file)


class EsxiVirtualDeviceDiskSetSizeString(Node):
    name: str = "ESXi Disk VirtualDevice Set Size from String"
    description: str = "Modify the size of this disk."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DISK

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Disk Virtual Device", description="The Disk Virtual Device to use.")
    size = InputSocket(
        datatype=String,
        name="Size",
        description="A string representing the new size of this disk. The size must be greater or equal to the current disk size. The string is expected to take the form <number><unit>, where <unit> is one of KB, MB, or GB (e.g. 32GB).",
    )

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.log(f"Setting size to {self.size}")
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk), "Not a VirtualDisk"
        self.vd.size = self.size


class EsxiVirtualDeviceDiskSetSizeKB(Node):
    name: str = "ESXi Disk VirtualDevice Set Size (in KB)"
    description: str = "Modify the size of this disk."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Disk"]
    color: str = esxi_constants.COLOR_VIRT_DISK

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Disk Virtual Device", description="The Disk Virtual Device to use.")
    size = InputSocket(
        datatype=Number,
        name="Size",
        description="A number representing the new size of this disk (in KB). The size must be greater or equal to the current disk size.",
    )

    def log_prefix(self):
        return f"[{self.name} - '{self.vd.label}' on {self.vd._vm.name}] "

    def run(self):
        self.log(f"Setting size to {int(self.size)}KB")
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualDisk), "Not a VirtualDisk"
        self.vd.size = int(self.size)


class EsxiVirtualDeviceNicGet(Node):
    name: str = "ESXi Get NIC VirtualDevice from VM"
    description: str = "Get the NIC assigned to this VM associated with the given network and raise an exception if not found."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    network = InputSocket(datatype=String, name="Network", description="The name of the network (portgroup) for the NIC to get.")

    output = OutputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice object.")

    def run(self):
        self.output = self.vm.nics.get(self.network)


class EsxiVirtualDeviceNicExists(Node):
    name: str = "ESXi NIC VirtualDevice Exists on VM"
    description: str = "Check whether a NIC exists on this virtual machine for the provided network."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    network = InputSocket(datatype=String, name="Network", description="The name of the network (portgroup) for the NIC.")

    output = OutputSocket(datatype=Boolean, name="NIC VirtualDevice", description="Whether or not a NIC exists connected to this network.")

    def run(self):
        self.output = self.vm.nics.exists(self.network)


class EsxiVirtualDeviceNicGetNetwork(Node):
    name: str = "ESXi NIC VirtualDevice Get Network Name"
    description: str = "Gets the name of the network associated with this NIC."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    output = OutputSocket(datatype=String, name="Network Name", description="The name of the network associated with this NIC.")

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.output = self.nic.network


class EsxiVirtualDeviceNicSetNetwork(Node):
    name: str = "ESXi NIC VirtualDevice Set Network"
    description: str = "Set the network associated with this NIC."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    input_value = OutputSocket(datatype=String, name="Network Name", description="The name of the network to assign to this NIC.")

    def log_prefix(self):
        return f"[{self.name} - '{self.nic.label}' on {self.nic._vm.name}] "

    def run(self):
        self.log(f'Setting network to "{self.input_value}"')
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.nic.network = self.input_value


class EsxiVirtualDeviceNicPci(Node):
    name: str = "ESXi NIC VirtualDevice Get PCI Number"
    description: str = "Gets the PCI slot number associated with this NIC."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    output = OutputSocket(datatype=Number, name="PCI Slot Number", description="The PCI slot number associated with this NIC.")

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.output = self.nic.pci


class EsxiVirtualDeviceNicMac(Node):
    name: str = "ESXi NIC VirtualDevice Get MAC Address"
    description: str = "Gets the Mac address associated with this NIC."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    output = OutputSocket(datatype=String, name="MAC Address", description="The MAC Address associated with this NIC.")

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.output = self.nic.mac


class EsxiVirtualDeviceNicIsDistr(Node):
    name: str = "ESXi NIC VirtualDevice is Connected to Distributed Network"
    description: str = "Outputs True if this NIC is connected to a distributed network."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    output = OutputSocket(datatype=Boolean, name="Is Distributed?", description="True if this NIC is connected to a distributed network.")

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.output = self.nic.distributed


class EsxiVirtualDeviceNicGetIp(Node):
    name: str = "ESXi NIC VirtualDevice Get IP Address"
    description: str = (
        "Outputs the IPv4 address for this NIC. If this NIC doesn't have an IP address (or one cannot be found) then it will output an empty string."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    output = OutputSocket(datatype=String, name="IP Address", description="The IPv4 address for this NIC or the empty string.")

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        result = self.nic.ip
        self.output = result if result else ""


class EsxiVirtualDeviceNicWaitForIp(Node):
    name: str = "ESXi NIC VirtualDevice Wait for IP Address"
    description: str = "Waits for a NIC to become available with an IPv4 address. If a timeout is reached, an empty string will be produced."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "NIC"]
    color: str = esxi_constants.COLOR_VIRT_NIC

    nic = InputSocket(datatype=datatypes.VirtualDevice, name="NIC VirtualDevice", description="The NIC VirtualDevice to use.")
    retries = InputSocket(
        datatype=Number, name="Retries", description="How many times to retry detecting an IP on the given network before exiting.", input_field=60
    )
    delay = InputSocket(datatype=Number, name="Delay", description="How long to pause between retries in seconds.", input_field=2)

    output = OutputSocket(datatype=String, name="IP Address", description="The IPv4 address for this NIC or the empty string.")

    def log_prefix(self):
        return f"[{self.name} - '{self.nic.label}' on {self.nic._vm.name}] "

    def run(self):
        assert isinstance(self.nic, esxi_utils.vm.hardware.VirtualNIC), "Not a VirtualNIC"
        self.log(f'Waiting for IP on network "{self.nic.network}"...')
        self.output = self.nic.wait(retries=int(self.retries), delay=int(self.delay))
        self.debug(f'IP on network "{self.nic.network}": {self.output}')


class EsxiVirtualDeviceVideoCardRAMSize(Node):
    name: str = "ESXi Video Card VirtualDevice Get VRAM Size"
    description: str = "Get the RAM size of this Video Card in KB."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=Number, name="RAM Size (KB)", description="The size of this video card's VRAM in KB.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.videoRamSizeKB


class EsxiVirtualDeviceVideoCardGraphicsMemorySize(Node):
    name: str = "ESXi Video Card VirtualDevice Get (3D) Graphics Memory Size"
    description: str = "Get the size of this Video Card's total (3D) Graphics Memory in KB. THIS IS NOT THE SETTING SHOWN IN THE ESXI UI FOR VRAM (see '... Get Video RAM Size (VRAM)')."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=Number, name="Graphics Memory Size (KB)", description="The size of this video card's video Graphic Memory in KB.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.graphicsMemorySizeKB


class EsxiVirtualDeviceVideoCardIsThreeD(Node):
    name: str = "ESXi Video Card VirtualDevice Supports 3D"
    description: str = "Whether this video card currently has 3D support enabled or not."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="3D Enabled?", description="Whether this video card currently has 3D support enabled or not.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.enable3D


class EsxiVirtualDeviceVideoCardThreeDRendererName(Node):
    name: str = "ESXi Video Card VirtualDevice Current 3D Renderer"
    description: str = "Returns the name of the currently enabled 3D Renderer (e.g. automatic)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=String, name="Current Renderer", description="Returns the name of the currently enabled 3D Renderer (e.g. automatic).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.use3Drenderer


class EsxiVirtualDeviceVideoCardAutoDetect(Node):
    name: str = "ESXi Video Card VirtualDevice Using Auto Detect"
    description: str = "Whether this video card currently is using auto-detect or not (this can also be called 'default settings' in the UI) (the alternative to auto-detect are 'custom settings' set by the user in the ESXi UI or configured via GraphEx)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=Boolean, name="Using Auto-Detect?", description="Whether this video card currently has auto-detect enabled or not.")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.useAutoDetect


class EsxiVirtualDeviceVideoCardNumberOfDisplays(Node):
    name: str = "ESXi Video Card VirtualDevice Get Number of Displays"
    description: str = "The number of displays currently connected to this video card (as reported by ESXi)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    output = OutputSocket(datatype=Number, name="Number of Displays", description="The number of displays currently connected to this video card (as reported by ESXi).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.output = self.vd.numDisplays


class EsxiVirtualDeviceVideoCardSetAutoDetect(Node):
    name: str = "ESXi Video Card VirtualDevice Set Auto Detect"
    description: str = "Set the video card to auto-detect video card settings based on the VM or not (this can also be called 'default settings' in the UI) (the alternative is specifying custom settings via the ESXi UI or GraphEx)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    user_setting = InputSocket(datatype=Boolean, name="Use Auto Detect?", description="Set to True to use auto detect. Set to False to use custom user settings instead.")

    output = OutputSocket(datatype=Boolean, name="Using Auto-Detect?", description="Whether this video card currently has auto-detect enabled or not (after the set operation completes).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.vd.useAutoDetect = self.user_setting
        self.output = self.vd.useAutoDetect


class EsxiVirtualDeviceVideoCardSetGraphicsMemory(Node):
    name: str = "ESXi Video Card VirtualDevice Set (3D) Graphics Memory Size"
    description: str = "Set the amount of (3D) graphics memory available to the video card in KiloBytes (KB) (1MB = 1024KB). This operation often fails. The default size is usually 32MB. THIS IS NOT THE SETTING SHOWN IN THE ESXI UI FOR VRAM (see '... Set Video RAM Size (VRAM)'). The VM must be powered off in order to change the available size. This is a custom user setting and is not usable alongside 'Auto Detect' graphic settings (this operation is ignored by ESXi if auto-detect or 'default settings' is set for this video card)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    user_setting = InputSocket(datatype=Number, name="Graphics Memory Size KB", description="The amount of graphics memory to assign to the VM in KiloBytes.")

    output = OutputSocket(datatype=Number, name="Graphics Memory Size (KB)", description="The size of this video card's graphic memory in KB (after the set operation completes).")


    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.vd.graphicsMemorySizeKB = self.user_setting
        self.output = self.vd.graphicsMemorySizeKB


class EsxiVirtualDeviceVideoCardSetVRAM(Node):
    name: str = "ESXi Video Card VirtualDevice Set Video RAM Size (VRAM)"
    description: str = "Set the amount of VRAM available to the video card in KiloBytes (KB) (1MB = 1024KB). This is the 'Total Video Memory' field as shown in the ESXi UI. The VM must be powered off in order to change the available size. This is a custom user setting and is not usable alongside 'Auto Detect' graphic settings (this operation is ignored by ESXi if auto-detect or 'default settings' is set for this video card)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    user_setting = InputSocket(datatype=Number, name="VRAM Size KB", description="The amount of VRAM to assign to the VM in KiloBytes.")

    output = OutputSocket(datatype=Number, name="RAM Size (KB)", description="The size of this video card's VRAM in KB (after the set operation completes).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.vd.videoRamSizeKB = self.user_setting
        self.output = self.vd.videoRamSizeKB


class EsxiVirtualDeviceVideoCardSetThreeDSupport(Node):
    name: str = "ESXi Video Card VirtualDevice Set 3D Support"
    description: str = "Set the video card to use/support 3D or not (default is usually False). The VM must be powered off in order for this operation to work."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    user_setting = InputSocket(datatype=Boolean, name="Use 3D?", description="Set to True to use 3D.")

    output = OutputSocket(datatype=Boolean, name="Using 3D?", description="Whether this video card currently has 3D enabled or not (after the set operation completes).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.vd.enable3D = self.user_setting
        self.output = self.vd.enable3D


# This errors from the API but works from the UI
# I'm not sure how to fix it at the moment
# class EsxiVirtualDeviceVideoCardSetThreeDRenderer(Node):
#     name: str = "ESXi Video Card VirtualDevice Set 3D Renderer"
#     description: str = "Set the name of the 3D renderer being used by the video card."
#     categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
#     color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

#     vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
#     user_setting = EnumInputSocket(datatype=String, name="3D Renderer Name", description="The name of the 3D renderer to use by the video card.", enum_members=['Automatic', 'Hardware', 'Software'],input_field="Automatic")

#     output = OutputSocket(datatype=String, name="3D Renderer Name", description="The name of the 3D renderer to use by the video card (after the set operation completes).")

#     def run(self):
#         assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
#         self.vd.use3Drenderer = self.user_setting
#         self.output = self.vd.use3Drenderer


class EsxiVirtualDeviceVideoCardSetNumDisplays(Node):
    name: str = "ESXi Video Card VirtualDevice Set Number of Displays"
    description: str = "Sets the number of displays connected to this video card. This is a custom user setting and is not usable alongside 'Auto Detect' graphic settings (this operation is ignored by ESXi if auto-detect or 'default settings' is set for this video card)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Hardware", "Virtual Devices", "Video Card"]
    color: str = esxi_constants.COLOR_VIRT_VIDEO_CARD

    vd = InputSocket(datatype=datatypes.VirtualDevice, name="Video Card Virtual Device", description="The Video Card Virtual Device to use.")
    user_setting = EnumInputSocket(datatype=Number, name="Number of Displays", description="The amount of displays you want connected to this video card.", enum_members=[1,2,3,4,5,6,7,8,9,10], input_field=1)

    output = OutputSocket(datatype=Number, name="Number of Displays", description="The amount of displays to connected to this video card. (after the set operation completes).")

    def run(self):
        assert isinstance(self.vd, esxi_utils.vm.hardware.VirtualVideoCard), "Not a VirtualVideoCard"
        self.vd.numDisplays = self.user_setting
        self.output = self.vd.numDisplays
