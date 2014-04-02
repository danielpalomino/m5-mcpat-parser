PARTREF = 'all.modules.m5.importer.configparser'

from m5mbridge import panic, warning, debug
from m5mbridge.machine.translator import Translator

class M5ConfigParser(object):
    def __init__(self, config_file, options):
        self.config_file = config_file
        self.options = options

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def run(self):
        cht = {}
        id = None #the id of current system component
        params = {} #params set for the current config

        #add all the components to the dictionary
        for line in self.config_file:

            #look for a new param id
            if '[' in line and ']' in line and '=' not in line:
                id = line.rstrip().rstrip(']').lstrip('[')
                if  cht.has_key(id):
                    warning("Identical component id '{0}' occurs twice! Invalid Config".format(id))

            #find params for id
            elif id:
                temp = line.split('=')
                #assume that a newline or line without an = is the beginning of the next component
                if len(temp) == 0 or len(temp) == 1:
                    self.debug('creating component {0} with params = {1}'.format(id, params))
                    cht[id]=Translator.createComponent(id, params)
                    params = {}
                    id = None
                #grab the param
                else:
                    if len(temp) != 2 and temp[0] != 'boot_osflags':
                        warning("A param with more than one '=' occurred: %s. parts=%d" %(line, len(temp)))
                    params[temp[0]]=temp[1].rstrip()
        # Return the component hash
        return cht
