from m5mbridge import bug, panic, warning
from visitor import Visitor, SimpleVisitor, Finder

class Machine(object):
    def __init__(self, cht, sht, options):
        self.tree = None
        self.cht = cht
        self.sht = sht
        self.options = options

    ## Forward the Component methods to the component tree's root object.
    def visit(self, visitor):
        if callable(visitor):
            return self.tree.visit(SimpleVisitor(visitor))
        else:
            return self.tree.visit(visitor)

    def visitPostOrderTraversal(self, visitor):
        if callable(visitor):
            return self.tree.visit(SimpleVisitor(visitor))
        else:
            return self.tree.visitPostOrderTraversal(visitor)

    def findComponent(self, nameOrCallable):
        '''Find a component by name or return None.

        If more than one component is found, it returns the first match.
        '''
        f = Finder(nameOrCallable)
        self.tree.visit(f)
        if len(f.components):
            return f.components[0]
        return None
