# Ditra: An SDN Hypervisor Module

Author : Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

### Design Goals

Ditra was designed a part of a dynamically distributed SDN virtualization layer. 
It works in conjunction with the SDN proxy module to allow for the dynamic 
migration of the OpenFlow control path in virtualized SDN networks.

Ditra has the ability to initiate the connection the a switch using it's listening port, 
it also implements a proposed protocol for the dynamic control path migration. 
It can thus contact the SDN proxy to initiate a controller connection migration, 
and can take over or give up control of the switch based on said protocol.

### Implementation Details

Ditra in currently divided in three different python modules. The module called 
ditra.py is the main module. It is where the hypervisor configuration is saved, 
and it is responsible for starting the hypervisor instance.

The module handlers.py implement the main logic behind ditra. It implement two 
classes called Switch() and Controller(). The Switch class is responsible for 
communication with the connected switches, while the class controller is responsible
for communication with the controllers (through the SDN proxy). For each controller
connection, a Controller() object is created. For each Switch connection, a Switch()
object is created.

The module messages.py is responsible for parsing and generating OF messages.
The current implementation is a wrapper around the Loxi library. It is currently 
using OF1.2, but could be changed to support any OF version supported by Loxi 
(i.e. 1.0 to 1.4).

### Current Limitations:

The current implementation does not support real virtualization functionality and 
only parses the received packets, checks if they have any significance to the 
migration process, and passes them to their destination (messages received from 
the switch are passed to the controller and vice versa).

For the purposes evaluating the protocol, all printing is currently out commented.

### Evaluation procedure:

The run Ditra using our SDN testbed (1 switch, 1 Proxy, 2 Ditras and 1 Controller).
follow the following steps:

1. Start all the 4 VMs: Controller-VM, Mininet-VM, Proxy-VM, and Ditra-VM. the
second Ditra instance will be run on the local host VM.
2. Make sure all the VM are connected to the same network and the local host 
machine is connected to that network
3. Make sure you have passwordless SSH access from your local host machine to
all VMs (using SSH keys)
4. Configure Ditra on both VM with te correct IP addresses of the switches, 
controllers, and SDN proxies. you also need to set the correct migration flags 
(i.e. Does a switch need migration or is contacted for the first time.)
5. Change the paths defined in the plot.py file to match your account.
6. Change the test.sh shell script present under tests to represent your setting 
(IP address and path might need to be changed)
7. Run the test.sh script. An Evaluation folder will be created in the location 
defined in the test.sh script. it will contain the captures and the plots.
