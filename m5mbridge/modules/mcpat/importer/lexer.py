'''See the parser module for documentation.'''

PARTREF = 'all.modules.mcpat.importer.lexer'

import re

from m5mbridge import debug

class LexerException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Lexer, ' + self.msg

class UnknownToken(LexerException):
    def __init__(self, line):
        super(UnknownToken, self).__init__("unrecognized input: '{0}'".format(line))

# Takes a list of arguments, strips trailing and leading whitespace and
# returns the arguments in a tuple.
def mt(*args):
    res = []
    for arg in args:
        arg = arg or ''
        res.append(arg.strip())
    return tuple(res)

class McPatLexer(object):
    # Higher level structural/meta-data related tokens. The juicy bits are
    # matched using the patterns in WORDEXPS below. The difference between
    # these two classes is that the TOKEXPS have the whole input line as data,
    # while the WORDEXPS extract parts of the input line which can be later
    # used to translate it into the proper data type.
    #
    # For example all lines containing Processor:, Core: or L2 are different
    # hardware components and the lexer does not match each individually, but
    # detects these as a common type of token: the 'component'. Doing this
    # avoids hard-coding of all possible components and attributes. And it's
    # also not necessary, because we already did that in the m5parser and just
    # need to match the names to the component names of the m5parser generated
    # components.
    TOKEXPS = {
            r'(?i)^McPat \(version.*(computing|results).+$' : 'metaData',
            r'^\**$' : 'separator',
            r'^\s*$' : 'paragraph',
            r'^\s*config\s*:.*$' : 'creationTime',
            r'^\s*request\s*:.*$' : 'computationTime'
    }

    # Unfortunately McPat's output is very irregular and thus order of the
    # regular expressions is important.
    # For example the L2 section uses "L2" as opening tag instead of "L2:" like
    # most others do and thus the component regexp does not require a colon at
    # the end and would also match the Technology, etc. parameters in the
    # header section.
    WORDEXPS = [
            (r'(?i)^\s*(Technology)\s*([0-9]+\s*nm)\s*$',
                lambda m: ('technology', mt(m.group(1), m.group(2)))),

            (r'(?i)^\s*(Interconnect\s*Metal\s*Projection)\s*=\s*([\w ]+)$',
                lambda m: ('interconnectProjection', mt(m.group(1), m.group(2)))),

            (r'(?i)^\s*(Using\s*long\s*channel\s*devices\s*when\s*appropriate)\s*',
                lambda m: ('longChannelDevices', mt(m.group(1)))),

            (r'(?i)^\s*(Core\s*clock\s*rate)\s*\((MHz)\)\s([0-9]+)$',
                lambda m: ('clockRate', mt(m.group(1), '{0} {1}'.format(m.group(3), m.group(2))))),

            (r'^\s*(?!Total)(\w[\w/ ]+(\s*\([\w/: ]+\))*)\s*:?\s*$',
                lambda m: ('component', mt(m.group(1)))),

            (r'^\s*(Total\s*\w[\w )(/]+)\s*:\s*(\w[\w ]+)?$',
                lambda m: ('parameter', mt(m.group(1), m.group(2)))),

            (r'^\s*([\w ]+)\s*[:=]\s*([-+\w][-\w .^+]+)$',
                lambda m: ('attribute', mt(m.group(1), m.group(2))))
    ]

    def __init__(self, mcpatDump):
        self.lines = mcpatDump.splitlines()
        self.pos = 0

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def __iter__(self):
        return self

    def next(self):
        if self.pos >= len(self.lines):
            raise StopIteration

        pos = self.pos
        self.pos = self.pos + 1
        t = self.fetchToken(pos)
        self.debug('token', t)
        return t

    def peekToken(self):
        if self.pos+1 >= len(self.lines):
            return '' # Peek line should never fails, to simplify parser!
        return self.fetchToken(self.pos+1)

    def fetchToken(self, pos):
        line = self.lines[pos]
        return { 'indent' : self.getIndent(line),
                 'token' : self.createToken(line) }

    def getIndent(self, line):
        return len(line) - len(line.lstrip())

    def createToken(self, line):
        tokType = self.categorize(line)
        if tokType:
            return (tokType, line)
        return self.splitLine(line)

    def categorize(self, line):
        for pattern in self.TOKEXPS:
            if re.match(pattern, line):
                tok = self.TOKEXPS[pattern]
                return tok
        return None

    def splitLine(self, line):
        for group in self.WORDEXPS:
            (pattern, f) = group
            m = re.match(pattern, line)
            if m:
                return f(m)
        raise UnknownToken(line)
