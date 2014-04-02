'''
The functions in this module are used to
(1) add statistics that are composed from several other statistics and params that
can be seen by the translator objects in the next phase.
(2) rename newly generated components to meet the McPat specifications
(3) move children components to a new parent component to meet the right xml form
(4) generate components that have no direct correlation to a single component
in the M5 machine description
This code is the least generic and will likely needed to be changed by new users.
If there is a bug, it probably is in this module ... X_X
'''

PARTREF = 'all.modules.m5.importer.generatecalcparts'

from copy import deepcopy
import re
import math

from m5mbridge import bug, panic, warning, debug
from m5mbridge.machine.component import Component
from m5mbridge.machine.translator import Translator
from m5mbridge.machine.visitor import Visitor

def generateCalcComponents(options, cht, sht):
    num_cores=0
    num_l1s=0
    num_l2s=0
    num_l3s=0
    num_nocs=0
    clock_rate=0
    o3_cpu_exists=False
    timing_cpu_exists=False
    homogeneous_cores="0"
    homogeneous_L2s="0"
    homogeneous_L3s="0"
    homogeneous_L1s="0"
    homogeneous_L2Directories="0"
    homogeneous_L1Directories="0"
    homogeneous_nocs="0"
    num_cache_levels=0
    new_components_to_add=[]
    components_to_remove=[]
    fastest_clock=None

    for c_key in cht:
        #grab generic component info
        component = cht[c_key]
        if not component.params.has_key('type'):
            continue
        params = component.params
        ptype = params['type']
        component_name = component.name

        if ("server" in c_key and options.system_name != "server" and "vncserver" not in c_key) or ("client" in c_key and options.system_name != "client"):
            bug("Fix me: power_xml_filter no longer exists, it's now part of the DefaultOutputFilter visitor in module tree2mcpat.")
            component.power_xml_filter=True

        if ptype == 'Bus' or ptype == 'CoherentBus' or ptype == "BusConn":

            num_ports=len(getPorts(component))
            for pair in options.interconn_names.split('#'):
                name, util = pair.split(',')
                if name in component.name:
                    component.re_name = component.name.replace(name, "noc%s"%num_nocs)
                    component.re_id = component.id.replace(name, "NoC%s"%num_nocs)
                    num_nocs = str(int(num_nocs)+1)
                    break
            cpu_clock_rate = int(1/(float(params['clock'])*1e-6))
            component.params["clockrate"] = str(cpu_clock_rate)
            component.params["input_ports"] = str(num_ports)
            component.params["output_ports"] = str(num_ports)
            bus_name = component_name


            ports = getPorts(component)
            for port in ports:
                #remove port name to find component this bus is attached to
                temp = port.split('.')
                comp_id = genId(temp[0:len(temp)-1])

                if not cht.has_key(comp_id):
                    panic("unable to find component: %s" % (comp_id), 1)

                #add the bus width to the component to make it easier for the power model
                cht[comp_id].params[bus_name + ".width"] = params['width']

        if ptype == 'Mesh2D':
            for pair in options.interconn_names.split('#'):
                name, util = pair.split(',')
                if name in component.name:
                    component.re_name = component.name.replace(name, "noc%s"%num_nocs)
                    component.re_id = component.id.replace(name, "NoC%s"%num_nocs)
                    homogeneous_nocs = str(int(num_nocs)+1)
                    break
            cpu_clock_rate=int(1/(float(params['clock'])*1e-6)) # 1/(tick_per_period*1e-12*1e6)
            component.params["clockrate"] = str(cpu_clock_rate)
            component.params["topology"] = "2Dmesh"
            num_ports=len(getPorts(component))
            component.params["horizontal_nodes"] = str(int(math.sqrt(num_ports))) #Makes assumption about the topology being near square like
            component.params["vertical_nodes"] = str(int(math.ceil(num_ports/float(component.params["horizontal_nodes"])))) #square like topology examinations
            component.params["has_global_link"] = "0" #FIXME: what is this?
            component.params["link_latency"] = "1"
            component.params["link_throughput"] = "1"
            component.params["input_ports"] = str(num_ports)
            component.params["output_ports"] = str(num_ports)
            component.params["flit_bits"] = str()

        #how many cores are there
        if options.cpu_name in component_name and (ptype == "DerivO3CPU" or ptype == "TimingSimpleCPU" or ptype == "AtomicSimpleCPU"):
            clock=int(component.params['clock'])
            if fastest_clock == None or fastest_clock > clock:
                fastest_clock=clock
            num_cores += 1
            if num_cores > 1:
                homogeneous_cores="0"
            # ASSUMPTION: ticks are picoseconds and converting to MHz
            cpu_clock_rate=int(1/(float(params['clock'])*1e-6))
            if "DerivO3CPU" == ptype:
                o3_cpu_exists=True
            elif "TimingSimpleCPU" == ptype:
                timing_cpu_exists=True
            # ASSUMPTION: only timingSimpleCPU and O3CPU will be used
            #if o3_cpu_exists and timing_cpu_exists:
            #    homogeneous_cores="0"
            component.params["clockrate"] = str(cpu_clock_rate)
            if ptype == "TimingSimpleCPU":
                #move components to the detail_cpu from the cpu like the cache
                match = re.match(r"%s.%s([\.0-9a-zA-z_:]+)"%(options.system_name, options.cpu_name), component.id)
                if  match:
                    new_id = "%s.cpu%s" %(options.system_name, match.group(1))
                else:
                    new_id = "%s.cpu" %(options.system_name)
                #homogeneous system needs only one core identification
                if  not cht.has_key(component.id):
                    panic("cht does not have the key I generated for detailed cpu:%s" %(new_id),3)
                new_component = cht[new_id]
                if component != new_component and new_component.params.has_key('children'):
                    removed_children=["dcache","icache"]
                    for child in new_component.params['children'].split():
                        if child == "dcache" or child == "icache":
                            child_id = "%s.%s" %(new_id, child)
                            if not cht.has_key(child_id):
                                panic("child_id %s does not exist." %(child_id),4)
                            cht[child_id].id="%s.%s" % (component.id, child)
                            component.children.append(cht[child_id])

                    rm_list=[]
                    for ch in new_component.children:
                        if ch.name in removed_children:
                            rm_list.append(ch)
                    for rm_i in rm_list:
                        new_component.children.remove(rm_i)

                #add BTB  unit
                child_id=component.id+".BTB"
                new_params={}
                new_params["BTB_config"] = "%s,4,2,1,1,3" % ("8192")#FIXME: not enough
                new_params["type"] = "BTB"
                new_comp=Translator.createComponent(child_id, new_params)

                new_comp.re_name=new_comp.name.replace(options.cpu_name, "core")
                new_comp.re_id=new_comp.id.replace(options.cpu_name, "core")
                new_components_to_add.append((child_id,new_comp))
                component.children.append(new_comp)

                child_id=component.id+".predictor"
                new_params={}
                #new_params["local_predictor_size"] = "10,3" #FIXME: Where to grab this information
                #new_params["local_predictor_entries"] = "1024"
                #new_params["global_predictor_entries"] = "4096" #FIXME
                #new_params["global_predictor_bits"] = "2" #FIXME
                #new_params["chooser_predictor_entries"] = "4096" #FIXME
                #new_params["chooser_predictor_bits"] = "2" #FIXME
                #new_params["prediction_width"] = "1"
                new_params["type"] = "PBT"
                new_comp=Translator.createComponent(child_id, new_params, "PBT")
                new_comp.re_name=new_comp.name.replace(options.cpu_name, "core")
                new_comp.re_id=new_comp.id.replace(options.cpu_name, "core")
                new_components_to_add.append((child_id,new_comp))
                component.children.append(new_comp)

            if ptype == "DerivO3CPU":
                issue_width = int(component.params["issueWidth"])
                component.params["ALU_per_core"] = str(int(math.ceil(issue_width)))
                component.params["fp_issue_width"] = str(int(math.ceil(2/3.0*issue_width)))
                component.params["MUL_per_core"] = str(int(math.ceil(1/3.0*issue_width)))
                component.params["FPU_per_core"] = str(int(math.ceil(2/3.0*issue_width)))
                component.params["instruction_buffer_size"] = "16"#str(int(math.ceil(16/3.0*issue_width)))
                component.params["decoded_stream_buffer_size"] = str(int(math.ceil(8/3.0*issue_width)))
                component.params["memory_ports"] = str(int(math.ceil(1/3.0*issue_width)))



                #add branch predictor child:
                child_id=component.id+".predictor"
                new_params={}
                new_params["local_predictor_size"] = "10,3" #FIXME: Where to grab this information
                new_params["local_predictor_entries"] = component.params["localPredictorSize"]
                new_params["global_predictor_entries"] = component.params["globalPredictorSize"] #FIXME
                new_params["global_predictor_bits"] = "2" #FIXME
                new_params["chooser_predictor_entries"] = component.params["choicePredictorSize"] #FIXME
                new_params["chooser_predictor_bits"] = "2" #FIXME
                new_params["prediction_width"] = "1"
                new_params["type"] = "PBT"
                new_comp=Translator.createComponent(child_id, new_params, "PBT")
                new_comp.re_name=new_comp.name.replace(options.cpu_name, "core")
                new_comp.re_id=new_comp.id.replace(options.cpu_name, "core")
                new_components_to_add.append((child_id,new_comp))
                component.children.append(new_comp)

                #move components to the detail_cpu from the cpu like the cache
                match = re.match(r"%s.%s([\.0-9a-zA-z_:]+)"%(options.system_name, options.cpu_name), component.id)
                if match:
                    new_id = "%s.cpu%s" %(options.system_name,match.group(1))
                else:
                    new_id = "%s.cpu" %(options.system_name)
                #homogeneous system needs only one core identification
                if  not cht.has_key(component.id):
                    panic("cht does not have the key I generated for detailed cpu:%s" %(new_id),3)
                new_component = cht[new_id]
                if component != new_component and new_component.params.has_key('children'):
                    removed_children=["dcache","icache"]
                    for child in new_component.params['children'].split():
                        if child == "dcache" or child == "icache":
                            child_id = "%s.%s" %(new_id, child)
                            if not cht.has_key(child_id):
                                panic("child_id %s does not exist." %(child_id),4)
                            cht[child_id].id="%s.%s" % (component.id, child)
                            component.children.append(cht[child_id])
                    for ch in new_component.children:
                        if ch.name in removed_children:
                            new_component.children.remove(ch)

                #add BTB  unit
                child_id=component.id+".BTB"
                new_params={}
                new_params["BTB_config"] = "%s,4,2,1,1,3" % (component.params["BTBEntries"])#FIXME: not enough
                new_params["type"] = "BTB"
                new_comp=Translator.createComponent(child_id, new_params)
                new_comp.associated_cpu = component

                new_comp.re_name=new_comp.name.replace(options.cpu_name, "core")
                new_comp.re_id=new_comp.id.replace(options.cpu_name, "core")
                new_components_to_add.append((child_id,new_comp))
                component.children.append(new_comp)

        if ptype == "BaseCache":
            try:
                banked  = component.params["banked"]
                num_banks = component.params["numBanks"]
            except:
                banked = "false"
                num_banks=1
            num_mshrs=int(component.params["mshrs"])
            if num_mshrs < 4:
                num_mshrs=4
            component.params["buffer_sizes"]= "%d,%d,%d,%d" % (num_mshrs,num_mshrs,num_mshrs,num_mshrs)
            size = component.params["size"]
            block_size = component.params["block_size"]
            assoc = component.params["assoc"]
            if banked == "false":
                banked="0"
                num_banks="1"
            else:
                banked="1"

            if "icache" in component_name or "dcache" in component_name:
                temp = component.id.split('.')
                core_component = temp[0]+'.'+temp[1]
                latency_wrt_core = str(int(math.ceil(float(component.params["latency"])/float(cht[core_component].params["clock"]))))
                if "icache" in component_name:
                    cache_config_type="icache_config"
                else:
                    cache_config_type="dcache_config"
                component.params[cache_config_type] = "%s,%s,%s,%s,%s,%s" % (size, block_size, assoc, num_banks, "1", latency_wrt_core) #TODO: set throughput w.r.t core clock
            #add l2 directory
            if ("l2" in component_name) or ("l3" in component_name):
                component.re_name=component.name.replace("l","L")
                component.re_id=component.id.replace("l","L")
                match = re.match(r".*(l[0-9])([0-9]*)", component_name)
                cache_qualifier=match.group(1).upper()
                new_cache_qualifier=None
                if "l3" in component_name:
                    new_cache_qualifier=cache_qualifier.replace("L3","L2")
                else:
                    new_cache_qualifier=cache_qualifier.replace("L2","L1")
                cache_number='0'
                if match.group(2) != '':
                    cache_number=match.group(2)
                else:
                    component.re_name=component.re_name+cache_number
                    component.re_id=component.re_id+cache_number
                child_id="%s.%sDirectory%s" % (options.system_name, new_cache_qualifier, cache_number)
                core_component="%s.%s0"%(options.system_name, options.cpu_name)
                if not cht.has_key(core_component):
                    core_component="%s.%s00"%(options.system_name, options.cpu_name)
                    if not cht.has_key(core_component):
                        core_component ="%s.%s"%(options.system_name, options.cpu_name)


                new_params={}
                new_params["clockrate"] = str(int(1/(float(component.params["latency"])*1e-6)))
                dir_size = str(int(float(size)/float(block_size)))
                latency_wrt_core = str(int(math.ceil(float(component.params["latency"])/float(cht[core_component].params["clock"]))))
                dir_block_size=block_size
                dir_number_banks=num_banks
                if "l2" in component_name:
                    dir_block_size="16" #block_size of 64 causes problems for L1Directory so I hardcoded 16
                    dir_number_banks="1" #bank_size not equal to 1 causes problems for the L1DIrectory.

                new_params["Dir_config"] = "%s,%s,%s,%s,%s,%s" % (dir_size,dir_block_size,assoc,dir_number_banks,"1", latency_wrt_core)#TODO: set throughput w.r.t core clock,
                new_params["type"] = "Dir_config"
                new_comp=Translator.createComponent(child_id, new_params)
                new_comp.params["clockrate"] = str(int(1/(float(component.params["latency"])*1e-6)))
                new_comp.associated_cache = component

                new_components_to_add.append((child_id,new_comp))
                cht[options.system_name].children.append(new_comp)
                component.params["%s_config"%(cache_qualifier)] = "%s,%s,%s,%s,%s,%s,%s,%s" % (size, block_size, assoc, num_banks, "32", latency_wrt_core,"12","1") #TODO: set throughput w.r.t core clock
                component.params["buffer_sizes"]= "%s,%s,%s,%s" % (component.params["mshrs"], component.params["mshrs"], component.params["mshrs"], component.params["mshrs"])
                component.params["clockrate"] = str(int(1/(float(component.params["latency"])*1e-6)))


        if "physmem" in component_name and options.system_name in component.id:
                component.re_name=component.name.replace("physmem","mem")
                component.re_id=component.id.replace("physmem","mem")

                child_id="%s.mc" %(options.system_name)
                new_params={}
                new_params["mc_clock"] = str(int(1/(float(component.params["latency"])*1e-6)))
                new_params["type"] = "mc"
                new_comp=Translator.createComponent(child_id, new_params)
                new_comp.associated_pmem = component
                new_components_to_add.append((child_id,new_comp))
                cht[options.system_name].children.append(new_comp)


        # The following three if statements all assume that if there's only one
        # cache in a hierarchy it's cache used for data and instructions. For
        # directories of cache coherency protocols its switches from shared to
        # exclusive directories if there is more than one cache in the next
        # higher hierarchy.

        if ptype == "BaseCache" and ("dcache" in component_name or "icache" in component_name):
            if num_cache_levels < 1:
                num_cache_levels = 1
            num_l1s += 1
            if num_l1s ==1:
                homogeneous_L1s="1"
            elif num_l1s > 1:
                homogeneous_L1s="0"

        if ptype == "BaseCache" and "l2" in component_name:
            if num_cache_levels < 2:
                num_cache_levels = 2
            num_l2s +=1
            if num_l2s ==1:
                homogeneous_L1Directories="1"
                homogeneous_L2s="1"
            elif num_l2s > 1:
                homogeneous_L1Directories="0"
                homogeneous_L2s="0"
        if ptype == "BaseCache" and "l3" in component_name:
            if num_cache_levels < 3:
                num_cache_levels = 3
            num_l3s +=1
            if num_l3s ==1:
                homogeneous_L2Directories="1"
                homogeneous_L3s="1"
            elif num_l3s > 1:
                homogeneous_L2Directories="0"
                homogeneous_L3s="0"


    # Add a fake NIC
    niu_id = "%s.niu" %(options.system_name)
    new_params = {}
    new_params["type"] = "niu"
    niu = Translator.createComponent(niu_id, new_params)
    new_components_to_add.append((niu_id,niu))
    cht[options.system_name].children.append(niu)

    # Add a fake PCI Express Controller
    pcie_id = "%s.pcie" %(options.system_name)
    new_params = {}
    new_params["type"] = "pcie"
    pcie = Translator.createComponent(pcie_id, new_params)
    new_components_to_add.append((pcie_id, pcie))
    cht[options.system_name].children.append(pcie)

    # Add a fake Flash Controller
    flash_id = "%s.flashc" %(options.system_name)
    new_params = {}
    new_params["type"] = "flashc"
    flash = Translator.createComponent(flash_id, new_params)
    new_components_to_add.append((flash_id, flash))
    cht[options.system_name].children.append(flash)

    for key_id, new_comp in new_components_to_add:
        cht[key_id]=new_comp

    cht[options.system_name].params["fastest_clock"] = str(fastest_clock)
    cht[options.system_name].params["number_of_cores"] = str(num_cores)
    cht[options.system_name].params["number_of_L1Directories"] = str(num_l1s)
    cht[options.system_name].params["number_of_L2s"] = str(num_l2s)
    cht[options.system_name].params["number_of_L2Directories"] = str(num_l3s)
    cht[options.system_name].params["number_of_L3s"] = str(num_l3s)
    cht[options.system_name].params["number_of_nocs"] = str(num_nocs)
    cht[options.system_name].params["homogeneous_cores"] = str(homogeneous_cores)
    cht[options.system_name].params["number_cache_levels"] = str(num_cache_levels)
    cht[options.system_name].params["homogeneous_L2s"] = str(homogeneous_L2s)
    cht[options.system_name].params["homogeneous_L3s"] = str(homogeneous_L3s)
    cht[options.system_name].params["homogeneous_L1Directories"] = str(homogeneous_L1Directories)
    cht[options.system_name].params["homogeneous_L2Directories"] = str(homogeneous_L2Directories)
    cht[options.system_name].params["number_of_dir_levels"] = str(num_cache_levels-1)
    cht[options.system_name].params["homogeneous_nocs"] = str(homogeneous_nocs)

def getPorts(component):
    # In Gem5 changeset 17f037ad8918 (30 Mar 2012) the combined port
    # class was split in a master and slave sub-class.
    if component.params.has_key('port'):
        return component.params['port'].split()
    else:
        ports = component.params['master'].split()
        ports.extend(component.params['slave'].split())
        return ports


def generateCalcStats(options, cht, sht):
    for c_key in cht:
        component = cht[c_key]
        ptype = component.params['type']

        #add subcomponents to different major components.
        if ptype == 'AlphaTLB':
            data_hits = tryGrabComponentStat(component, "data_hits", conversion="int")
            data_misses= tryGrabComponentStat(component, "data_misses", conversion="int")
            fetch_hits= tryGrabComponentStat(component, "fetch_hits", conversion="int")
            fetch_misses=tryGrabComponentStat(component, "fetch_misses", conversion="int")
            write_hits=tryGrabComponentStat(component, "write_hits", conversion="int")
            write_misses=tryGrabComponentStat(component, "write_misses", conversion="int")
            read_hits=tryGrabComponentStat(component, "read_hits", conversion="int")
            read_misses=tryGrabComponentStat(component, "read_misses", conversion="int")
            component.statistics["total_accesses"] = str(data_hits+ data_misses + fetch_hits + fetch_misses)
            component.statistics["write_accesses"] = str(write_hits+write_misses)
            component.statistics["read_accesses"] = str(read_hits+read_misses)

        elif ptype == 'Mesh2D':
            component.statistics["total_routing_counts"] = 0
            for stat_key in component.statistics:
                if "routing_counts" in stat_key:
                    stat = component.statistics[stat_key]
                    component.statistics["total_routing_counts"] += int(stat)
            component.statistics["total_routing_counts"] = str(tryGrabComponentStat(component, "total_routing_counts", conversion="int"))

        elif ptype == "BTB":
            # If we have an O3 CPU model we can take it from its branch
            # predictor statistics, else we don't have this information and set
            # it to zero.
            if hasattr(component, 'cpu'):
                cpu = component.associated_cpu # Set in generateCalcComponents
                component.statistics["total_accesses"] = str(tryGrabComponentStat(cpu, "BPredUnit.lookups", conversion="int"))
                component.statistics["total_hits"] = str(tryGrabComponentStat(cpu, "BPredUnit.BTBHits", conversion="int"))
                component.statistics["total_misses"] = str(tryGrabComponentStat(cpu, "BPredUnit.lookups", conversion="int") - tryGrabComponentStat(cpu, "BPredUnit.BTBHits", conversion="int"))
            else:
                component.statistics["total_accesses"] = "0"#component.statistics["BPredUnit.lookups"]
                component.statistics["total_hits"] = "0"#component.statistics["BPredUnit.BTBHits"]
                component.statistics["total_misses"] = '0'#str(int(component.statistics["BPredUnit.lookups"]) - int(component.statistics["BPredUnit.BTBHits"]))

        elif ptype == "DerivO3CPU":
            component.statistics["fp_instructions"] = str(tryGrabComponentStat(component, "iq.FU_type_0::FloatAdd", conversion="int")  + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::FloatCmp", conversion="int")  + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::FloatCvt", conversion="int")  + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::FloatMult", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::FloatDiv", conversion="int")  + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::FloatSqrt", conversion="int"))
            component.statistics["int_instructions"] =  str(tryGrabComponentStat(component, "iq.FU_type_0::No_OpClass", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::IntAlu", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::IntMult", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::IntDiv", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::IprAccess", conversion="int"))
            try:
                component.statistics["committed_int_instructions"] = str(int(float(component["int_instructions"])\
                                                            /(float(component["int_instructions"])+float(component["fp_instructions"]))\
                                                            *int(component["commit:count"])))
                component.statistics["committed_fp_instructions"] = str(int(float(component["fp_instructions"])\
                                                            /(float(component["int_instructions"])+float(component["fp_instructions"]))\
                                                            *int(component["commit.count"])))
            except:
                component.statistics["committed_int_instructions"] = "0"
                component.statistics["committed_fp_instructions"] = "0"
            component.statistics["load_instructions"] = str(tryGrabComponentStat(component, "iq.FU_type_0::MemRead", conversion="int") + \
                                                        tryGrabComponentStat(component, "iq.FU_type_0::InstPrefetch", conversion="int"))
            component.statistics["store_instructions"] = str(tryGrabComponentStat(component, "iq.FU_type_0::MemWrite", conversion="int"))
            component.statistics["num_busy_cycles"] = str(tryGrabComponentStat(component, "numCycles", conversion="int") - tryGrabComponentStat(component, "idleCycles", conversion="int"))

        elif ptype == "Dir_config":
            cache = component.associated_cache # Set in generateCalcComponents
            try:
                component.statistics["read_accesses"] = str(int(cache["directory_transactions::Shared_ReadMiss_1"]) + \
                                                        int(cache["directory_transactions::Uncached_ReadMiss_3"]) + \
                                                        int(cache["directory_transactions::Modified_ReadMiss_5"]))
                                                        #component.statistics["directory_transactions::Internal_Shared_Fetch_11"] + \
                                                        #component.statistics["directory_transactions::Internal_Modified_Fetch_10"]
                component.statistics["write_accesses"] = str(int(cache["directory_transactions::Shared_ReadExMiss_0"]) + \
                                                        int(cache["directory_transactions::Uncached_ReadExMiss_4"]) + \
                                                        int(cache["directory_transactions::Modified_ReadExMiss_6"]))
                                                        #component.statistics["directory_transactions::Shared_Invalidate_2"] + \
                                                        #component.statistics["directory_transactions::Modified_WritebackInvalidate_7"] + \
                                                        #component.statistics["directory_transactions::Internal_Shared_Invalidate_8"] + \
                                                        #component.statistics["directory_transactions::Internal_Modified_Invalidate_9"]
            except:
                component.statistics["read_accesses"] = "0"
                component.statistics["write_accesses"] = "0"

        # Calculate the stats for the memory controlle and the physical memory.
        # These components are tightly coupled, so we need to process them in
        # the correct order. First the physical memory, then the memory
        # controller.
        elif ptype == 'PhysicalMemory' or ptype == 'SimpleMemory' or ptype == 'mc':
            # If mc is processed prior to physical memory, the calculated
            # attributes are not yet visible to it. Thus we process them
            # on-demand.
            comp = component
            if ptype == 'mc':
                comp = component.associated_pmem
            # add some stats:
            try:
                s = comp.statistics
                if s.has_key('num_reads::total'):
                    s['num_phys_mem_reads'] = s['num_reads::total']
                if s.has_key('num_writes::total'):
                    s['num_phys_mem_writes'] = s['num_writes::total']

                comp.statistics["num_phys_mem_accesses"] = str(int(comp.statistics["num_phys_mem_reads"]) \
                                + int(comp.statistics["num_phys_mem_writes"]))
            except:
                comp.statistics["num_phys_mem_accesses"] = "0"

            # Now we can actually process the mc.
            if ptype == 'mc':
                pmem = component.associated_pmem # Set in generateCalcComponents
                try:
                    component.statistics["num_phys_mem_accesses"] = str(int(pmem.statistics["num_phys_mem_accesses"]))
                    component.statistics["num_phys_mem_reads"] = str(int(pmem.statistics["num_phys_mem_reads"]))
                    component.statistics["num_phys_mem_writes"] = str(int(pmem.statistics["num_phys_mem_writes"]))
                except:
                    component.statistics["num_phys_mem_accesses"] = "0"
                    component.statistics["num_phys_mem_reads"] = "0"
                    component.statistics["num_phys_mem_writes"] = "0"

    # add calculated statistics
    tick_key = "%s.sim_ticks"%(options.system_name)
    if tick_key in sht:
        fastest_clock = cht[options.system_name].params["fastest_clock"]
        cht[options.system_name].statistics["total_cycles"] = str(int(sht[tick_key])/int(fastest_clock))


'''
genId will take a list of system components and concat
them to make a specific component of stat identifier.
'''
def genId(id_list):
    return '.'.join(id_list)

def tryGrabComponentStat(component, stat, conversion="int"):
    try:
        value=str(component.statistics[stat])
    except:
        value="0"

    if conversion=="int":
        value=int(value)
    elif conversion=="float":
        value=float(value)
    else:
        panic("unable to perform conversion", 8)
    return value

def addVirtualComponents(machine):
    tree = machine.tree
    cpuName = machine.options.cpu_name
    isCpu = lambda x: x.name.startswith(cpuName) # True for all cpu components

    # For all cpus: add an instruction fetch unit and move the icache to it
    debug.pp(PARTREF, 'adding component IFU, inheriting icache')
    addComponentAndInheritSubtree(tree,
        isCpu,        # Boolean filter function to identify components
        'icache',     # Component to move
        'ifu',        # New component's name
        type = 'IFU') # and parameter(s)

    # For all cpus: add a load/store unit and move the dcache to it
    debug.pp(PARTREF, 'adding component LSU, inheriting dcache')
    addComponentAndInheritSubtree(tree, isCpu, 'dcache', 'lsu', type = 'LSU')

    # For all cpus: add a load queue to their lsu
    debug.pp(PARTREF, 'adding loadqueue to LSU')
    forAllAddNewComponent(tree, 'lsu', 'loadqueue', type = 'LOADQ')

    # For all cpus: add a store queue to their lsu
    debug.pp(PARTREF, 'adding storequeue to LSU')
    forAllAddNewComponent(tree, 'lsu', 'storequeue', type = 'STOREQ')

    # For all cpus: add an execution unit
    debug.pp(PARTREF, 'adding execution unit')
    forAllAddNewComponent(tree, isCpu, 'execunit', type = 'EXECU')

    # For all cpus: add a register file to their execunit
    debug.pp(PARTREF, 'adding register files to execunit')
    forAllAddNewComponent(tree, 'execunit', 'intrf', type = 'INTRF')
    forAllAddNewComponent(tree, 'execunit', 'floatrf', type = 'FLOATRF')

    # For all cpus: add integer ALU
    debug.pp(PARTREF, 'adding integer ALU')
    forAllAddNewComponent(tree, 'execunit', 'alu', type = 'ALU')

    # For all cpus: add FPU
    debug.pp(PARTREF, 'adding FPU')
    forAllAddNewComponent(tree, 'execunit', 'fpu', type = 'FPU')

    # For all cpus: add an instruction scheduler
    debug.pp(PARTREF, 'adding instruction scheduler')
    forAllAddNewComponent(tree, 'execunit', 'scheduler', type = 'SCHEDULER')

    # For all cpus: add regular and floating point instruction windows
    debug.pp(PARTREF, 'adding instruction windows')
    forAllAddNewComponent(tree, 'scheduler', 'window', type = 'WINDOW')
    forAllAddNewComponent(tree, 'scheduler', 'fpwindow', type = 'WINDOW')


class AddComponent(Visitor):
    '''Add a component to the component tree below a configurable node.

    This class adds additional components that have no direct correspondance in
    Gem5's machine configuration. It is similar to the generateCalcComponents
    function, but uses a cleaner interface to do so.

    The constructor takes an instance of class Component and adds it to the
    first component in the component-tree for which the given `tester' returns
    true. The `tester' can bei either a custom function that takes the
    currently visited component as its sole argument or a component name. If
    the cloneForAllMatches parameter is true it clones the component instance
    and adds it to all components for which the tester yields true.

    The component's id attribute it automatically re-created to match the place
    where it is inserted. Only the last part of the id-field is used when
    constructing the new id.

    The new component is always appended to the parent's child list, i.e.,
    after visiting the tree with an AddComponent visitor the new components are
    the last elements in their parent's children list.
    '''

    def __init__(self, component, tester, cloneForAllMatches = False):
        super(AddComponent, self).__init__()

        if not callable(tester):
            self.tester = lambda c: c.name == tester
        else:
            self.tester = tester

        self.component = component
        self.alreadyAdded = False
        self.cloneForAllMatches = cloneForAllMatches

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def visit(self, component):
        if self.tester(component):
            self.addChild(component)

    def addChild(self, component):
        if not self.cloneForAllMatches and self.alreadyAdded:
            return

        if not self.cloneForAllMatches:
            self.doAddChild(component, self.component)
            self.alreadyAdded = True
        else:
            self.doAddChild(component, deepcopy(self.component))

    def doAddChild(self, parent, child):
        id = parent.id + child.id.split('.')[-1]
        child.id = id
        self.debug("adding child {0} to component {1}".format(child.name, parent.name))
        parent.children.append(child)

def createComponent(name, **params):
    return Component(name, params)

def addNewComponent(tree, parentNameOrTester, name, **params):
    c = createComponent(name, **params)
    v = AddComponent(c, parentNameOrTester)
    tree.visit(v)

def forAllAddNewComponent(tree, parentNameOrTester, name, **params):
    c = createComponent(name, **params)
    v = AddComponent(c, parentNameOrTester, True)
    tree.visit(v)

class ComponentNotFound(Exception):
    def __init__(self, tree, name):
        self.tree = tree
        self.name = name

    def __str__(self):
        return "Cannot find component '{0}' in tree '{1}'".format(name, tree)

def findComponent(tree, name):
    '''Find a component in the component tree by name.'''

    class FindVisitor(Visitor):
        def __init__(self):
            super(FindVisitor, self).__init__()
            self.component = None
        def visit(self, component):
            if component.name == name:
                self.component = component

    v = FindVisitor()
    tree.visit(v)
    if v.component:
        return v.component
    raise ComponentNotFound(tree, name)

class RootIsImmutable(Exception):
    def __str__(self):
        return "Tried to move the 'root' component, which is forbidden!"

class MoveSubtree(Visitor):
    '''Move a subtree to another component.

    This visitor takes the new parent (a Component instance or a name) and a
    tester which can be either a name or a function that returns true if the
    subtree was found.

    Moving the root of the tree is not allowed and the visitor raises a
    RootIsImmutable exception.

    All subtrees for which the tester evaluates to true are moved to the new parent.

    If newParent is an instance of class Component the parameter `tree' can be
    set to None, it is only needed if newParent is a name/string.
    '''

    def __init__(self, tree, newParent, tester):
        super(MoveSubtree, self).__init__()

        self.tree = tree

        if not callable(tester):
            self.tester = lambda c: c.name == tester
        else:
            self.tester = tester

        if not isinstance(newParent, Component):
            newParent = findComponent(tree, newParent)
        self.newParent = newParent

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def visit(self, component):
        if not self.tester(component): return

        parent = self.parent()
        # parent() returns only None if there is no element on the stack
        # yet, meaning that we're currently visiting the root component.
        if not parent: raise RootIsImmutable()

        self.debug('moving subtree, component {0} is now parent of'.format(self.newParent.name), component)

        parent.children.remove(component)
        self.newParent.children.append(component)

def moveSubtree(tree, subtreeNameOrTester, newParent):
    '''Move subtree subtreeNameOrTester TO newParent.'''
    v = MoveSubtree(tree, newParent, subtreeNameOrTester)
    tree.visit(v)

class AddComponentAndInheritSubtree(Visitor):
    '''Add a component and make it parent of a child.

    This visitor adds a new component as child of another component, the
    commonParent and in a second step it moves a child of the commonParent to
    the children list of the new component. In other words, it pushes a subtree
    of a node down into a newly added node. This is used for example to move
    the icache node of the cpu component into the ifu component which is a
    child of the cpu component.

    This visitor can do this operation for more than one node, e.g., create an
    ifu component for all cpus and move their icache node to it.

    As with the AddComponent and MoveSubtree visitor the commonParent and
    subtreeToMove parameters can be either a boolean function that takes a
    component as its sole argument, or the name of a component.
    '''
    def __init__(self, commonParent, newComponent, subtreeToMove):
        super(AddComponentAndInheritSubtree, self).__init__()

        if not callable(commonParent):
            self.isCommonParent = lambda c: c.name == commonParent
        else:
            self.isCommonParent = commonParent

        self.newComponent = newComponent

        if not callable(subtreeToMove):
            self.isSubtreeToMove = lambda c: c.name == subtreeToMove
        else:
            self.isSubtreeToMove = subtreeToMove

    def debug(self, *args):
        debug.pp(PARTREF, *args)

    def visit(self, component):
        if not self.isCommonParent(component): return

        self.debug('about to add a component and moving a subtree')

        # Add a copy of the new component
        adder = AddComponent(self.newComponent, self.isCommonParent, True)
        adder.pushParent(self.parent()) # Be nice and set up the parent stack
        adder.visit(component)

        # Move the subtree to the new component
        newParent = component.children[-1] # Guaranteed to be the last element.
        mover = MoveSubtree(None, newParent, self.isSubtreeToMove)
        mover.pushParent(component) # Be nice and set up the parent stack
        for child in component.children:
            mover.visit(child)

def addComponentAndInheritSubtree(tree, commonParent, subtreeToMove, name, **params):
    c = createComponent(name, **params)
    v = AddComponentAndInheritSubtree(commonParent, c, subtreeToMove)
    tree.visit(v)
