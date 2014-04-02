'''Checks that verify the integrity of the component tree.

This is mainly useful to detect unsuitable machine models, for example the use
of the atomic simple cpu model when simulating with M5
'''

from m5mbridge.machine.component import MCPAT_EXPORT_CONF

class ImproperCpuModel(Exception):
    def __init__(self):
        super(ImproperCpuModel, self).__init__()

    def __str__(self):
        return 'Simulation with McPat/Hotspot requires a more complex cpu model than the atomic simple model.'

def check(machine):
    checkCpuModels(machine.tree, machine.options.cpu_name)

def checkCpuModels(root, cpu_name):
    '''Make sure that there's a cpu with a proper cpu model.

    Currently all cpu models of M5 are suitable for translation to McPAT,
    except for the atomic simple cpu model.
    '''

    from re import match

    def walkTree(node):
        if match('{0}[0-9]*'.format(cpu_name), node.name) and not 'atomic' in node.params['type'].lower():
            return True

        for child in node.children:
            if walkTree(child):
                return True
        return False

    if not walkTree(root):
        raise ImproperCpuModel()
