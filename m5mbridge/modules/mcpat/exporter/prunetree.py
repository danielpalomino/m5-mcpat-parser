PARTREF = 'all.modules.mcpat.exporter.prunetree'

from m5mbridge import bug, panic, warning, debug
from m5mbridge.machine.visitor import Visitor
from m5mbridge.machine.component import Component, MCPAT_EXPORT_CONF
from m5mbridge.machine.component import sortComponentList

class PruneChildrenForMcPatVisitor(Visitor):
    '''Prunes irrelevant nodes from the component tree.

    This visitor class hides all components from the tree that are not
    relevant for McPat's machine model. This is done by setting the
    mcpat_export_conf attribute of class Component.

    There used to be a distinction between the DefaultOutputFilter and
    PruneChildrenForMcPatVisitor operations, but nowadays both just set the
    mcpat_export_conf attribute to include/exclude parts of the component tree.
    '''

    def __init__(self, options):
        super(PruneChildrenForMcPatVisitor, self).__init__()
        self.options = options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def visit(self, component):
        '''
            Select children which must be included in the power XML files.

            You must call this function prior to calling either formXmlSystemConfig() or formXmlSystemStats().
        '''
        #include the root component
        if component.name == 'root':
            self.debug('exporting root')
            component.mcpat_export_conf = MCPAT_EXPORT_CONF.WITH_CHILDREN

        #add architectural stats for this level.
        #re-order children for xml output
        if component.name == self.options.system_name:
            new_children=[]
            #add cores
            filters=[self.options.cpu_name, "L1Directory", "L2Directory", "l2", "l3","tol2bus","tol3bus","NoC", "physmem", "mc", "niu","pcie","flashc"]
            unfilters=[None,None,None, "Directory", "Directory", None, None, None, None,None,None,None,None,None]
            unfilters2=[None,None,None, "bus", "bus", None, None, None, None,None,None,None,None,None]

            filter_pair=zip(filters, unfilters, unfilters2)
            for filt, unfilter, unfilter2 in filter_pair:
                temp_new=[]
                for child in component.children:
                    if filt in child.name:
                        if (unfilter==None or unfilter not in child.name)\
                            and (unfilter2==None or unfilter2 not in child.name):
                            #print "filt:%s unfilter:%s unfilter2:%s child.name:%s"%(filt, unfilter, unfilter2, child.name)
                            temp_new.append(child)

                new_children += sortComponentList(temp_new)

            for child in new_children:
                child.mcpat_export_conf = MCPAT_EXPORT_CONF.WITH_CHILDREN
            self.debug('exporting children of {0}: {1}'.format(component.name, [c.name for c in new_children]))

            # The filter-loop also sorts the components in such a way that
            # they're in the correct order for the McPat XML file. We keep the
            # old elements in their random order, but replace the elements that
            # are definitely exported with their sorted counterpart.
            old_children = filter(lambda x: not x in new_children, component.children)

            component.children = new_children + old_children

        if component.params.has_key('type') and (component.params['type'] == "DerivO3CPU" or component.params['type'] == "TimingSimpleCPU"):
            new_children=[]
            #add cores
            filters=["PBT", self.options.itb_name, "icache", self.options.dtb_name, "dcache", "BTB"]
            unfilters=[None, None, None, None, None, None]
            filter_pair=zip(filters, unfilters)
            for filt, unfilter in filter_pair:
                temp_new=[]
                for child in component.children:
                    if filt in child.name:
                        temp_new.append(child)
                new_children += sortComponentList(temp_new)

            #component.unpruned_children = component.children
            #component.children=new_children
            for child in new_children:
                child.mcpat_export_conf = MCPAT_EXPORT_CONF.WITH_CHILDREN
            self.debug('exporting children of {0}: {1}'.format(component.name, [c.name for c in new_children]))

            old_children = filter(lambda x: not x in new_children, component.children)

            component.children = new_children + old_children
