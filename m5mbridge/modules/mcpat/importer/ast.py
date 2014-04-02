'''An abstract syntax tree for McPat output and a converter.'''

import re

class UnknownType(Exception):
    def __init__(self, node):
        self.node = node

    def __str__(self):
        return "Parse-tree node of unknown type encountered: {0}\n\nData: {1}".format(self.node.typ, self.node.data)

class Ast(object):
    def __init__(self, name, typ, parent = None):
        self.name = name
        self.typ = typ
        self.children = []
        self.parent = parent

    def addChild(self, child):
        self.children.append(child)

    def addChildren(self, children):
        self.children.extend(children)

class AstMcPatVersion(Ast):
    def __init__(self, typ, parent, data):
        super(AstMcPatVersion, self).__init__("Version", typ, parent)
        # data = ("McPAT (version 0.8 of Aug, 2010) is computing the target processor...")
        self.version = re.search(r'\(version ([\w\s,.:;-_/]+)\)', data[0]).group(1)

class AstTechnology(Ast):
    def __init__(self, typ, parent, data):
        super(AstTechnology, self).__init__("Technology", typ, parent)
        # data = (("Technology", "90 nm"),)
        (self.featureSize, self.sizeUnit) = data[0][1].split()
        self.featureSize = int(self.featureSize)

class AstLongChannelDev(Ast):
    def __init__(self, typ, parent, data):
        super(AstLongChannelDev, self).__init__("LongChannelDevices", typ, parent)
        self.present = True

class AstConvertInterconnectProjection(Ast):
    def __init__(self, typ, parent, data):
        super(AstConvertInterconnectProjection, self).__init__("ConvertInterconnectProjection", typ, parent)
        # data = (('Interconnect metal projection', 'aggressive interconnect technology projection'),)
        self.conversionType = data[0][1]

class AstClockRate(Ast):
    def __init__(self, typ, parent, data):
        super(AstClockRate, self).__init__("ClockRate", typ, parent)
        # data = (('Core clock Rate', '1200 MHz'),)
        (self.frequency, self.unit) = data[0][1].split()

class TreeToAstConverter(object):
    def __init__(self, tree):
        self.tree = tree

    def convert(self):
        return self.convertTree(self.tree, None)

    def convertTree(self, node, parent):
        astChildren = []

        for child in node.children:
            astChildren.append(self.convertTree(child, node))

        ast = self.convertNode(node, parent)
        ast.addChildren(astChildren)

        return ast

    def convertNode(self, node, parent):
        name = 'convert{0}{1}'.format(node.typ[0].upper(), node.typ[1:])
        try:
            converter = getattr(self, name)
            return converter(node, parent)
        except AttributeError, e:
            raise UnknownType(node)

    def convertMetaData(self, node, parent):
        if node.data[0].find('is computing the target processor'):
            return AstMcPatVersion(node.typ, parent, node.data)
        # else discard

    def convertTechnology(self, node, parent):
        return AstTechnology(node.typ, parent, node.data)

    def convertLongChannelDevices(self, node, parent):
        return AstLongChannelDev(node.typ, parent, node.data)

    def convertInterconnectProjection(self, node, parent):
        return AstConvertInterconnectProjection(node, parent, node.data)

    def convertClockRate(self, node, parent):
        return AstClockRate(node, parent, node.data)

    def convertParameter(self, node):
        pass

    def convertComponent(self, node):
        pass
