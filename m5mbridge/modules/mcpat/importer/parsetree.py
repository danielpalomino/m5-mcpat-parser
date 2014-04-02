'''See the parser module for documentation.'''

class Block(object):
    '''A block is a token broken into type, data and child tokens.'''

    def __init__(self, token, parent):
        (self.typ, self.data) = token[0], token[1:]
        self.parent = parent
        self.children = []

    def addData(self, toklist):
        self.data.extend(toklist)

    def addChild(self, child):
        self.children.append(child)

    def visit(self, visitor):
        '''Preorder traversal of subtree.'''
        visitor.visit(self)

        visitor.pushParent(self)
        for child in self.children:
            child.visit(visitor)
        visitor.popParent()

    def visitPostOrder(self, visitor):
        visitor.pushParent(self)
        for child in self.children:
            child.visit(visitor)
        visitor.popParent()

        visitor.visit(self)

    def __str__(self, indent=0):
        '''Create a string representation of the tree with this instance as root.'''
        if len(self.data) == 1:
            data = self.data[0]
        elif len(self.data) == 0:
            data = ''
        else:
            data = self.data
        s = '{0}{1} {2}: {3}\n'.format(' '*indent, self.typ, data, ', '.join([c.typ for c in self.children]))

        for child in self.children:
            s += child.__str__(indent+2)

        return s

class Visitor(object):
    '''The Visitor base class keeps track of all ancestors of the currently visited node.'''

    def __init__(self):
        self.parentStack = []

    def pushParent(self, node):
        self.parentStack.append(node)

    def popParent(self):
        self.parentStack.pop()

    def parentNode(self):
        if len(self.parentStack):
            return self.parentStack[-1]
        return None

class IndentStack(object):
    '''A stack tracking all currently opened indentation/nest-levels.

    Used to keep track of the nested indentations/indentation levels as the
    tree-builder proceeds through the list of tokens, reconstructing the
    tree.

    Each indentation pushed to the stack can be viewed as a new (nested) scope
    of a programing language. For example, in this python script theres the
    module global scope where the class IndenStack is defined, the class-scope
    where the methods are defined and the local scopes where code of each
    method is listed.
    '''

    def __init__(self):
        self.indentStack = []

    def toTopLevel(self):
        self.indentStack = []

    def level(self):
        return self.indentStack[-1]

    def _level(self):
        if len(self.indentStack):
            return self.indentStack[-1]
        return None

    def indent(self, indent):
        if indent > self._level():
            self.indentStack.append(indent)

    def outdent(self, indent):
        if self._level():
            self.indentStack.pop()
        if self._level() != indent:
            print 'Warning indentation mismatch, expected:', self._level(), 'got', indent

    def __lt__(self, other):
        return self._level() < other

    def __le__(self, other):
        return self._level() <= other

    def __eq__(self, other):
        return self._level() == other

    def __ge__(self, other):
        return self._level() >= other

    def __gt__(self, other):
        return self._level() > other

    def __ne__(self, other):
        return self._level() != other

class TreeBuilder(object):
    '''Creates a tree from the token list and each token's indentation level.

    The tree constructed by this class does not reflect the actual hierarchy as
    seen in McPat's output. It needs further post-processing.
    '''

    def __init__(self, tokList):
        self.tokList = tokList
        self.indent = IndentStack()
        # The comma after 'root' is not a typo it turns the first argument into
        # a tuple with the single element 'root'.
        self.root = Block(('root',), None)

    def createTree(self):
        i = 0
        while i < len(self.tokList):
            (i,child) = self.makeSubTree(i, self.root)
            self.root.addChild(child)
        return self.root

    def makeSubTree(self, start, parent):
        (myindent,tok) = self.tokList[start]
        block = Block(tok, parent)

        i = start+1
        while i < len(self.tokList):
            (indent,tok) = self.tokList[i]
            if indent == myindent: # Not a child, go up one level.
                break
            elif indent > myindent: # A child
                (i,child) = self.makeSubTree(i, block)
                block.addChild(child)
            else: # indent < myindent: Go up one level:
                break

        return (i,block)
