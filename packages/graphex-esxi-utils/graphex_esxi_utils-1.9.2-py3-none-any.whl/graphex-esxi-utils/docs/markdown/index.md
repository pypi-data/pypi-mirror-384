# ESXi Utilities Documentation

Welcome to the ESXi Utilties plugin documentation for GraphEx. The nodes included in this plugin were created to interface with VMware ESXi hosts and virtual machines (VMs). The primary purpose of this plugin was to enable the automation of virtual machine configuration (and networking) from Graphex.

## About ESXi

You can read more about what ESXi is on [their own website](https://www.vmware.com/products/esxi-and-esx.html). This documentation assumes you are familar with VMware and ESXi. You will also need to execute your GraphEx graphs from a machine (which we commonly refer to as an 'agent') that has a connection to the ESXi host. More commonly, you will want to execute your GraphEx graphs from a virtual machine living on the ESXi host.

## Category Breakdown

When browsing available nodes from this plugin package, all nodes are contained under the categories "ESXi" and "Remote Connections":

![The categories installed by this plugin package](images/esxi_categories.png)

## Getting Started

The vast majority of the time you are going to need to connect to the ESXi host itself before performing any operation. This is the purpose of the "Connect to ESXi" node:

![The node that enables a connection to ESXi](images/esxi_connect.png)

This node outputs a "ESXi Client" object which can be used by various other nodes included in this plugin. One notable example being the retrieval of a specific VM from the ESXi environment.

If your ESXi host is connected in a vCenter configuration, you will have to fill out all of the input sockets with values. The host/master (parent) IP will be for the server that coordinates the hosts containing individual VMs. The Child's IP is then, for example, the IP of the server in which a VM lives on in which you want to access. Due to the partitioning of vCenter arrangements, it is not possible to access VMs living on child servers other than the one you specify. For example, if your master/parent IP is x.x.x.100 and you have three child servers connected to the master/parent as children: ...101, ...102, and ..103, then you can only connect to one of "101", "102", or "103" per "ESXi Client" object instance.

If your ESXi host is not connected in a vCenter configuration, then you only need to provide data to the first three input sockets (Host/Master IP, Username, and Password) in order to establish a connection.

All nodes from this ESXi Utilties plugin package will be prefixed with the name: "graphex-esxi-utils". You can see this in blue text at the bottom of each node description in the left-hand sidebar panel (see image above). Additionally, nodes from this package strive to include the word "ESXi" somewhere in the title of the node.

$note$ As seen in the above image, some nodes in this plugin enable you to save their output directly to a variable via a checkbox on the output socket. Notable examples at the time of this writing are: 'Connect to ESXi', 'Open SSH Connection' (any kind) and 'Open WinRM Connection'. Keep in mind that not all the images on these document pages are going to be updated just because a checkbox was added to the program. For more information on variables, please see the [core GraphEx documentation on the Sidebar Panel](../../ui/sidebar.html).

### Virtual Machine Example

A simple example of using this package would be to retrieve a Virtual Machine from the ESXi Client connection and perform some operation on it. In the image below, we retrieve a VM called "my_vm" from ESXi, power it off, wait for the vm to fully power off, and then export the VM to an OVF file on our agent:

![an example of using this plugin package](images/esxi_vm_example_export.png)

1. Using the "Connect to ESXi" node, a connection to a 'non-vCenter' host at IP 1.2.3.4 is attempted using the username: "username" and the password: "password". If unsuccessful, the node will throw an error and end the program. Note that it is recommended you make the "Password" field a graph input so that you can hide its content from others. This is described [in the vanilla GraphEx documentation under the sidebar panel page](../../ui/sidebar.html). The node then outputs a "ESXi Client" connection object instance.
2. The "Get ESXi VM" node then uses the ESXi Client connection in order to retrieve a VM called "my_vm" from the server. An error will be thrown and the program will exit if a VM with that name is not found on the server. This node outputs a "ESXi VM" object that represents the VM on the ESXi server.
3. The "ESXi Power Off Virtual Machine" node takes as input the VM and powers down the VM. This particular node shuts down the VM as if you powered it off from the vSphere UI. This is not the same as a shutdown using guest tools (see the "ESXi VM Tools Shutdown" node)
4. When we want to perform some follow-up action after a shutdown/power-off sequence, we can use the "ESXi Wait for VM Power State" node to wait for the VM to completely power off.
5. Finally, we use the "ESXi Export VM" to export/download the VM as an OVF file to our agent. The "Export Path" describes where on the agent to place the file. An "OVF File" object is also produced from the output socket should you want to perform operations on the file itself after export.

## ESXi Category

[Click here to go to the document providing a generic breakdown of the categories of nodes added by this plugin.](esxi.md)

## Remote Connections

Sometimes you only need an SSH or WinRM connection to complete the task you want to get done. [Click here to read about the remote connection objects offered by this plugin package.](remote.md)

## Keyboard Input

Included in this package is the ability emulate keyboard input. [Please see the dedicated page on keyboard input](keycodes.md) for more information on available key names and hexidecimal codes.