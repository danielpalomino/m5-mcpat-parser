from orca.scripts import default
import re
import traceback
from m5mbridge import bug, panic, warning
from m5mbridge.machine.component import Component

'''
class Translator is used for finding and adding params and stats
to the xml. Define a translator for each unique component in your system
and make sure you add the assignment of the translator in setComponentType
'''
class Translator(object):
    M5_PARAM=0
    CONVERSION=1
    DEFAULT_VALUE=2
    M5_STAT=3

    # Used by get_component_statistic to search for vector-type statistics.
    STAT_VECTOR_SUFFIX = re.compile('.*::([0-9]+|total)')

    __component_class = {}

    @staticmethod
    def registerComponentClass(name, cls):
        Translator.__component_class[name] = cls

    @staticmethod
    def createComponent(id, *args):
        name = id.split('.')[-1]
        if name in Translator.__component_class:
            return Translator.__component_class[name](id, *args)
        else:
            return Component(id, *args)

    def __init__(self, options):
        self.power_params_order = []
        self.power_params = {}
        self.power_statistics = {}
        self.power_statistics_order = []
        self.options = options
        None

    def addPowerParam(self, power_key, m5_key, default_value="NaV"):
        if not self.power_params.has_key(power_key):
            self.power_params_order.append(power_key)
        self.power_params[power_key] = {Translator.M5_PARAM: m5_key, Translator.DEFAULT_VALUE: default_value}

    def addPowerStat(self, power_key, m5_key, default_value="NaV"):
        if not self.power_statistics.has_key(power_key):
            self.power_statistics_order.append(power_key)
        self.power_statistics[power_key] = {Translator.M5_STAT: m5_key, Translator.DEFAULT_VALUE: default_value}

    def translate(self, component):
        '''Generic translator function.

        This method is intended for derived translator classes that need to do more
        translation than just translating <param> and <stat> names. It is used for
        example to change a component's name or id (attributes re_id and re_name).
        '''
        pass

    '''
    translate_params(component) translates all params in component object
    from m5 parameters to the equivalent power model name
    '''
    def translate_params(self, component):
        for power_param_key in self.power_params_order:
            power_param = self.power_params[power_param_key]
            #grab M5's version of the parameter needed and translate it to power file name
            self.translate_param(component, power_param, power_param_key)
    '''
    translate_param(component, power_param) responsible for translating one M5 parameter
    to an m5 parameter and adding that parameter to the component translated_params variable
    '''
    def translate_param(self, component, power_param, key):
        #find the translated value if it exists
        component.translated_params_order.append(key)
        try:
            component.translated_params[key] = component.params[power_param[Translator.M5_PARAM]]
        except:
            #if it doesn't exist, use a default value
            component.translated_params[key] = power_param[Translator.DEFAULT_VALUE]

    '''
    translate_statistics(component) translates all statistics in component object
    from m5 statistics to the equivalent power model statistics
    '''
    def translate_statistics(self, component):
        for power_stat_key in self.power_statistics_order:
            power_stat = self.power_statistics[power_stat_key]
            #grab M5's version of the statistic needed and translate it to power file stat
            self.translate_statistic(component, power_stat, power_stat_key)

    '''
    translate_statistc(component, power_param) responsible for translating one M5 statistic
    to a m5 statistic and adding that parameter to the component translated_statistics variable
    '''
    def translate_statistic(self, component, power_stat, key):
        #find the translated value if it exists
        component.translated_statistics_order.append(key)
        try:
            component.translated_statistics[key] = self.get_component_statistic(component, power_stat[Translator.M5_STAT])
        except KeyError:
            #if it doesn't exist, use a default value
            component.translated_statistics[key] = power_stat[Translator.DEFAULT_VALUE]

    def get_component_statistic(self, component, stat_key):
        '''Find the statistics entry named stat_key in component.statistics.

        This function can also handle accesses to stats that have a suffix
        appended starting with ::. There are basically two important types of
        such suffixes: explicit suffixes, e.g., blocked_cycles::no_mshrs and
        index-suffixes of vectors, e.g., demand_avg_miss_latency::0 with an
        optional running total, e.g., ReadExReq_avg_miss_latency::total.

        This function fails if stat_key is not an exact match, unless it is a
        vector. In that case it tries to use the total value, if that value is
        not a number, often it is 'inf', it uses the value of the first index
        with a real number. If there is no such index the function fails and
        the default value is used.
        '''

        if stat_key in component.statistics:
            return component.statistics[stat_key]

        keys = component.statistics.keys()
        matches = filter(lambda x: x.startswith(stat_key) and self.STAT_VECTOR_SUFFIX.match(x), keys)

        if len(matches) == 0:
            raise KeyError(stat_key)

        # Check if ::total exists and is real
        total_stat_key = stat_key + '::total'
        if total_stat_key in matches:
            val = component.statistics[total_stat_key]
            if is_number(val):
                return val

        # Else loop through the matches, starting with ::0 and return the first real result

        # Remove the ::total entry and then sort the array, due to
        # lexicographical sorting we get the entries in ascending order and can
        # just iterate over it.
        total_idx = matches.index(total_stat_key)
        del matches[total_idx]
        matches.sort() # Rember: list.sort() is in-place!

        for key in matches:
            val = component.statistics[key]
            if is_number(val):
                return val

        # No matching entry found
        raise KeyError(stat_key)


def is_number(num):
    '''Check if the given string is a real floating point number, i.e., it's a float and not NaN or +-Inf.'''
    try:
        f = float(num)
        return num != 'inf' and num != 'nan'
    except ValueError:
        return False
