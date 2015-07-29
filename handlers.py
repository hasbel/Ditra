# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
module containing the ditra handlers.

Ditra uses asyncore module for asynchronous IO handling. Each socket
is associated with a handler that inherits from the asyncore.dispatcher
class. BasicDispatcher is a wrapper around this class, and the Switch()
and Controller() handler-classes inherit from it.
"""

import asyncore
import socket

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
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.connect((address, port))
        self.buffer = []

    def handle_message(self, message):
        """Placeholder, to be overridden when inheriting"""
        print "[WARNING] No message handling implemented!"

    def handle_read(self):
        """receive, parse and pass packets to handle_message()"""
        packet = self.recv(8192)
        if packet == "":
            #print "[WARNING] Socket closed by remote host %s:%s" % (
            #    self.address,self.port)
            self.close()
            return
        packet_list = messages.separate_messages(packet)
        #received_types = " + ".join(
        #    messages.get_message_type(messages.parse(packet))
        #    for packet in packet_list)
        #print "From %s:%s received: " % (self.address, self.port), received_types
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
        #send_types = " + ".join(
        #    messages.get_message_type(message) for message in self.buffer)
        for message in self.buffer:
            if isinstance(message, str):
                self.send(message)
            else:
                self.send(message.pack())
        self.buffer = []
        #print "To %s:%s sent: " % (self.address, self.port), send_types

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
        self.giving_up = False
        ######### Evaluation ##########
        self.last_xid = 0
        self.first_received = False
        ###########################

    def handle_connect(self):
        """Called just before sending or receiving the first message

        This function is called by asyncore just before sending or
        receiving the first message. We use it to send the initial
        handshake messages
        """
        #print "Switch initiated on: %s:%s" % (self.address, self.port)
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
            #print "Switch on: %s:%s has the datapath ID: %s" % (
            #    self.address, self.port, self.dpid)
            if self.needs_migration:
                #print "Migrating switch..."
                self.handle_migration(message)
            else:
                self.activate_controller()
                self.controller.start_sending_to_switch()

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
            if (messages.get_message_type(message) == "OFPT_FLOW_REMOVED"
                and message.cookie == 1991):
                self.migrating = False
                self.controller.start_sending_to_switch()
                #print "Switch migration successfully completed!"
        else:
            self.buffer.append(messages.of_flow_add)
            self.migrating = True
            self.activate_controller()

    def handle_switch_give_up(self, message):
        """Function is called after receiving the flow_deleted msg"""
        # TODO: ADD timer and close
        if message.type == 11 and not self.giving_up:
            #print "giving up control"
            ########## Evaluation ######
            print "Switch migrated: ", self.last_xid
            ########################
            if self.buffer:
                self.handle_write()
            if self.controller.buffer:
                self.controller.handle_write()
            self.giving_up = True
        # Keep processing replies, they are not sent to other controllers.
        if message.type in [3, 6, 8, 19, 21, 23, 25]:
            self.controller.buffer.append(message)

    def activate_controller(self):
        """Function responsible for starting the controller channel"""
        if self.controller_address:
            #print "Activating controller..."
            self.controller = Controller(
                self.controller_address,
                self.proxy_address,
                self.migrating)
            self.controller.switch = self
        else:
            print "[WARNING] Controller undefined"

    def handle_message(self, message):
        # Still doing the initial handshake
        if not (self.hello_received and self.features_reply_received):
            self.handle_handshake(message)
        # Switch still being migrated
        elif self.migrating:
            self.handle_migration(message)
        # Should we give up control of switch?
        elif (messages.get_message_type(message) == "OFPT_FLOW_REMOVED"
              and message.cookie == 1991) or self.giving_up :
            # cookie 1991 is reserved for switch migration
            self.handle_switch_give_up(message)
        elif self.controller:
            ########### Evaluation #########
            self.last_xid = message.xid
            ############################
            self.controller.buffer.append(message)


class Controller(BasicDispatcher):
    """Controller handling functionality, understandable by asyncore"""
    def __init__(self, controller_address, proxy_address, needs_migration=False):
        BasicDispatcher.__init__(self, proxy_address)
        self.switch = None
        self.hello_received = False
        self.internal_switch_buffer = []
        self.needs_migration = needs_migration
        self.switch_active = False
        self.configure_proxy(controller_address)
        ######### Evaluation ##########
        self.first_received = False
        ###########################

    def configure_proxy(self, controller_address):
        """Tell the proxy to which controller we should be connected"""
        self.buffer.append(controller_address[0] + ":"
                           + str(controller_address[1]))

    def handle_connect(self):
        """Called just before sending or receiving the first message

        This function is called by asyncore just before sending or
        receiving the first message. We use it to send the initial
        handshake messages
        """
        #print "Controller initiated on: %s:%s" % (self.address, self.port)
        if not self.needs_migration:
            self.buffer.append(messages.of_hello)

    def start_sending_to_switch(self):
        """Start sending the buffered messages to the switch

        All messages received from the controller/proxy and internally
        buffered should be sent to the switch. all futures messages
        received from the controller/switch we be directly sent to the
        switch."""
        self.switch_active = True
        for message in self.internal_switch_buffer:
            self.switch.buffer.append(message)
        self.internal_switch_buffer = []

    def handle_message(self, message):
        if not self.hello_received:
            if messages.get_message_type(message) == "OFPT_HELLO":
                self.hello_received = True
                if self.needs_migration:
                    self.switch.buffer.append(messages.of_flow_delete)
        elif self.switch_active:
            #### Evaluation #######
            if self.needs_migration and not self.first_received:
                print "Controller migrated: ", message.xid
                self.first_received = True
            ####################
            for message in self.internal_switch_buffer:
                self.switch.buffer.append(message)
            self.switch.buffer.append(message)
        else:
            #### Evaluation #######
            if self.needs_migration and not self.first_received:
                print "Controller migrated: ", message.xid
                self.first_received = True
            ####################
            self.internal_switch_buffer.append(message)
