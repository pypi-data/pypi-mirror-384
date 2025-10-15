from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, ListOutputSocket, OptionalInputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
import esxi_utils
import typing
import time
import os


class EsxiVirtualMachineToolsUnixBash(Node):
    name: str = "ESXi Unix VM Tools Execute Bash"
    description: str = "Runs a script in the guest operating system using bash. This will block until the associated command has finished. Unlike ``ESXi VM Tools Execute Program``, the command is executed as a standard bash script and thus the full path to programs do not need to be provided. Systems without bash will fail. ``command`` may also be provided as a script, with newlines separating the commands to be run. When executing a script already on the filesystem, avoid the tidle character '~' and explicitly provide the word 'sudo' (when needed) in front of the path in addition to checking the 'Sudo?' input on this node (e.g.: sudo /home/username/myscript.bash). If you are able to establish a connection to the VM via SSH, it is recommended you instead use one of the following nodes instead of this one: 'Unix SSH: Execute Bash Command' or 'Unix SSH: Execute Bash Script'. You can use the node 'Expand Home Path' to automatically expand the tilde '~' character for you."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    cmd = InputSocket(datatype=String, name="Command", description="The command to run (the full path to programs does not need to be provided).")
    sudo = InputSocket(
        datatype=Boolean,
        name="Sudo?",
        description="Whether to run the command with sudo. Provide a string to 'sudo password' to use a different password for sudo.",
        input_field=False,
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    cwd = OptionalInputSocket(
        datatype=String, name="CWD", description="The directory that the command should run in. By default: runs in the default directory."
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If `None`, no assertion is made and checking the status is left to the caller.",
    )
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    sudo_password = OptionalInputSocket(datatype=String, name="Sudo Password", description="An alternate password to use when 'Sudo?' is set to True.")
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Executing Bash command: {self.cmd}")
        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        cwd = self.cwd if self.cwd else None
        assert_status = int(self.assert_status) if self.assert_status is not None else None
        sudo_password = self.sudo_password if self.sudo_password else self.password
        sudo = sudo_password if self.sudo else False

        try:
            if self.bash_path:
                command_response = self.vm.tools.bash(
                    username=self.username,
                    password=self.password,
                    command=self.cmd,
                    cwd=cwd,
                    sudo=sudo,
                    timeout=int(self.timeout),
                    assert_status=assert_status,
                    bash_path=self.bash_path,
                )
            else:
                command_response = self.vm.tools.bash(
                    username=self.username, password=self.password, command=self.cmd, cwd=cwd, sudo=sudo, timeout=int(self.timeout), assert_status=assert_status
                )
        except Exception as e:
            self.logger.add_azure_build_tag('vmware-bash-failed')
            try:
                raise e
            except esxi_utils.util.exceptions.GuestToolsError as gte:
                if "process not found" in str(gte).lower():
                    raise exceptions.GuestToolsConnectionLost(str(gte))
                else:
                    raise e

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


class EsxiVirtualMachineToolsUnixStat(Node):
    name: str = "ESXi Unix VM Tools Stat"
    description: str = "Get information about a file."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    sudo = InputSocket(datatype=Boolean, name="Sudo?", description="Whether to run commands with sudo.", input_field=False)
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    sudo_password = OptionalInputSocket(datatype=String, name="Sudo Password", description="An alternate password to use when 'Sudo?' is set to True.")
    ##

    # Outputs
    # https://man7.org/linux/man-pages/man1/stat.1.html
    file_found = OutputSocket(
        datatype=Boolean,
        name="File Found?",
        description="Outputs True if the file was found by guest tools. False is the file was not found. If this value is 'False': then the other fields will be empty strings or -1",
    )
    o_name = OutputSocket(datatype=String, name="Name", description="The name of the file.")
    o_size = OutputSocket(datatype=Number, name="Size", description="The size of the file.")
    o_mode = OutputSocket(datatype=Number, name="Mode", description="The mode of the file.")
    o_isfile = OutputSocket(datatype=Boolean, name="Is File", description="Represents if this file object is a file.")
    o_isdir = OutputSocket(datatype=Boolean, name="Is Dir", description="Represents if this file object is a directory.")
    o_mtime = OutputSocket(datatype=Number, name="Last Modified", description="Represents the last time this file was modified.")
    o_atime = OutputSocket(datatype=Number, name="Last Accessed", description="Represents the last time this file was accessed.")
    o_gid = OutputSocket(datatype=Number, name="GID", description="The group ID of the file owner.")
    o_uid = OutputSocket(datatype=Number, name="UID", description="The user ID of the file owner.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Getting File Information: {self.path}")
        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        sudo_password = self.sudo_password if self.sudo_password else self.password
        sudo = sudo_password if self.sudo else False
        if self.bash_path:
            stat_d = self.vm.tools.stat(path=self.path, username=self.username, password=self.password, sudo=sudo, bash_path=self.bash_path)
        else:
            stat_d = self.vm.tools.stat(path=self.path, username=self.username, password=self.password, sudo=sudo)

        self.debug(f"File Information for {self.path}: {stat_d}")

        self.file_found = True if stat_d else False
        self.o_name = stat_d["name"] if stat_d else ""
        self.o_size = stat_d["size"] if stat_d else -1
        self.o_mode = stat_d["mode"] if stat_d else -1
        self.o_isfile = stat_d["isfile"] if stat_d else False
        self.o_isdir = stat_d["isdir"] if stat_d else False
        self.o_mtime = stat_d["mtime"] if stat_d else -1
        self.o_atime = stat_d["atime"] if stat_d else -1
        self.o_gid = stat_d["gid"] if stat_d else -1
        self.o_uid = stat_d["uid"] if stat_d else -1


class EsxiVirtualMachineToolsUnixIsFile(Node):
    name: str = "ESXi Unix VM Tools Path Is File"
    description: str = "Checks if the path exists and is a regular file."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    sudo = InputSocket(datatype=Boolean, name="Sudo?", description="Whether to run commands with sudo.", input_field=False)
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    sudo_password = OptionalInputSocket(datatype=String, name="Sudo Password", description="An alternate password to use when 'Sudo?' is set to True.")
    ##

    # Outputs
    o_isfile = OutputSocket(datatype=Boolean, name="Is File", description="Represents if this file object is a file (and exists).")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        sudo_password = self.sudo_password if self.sudo_password else self.password
        sudo = sudo_password if self.sudo else False
        if self.bash_path:
            isfile = self.vm.tools.isfile(path=self.path, username=self.username, password=self.password, sudo=sudo, bash_path=self.bash_path)
        else:
            isfile = self.vm.tools.isfile(path=self.path, username=self.username, password=self.password, sudo=sudo)

        self.o_isfile = isfile


class EsxiVirtualMachineToolsUnixIsDir(Node):
    name: str = "ESXi Unix VM Tools Path Is Directory"
    description: str = "Checks if the path exists and is a directory."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    path = InputSocket(datatype=String, name="Path", description="A path to a file or directory on the remote system.")
    sudo = InputSocket(datatype=Boolean, name="Sudo?", description="Whether to run commands with sudo.", input_field=False)
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    sudo_password = OptionalInputSocket(datatype=String, name="Sudo Password", description="An alternate password to use when 'Sudo?' is set to True.")
    ##

    # Outputs
    o_isdir = OutputSocket(datatype=Boolean, name="Is Directory", description="Represents if this file object is a directory (and exists).")

    def run(self):
        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        sudo_password = self.sudo_password if self.sudo_password else self.password
        sudo = sudo_password if self.sudo else False
        if self.bash_path:
            isdir = self.vm.tools.isdir(path=self.path, username=self.username, password=self.password, sudo=sudo, bash_path=self.bash_path)
        else:
            isdir = self.vm.tools.isdir(path=self.path, username=self.username, password=self.password, sudo=sudo)

        self.o_isdir = isdir


class EsxiVirtualMachineToolsUnixDownload(Node):
    name: str = "ESXi Unix VM Tools Download"
    description: str = "Download a file or directory from the remote system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
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
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    ##

    # Outputs
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

        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        start_time = time.perf_counter()
        if self.bash_path:
            downloaded_paths = self.vm.tools.download(
                path=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
                bash_path=self.bash_path,
            )
        else:
            downloaded_paths = self.vm.tools.download(
                path=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
            )
        self.o_local_paths = downloaded_paths
        self.debug(f"Finished downloading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")


class EsxiVirtualMachineToolsUnixUpload(Node):
    name: str = "ESXi Unix VM Tools Upload"
    description: str = "Upload a local file or directory to this path on the remote system. Warning: This function will load entire files into memory. Ensure that extremely large files are not uploaded using this method."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools", "Unix"]
    color: str = esxi_constants.COLOR_UNIX_VM

    ## inputs
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
    bash_path = OptionalInputSocket(datatype=String, name="Path to Bash", description="The path to the bash executable.")
    ##

    # Outputs
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

        assert isinstance(self.vm, esxi_utils.vm.LinuxVirtualMachine), "Not a LinuxVirtualMachine"
        start_time = time.perf_counter()
        if self.bash_path:
            remote_paths = self.vm.tools.upload(
                src=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
                bash_path=self.bash_path,
            )
        else:
            remote_paths = self.vm.tools.upload(
                src=self.path,
                dst=self.dst,
                username=self.username,
                password=self.password,
                directory_contents_only=self.directory_contents_only,
                overwrite=self.overwrite,
            )
        self.o_remote_paths = remote_paths
        self.debug(f"Finished uploading {log_string} after {round(time.perf_counter() - start_time, ndigits=1)} seconds.")
