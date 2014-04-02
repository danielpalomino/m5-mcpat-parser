def fatal(msg):
    print "Fatal error:", msg
    import pdb
    pdb.set_trace()

def curTick():
    import core
    return core.curTick()
