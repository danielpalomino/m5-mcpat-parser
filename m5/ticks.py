# (Simulator) ticks per second
tps = 1.0e12 # 1THz <==> 1 pico sedond per tick

tps_fixed = False # see function fixGlobalFrequency()

def fixGlobalFrequency():
    '''Only meaningful for the M5 simulator.

    In M5 this function tells the simulation core the simulation frequency
    (ticks per seconds, tps). Once the simulation frequency is set it cannot be
    changed.
    '''
    global tps_fixed
    tps_fixed = True

# how big does a rounding error need to be before we warn about it?
frequency_tolerance = 0.001  # 0.1%

## fromSeconds is (mostly) copied from gem5/src/python/ticks.py
def fromSeconds(value):
    if not isinstance(value, float):
        raise TypeError, "can't convert '%s' to type tick" % type(value)

    if value == 0:
        return 0

    # convert the value from time to ticks
    value *= tps

    int_value = int(round(value))
    err = (value - int_value) / value
    if err > frequency_tolerance:
        print >>sys.stderr, "Warning: rounding error > tolerance"
        print >>sys.stderr, "    %f rounded to %d" % (value, int_value)
    return int_value

def toSeconds(tcks):
    '''Convert ticks to seconds.'''
    return tcks/tps
