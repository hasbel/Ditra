# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
module containing the ditra handlers
"""

import asyncore
import socket
import time

import messages


class BasicDispatcher(asyncore.dispatcher):
    """a parent class for switches and controllers to inherit from

    This class wraps the asyncore dispatcher class, and provides the
    handling functionality that is common to both switches and
    controllers. Both the controller and the switch classes inherit
    from this class.
    """
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((address, port))
        self.buffer = []

    def handle_message(self, message):
        """Placeholder, to be overridden when inheriting"""
        print "[WARNING] No message handling implemented!"

    def handle_read(self):
        """receive, parse and pass packets to handle_message()"""
        packet = self.recv(4096)
        if packet == "":
            print "[WARNING] Socket closed by remote host %s:%s" % (
                self.address,self.port)
            self.close()
            return
        packet_list = messages.separate_messages(packet)
        received_types = " + ".join(
            messages.get_message_type(messages.parse(packet))
            for packet in packet_list)
        print "From %s:%s received: " % (self.address, self.port), received_types
        # Process a single message at a time
        for packet in packet_list:
            message = messages.parse(packet)
            if messages.get_message_type(message) == "OFPT_ECHO_REQUEST":
                self.buffer.append(messages.of_echo_reply)
            else:
                self.handle_message(message)

    def handle_write(self):
        """Send the content of self.buffer on the socket, self.buffer
        must be a list and can contain either OFObjects or strings
        """
        send_types = " + ".join(
            messages.get_message_type(message) for message in self.buffer)
        for message in self.buffer:
            if isinstance(message, str):
                self.send(message)
                time.sleep(0.04) # to compensate for Nagel's algorithm
            else:
                self.send(message.pack())
        self.buffer = []
        print "To %s:%s sent: " % (self.address, self.port), send_types

    def writable(self):
        """Only send when there is something in the buffer"""
        return bool(self.buffer)


class Switch(BasicDispatcher):
    """Switch handling functionality, understandable by asyncore"""
    def __init__(self, address, proxy_address,
                 controller_address, needs_migration):
        BasicDispatcher.__init__(self, address)
        self.proxy_address = proxy_address
        self.controller_address = controller_address
        self.needs_migration = needs_migration
        self.dpid = ""
        self.controller = None
        self.hello_received = False
        self.features_reply_received = False
        self.migrating = False
        self.controller_active = False

    def handle_connect(self):
        """function called just after connecting to the switch

        This function is responsible for sending the initial handshake
        messages
        """
        print "Switch initiated on: %s:%s" % (self.address, self.port)
        self.buffer.append(messages.of_hello)
        self.buffer.append(messages.of_features_request)
        self.buffer.append(messages.of_set_config)

    def handle_handshake(self, message):
        """Handle all received messages until handshake is complete

        After handle_connect() initiates the handshake, we have
        to wait for the switch to send the hello and features_reply
        messages. After receiving these two messages we consider
        the handshake finished, and proceed to migrating the switch
        if needed or to activating the controller.
        """
        message_type = messages.get_message_type(message)
        if message_type == "OFPT_HELLO":
            self.hello_received = True
        if message_type == "OFPT_FEATURES_REPLY":
            self.features_reply_received = True
            self.dpid = message.datapath_id
        if self.features_reply_received and self.hello_received:
            print "Switch on: %s:%s has the datapath ID: %s" % (
                self.address, self.port, self.dpid)
            if self.needs_migration:
                print "Migrating switch..."
                self.handle_migration(message)
            else:
                self.activate_controller()

    def handle_migration(self, message):
        """Handle the process of taking over control of the switch

        Function is called if the switch needs to be migrated from
        an other instance of ditra.
        This function is responsible for sending the flow_add and
        waiting for the flow_removed message. The sending the the
        flow_delete messages is handled by the controller after
        successfully connecting to the proxy.
        """
        if self.migrating:
            if messages.get_message_type(message) == "OFPT_FLOW_REMOVED":
                # todo: use xid or match to differentiate? what if another flow removed occurs?
                self.migrating = False
                self.needs_migration = False
                print "Switch migration successfully completed!"
        else:
            self.buffer.append(messages.of_flow_add)
            self.migrating = True
            self.activate_controller()

    def handle_switch_give_up(self):
        """Function is called after receiving the flow_deleted msg"""
        print "giving up control"
        if self.buffer:
            self.handle_write()
        self.close()
        print "Handler for switch with dpid %s closed." % self.dpid
        if self.controller.buffer:
            self.controller.handle_write()
        self.controller.close()

    def activate_controller(self):
        """Function responsible for starting the controller channel"""
        if self.controller_address:
            print "Activating controller..."
            self.controller = Controller(
                self.controller_address,
                self.proxy_address,
                self.migrating)
            self.controller_active = True
            self.controller.add_switch(self)
        else:
            print "[WARNING] Controller undefined"
        # TODO: IF controller is activated it can start sending messages, is this ok?

    def handle_message(self, message):
        # Still doing the initial handshake
        if not (self.hello_received and self.features_reply_received):
            self.handle_handshake(message)
        # Switch still being migrated
        elif self.migrating:
            self.handle_migration(message)
        # Should we give up control of switch?
        elif (messages.get_message_type(message) == "OFPT_FLOW_REMOVED"
              and message.cookie == 1991):
            # cookie 1991 is reserved for switch migration
            self.handle_switch_give_up()
        elif self.controller_active:
            self.controller.buffer.append(message)


class Controller(BasicDispatcher):
    """Controller handling functionality, understandable by asyncore"""
    def __init__(self, controller_address, proxy_address, needs_migration=False):
        BasicDispatcher.__init__(self, proxy_address)
        self.switches = []
        self.hello_received = False
        self.internal_switch_buffer = []
        self.needs_migration = needs_migration
        self.buffer.append(controller_address[0] + ":" + str(controller_address[1]))

    def handle_connect(self):
        """Executed just after connecting to controller"""
        print "Controller initiated on: %s:%s" % (self.address, self.port)
        if self.needs_migration:
            self.hello_received = True
            self.switches[0].buffer.append(messages.of_flow_delete)
        else:
            self.buffer.append(messages.of_hello)

    def add_switch(self, switch):
        """Set the switch to which messages should be sent

        First, send the contents of the internal switch buffer to
        the switch. All futures messages received from controller
        should also be sent to the switch."""
        self.switches.append(switch)
        for message in self.internal_switch_buffer:
            switch.buffer.append(message)
        self.internal_switch_buffer = []

    def handle_message(self, message):
        if not self.hello_received:
            if messages.get_message_type(message) == "OFPT_HELLO":
                self.hello_received = True
        elif self.switches:
            for message in self.internal_switch_buffer:
                self.switches[0].buffer.append(message)
            self.switches[0].buffer.append(message)
        else:
            self.internal_switch_buffer.append(message)
