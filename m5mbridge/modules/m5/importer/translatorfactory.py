PARTREF = 'all.modules.m5.importer.translatorfactory'
import sys
from m5mbridge import bug, panic, warning, debug
import translators

class TranslatorFactory(object):

    '''
    create takes as input a component object, and assigns
    the translator field to the right type of Translator object. Translator
    objects are responsible for grabbing the right stats and naming them
    correctly.
    If no translator is needed, this function returns None.
    '''
    @staticmethod
    def create(options, component):

        translatorClass = None

        for pair in options.interconn_names.split('#'):
            name, util = pair.split(',')
            if name in component.name:
                if component.params['type'] == "Bus":
                    translatorClass = translators.Bus
                elif component.params['type'] == 'CoherentBus':
                    translatorClass = translators.Bus
                elif component.params['type'] == "BusConn":
                    translatorClass = translators.BusConn
                elif component.params['type'] == "Mesh2D":
                    translatorClass = translators.Mesh
                elif component.params['type'] == "Crossbar":
                    translatorClass = translators.Crossbar

                if translatorClass:
                    return translatorClass(options)
                return None

        if options.cpu_name in component.name:
            if component.params['type'] == "TimingSimpleCPU":
                translatorClass = translators.InOrderCore
            if component.params['type'] == "DerivO3CPU":
                translatorClass = translators.OOOCore
        elif options.itb_name in component.name:
            translatorClass = translators.ITLB
        elif options.dtb_name in component.name:
            translatorClass = translators.DTLB
        elif "icache" in component.name:
            if component.params['type'] == "BaseCache":
                translatorClass = translators.InstructionCache
        elif "dcache" in component.name:
            if component.params['type'] == "BaseCache":
                translatorClass = translators.DataCache
        elif "Directory" in component.name:
            if "L1" in component.name:
                translatorClass = translators.L1Directory
            elif "L2" in component.name:
                translatorClass = translators.L2Directory
        elif "l2" in component.name:
            if component.params['type'] == "BaseCache":
                translatorClass = translators.SharedCacheL2
        elif "l3" in component.name:
            if component.params['type'] == "BaseCache":
                translatorClass = translators.SharedCacheL3
        elif "physmem" in component.name:
            translatorClass = translators.PhysicalMemory
        elif options.system_name == component.name:
            translatorClass = translators.System
        elif "PBT" in component.name:
            translatorClass = translators.Predictor
        elif "BTB" in component.name:
            translatorClass = translators.BTB
        elif "mc" in component.name:
            translatorClass = translators.MC
        elif "niu" in component.name:
            translatorClass = translators.NIC
        elif "pcie" in component.name:
            translatorClass = translators.PCIE
        elif "flash" in component.name:
            translatorClass = translators.Flash

        if translatorClass:
            debug.pp(PARTREF, 'component {0}: using translator {1}'.format(component.name, translatorClass.__name__))
            return translatorClass(options)
        debug.pp(PARTREF, 'component {0}: no translator found'.format(component.name))
        return None
