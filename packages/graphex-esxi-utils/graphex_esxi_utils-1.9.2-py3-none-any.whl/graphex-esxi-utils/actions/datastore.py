from graphex import Boolean, String, Number, Node, InputSocket, OptionalInputSocket, OutputSocket, ListOutputSocket, ListInputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex import exceptions as graphex_exceptions
import esxi_utils
import typing
import re


class EsxiDatastoreGetName(Node):
    name: str = "ESXi Get Datastore Name"
    description: str = "Gets the name for the provided Datastore."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(datatype=String, name="Datastore Name", description="The name for the provided Datastore.")

    def run(self):
        self.output = self.datastore.name


class EsxiDatastoreGetFileSystemType(Node):
    name: str = "ESXi Datastore Get File System Type"
    description: str = "Get the type of file system volume, such as VMFS or NFS."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(datatype=String, name="File System Type", description="The file system type, such as VMFS or NFS.")

    def run(self):
        self.output = self.datastore.file_system_type


class EsxiDatastoreIsNfs(Node):
    name: str = "ESXi Datastore is NFS"
    description: str = "Get whether or not this datastore is a network file system."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(datatype=Boolean, name="is NFS?", description="Whether or not this datastore is a network file system.")

    def run(self):
        self.output = self.datastore.nfs


class EsxiDatastoreGetPath(Node):
    name: str = "ESXi Datastore Get Path"
    description: str = "Get the path of the datastore on the ESXi host (i.e. /vmfs/volumes/<id>)."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(datatype=String, name="Path", description="The path of the datastore on the ESXi host (i.e. /vmfs/volumes/<id>).")

    def run(self):
        self.output = self.datastore.path


class EsxiDatastoreIsAccessible(Node):
    name: str = "ESXi Datastore is Accessible"
    description: str = "Get the connectivity status of this datastore. If false, this means the datastore is not accessible and certain properties (i.e. this datastore's capacity and freespace properties) cannot be validated."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(
        datatype=Boolean,
        name="Accessible?",
        description="The connectivity status of this datastore. If false, this means the datastore is not accessible and certain properties (i.e. this datastore's capacity and freespace properties) cannot be validated.",
    )

    def run(self):
        self.output = self.datastore.accessible


class EsxiDatastoreGetRootPath(Node):
    name: str = "ESXi Datastore Get Root Path"
    description: str = "Get the root filepath for this datastore (as a DatastoreFile object)."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="Root Path", description="The root filepath for this datastore.")

    def run(self):
        self.output = self.datastore.root


class EsxiDatastoreGetVms(Node):
    name: str = "ESXi Datastore Get VMs"
    description: str = "Get the Virtual machines stored on this datastore."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    output = ListOutputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machines", description="The Virtual machines stored on this datastore.")

    def run(self):
        self.debug(f'Getting Virtual Machines from Datastore "{self.datastore.name}"')
        self.output = self.datastore.vms


class EsxiDatastoreGetFilePath(Node):
    name: str = "ESXi Datastore Get DatastoreFile from File Path"
    description: str = "Get a 'DatastoreFile' object for the provided path."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    path = InputSocket(datatype=String, name="File Path", description="The Path to get the DatastoreFile from.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A 'DatastoreFile' object for the provided path.")

    def run(self):
        self.output = self.datastore.filepath(self.path)


class EsxiDatastoreGetCapacity(Node):
    name: str = "ESXi Datastore Get Capacity"
    description: str = "Get the capacity of this datastore in the provided unit."
    categories: typing.List[str] = ["ESXi", "Datastore", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")
    output = OutputSocket(datatype=Number, name="Capacity", description="The capacity of the datastore in the provided unit.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output = self.datastore.capacity(unit=used_unit)


class EsxiDatastoreGetFreespace(Node):
    name: str = "ESXi Datastore Get Free Space"
    description: str = "Get the free space of this datastore in the provided unit."
    categories: typing.List[str] = ["ESXi", "Datastore", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")
    output = OutputSocket(datatype=Number, name="Free Space", description="The free space of the datastore in the provided unit.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output = self.datastore.freespace(unit=used_unit)


class EsxiDatastoreGetDiskUsage(Node):
    name: str = "ESXi Datastore Get Used Disk Space"
    description: str = "Get the consumed space of this datastore in the provided unit."
    categories: typing.List[str] = ["ESXi", "Datastore", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")
    output = OutputSocket(datatype=Number, name="Used Space", description="The used space of the datastore disk in the provided unit.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output = self.datastore.used_disk_space(unit=used_unit)


class EsxiDatastoreGetUsagePercent(Node):
    name: str = "ESXi Datastore Get Disk Usage Percent"
    description: str = "The amount of disk space currently being utilized by the datastore as a percent (e.g. 34.54%)."
    categories: typing.List[str] = ["ESXi", "Datastore", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")

    result = OutputSocket(datatype=Number, name="Disk Usage Percent", description="The amount of Disk being utilized as a percent.")

    def run(self):
        self.result = self.datastore.disk_usage_percent()


class EsxiDatastoreGetDiskUsageAll(Node):
    name: str = "ESXi Datastore Get All Disk Usage Information"
    description: str = "All of the currently available information about the disk (total space capacity, free space, used/consumed space, and percent usage)."
    categories: typing.List[str] = ["ESXi", "Datastore", "Stack Monitoring"]
    color: str = esxi_constants.COLOR_DATASTORE

    datastore = InputSocket(datatype=datatypes.Datastore, name="Datastore", description="The Datastore to use.")
    unit = InputSocket(datatype=String, name="Bytes Unit", description="The unit of measurement to use (must be one of: B, KB, MB, GB, TB).", input_field="B")

    output_capacity = OutputSocket(datatype=Number, name="Capacity", description="The capacity of the datastore in the provided unit.")
    output_free_space = OutputSocket(datatype=Number, name="Free Space", description="The free space of the datastore in the provided unit.")
    output_used_space = OutputSocket(datatype=Number, name="Used Space", description="The used space of the datastore disk in the provided unit.")
    result_percent = OutputSocket(datatype=Number, name="Disk Usage Percent", description="The amount of Disk being utilized as a percent.")

    def run(self):
        units = ["B", "KB", "MB", "GB", "TB"]
        used_unit = self.unit.upper()
        if used_unit not in units:
            raise graphex_exceptions.InvalidParameterError(self.name, "Bytes Unit", used_unit, units)
        self.output_capacity = self.datastore.capacity(unit=used_unit)
        self.output_free_space = self.datastore.freespace(unit=used_unit)
        self.output_used_space = self.datastore.used_disk_space(unit=used_unit)
        self.result_percent = self.datastore.disk_usage_percent()


class EsxiDatastoreFileJoin(Node):
    name: str = "ESXi DatastoreFile Join"
    description: str = "Join this path with one or more additional path components. Does not check that this path exists."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    paths = ListInputSocket(datatype=String, name="Paths", description="The paths to join with this DatastoreFile.")
    output = OutputSocket(datatype=String, name="Joined DatastoreFile", description="The joined DatastoreFile.")

    def run(self):
        self.output = self.datastoreFile.join(self.paths)


class EsxiDatastoreFileGetDatastore(Node):
    name: str = "ESXi DatastoreFile Get Datastore"
    description: str = "The datastore for this filepath."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=datatypes.Datastore, name="Datastore", description="The datastore for this filepath.")

    def run(self):
        self.output = self.datastoreFile.datastore


class EsxiDatastoreFileGetRelpath(Node):
    name: str = "ESXi DatastoreFile Get Relative Path"
    description: str = "Return the relative path for this filepath in the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=String, name="Relative Path", description="The relative path for this filepath in the datastore.")

    def run(self):
        self.output = self.datastoreFile.relpath


class EsxiDatastoreFileGetPath(Node):
    name: str = "ESXi DatastoreFile Get Path"
    description: str = "Return the path for this filepath in the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=String, name="Path", description="The path for this filepath in the datastore.")

    def run(self):
        self.output = self.datastoreFile.path


class EsxiDatastoreFileGetAbsPath(Node):
    name: str = "ESXi DatastoreFile Get Absolute Path"
    description: str = "Return absolute the path for this filepath in the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=String, name="Absolute Path", description="The absolute path for this filepath in the datastore.")

    def run(self):
        self.output = self.datastoreFile.abspath


class EsxiDatastoreFileGetFilename(Node):
    name: str = "ESXi DatastoreFile Get Filename"
    description: str = "The final component of the file path (basename)."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=String, name="Filename", description="The final component of the file path (basename).")

    def run(self):
        self.output = self.datastoreFile.filename


class EsxiDatastoreFileGetParent(Node):
    name: str = "ESXi DatastoreFile Get Parent"
    description: str = "Gets the parent directory of this file. Check whether the parent directory exists before using the result."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    is_parent = OutputSocket(datatype=Boolean, name="Has Parent?", description="Whether this datastore file has a parent directory.")
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="Parent DatastoreFile", description="The parent directory of this file (if it exists).")

    def run(self):
        result = self.datastoreFile.parent
        self.is_parent = True if result else False
        self.output = result


class EsxiDatastoreFileLS(Node):
    name: str = "ESXi DatastoreFile ls"
    description: str = "List all files and directories in this directory."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    recursive = InputSocket(datatype=Boolean, name="Recursive?", description="List files recursively or not.", input_field=False)
    output = ListOutputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFiles", description="All files and directories in this directory (as DatastoreFile objects)/."
    )

    def run(self):
        self.output = self.datastoreFile.ls(recursive=self.recursive)


class EsxiDatastoreFileListFiles(Node):
    name: str = "ESXi DatastoreFile List Files"
    description: str = "List files in this directory (directories not included)."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = ListOutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFiles", description="All files in this directory (as DatastoreFile objects).")

    def run(self):
        self.output = self.datastoreFile.files


class EsxiDatastoreFileListDirectories(Node):
    name: str = "ESXi DatastoreFile List Directories"
    description: str = "List directories in this directory (files not included)."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = ListOutputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFiles", description="All directories in this directory (as DatastoreFile objects)"
    )

    def run(self):
        self.output = self.datastoreFile.dirs


class EsxiDatastoreFileExists(Node):
    name: str = "ESXi DatastoreFile Exists"
    description: str = "Whether or not this file exists on the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=Boolean, name="Exists?", description="Whether or not this file exists on the datastore.")

    def run(self):
        self.output = self.datastoreFile.exists


class EsxiDatastoreFileIsFile(Node):
    name: str = "ESXi DatastoreFile is File"
    description: str = "Whether or not this is a file on the datastore (as opposed to being a directory)."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=Boolean, name="Is File?", description="Whether or not this is a file on the datastore.")

    def run(self):
        self.output = self.datastoreFile.isfile


class EsxiDatastoreFileIsDirectory(Node):
    name: str = "ESXi DatastoreFile is Directory"
    description: str = "Whether or not this is a directory on the datastore. (as opposed to being a file)."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    output = OutputSocket(datatype=Boolean, name="Is Directory?", description="Whether or not this is a directory on the datastore.")

    def run(self):
        self.output = self.datastoreFile.isdir


class EsxiDatastoreFileRead(Node):
    name: str = "ESXi Read DatastoreFile"
    description: str = "Returns the contents of a file on the remote server."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use when decoding the file.", input_field="utf-8")
    output = OutputSocket(datatype=String, name="File Contents", description="The file contents as a string.")

    def run(self):
        self.log(f"Reading file {self.datastoreFile.path}")
        self.output = str(self.datastoreFile.read(self.encoding))
        self.debug(f"File contents for {self.datastoreFile.path}:\n" + re.sub(r"^", "  │  ", self.output, flags=re.MULTILINE))


class EsxiDatastoreFileWrite(Node):
    name: str = "ESXi Write to DatastoreFile"
    description: str = "Writes to the remote file. The file will be created if it does not exist. If it does exist, the contents will be overwritten."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    contents = InputSocket(datatype=String, name="Contents", description="The contents to write to the file.")

    def run(self):
        self.log(f"Writing file {self.datastoreFile.path}")
        self.debug(f"Writing to file {self.datastoreFile.path}:\n" + re.sub(r"^", "  │  ", self.contents, flags=re.MULTILINE))
        self.datastoreFile.write(contents=self.contents)


class EsxiDatastoreFileDownload(Node):
    name: str = "ESXi Download DatastoreFile"
    description: str = "Download this file or directory from the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    dst = InputSocket(datatype=String, name="Local Destination", description="The local destination file or directory to download to.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only?",
        description="If 'True' and this is a directory, then just the contents of the directory will be downloaded rather than the directory itself.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite?", description="Whether to overwrite existing files.", input_field=False)

    output = ListOutputSocket(datatype=String, name="Downloaded Paths", description="A list of local paths to all files downloaded.")

    def run(self):
        self.log(f"Downloading file {self.datastoreFile.path} to {self.dst}")
        self.output = self.datastoreFile.download(dst=self.dst, directory_contents_only=self.directory_contents_only, overwrite=self.overwrite)


class EsxiDatastoreFileUpload(Node):
    name: str = "ESXi Upload DatastoreFile"
    description: str = "Upload a file or directory to this path on the datastore."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")
    src = InputSocket(datatype=String, name="Local Source", description="The local path to a file or directory to upload.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only?",
        description="If 'True' and 'src' points to a directory, then only the contents of the directory will be uploaded rather than the directory itself.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite?", description="Whether to overwrite existing files on the datastore.", input_field=False)

    output = ListOutputSocket(
        datatype=datatypes.DatastoreFile, name="Uploaded DatastoreFiles", description="A list of 'DatastoreFile' objects for all files uploaded."
    )

    def run(self):
        self.log(f"Uploading file {self.src} to {self.datastoreFile.path}")
        self.output = self.datastoreFile.upload(src=self.src, directory_contents_only=self.directory_contents_only, overwrite=self.overwrite)


class EsxiDatastoreFileMkdir(Node):
    name: str = "ESXi DatastoreFile Make Directory (mkdir)"
    description: str = "Create this folder (directory) in the datastore. If the directory already exists, this does nothing."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to the path to make.")
    parents = InputSocket(datatype=Boolean, name="Parents?", description="Make parent directories as needed.", input_field=False)

    def run(self):
        self.log(f"Creating directory {self.datastoreFile.path}")
        self.datastoreFile.mkdir(parents=self.parents)


class EsxiDatastoreFileCopy(Node):
    name: str = "ESXi DatastoreFile Copy"
    description: str = "Copy this file or directory to another location."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to copy.")
    to = InputSocket(datatype=datatypes.DatastoreFile, name="To", description="The 'DatastoreFile' to the destination file or directory (location to copy to).")
    force = InputSocket(datatype=Boolean, name="Force?", description="If true, overwrite any identically named file at the destination.", input_field=False)

    def run(self):
        self.log(f"Copying {self.datastoreFile.path} to {self.to.path}")
        self.datastoreFile.copy(to=self.to, force=self.force)


class EsxiDatastoreFileMerge(Node):
    name: str = "ESXi DatastoreFile Merge"
    description: str = "Merge (copy) the contents of this directory to another."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to the directory to merge.")
    to = InputSocket(datatype=datatypes.DatastoreFile, name="To", description="The 'DatastoreFile' for the destination directory (location to merge to).")
    force = InputSocket(datatype=Boolean, name="Force?", description="If true, overwrite any identically named file at the destination.", input_field=False)

    def run(self):
        self.log(f"Merging {self.datastoreFile.path} to {self.to.path}")
        self.datastoreFile.merge(to=self.to, force=self.force)


class EsxiDatastoreFileMove(Node):
    name: str = "ESXi DatastoreFile Move"
    description: str = "Move this file or directory to another location."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to move.")
    to = InputSocket(datatype=datatypes.DatastoreFile, name="To", description="The 'DatastoreFile' for the destination (location to move to).")
    force = InputSocket(datatype=Boolean, name="Force?", description="If true, overwrite any identically named file at the destination.", input_field=False)

    def run(self):
        self.log(f"Moving {self.datastoreFile.path} to {self.to.path}")
        self.datastoreFile.move(to=self.to, force=self.force)


class EsxiDatastoreFileRemove(Node):
    name: str = "ESXi DatastoreFile Remove (Delete)"
    description: str = (
        "Removes (deletes) this file or directory on the datastore. Folder deletes are always recursive. If the path does not exist, this does nothing."
    )
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to remove.")

    def run(self):
        self.log(f"Removing {self.datastoreFile.path}")
        self.datastoreFile.remove()


class EsxiDatastoreFileRegisterVM(Node):
    name: str = "ESXi DatastoreFile Register VM"
    description: str = "Register a new VM using this file. This must be a valid VMX file, or a directory containing a single VMX file."
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(
        datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to the VMX file (or directory containing the VMX file)."
    )
    vm_name = OptionalInputSocket(
        datatype=String, name="Name", description="The name to set for the VM. If not provided, the VM name will be derived from the VMX file."
    )
    output = OutputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="A 'VirtualMachine' object for the new VM.")

    def run(self):
        self.log(f'Registering Virtual Machine "{self.vm_name}" from {self.datastoreFile.path}')
        vm_name = self.vm_name if self.vm_name else None
        self.output = self.datastoreFile.register_vm(name=vm_name)


class EsxiDatastoreFileParse(Node):
    name: str = "ESXi Parse String to DatastoreFile"
    description: str = (
        "Convert a path to a 'DatastoreFile'. This effectively gets a datastore file given the path as a string. The datastore file does not need to exist."
    )
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    filepath = InputSocket(
        datatype=String,
        name="File Path",
        description="The file path to resolve. This may be in the form of an absolute path (e.g. '/vmfs/volumes/<id>/path/to/file') or in the form of a datastore path (e.g. '[datastore] path/to/file')",
    )
    output = OutputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="A new 'DatastoreFile' object.")

    def run(self):
        self.output = esxi_utils.DatastoreFile.parse(self.esxi_client, self.filepath)


class EsxiDatastoreFileStat(Node):
    name: str = "ESXi DatastoreFile Stat"
    description: str = "Information on this file or directory. Outputs the size and whether this DatastoreFile object is a file or not. Raises a 'DatastoreFileNotFoundError' exception if this file does not exist"
    categories: typing.List[str] = ["ESXi", "Datastore", "DatastoreFile"]
    color: str = esxi_constants.COLOR_DATASTORE_FILE

    datastoreFile = InputSocket(datatype=datatypes.DatastoreFile, name="DatastoreFile", description="The DatastoreFile to use.")

    size = OutputSocket(datatype=Number, name="Size", description="The Size of the Datastore File saved in the Datastore.")
    isfile = OutputSocket(datatype=Boolean, name="Is File?", description="Whether this is a file or not.")

    def run(self):
        result = self.datastoreFile.stat
        self.size = result["size"] if "size" in result else -1
        self.isfile = result["isfile"] if "isfile" in result else ""


class EsxiDatastoreExists(Node):
    name: str = "ESXi Datastore Exists"
    description: str = "Outputs True if the queried datastore name exists."
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    name_value = InputSocket(datatype=String, name="Datastore Name", description="The name of the Datastore to search for.")
    exists = OutputSocket(Boolean, name="Exists?", description="True if the object exists on this client.")

    def run(self):
        self.exists = self.esxi_client.datastores.exists(self.name_value)


class EsxiDatastoreNames(Node):
    name: str = "ESXi Datastore Names"
    description: str = "Outputs the name of every datastore on this client"
    categories: typing.List[str] = ["ESXi", "Datastore"]
    color: str = esxi_constants.COLOR_CLIENT

    esxi_client = InputSocket(datatype=datatypes.ESXiClient, name="ESXi Client", description="The ESXi client to use.")
    the_names = ListOutputSocket(datatype=String, name="Names", description="The names of of every datastore on this client")

    def run(self):
        self.the_names = self.esxi_client.datastores.names
