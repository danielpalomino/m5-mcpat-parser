'''This module provides parsing, importing and clearing of access statistics.'''

PARTREF = 'all.modules.m5.importer.stats'

from m5mbridge import bug, panic, warning, debug
import re
from generatecalcparts import generateCalcStats
from generatecalcparts import genId

def importStatsFromFile(stats_file_path, machine):
    '''Like importStats but reads from a file given as a path.'''
    with open(stats_file_path, 'r') as stats_file:
        importStats(stats_file, machine)

def importStats(stats_file, machine):
    '''Convenience function to simplify stats importing.

    This function uses the M5StatsParser class to read the stats.txt file
    generated by M5 and adds the stats data to the machine's component tree
    using the M5StatsImporter class.

    stats_file must be an open file object.'''

    debug.pp(PARTREF, 'parsing stats')
    parser = M5StatsParser(stats_file, machine.options)
    sht = parser.run()
    debug.pp(PARTREF, 'importing stats')
    importer = M5StatsImporter(machine, sht)
    importer.run()

class M5StatsParser(object):
    def __init__(self, stats_file, options):
        self.stats_file = stats_file
        self.options = options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def run(self):
        sht = {}
        #add all the statistics to the dictionary
        for line in self.stats_file:
            #print line
            match = re.match("(%s[\.0-9a-zA-z_:]*)\s+([\w\.]+)\s+"%(self.options.system_name), line)
            if match:
                self.debug('sht[{0}] = {1} (1st try)'.format(match.group(1), match.group(2)))
                sht[match.group(1)] = match.group(2)
                continue

            #match = re.match(r"(client[\.0-9a-zA-z_:]*)\s+([\w\.]+)\s+", line)
            #if match:
            #    #sht[match.group(1)] = match.group(2)
            #    continue
            #
            #match = re.match(r"(server[\.0-9a-zA-z_:]*)\s+([\w\.]+)\s+", line)
            #if match:
            #    #sht[match.group(1)] = match.group(2)
            #    continue

            match = re.match(r"(global[\.0-9a-zA-z_:]*)\s+([\w\.]+)\s+", line)
            if  match:
                self.debug('sht[{0}] = {1} (2nd try)'.format(match.group(1), match.group(2)))
                sht[match.group(1)] = match.group(2)
                continue

            match = re.match(r"([\.0-9a-zA-z_:]*)\s+([\w\.]+)\s+", line)
            if  match:
                self.debug('sht[{0}] = {1} (3rd try)'.format(match.group(1), match.group(2)))
                sht["%s."%(self.options.system_name)+match.group(1)] = match.group(2)
                #sht[match.group(1)] = match.group(2)
                continue

        return sht

class M5StatsImporter(object):
    def __init__(self, machine, sht):
        self.machine = machine
        self.cht = machine.cht
        self.sht = sht
        self.tree = machine.tree
        self.options = machine.options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def run(self):

        self.debug('clearing component stats')
        clearComponentStats(self.machine)

        #add all statistics to right component
        for stat_key in self.sht:
            #find the longest prefix that matches a component id
            stat = self.sht[stat_key]
            temp = stat_key.split('.')
            num_fields = len(temp)
            prefix_id = None

            for x in xrange(num_fields, 0, -1):
                prefix_id = genId(temp[0:x])
                if self.cht.has_key(prefix_id):
                    break

            #add the statistic to the right component
            stat_id = genId(temp[x:num_fields])
            if len(stat_id) < 1:
                panic("error: parsed invalid stat.",6)

            #for all those stats that don't have a component, add it to root component
            if not self.cht.has_key(prefix_id):
                prefix_id="root"
                stat_id = genId(temp)

            self.debug('{0}.stats[{1}] = {2}'.format(prefix_id, stat_id, stat))
            component = self.cht[prefix_id]
            component.statistics[stat_id] = stat

        # generate calculated statistics
        self.debug('generating calculated stats')
        generateCalcStats(self.options, self.cht, self.sht)


        # translate statistics
        self.debug('translating statistics')
        self.machine.visit(lambda x: x.translator and x.translator.translate_statistics(x))

def clearComponentStats(machine):
    '''Resets all access statistics of every component.'''
    machine.visit(clearComponentStat)

def clearComponentStat(component):
    component.statistics.clear()
    component.translated_statistics.clear()
    del component.translated_statistics_order[:]