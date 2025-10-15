from graphex import Boolean, String, Number, Node, InputSocket, OutputSocket, ListOutputSocket, OptionalInputSocket, LinkOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes
from graphex_esxi_utils.utils import misc as misc_utils
import typing
import re


class EsxiVirtualMachineToolsRunning(Node):
    name: str = "ESXi VM Tools Running"
    description: str = "Whether or not this Virtual Machine has guest tools running."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    output = OutputSocket(datatype=Boolean, name="Running?", description="Whether or not this Virtual Machine has guest tools running.")

    def run(self):
        self.output = self.vm.tools.running


class EsxiVirtualMachineToolsWait(Node):
    name: str = "ESXi VM Wait for Guest Tools"
    description: str = "Wait for the guest tools to be in the running state."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    retries = InputSocket(datatype=Number, name="Retries", description="How many times to retry before exiting / continuing.", input_field=120)
    delay = InputSocket(datatype=Number, name="Delay", description="How long to pause between retries (in seconds).", input_field=2)

    output = OutputSocket(
        datatype=Boolean,
        name="Verified Running?",
        description="Whether or not this Virtual Machine has guest tools running. This value will  be 'False' if the tools still aren't available after running out of retries.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Waiting for Guest Tools to become available...")
        self.output = self.vm.tools.wait(retries=int(self.retries), delay=int(self.delay))
        if self.output:
            self.debug(f"Guest Tools available.")
        else:
            self.debug(f"Guest Tools not available.")


class EsxiVirtualMachineToolsReboot(Node):
    name: str = "ESXi VM Tools Reboot / Restart"
    description: str = "Perform an ESXi reboot of the VM (soft reboot)."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Soft Rebooting Virtual Machine...")
        self.vm.tools.reboot()


class EsxiVirtualMachineToolsShutdown(Node):
    name: str = "ESXi VM Tools Shutdown"
    description: str = "Perform a clean shutdown of the VM."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Shutting Down Virtual Machine...")
        self.vm.tools.shutdown()


class EsxiVirtualMachineToolsIp(Node):
    name: str = "ESXi VM Tools Get IP"
    description: str = "Get the IP of this VM on a specific network, as reported by guest tools."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    network_name = InputSocket(datatype=String, name="Network Name", description="The name of the network to get the IP for.")

    output_ip = OutputSocket(datatype=String, name="IP", description="The IP if found. If no IP is found, this will be an empty string.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        result = self.vm.tools.ip(self.network_name)
        self.output_ip = result if result else ""
        self.debug(f"Virtual Machine IP: {self.output_ip}")


class EsxiVirtualMachineToolsNetworkNames(Node):
    name: str = "ESXi VM Tools Get Network Names"
    description: str = "Get the names of the networks for this VM, as reported by guest tools."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    network_names = ListOutputSocket(datatype=String, name="Networks", description="The names of each network connected to this VM.")

    def run(self):
        result = self.vm.tools.networks
        self.network_names = [x["network"] for x in result]


class EsxiVirtualMachineToolsNetworkInfo(Node):
    name: str = "ESXi VM Tools Get Network Info"
    description: str = "Gets the IP, MAC, and connection state of a network (if any of those are discoverable), as reported by guest tools."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    network_name = InputSocket(datatype=String, name="Network Name", description="The name of the network to get the IP for.")

    output_ip = OutputSocket(datatype=String, name="IP", description="The IP if found. If no IP is found, this will be an empty string.")
    mac = OutputSocket(datatype=String, name="MAC", description="The MAC Address if found. If no MAC is found, this will be an empty string.")
    connected = OutputSocket(datatype=Boolean, name="Connected?", description="Whether this network NIC reports connected or not.")

    def run(self):
        result = self.vm.tools.networks
        for listitem in result:
            if listitem["network"] == self.network_name:
                ip = self.vm.tools.ip(self.network_name)
                self.output_ip = ip if ip else ""
                self.mac = listitem["mac"] if "mac" in listitem else ""
                self.connected = listitem["connected"] if "connected" in listitem else ""
                return
        self.output_ip = ""
        self.mac = ""
        self.connected = False


class EsxiVirtualMachineToolsListFiles(Node):
    name: str = "ESXi VM Tools List Files"
    description: str = "List files and directories in the given filepath in the guest operating system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    filepath = InputSocket(datatype=String, name="File Path", description="The filepath to list.")

    output = ListOutputSocket(datatype=String, name="Files", description="A list of files and directories in the provided filepath")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.output = self.vm.tools.list_files(self.username, self.password, self.filepath)
        self.debug(f"Files in {self.filepath}: {str(self.output)[1:-1]}")


class EsxiVirtualMachineToolsExec(Node):
    name: str = "ESXi VM Tools Execute Program"
    description: str = "Runs a program in the guest operating system. This will block until the associated command has finished. The command should use the full path to the program, e.g. `/usr/bin/date` rather than `date`"
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    ## inputs
    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")

    username = InputSocket(datatype=String, name="Username", description="The username of the the user to login as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in.")

    cmd = InputSocket(
        datatype=String,
        name="Command",
        description="The command to run. This command should use the full path to the program, e.g. `/usr/bin/date` rather than `date`",
    )
    timeout = InputSocket(datatype=Number, name="Timeout", description="The command timeout in seconds. Set to 0 to disable timeout.", input_field=120)
    make_output_available = InputSocket(
        datatype=Boolean,
        name="Make Output Available?",
        description="Whether or not to attempt to make output available by running the command with stdout/stderr redirects. This may not work for all operating systems and is therefore left as an optional feature.",
        input_field=True,
    )
    cwd = OptionalInputSocket(
        datatype=String, name="CWD", description="The directory that the command should run in. By default: runs in the default Guest Tools directory."
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If `None`, no assertion is made and checking the status is left to the caller.",
    )
    ##

    # Outputs
    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="stderr", description="The stderr from the command response.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Executing command: {self.cmd}")
        cwd = self.cwd if self.cwd else None
        assert_status = int(self.assert_status) if self.assert_status is not None else None
        command_response = self.vm.tools.execute_program(
            username=self.username,
            password=self.password,
            command=self.cmd,
            cwd=cwd,
            timeout=int(self.timeout),
            assert_status=assert_status,
            make_output_available=self.make_output_available,
        )

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr
        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))


# TODO fix bug preventing 'get' of '/etc/os-release' (probably in esxi_utils itself)
class EsxiVirtualMachineToolsGetFile(Node):
    name: str = "ESXi VM Tools Get File"
    description: str = "Read the content of a file at the given filepath in the guest operating system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    filepath = InputSocket(datatype=String, name="File Path", description="The filepath to list.")
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use when reading the file", input_field="UTF-8")

    contents = OutputSocket(datatype=String, name="File Contents", description="The contents of the file in the specified encoding.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Reading file: {self.filepath}")
        # A list of all supported encodings can be found here: https://docs.python.org/3/library/codecs.html#encodings-and-unicode
        self.contents = self.vm.tools.get_file(username=self.username, password=self.password, filepath=self.filepath, encoding=self.encoding)
        self.debug(f"File contents for {self.filepath}:\n" + re.sub(r"^", "  │  ", str(self.contents), flags=re.MULTILINE))


class EsxiVirtualMachineToolsWriteFile(Node):
    name: str = "ESXi VM Tools Write File"
    description: str = "Write data to a file at the given filepath in the guest operating system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    filepath = InputSocket(datatype=String, name="File Path", description="The filepath to list.")
    file_data = InputSocket(datatype=String, name="Data", description="The String data to write to the file.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Writing file: {self.filepath}")
        self.debug(f"Writing to {self.filepath}:\n" + re.sub(r"^", "  │  ", self.file_data, flags=re.MULTILINE))
        self.vm.tools.write_file(username=self.username, password=self.password, filepath=self.filepath, data=self.file_data)


class EsxiVirtualMachineToolsUploadFile(Node):
    name: str = "ESXi VM Tools Upload File"
    description: str = (
        "Upload the file at the given filepath to the guest operating system. The file will be created if it does not exist, or overwritten if it does exist."
    )
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    filepath = InputSocket(datatype=String, name="File Path", description="The file path to upload.")
    dst = InputSocket(
        datatype=String,
        name="Destination",
        description="The destination file path to upload to on the guest operating system. This must be an exact filepath. The file will be created if it does not exist, or overwritten if it does exist.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Uploading file {self.filepath} to {self.dst}")
        with open(self.filepath, mode="rb") as f:
            self.vm.tools.write_file(username=self.username, password=self.password, filepath=self.filepath, data=f.read())


class EsxiVirtualMachineToolsRegexReplaceFile(Node):
    name: str = "ESXi VM Tools File Regex Replace"
    description: str = "Use Guest Tools to apply a regex substitution to a file remote end of this connection."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    path = InputSocket(datatype=String, name="File Path", description="The file path on the remote machine.")
    regex_string = InputSocket(datatype=String, name="Regex", description="The regex to apply to the string.")
    replacement = InputSocket(
        datatype=String,
        name="Replacement",
        description="The replacement string to replace regex matches with. \\g<number> will substitute in the substring matched by group 'number' (e.g., \\g<2> will reference and insert group 2). The backreference \\g<0> substitutes in the entire substring matched.",
    )
    encoding = InputSocket(datatype=String, name="Encoding", description="The encoding to use to read and write the file as a string.", input_field="UTF-8")
    num_replacements = InputSocket(
        datatype=Number,
        name="Maximum Replacements",
        description="The maximum number of replacements to make within the string. If 0, all matches will be replaced.",
        input_field=0,
    )
    multiline = InputSocket(
        datatype=Boolean,
        name="Multiline",
        description="When specified, the pattern character '^' matches at the beginning of the string and at the beginning of each line (immediately following each newline); and the pattern character '$' matches at the end of the string and at the end of each line (immediately preceding each newline).",
        input_field=True,
    )
    ignore_case = InputSocket(
        datatype=Boolean,
        name="Ignore Case",
        description="Perform case-insensitive matching; expressions like [A-Z] will also match lowercase letters.",
        input_field=False,
    )
    dot_all = InputSocket(
        datatype=Boolean,
        name="Dot-All",
        description="Make the '.' special character match any character at all, including a newline; without this flag, '.' will match anything except a newline.",
        input_field=False,
    )

    contents_before = OutputSocket(datatype=String, name="File Contents Before", description="The file contents before replacements.")
    contents_after = OutputSocket(datatype=String, name="File Contents After", description="The file contents after replacements.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Modifying file: {self.path}")

        escaped_replacement_string = self.replacement.replace("\n", "\\n")
        self.debug(f"{self.path}: Replacing regex {re.escape(self.regex_string)} with {escaped_replacement_string}")
        self.contents_before = str(self.vm.tools.get_file(username=self.username, password=self.password, filepath=self.path, encoding=self.encoding))

        flags = 0
        if self.multiline:
            flags = flags | re.MULTILINE
        if self.ignore_case:
            flags = flags | re.IGNORECASE
        if self.dot_all:
            flags = flags | re.DOTALL
        regex = re.compile(self.regex_string, flags=flags)

        self.contents_after = regex.sub(self.replacement, self.contents_before, count=0 if self.num_replacements <= 0 else int(self.num_replacements))
        self.vm.tools.write_file(username=self.username, password=self.password, filepath=self.path, data=self.contents_after)

        formatted_contents_before = re.sub(r"^", "  │  ", self.contents_before, flags=re.MULTILINE)
        formatted_contents_after = re.sub(r"^", "  │  ", self.contents_after, flags=re.MULTILINE)
        self.debug(f"Before Replacement:\n{formatted_contents_before}\n\nAfter Replacement:\n{formatted_contents_after}")


class EsxiVirtualMachineToolsDeleteFile(Node):
    name: str = "ESXi VM Tools Delete File"
    description: str = "Delete a file in the guest operating system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    filepath = InputSocket(datatype=String, name="File Path", description="The path to the file to delete.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Deleting file: {self.filepath}")
        self.output = self.vm.tools.delete_file(username=self.username, password=self.password, filepath=self.filepath)


class EsxiVirtualMachineToolsDeleteDirectory(Node):
    name: str = "ESXi VM Tools Delete Directory"
    description: str = "Delete a directory in the guest operating system."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    dirpath = InputSocket(datatype=String, name="Directory Path", description="The path to the directory to delete.")
    recursive = InputSocket(
        datatype=Boolean,
        name="Recursive?",
        description="If true, all subdirectories are also deleted. If false, the directory must be empty for the operation to succeed.",
        input_field=False,
    )

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.log(f"Deleting directory (recursive={self.recursive}): {self.dirpath}")
        self.output = self.vm.tools.delete_directory(username=self.username, password=self.password, dirpath=self.dirpath, recursive=self.recursive)


class EsxiVirtualMachineToolsCreateTempFile(Node):
    name: str = "ESXi VM Tools Create Temporary File"
    description: str = "Creates a new unique temporary file for the user to use as needed. The user is responsible for removing it when it is no longer needed. A guest-specific location will be used."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    extension = InputSocket(datatype=String, name="File Extension", description="The extension to give to the new temporary file.")

    output = OutputSocket(datatype=String, name="File Path", description="The absolute file path to the created temporary file.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f'Creating temporary file with extension "{self.extension}"')
        self.output = self.vm.tools.create_temporary_file(username=self.username, password=self.password, extension=self.extension)
        self.debug(f"Temporary file: {self.output}")


class EsxiVirtualMachineToolsUseTempFile(Node, include_forward_link=False):
    name: str = "ESXi VM Tools Use Temporary File"
    description: str = "Creates a new unique temporary file for the user to use as needed, and delete the file after the corresponding branch completes. A guest-specific location will be used."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    extension = InputSocket(datatype=String, name="File Extension", description="The extension to give to the new temporary file.")

    tempfile_branch = LinkOutputSocket(
        name="Use Temporary File",
        description="The branch of execution making use of the temporary file. The temporary file will be removed when this branch completes.",
    )
    tempfile = OutputSocket(datatype=String, name="Temporary File", description="The absolute path to the created temporary file.")
    continue_branch = LinkOutputSocket(name="Continue", description="The branch of execution to continue to graph after making use of the temporary file.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f'Creating temporary file with extension "{self.extension}"')
        with self.vm.tools.use_temporary_file(username=self.username, password=self.password, extension=self.extension) as path:
            self.debug(f"Temporary file: {path}")
            self.tempfile = path

            # Continue down the 'Use Temporary File' line
            for node in self.forward("Use Temporary File"):
                self._runtime.execute_node(node)

        self.debug(f"Removing temporary file: {path}")

    def run_next(self):
        for node in self.forward("Continue"):
            self._runtime.execute_node(node)


class EsxiVirtualMachineToolsCreateTempDirectory(Node):
    name: str = "ESXi VM Tools Create Temporary Directory"
    description: str = "Creates a new unique temporary directory for the user to use as needed. The user is responsible for removing it when it is no longer needed. A guest-specific location will be used."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    prefix = OptionalInputSocket(datatype=String, name="Prefix", description="The prefix to give to the new temporary directory.")
    suffix = OptionalInputSocket(datatype=String, name="Suffix", description="The suffix to give to the new temporary directory.")

    output = OutputSocket(datatype=String, name="Directory Path", description="The absolute path to the created temporary directory.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Creating temporary directory")
        self.output = self.vm.tools.create_temporary_directory(
            username=self.username, password=self.password, prefix=self.prefix or "", suffix=self.suffix or ""
        )
        self.debug(f"Temporary directory: {self.output}")


class EsxiVirtualMachineToolsUseTempDirectory(Node, include_forward_link=False):
    name: str = "ESXi VM Tools Use Temporary Directory"
    description: str = "Creates a new unique temporary directory for the user to use as needed, and delete the directory (and all contents) after the corresponding branch completes. A guest-specific location will be used."
    categories: typing.List[str] = ["ESXi", "Virtual Machine", "Guest Tools"]
    color: str = esxi_constants.COLOR_VM

    vm = InputSocket(datatype=datatypes.VirtualMachine, name="Virtual Machine", description="The Virtual Machine to use.")
    username = InputSocket(datatype=String, name="Username", description="The username of the virutal machine user.")
    password = InputSocket(datatype=String, name="Password", description="The password of the virtual machine user.")
    prefix = OptionalInputSocket(datatype=String, name="Prefix", description="The prefix to give to the new temporary directory.")
    suffix = OptionalInputSocket(datatype=String, name="Suffix", description="The suffix to give to the new temporary directory.")

    tempdir_branch = LinkOutputSocket(
        name="Use Temporary Directory",
        description="The branch of execution making use of the temporary directory. The temporary directory will be removed when this branch completes, along with all its contents.",
    )
    tempdir = OutputSocket(datatype=String, name="Temporary Directory", description="The absolute path to the created temporary directory.")
    continue_branch = LinkOutputSocket(name="Continue", description="The branch of execution to continue to graph after making use of the temporary directory.")

    def log_prefix(self):
        return f"[{self.name} - {self.vm.name}] "

    def run(self):
        self.debug(f"Creating temporary directory")
        with self.vm.tools.use_temporary_directory(username=self.username, password=self.password, prefix=self.prefix or "", suffix=self.suffix or "") as path:
            self.debug(f"Temporary directory: {path}")
            self.tempdir = path

            # Continue down the 'Use Temporary Directory' line
            for node in self.forward("Use Temporary Directory"):
                self._runtime.execute_node(node)

            self.debug(f"Removing temporary directory: {path}")

    def run_next(self):
        for node in self.forward("Continue"):
            self._runtime.execute_node(node)
