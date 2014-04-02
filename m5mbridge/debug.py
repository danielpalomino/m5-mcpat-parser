'''Debbuging interface for the m5mbridge.

All parts of m5mbridge that support debugging must be registered here.
Debugging is hierarchical to control the degree of debugging output that is
desired.

Every part is a direct or indirect child of the debugging class 'all' which
enables debugging globally. Children of 'all' are, for example mcpat and m5
which have as children importer and exporter.

For example to enable debugging for the mcpat module you use the following path
specifier: all.modules.mcpat

In general every individual part is separated with a ., similar to a / in
filesystem paths. Such a path is call a partref.

Debugging for a module is enabled if the debugging flag is set for its partref
or for a partref of an ancestor. For example for the mcpat module debugging is
enabled if the debugging flag is set for any of the following partrefs:
'all.modules.mcpat', 'all.modules' or 'all'.

For more information on the allowed command-line syntax see the docstring of
enable_debugging_from_options.
'''

import inspect

from m5mbridge import bug, warning

DEBUGGABLE_PARTS = set([
    'all',
    'all.controller',
    'all.controller.playback',
    'all.controller.recorder',
    'all.modules',
    'all.modules.m5',
    'all.modules.m5.importer',
    'all.modules.m5.importer.configparser',
    'all.modules.m5.importer.generatecalcparts',
    'all.modules.m5.importer.machinefactory',
    'all.modules.m5.importer.stats',
    'all.modules.m5.importer.translatorfactory',
    'all.modules.m5.exporter',
    'all.modules.mcpat',
    'all.modules.mcpat.importer',
    'all.modules.mcpat.importer.lexer',
    'all.modules.mcpat.importer.parser',
    'all.modules.mcpat.exporter',
    'all.modules.mcpat.exporter.prunetree',
    'all.modules.mcpat.exporter.tree2mcpat',
    'all.modules.mcpat.exporter.tree2xml',
])

# Create a dict with the partrefs as key and a boolean flag as value indicating
# whether debugging for that partref is enabled or disabled.
DEBUG = dict((part, False) for part in DEBUGGABLE_PARTS)

# This is a subset of DEBUGGABLE_PARTS which have debugging currently enabled,
# i.e., for those keys in DEBUG which have a True value as value.
DEBUGGED_PARTS = set()

def enabled(partref):
    'Check if debugging for the given partref is enabled.'
    return partref in DEBUGGED_PARTS

def enable(partref):
    'Enable debugging for partref and all children.'
    if DEBUG.has_key(partref):
        DEBUG[partref] = True
    else:
        warning("Attempt to enable debugging for non-existing part '{0}' ignored.".format(partref))

def shortref(partref):
    '''Return an abbreviated but unique partref.

    This function returns an abbreviated partref as accepted by
    enable_debugging_from_options that is still unique among all parts which
    have have debugging enabled.
    '''

    if not partref in DEBUGGED_PARTS:
        bug('Cannot find partref {0} in debugged parts {1}.'.format(partref, DEBUGGED_PARTS))

    parts = partref.split('.')

    # Iterate over all possible abbreviations, starting with the shortest (just
    # the last part name in the partref). The first that is unique is returned.
    sref = ''
    for part in reversed(parts):
        newSref = part + sref
        if len([p for p in DEBUGGED_PARTS if p.endswith(newSref)]) == 1:
            return newSref
        sref = '.' + newSref

    # No abbreviation possible, need the full name
    return partref


def enable_debugging_from_options(partrefList):
    '''Parses the argument of the --debug optional argument.

    Iterate the colon-separated list of partrefs of --debug and enable
    debugging for all listed parts. To enhance the user experience it is not
    required that the partrefs are written out in full. Partial partrefs are
    allowed and if there's more than one part with that partref debugging for
    all of them is enabled. For example the partref 'importer' would enable
    debugging for all.modules.mcpat.importer and all.modules.m5.importer, but
    the partref 'm5.importer' enables debugging just for
    all.modules.m5.importer.

    Enabling debugging for a part implicitly enables debugging for all subparts
    of that part. If that is not wanted the partref can end in a '-' character,
    which disabled the implicit inclusion of subparts. For example
    modules.mcpat- enabled debugging only for the part with partref
    all.modules.mcpat but none of its subparts, e.g.,
    all.modules.mcpat.importer.

    For even more information about parsing see the docstring of
    possible_matches.
    '''

    withSubParts = filter(lambda x: not x.endswith('-'), partrefList)
    withoutSubParts = filter(lambda x: x.endswith('-'), partrefList)

    # Reset, just in case.
    global DEBUGGED_PARTS
    DEBUGGED_PARTS = set()

    __enable_debugging_from_options(withSubParts)
    update_debugged_parts(__enabled)

    # Now that update_debugged_parts() enabled debugging for all sub-parts, we
    # can set the debug flag for partrefs that should not activate debugging
    # for their children. We also have to remove the trailing '-' character.
    __enable_debugging_from_options(map(lambda x: x[:-1], withoutSubParts))
    update_debugged_parts(lambda p: DEBUG.get(p, False))

    if len(DEBUGGED_PARTS):
        print "Debugging enabled for", DEBUGGED_PARTS

def __enable_debugging_from_options(partrefList):
    '''Set debug flag for all partrefs that end in an element of the list.

    This function sets the debug flag in DEBUG for any partref from
    DEBUGGABLE_PARTS that ends in a suffix from the `partrefList'.
    '''
    for partref in partrefList:
        possibleParts = possible_matches(partref)

        if len(possibleParts) > 1:
            warning("More than one part matches '{0}': {1}".format(partref, possibleParts))
        elif len(possibleParts) == 0:
            warning("Ignoring unknown partref '{0}'".format(partref))

        for part in possibleParts:
            DEBUG[part] = True

def possible_matches(partref):
    '''Returns all partrefs that end in the given shortref/partial partref.

    If the shortref contains a . it returns all partrefs that end in the given
    shortref, else the shortref must match the last component of the shortref
    exactly. This is to avoid, for example matching of 'modules.mcpat' and
    'mcpat.exporter.tree2mcpat' with the shortref 'mcpat'.
    '''
    if '.' in partref:
        f = lambda x: x.endswith(partref)
    else:
        f = lambda x: x.split('.')[-1] == partref
    return [part for part in DEBUGGABLE_PARTS if f(part)]


def update_debugged_parts(enabled):
    global DEBUGGED_PARTS
    DEBUGGED_PARTS.update(part for part in DEBUGGABLE_PARTS if enabled(part))

def __enabled(partref):
    'Check if debugging for the given partref is enabled.'
    parts = partref.split('.')

    # Iterate over all ancestors, starting with the most remote ancestor, i.e.
    # 'all'.
    ancestor = ''
    for part in parts:
        ancestor += part
        if DEBUG.get(ancestor, False):
            return True
        ancestor += '.' # Append a dot for next part name.

    return False

def pp(partref, *args):
    'A pretty printer for debug messages.'
    if not partref in DEBUGGED_PARTS:
        if not partref in DEBUGGABLE_PARTS:
            warning('debug.pp called for unknown partref {0}'.format(partref))
        return
    args = map(str, args) # Convert args to strings (required for joining them)
    s = '\n'.join(args).replace('\n', '\n\t')
    print "{0}: {1}".format(shortref(partref), s)

def caller_name(fully_qualified = True):
    '''Return name of caller from our caller.

    This helper uses Python's introspection interface to find the name of the
    caller from our caller. Using this function makes the intention more clear
    than an ugly inspect.stack()[1][3] in our caller's code.
    '''
    if fully_qualified:
        return __caller_name(3)
    return inspect.stack()[2][3]

def __caller_name(skip=2):
    '''Get a fully qualified name of a caller in the format module.class.method.

    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

    An empty string is returned if skipped levels exceed stack height

    Taken from https://gist.github.com/2151727 (License: public domain).
    '''
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)
