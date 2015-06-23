#!/usr/bin/env python

# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
Ditra is a distributed SDN translation module

This module is developed with the main goal of handling the OpenFlow
Translation functionality of an SDN hypervisor in a distributed way.
"""

import sys
import asyncore

import handlers

# ------------------ Configuration ------------------

SWITCHES = [("192.168.57.102", 6634, True)]
CONTROLLERS = [("192.168.57.1", 6633)]
MAP = {}

# ---------------------------------------------------

def main():
    """main function for initialising and starting ditra

    For each switch create a Switch() handler object, and for each
    controller create a Controller() handler object. assign each
    controller to it's corresponding switch and vice-versa. The last
    step is to start the asyncore loop
    """
    switch_handlers = []
    for switch_data in SWITCHES:
        switch_handlers.append(handlers.Switch(
            switch_data,
            controller_data=CONTROLLERS[0]))

    while True:
        asyncore.loop(use_poll=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Interrupted by user. (Ctrl-C)"
        sys.exit(1)
