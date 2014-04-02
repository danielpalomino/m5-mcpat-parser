PARTREF = 'all.modules.m5'

import cStringIO

import m5
import m5.internal.stats
from m5 import readstats
from m5.stats import registerOutput

from m5mbridge import debug
from importer import stats
from exporter.tree2datatable import tree2DataTable

class M5Module(object):
    def __init__(self):
        self.output = m5.internal.stats.initTextStream()
        self.patTable = ''
        registerOutput(self.output)
        readstats.setReadstatsHandler(lambda l,o: self.readstats(l, o))

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def importStats(self, machine):
        '''Call this function via the Controller.accessMachine-method.'''
        s = self.output.str()
        stats.importStats(cStringIO.StringIO(s), machine)

    def stateModified(self, controller, event):
        self.debug('rcv event {0}'.format(event))
        if event == 'pat':
            controller.accessMachine(lambda c,m: self.updatePatTable(m))

    def tick(self, controller):
        pass

    def updatePatTable(self, machine):
        self.patTable = tree2DataTable(machine)
        self.debug('updating pat table:', self.patTable)

    def readstats(self, length, offset):
        # Python's []-operator does already all the special case handling,
        # where the requested range is larger than our buffer. Awesome!
        return self.patTable[offset:offset+length]
