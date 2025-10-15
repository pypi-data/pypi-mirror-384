from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, OptionalInputSocket, ListOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex_esxi_utils.utils import misc as misc_utils
import esxi_utils
import typing
import time
import os
import re


class EsxiVirtualMachineToolsWindowsPowershell(Node):
    name: str = "ESXi Windows VM Tools Execute Powershell"
    description: str = "Runs a script in the guest operating system using powershell. This will block until the associated command has finished. Unlike ``execute_program``, the command is executed as a standard powershell script and thus the full path to programs do not need to be provided. Systems without powershell will fail. ``command`` may also be provided as a script, with newlines separating the commands to be run."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    cmd = InputSocket(datatype=String, name="Command", description="The command or script to run (the full path to programs does not need to be provided).")
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    cwd = OptionalInputSocket(
        datatype=String, name="CWD", description="The directory that the command should run in. By default: runs in the default directory."
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If `None`, no assertion is made and checking the status is left to the caller.",
    )
    powershell_path = OptionalInputSocket(datatype=String, name="Path to Powershell", description="The path to the powershell executable.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        cmd_log_str = self.cmd if "\n" not in self.cmd else "\n" + re.sub(r"^", "  │  ", self.cmd, flags=re.MULTILINE)
        self.log(f"Executing PowerShell: {cmd_log_str}")
        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"
        cwd = self.cwd if self.cwd else None
        assert_status = int(self.assert_status) if self.assert_status is not None else None
        if self.powershell_path:
            command_response = self.vm.tools.powershell(
                username=self.username,
                password=self.password,
                command=self.cmd,
                timeout=int(self.timeout),
                assert_status=assert_status,
                cwd=cwd,
                powershell_path=self.powershell_path,
            )
        else:
            command_response = self.vm.tools.powershell(
                username=self.username, password=self.password, command=self.cmd, timeout=int(self.timeout), assert_status=assert_status, cwd=cwd
            )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachineToolsUnixStat(Node):
    name: str = "ESXi Windows VM Tools Stat"
    description: str = "Get information about a file."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    powershell_path = OptionalInputSocket(datatype=String, name="Path to PowerShell", description="The path to the PowerShell executable, if not the default.")

    file_found = OutputSocket(
        datatype=Boolean,
        name="File Found?",
        description="Outputs True if the file was found by guest tools, or False is the file was not found. If this value is 'False', then the other fields will be empty strings or -1",
    )
    o_name = OutputSocket(datatype=String, name="Name", description="The name of the file.")
    o_fullname = OutputSocket(datatype=String, name="Absolute Path", description="The full name (absolute path) of the file.")
    o_isfile = OutputSocket(datatype=Boolean, name="Is File?", description="Whether this provided path is a file.")
    o_isdir = OutputSocket(datatype=Boolean, name="Is Directory?", description="Whether this provided path is a directory.")
    o_length = OutputSocket(datatype=Number, name="Length", description="Length of the file in bytes (this is 0 for directories).")
    o_mode = OutputSocket(datatype=String, name="Mode", description="The Mode string for this file.")
    o_createtime = OutputSocket(datatype=Number, name="Creation Time", description="The creation time of the file as second since Epoch.")
    o_lastaccesstime = OutputSocket(datatype=Number, name="Last Access Time", description="The last access time of the file as second since Epoch.")
    o_lastwritetime = OutputSocket(datatype=Number, name="Last Write Time", description="The last write time of the file as second since Epoch.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting File Information: {self.path}")
        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"

        if self.powershell_path:
            stat_d = self.vm.tools.stat(path=self.path, username=self.username, password=self.password, powershell_path=self.powershell_path)
        else:
            stat_d = self.vm.tools.stat(path=self.path, username=self.username, password=self.password)
        self.debug(f"File Information for {self.path}: {stat_d}")

        self.file_found = True if stat_d else False
        self.o_name = stat_d["Name"] if stat_d else ""
        self.o_fullname = stat_d["FullName"] if stat_d else ""
        self.o_isfile = stat_d["IsFile"] if stat_d else False
        self.o_isdir = stat_d["IsDirectory"] if stat_d else False
        self.o_length = stat_d["Length"] if stat_d else -1
        self.o_mode = stat_d["Mode"] if stat_d else ""
        self.o_createtime = stat_d["CreationTimeUtc"] if stat_d else -1
        self.o_lastaccesstime = stat_d["LastAccessTimeUtc"] if stat_d else -1
        self.o_lastwritetime = stat_d["LastWriteTimeUtc"] if stat_d else -1


class EsxiVirtualMachineToolsUnixIsFile(Node):
    name: str = "ESXi Windows VM Tools Path Is File"
    description: str = "Checks if the path exists and is a regular file."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    powershell_path = OptionalInputSocket(datatype=String, name="Path to PowerShell", description="The path to the PowerShell executable, if not the default.")

    o_isfile = OutputSocket(datatype=Boolean, name="Is File", description="Represents if this file object is a file (and exists).")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"
        if self.powershell_path:
            self.o_isfile = self.vm.tools.isfile(path=self.path, username=self.username, password=self.password, powershell_path=self.powershell_path)
        else:
            self.o_isfile = self.vm.tools.isfile(path=self.path, username=self.username, password=self.password)


class EsxiVirtualMachineToolsUnixIsDir(Node):
    name: str = "ESXi Windows VM Tools Path Is Directory"
    description: str = "Checks if the path exists and is a directory."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    powershell_path = OptionalInputSocket(datatype=String, name="Path to PowerShell", description="The path to the PowerShell executable, if not the default.")

    o_isdir = OutputSocket(datatype=Boolean, name="Is Directory", description="Represents if this file object is a directory (and exists).")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"
        if self.powershell_path:
            self.o_isdir = self.vm.tools.isdir(path=self.path, username=self.username, password=self.password, powershell_path=self.powershell_path)
        else:
            self.o_isdir = self.vm.tools.isdir(path=self.path, username=self.username, password=self.password)


class EsxiVirtualMachineToolsUnixDownload(Node):
    name: str = "ESXi Windows VM Tools Download"
    description: str = "Download a file or directory from the remote system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    path = InputSocket(datatype=String, name="Remote Path", description="Path to the file or directory on the remote system.")
    dst = InputSocket(datatype=String, name="Local Destination", description="The local destination file or directory to download to.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only?",
        description="If `True` and `path` points to a directory, then just the contents of the directory will be downloaded rather than the directory itself.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite Existing?", description="Whether to overwrite existing files.", input_field=False)
    powershell_path = OptionalInputSocket(datatype=String, name="Path to PowerShell", description="The path to the PowerShell executable, if not the default.")

    o_local_paths = ListOutputSocket(datatype=String, name="Local Paths", description="A list of local paths to all files downloaded.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        log_string = ""
        if self.directory_contents_only:
            log_string = f"{self.path} (contents) to {self.dst}"
        else:
            log_string = f"{self.path} to {self.dst}"

        self.log(f"Downloading {log_string}")

        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"
        start_time = time.perf_counter()
        if self.powershell_path:
            self.o_local_paths = self.vm.tools.download(
                path=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
                powershell_path=self.powershell_path,
            )
        else:
            self.o_local_paths = self.vm.tools.download(
                path=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
            )
        self.debug(f"Finished downloading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")


class EsxiVirtualMachineToolsUnixUpload(Node):
    name: str = "ESXi Windows VM Tools Upload"
    description: str = "Upload a local file or directory to this path on the remote system. Warning: This function will load entire files into memory. Ensure that extremely large files are not uploaded using this method."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Windows"]
    color: str = esxi_constants.COLOR_WINDOWS_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")
    path = InputSocket(datatype=String, name="Local Source", description="The local path to a file or directory to upload.")
    dst = InputSocket(datatype=String, name="Remote Destination", description="The remote path to upload to.")
    directory_contents_only = InputSocket(
        datatype=Boolean,
        name="Directory Contents Only?",
        description="If `True` and `path` points to a directory, then just the contents of the directory will be downloaded rather than the directory itself.",
        input_field=False,
    )
    overwrite = InputSocket(datatype=Boolean, name="Overwrite Existing?", description="Whether to overwrite existing files.", input_field=False)
    powershell_path = OptionalInputSocket(datatype=String, name="Path to PowerShell", description="The path to the PowerShell executable, if not the default.")

    o_remote_paths = ListOutputSocket(datatype=String, name="Remote Paths", description="A list of remote paths to all files uploaded.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        if not os.path.exists(self.path):
            raise RuntimeError(f"No such file or directory: {self.path}")

        log_string = ""
        if os.path.isdir(self.path) and not self.directory_contents_only:
            log_string = f"directory {self.path} to {self.dst}"
        elif os.path.isdir(self.path):
            log_string = f"directory (contents) {self.path} to {self.dst}"
        else:
            log_string = f"file {self.path} to {self.dst}"

        self.log(f"Uploading {log_string}")

        assert isinstance(self.vm, esxi_utils.vm.WindowsVirtualMachine), "Not a WindowsVirtualMachine"
        start_time = time.perf_counter()
        if self.powershell_path:
            self.o_remote_paths = self.vm.tools.upload(
                src=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
                powershell_path=self.powershell_path,
            )
        else:
            self.o_remote_paths = self.vm.tools.upload(
                src=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
            )
        self.debug(f"Finished uploading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")
