from os.path import join as pathjoin

import core

dumpListeners = []

def registerDumpListener(listener):
    dumpListeners.append(listener)

outputStreams = []

def registerOutput(stream):
    outputStreams.append(stream)

class StatsDumpSimulator(object):
    def __init__(self, path = None):
        if not path:
            path = pathjoin(core.getOutputDir(), 'stats.txt')
        self.path = path
        self.dumps = []
        self.readDumpsFromFile()
        self.nextDumpIdx = 0

    def readDumpsFromFile(self):
        lines = ''
        with open(self.path, 'r') as f:
            lines = f.read()
        self.dumps = lines.split('---------- Begin Simulation Statistics ----------')

        # Strip empty stats dumps
        self.dumps = map(lambda x: x.strip(), self.dumps)
        self.dumps = filter(len, self.dumps)

        for dump in self.dumps:
            dump = '---------- Begin Simulation Statistics ----------' + dump

    def dumpOne(self):
        if not self.haveDump(): return

        dump = self.nextDump()
        for stream in outputStreams:
            stream.write(dump)

        for listener in dumpListeners:
            listener()

    def dumpAll(self):
        while self.haveDump():
            self.dumpOne()

    def haveDump(self):
        return self.nextDumpIdx < len(self.dumps)

    def nextDump(self):
        cur = self.nextDumpIdx
        self.nextDumpIdx += 1
        return self.dumps[cur]
