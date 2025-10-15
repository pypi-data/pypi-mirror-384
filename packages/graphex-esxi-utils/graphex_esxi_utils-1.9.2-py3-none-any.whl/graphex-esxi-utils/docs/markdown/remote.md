# Remote Connections

There are two types of remote connections that you can establish to VMs using the nodes provided by this plugin package: SSH and WinRM. Additionally, if you are attempting a connection to VM running a Unix or Cisco Operating System (OS), then there are additional functionalites available to you (as compared to the rather basic SSH offerings).

![the remote connection categories](images/esxi_remote_connections.png)

## SSH

![The SSH category](images/esxi_remote_ssh.png)

The SSH category is rather basic and is meant to be simple to use. You initialize an SSH connection using the "Open SSH Connection" node. You can then reuse the produced "SSH Connection" object over and over until you are finished with the connection. You feed "ESXi SSH Connection" objects into the "SSH: Execute Command" node in order to execute the command you provide. When you are done, you close the connection with the "Close SSH Connection" node.

Take for example this graph that executes "ls -la" on a remote machine with an IP of "1.2.3.4":

![A simple SSH example](images/esxi_ssh_remote_example.png)

Notice that you can chain the SSH connection object inbetween the nodes for easy reuse. This makes is possible to chain as many "SSH: Execute Commands" together as you want (without using variables). You can use the other output sockets on "SSH: Execute Command" to monitor the status code, stdout and stderr of the command that was just executed.

Another feature you might be interested in is quickly testing if an SSH connection is available. You can do this by unchecking (setting False) the box "Keep Connection Open" on the "Open SSH Connection" node.

### Specialized Unix and Cisco SSH Connections

If you drill down into either of these individual categories, you will see nodes that perform common SSH actions on these operating systems. For example, the Unix category has a node called "Unix SSH: List Files", which will perform an operation similar to "ls" for you on the remote system. Notice that since this node knows what to expect as output, it will produce a list of filenames for you instead of the more annoying stdout (that you would normally have to parse yourself):

![The unix ssh list files node](images/unix_ssh_ls.png)

You will also see nodes specific to opening SSH connections to these operating systems: "Open Unix SSH Connection" and "Open Cisco SSH Connection". It is recommended that you use these specific initializing nodes when you already know the operating system you will be executing commands on. Both of these nodes produce the same "ESXi SSH Connection" object as the normal "Open SSH Connection" node.

![the unix and cisco ssh connection nodes](images/unix_cisco_ssh.png)

If you plan to perform a command over SSH, I strongly suggest you read through your available options as prebuilt nodes first. This may save you the time and headache of graphing out a custom solution to your specific problem.

### Executing Bash Scripts

There are two different ways to execute scripts on your remote Unix VMs. You can provide a string to execute as a bash script using the "Unix SSH: Execute Bash Script" node or provde the path to a script to execute using the "Unix SSH: Execute Bash Command" node:

![The primary nodes for executing bash scripts](images/unix_bash.png)

In general, use the "Unix SSH: Execute Bash Script" node when you want to use a GraphEx string and have it be executed as a bash script on the remote machine. It there is already a script written on the remote machine (or you want to execute a single command), then use the "Unix SSH: Execute Bash Command" node and provide it the path to execute the script just like if you were on the CLI (e.g. ./my_script.sh).

$note$ Newer versions of this package have the node called 'Unix SSH: Execute Bash Command' whereas older versions have 'Unix SSH: Execute Command'. This change was made to help alleviate some of the confusion with the Execute Bash Script node being incorrectly used for both use cases.

### Breakdown of Inputs and Outputs on Execution Nodes

This section give a more detailed description of what all the options do on the 'Execute Command' nodes. These descriptions have been copied from the various hover texts available for the node: 'Unix SSH: Execute Command'.

- Node Description Itself: "Use an SSH connection to execute a command on the remote end of this connection. This will block until the associated command has finished. Only valid for connections to Unix-like hosts. You can respond to stdin requests using this node by specifying regexes to match (Stdin Regexes list) and send string responses to regex matches (Stdin Responses list). This regex to response relationship is one-to-one and each entry in one list assumes a cooresponding entry in the other list."

- "SSH Connection" Input: "A previously opened SSH connection object to execute over." (Opened via the cooresponding 'Open ... SSH Connection' node)

- "Command" Input: "The command to execute over SSH. You can also specify paths to bash scripts to execute (e.g. /home/username/myscript.sh). Please give the scripts the proper permissions before attempting with new scripts." (e.g. using the 'chmod' command on the script before attempting to execute it)

- "Timeout" Input: "The command timeout in seconds. An exception (error) will be raised if the timeout time is reached and all retries have been exhausted."

- "Retries" Input: "Number of times to retry the command on failure (based on 'Assert Status')."

- "PTY?" Input: "Run the command in a pseudoterminal. When set to True this node 'emulates' a human running the command in a physical terminal. When set to False: this node will use the SSH protocol but no 'terminal' will be asserted by the connection (signifies a machine doing SSH instead of a human). When running as 'sudo': this should be 'True'. If you aren't sure what to choose here: leave this set to 'True'. Note that pseudoterminals have limited access to stdout/stderr and you will get better results from those output sockets if you set this to 'False'."

- "CWD" Input: "The directory that the command should run in. By default: runs in the default directory (e.g. usually the home directory)."

- "Sudo Password" List Input: "Sudo password to use for answering sudo prompts. If not provided, the password used for the SSH connection will be used."

- "Stdin Regexes" List Input: "Regexes for matching the SSH output to determine when to send responses over stdin. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the responses in 'Stdin Responses'. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': The terminal will ask for the password the 'otheruser' in order to transfer the file. You would provide a string regular expression in this list that looks something like this: '.*password:'. This regex would then match when the terminal prompts for 'otheruser@somehostname's password:' and it would look at the list for 'Stdin Responses' to determine what response to send to the scp command."

- "Stdin Responses" Input: "Text to send over stdin when the corresponding regex is matched from 'Stdin Regexes'. This option sometimes requires that 'PTY?' is set to 'True'. This is one-to-one with the regexes in 'Stdin Regexes'. Please read the description for 'Stdin Regexes' above. For example, if you want to run the command: 'scp /home/user/myscript.bash' to otheruser@somehostname:~': In this list you would provide the password to respond with."

- "Assert Status" Input: "Assert that the command exits with a certain status number. If not value is provided, no assertion is made and checking the status is left to the caller."

- "Status Code" Output: "The exit status code from the commands execution."

- "Stdout" Output: "The stdout from the command response." (**NOTE:** Results may vary here when 'PTY?' is set to True)

- "Stderr" Output: "The stderr from the command response." (**NOTE:** Results may vary here when 'PTY?' is set to True)

- "SSH Connection" Output: "The SSH Connection (same as input). This maybe be used to 'chain' multiple SSH operations together."

## WinRM

Virtual Machines running the Windows Operating System can be connected to using WinRM connections. The nodes for WinRM are extremely similar to the "specialized" Unix and Cisco SSH connections discussed a little earlier on this page. You initiate a WinRM connection with the "Open WinRM Connection" node and you close it with the "Close WinRM Connection" node. There are a number of nodes for you to browse to perform common operations over WinRM in the 'WinRM' category.

Slightly different from the other connection node types, WinRM connections can either execute CMD (Command Prompt) or PowerShell commands:

![Common WinRM nodes](images/winrm_nodes.png)

Other than this slight difference, you can execute commands based off of "ESXi WinRM Connection" object instances in the same manners as the SSH nodes.


[Click here to return to the main page for the ESXi Utilities plugin](index.md)