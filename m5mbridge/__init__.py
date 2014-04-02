import os
import sys
import traceback

def bug(msg):
    sys.stderr.write(msg+'\n')
    sys.stderr.writelines('Stack trace to bug:\n')
    traceback.print_stack()

    if sys.stdout.isatty():
        sys.stderr.write("Entering debugger... (use the debugger command 'up' to move to stack frame where bug() was called)\n")
        try:
            # Try to use ipdb if available
            import ipdb
            ipdb.set_trace()
        except ImportError:
            import pdb
            pdb.set_trace()
    else:
        raise RuntimeError, "Bug encountered...aborting."

def panic(msg, code=9):
    sys.stderr.write("Error: {0}\n".format(msg))
    os.sys.exit(code)

def warning(msg):
    sys.stderr.write("Warning: {0}\n".format(msg))

def getController(options = None):
    '''See setup.py's docstring for the need of this function.

    The `options' argument is only used during initialization.
    '''
    import setup
    return setup.getController(options)
