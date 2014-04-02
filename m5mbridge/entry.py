'''
This file contains the entry-hooks into the m5mbridge from the M5 process.
'''

import m5
import m5.event
from m5.stats import registerDumpListener
from m5mbridge import getController
from m5mbridge.machine import options
import factory


useM5MBridge = False

def initM5MBridge(args):
    global useM5MBridge
    useM5MBridge = True

    opts = options.parse(fixArgs(args))

    # The first call to getController() creates the controller object and
    # registers all modules. It is important to create those objects before
    # the simulation is started, for example the M5Module needs to register
    # itself to the m5.stats module to get the usage data.
    controller = getController(opts)

    handleEventPlayback(controller, opts)

    registerDumpListener(dump)

def dump():
    global useM5MBridge
    if not useM5MBridge: return

    controller = getController()

    # Create the machine on the first dump call. At this point we can be sure
    # that the config.ini was written.
    if not controller.machine:
        factory.createMachine(controller)
        startTicker(controller)
    #controller.tick()
    # We import stats only if the M5 module is loaded, this is what users
    # probably expect when they exclude the m5module via the --modules command
    # line argument.
    if 'm5' in controller.modules:
        importStats(controller)

def importStats(controller):
    m5Module = controller.getModule('m5')
    controller.accessMachine(lambda c,m: (m5Module.importStats(m), c.stateModified('m5stats')))

def fixArgs(args):
    if any(arg.startswith('-c') or arg.startswith('--cpu_name') for arg in args):
        return args
    args.extend([ '--cpu_name', 'cpu' ])
    return args

def startTicker(controller):
    '''Start periodic calls to controller.tick().'''
    # Call controller.tick() periodically
    tickInterval = controller.getOptions().tick_interval
    TickEvent(m5.event.mainq, tickInterval)

class TickEvent(m5.event.Event):
    '''A periodic M5 event that invokes Controller.tick().

    For more information about M5 events see http://gem5.org/Events and the
    src/python/m5/events.py and src/python/swig/event.i files in the gem5
    project.
    '''
    def __init__(self, eventq, period):
        super(TickEvent, self).__init__()
        self.period = int(period)
        self.eventq = eventq
        self.eventq.schedule(self, m5.curTick() + self.period)

    def __call__(self):
        getController().tick()
        self.eventq.schedule(self, m5.curTick() + self.period)

def handleEventPlayback(controller, options):
    if not options.playback_file: return

    from controller import playback
    # Use all non-empty colon-separated words as event names.
    events = filter(len, options.playback.split(':'))

    offset = options.playback_offset or m5.curTick()

    # The scheduleRecordedEvents() function uses m5.ticks.fromSeconds() which
    # needs a fixed simulator frequency. Because this function is called early
    # during M5 initialization the frequency is not yet fixed by M5 itself.
    m5.ticks.fixGlobalFrequency()

    playback.scheduleRecordedEvents(m5.event.mainq, controller, options.playback_file, events, 1.0/options.playback_speed, offset)
