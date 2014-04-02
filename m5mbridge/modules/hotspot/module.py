from os.path import dirname, join as pathjoin
import re

import hotspot

import floorplan

class HotspotModule(object):
    def __init__(self, flpFile = None):
        plan = None
        if flpFile:
            with open(flpFile, 'r') as f:
                plan = f.read()
        else:
            plan = floorplan.flp

        self.flpStream = hotspot.load_floorplan_from_string(plan)

        self.flp = None
        self.powerMap = {}
        self.flpUnitNames = []

    def stateModified(self, controller, event):
        if event == 'machineCreated':
            controller.accessMachine(lambda c,m: self.init(m))
        elif event == 'pat':
            #print "Hotspot: pat received"
            controller.accessMachine(lambda c,m: self.simulate(m))
        else:
            #print "Hotspot: ignoring event:", event
            pass

    def tick(self, controller):
        pass

    def init(self, machine):
        self.flp = hotspot.read_flp_stream(self.flpStream, False)

        self.collectUnitNames()
        #print '---- tree ----'
        #print machine.tree
        #print '---- tree ----'
        #import ipdb
        #ipdb.set_trace()

        self.configureHotspot(machine)

        self.model = hotspot.alloc_RC_model(self.config, self.flp)
        hotspot.populate_R_model(self.model, self.flp)
        hotspot.populate_C_model(self.model, self.flp)

        self.temp = hotspot.hotspot_vector(self.model)
        self.power = hotspot.hotspot_vector(self.model)

        hotspot.set_temp(self.model, self.temp, self.model.config.init_temp)

    def simulate(self, machine):
        self.updatePowerValues(machine)

    def updatePowerValues(self, machine):
        self.powerMap.clear()
        machine.visit(lambda c: self.updatePowerValue(c))

        #import ipdb
        #ipdb.set_trace()


    def updatePowerValue(self, component):
        power = self.getPower(component)
        if power:
            self.powerMap[component.name] = power

    def getPower(self, component):
        if not component.pat: return

        # Values of the power dictionary are of the form ('0.0853658', 'W').
        leakage = float(component.pat.power['Gate Leakage'][0])
        dynamic = float(component.pat.power['Runtime Dynamic'][0])

        return leakage + dynamic

    def collectUnitNames(self):
        self.flpUnitNames = [ hotspot.unit_array_get(self.flp.units, i).name for i in xrange(self.flp.n_units) ]

    def configureHotspot(self, machine):
        self.config = hotspot.default_thermal_config()

        clockRate = self.getFastestClock(machine)

        # Convert clockRate from MHz to Hz and assign it to Hotspot config.
        self.config.base_proc_freq = clockRate*10e5

    def getFastestClock(self, machine):
        '''Iterate through the component tree and return the fastest CPU's clock rate.'''

        # We need to pass clockRate as reference to the visit() function
        # defined below. It stores the currently fastest clock rate and is
        # updated during the tree traversal. Afterwards we remove this
        # attribute again.
        #
        # If there's a better way to do this, let me know.
        self.clockRate = 0

        def visitor(component, self):
            if 'cpu' in component.name.lower():
                # If switch_cpus are present there are cpu components in the
                # tree that don't have a clockrate param.
                # Switch_cpus are most likely present, because M5 restored the
                # system from a checkpoint.
                self.clockRate = max(self.clockRate, component.params.get('clockrate', 0))

        machine.visit(lambda c: visitor(c, self))

        clockRate = self.clockRate
        del self.clockRate

        return float(clockRate)

