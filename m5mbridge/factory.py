from os import path

import m5

from controller import Controller
from modules.m5.importer import machinefactory
from modules.mcpat.exporter.prunetree import PruneChildrenForMcPatVisitor
from modules.mcpat.exporter.tree2mcpat import DefaultOutputFilter

def createController():
    return Controller()

def createMachine(controller):
    opts = controller.getOptions()
    m5configPath = path.join(m5.core.getOutputDir(), opts.config_fn)

    initRecorder(controller, opts)

    machine = machinefactory.createFromConfigFile(m5configPath, opts)
    machine.visit(PruneChildrenForMcPatVisitor(opts))
    machine.visit(DefaultOutputFilter(opts))
    controller.machine = machine
    controller.stateModified('machineCreated')

def initRecorder(controller, opts):
    '''Enable event recording.

    If event recording was enabled on the command line this function activates
    the event recorder.
    '''

    # len(opts.record) is greated than zero if recording is desired.
    if not opts.record:
        return

    logFile = path.join(m5.core.getOutputDir(), opts.record_file)

    # Multiple events are separated by a colon, we omit empty events cause
    # by, for example --record=:pat.
    events = filter(len, opts.record.split(':'))

    from controller.recorder import EventRecorder
    controller.registerModule('recorder', EventRecorder(events, logFile))
