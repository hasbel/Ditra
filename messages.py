# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
This module wraps loxi to provide the functions and classes used by
ditra to generate and parse OpenFlow messages
"""

import random

import loxi
from loxi import of12 as of


def generate_xid():
    """Randomly generate a 64bits xid for OF messages"""
    return random.randrange(1,0xffffffff)

def parse(raw_message):
    """get a raw message buffer in, return a parsed message object"""
    return of.message.parse_message(raw_message)

def get_type(message):
    """Return the OF type of message"""
    if not isinstance(message, loxi.OFObject):
        message = parse(message)
    return of.const.ofp_type_map[message.type]

# OpenFlow messages

of_hello = of.message.hello(xid=generate_xid())
of_features_request = of.message.features_request(xid=generate_xid())
of_echo_reply = of.message.echo_reply(xid=generate_xid())
of_role_request = of.message.role_request(xid=generate_xid(),
                                          role=of.const.OFPCR_ROLE_MASTER)
of_set_config = of.message.set_config(xid=generate_xid(), miss_send_len=128)
