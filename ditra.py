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

switches = [("192.168.57.102", 9999)]
controllers = [("192.168.57.101", 6633)]
control_maps = []

# ---------------------------------------------------

def main():
    """main function for initialising and starting ditra

    For each switch create a Switch() handler object, and for each
    controller create a Controller() handler object. assign each
    controller to it's corresponding switch and vice-versa. The last
    step is to start the asyncore loop
    """
    switch_handlers = []
    for ip_port_pair in switches:
        switch_handlers.append(handlers.Switch(ip_port_pair))

    controller_handlers = []
    for ip_port_pair in controllers:
        controller_handlers.append(handlers.Controller(ip_port_pair))

    controller_handlers[0].set_switch(switch_handlers[0])
    switch_handlers[0].set_controller(controller_handlers[0])

    while True:
        asyncore.loop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Interrupted by user. (Ctrl-C)"
        sys.exit(1)
