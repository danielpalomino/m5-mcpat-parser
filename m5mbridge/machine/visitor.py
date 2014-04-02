from m5mbridge import bug, panic, warning

class UnknownComponent(Exception):
    """Indicates a component of unknown type.

    Thrown by Visitor.visit() if a component of unknown type is encountered.

    Attributes:
        component -- the offending component object
    """
    def __init__(self, component):
        self.component = component

class Visitor(object):
    def __init__(self):
        self.parentStack = []

    def pushParent(self, parent):
        self.parentStack.append(parent)

    def popParent(self):
        return self.parentStack.pop()

    def parent(self):
        if len(self.parentStack):
            return self.parentStack[-1]
        else:
            return None

    def visit(self, component):
        pass

class SimpleVisitor(Visitor):
    '''Allows use of a function as visitor.'''
    def __init__(self, func):
        super(SimpleVisitor, self).__init__()
        self.func = func

    def visit(self, component):
        self.func(component)

class Finder(Visitor):
    '''Find all components matching a name.

    This visitor iterates over the component tree and collects all components
    matching a given name or for which a given boolean function evaluates to true.
    '''
    def __init__(self, nameOrCallable):
        super(Finder, self).__init__()
        self.cb = nameOrCallable
        if not callable(nameOrCallable):
            self.cb = lambda c: c.name == nameOrCallable
        self.components = []

    def visit(self, component):
        if self.cb(component):
            self.components.append(component)


