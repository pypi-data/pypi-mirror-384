from graphex import Boolean, String, Number, DataContainer, Node, InputSocket, OutputSocket, ListOutputSocket
from graphex import exceptions as graphex_exceptions
from graphex_esxi_utils import esxi_constants, datatypes
import esxi_utils
import typing


class EsxiOvfFileCreate(Node):
    name: str = "ESXi Create OVF File from Path"
    description: str = "Creates an OVF File Object from the provided path to the ovf file."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    path = InputSocket(datatype=String, name="Path", description="The path to the actual OVF file on disk to convert to an OVF File object.")
    output = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="An object representing an OVF file.")

    def run(self):
        self.debug(f"Creating OVF File object from {self.path}")
        self.output = esxi_utils.file.OvfFile(self.path)


class EsxiOvfFileGetPath(Node):
    name: str = "ESXi OVF File Get Path"
    description: str = "Gets the path associated with this OVF File object."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="Path to OVF File", description="The path associated with this file.")

    def run(self):
        self.output = self.ovf.path


class EsxiOvfFileGetExt(Node):
    name: str = "ESXi OVF File Get Extension"
    description: str = "Gets the file extension associated with this OVF File object."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="File Extension", description="The file extension associated with this file.")

    def run(self):
        self.output = self.ovf.ext


class EsxiOvfFileIsArchive(Node):
    name: str = "ESXi OVF File is Archive"
    description: str = "Outputs True if this OVF is archive type (extension '.ova')"
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=Boolean, name="Is OVA?", description="True if this OVF is archive type (extension '.ova')")

    def run(self):
        self.output = self.ovf.is_archive


class EsxiOvfFileGetDescriptorName(Node):
    name: str = "ESXi OVF File Get Descriptor Name"
    description: str = "Gets the name of the virtual appliance descriptor file (i.e. the OVF file itself)."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="Descriptor Name", description="The name of the virtual appliance descriptor file (i.e. the OVF file itself).")

    def run(self):
        self.output = self.ovf.descriptor_name


class EsxiOvfFileGetManifestName(Node):
    name: str = "ESXi OVF File Get Manifest Name"
    description: str = "The name of the manifest file, if it exists. Outputs the empty string if the manifest file does not exist."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(
        datatype=String,
        name="Manifest Name",
        description="The name of the manifest file, if it exists. Outputs the empty string if the manifest file does not exist.",
    )

    def run(self):
        result = self.ovf.manifest_name
        self.output = result if result else ""


class EsxiOvfFileGetName(Node):
    name: str = "ESXi OVF File Get Name"
    description: str = "The name of the OVF/OVA."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="OVF/OVA Name", description="The name of the OVF/OVA.")

    def run(self):
        self.output = self.ovf.name


class EsxiOvfFileGetVmName(Node):
    name: str = "ESXi OVF File Get VM Name"
    description: str = "The VM name specified in the OVF/OVA."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="VM Name", description="The VM name specified in the OVF/OVA.")

    def run(self):
        self.output = self.ovf.vmname


class EsxiOvfFileGetNetworkNames(Node):
    name: str = "ESXi OVF File Get Network Names"
    description: str = "Get the names of the networks assigned to the OVF/OVA."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = ListOutputSocket(datatype=String, name="Network Names", description="The names of the networks assigned to the OVF/OVA.")

    def run(self):
        self.output = self.ovf.networks


class EsxiOvfFileGetFileNames(Node):
    name: str = "ESXi OVF File Get File Names"
    description: str = "Get a list of all file names referenced by this virtual appliance (Note: does not check for file existence)."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = ListOutputSocket(
        datatype=String,
        name="File Names",
        description="A list of all file names referenced by this virtual appliance (Note: does not check for file existence).",
    )

    def run(self):
        self.output = self.ovf.files


class EsxiOvfFileGetDiskNames(Node):
    name: str = "ESXi OVF File Get Disk Names"
    description: str = "Get a list of all disk names referenced by this virtual appliance."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = ListOutputSocket(datatype=String, name="Disk Names", description="A list of all disk names referenced by this virtual appliance.")

    def run(self):
        self.output = self.ovf.disks


class EsxiOvfFileGetRequiredStorage(Node):
    name: str = "ESXi OVF File Get Required Storage"
    description: str = "Get the amount of required storage to contain the VM represented by this virtual appliance. This is the sum of all disk sizes, plus the size of any non-disk files."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    bytes_unit = InputSocket(
        datatype=String, name="Bytes Unit", description="The unit of measurement to use (Must be one of: B, KB, MB, GB).", input_field="KB"
    )

    output = OutputSocket(
        datatype=Number, name="Required Storage", description="The amount of required storage to contain the VM represented by this virtual appliance."
    )

    def run(self):
        valid_units = ["B", "KB", "MB", "GB"]
        unit = self.bytes_unit.upper()
        if unit not in valid_units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", unit, valid_units)
        self.output = self.ovf.required_storage(unit=unit)


class EsxiOvfFileCreateManifest(Node):
    name: str = "ESXi OVF File Create Manifest"
    description: str = "Creates a manifest file, or updates if it already exists."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    hash_type = InputSocket(
        datatype=String,
        name="Hash Type",
        description="The hash function to use for generating file checksums. Accepts any `hashlib` hash functions.",
        input_field="sha1",
    )

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Creating manifest...")
        self.output_ovf = self.ovf
        self.output = self.ovf.create_manifest(hash_type=self.hash_type)


class EsxiOvfFileValidate(Node):
    name: str = "ESXi OVF File Validate"
    description: str = "Validates this virtual appliance file by checking that referenced files exist and that the manifest file (if exists) is correct. Raises an `OvfManifestError` if the validation fails."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Validating...")
        self.output_ovf = self.ovf
        self.ovf.validate()


class EsxiOvfFileRemove(Node):
    name: str = "ESXi OVF File Remove"
    description: str = "Delete this file and any associated files."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to delete.")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Removing...")
        self.ovf.remove()


class EsxiOvfFileGetOsTypeString(Node):
    name: str = "ESXi OVF File Get OS Type as String"
    description: str = "The VM OS type specified in the OVF/OVA (as a string)."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    output = OutputSocket(datatype=String, name="OS Type String", description="The VM OS type specified in the OVF/OVA (as a string).")

    def run(self):
        self.output = str(self.ovf.ostype)


class EsxiOvfFileRename(Node):
    name: str = "ESXi OVF File Rename"
    description: str = "Rename this virtual appliance and its files. The update will happen in-place. Files after the the rename will follow the convention `{new_name}_file{num}` or `{new_name}_disk{num}`"
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    new_name = InputSocket(datatype=String, name="New Name", description="The new name to give to the virtual appliance and its file.")

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Renaming {self.ovf.name} to {self.new_name}")
        self.output_ovf = self.ovf
        self.ovf.rename(new_name=self.new_name)


class EsxiOvfFileRenameNetwork(Node):
    name: str = "ESXi OVF File Rename Network"
    description: str = (
        "Rename a network in this OVF or OVA. The update will happen in-place. If the network is not found in the OVF, an exception will be raised."
    )
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    old_name = InputSocket(datatype=String, name="Old Network Name", description="The name of the old network to update.")
    new_name = InputSocket(datatype=String, name="New Network Name", description="The new name of the network.")

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Renaming Network {self.old_name} to {self.new_name}")
        self.output_ovf = self.ovf
        self.ovf.rename_network(old_network_name=self.old_name, new_network_name=self.new_name)


class EsxiOvfFileAsOvf(Node):
    name: str = "ESXi OVF File Write as OVF"
    description: str = "Write this file as an OVF to the provided directory. If this is an OVA, the contents will be extracted to the target directory. If this is already an OVF, the files will simply be copied to the target directory."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    path = InputSocket(datatype=String, name="Path", description="The path to the directory in which to place the OVF.", input_field=".")
    move = InputSocket(
        datatype=Boolean,
        name="Move?",
        description="Whether or not the move the files instead of copying them (delete original files). If `True`, the path for this object will be updated as well.",
        input_field=False,
    )

    output = OutputSocket(datatype=datatypes.OvfFile, name="New OVF File Object", description="An `OvfFile` object for the new OVF.")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        if self.move:
            self.log(f"Moving as OVF to {self.path}")
        else:
            self.log(f"Copying as OVF to {self.path}")
        path = self.path if self.path != "." and self.path != "" else None
        self.output = self.ovf.as_ovf(path=path, move=self.move)


class EsxiOvfFileAsOva(Node):
    name: str = "ESXi OVF File Write as OVA"
    description: str = "Write this file as an OVA to the provided directory. If this is already an OVA, this will simply be copied to the target directory. If this is an OVF, the files will be added as a new archive in the target directory."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    path = InputSocket(datatype=String, name="Path", description="The path to the directory in which to place the OVA.", input_field=".")
    move = InputSocket(
        datatype=Boolean,
        name="Move?",
        description="Whether or not the move the files instead of copying them (delete original files). If `True`, the path for this object will be updated as well.",
        input_field=False,
    )

    output = OutputSocket(datatype=datatypes.OvfFile, name="New OVF File Object", description="An `OvfFile` object for the new OVA.")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        if self.move:
            self.log(f"Moving as OVA to {self.path}")
        else:
            self.log(f"Copying as OVA to {self.path}")
        path = self.path if self.path != "." and self.path != "" else None
        self.output = self.ovf.as_ova(path=path, move=self.move)


class EsxiOvfFileSetConfig(Node):
    name: str = "ESXi OVF File Set Config Value"
    description: str = "Set a config entry (a <Config> tag) in the OVF. If the entry does not exist, it will be created."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    entry_key = InputSocket(datatype=String, name="Key", description="The entry key.")
    entry_value = InputSocket(datatype=String, name="Value", description="The entry value.")
    required = InputSocket(datatype=Boolean, name="Required?", description="Whether or not the entry is set to be required.", input_field=False)
    extraconfig = InputSocket(
        datatype=Boolean,
        name="ExtraConfig Tag?",
        description="Whether or not this is an extra-config entry (an <ExtraConfig> tag) rather than a standard config entry.",
        input_field=False,
    )

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Setting {'ExtraConfig' if self.extraconfig else 'Config'} {self.entry_key}={self.entry_value} (Required={self.required})")
        self.output_ovf = self.ovf
        self.ovf.set_config(key=self.entry_key, value=self.entry_value, required=self.required, extraconfig=self.extraconfig)


class EsxiOvfFileSetConfigValues(Node):
    name: str = "ESXi OVF File Set Config Values"
    description: str = "Set multiple config entries (<Config> tags) in the OVF. If an entry does not exist, it will be created."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    config_values = InputSocket(
        datatype=DataContainer, name="Key/Value Pairs", description="The key/value pairs to apply to the OVF (as a DataContainer object)."
    )
    required = InputSocket(datatype=Boolean, name="Required?", description="Whether or not the entries are set to be required.", input_field=False)
    extraconfig = InputSocket(
        datatype=Boolean,
        name="ExtraConfig Tag?",
        description="Whether or not these are extra-config entries (<ExtraConfig> tags) rather than standard config entries.",
        input_field=False,
    )

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.output_ovf = self.ovf
        assert isinstance(self.config_values, dict), "Provided DataContainer object is not a dictionary-like value."
        for key, value in self.config_values.items():
            self.log(f"Setting {'ExtraConfig' if self.extraconfig else 'Config'} {key}={value} (Required={self.required})")
            self.ovf.set_config(key=key, value=str(value), required=self.required, extraconfig=self.extraconfig)


class EsxiOvfFileRemoveConfig(Node):
    name: str = "ESXi OVF File Remove Config"
    description: str = "Remove a config entry (a <Config> tag) in the OVF. If the entry does not exist, this does nothing."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")

    entry_key = InputSocket(datatype=String, name="Key", description="The entry key.")
    extraconfig = InputSocket(
        datatype=Boolean,
        name="ExtraConfig Tag?",
        description="Whether or not this is an extra-config entry (an <ExtraConfig> tag) rather than a standard config entry.",
        input_field=False,
    )

    output_ovf = OutputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object (same as input).")

    def log_prefix(self):
        return f"[{self.name} - {self.ovf.path}] "

    def run(self):
        self.log(f"Removing {'ExtraConfig' if self.extraconfig else 'Config'} {self.entry_key}")
        self.output_ovf = self.ovf
        self.ovf.remove_config(key=self.entry_key, extraconfig=self.extraconfig)


class EsxiOvfFileGetDiskSizes(Node):
    name: str = "ESXi OVF File Get Disk Sizes"
    description: str = "Get the sizes of disk for this virtual machine. This is the maximum capacity of the disk when the OVF/OVA is deployed, not the size of the VMDK as stored on the filesystem."
    categories: typing.List[str] = ["ESXi", "OVF"]
    color: str = esxi_constants.COLOR_OVF_FILE

    ovf = InputSocket(datatype=datatypes.OvfFile, name="OVF File Object", description="The OVF File Object to use.")
    bytes_unit = InputSocket(
        datatype=String, name="Bytes Unit", description="The unit of measurement to use (Must be one of: B, KB, MB, GB).", input_field="KB"
    )

    output_names = ListOutputSocket(datatype=String, name="Disk Names", description="The names of the disks in this OVF file.")
    output_sizes = ListOutputSocket(datatype=Number, name="Disk Sizes", description="The sizes of the disks in this OVF file.")

    def run(self):
        valid_units = ["B", "KB", "MB", "GB"]
        unit = self.bytes_unit.upper()
        if unit not in valid_units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", unit, valid_units)
        result = self.ovf.disk_sizes(unit=unit)
        names = []
        sizes = []
        for key, value in result.items():
            names.append(key)
            sizes.append(value)
        self.output_names = names
        self.output_sizes = sizes
