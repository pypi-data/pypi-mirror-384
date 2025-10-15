import esxi_utils
import time
import typing
from graphex_esxi_utils import exceptions, panos_constants
from graphex_esxi_utils.utils import misc


def api_conn_refused(msg: str, check_for_credential_error: bool = True, raise_credential_error: bool = False) -> bool:
    """
    Check the API response for connection issues. These are typically ignored/interpretted as the VM 'not being ready yet' errors.
    :param msg:
        The message response from the VM (typically response.stdout)
    :param check_for_credential_error:
        When set to True, will check for 'Invalid Credentia' and return True if found
    :return:
        True if the API request was a connection problem, else: False
    """
    msg = msg.lower()
    if "gateway time-out" in msg or "connection refuse" in msg or "connection reset" in msg or "no route" in msg or "connection timed out" in msg:
        return True
    elif check_for_credential_error:
        if "invalid credentia" in msg or "403 reason" in msg:
            if raise_credential_error:
                raise exceptions.PaloAltoCredentialError(msg)
            else:
                return True
    return False


def wait_for_api_resp(
    api: esxi_utils.util.connect.PanosAPIConnection,
    api_cmd: str,
    logger_function: typing.Callable,
    timeout_time: float = 360,
    timeout_msg: str = "ERROR: timeout while waiting!",
    print_connection_error: bool = False,
):
    """
    Attempts the given api_cmd via the API in a loop until either a 'non-connection error' response is returned or a timeout occurs.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param api_cmd:
        the command to send through the API to execute
    :param logger_function:
        a reference to the logger function for printing connection failures to the terminal
    :param timeout_time:
        how long in seconds to wait before timing out (at least one attempt will be made regardless of this value)
    :param timeout_msg:
        what to print to the screen if a timeout occurs
    """
    # The time we started trying this API command
    start_time = time.time()
    # Loop until return or timeout
    while True:
        res = None
        try:
            # connect to the API
            res = api.exec(api_cmd)  # execute the command
            res_msg =  str(res.stdout)
            # if the connection was refused via message in the response: throw exception to be caught below
            if api_conn_refused(res_msg, raise_credential_error=True):
                if print_connection_error:
                    raise Exception(res.stdout)
                raise Exception()
            elif res.status > 0:
                logger_function(f"Bad status response from VM: {res.status} ... message: {res_msg} ... Retrying...")
                raise Exception()
            elif "invalid password" in res_msg.lower():
                raise Exception()
            # return the 'good' response
            return res
        # either the conn.exec command failed or we manually triggered this block by finding an error message in a response string
        except Exception as e:
            # if we have run out of 'retry' time, throw the timeout error
            if misc.timeout(start_time, timeout_time):
                raise exceptions.PaloAltoApiError(api_cmd, timeout_msg)
            elif res is not None and "invalid password" in str(res.stdout).lower():
                raise exceptions.PaloAltoApiError(api_cmd, f"ERROR: Invalid password provided to VM!: {res.stdout}")
            # else we sleep 10 seconds and try again
            logger_function("Failed to connect... retrying...")
            if print_connection_error:
                logger_function(str(e))
            time.sleep(10)

def get_license_info(
    api: esxi_utils.util.connect.PanosAPIConnection,
    logger_function: typing.Callable,
    exception_msg: str = "Failed to connect... retrying...",
    print_exception_res: bool = False,
    timeout: int = 8*60
) -> list:
    """
    Uses a built-in Palo Alto method to get a list of license information from the VM.
    Will attempt to retrieve the information for up to 8 minutes.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        a reference to the logger function for printing to the terminal
    :param exception_msg:
        the message to print when an exception is caught and ignored
    :param print_exception_res:
        when True: will print the response from the VM on each failed connection attempt (useful for debugging)
    :timeout:
        How long to atempt to get the license info before raising an error
    :return:
        A list of Python 'namedtuple' objects containing license information.
    """
    start_time = time.time()
    while True:
        try:
            list_res = api.get_license_info()
            return list_res
        except Exception as e:
            if misc.timeout(start_time, timeout):
                raise Exception("ERROR: timeout while waiting to get license info!: " + str(e))
            logger_function(exception_msg)
            if print_exception_res:
                logger_function("DEBUG: Response from VM:", str(e))
            time.sleep(10)


def check_software_versions(
    api: esxi_utils.util.connect.PanosAPIConnection, logger_function: typing.Callable,
):
    """
    Runs the 'op' command 'request system software check' via the Palo Alti API. Will wait for up to 8 minutes waiting for a connection.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        a reference to the logger function for printing to the terminal
    :return:
        the Response from the API for 'request system software check'
    """
    res = wait_for_api_resp(
        api=api,
        api_cmd="request system software check",
        timeout_time=8 * 60,  # 8 minutes
        timeout_msg="ERROR: timeout while waiting to check available system software versions!",
        logger_function=logger_function,
    )
    return res

def show_sys_info(api: esxi_utils.util.connect.PanosAPIConnection, logger_function: typing.Callable):
    """
    Runs the 'op' command 'show system info' via the Palo Alti API. Will wait for up to 8 minutes waiting for a connection.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        a reference to the logger function for printing to the terminal
    :return:
        the Response from the API for 'show system info'
    """
    res = wait_for_api_resp(
        api=api,
        api_cmd="show system info",
        timeout_time=8 * 60,  # 8 minutes
        timeout_msg="ERROR: timeout while waiting to get system info!",
        logger_function=logger_function
    )
    return res


def restart_vm(
    api: esxi_utils.util.connect.PanosAPIConnection,
    logger_function: typing.Callable,
    wait_for_boot: bool = True,
    timeout: int = 2*60,
    reboot_wait_time: int = 7*60,
    connect_wait_time: int = 20*60
) -> None:
    """
    Gracefully restarts the given vm instance. Uses the 'request restart system' command via the Palo Alto CLI.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        a reference to the logger function for printing to the terminal
    :param wait_for_boot:
        Waits 7 minutes for the VM to restart and be ready for interaction (when set to True (default))
    :param timeout:
        How long in seconds to wait before timing out (at least one attempt will be made regardless of this value)
    :param reboot_wait_time:
        How long in seconds to wait (before checking the VM) for the VM to reboot when 'wait_for_boot' is set to 'True'.
    :param connect_wait_time:
        How long in seconds to attempt to get a successful connection to the rebooted VM after the 'reboot_wait_time'. A timeout will be thrown if this value is reached.
    :return:
        the Response for 'show system info' if 'wait_for_boot' is set to True, else: the Response for 'request restart system'
    """
    start_time = time.time()
    connected = False
    res = None
    while not connected:
        try:
            res = api.exec("request restart system")
            logger_function("Reboot command issued.")
            connected = True
        except Exception:
            if res is not None and not api_conn_refused(str(res.stdout)):
                logger_function("WARN: Interrupted while trying to restart... assuming system went done for reboot...")
                connected = True
            elif misc.timeout(start_time, timeout):
                logger_function("WARN: Timeout while trying to restart the VM! Assuming the VM went down for reboot...")
                connected = True
            else:
                logger_function("Connection refused while trying to reboot... retrying...")
    if wait_for_boot:
        logger_function("Sleeping 7 minutes to wait for reboot...")
        time.sleep(reboot_wait_time)
        # loop until we can connect to the VM
        res = wait_for_api_resp(
            api=api,
            api_cmd="show system info",
            timeout_time=connect_wait_time,
            timeout_msg="ERROR: timeout while waiting to see if VM rebooted. Is the VM on?",
            logger_function=logger_function
        )


def get_software_version(api: esxi_utils.util.connect.PanosAPIConnection, logger_function: typing.Callable):
    """
    Parses out the 'show system info' command to find the software version of this VM.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        a reference to the logger function for printing to the terminal
    :return:
        the sofware version assigned to this VM (or None if this method fails). In rare cases, an error message may slip through and return instead.
    """
    # attempt to determine the version of software currently installed on the VM
    while True:
        try:
            res = show_sys_info(api=api, logger_function=logger_function)
            res_msg = str(res.stdout)
            if api_conn_refused(res_msg):
                logger_function("Connection refused... Retrying...")
                time.sleep(10)
                continue
            if "change your password" in res_msg:
                raise exceptions.PaloAltoVersionError(f"ERROR: VM requested password change. This should have been completed in an earlier stage!: {res}")
            elif "content-type" in res_msg:
                logger_function("Connection refused... Retrying...")
                time.sleep(10)
                continue
            try:
                sw_version = misc.extract_string_from_tag(res_msg, "<sw-version>", "</sw-version>")
                logger_function(f"VM is software version: {str(sw_version)}")
                if sw_version is None or sw_version == "unknown":
                    raise exceptions.PaloAltoVersionError(f"Couldn't determine software version currently installed!: {sw_version}")
                return sw_version
            except Exception as e:
                raise exceptions.PaloAltoVersionError(f"'sw-version' string not found in 'show system info' command!: {e}")
        except Exception as e:
            logger_function(f"WARNING: Failed to figure out what version is installed. Skipping check... Exception:\n {str(e)}")
            return None


def check_version(current_version: str, requested_version: str, logger_function_error: typing.Callable):
    """
    Compares the currently installed software version with the version requested for install.
    :param current_version:
        the version currently installed on this vm
    :param requested_version:
        the version that is trying to be installed
    :param logger_function_error:
        a reference to the logger function for printing to the terminal

    :return:
    - 'equal' if the versions match exactly
    - 'valid' if the current version can be upgraded to the requested version
    - 'invalid' if the current version is higher than the requested version
    - 'unknown_z': When comparing versions in the format x.y.z, x and y are equal, but z cannot be calculated due to letters
    The 'z' value will be compared from both the beginning and the end before returning this string.
    - 'error' if the comparison throws an exception
    """
    EQUAL = "equal"
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN_Z = "unknown_z"
    ERROR = "error"
    if current_version == requested_version:
        return EQUAL
    try:
        # break out x.z.y to [x, y, z]
        current_version_l = current_version.split(".")
        requested_version_l = requested_version.split(".")
        # compare major versions
        current_major = int(current_version_l[0])
        requested_major = int(requested_version_l[0])
        # e.g. current 10, requested 9
        if current_major > requested_major:
            return INVALID
        # e.g. current 9, requested 10
        elif current_major < requested_major:
            return VALID
        # else:
        # e.g. current 10, requested 10
        current_y = int(current_version_l[1])
        requested_y = int(requested_version_l[1])
        # e.g. current 10.5, requested 10.1
        if current_y > requested_y:
            return INVALID
        # e.g. current 10.1, requested 10.5
        elif current_y < requested_y:
            return VALID
        # e.g. current 10.1, requested 10.1
        # else:
        try:
            current_z = int(current_version_l[2])
            requested_z = int(requested_version_l[2])
            # e.g. current 10.1.5, requested 10.1.1
            if current_z > requested_z:
                return INVALID
            # e.g. current 10.1.1, requested 10.1.5
            elif current_z < requested_z:
                return VALID
            # else:
            # this shouldn't happen (both strings should have evaluated equal at the beginning)
            return EQUAL
        # there are characters present in the string, try to remove them
        except ValueError:
            # grab version numbers from the string until you encounter a character
            current_z = misc.convert_string_to_int(current_version_l[2])
            requested_z = misc.convert_string_to_int(requested_version_l[2])
            # e.g. current 10.1.5, requested 10.1.1
            if current_z > requested_z:
                return INVALID
            # e.g. current 10.1.1, requested 10.1.5
            elif current_z < requested_z:
                return VALID
            # else:
            # the z values are equal after stripping characters
            # try backwards comparison
            current_z = misc.convert_string_to_int(current_version_l[2], False)
            requested_z = misc.convert_string_to_int(requested_version_l[2], False)
            if current_z > requested_z:
                return INVALID
            # e.g. current 10.1.1, requested 10.1.5
            elif current_z < requested_z:
                return VALID
            # something strange happened
            return UNKNOWN_Z
    except Exception as e:
        logger_function_error(f"ERROR: Was unable to determine version requirements: {str(e)}")
        return ERROR

def installing_wait_loop(
    software_name: str,
    job_number: str,
    api: esxi_utils.util.connect.PanosAPIConnection,
    logger_function: typing.Callable,
    msg_name: str = "software task",
    exit_on_fail: bool = True,
    return_res: bool = False,
    print_conn_refused: bool = False,
    timeout: int = 10*60
):
    """
    Wait for the software install to complete. Will periodically print the install status to the screen.
    :param software_name:
        Whatever you want to call the software you are waiting to install. (used in print messages)
    :param job_number:
        The job number you monitoring for completion.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param msg_name:
        A description of what type of task this is for logging
    :param exit_on_fail:
        Will return False from this function on failure instead of throwing an error.
    :param return_res:
        Will return the response from the 'show jobs id' task alongside the boolean
    :param print_conn_refused:
        Will print the response from the VM when a connection is refused
    :return:
        True if the wait loop completed. False if exit_on_fail was set to False and the procedure failed.
        OR the response from 'show jobs id' as a tuple of (job_failed_or_not, jobs_response_object)
    """
    installing = True
    start_time = time.time()
    res = None
    while installing:
        if misc.timeout(start_time, timeout):
            if res is not None:
                logger_function(f"VM Response before timeout error: {res}")
            raise exceptions.PaloAltoInstallError(f'ERROR: timeout while waiting for "{software_name}" {msg_name} install!')
        connected = False
        time.sleep(15)
        while not connected:
            try:
                res = api.exec(f'show jobs id "{job_number}"')
                connected = True
            except (
                Exception
            ):  # used to be esxi_utils.util.exceptions.RemoteConnectionCommandError, but then I ran into a http.client.RemoteDisconnected (from panos op command)
                logger_function("Failed to connect to check status... Retrying...")
                continue
        # end while not connected
        if str(res.stdout).find("<result>PEND</result>") < 0:  # job is no longer pending # type: ignore
            installing = False
            if str(res.stdout).find("<result>OK</result>") >= 0:  # type: ignore
                logger_function(f'"{software_name}" {msg_name} complete!')
            elif api_conn_refused(str(res.stdout)): # type: ignore
                installing = True
                logger_function("Connection refused while checking job completion status... retrying...")
                if print_conn_refused:
                    logger_function(f"Refused message: {str(res.stdout)}") # type: ignore
            elif not exit_on_fail:
                logger_function(f'The "{software_name}" {msg_name} failed!: VM Response: {res.stdout}') # type: ignore
                if return_res:
                    return False, res
                return False
            else:  # likely the result was FAIL
                raise exceptions.PaloAltoInstallError(f'The "{software_name}" {msg_name} failed!: {res}')
        else:  # job is still pending/installing
            try:
                p_find_str = "<progress>"
                p_i = res.stdout.find(p_find_str)  # type: ignore
                progress = res.stdout[p_i + len(p_find_str) : -1].strip() # type: ignore
                p_i = progress.find("<") # type: ignore
                progress = progress[0:p_i].strip()
                logger_function(f"Progress is at: {str(progress)}%")
            except Exception:
                pass  # a parsing error here isn't important enough to kill the hold procedure
    if return_res:
        return True, res
    return True


def parse_job_number(text: str, import_category: str, key: str = "software") -> str:
    """
    Parse the job number out of the response from the VM and return it as a string for future use.

    :param text:
        Response object returned after the 'install software' command was given to the VM.
    :param import_category:
        what 'kind' of software install this is (see import_category_dict)
    :param key:
        (optional) what kind of 'software' install this is (e.g. anti-virus) (prints in the exception if raised)
    :return:
        string containing the job number for this install.
    """
    find_str = "job enqueued with jobid"
    if import_category == panos_constants.COMMIT_JOB_KEY:
        find_str = "Commit job"
        if key == "software":
            key = find_str
    i = text.find(find_str)
    if i < 0 or len(text) - len(find_str) + 10 <= 0:
        raise exceptions.PaloAltoParsingError(f'ERROR: Unknown response from Palo Alto while trying to enqueue "{key}" task!: {text}')
    i = i + len(find_str)
    job_number: str = text[i : i + 10].strip()
    if import_category == panos_constants.SOFTWARE_KEY:
        i = job_number.find(".")
    elif import_category == panos_constants.COMMIT_JOB_KEY:
        i = job_number.find("is in progress", i - 1)
    else:
        i = job_number.find("<")
    job_number = job_number[0:i].strip()
    job_number = str(misc.convert_string_to_int(job_number))
    return job_number


def get_serial_no(api: esxi_utils.util.connect.PanosAPIConnection, logger_function: typing.Callable, timeout: int = 8*60) -> str:
    """
    Parses out the 'show system info' command to find the serial number of this VM.
    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param logger_function:
        the function to use to print output messages to
    :param timeout:
        How long to retry before raising a timeout error
    :return:
        the serial number assigned to this VM. Can be 'unknown'. In rare cases, an error message may slip through and return instead.
    """
    connected_to_api = False
    start_time_api = time.time()
    while not connected_to_api:
        res = show_sys_info(api=api, logger_function=logger_function)
        if not api_conn_refused(str(res.stdout), check_for_credential_error=True):
            connected_to_api = True
        elif misc.timeout(start_time_api, timeout):
            raise exceptions.PaloAltoApiError("show system info", "ERROR: timeout! Failed to connect to VM to get serial number!")
        else:
            logger_function("Failed to connect to Vm. Retrying...")
            time.sleep(10)
    # end while loop
    try:
        s = misc.extract_string_from_tag(str(res.stdout), "<serial>", "</serial>") # type: ignore
        return s
    except Exception as e:
        raise exceptions.PaloAltoParsingError(f"'serial' string not found in 'show system info' command: {str(e)}")
    # end of try except

def extract_license_filenames(license_res_list: list):
    """
    Extracts the 'feature', 'issued', and 'authcode' field from each namedTuple in the provided list.
    Parses and combines these fields to create the 'filename' Palo Alto assigns to each license on the VM.
    :param license_res_list:
        List provided by 'common_functions' -> 'get_license_info()'
    :return:
        List of extracted filenames
    """
    from datetime import datetime

    license_filenames = []
    if len(license_res_list) <= 0:
        return None
    for license_tuple in license_res_list:
        if len(license_tuple) < 7:
            raise exceptions.PaloAltoDelicenseError(
                f"ERROR: Not enough information about this license! Delete licenses manually! (Length of license tuple should be at least 7): {license_tuple}"
            )
        feature: str = license_tuple[0]
        issued: datetime = license_tuple[3]
        authcode: str = license_tuple[6]
        filename = feature.strip() + "_" + str(issued.strftime("%Y_%m_%d")).strip() + "_" + authcode.strip()
        filename = filename.replace(" ", "_") + ".key"
        license_filenames.append(filename)
    return license_filenames

def create_password_hash(api: esxi_utils.util.connect.PanosAPIConnection, username: str, password: str, logger_function: typing.Callable, timeout: int = 8*60):
    """
    Runs the 'op' command 'request password-hash...' via the Palo Alti API.

    :param api:
        An object representing the connection to the PaloAlto VM. Should contain _username, _password, and _ip
    :param username:
        the username to login as and request the password hash for
    :param password:
        the password for the username to login as and to hash.
    :param logger_function:
        the function to use to print output messages to
    :return:
        the Response from the API for 'request password-hash...'
    """
    res = wait_for_api_resp(
        api=api,
        api_cmd=f'request password-hash username "{username}" password "{password}"',
        timeout_time=timeout,
        timeout_msg="ERROR: timeout while waiting to get system info!",
        print_connection_error=True,
        logger_function=logger_function,
    )
    return misc.extract_string_from_tag(str(res.stdout), "<phash>", "</phash>")
