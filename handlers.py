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
        if packet == "ha":
            return
        if packet == "":
            print "[WARNING] Socket closed by remote host!"
            self.close()
            return
        packet_list = messages.separate_messages(packet)
        received_types = " + ".join(
            messages.get_message_type(messages.parse(packet))
            for packet in packet_list) # todo
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
        must be a list of OFObjects
        """
        send_types = " + ".join(
            messages.get_message_type(message) for message in self.buffer) # todo
        for message in self.buffer:
            self.send(message.pack())
        self.buffer = []
        print "To %s:%s sent: " % (self.address, self.port), send_types

    def writable(self):
        return bool(self.buffer)


class Switch(BasicDispatcher):
    """Switch handling functionality, understandable by asyncore"""
    def __init__(self, (address, port, needs_migration), controller_data=None):
        BasicDispatcher.__init__(self, (address, port))
        self.hello_received = False
        self.features_reply_received = False
        self.needs_migration = needs_migration
        self.migrating = False
        self.dpid = ""
        self.controller_data = controller_data
        self.controller = None
        self.controller_active = False

    def activate_controller(self, migrating=False):
        if self.controller_data:
            print "Activating controller..."
            self.controller = Controller(self.controller_data, migrating)
            self.controller_active = True
            self.controller.add_switch(self)
        else:
            print "[WARNING] Controller undefined"

    def handle_handshake(self, message):
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
        if self.migrating:
            if messages.get_message_type(message) == "OFPT_FLOW_REMOVED":
                self.buffer.append(messages.of_master_role_request)
                # todo: wait for role reply, use xid to differentiate ?
            elif messages.get_message_type(message) == "OFPT_ROLE_REPLY":
            # todo: messages received before role reply might be lost
                self.migrating = False
                self.needs_migration = False
                print "Switch migration successfully completed!"
                time.sleep(0.2) # make sure the old controller got the message
        else:
            self.buffer.append(messages.of_flow_add)
            self.migrating = True
            self.activate_controller(migrating=True)

    def handle_connect(self):
        print "Switch initiated on: %s:%s" % (self.address, self.port)
        self.buffer.append(messages.of_hello)
        self.buffer.append(messages.of_features_request)
        self.buffer.append(messages.of_set_config)

    def handle_message(self, message):
        # Still doing the initial handshake
        if not (self.hello_received and self.features_reply_received):
            self.handle_handshake(message)
        # Switch still being migrated
        elif self.migrating:
            self.handle_migration(message)
        else:
            if messages.get_message_type(message) == "OFPT_FLOW_REMOVED":
                # cookie 1991 is reserved for switch migration
                if message.cookie == 1991:
                    print "giving up control"
                    self.close()
                    print "Handler for switch %s closed." % self.dpid
                    self.controller.close() # todo this should not be handled here
            if self.controller_active:
                self.controller.buffer.append(message)


class Controller(BasicDispatcher):
    """Controller handling functionality, understandable by asyncore"""
    def __init__(self, (address, port), needs_migration=False):
        BasicDispatcher.__init__(self, (address, port))
        self.switches = []
        self.hello_received = False
        self.internal_switch_buffer = []
        self.needs_migration = needs_migration
        self.ct_addr = "192.168.57.101"
        self.ct_port = 6633
        self.socket.setblocking(1)
        self.socket.send(self.ct_addr + ":" + str(self.ct_port))
        self.socket.setblocking(0)

    def handle_connect(self):
        print "Controller initiated on: %s:%s" % (self.address, self.port)
        if self.needs_migration:
            self.hello_received = True
        else:
            self.buffer.append(messages.of_hello)

    def add_switch(self, switch):
        self.switches.append(switch)
        for message in self.internal_switch_buffer:
            switch.buffer.append(message)
        self.internal_switch_buffer = []
        # todo: add a buffer for each switch ?

    def handle_message(self, message):
        if not self.hello_received:
            if messages.get_message_type(message) == "OFPT_HELLO":
                self.hello_received = True
        elif self.switches:
            for message in self.internal_switch_buffer:
                self.switches[0].buffer.append(message)
            self.switches[0].buffer.append(message) # todo: handle multiple switches
        else:
            self.internal_switch_buffer.append(message)
