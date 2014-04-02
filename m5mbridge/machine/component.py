from m5mbridge import bug, panic, warning

def sortComponentList(components):
    '''Sort a list of component objects by their name attribute.'''
    names=[]
    temp_hash={}
    for comp in components:
        names.append(comp.name)
        temp_hash[comp.name]=comp

    names.sort()
    ret=[]
    for comp_name in names:
        ret.append(temp_hash[comp_name])

    return ret

class ComponentParameterMissing(Exception):
    def __init__(self, name, params, missingParam):
        self.name = name
        self.params = params
        self.missingParam = missingParam

    def __str__(self):
        return "Component {0} is missing parameter '{1}'. Given parameters were {2}.".format(self.name, self.missingParam, self.params)

def enum(*sequential, **named):
    '''An enum-implementation from http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python'''
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

# Constants that definde the export behaviour for the McPAT exporter. Some
# components used to be pruned from the component tree in earlier versions
# and the original m5-mcpat-parse-se.py script, but we don't prune those
# components anymore. Instead we specify for each component if it should be
# exported with or without its children or if only its children should be
# exported and of course there's an additional option that prohibits the
# export of the node and its children.
MCPAT_EXPORT_CONF = enum('WITH_CHILDREN', 'WITHOUT_CHILDREN', 'ONLY_CHILDREN', 'EXCLUDE')

class Component(object):

    def __init__(self, id, params, name=None):
        '''The params attribute has one required attribute, the component's with key 'type'.'''
        temp = id.split('.')
        if name==None:
            self.name = temp[len(temp)-1] #last field specifies what this component is
        else:
            self.name=name

        if not params.has_key('type'):
            raise ComponentParameterMissing(self.name, params, 'type')

        self.id = id
        self.params = params
        self.re_id=None
        self.re_name=None
        self.translated_params = {}
        self.translated_params_order = []
        self.children = []
        self.statistics = {}
        self.translated_statistics = {}
        self.calc_statistics = {}
        self.translator = None
        self.translated_statistics_order=[]
        self.pat = None
        self.mcpat_export_conf = MCPAT_EXPORT_CONF.EXCLUDE

    def visit(self, visitor):
        '''Pre order traversal of the component tree.'''
        visitor.visit(self)
        visitor.pushParent(self)
        for child in self.children:
            child.visit(visitor)
        visitor.popParent()

    def visitPostOrderTraversal(self, visitor):
        visitor.pushParent(self)
        for child in self.children:
            child.visitPostOrderTraversal(visitor)
        visitor.popParent()
        visitor.visit(self)

    def __str__(self, indent=0):
        '''Create a string representation of the tree with this instance as root.'''
        s = "{0}{1}\n".format(' '*indent, self.name)

        for child in self.children:
            s += child.__str__(indent+2)

        return s

    def export(self):
        '''Returns true if component is marked for mcpat export.

        This is only a simple check, it does not take the export settings of
        the components ancestory into account. It simply returns if the
        MCPAT_EXPORT_CONF setting of this component allows exportation.
        '''
        return self.mcpat_export_conf in [MCPAT_EXPORT_CONF.WITH_CHILDREN, MCPAT_EXPORT_CONF.WITHOUT_CHILDREN]


'''
The <system>-component in the McPAT XML file includes some <param>-components
that are needed by the parser in McPAT. Thus, this script must print these
components always, even if the user only wants an XML file that includes just
the <stat>-components.
'''
class SystemComponent(Component):
    def __init__(self, *args):
        super(SystemComponent, self).__init__(*args)
        # Overwrite the default setting (exclude component and subtree), we
        # always want the system component in the output.
        self.mcpat_export_conf = MCPAT_EXPORT_CONF.WITH_CHILDREN

    def createContent(self, contentCreators, new_component, doc):
        if not "createSystemConfig" in contentCreators:
            contentCreators = list(contentCreators)
            contentCreators.append("createSystemConfig")
        super(SystemComponent, self).createContent(contentCreators, new_component, doc)
