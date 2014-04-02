'''The m5mbridge controller.

The controller mediates access to the global instance of class Machine which
stores the accumulated simulator data at any point in time.


There are parts of the class which are designed for concurrent access and
others which are only designed for access from a single thread. The former are
for access to the global machine instance and for signaling new events, i.e.,
changes to it. All other functions are mostly used during early initialization,
e.g., registering the simulator modules.


At the moment the m5mbridge does not employ multi-threading and all code is run
from a single thread. In order to make a port to a multi-threaded architecture
possible you should only use the thread-safe interface from the simulator
modules and the non-threadsafe part only from the initialization code, except
for read-only/getter methods.
'''

PARTREF = 'all.controller'

import Queue

from m5mbridge import debug, warning, bug

class UninitializedMachine(Exception):
    pass

class Controller(object):
    def __init__(self):
        self.machine = None
        self.lock = False
        self.modules = {}
        self.options = None
        self.events =  Queue.Queue()
        self.eventLock = False

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def registerModule(self, name, module):
        '''Not thread-safe.'''
        self.debug('register module {0} ({1})'.format(name, module))
        self.modules[name] = module

    def getModule(self, name):
        return self.modules[name]

    def accessMachine(self, handler):
        self.debug('machine access by {0}'.format(debug.caller_name()))
        if not self.machine:
            raise UninitializedMachine

        self.enter_monitor()
        result = handler(self, self.machine)
        self.exit_monitor()
        self.dispatchEvents()
        return result

    def stateModified(self, event):
        self.debug('new event {0}'.format(event))
        if not self.locked() and event != 'machineCreated':
            bug('Calling stateModified outside controller.accessMachine()!')
        self.events.put(event)

    def dispatchEvents(self):
        '''Empty event queue. (internal).'''
        events = self.__getQueuedEvents()

        # Dispatch events
        # Note: if the m5mbridge controller is ported to a multi-threaded
        # architecture this will be thread-safe because module.stateModified()
        # will send a message to the thread of each module. Of course, sending
        # messages simultaneously from multiple threads happens in a
        # synchronized manner.
        #
        # However there is a possible problem with event-order, when multiple
        # threads are dispatching events. It's probably best to have a
        # dedicated worker thread do the event dispatching.
        for event in events:
            for module in self.modules.itervalues():
                module.stateModified(self, event)

    def __getQueuedEvents(self):
        '''Thread-safe emptying of the event queue.'''
        events = []
        self.acquireEventQueue()
        size = self.events.qsize()
        # Empty the event queue
        for i in xrange(0, size):
            try:
                events.append(self.events.get())
            # Avoid infinite event buffering (in unlucky scenarios).
            except Queue.Empty:
                break
        self.releaseEventQueue()
        return events

    def tick(self):
        '''Not thread-safe.'''
        self.debug('tick')
        for module in self.modules.itervalues():
            module.tick(self)

    def setOptions(self, options):
        '''Not thread-safe.'''
        '''Provides a way to store the m5mbridge command line options.

        This is mostly useful during early initialization. Once the machine is
        created all running code can accesss the options at any time from
        machine.options.
        '''
        if self.options:
            warning('Overwriting Controller.options.')
        self.options = options

    def getOptions(self):
        if self.options is None:
            raise RuntimeError('Controller.getOptions() called without setting options first!')
        return self.options

    # At the moment the controller and modules all run in a single thread, so
    # we don't have to do any locking. We just check that we never re-enter
    # the monitored code indirectly and break future multi-threading
    # capacilities.
    def enter_monitor(self):
        '''(internal)'''
        if self.lock:
            warning("Recursing into monitored code detected!")
        self.lock = True

    def exit_monitor(self):
        '''(internal)'''
        if not self.lock:
            warning("Leaving monitor without entering it!")
        self.lock = False

    def acquireEventQueue(self):
        '''(internal)'''
        if self.eventLock:
            warning("Event queue already locked!")
        self.eventLock = True

    def releaseEventQueue(self):
        '''(internal)'''
        if not self.eventLock:
            warning("Releasing event queue lock without locking it!")
        self.eventLock = False

    def locked(self):
        '''(internal)'''
        return self.lock
