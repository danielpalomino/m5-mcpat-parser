PARTREF = 'all.modules.mcpat.exporter.tree2mcpat'

from m5mbridge import bug, panic, warning, debug
from xmldocvisitor import XmlDocVisitor
from m5mbridge.machine.component import Component, MCPAT_EXPORT_CONF
from m5mbridge.machine.visitor import Visitor

class MachineGenerator(object):
    def __init__(self, xmldoc):
        self.doc = xmldoc

    def debug(self, *args):
        debug.pp(PARTREF, *args)

class MachineConfigGenerator(MachineGenerator):
    def createContent(self, component, docNode):
        self.debug('params for {0}: {1}'.format(component.name, component.translated_params))
        for paramKey in component.translated_params_order:
            newParam = self.doc.createElement("param")
            newParam.setAttribute("name", paramKey)
            newParam.setAttribute("value", component.translated_params[paramKey])
            docNode.appendChild(newParam)

class MachineStatsGenerator(MachineGenerator):
    def createContent(self, component, docNode):
        self.debug('stats for {0}: {1}'.format(component.name, component.translated_params))
        for statKey in component.translated_statistics_order:
            newStat = self.doc.createElement("stat")
            newStat.setAttribute("name", statKey)
            newStat.setAttribute("value", component.translated_statistics[statKey])
            docNode.appendChild(newStat)

class DefaultOutputFilter(Visitor):
    '''Excludes some components from McPat XML output.

    This visitor sets the mcpat_export_conf attribute of all components to
    indicate which parts of the component tree should be excluded from the XML
    file for McPAT.

    There used to be a distinction between the DefaultOutputFilter and
    PruneChildrenForMcPatVisitor operations, but nowadays both just set the
    mcpat_export_conf attribute to include/exclude parts of the component tree.
    '''
    FILTER_TYPES = ["Tsunami"\
                   , "IsaFake"\
                   , "SimpleDisk"\
                   , "Terminal"\
                   , "Crossbar"\
                   , "IntrControl"\
                   , "IdeDisk"\
                   , "ExeTracer"\
                   , "AlphaInterrupts"\
                   , "Tracer"\
                   , "Bridge"\
                   , "AtomicSimpleCPU"\
                   , "FUPool"\
                   , "BusConn"]

    def __init__(self, options):
        super(DefaultOutputFilter, self).__init__()
        self.options = options

    def visit(self, component):
        export_conf = None
        ptype = component.params['type']
        for f in self.FILTER_TYPES:
            if ptype == f:
                export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if "TimingSimpleCPU" in component.params['type'] and self.options.cpu_name not in component.name:
            export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if "iocache" in component.name:
            export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if "server" in component.name:
            export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if "client" in component.name:
            export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if "etherdump" in component.name or "etherlink" in component.name:
            export_conf = MCPAT_EXPORT_CONF.EXCLUDE

        if export_conf is not None:
            component.mcpat_export_conf = export_conf

            if not component.export():
                debug.pp(PARTREF, 'DefaultOutputFilter excludes component {0}'.format(component.name))

class Tree2McPatVisitor(XmlDocVisitor):
    '''Creates a McPat XML file from a machine config.

    This visitor class creates a McPat compatible XML file describing the
    machine and containing access statistics to each of its components. It is
    advised that you prune the tree with the PruneChildrenForMcPatVisitor
    class, or the generated XML file may not be valid a input for McPat.

    During construction of a visitor object of this class you can what kind of
    information should be written into the XML file. Currently it supports
    generation of machine configuration parameters and machine access/usage
    statistics.
    '''
    def __init__(self, xmldoc, generators, options):
        super(Tree2McPatVisitor, self).__init__(xmldoc)
        self.generators = generators
        self.options = options
        # Pre-initialize the export stack with as many elements as there are
        # already elements in the parent stack.
        self.exportConfStack = map(lambda x: MCPAT_EXPORT_CONF.WITH_CHILDREN, self.parentStack)
        # Debugging switch and information
        self.parentNameStack = map(lambda x: 'None', self.parentStack)

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def pushParent(self, parent):
        super(Tree2McPatVisitor, self).pushParent(parent)
        self.exportConfStack.append(self.getExcludeConf(parent))
        self.parentNameStack.append(parent.name)

    def popParent(self):
        self.exportConfStack.pop()
        self.parentNameStack.pop()
        return super(Tree2McPatVisitor, self).popParent()

    def getExcludeConf(self, component):
        '''Check if a component should be excluded from the export.

        We exclude a component if any of its parents is excluded, one of its
        parents excludes its children from the export or if the component
        itself is marked for exclusion from the export.
        '''

        # See class XmlDocVisitor's __init__() method (it pushes an initial
        # None value to avoid special-cases in the export code).
        if not issubclass(type(component), Component):
            return MCPAT_EXPORT_CONF.WITH_CHILDREN

        if len(self.exportConfStack):
            exportConf = self.exportConfStack[-1]
            if exportConf == MCPAT_EXPORT_CONF.EXCLUDE:
                return MCPAT_EXPORT_CONF.EXCLUDE
            elif exportConf == MCPAT_EXPORT_CONF.WITHOUT_CHILDREN:
                return MCPAT_EXPORT_CONF.EXCLUDE

        return component.mcpat_export_conf

    def visit(self, component):
        self.debug('visiting component {0}, export conf = {1}'.format(component.name, component.mcpat_export_conf),
                   'parents = {0}'.format(zip(self.parentNameStack, self.exportConfStack)))

        if self.exclude(component):
            return

        self.debug('Generating system config component {0}'.format(component.name))

        docNode = self.allocDocNode(component)
        self.createContent(docNode, component)

    def exclude(self, component):
        if not issubclass(type(component), Component):
            return MCPAT_EXPORT_CONF.WITH_CHILDREN

        export_conf = self.getExcludeConf(component)
        return export_conf == MCPAT_EXPORT_CONF.ONLY_CHILDREN or export_conf == MCPAT_EXPORT_CONF.EXCLUDE

    def createContent(self, docNode, component):
        for generator in self.generators:
            generator.createContent(component, docNode)

    def allocDocNode(self, component):
        docNode = self.doc.createElement("component")
        self.currentDocElement = docNode
        parentNode = self.parent()
        parentNode.appendChild(docNode)

        self.setNameAndId(docNode, component)

        return docNode

    def setNameAndId(self, docNode, component):
        if component.re_id == None:
            docNode.setAttribute("id", component.id)
        else:
            docNode.setAttribute("id", component.re_id)
        if component.re_name == None:
            docNode.setAttribute("name", component.name)
        else:
            docNode.setAttribute("name", component.re_name)
