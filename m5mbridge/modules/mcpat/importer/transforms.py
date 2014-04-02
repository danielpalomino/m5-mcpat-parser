'''See the parser module for documentation.'''

class TreeTransform(object):
    '''Base class for all transformations applied to the tree.

    All transforms use a hand-written tree traversal algorithm, because they
    modify the tree which must be taken into account.
    '''

    def __init__(self, tree):
        self.tree = tree

    def transform(self):
        return self.tree

    def __call__(self):
        return self.transform()

class PullUpFromBlocks(TreeTransform):
    '''Recursively replace specific nodes with their children.

    This transform iterates over all nodes and looks for nodes of token type
    `typ'. It replaces these nodes with their children, i.e., it promotes its
    grand-children to children and deletes the now childless node.

    This transformation is primarily needed to clean up the tree after parsing
    the following piece of output:

    *********************************************************************************
      Technology 90 nm
      Using Long Channel Devices When Appropriate
      Interconnect metal projection= aggressive interconnect technology projection
      Core clock Rate(MHz) 1200

    Due to the indentation the tokens created from the last four lines are
    children of the first line.

    The process also implies that after the transformation all nodes with token
    type `typ' are removed from the tree.
    '''

    def __init__(self, tree, typ):
        super(PullUpFromBlocks, self).__init__(tree)
        self.typ = typ

    def transform(self):
        self.pullUpFromBlocks(self.tree)
        return self.tree

    def pullUpFromBlocks(self, node):
        i = 0
        while i < len(node.children):
            child = node.children[i]
            self.pullUpFromBlocks(child)
            if child.typ == self.typ:
                i += self.replaceChildWithGrandChildren(node, child)
            else:
                i += 1

    def replaceChildWithGrandChildren(self, node, child):
        '''Replaces the child with its children (grandchildren of node).

        If the child has no grandchildren it is removed from the list of
        children and all following children are moved to a lower index, i.e.,
        it is perfectly fine for this function to return zero if a child has no
        grandchildren.
        '''
        children = node.children
        idx = children.index(child)
        children[idx:idx+1] = child.children
        return len(child.children)

class FlattenNestedAttributes(TreeTransform):
    '''Promotes grandchildren of attributes to children.

    As can be seen in the following McPat output, sometimes attributes are
    nested:

      Device Type= ITRS high performance device type
        Area = 116.308 mm^2
        Peak Dynamic = 5.51367 W
        Subthreshold Leakage = 2.41316 W
        Gate Leakage = 0.242513 W
        Runtime Dynamic = 4.00707 W

   This transform turns such nested attributes into a flat list of
   attributes, like this:

      Device Type= ITRS high performance device type
      Area = 116.308 mm^2
      Peak Dynamic = 5.51367 W
      Subthreshold Leakage = 2.41316 W
      Gate Leakage = 0.242513 W
      Runtime Dynamic = 4.00707 W
    '''
    def transform(self):
        self.pullUpFromAttributeBlocks(self.tree)
        return self.tree

    def pullUpFromAttributeBlocks(self, node):
        i = 0
        while i < len(node.children):
            child = node.children[i]
            self.pullUpFromAttributeBlocks(child)
            if child.typ == 'attribute':
                i += self.pullUpGrandChildren(node, child)
            else:
                i += 1

    def pullUpGrandChildren(self, node, child):
        '''Promote grandchildren to children.

        Order is important here, or we loose structural information. The
        Grandchildren are inserted after the child into the children list of
        node.'''
        children = node.children
        idx = children.index(child)
        for i in xrange(0, len(child.children)):
            children.insert(idx+i+1, child.children[i])
        nchildren = len(child.children)
        child.children = []
        return nchildren or 1

class AddParamAttributesToParamBlock(TreeTransform):
    '''Adds parametric attributes to their parameter block.

    Attributes that belong to a parameter are not correctly indented, as it can
    be seen in the following output of McPat (already transform with the
    FlattenNestedAttributes transform):

        Total First Level Directory:
        Device Type= ITRS high performance device type
        Area = 8.77473 mm^2
        Peak Dynamic = 3.38588 W
        Subthreshold Leakage = 0.224524 W
        Gate Leakage = 0.0320801 W
        Runtime Dynamic = 15.1158 W

    This transforms turns this into the following structure:

        Total First Level Directory:
          Device Type= ITRS high performance device type
          Area = 8.77473 mm^2
          Peak Dynamic = 3.38588 W
          Subthreshold Leakage = 0.224524 W
          Gate Leakage = 0.0320801 W
          Runtime Dynamic = 15.1158 W
    '''
    def transform(self):
        self.pushDownAttributestoParamBlocks(self.tree)
        return self.tree

    def pushDownAttributestoParamBlocks(self, node):
        i = 0
        while i < len(node.children):
            child = node.children[i]
            self.pushDownAttributestoParamBlocks(child)
            if child.typ == 'parameter':
                attribs = self.collectAttributes(node, i+1)
                self.pushDownChildren(node, child, attribs)
            i += 1

    def collectAttributes(self, node, start):
        attribs = []
        for i in xrange(start, len(node.children)):
            child = node.children[i]
            if child.typ == 'attribute':
                attribs.append(child)
            else:
                break
        return attribs

    def pushDownChildren(self, node, child, attribs):
        for attrib in attribs:
            idx = node.children.index(attrib)
            child.addChild(attrib)
            del node.children[idx]

#########################################################################################
##  Transforms
#########################################################################################

def pullUpFromSeparatorBlocks(tree):
    '''Replace separator blocks with their children.

    See the documentation of PullUpFromBlocks for more details.'''
    t = PullUpFromBlocks(tree, 'separator')
    return t.transform()

def cleanUpParagraphs(tree):
    '''Replace paragraphs with their children.

    Works like the separator blocks. Paragraphs are defined by empty lines in
    McPat's output and used for grouping in addition to indentation.'''
    t = PullUpFromBlocks(tree, 'paragraph')
    return t.transform()

def flattenNestedAttributes(tree):
    '''See documentation of FlattenNestedAttributes.'''
    t = FlattenNestedAttributes(tree)
    return t.transform()

def addParamAttributesToParamBlock(tree):
    '''See documentation of AddParamAttributesToParamBlock.'''
    t = AddParamAttributesToParamBlock(tree)
    return t.transform()
