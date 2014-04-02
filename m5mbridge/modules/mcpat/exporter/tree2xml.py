PARTREF = 'all.modules.mcpat.exporter.tree2xml'

from m5mbridge import bug, panic, warning, debug
from xmldocvisitor import XmlDocVisitor

class Tree2XmlVisitor(XmlDocVisitor):
    def __init__(self, xmldoc, options):
        super(Tree2XmlVisitor, self).__init__(xmldoc)
        self.options = options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def visit(self, component):
        self.debug('Generating summary component'.format(component.name))

        docNode = self.allocDocNode(component)
        self.addParams(docNode, component)
        self.addStats(docNode, component)

    def allocDocNode(self, component):
        docNode = self.doc.createElement("component")
        self.currentDocElement = docNode
        parentNode = self.parent()
        parentNode.appendChild(docNode)
        docNode.setAttribute("id", component.id)
        docNode.setAttribute("name", component.name)
        return docNode

    def addParams(self, docNode, component):
        self.debug('params = {0}'.format(component.params))
        for paramKey in component.params:
            newParam = self.doc.createElement("param")
            newParam.setAttribute("name", paramKey)
            newParam.setAttribute("value", component.params[paramKey])
            docNode.appendChild(newParam)

    def addStats(self, docNode, component):
        self.debug('stats = {0}'.format(component.statistics))
        for statKey in component.statistics:
            newStat = self.doc.createElement("stat")
            newStat.setAttribute("name", statKey)
            newStat.setAttribute("value", component.statistics[statKey])
            docNode.appendChild(newStat)
