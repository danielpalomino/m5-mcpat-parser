'''Playback device for events recorded by the EventRecorder module.

This module reads a sequence of events 'pickled' by the EventRecorder module
and recreates the events as they happened originally. It is possible to play
them back in a time-accurate fashion using the time delay between the events as
recorded by the EventRecorder or to play them back with maximum throughput
ignoring the time delay between events. In any case the order of the events is
retained.

Because events typically create new events, for example an m5stats event
results eventually in a pat event, it is in some cases desirable to play back
only a subset of the recorded events. To recreate the original event chain it
typically suffices to play back the initial machineCreated event and all
m5stats events. All the other events are then recreated by the modules
registered to the m5mbridge controller.

Instead of filtering the events to play back it is also possible to filter the
events that the EventRecorder records. This has the benefit of a reduced file
size, but limits the freedom to play back different subsets of a recorded
sequence.
'''

PARTREF = 'all.controller.playback'

try:
    import cPickle as pickle
except:
    import pickle

from time import sleep, time

import m5

from m5mbridge import debug

def simplePlaybackDevice(logFile, events=['all'], options=None):
    '''Create a simple time-inaccurate playback device.

    A typical usage scenario:

    controller = m5mbridge.getController()
    for (event, machine) in simplePlaybackDevice('events.log'):
       controller.machine = machine
       controller.stateModified(event)
    '''
    f = openLogFile(logFile)
    debug.pp(PARTREF, 'Creating simple playback device <{0}, {1}>'.format(logFile, events))
    return SimplePlaybackDevice(f, events, options)

def timeAccuratePlaybackDevice(logFile, events=['all'], options=None):
    '''Create a time-accurate playback device.

    A typical usage scenario:

    controller = m5mbridge.getController()
    for (event, machine) in simplePlaybackDevice('events.log'):
       controller.machine = machine
       controller.stateModified(event)
    '''
    f = openLogFile(logFile)
    debug.pp(PARTREF, 'Creating time-accurate playback device <{0}, {1}>'.format(logFile, events))
    return TimeAccuratePlaybackDevice(f, events, options)

def scheduleRecordedEvents(eventq, controller, logFile, events=['all'], scalingFactor=1.0, tickOffset=m5.curTick()):
    '''Schedule recorded events.

    This function's `logFile', `events' and `options' parameters are the same
    as those of the timeAccuratePlaybackDevice() and simplePlaybackDevice()
    functions. The `options' parameter is read from `controller'.getOptions().

    The function schedules recorded events into the given eventqueue `eventq'.
    No event is run in this function, only inserted into the event queue. All
    events are scheduled relative to `tickOffset'. By default the recorded
    delay times are converted to the appropriate number of simulator ticks and
    events inserted at the respective point in (tick) time. To speed up or slow
    down the playback the delay is multiplied by `scalingFactor'.
    '''
    import m5.event
    from m5 import ticks
    class PlaybackEvent(m5.event.Event):
        def __init__(self, event, machine):
            super(PlaybackEvent, self).__init__()
            self.event = event
            self.machine = machine

        def __call__(self):
            self.modifyMachine()

        def modifyMachine(self):
            if controller.machine:
                controller.accessMachine(lambda c,m: (self.swapMachine(c), c.stateModified(self.event)))
            else:
                # Machine not yet created...
                self.swapMachine(controller)

        def swapMachine(self, controller):
            controller.machine = self.machine

    debug.pp(PARTREF, 'Scheduling recorded events from {0}'.format(logFile))
    pbDev = RawPlaybackDevice(openLogFile(logFile), events, controller.getOptions())

    for (timespan, event, machine) in pbDev:
        when = tickOffset + ticks.fromSeconds(timespan)*scalingFactor
        debug.pp(PARTREF, 'schedule event <{0}, {1}>'.format(event, when))
        eventq.schedule(PlaybackEvent(event, machine), int(when))

def openLogFile(logFile):
    return open(logFile, 'rb')

class RawPlaybackDevice(object):
    def __init__(self, eventLog, events, options=None):
        '''Loads a sequence of recorded events.

        The parameter `events' is a list of elements that should be loaded, all
        other events are ignored. If the special event 'all' appears in
        `events' all events are loaded.

        The `options' parameter can be used to replace the options stored by
        the event recorder. This is mostly useful to change things like the
        debugging settings and not to alter the machine configuration settings,
        e.g., the cpu name.
        '''
        self.eventLog = eventLog
        self.playbackAll = False
        # Operate on copy of events
        import copy
        events = copy.copy(events)
        if 'all' in events:
            self.playbackAll = True
            events.remove('all')
            self.debug('Playing back all events.')
        self.events = events
        self.options = options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def nextEvent(self):
        try:
            timespan = 0
            while True:
                (tspan, event, machine) = pickle.load(self.eventLog)
                if self.filterEvent(event):
                    self.debug('Filtering event {0}'.format(event))
                    timespan += tspan
                    continue
                timespan += tspan
                self.debug('Next event <{0}, {1}>'.format(event, timespan))
                return (timespan, event, machine)
        except EOFError:
            return None

    def filterEvent(self, event):
        if self.playbackAll or event in self.events:
            return False
        return True

    def __iter__(self):
        'next() is implemented in the derived classes.'
        return self

    def next(self):
        '''Event iteration honoring the `events' list from the constructor.

        doNext() is implemented in the derived classes.
        '''
        evt = self.nextEvent()
        if evt:
            return self.doNext(*evt)
        raise StopIteration

    def doNext(self, timespan, event, machine):
        if self.options:
            machine.options = self.options
        return (timespan, event, machine)

class BasicPlaybackDevice(RawPlaybackDevice):
    '''A playback device returning only event name and machine state.

    For more information see the documentation of the RawPlaybackDevice.

    Typically you'll want to use either the SimplePlaybackDevice
    (time-inaccurate) or the TimeAccuratePlaybackDevice class.
    '''
    def doNext(self, timespan, event, machine):
        super(BasicPlaybackDevice, self).doNext(timespan, event, machine)
        return (event, machine)

class SimplePlaybackDevice(BasicPlaybackDevice):
    '''A simple time-inaccurate playback device.

    This playback device plays the events back as fast as possible, no time
    accuracy is retained.
    '''
    pass

## SimplePlaybackDevice and BasicPlaybackDevice must be two distinct classes,
## because the time-accurate playback device _is not_ a simple time-inaccurate
## device!

class TimeAccuratePlaybackDevice(BasicPlaybackDevice):
    '''A playback device that honors the recorded event delay times.

    This playback device delays the retrieval for an event for at least the
    time that was recorded by the EventRecorder between two events. If events
    are filtered/ignored the delays of those events are accumulated, i.e., the
    device does what you would expect it to do. For example consider the
    following three events and their respective delay times:

      event   | delay
    ------------------
     m5stats  | 0.5s
     pat      | 0.3s
     m5stats  | 0.4s

    If only m5stats events are to be played back the first event is delayed for
    0.5 seconds. When reading the second event the playback device skips the
    second event, because it is not an m5stats event and continues with the
    third event. But instead of delaying it for 0.4 seconds it is delayed for
    0.3s + 0.4s = 0.7s.

    Playing events back in a time-accurate fashion is especially useful if you
    want to give the McPat simulator enough time to compute the machine
    model.
    '''

    def __init__(self, eventLog, events, options):
        super(TimeAccuratePlaybackDevice, self).__init__(eventLog, events, options)
        self.lastPlaybackTime = None

    def doNext(self, timespan, event, machine):
        self.delayEvent(timespan)
        return super(TimeAccuratePlaybackDevice, self).doNext(timespan, event, machine)

    def delayEvent(self, timespan):
        '''Delay event for at least `timespan' seconds.

        Measure time between last event retrieval and NOW and sleep for the
        remaining time to fill the `timespan' delay gap.
        '''
        now = time()
        if self.lastPlaybackTime is None:
            self.lastPlaybackTime = now
        delayedTime = now - self.lastPlaybackTime
        if delayedTime >= timespan:
            self.lastPlaybackTime = now
            return

        delayTime = timespan - delayedTime
        sleep(delayTime)
        self.lastPlaybackTime = time()
        # Debugging output must not occur during the above calculation, or we
        # introduce unecessary errors in `now' and the output of time() at the
        # point where we actually invoke sleep.
        self.debug('Slept for %.3fs' % delayTime)
