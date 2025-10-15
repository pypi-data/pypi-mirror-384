class GraphexEsxiUtilsException(Exception):
    """Base class for all Graphex ESXi Utils exceptions."""

    pass


class EsxiConnectionFailedError(GraphexEsxiUtilsException):
    """
    Raised when an instance fails to connect to ESXi utils.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"Failed to open connection to ESXi server: {str(err_msg)}")


class EsxiObjectDoesNotExistError(GraphexEsxiUtilsException):
    """
    Raised when an object retrieval is attempted and fails because the object is 'None' or unassigned (doesn't exist)

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"ESXi Object doesn't exist: {str(err_msg)}")


class SSHExecutionError(GraphexEsxiUtilsException):
    """
    Raised when a command or script fails execution over SSH.

    :param msg: The error message.
    """

    def __init__(self, msg: str):
        super().__init__(str(msg))


class WinRMExecutionError(GraphexEsxiUtilsException):
    """
    Raised when a command or script fails execution over WinRM.

    :param msg: The error message.
    """

    def __init__(self, msg: str):
        super().__init__(str(msg))


class PanosApiExecutionError(GraphexEsxiUtilsException):
    """
    Raised when a command or script fails execution over the PAN-OS API.

    :param msg: The error message.
    """

    def __init__(self, msg: str):
        super().__init__(str(msg))


class PaloAltoApiError(GraphexEsxiUtilsException):
    """
    Raised the Palo Alto API fails a task.

    :param command: The command that failed to execute.
    :param err_msg: The error message.
    """

    def __init__(self, command: str, err_msg: str):
        super().__init__(f"Failed to execute command using Palo Alto API: '{str(command)}' ... error message: {str(err_msg)}")


class PaloAltoCredentialError(GraphexEsxiUtilsException):
    """
    Raised when invalid credentials are provided to a Palo Alto VM.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"ERROR: Invalid credentials provided to VM! ... error message: {str(err_msg)}")


class PaloAltoImportError(GraphexEsxiUtilsException):
    """
    Raised when a file fails to import into a Palo Alto VM.

    :file_type: The type of import that failed.
    :param err_msg: The error message.
    """

    def __init__(self, file_type: str, err_msg: str):
        super().__init__(f"ERROR: failed to import '{file_type}' file! ... error message: {str(err_msg)}")


class PaloAltoToolsExecError(GraphexEsxiUtilsException):
    """
    Raised the Palo Alto Guest Tools fails to execute a command.

    :param command: The command that failed to execute.
    :param err_msg: The error message.
    """

    def __init__(self, command: str, err_msg: str):
        super().__init__(f"Failed to execute command using Palo Alto Guest Tools: '{str(command)}' ... error message: {str(err_msg)}")


class PaloAltoSeriesError(GraphexEsxiUtilsException):
    """
    Raised when an invalid series string is provided when querying for a series of PanOS VM.

    :param invalid_series: The invalid string.
    :param valid_series: The valid series options.
    """

    def __init__(self, invalid_series: str, valid_series: str):
        super().__init__(f"ERROR: Provided PanOS series: '{invalid_series}' is not a known value. Valid options are: {str(valid_series)}")


class PaloAltoParsingError(GraphexEsxiUtilsException):
    """
    Raised when failing to parse out a response from a Palo Alto device.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"Failed to parse string!: {str(err_msg)}")


class PaloAltoVersionError(GraphexEsxiUtilsException):
    """
    Raised when failing to configure the version of a Palo Alto device.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"{str(err_msg)}")


class PaloAltoInstallError(GraphexEsxiUtilsException):
    """
    Raised when failing to install a software version on a Palo Alto device.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"{str(err_msg)}")


class PaloAltoDelicenseError(GraphexEsxiUtilsException):
    """
    Raised when failing to remove licenses from a Palo Alto device.

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"{str(err_msg)}")


class PaloAltoXmlConfigError(GraphexEsxiUtilsException):
    """
    Raised when something is wrong with a Palo Alto XML configuration file (linting or testing the application of it).

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"{str(err_msg)}")

class GuestToolsConnectionLost(GraphexEsxiUtilsException):
    """
    Raised when executing a command using guest tools and the connection was lost for any reason (e.g. reboot).

    :param err_msg: The error message.
    """

    def __init__(self, err_msg: str):
        super().__init__(f"Connection Lost to Guest Tools on the VM! Did your command reboot the machine? Verbose error message: {str(err_msg)}")
