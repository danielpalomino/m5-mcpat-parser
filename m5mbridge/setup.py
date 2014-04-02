''' Implementation of m5mbridge setup.

This file contains the internal setup of the m5mbridge. Use the public
interface in m5mbridge.entry to interface with the controller.

BUG:

For unknown reasons this code cannot be included into factory.py, because
importing the M5Module raises an ImportError exception when trying to import
the modules.m5.exporter.tree2datatable module. This happens only if we try to
import this module directly from entry.initM5MBridge(). If it is indirectly
imported via m5mbridge.__init__.py:getController() there is no such error. I
suspect that M5's custom import handler is causing this, because there is no
such issue if the code is run in the testbed environment.
'''

from os import path

import m5

from modules.hotspot.module import HotspotModule
from modules.m5.module import M5Module
from modules.mcpat.module import McPatModule
import factory

# A dictionary of all known modules for the m5mbridge controller and their
# respective names.
ALL_MODULES = dict(m5=M5Module, mcpat=McPatModule)

# Our singleton controller instance
controller = None
def getController(options = None):
    global controller
    if not controller:
        initM5MBridge(options)
    return controller

def initM5MBridge(options):
    global controller
    controller = factory.createController()
    controller.setOptions(options)
    registerModules(controller, options)

def registerModules(controller, options):
    # Split the colon separated list of modules to load. Remove emptry entries.
    toLoad = filter(len, options.modules.split(':'))

    if 'all' in toLoad:
        toLoad = ALL_MODULES.keys()

    for name in toLoad:
        ctor = ALL_MODULES[name]
        controller.registerModule(name, ctor())

__all__ = [ 'getController' ]
