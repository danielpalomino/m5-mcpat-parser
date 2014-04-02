PARTREF = 'all.modules.mcpat.importer'

from m5mbridge import debug

from importer import PatImporter
from lexer import McPatLexer
from parser import McPatParser

def importMcPatData(machine, mcpatOutput):
    debug.pp(PARTREF, 'mcpat output', mcpatOutput)

    lex = McPatLexer(mcpatOutput)
    parser = McPatParser(lex)

    parser.parse()

    debug.pp(PARTREF, 'comptree', parser.componentTree)

    imp = PatImporter(parser.componentTree, machine.options)
    machine.visit(imp)
