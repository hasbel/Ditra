# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
This module wraps loxi to provide the functions and classes used by
ditra to generate and parse OpenFlow messages
"""

import random
import struct

from loxi import of12 as of


def generate_xid():
    """Return a randomly generated a 64bits xid for OF messages"""
    return random.randrange(1, 0xffffffff)

def separate_messages(packet):
    """Separate a TCP packet into smaller one-message packets

    Gets a TCP packet that may contain multiple aggregated OpenFlow
    messages and separate it into smaller packets each containing
    exactly one message. returns a list.
    """
    packet_list = []
    while packet:
        msg_length= struct.unpack("!H",packet[2:4])[0]
        message = packet[0:msg_length]
        packet = packet[msg_length:]
        packet_list.append(message)
    return packet_list

def parse(packet):
    """Parse a binary packet into a high level OFObjects

    Get a packet containing data of a single OF message in a binary
    format as received by the socket and returns the corresponding
    OFObject.
    """
    return of.message.parse_message(packet)

def get_message_type(message):
    """return a string representation of type of message

    If message is an OFObject , return a string representation of
    the OFtype of message. Message might also be a string, for example
    if we are doing the handshake with the proxy, in that case return
    the message itself.
    """
    if isinstance(message, str):
        return "'%s'" % message
    return of.const.ofp_type_map[message.type]

# OpenFlow messages

of_hello = of.message.hello(
    xid=generate_xid())

of_features_request = of.message.features_request(
    xid=generate_xid())

of_echo_reply = of.message.echo_reply(
    xid=generate_xid())

of_equal_role_request = of.message.role_request(
    xid=generate_xid(),
    role=of.const.OFPCR_ROLE_EQUAL)

of_master_role_request = of.message.role_request(
    xid=generate_xid(),
    role=of.const.OFPCR_ROLE_MASTER)

of_set_config = of.message.set_config(
    xid=generate_xid(),
    miss_send_len=128)

# FlowMod message to add the dummy flow
of_flow_add = of.message.flow_add(
    xid=generate_xid(),
    cookie=1991, hard_timeout=1,
    flags=of.const.OFPFF_SEND_FLOW_REM,
    buffer_id=of.const.OFP_NO_BUFFER,
    out_port=of.const.OFPP_ANY,
    out_group=of.const.OFPG_ANY,
    match=of.match([of.oxm.in_port(1991),]),
    instructions=[])

# FlowMod message to add the dummy flow
of_flow_delete = of.message.flow_delete(
    xid=generate_xid(),
    cookie=1991, hard_timeout=1,
    flags=of.const.OFPFF_SEND_FLOW_REM,
    buffer_id=of.const.OFP_NO_BUFFER,
    out_port=of.const.OFPP_ANY,
    out_group=of.const.OFPG_ANY,
    match=of.match([of.oxm.in_port(1991),]),
    instructions=[])
