import os.path
from time import time

import ticks

def getOutputDir():
    return os.path.realpath('.')

startTime = None
def curTick():
    global startTime
    if startTime is None:
        startTime = time()
    now = time()
    return ticks.fromSeconds(now - startTime)
