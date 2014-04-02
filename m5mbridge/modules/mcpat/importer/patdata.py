'''A container class for the power and area data computed by McPat.

Each component of the m5parser's component-tree is extended with an attribute
that points to such an object.
'''

class PatData(object):
    def __init__(self, attributes):
        self.area = attributes['Area']
        self.power = {}
        self.attributes = attributes
        self.addPowerStat('Subthreshold Leakage')
        self.addPowerStat('Gate Leakage')
        self.addPowerStat('Peak Dynamic')
        self.addPowerStat('Runtime Dynamic')

    def addPowerStat(self, name):
        self.power[name] = self.attributes[name]
