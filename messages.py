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

    Gets a TCP packet that may contain multiple OpenFlow messages
    and separate it into smaller packets each containing exactly one
    OF message. returns a list.
    """
    packet_list = []
    while packet:
        of_length= struct.unpack("!H",packet[2:4])[0]
        of_message = packet[0:of_length]
        packet = packet[of_length:]
        packet_list.append(of_message)
    return packet_list

def parse(packet):
    """Parse a binary packet into a high level OFObjects

    Get a packet containing data in a binary format as received by
    the socket and returns the corresponding OFObject.
    """
    return of.message.parse_message(packet)

def get_message_type(message):
    """return a string representation of the OF type of message"""
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

of_flow_add = of.message.flow_add(
    xid=generate_xid(),
    cookie=1991, hard_timeout=1,
    flags=of.const.OFPFF_SEND_FLOW_REM,
    buffer_id=of.const.OFP_NO_BUFFER,
    out_port=of.const.OFPP_ANY,
    out_group=of.const.OFPG_ANY,
    match=of.match([of.oxm.in_port(1991),]),
    instructions=[])
