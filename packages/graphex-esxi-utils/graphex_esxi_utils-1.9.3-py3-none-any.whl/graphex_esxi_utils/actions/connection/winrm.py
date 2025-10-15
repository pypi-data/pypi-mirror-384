from graphex import Boolean, String, Number, DataContainer, Node, InputSocket, OptionalInputSocket, OutputSocket, ListOutputSocket, VariableOutputSocket
from graphex_esxi_utils import esxi_constants, datatypes, exceptions
from graphex_esxi_utils.utils import misc as misc_utils
import typing
import json
import re


class OpenWinRMConnection(Node):
    name: str = "Open WinRM Connection"
    description: str = "Open a WinRM connection to a host."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    ip = InputSocket(datatype=String, name="IP", description="The IP to connect to.")
    username = InputSocket(datatype=String, name="Username", description="The username of the user to login through WinRM as.")
    password = InputSocket(datatype=String, name="Password", description="The password for the user that is logging in via WinRM.")
    domain = OptionalInputSocket(datatype=String, name="Domain", description="The domain (if available) for the user.")
    transport = InputSocket(
        datatype=String, name="Transport", description="The transport to use for WinRM. Currently the only supported value is NTLM.", input_field="NTLM"
    )
    retries = InputSocket(datatype=Number, name="Retries", description="The maximum number of WinRM connection attempts to make.", input_field=10)
    delay = InputSocket(datatype=Number, name="Delay", description="The time to wait between each WinRM connection attempt.", input_field=5)
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when an WinRM connection could not be established.",
        input_field=True,
    )
    keep_open = InputSocket(
        datatype=Boolean,
        name="Keep Connection Open",
        description="Whether to keep the connection open so that a usable WinRM connection object is returned. If this is False, the 'WinRM Connection' output will be disabled.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Connection Available", description="Whether a connection could be established to the virtual machine.")
    connection = VariableOutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="A reusable WinRM connection to execute commands over. This is only available if this node succeeds and 'Keep Connection Open' is True.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.ip}] "

    def run(self):
        self.disable_output_socket("WinRM Connection")
        try:
            conn = datatypes.WinRMConnection.construct(self._runtime, self.log, self.debug, self.ip, self.username, self.password, self.retries, self.delay, self.keep_open, self.domain, self.transport)
            self.success = True
            # assigning a value to self.connection will re-enable it, so we only do that if the connection successfully connects
            self.connection = conn
        except RuntimeError as e:
            self.logger.add_azure_build_tag('winrm-connection-error')
            self.success = False
            if self.error_on_failure:
                raise e


class CloseWinRMConnection(Node):
    name: str = "Close WinRM Connection"
    description: str = "Close an open WinRM connection. The connection object will no longer be usable for WinRM operations. If the WinRM object is already closed, this will do nothing."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        if self.winrmobj._connection:
            self.debug(f"Closing connection.")
            self.winrmobj.close()


class WinRMPowershellExec(Node):
    name: str = "WinRM: Execute PowerShell Command"
    description: str = "Use an WinRM connection to execute a PowerShell command on the remote end of this connection. This will block until the associated command has finished."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    cmd = InputSocket(datatype=String, name="Command", description="The PowerShell command to execute over WinRM.")
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="Stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="Stderr", description="The stderr from the command response.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.winrmobj._ip}] "
        else:
            return f"[{self.name} - {self.winrmobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        self.log(f"Executing PowerShell command: {self.cmd}")
        command_response = self.winrmobj.powershell(self.cmd)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            self.logger.add_azure_build_tag('powershell-exec-failed')
            raise exceptions.WinRMExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        self.connection = self.winrmobj
        self.attempt = 0
        error = None
        while self.attempt < int(self.retries) + 1:
            try:
                self.run_attempt()
                return  # OK
            except Exception as e:
                error = e
            self.attempt += 1

        if error:
            raise error


class WinRMCMDExec(Node):
    name: str = "WinRM: Execute CMD Command"
    description: str = "Use an WinRM connection to execute a CMD (Windows Command Prompt) command on the remote end of this connection. This will block until the associated command has finished."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    cmd = InputSocket(datatype=String, name="Command", description="The CMD command to execute on the VM over WinRM.")
    retries = InputSocket(
        datatype=Number, name="Retries", description="Number of times to retry the command on failure (based on 'Assert Status').", input_field=0
    )
    assert_status = OptionalInputSocket(
        datatype=Number,
        name="Assert Status",
        description="Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller.",
        input_field=0,
    )

    status = OutputSocket(datatype=Number, name="Status Code", description="The exit status code from the commands execution.")
    stdout = OutputSocket(datatype=String, name="Stdout", description="The stdout from the command response.")
    stderr = OutputSocket(datatype=String, name="Stderr", description="The stderr from the command response.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    # State
    attempt: int = 0

    def log_prefix(self):
        if self.attempt == 0:
            return f"[{self.name} - {self.winrmobj._ip}] "
        else:
            return f"[{self.name} - {self.winrmobj._ip} (Attempt {self.attempt+1} of {int(self.retries)+1})] "

    def run_attempt(self):
        self.log(f"Executing CMD command: {self.cmd}")
        command_response = self.winrmobj.cmd(self.cmd)

        self.status = command_response.status
        self.stdout = command_response.stdout
        self.stderr = command_response.stderr

        if self.assert_status is not None and command_response.status != int(self.assert_status):
            # Bad status code
            s = f"Failed:\n" + misc_utils.get_response_debug_string(command_response)
            self.debug(s)
            self.logger.add_azure_build_tag('win-cmd-exec-failed')
            raise exceptions.WinRMExecutionError(s)

        self.debug(f"Results:\n" + misc_utils.get_response_debug_string(command_response))

    def run(self):
        self.connection = self.winrmobj
        self.attempt = 0
        error = None
        while self.attempt < int(self.retries) + 1:
            try:
                self.run_attempt()
                return  # OK
            except Exception as e:
                error = e
            self.attempt += 1

        if error:
            raise error


class WinRMIsFile(Node):
    name: str = "WinRM: Is File"
    description: str = "Use an WinRM connection to check if the given path points to a file."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to check on the remote system.")

    is_file = OutputSocket(
        datatype=Boolean, name="Is File", description="Whether the given path is a regular file. If the path does not exist, this will be False."
    )
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.debug(f"Checking file: {self.path}")
        self.is_file = self.winrmobj.isfile(self.path)


class WinRMIsDir(Node):
    name: str = "WinRM: Is Directory"
    description: str = "Use an WinRM connection to check if the given path points to a directory."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to check on the remote system.")

    is_directory = OutputSocket(
        datatype=Boolean, name="Is Directory", description="Whether the given path is a directory. If the path does not exist, this will be False."
    )
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.debug(f"Checking directory: {self.path}")
        self.is_directory = self.winrmobj.isdir(self.path)


class WinRMCreateFile(Node):
    name: str = "WinRM: Create File"
    description: str = "Use an WinRM connection to create a file on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to the file to create.")

    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Creating file: {self.path}")
        self.winrmobj.touch(self.path)


class WinRMCreateDirectory(Node):
    name: str = "WinRM: Create Directory"
    description: str = "Use an WinRM connection to create a directory on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to the directory to create.")
    parents = InputSocket(datatype=Boolean, name="Create Parents", description="Whether to create parent directories as needed.")

    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Creating directory (Parents={self.parents}): {self.path}")
        self.winrmobj.mkdir(self.path, parents=self.parents)


class WinRMDirectoryIsEmpty(Node):
    name: str = "WinRM: Directory Is Empty"
    description: str = "Use an WinRM connection to check whether a directory on the remote system is empty."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to the directory to check.")

    is_empty = OutputSocket(datatype=Boolean, name="Is Empty", description="Whether the given directory is empty.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.debug(f"Checking directory: {self.path}")
        self.is_empty = self.winrmobj.directory_is_empty(self.path)


class WinRMDeletePath(Node):
    name: str = "WinRM: Delete Path"
    description: str = "Use an WinRM connection to remove / delete a file or directory on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to the file or directory to delete.")
    recursive = InputSocket(
        datatype=Boolean,
        name="Recursive?",
        description="Whether or not the delete directories recursively (required to be True for removing directories).",
        input_field=True,
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when the file or directory is not successfully deleted (e.g. if the path was not found). If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in deleting the file or directory.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Deleting path (Recursive={self.recursive}): {self.path}")
        err = None
        try:
            self.winrmobj.rm(self.path, recursive=self.recursive)
        except Exception as e:
            err = e

        self.success = err is None
        if self.error_on_failure and err:
            raise err
        elif err:
            self.debug(f"Failed to delete {self.path}: {str(err)}")


class WinRMCopyPath(Node):
    name: str = "WinRM: Copy Path"
    description: str = "Use an WinRM connection to copy a file or directory to another path on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    src = InputSocket(
        datatype=String, name="Source Path", description="The path to the file or directory to copy on the remote system. File globs may be used."
    )
    dst = InputSocket(
        datatype=String, name="Destination Path", description="The path to copy to on the remote system. If the destination exists, it will be overwritten."
    )
    recursive = InputSocket(
        datatype=Boolean,
        name="Recursive?",
        description="Whether to copy directories and their contents recursively (required to be True for copying directories).",
        input_field=True,
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when the file or directory is not successfully copied (e.g. if the path was not found). If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in copying the file or directory.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Copying path (Recursive={self.recursive}) {self.src} to {self.dst}")
        err = None
        try:
            self.winrmobj.cp(src=self.src, dst=self.dst, recursive=self.recursive)
        except Exception as e:
            err = e

        self.success = err is None
        if self.error_on_failure and err:
            raise err
        elif err:
            self.debug(f"Failed to copy {self.src} to {self.dst}: {str(err)}")


class WinRMMovePath(Node):
    name: str = "WinRM: Move Path"
    description: str = "Use an WinRM connection to move a file or directory to another path on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    src = InputSocket(
        datatype=String, name="Source Path", description="The path to the file or directory to move on the remote system. File globs may be used."
    )
    dst = InputSocket(
        datatype=String, name="Destination Path", description="The path to move to on the remote system. If the destination exists, it will be overwritten."
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when the file or directory is not successfully moved (e.g. if the path was not found). If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in moving the file or directory.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Moving path {self.src} to {self.dst}")
        err = None
        try:
            self.winrmobj.mv(src=self.src, dst=self.dst)
        except Exception as e:
            err = e

        self.success = err is None
        if self.error_on_failure and err:
            raise err
        elif err:
            self.debug(f"Failed to move {self.src} to {self.dst}: {str(err)}")


class WinRMListFiles(Node):
    name: str = "WinRM: List Files"
    description: str = "Use an WinRM connection to list files and directories with a directory on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    path = InputSocket(datatype=String, name="Path", description="The path to the directory on the remote system to list the contents of.")

    contents = ListOutputSocket(datatype=String, name="Contents", description="The files and directories containing with the given path.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.debug(f"Listing files in {self.path}")
        self.contents = self.winrmobj.ls(self.path)
        self.debug(f"Contents of {self.path}: {str(self.contents)[1:-1]}")


class WinRMListPackages(Node):
    name: str = "WinRM: List Installed Packages"
    description: str = "Use an WinRM connection to list the packages installed on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    regex_filter = OptionalInputSocket(
        datatype=String,
        name="Regex Filter",
        description="The regex to use to filter packages. If provided and not empty, only packages matching this regex will be returned. Case will be ignored.",
    )

    packages = ListOutputSocket(
        datatype=String, name="Packages", description="The packages installed on the system (and, if 'Regex Filter' is provided, also matching the regex)."
    )
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.debug(f"Querying packages...")
        installed_packages = self.winrmobj.list_installed_packages()

        if self.regex_filter and self.regex_filter.strip():
            regex = re.compile(self.regex_filter.strip(), flags=re.IGNORECASE)
            installed_packages = [pkg for pkg in installed_packages if regex.search(pkg)]
            self.debug(f"Installed packages (Filter: {self.regex_filter.strip()}): {str(installed_packages)[1:-1]}")
        else:
            self.debug(f"Installed packages: {str(installed_packages)[1:-1]}")

        self.packages = installed_packages


class WinRMRemovePackage(Node):
    name: str = "WinRM: Uninstall Package"
    description: str = "Use an WinRM connection to uninstall (remove) a package installed on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    package = InputSocket(
        datatype=String,
        name="Package",
        description="The name of the package to remove. This name must match exactly to the name of the package as installed on the system.",
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when the package is not successfully removed or does not exist. If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in removing the package.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Removing package: {self.package}")
        err = None
        try:
            self.winrmobj.uninstall_package(self.package)
        except Exception as e:
            err = e

        self.success = err is None
        if self.error_on_failure and err:
            raise err

        if err:
            self.debug(f'Failed to remove package "{self.package}": {str(err)}')


class WinRMFindAndRemovePackages(Node):
    name: str = "WinRM: Find and Remove Packages"
    description: str = "Use an WinRM connection to find all packages matching a regex currently installed on the remote system and remove them."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    regex_filter = InputSocket(datatype=String, name="Regex Filter", description="The regex to use to find the packages to remove. Case will be ignored.")
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when a package is not successfully removed, or no matching packages are found. If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in removing the package(s).")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        regex = re.compile(self.regex_filter.strip(), flags=re.IGNORECASE)
        self.debug(f"Querying packages (Filter: {self.regex_filter.strip()})...")
        installed_packages = self.winrmobj.list_installed_packages()
        installed_packages = [pkg for pkg in installed_packages if regex.search(pkg)]

        errors = []
        if len(installed_packages) == 0:
            errors.append(RuntimeError(f"No packages matching: {self.regex_filter}"))

        for package in installed_packages:
            self.log(f"Removing package (Filter: {self.regex_filter.strip()}): {package}")
            try:
                self.winrmobj.uninstall_package(package)
            except Exception as e:
                errors.append(e)

        self.success = len(errors) == 0
        if len(errors) > 0:
            error_string = f'Failed to remove packages matching "{self.regex_filter}":\n' + "\n".join([str(err) for err in errors])
            if self.error_on_failure:
                raise RuntimeError(error_string)
            else:
                self.debug(error_string)


class WinRMStopProcess(Node):
    name: str = "WinRM: Stop Process"
    description: str = "Use an WinRM connection to stop a process on the remote system."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    process_name = InputSocket(
        datatype=String,
        name="Process Name",
        description="The name of the process to stop.",
    )
    error_on_failure = InputSocket(
        datatype=Boolean,
        name="Error on Failure?",
        description="Whether to raise an error when the process is not successfully stopped or does not exist. If False, no error will be raised.",
        input_field=True,
    )

    success = OutputSocket(datatype=Boolean, name="Success", description="Whether this node succeeded in stopping the process.")
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.connection = self.winrmobj
        self.log(f"Stopping process: {self.process_name}")
        err = None
        try:
            response = self.winrmobj.powershell(f"Get-Process -Name {self.process_name} | Stop-Process -Force", assert_status=0)
            self.debug(f"Results:\n" + misc_utils.get_response_debug_string(response))
        except Exception as e:
            err = e

        self.success = err is None
        if self.error_on_failure and err:
            raise err

        if err:
            self.debug(f'Failed to stop process "{self.process_name}": {str(err)}')


class WinRMRestart(Node):
    name: str = "WinRM: Restart Host"
    description: str = "Use an WinRM connection to trigger a graceful restart / reboot of the remote system. This will close the WinRM connection and a new connection will need to be established. This node will not wait for the remote system to be fully rebooted."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.log(f"Rebooting system...")
        self.winrmobj.restart()


class WinRMShutdown(Node):
    name: str = "WinRM: Shutdown Host"
    description: str = "Use an WinRM connection to trigger a graceful shutdown / power-off of the remote system. This will close the WinRM connection and a new connection will need to be established. This node will not wait for the remote system to be fully powered off."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.log(f"Shutting down system...")
        self.winrmobj.shutdown()


class WinRMGetADGroupInfo(Node):
    name: str = "WinRM: Get AD Group Info"
    description: str = "Use an WinRM connection to get information about an Active Directory group and its members. This will run and parse the 'Get-ADgroup' and 'Get-ADGroupMember' commands."
    categories: typing.List[str] = ["Remote Connections", "WinRM"]
    color: str = esxi_constants.COLOR_WINRM_CONNECTION

    winrmobj = InputSocket(
        datatype=datatypes.WinRMConnection, name="WinRM Connection", description="A previously opened WinRM connection object to execute over."
    )
    ad_group = InputSocket(datatype=String, name="AD Group Name", description="The name of the Active Directory Group.")

    ad_group_name = OutputSocket(
        datatype=String,
        name="Name",
        description="The Active Directory Group name.",
    )
    distinguished_names = ListOutputSocket(
        datatype=String,
        name="Distinguished Names",
        description="The Active Directory Group Distinguished Names.",
    )
    group_category = OutputSocket(
        datatype=String,
        name="Group Category",
        description="The Active Directory Group Category.",
    )
    group_scope = OutputSocket(
        datatype=String,
        name="Group Scope",
        description="The Active Directory Group Scope.",
    )
    members = ListOutputSocket(
        datatype=String,
        name="Group Members",
        description="The Active Directory Group Members (names only).",
    )
    data = OutputSocket(
        datatype=DataContainer,
        name="AD Group Info Object",
        description="The parsed Active Directory Group information.",
    )
    connection = OutputSocket(
        datatype=datatypes.WinRMConnection,
        name="WinRM Connection",
        description="The WinRM Connection (same as input). This maybe be used to 'chain' multiple WinRM operations together.",
    )

    def log_prefix(self):
        return f"[{self.name} - {self.winrmobj._ip}] "

    def run(self):
        self.log(f"Getting Information for Active Directory Group '{self.ad_group}'")
        self.connection = self.winrmobj

        self.data = self.winrmobj.get_AD_group(self.ad_group)
        self.debug(f"Result:\n" + re.sub("^", "  │  ", json.dumps(self.data, indent=2), flags=re.MULTILINE))

        self.ad_group_name = self.data["name"]
        self.distinguished_names = self.data["distinguished_name"]
        self.group_category = self.data["group_category"]
        self.group_scope = self.data["group_scope"]
        self.members = [member["name"] for member in self.data["members"]]
