'''Imports McPat output data into m5parser's component tree.'''

PARTREF = 'all.modules.mcpat.importer'

from m5mbridge import debug
from m5mbridge.machine import visitor
from translators import TranslatorFactory, NopTranslator

class TreeMismatch(Exception):
    def __init__(self, parentNodes, parseNode, compTreeNode):
        self.parentNodes = parentNodes
        self.parseNode = parseNode
        self.compTreeNode = compTreeNode

    def __str__(self):
        childNames = [ n.name for n in self.parseNode.children]
        return "Cannot match any of {0}'s children {1} with '{2}'!".format(self.parseNode.name, childNames, self.compTreeNode.name)

class PatImporter(visitor.Visitor):
    '''Mcpat PAT data importer for m5parser.

    Imports the PAT data (power, area, timing) issued by McPat into the
    component tree generated by the m5parser.'''

    def __init__(self, parseTree, options):
        '''Takes as input a parser-tree generated by McPatParser.'''
        super(PatImporter, self).__init__()
        self.options = options
        self.parseTree = parseTree
        self.skipNode = False   # Skip node (implies skipSubTree)
        self.skipSubTree = None # Skips all descendents of skipNode
                                # skipSubTree stores a reference to the node to skip

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def pushParent(self, parent):
        if self.skipSubTree and self.skipNode:
            # Does not matter what we push, we just need to push a value to
            # keep track of the stack depth for popParent().
            self.debug('Pushing {0}'.format(parent.name))
            self.parentStack.append((parent, None))
            return
        elif self.skipSubTree:
            # Only skip children ---> we need a translator for their parent node
            # Set skipNode to True, so that we enter the if-statements
            # true-branch for this node's children.
            self.skipNode = True

        if self.parent():
            parseNode = self.findParseTreeNode(parent)
        else: # First call to pushParent(), it's the root node.
            parseNode = TranslatorFactory.create(self.parseTree, self.options)
        self.debug('Pushing {0}, {1}'.format(parent.name, parseNode.parseTreeNode.name))
        self.parentStack.append((parent, parseNode))

    def popParent(self):
        self.debug('Popping {0}'.format(self.parent()[0].name))
        if self.skipSubTree == self.parent()[0]:
            self.skipNode = False
            self.skipSubTree = None
        super(PatImporter, self).popParent()

    def visit(self, node):
        '''Visitor method for the m5parser component-tree.'''

        if self.skipThisNode(node):
            self.debug('Skipping {0}'.format(node.name))
            return

        if node.name.upper() == 'ROOT':
            translator = TranslatorFactory.create(self.parseTree, self.options)
        else:
            translator = self.findParseTreeNode(node)
        translator.extend(node)

        self.skipChildren(node, translator)

    def skipThisNode(self, node):
        if self.skipSubTree:
            return True
        if TranslatorFactory.filterOut(node, self.options):
            self.debug('Filtering {0}'.format(node.name))
            self.skipNode = True
            self.skipSubTree = node
            return True
        return False

    def skipChildren(self, node, translator):
        if translator.skipChildren:
            self.skipSubTree = node

    def findParseTreeNode(self, comptreeChild):
        '''Check children of `parent' in parentStack for node matching `child' from component-tree.

        This function does not return the parse-tree node directly, instead it
        returns it embedded in a Translator-object.'''
        parseTreeParent = self.parent()[1].parseTreeNode # parent() --> (compTreeParent, translator)

        for child in parseTreeParent.children:
            translator = TranslatorFactory.create(child, self.options)
            if translator.match(comptreeChild):
                return translator
        # No translator found.
        if TranslatorFactory.isOptional(comptreeChild):
            return NopTranslator()
        raise TreeMismatch(self.parentStack, parseTreeParent, comptreeChild)
