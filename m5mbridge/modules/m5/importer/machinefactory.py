PARTREF = 'all.modules.m5.importer.machinefactory'

from m5mbridge import bug, panic, warning, debug
from configparser import M5ConfigParser
from m5mbridge.machine import Machine
from m5mbridge.machine.component import Component
from m5mbridge.machine.visitor import Visitor
from generatecalcparts import genId
from generatecalcparts import generateCalcComponents, addVirtualComponents
from translatorfactory import TranslatorFactory

import sanitychecker

def createFromConfigFile(config_file_path, options):
    '''Like createFromConfig but reads the config from a file given as a path.'''

    with open(config_file_path, 'r') as config_file:
        return createFromConfig(config_file, options)


def createFromConfig(config_file, options):
    '''Create a machine object describing an M5 machine from a config.ini.

    This function returns a machine object containing a complete description of
    the M5 machine. It reads the config file from an open file object.
    '''

    debug.pp(PARTREF, 'parsing config file')
    parser = M5ConfigParser(config_file, options)
    cht = parser.run()

    debug.pp(PARTREF, 'creating machine')
    m = Machine(cht, {}, options)

    createComponentTree(m)

    return m

def createComponentTree(machine):
    '''Build component tree from config.ini children param.

    createComponentTree() does the following:
    (1) creates a tree of components by looking at the config.ini
    parameter children for each component.
    (2) stats are added to each component as appropriate.
    (3) missing stats are generated.
    (4) component translator is set
    (5) the translator grabs all relevant stats and params for
    the component and renames from M5 names to McPat names
    '''

    debug.pp(PARTREF, 'creating component tree')

    #create a component tree by looking at the children parameter
    for c_key in machine.cht:
        debug.pp(PARTREF, 'looking at {0}'.format(c_key))
        component = machine.cht[c_key]
        if component.params.has_key('children'):
            for child in component.params['children'].split():
                if c_key == "root":
                    child_id = child
                else:
                    child_id = "%s.%s" %(component.id, child)

                # For the x86 system Gem5 generates a broken config.ini, the
                # terminal component is not a children of the system component.
                # To fix the hierarchy, we just ignore it. The terminal is not
                # important for the statistics.
                if 'terminal' in child_id:
                    debug.pp(PARTREF, 'skipping child {0}'.format(child_id))
                    continue

                if not machine.cht.has_key(child_id):
                    panic("child_id %s does not exist." %(child_id),5)
                debug.pp(PARTREF, 'appending child {0}'.format(child_id))
                component.children.append(machine.cht[child_id])

    #detect and handle switch cpu configurations
    handleSwitchCpus(machine.options, machine.cht)

    #generate calculated components
    debug.pp(PARTREF, 'generating calculated components')
    generateCalcComponents(machine.options, machine.cht, machine.sht)

    #set root component
    machine.tree = machine.cht['root']

    #add additional (calculated/virtual) components
    debug.pp(PARTREF, 'adding virtual components')
    addVirtualComponents(machine)

    # rehash components
    debug.pp(PARTREF, 'rehashing components')
    hashComponents(machine)

    debug.pp(PARTREF, 'translating components')
    translateComponents(machine)

    #run some sanity tests
    sanitychecker.check(machine)

def hashComponents(machine):
    '''Add all components in tree to attribute cht.'''
    hasher = ComponentHasher(machine.cht)
    machine.visit(hasher)

def translateComponents(machine):
    machine.visit(lambda x: translateComponent(machine, x))

def translateComponent(machine, component):
    component.translator = TranslatorFactory.create(machine.options, component)
    if component.translator:
        component.translator.translate(component)
        component.translator.translate_params(component)
        component.translator.translate_statistics(component)

class ComponentHasher(Visitor):
    def __init__(self, cht):
        super(ComponentHasher, self).__init__()
        self.cht = cht

    def visit(self, component):
        if not component.id:
            bug('Component without id encountered!')
        self.cht[component.id] = component

def handleSwitchCpus(options, cht):
    def isExportedSwitchCpu(c):
        return 'switch' in c.name and 'cpu' in c.params['type'].lower()
    switchCpu = filter(isExportedSwitchCpu, cht.itervalues())
    # For switch cpus we must adjust the cpu name.
    if len(switchCpu):
        switchCpu = switchCpu[0]
        from re import sub
        options.cpu_name = sub(r'[0-9]*$', '', switchCpu.name)

