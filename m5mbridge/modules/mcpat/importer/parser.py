'''A parser for McPat's output.

The parser consists of two major parts: the lexer and the actual parser. The
lexer reads the input line-wise and transforms each line into a token. The
token type is found by applying regular expressions to the input. Each token is
delivered with its indentation attached. This is necessary, because the McPat
output uses indentation to represent the hierarchical data.

The parser fetches all tokens, then it uses the indentation to build a tree
from the indentation information. Because the output of McPat is not meant for
machine computation several clean up and transformation steps are necessary to
compute the intended tree structure.

This is further complicated, because there are some obvious bugs in McPat's
output, e.g., sometimes a colon is missing after a component type (L2 instead
of L2:). Then there's inconsistent indentation for the paragraphs of the
Processor: output chunk, for example:

  Total First Level Directory:
  Device Type= ITRS high performance device type
    Area = 8.77473 mm^2
    Peak Dynamic = 3.38588 W
    Subthreshold Leakage = 0.224524 W
    Gate Leakage = 0.0320801 W
    Runtime Dynamic = 15.1158 W

Instead of having all on the same indentation or the Device Type line indented
too. The post-processing steps transform these blocks to look like this:

  Total First Level Directory:
    Device Type= ITRS high performance device type
    Area = 8.77473 mm^2
    Peak Dynamic = 3.38588 W
    Subthreshold Leakage = 0.224524 W
    Gate Leakage = 0.0320801 W
    Runtime Dynamic = 15.1158 W

After the post-processing (implemented by classes derived from class
TreeTransform) the tree has a proper hierarchy as implied by McPat's output.
Now, the tokens can be interpreted and an abstract syntax tree created.

To get a better understanding of the parser's working it is advised to enable
the of the McPatLexer class and inspect the tokens the lexer creates for a
given McPat input file.

After this inspect the constructed tree from TreeBuilder and the changes
performed by each of the transformations steps.

You can enable debugging with the --debug option, see machine/options.py and
debug.py in the m5mbridge directory.
'''

PARTREF = 'all.modules.mcpat.importer.parser'

from m5mbridge import debug

import lexer
import parsetree
import comptree
from transforms import addParamAttributesToParamBlock, flattenNestedAttributes, cleanUpParagraphs, pullUpFromSeparatorBlocks
from comptree import groupLocalPredictors, enumerateCores, enumerateL1Dirs, mergeProcessorAndSystem, replaceBusesWithBusComponents, pullUpBranchTargetBuffer, pullUpBranchPredictor, pullUpItlb, pullUpDtlb, splitLoadStoreQueue, pullUpRegisterFiles
from parsetree import Block, TreeBuilder

class McPatParser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.tokList = []
        self.tree = None
        self.componentTree = None

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def parse(self):
        self.collectTokens()
        self.buildTree()
        self.createComponentTree()

    def collectTokens(self):
        for t in self.lexer:
            indent = t['indent']
            token = t['token']
            self.collectToken(indent, token)

    def collectToken(self, indent, token):
        typ = token[0]

        # Use the separator lines as borders between parts of the output. Some
        # parts are indented but don't belong logically to the preceeding
        # token. For example the Technology, etc. parameters. Luckily they're
        # preceeded by such a separator line.
        #
        # Append a synthetic paragraph token after each separator. This is just
        # in case that a component token follows a separator with indentation,
        # i.e., a component that starts not at the beginning of a line. The
        # paragraph token is inserted, because separators are removed early in
        # the post-processing step and having just one structural token type
        # (paragraph) simplifies the tree.
        #
        # Note: adding a paragraph makes the pullUpFromSeparatorBlocks()
        # delegates the task of fixing the position of the Technology, Clock
        # Rate, etc. parameters from the separator blocks to the paragraph
        # blocks. Which is nice, because paragraphs are used for just that kind
        # of grouping.
        if typ == 'separator':
            self.tokList.append((indent, token))
            self.tokList.append((indent, lexer.mt('paragraph')))
        elif typ == 'paragraph':
            if len(self.tokList):
                indent = self.tokList[-1][0]
            else:
                indent = 0
            self.tokList.append((indent, token))
        else: # Store token
            self.tokList.append((indent, token))

    # These transforms are called in the listed order by the buildTree() method.
    TRANSFORMS = [
            pullUpFromSeparatorBlocks,
            flattenNestedAttributes,
            addParamAttributesToParamBlock,
            cleanUpParagraphs
    ]

    # These transforms work like those in TRANSFORMS, but instead of
    # manipulating the parse-tree, they operate on the component-tree.
    COMPTREE_TRANSFORMS = [
            groupLocalPredictors,
            enumerateCores,
            enumerateL1Dirs,
            mergeProcessorAndSystem,
            replaceBusesWithBusComponents,
            pullUpBranchTargetBuffer,
            pullUpBranchPredictor,
            pullUpItlb,
            pullUpDtlb,
            splitLoadStoreQueue,
            pullUpRegisterFiles
    ]

    def buildTree(self):
        '''Create a tree from the token list created by the lexer.

        The tree is subjected to some post-processing as mentioned in the module
        documentation.
        '''
        builder = TreeBuilder(self.tokList)
        tree = builder.createTree()
        self.debug('initial parsetree', tree)

        for transform in self.TRANSFORMS:
            tree = transform(tree)
            self.debug("After applying transform {0}".format(transform.__name__), tree)

        self.tree = tree

    def createComponentTree(self):
        '''Converts the parse-tree to a component-tree.

        The component tree matches the component tree generated by the m5parser.
        '''
        compTree = comptree.createFromParseTree(self.tree)
        self.debug('initial comptree', compTree)

        for transform in self.COMPTREE_TRANSFORMS:
            compTree = transform(compTree)
            self.debug("After applying comp-tree transform {0}".format(transform.__name__), compTree)

        self.componentTree = compTree
