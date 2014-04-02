import sys
#sys.path.append('../HotSpot-5.02')
#import hotspot

from m5mbridge import getController
from m5mbridge.factory import createMachine, fixArgs
from m5mbridge.entry import initM5MBridge, dump
from m5.stats import StatsDumpSimulator
from m5.patsim import PatEventSimulator
from m5mbridge.controller.playback import simplePlaybackDevice, timeAccuratePlaybackDevice
from m5mbridge.machine import options

# C
args = ['--config_fn', '../gem5/m5out/config.ini', '--debug=controller-']
opts = options.parse(fixArgs(args))
initM5MBridge(args)
controller = getController()

spd = simplePlaybackDevice('../gem5/m5out/events.log.gz', options=opts)

for (e,m) in spd:
    print "Unpickling, ", e
    controller.machine = m
    controller.stateModified(e)

exit(137)

stats = StatsDumpSimulator('stats.txt')
stats = StatsDumpSimulator('stats.txt')

pat = PatEventSimulator('mcpat-test.log')

controller = getController()
stats.dumpOne()

from m5mbridge.machine import component

machine = controller.machine

print machine.tree

from m5mbridge.modules.m5.importer.generatecalcparts import addNewComponent

#addNewComponent(machine.tree, 'system', 'TEST', id=12, type='Bus', rw='yes')
cpu = machine.tree.children[0].children[0]

print "CPU-id: {0} name: {1}".format(cpu, cpu.name)
print machine.tree
stats.dumpOne()
pat.importPatData(controller)

# Give McPat time to compute machine
from time import sleep
sleep(60)

while stats.haveDump():
    stats.dumpOne()
    sleep(1)
    controller.tick()

