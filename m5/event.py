'''A mockup of M5's event scheduler.'''
from Queue import PriorityQueue
import time
import core
import ticks

class SchedulerQueue(object):
    '''A double-queue based scheduler queue.

    New events are inserted into another queue than the one events are
    currently fetched from. This prevents infinited event-processing cycles if
    events cause themselves new events, etc.

    The second queue is only used during event processing.
    '''
    def __init__(self):
        self.queues = [PriorityQueue(), PriorityQueue()]
        self.cur = 0

    def put(self, event):
        self.queues[self.putQueue()].put(event)

    def get(self):
        '''Nonblocking, returns the next event if available or None.'''
        queue = self.queues[self.getQueue()]
        if queue.empty():
            return None
        return queue.get()

    def swapQueues(self):
        self.cur = self.putQueue()

    def putQueue(self):
        return (self.cur+1) % len(self.queues)

    def getQueue(self):
        return self.cur

    def __iter__(self):
        return self

    def next(self):
        evt = self.get()
        if evt:
            return evt
        raise StopIteration

class SchedulerEvent(object):
    def __init__(self, event, when):
        self.event = event
        self.when = when

    def __cmp__(self, other):
        # If time difference is smaller than 100us, we schedule on priority.
        if abs(self.when - other.when) < 0.0001:
            return cmp(-self.event.priority(), -other.event.priority())
        # Else on timestamp
        return cmp(self.when, other.when)

class Scheduler(object):
    '''A simple scheduler mimicking M5's event scheduler.

    This scheduler provides blocking and non-blocking event processing for M5
    events. However, it does currently not honor priorities and events may get
    scheduled late to avoid infinite event-loops.
    '''
    def __init__(self):
        self.queue = SchedulerQueue()

    def schedule(self, event, when):
        when = core.startTime + ticks.toSeconds(when)
        self.put(event, when)

    def deschedule(self, event):
        raise NotImplementedError('m5.event.Scheduler.deschedule is not implemented.')

    def run(self):
        # Swap queues, i.e., make the queue where events were stored until now
        # the queues where events are fetched from and store newly created
        # events during event processing in the former get-queue.
        self.queue.swapQueues()

        # Fetch all events from queue, if we have to sleep for the foremost
        # event we give up unless we're in blocking mode.
        for evt in self.queue:
            now = time.time()
            if evt.when <= now:
                evt.event()
            else:
                # Event not ready, re-insert it and stop
                self.queue.swapQueues()
                self.put(evt.event, evt.when)
                break

    def put(self, event, when):
        self.queue.put(SchedulerEvent(event, when))

    def runBlocking(self):
        '''Like run() but blocks while waiting on timeouts.'''
        self.queue.swapQueues()

        # Fetch all events from queue, if we have to sleep for the foremost
        # event we give up unless we're in blocking mode.
        for evt in self.queue:
            now = time.time()
            if evt.when <= now:
                evt.event()
            else:
                time.sleep(evt.when - now)
                evt.event()

# You must call mainq.run() on a regular basis to process all queued events.
# Unfortunately there's no way to execute just some events with
# sched.scheduler, thus this may block for some time.
mainq = Scheduler()

class Event(object):
    def __init__(self, priority=None):
        if priority is None:
            # Default priority in M5 is 0 for historical reasons, see also
            # src/sim/eventq.hh in the gem5 project.
            priority = 0
        self.__priority = priority

    def priority(self):
        return self.__priority
