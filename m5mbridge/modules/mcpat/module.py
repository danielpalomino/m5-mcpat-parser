PARTREF = 'all.modules.mcpat'

import subprocess
from os import path
import xml.dom.minidom
import select

import m5
import m5.core

import m5mbridge
from m5mbridge import debug, warning
from exporter.tree2mcpat import Tree2McPatVisitor
from exporter.tree2mcpat import MachineConfigGenerator
from exporter.tree2mcpat import MachineStatsGenerator

import importer

import atexit

def hasMachineBuses(machine):
    return machine.findComponent(lambda c: c.export() and 'bus' in c.params['type'].lower())

class McPatModule(object):

    # Wait at most this many seconds at exit for pending responses from McPat.
    # (See the onM5Stats method.)
    MAX_WAIT_AT_EXIT = 3

    def __init__(self):
        self.outputDir = m5.core.getOutputDir()
        self.mcpatLogPath = path.join(self.outputDir, 'mcpat.log')
        self.mcpatLog = open(self.mcpatLogPath, 'w')
        self.mcpatConfig = path.join(self.outputDir, 'config.xml')
        self.mcpat = None
        self.mcpatOutputGrabber = None
        self.requestsInFlight = 0
        self.exiting = False

        atexit.register(lambda : self.atexit())

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def atexit(self):
        self.debug('Simulator about to exit. Outstanding requests: {0}'.format(self.requestsInFlight))
        self.exiting = True

    def stateModified(self, controller, event):
        self.debug('rcv event {0}'.format(event))

        self.tick(controller)

        if event == 'm5stats':
            self.onM5Stats(controller)

    def tick(self, controller):
        controller.accessMachine(lambda c,m: self.readMcPatOutput(c, m))

    def onM5Stats(self, controller):
        controller.accessMachine(lambda c,m: self.dispatch(m))

        # We've received the last m5stats event, we have to block M5 and wait
        # for McPat's reply. But we wait only for some seconds, to avoid
        # blocking endlessly in case something went wrong.
        if self.exiting:
            import time
            endTime = time.time() + self.MAX_WAIT_AT_EXIT
            while self.requestsInFlight != 0 and time.time() <= endTime:
                self.tick(controller)

            if self.requestsInFlight != 0:
                warning("McPat seems not to respond. We lost the last {0} dumps.".format(self.requestsInFlight))

    def dispatch(self, machine):
        if not self.mcpat:
            self.setup(machine)

        request = self.prepareRequest(machine)
        f = open(path.join(self.outputDir, 'performance_stats.xml'),'a')
        f.write(request)
        f.close()
        self.sendRequest(request)

    def setup(self, machine):
        if self.mcpat: return

        self.createMcPatConfig(machine)

        self.debug('starting mcpat process')
        try:
            self.mcpat = subprocess.Popen(['mcpat', '-infile', self.mcpatConfig, '-print_level', '5'],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)
        except OSError as e:
            m5.fatal("Running mcpat failed (error {0.errno}): {0.strerror}".format(e))

        self.mcpatOutputGrabber = McPatOutputGrabber(self.mcpat.stdout, hasMachineBuses(machine))

    def prepareRequest(self, machine):
        doc = xml.dom.minidom.Document()

        visitor = Tree2McPatVisitor(doc,
                                    [MachineConfigGenerator(doc), MachineStatsGenerator(doc)],
                                    machine.options)
        machine.visit(visitor)

        return doc.toprettyxml()

    def sendRequest(self, request):
        self.debug('send request', request)
        self.mcpat.stdin.write(request)
        self.requestsInFlight += 1

    def createMcPatConfig(self, machine):
        self.debug('creating mcpat config.xml')
        doc = xml.dom.minidom.Document()

        visitor = Tree2McPatVisitor(doc,
                                    [MachineConfigGenerator(doc)],
                                    machine.options)
        machine.visit(visitor)

        with open(self.mcpatConfig, 'w') as f:
            f.write(doc.toprettyxml())

    def readMcPatOutput(self, controller, machine):
        if not self.mcpatOutputGrabber: return

        self.mcpatOutputGrabber.run()

        # Avoid signaling a 'pat'-event in case there are no reports to process.
        if not len(self.mcpatOutputGrabber.reportQueue): return

        self.debug('got {0} reports'.format(len(self.mcpatOutputGrabber.reportQueue)))

        # Log all reports
        for report in self.mcpatOutputGrabber.reportQueue:
            self.mcpatLog.write(report)

        # Adjust the number of requests for which we're still waiting for a reply.
        self.requestsInFlight -= len(self.mcpatOutputGrabber.reportQueue)

        # Copy the reports to a temporary queue, so that we can clear the
        # report queue (due to recursion caused by issuing pat events).
        queue = [ report for report in self.mcpatOutputGrabber.reportQueue ]

        # Clear the report queue
        self.mcpatOutputGrabber.clearQueue()

        self.importPatData(controller, machine, queue)

    def importPatData(self, controller, machine, queue):
        for report in queue:
            self.debug('importing report', report)
            importer.importMcPatData(machine, report)
            # Signal machine modified to the controller. It is important to do this
            # after we clear the current content of the report queue, or we will
            # cause an infinite recursion where we process the same reports over
            # and over again.
            controller.stateModified('pat')

class McPatOutputGrabber(object):
    def __init__(self, mcpatStdout, machineHasBuses):
        super(McPatOutputGrabber, self).__init__()
        self.mcpatStdout = mcpatStdout
        self.reportQueue = []
        self.reportLines = []
        self.machineHasBuses = machineHasBuses

    def clearQueue(self):
        del self.reportQueue[:]

    def run(self):

        while self.dataAvailable():
            line = self.mcpatStdout.readline()
            if line:
                self.reportLines.append(line)
                if self.completeReport():
                    self.createReport()
            else:
                break

    def dataAvailable(self):
        (ready, _, _) = select.select([self.mcpatStdout], [], [], 0)
        return ready

    def createReport(self):
        report = ''.join(self.reportLines)
        self.reportQueue.append(report)
        del self.reportLines[:]

    def completeReport(self):
        lastLine = self.reportLines[-1]

        # A McPat output always ends with a bus component or the memory
        # controller component, which has a transaction engine as last
        # sub-component. The transaction engine and the bus have has as last
        # stat the runtime dynamic power. And finally the last component is
        # closed with a line of * characters.
        # In summary, this expression checks if the output contains either a
        # complete bus or transaction engine component.
        if self.machineHasBuses:
            return -1 != self.rfind('BUSES', self.rfind('Bus:', self.rfind('Runtime Dynamic', self.rfind('**********'))))
        else:
            return -1 != self.rfind('Memory Controller:', self.rfind('Transaction Engine:', self.rfind('Runtime Dynamic', self.rfind('**********'))))

    def rfind(self, string, rstart=None):
        '''Tests if string is a substring of any line in McPat's output, starting at the last line.

        To avoid a lot of unnecessary checks, this function looks only as far
        back as two encounters of lines consisting of only * characters, i.e.,
        it exploits some knowledge about McPat's output format. This reduces
        the cost of a single call from O(n) to O(1), because the number of
        lines between two stars is bounded, and the accumulative cost for a
        complete report from O(n^2) down to O(n).
        '''
        length = len(self.reportLines)

        if not length: return None

        if not rstart: rstart = length-1

        numStarLines = 0

        for i in xrange(rstart, -1, -1):
            line = self.reportLines[i]
            if string in line:
                return i
            elif '***************' in line:
                numStarLines += 1
            if numStarLines == 2:
                break

        return -1
