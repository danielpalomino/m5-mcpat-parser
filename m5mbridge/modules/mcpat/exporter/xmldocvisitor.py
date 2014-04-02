from m5mbridge import bug, panic, warning
from m5mbridge.machine.visitor import Visitor

class XmlDocVisitor(Visitor):
    '''Visitor base class storing XML doc parent components.

    This visitor class is intended to serve as base class for visitor classes
    that generate an XML file. Instead of storing the parent components in the
    parentStack attribute of the Visitor base class, it stores the parent
    document element of the XML document object.
    '''
    def __init__(self, xmldoc):
        super(XmlDocVisitor, self).__init__()
        self.doc = xmldoc
        self.currentDocElement = xmldoc # xmldoc is the root of the root component
        # Don't call pushParent() in the initalizer. This is only a base class
        # and we must expect that derived classes overwrite our implementation
        # of pushParent(), which would cause their code to execute before their
        # initializer did run.
        self.parentStack.append(self.currentDocElement)

    def pushParent(self, parent):
        self.parentStack.append(self.currentDocElement)

