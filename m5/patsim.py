from os.path import join as pathjoin

import core

from m5mbridge.modules.mcpat import importer

class PatEventSimulator(object):
    def __init__(self, mcpatLog = None):
        if not mcpatLog:
            mcpatLog = pathjoin(core.getOutputDir(), 'mcpat-test.log')
        self.mcpatLog = mcpatLog
        self.dumps = []
        self.readDumpsFromFile()
        self.nextDumpIdx = 0

    def readDumpsFromFile(self):
        lines = ''
        with open(self.mcpatLog, 'r') as f:
            lines = f.read()
        self.dumps = lines.split('McPAT (version 0.8 of Aug, 2010) results  (current print level is 5)')

        # Strip empty dumps
        self.dumps = map(lambda x: x.strip(), self.dumps)
        self.dumps = filter(len, self.dumps)

        # Strip first dump, it's the 'McPat computing target processor' line.
        del self.dumps[0]

        for dump in self.dumps:
            dump = 'McPAT (version 0.8 of Aug, 2010) results  (current print level is 5)' + dump

        if len(self.dumps) <= 1:
            print "WARNING: less than two dumps read from the McPat log file. Did the simple parser break, or is the input corrupted?"

    def importPatData(self, controller):
        if not self.havePatData(): return

        controller.accessMachine(lambda c,m: self.updatePatData(m))
        controller.stateModified('pat')

    def updatePatData(self, machine):
        dump = self.nextDump()
        importer.importMcPatData(machine, dump)

    def havePatData(self):
        return self.nextDumpIdx < len(self.dumps)

    def nextDump(self):
        cur = self.nextDumpIdx
        self.nextDumpIdx += 1
        return self.dumps[cur]
