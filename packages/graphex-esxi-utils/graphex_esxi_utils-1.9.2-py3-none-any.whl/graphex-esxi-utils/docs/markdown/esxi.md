# ESXi Category

There are over 400 nodes included in this plugin. This document will briefly go over the subcategories in which you can browse (or search) to find the functionality you are looking for in ESXi.

![The Subcategories for the ESXi Category](images/esxi_subcategories.png)

## Cast

For the most part, you can disregard the "Cast" category. It contains a collection of type casting nodes to convert the various objects included by this plugin package into other node types. Nodes in this category could be useful if you want a string or data container (JSON) representation of an object in this plugin.

## Client

The vast majority of the nodes in this category are for either: connecting to ESXi or getting a value out of the connection object (such as the Hostname of the ESXi client you are connected to). As mentioned in the "Getting Started" section of the main page, the "Connect to ESXi" node is usually your starting point for interfacing with ESXi.

If you are very experienced with ESXi, you might find use from the "ESXi Server Run Esxcli Command" node. This node lets you run commands that you normally have to SSH into the ESXi host in order to run.

## Datastore

The datastore category abstracts the datastore into two separate objects: "ESXi Datastore" and "ESXi Datastore File". Some common node operations available with the datastore are: getting information about capacity/free space of the datastore itself, retrieving 'Datastore File' objects from the store, getting all the VMs associated with a datastore, determining the storage type of the datastore, retrieving a specific datastore from the ESXi Client, and retrieving all datastores from the client.

Datastore File objects are located in their own subcategory underneath the 'Datastore' category. There are many, many operations available here, including (but not limited to): copying, checking existance, getting paths, joining, listing, making directories, merging, moving, registering VMs, deleting, stat-ing, downloading, uploading, reading and writing.

## Debugging

This category provides a single node: the "ESXi Connect Debug Logger". When this node is added to a GraphEx graph, it will enable more detailed debug logging from the ESXi Utilities *python* package. This python package is what this GraphEx plugin package uses 'underneath the hood' to enable interface with ESXi itself. These logs will show up in your terminal just like normal logging messages.

## Firewall

This category is used to interface with the ESXi firewall. In general you shouldn't need to use these nodes very often (if at all). Nodes functions categorized here include: modifying policies, rulesets, rule directions, ports, protocols, services, enabled/disabled, etc.

## Network

The Network category contains many subcategories because networking in ESXi can get fairly complicated. You will find many objects here representing different types of networks: various types of NICs (Network Interface Cards), portgroups (including distributed), temporary networks, and switches (including distributed).

![The available network categories](images/esxi_network.png)

### Physical NIC

Nodes categorized in this section include: checking the existance of physical NICs, getting driver names, MAC addresses, PCI Device strings, duplex status and link speeds, and 'up' status.

### Portgroup

There are a lot of nodes in here corresponding to portgroups, distributed portgroups, and ports contained on portgroups. It is important to note that this section doesn't contain any nodes for the creation of portgroups (see vSwitch), but instead contains many nodes to get objects related to portgroups and themselves or to remove portgroups. The ports on portgroups can have either: MAC address or connection 'type' retrieved from them.

### Temporary Network

Nodes in this subcategory specialize in standing up, finding, and tearing down temporary networks. These temporary networks setup both vSwitches and PortGroups so that you can configure VMs over a network and then quickly remove the networking components when you are done. The primary use case for the networks are in subnets where IPs are running out. For example, you could have multiple temporary networks where VMs in each individual network have the same IP.

### VMKernel NIC

Nodes related VM Kernel NICs are stored in here and you will not need them if you don't know what a VM Kernel NIC is.

### vSwitch

There are a lot of nodes in here corresponding to vSwitches and distributed switches. It is important to note that adding/creating both switches and port groups are handled from this category. Switches can also be removed using the "ESXi Remove vSwitch" node in this category.

## OVF

This category contains a collection of nodes for manipulating OVF files from inside GraphEx. Some operations available here are: loading OVF files from a path on the agent, creating manifests, getting values out of an OVF file, removing the OVF and associated files from the file system, removing configuration files, renaming associated files in bulk, setting config file values, validating OVF files, and rewriting OVFs to OVAs and vice versa.

## Virtual Machine

This is the largest category of nodes in this plugin and contains many subcategories:

![The many VM subcategories](images/vm_categories.png)

There are also nodes here under this category that don't fall into a particular subcategory. Some examples of the functions of these nodes are: cloning, creating, exporting, reloading, removing/deleting, reloading, and uploading virtual machines.

### Guest Tools

This subcategory contains nodes that can only be executed if 'VMWare Guest Tools Software' is installed on the VM. These tools can't be installed via any external tool and must be installed in any way recommended by VMWare. You can, however, use the "ESXi VM Tools Running" node to check if VM tools are available for use before attempting to use them. There is also a "ESXi VM Wait for Guest Tools" if you expect tools be installed on the VM and want to wait for them to become available (usually after a boot sequence).

There are 'generic' functions in here to help you setup your VM but there are also specific subcategories for the Operating Systems: Palo Alto, Unix, and Windows.

One extremely crucial usage for VM tools is in setting up IP configurations for freshly booted Operating Systems that have no network configuration set up. In these cases, VM tools should be your primary 'tool' in setting up an IP so that you can switch to a more reliable method (such as SSH). Should VM tools not be able in this situation, the final alternative is to use the 'screen capture' and 'keyboard' subcatgories together to create automation that reacts to changes in what the 'screen' of the VM sees.

### Hardware

This subcategory contains nodes that allow you to configure the hardware of a specific virtual machine. Basic examples include: setting number of cpus, cores per cpu, memory sizes, hard disk sizes and getting this information as well.

There are more subcategories contained within this one for 'Virtual Devices'. These are essentially devices that emulate things being 'plugged in' to the VM. Notable subcategories here are: CD ROM, Disk, Floppy, Video Card, and NIC (Not to be confused with the other types of NICs defined by ESXi).

### IP Management

There are three utility nodes in this category: "ESXi Find Available IP Address", "ESXi Generate Dynamic Networking ID", and "ESXi Get All Connected IP Addresses". The "ESXi Find Available IP Address" will retrieve an available IP address for you by quering the available ones as known by ESXi or by pinging for non-responsive IP. The "ESXi Get All Connected IP Addresses" will retrieve all currently occupied IP addresses as known by ESXi (no pinging). Finally, the "ESXi Generate Dynamic Networking ID" can be used to generate a random ID for use in assigning to networking objects, but has largely been replaced in usage by the nodes described in the 'Temporary Network' section above.

### Keyboard

The nodes in this subcategory let you send 'USB Scan Codes' to the virtual machine to emulate keyboard input to the machine. You can send individual keys or strings of characters (words, sentences) to the VM ("ESXi VM Press Key" and "ESXi VM Keyboard Write"). You can also send the exact keycode via hexidecimal if you wish to do so.

When you send individual hexidecimal scan codes, you can also attach a list of modifiers (alt, ctrl, etc.) to apply to the key you are attempting to press (which would emulate pressing somelike like ctrl+key). There is also a node, "ESXi VM Get USB Scan Code" which will convert the provided character into the proper keycode for you, so you can chain the output of that node into the Scan Code node with modifier. Here is an example that will send Ctrl+A to the VM:

![An example of how to apply a modifier to a key](images/vm_keyboard_input_example.png)

### OS Type

The nodes in this subcategory are used to help discern what Operating System a particular VM is running. You can retrieve a string containing the name of the OS or use a node such as "ESXi VM Operating System Is Linux" (which would output the Boolean 'True' if True).

### PAN-OS

The nodes in this subcategory are used for interacting with the Palo Alto API contained on PAN-OS VMs. One of the pilots (tests) of GraphEx included the automated building of Palo Alto firewalls. This category of nodes has been extensively tested in that GraphEx pilot and this wealth of nodes is now available for you to use when configuring Palo Alto VMs.

Similar to the "ESXi Client" or "SSH" connection objects, you must initiate a connection to the Palo Alto API on the VM in order to utilize the nodes in this category. You can then use the connection object as input into any of the nodes into this category, including the node that lets you call your own Palo Alto API commands ("ESXi PAN-OS API Exec"). You must close the API connection with the "ESXi Close PAN-OS API Connection" node when you are done:

![Example of some panos connection nodes](images/panos_api_nodes.png)

Please refer to the Palo Alto's documentation for the version of the VM you are using in order to determine what commands are available for execution (or use one of the prebuilt nodes provided by this plugin in this category).

### Power

Nodes in this subcategory are used to start, shutdown, reboot, check power status, and wait for power status on VMs. It is important to use the "ESXi Wait for VM Power State" ([as shown on the main page of this plugin documentation](index.md)) when you intend to perform operations on the same VM after the expected power state.

Note that the power operations in here are the 'hard' or 'force' options. If you were to go into the web UI for vSphere and shutdown a VM, the node included in this category would perform the same operation. If you want to perform a more graceful shutdown: look into the offerings of the VM tools category (e.g. "ESXi VM Tools Shutdown") or shutdown the VM over a connection node (such as SSH).

### Screen Capture

There are only two nodes in this category: "ESXi VM Capture Screen" and "ESXi VM Expect Screen". These nodes are used to setup VMs that can't be setup/controlled via VM tools nor remote connections. For instance, you use the "ESXi VM Expect Screen" node to wait for the VMs "screen" to match a previously captured picture of the screen. This functionality is usually pretty accurate when the 'screen' on the VM is simply a terminal with text. You can adjust the "match score" to fine tune how tolerable you want the differences between your stored image and the screen to be.

You can capture the current 'screen' on the VM by using the "ESXi VM Capture Screen" node. This is useful to save images for reuse in automating the "ESXi VM Expect Screen" node. Note that the "ESXi VM Expect Screen" node uses the same code 'under the hood' to capture the screen as the "ESXi VM Capture Screen" node. This helps eliminate any possible differences between the methods of screen capture between the saved image and the current screen.

### Snapshots

Nodes in this category are used to: create, list, remove, and revert snapshots. You can also get some information about the snapshots taken in the past on the provided VM.

### SSH -> Interactive

The nodes in this category are different from the SSH Connection nodes [as described in the document about remote connections.](remote.md). The nodes in this category go out of their way to completely emulate the way a user would open an SSH session (as opposed to how a machine would automate an SSH session using the protocol in python code). If you need the automation to explicitly use the 'ssh' command, use this subcategory. Otherwise, read the documentation on using the 'SSH Connection' object in the remote connections document and use that object instead.

Other than the difference in *how the connection is established*: you still open, execute, and close the connection in a similar way (using the appropriate nodes from this subcategory).


[Click here to return to the main page for the ESXi Utilities plugin](index.md)