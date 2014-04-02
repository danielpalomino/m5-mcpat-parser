'''A recorder module.

The EventRecorder is a module for the m5mbridge controller that writes events
and the machine state to a file. This can be used to record some events and
replay them at a later time.

The file format is a series of one or more calls to pickle.dump(), where each
dump is a tuple (timespan:float, event:str, machine:Machine). The first element
is the number of seconds the event happened after the preceeding event, i.e.,
the delay between the two events. The first event has a delay of 0 seconds. The
second element in the tuple is the name of the event and the last element is
the machine instance managed by the m5mbridge controller.
'''

PARTREF = 'all.controller.recorder'

# If possible use the faster C implementation of pickle.
try:
    import cPickle as pickle
except:
    import pickle

from time import time

from m5mbridge import debug

class EventRecorder(object):
    def __init__(self, events, logFile):
        '''Record all events listed in the list `events'.

       Use the special event 'all' to record all events.
       '''
        self.logFile = open(logFile, 'wb')
        self.logAll = False
        # Operate on copy of events
        import copy
        events = copy.copy(events)
        if 'all' in events:
            self.logAll = True
            events.remove('all')
        self.events = set(events)
        self.lastEventTimestamp = None
        self.pickle = pickle.Pickler(self.logFile, -1)

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def stateModified(self, controller, event):
        if self.logAll or event in self.events:
            controller.accessMachine(lambda c,m: self.saveState(event, m))

    def tick(self, controller):
        pass

    def saveState(self, event, machine):
        now = time()
        if self.lastEventTimestamp is None:
            self.lastEventTimestamp = now
        timespan = now - self.lastEventTimestamp

        self.debug('Saving event {0}'.format(event))
        self.pickle.clear_memo()
        self.pickle.dump((timespan, event, machine))

        self.lastEventTimestamp = now
