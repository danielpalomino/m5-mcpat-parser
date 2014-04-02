'''Extracts power-data from the component-tree and generates a flat column file
containing it.

The file is in a format suitable for use with Gnuplot, i.e., it just contains
column separated by whitespace and comment-lines starting with '#'. There are
some special comment lines that contain some meta-data. The meta-data is the
time-interval during which the data was recorded, the parent-child relationship
between components and the component names.

The following is an example output:
---------------------Start-------------------------
# time (seconds): 2.352710
# PeakDynamic RuntimeDynamic SubthresholdLeakage GateLeakage
# system : cpu0 cpu1 l1directory0 l2 tol2bus physmem mc niu pcie flashc
306.96	0.818311	6.96628	1.7607
# cpu0 : pbt itb icache dtb btb
153.288	0.433902	3.05913	0.808673
# pbt : 
0.0193899	6.22181e-05	0.00503837	0.000716637
# itb : 
0.0119271	2.75142e-06	0.000816149	0.000189322
# icache : 
0.137093	0	0.0144267	0.00213214
# dtb : 
0.0786724	7.8466e-12	0.00284792	0.000628339
# btb : 
0.0288731	1.99165e-11	0.0123795	0.00245086
# cpu1 : pbt itb icache dtb btb
153.288	0.366582	3.05913	0.808673
# pbt : 
0.0193899	2.26878e-05	0.00503837	0.000716637
# itb : 
0.0119271	1.78086e-06	0.000816149	0.000189322
# icache : 
0.137093	0	0.0144267	0.00213214
# dtb : 
0.0786724	7.8466e-12	0.00284792	0.000628339
# btb : 
0.0288731	1.99165e-11	0.0123795	0.00245086
# l1directory0 : 
0.00383535	2.88651e-12	0.021481	0.00440768
# l2 : 
0.0566863	1.06313e-11	0.819757	0.137044
# tol2bus : 
0.144002	0	0.00468368	0.00114045
# physmem : 

# mc : 
0.178272	0.0178272	0.00209381	0.000765475
# niu : 

# pcie : 

# flashc : 

----------------------End--------------------------

As you can see a name is not unique, but because the tree-structure is encoded
in the meta-data it follows that a component is a child of the first component
that preceeds it and lists it in its children list. Or fomulated the other way,
all components that are listed in a children list of a component directly
follow that component in the order they're listed in the children list.

If a component has no power-data the line is empty. This is in accordance with
the format of Gnuplot input files and makes machine-parsing easy.

'''

from m5mbridge.machine.visitor import Visitor
from cStringIO import StringIO

def tree2DataTable(machine):
    t = Tree2DataTable()
    machine.visit(t)
    return t.buf.getvalue()

class Tree2DataTable(Visitor):

    # Names of keys in class PatData's power attribute.
    POWER_TYPES = [
            'Peak Dynamic',
            'Runtime Dynamic',
            'Subthreshold Leakage',
            'Gate Leakage'
    ]

    def __init__(self):
        super(Tree2DataTable, self).__init__()
        self.buf = StringIO()

    def visit(self, component):
        # Skip components without PAT data
        if not component.pat: return

        if component.name.lower() == 'root':
            # Skip the root component, we start with 'system'
            return
        elif component.name.lower() == 'system':
            # Extract the time-interval
            self.writeTimeInterval(component)
            self.writeColumnHeaderLine()

        self.writeComponentHeader(component)
        self.writeComponentPowerData(component)

    def writeTimeInterval(self, component):
        self.buf.write("# time (seconds): {0}\n".format(component.statistics['sim_seconds']))

    def writeComponentHeader(self, component):
        name = self.componentName(component)
        childrenNames = self.createChildrenNames(component)
        self.buf.write("# {0} : {1}\n".format(name, childrenNames))

    def componentName(self, component):
        parts = component.name.split()
        parts[0] = parts[0].lower()
        for i in range(1, len(parts)):
            parts[i] = parts[i].capitalize()
        return ''.join(parts)

    def createChildrenNames(self, component):
        childrenNameList = []
        for child in component.children:
            # Skip children without PAT data.
            if child.pat:
                childrenNameList.append(self.componentName(child))
        return ' '.join(childrenNameList)

    def writeComponentPowerData(self, component):
        power = component.pat.power
        values = "\t".join([power[ptype][0] for ptype in self.POWER_TYPES])
        self.buf.write("{0}".format(values))
        self.buf.write("\n")

    def writeColumnHeaderLine(self):
        self.buf.write('#')
        for ptype in self.POWER_TYPES:
            self.buf.write(' {0}'.format(self.colHeaderName(ptype)))
        self.buf.write("\n")

    def colHeaderName(self, name):
        parts = name.split()
        for i in range(0, len(parts)):
            parts[i] = parts[i].capitalize()
        return ''.join(parts)
