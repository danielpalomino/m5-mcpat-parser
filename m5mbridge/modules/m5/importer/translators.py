import pdb

from m5mbridge import bug, panic, warning
from m5mbridge.machine.translator import Translator
from m5mbridge.machine.component import SystemComponent

class CoreTranslator(Translator):
    def translate(self, component):
        if self.options.cpu_name in component.name:
            component.re_name = component.name.replace(self.options.cpu_name, "core")
            component.re_id = component.id.replace(self.options.cpu_name, "core")

class InOrderCore(CoreTranslator):
    def __init__(self, options):
        super(InOrderCore, self).__init__(options)
        #reverse translation from m5 params to power params
        #params
        self.addPowerParam(power_key="clock_rate", m5_key="clockrate", default_value="NaV")
        self.addPowerParam(power_key="instruction_length", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="opcode_width", m5_key="unknown", default_value="7") #TODO: set your value
        self.addPowerParam(power_key="machine_type", m5_key="unknown", default_value="1") # 1 for inorder
        self.addPowerParam(power_key="number_hardware_threads", m5_key="numThreads", default_value="1")
        self.addPowerParam(power_key="fetch_width", m5_key="unknown", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="number_instruction_fetch_ports", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="decode_width", m5_key="unknown", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="issue_width", m5_key="unknown", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="commit_width", m5_key="unknown", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="fp_issue_width", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="prediction_width", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="pipelines_per_core", m5_key="unknown", default_value="1,1") #TODO: set your value
        self.addPowerParam(power_key="pipeline_depth", m5_key="unknown", default_value="7,7") #TODO: set your value
        self.addPowerParam(power_key="ALU_per_core", m5_key="unknown", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="MUL_per_core", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="FPU_per_core", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="instruction_buffer_size", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="decoded_stream_buffer_size", m5_key="unknown", default_value="16") #TODO: set your value
        self.addPowerParam(power_key="instruction_window_scheme", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="instruction_window_size", m5_key="unknown", default_value="20")
        self.addPowerParam(power_key="fp_instruction_window_size", m5_key="unknown", default_value="15")
        self.addPowerParam(power_key="ROB_size", m5_key="unknown", default_value="80")
        self.addPowerParam(power_key="archi_Regs_IRF_size", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="archi_Regs_FRF_size", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="phy_Regs_IRF_size", m5_key="unknown", default_value="80")
        self.addPowerParam(power_key="phy_Regs_FRF_size", m5_key="unknown", default_value="75")
        self.addPowerParam(power_key="rename_scheme", m5_key="unknown", default_value="0")
        self.addPowerParam(power_key="register_windows_size", m5_key="unknown", default_value="0")
        self.addPowerParam(power_key="LSU_order", m5_key="unknown", default_value="inorder") #TODO: set your value
        self.addPowerParam(power_key="store_buffer_size", m5_key="unknown", default_value="32")
        self.addPowerParam(power_key="load_buffer_size", m5_key="unknown", default_value="32")
        self.addPowerParam(power_key="memory_ports", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="RAS_size", m5_key="unknown", default_value="32")

        #statistics
        self.addPowerStat(power_key="total_instructions", m5_key="committedInsts", default_value="0")
        self.addPowerStat(power_key="int_instructions", m5_key="num_int_insts", default_value="0")
        self.addPowerStat(power_key="fp_instructions", m5_key="num_fp_insts", default_value="0")
        self.addPowerStat(power_key="branch_instructions", m5_key="num_conditional_control_insts", default_value="0") # TODO: check this
        self.addPowerStat(power_key="branch_mispredictions", m5_key="unknown", default_value="0") # TODO: set your value
        if options.old_m5_stats:
            self.addPowerStat(power_key="load_instructions", m5_key="load_insts", default_value="0")
            self.addPowerStat(power_key="store_instructions", m5_key="store_insts", default_value="0")
        else:
            self.addPowerStat(power_key="load_instructions", m5_key="num_load_insts", default_value="0")
            self.addPowerStat(power_key="store_instructions", m5_key="num_store_insts", default_value="0")

        self.addPowerStat(power_key="committed_instructions", m5_key="committedInsts", default_value="0")
        self.addPowerStat(power_key="committed_int_instructions", m5_key="num_int_insts", default_value="0")
        self.addPowerStat(power_key="committed_fp_instructions", m5_key="num_fp_insts", default_value="0")
        self.addPowerStat(power_key="pipeline_duty_cycle", m5_key="unknown", default_value="1.0") #TODO: set your value
        self.addPowerStat(power_key="total_cycles", m5_key="numCycles", default_value="0")
        self.addPowerStat(power_key="idle_cycles", m5_key="num_idle_cycles", default_value="0") #FIXME
        self.addPowerStat(power_key="busy_cycles", m5_key="num_busy_cycles", default_value="0") #FIXME
        self.addPowerStat(power_key="ROB_reads", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="ROB_writes", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="rename_accesses", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="fp_rename_accesses", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="inst_window_reads", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="inst_window_writes", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="inst_window_wakeup_access", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="fp_inst_window_reads", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="fp_inst_window_writes", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="fp_inst_window_wakeup_access", m5_key="unknown", default_value="0")
        self.addPowerStat(power_key="int_regfile_reads", m5_key="num_int_register_reads", default_value="0")
        if options.old_m5_stats:
            self.addPowerStat(power_key="float_regfile_reads", m5_key="num_float_register_reads", default_value="0")
        else:
            self.addPowerStat(power_key="float_regfile_reads", m5_key="num_fp_register_reads", default_value="0")
        self.addPowerStat(power_key="int_regfile_writes", m5_key="num_int_register_writes", default_value="0")
        if options.old_m5_stats:
            self.addPowerStat(power_key="float_regfile_writes", m5_key="num_float_register_writes", default_value="0")
        else:
            self.addPowerStat(power_key="float_regfile_writes", m5_key="num_fp_register_writes", default_value="0")
        self.addPowerStat(power_key="function_calls", m5_key="num_func_calls", default_value="0")
        self.addPowerStat(power_key="context_switches", m5_key="kern.swap_context", default_value="0")
        if options.old_m5_stats:
            self.addPowerStat(power_key="ialu_accesses", m5_key="num_ialu_accesses", default_value="0")
            self.addPowerStat(power_key="fpu_accesses", m5_key="num_falu_accesses", default_value="0")
        else:
            self.addPowerStat(power_key="ialu_accesses", m5_key="num_int_alu_accesses", default_value="0")
            self.addPowerStat(power_key="fpu_accesses", m5_key="num_fp_alu_accesses", default_value="0")
        self.addPowerStat(power_key="mul_accesses", m5_key="unknown", default_value="0") #TODO: FIXME
        if options.old_m5_stats:
            self.addPowerStat(power_key="cdb_alu_accesses", m5_key="num_ialu_accesses", default_value="0")
            self.addPowerStat(power_key="cdb_mul_accesses", m5_key="unknown", default_value="0") #TODO: FIXME
            self.addPowerStat(power_key="cdb_fpu_accesses", m5_key="num_falu_accesses", default_value="0")
        else:
            self.addPowerStat(power_key="cdb_alu_accesses", m5_key="num_int_alu_accesses", default_value="0")
            self.addPowerStat(power_key="cdb_mul_accesses", m5_key="unknown", default_value="0") #TODO: FIXME
            self.addPowerStat(power_key="cdb_fpu_accesses", m5_key="num_fp_alu_accesses", default_value="0")
        #DO NOT CHANGE BELOW UNLESS YOU KNOW WHAT YOU ARE DOING
        self.addPowerStat(power_key="IFU_duty_cycle", m5_key="unknown", default_value="0.5")
        self.addPowerStat(power_key="LSU_duty_cycle", m5_key="unknown", default_value="0.5")
        self.addPowerStat(power_key="MemManU_I_duty_cycle", m5_key="unknown", default_value="0.5")
        self.addPowerStat(power_key="MemManU_D_duty_cycle", m5_key="unknown", default_value="0.5")
        self.addPowerStat(power_key="ALU_duty_cycle", m5_key="unknown", default_value="1.0")
        self.addPowerStat(power_key="MUL_duty_cycle", m5_key="unknown", default_value="0.3")
        self.addPowerStat(power_key="FPU_duty_cycle", m5_key="unknown", default_value="1.0")
        self.addPowerStat(power_key="ALU_cdb_duty_cycle", m5_key="unknown", default_value="1.0")
        self.addPowerStat(power_key="MUL_cdb_duty_cycle", m5_key="unknown", default_value="0.3")
        self.addPowerStat(power_key="FPU_cdb_duty_cycle", m5_key="unknown", default_value="1.0")


class OOOCore(CoreTranslator):
    def __init__(self, options):
        super(OOOCore, self).__init__(options)
        #reverse translation from m5 params to power params
        #params
        self.addPowerParam(power_key="clock_rate", m5_key="clockrate")
        self.addPowerParam(power_key="opt_local", m5_key="unknown", default_value='1')
        self.addPowerParam(power_key="instruction_length", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="opcode_width", m5_key="unknown", default_value="7") #TODO: set your value
        self.addPowerParam(power_key="x86", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="micro_opcode_width", m5_key="unknown", default_value="8") #TODO: set your value
        self.addPowerParam(power_key="machine_type", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="number_hardware_threads", m5_key="numThreads", default_value="1")
        self.addPowerParam(power_key="fetch_width", m5_key="fetchWidth", default_value="4")
        self.addPowerParam(power_key="number_instruction_fetch_ports", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="decode_width", m5_key="decodeWidth", default_value="4")
        self.addPowerParam(power_key="issue_width", m5_key="issueWidth", default_value="4")
        self.addPowerParam(power_key="peak_issue_width", m5_key="issueWidth", default_value="6") #TODO: set your value
        self.addPowerParam(power_key="commit_width", m5_key="commitWidth", default_value="4")
        self.addPowerParam(power_key="fp_issue_width", m5_key="fp_issue_width", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="prediction_width", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="pipelines_per_core", m5_key="unknown", default_value="1,1") #TODO: set your value
        self.addPowerParam(power_key="pipeline_depth", m5_key="unknown", default_value="7,7") #TODO: set your value
        self.addPowerParam(power_key="ALU_per_core", m5_key="ALU_per_core", default_value="4") #TODO: set your value
        self.addPowerParam(power_key="MUL_per_core", m5_key="MUL_per_core", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="FPU_per_core", m5_key="FPU_per_core", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="instruction_buffer_size", m5_key="instruction_buffer_size", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="decoded_stream_buffer_size", m5_key="decoded_stream_buffer_size", default_value="16") #TODO: set your value
        self.addPowerParam(power_key="instruction_window_scheme", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="instruction_window_size", m5_key="numIQEntries", default_value="20")
        self.addPowerParam(power_key="fp_instruction_window_size", m5_key="numIQEntries", default_value="15")
        self.addPowerParam(power_key="ROB_size", m5_key="numROBEntries", default_value="80")
        self.addPowerParam(power_key="archi_Regs_IRF_size", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="archi_Regs_FRF_size", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="phy_Regs_IRF_size", m5_key="numPhysIntRegs", default_value="80")
        self.addPowerParam(power_key="phy_Regs_FRF_size", m5_key="numPhysFloatRegs", default_value="72")
        self.addPowerParam(power_key="rename_scheme", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="register_windows_size", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="LSU_order", m5_key="unknown", default_value="inorder") #TODO: set your value
        self.addPowerParam(power_key="store_buffer_size", m5_key="SQEntries", default_value="32")
        self.addPowerParam(power_key="load_buffer_size", m5_key="LQEntries", default_value="32")
        self.addPowerParam(power_key="memory_ports", m5_key="memory_ports", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="RAS_size", m5_key="RASSize", default_value="32")

        #statistics
        self.addPowerStat(power_key="total_instructions", m5_key="committedInsts", default_value="0")
        self.addPowerStat(power_key="int_instructions", m5_key="int_instructions", default_value="NaV")
        self.addPowerStat(power_key="fp_instructions", m5_key="fp_instructions", default_value="NaV")
        self.addPowerStat(power_key="branch_instructions", m5_key="BPredUnit.condPredicted", default_value="NaV")
        self.addPowerStat(power_key="branch_mispredictions", m5_key="BPredUnit.condIncorrect", default_value="NaV")
        self.addPowerStat(power_key="load_instructions", m5_key="load_instructions", default_value="NaV")
        self.addPowerStat(power_key="store_instructions", m5_key="store_instructions", default_value="NaV")
        self.addPowerStat(power_key="committed_instructions", m5_key="commit.count", default_value="NaV")
        self.addPowerStat(power_key="committed_int_instructions", m5_key="commit.int_insts", default_value="NaV")
        self.addPowerStat(power_key="committed_fp_instructions", m5_key="commit.fp_insts", default_value="NaV")
        self.addPowerStat(power_key="pipeline_duty_cycle", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerStat(power_key="total_cycles", m5_key="numCycles", default_value="NaV")
        self.addPowerStat(power_key="idle_cycles", m5_key="idleCycles", default_value="NaV")
        self.addPowerStat(power_key="busy_cycles", m5_key="num_busy_cycles", default_value="NaV")
        self.addPowerStat(power_key="ROB_reads", m5_key="rob_reads", default_value="34794891") #FIXME: rerun the experiments to include this statistic
        self.addPowerStat(power_key="ROB_writes", m5_key="rob_writes", default_value="34794891") #FIXME: rerun the experiments to include this statistic
        self.addPowerStat(power_key="rename_reads", m5_key="rename.int_rename_lookups", default_value="0")
        self.addPowerStat(power_key="rename_writes", m5_key="unknown", default_value="0") #TODO: FIXME
        self.addPowerStat(power_key="fp_rename_reads", m5_key="rename.fp_rename_lookups", default_value="0")
        self.addPowerStat(power_key="fp_rename_writes", m5_key="unknown", default_value="0") #TODO: FIXME
        self.addPowerStat(power_key="inst_window_reads", m5_key="iq.int_inst_queue_reads", default_value="NaV")
        self.addPowerStat(power_key="inst_window_writes", m5_key="iq.int_inst_queue_writes", default_value="NaV")
        self.addPowerStat(power_key="inst_window_wakeup_accesses", m5_key="iq.int_inst_queue_wakeup_accesses", default_value="NaV")
        self.addPowerStat(power_key="fp_inst_window_reads", m5_key="iq.fp_inst_queue_reads", default_value="0")
        self.addPowerStat(power_key="fp_inst_window_writes", m5_key="iq.fp_inst_queue_writes", default_value="NaV")
        self.addPowerStat(power_key="fp_inst_window_wakeup_accesses", m5_key="iq.fp_inst_queue_wakeup_accesses", default_value="NaV")
        self.addPowerStat(power_key="int_regfile_reads", m5_key="int_regfile_reads", default_value="0")
        self.addPowerStat(power_key="float_regfile_reads", m5_key="fp_regfile_reads", default_value="0")
        self.addPowerStat(power_key="int_regfile_writes", m5_key="int_regfile_writes", default_value="0")
        self.addPowerStat(power_key="float_regfile_writes", m5_key="fp_regfile_writes", default_value="0")
        self.addPowerStat(power_key="function_calls", m5_key="commit.function_calls", default_value="NaV")
        self.addPowerStat(power_key="context_switches", m5_key="kern.swap_context", default_value="0")
        self.addPowerStat(power_key="ialu_accesses", m5_key="iq.int_alu_accesses", default_value="NaV")
        self.addPowerStat(power_key="fpu_accesses", m5_key="iq.fp_alu_accesses", default_value="NaV")
        self.addPowerStat(power_key="mul_accesses", m5_key="iq.FU_type_0::IntMult", default_value="NaV")
        self.addPowerStat(power_key="cdb_alu_accesses", m5_key="iq.int_alu_accesses", default_value="NaV")
        self.addPowerStat(power_key="cdb_mul_accesses", m5_key="iq.FU_type_0::IntMult", default_value="NaV")
        self.addPowerStat(power_key="cdb_fpu_accesses", m5_key="iq.fp_alu_accesses", default_value="NaV")
        #DO NOT CHANGE BELOW UNLESS YOU KNOW WHAT YOU ARE DOING
        self.addPowerStat(power_key="IFU_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="LSU_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="MemManU_I_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="MemManU_D_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="ALU_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="MUL_duty_cycle", m5_key="unknown", default_value="0.3")
        self.addPowerStat(power_key="FPU_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="ALU_cdb_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="MUL_cdb_duty_cycle", m5_key="unknown", default_value="0.3")
        self.addPowerStat(power_key="FPU_cdb_duty_cycle", m5_key="unknown", default_value="1")
        self.addPowerStat(power_key="number_of_BPT", m5_key="unknown", default_value="2")

class ITLB(Translator):
    def __init__(self, options):
        super(ITLB, self).__init__(options)
        #params
        self.addPowerParam(power_key="number_entries", m5_key="size", default_value="128")
        #statistics
        self.addPowerStat(power_key="total_accesses", m5_key="fetch_accesses", default_value="0")
        self.addPowerStat(power_key="total_misses", m5_key="fetch_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="fetch_acv", default_value="0") #FIXME: add this stat to M5. Sheng says it is the number of evictions. This is a question for the M5 community(fixed by daniel).

    def translate(self, component):
        if component.name == self.options.itb_name:
            component.re_name = component.name.replace(self.options.itb_name,"itlb").replace(self.options.cpu_name, "core")
            component.re_id = component.id.replace(self.options.itb_name, "itlb").replace(self.options.cpu_name, "core")

class DTLB(Translator):
    def __init__(self, options):
        super(DTLB, self).__init__(options)
        #params
        self.addPowerParam(power_key="number_entries", m5_key="size", default_value="128")
        #statistics
        self.addPowerStat(power_key="read_accesses", m5_key="read_accesses", default_value="0")
        self.addPowerStat(power_key="write_accesses", m5_key="write_accesses", default_value="0")
        self.addPowerStat(power_key="read_misses", m5_key="read_misses", default_value="0")
        self.addPowerStat(power_key="write_misses", m5_key="write_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="data_acv", default_value="0") #FIXME: add this stat to M5. Sheng says it is the number of evictions. This is a question for the M5 community

    def translate(self, component):
        if component.name == self.options.dtb_name:
            component.re_name = component.name.replace(self.options.dtb_name,"dtlb").replace(self.options.cpu_name, "core")
            component.re_id = component.id.replace(self.options.dtb_name, "dtlb").replace(self.options.cpu_name, "core")

class BaseCache(Translator):
    def translate(self, component):
        if 'icache' in component.name or 'dcache' in component.name:
            component.re_name = component.name.replace(self.options.l1_cache_cpu_name, "core")
            component.re_id = component.id.replace(self.options.l1_cache_cpu_name, "core")

class InstructionCache(BaseCache):
    def __init__(self, options):
        super(InstructionCache, self).__init__(options)
        #params
        self.addPowerParam(power_key="icache_config", m5_key="icache_config")
        self.addPowerParam(power_key="buffer_sizes", m5_key="buffer_sizes")
        #statistics
        self.addPowerStat(power_key="read_accesses", m5_key="ReadReq_accesses", default_value="0")
        self.addPowerStat(power_key="read_misses", m5_key="ReadReq_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="replacements", default_value="0")

class DataCache(BaseCache):
    def __init__(self, options):
        super(DataCache, self).__init__(options)
        #params
        self.addPowerParam(power_key="dcache_config", m5_key="dcache_config")
        self.addPowerParam(power_key="buffer_sizes", m5_key="buffer_sizes")
        #statistics
        self.addPowerStat(power_key="read_accesses", m5_key="ReadReq_accesses", default_value="0")
        if options.old_m5_stats:
            self.addPowerStat(power_key="write_accesses", m5_key="ReadExReq_accesses", default_value="0")
        else:
            self.addPowerStat(power_key="write_accesses", m5_key="WriteReq_accesses", default_value="0")
        self.addPowerStat(power_key="read_misses", m5_key="ReadReq_misses", default_value="0")
        if options.old_m5_stats:
            self.addPowerStat(power_key="write_misses", m5_key="ReadExReq_misses", default_value="0")
        else:
            self.addPowerStat(power_key="write_misses", m5_key="WriteReq_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="replacements", default_value="0")

class SharedCacheL2(Translator):
    def __init__(self, options):
        super(SharedCacheL2, self).__init__(options)
        #params
        self.addPowerParam(power_key="L2_config", m5_key="L2_config")
        self.addPowerParam(power_key="buffer_sizes", m5_key="buffer_sizes")
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="NaV")
        self.addPowerParam(power_key="ports", m5_key="unknown", default_value="1,1,1") #TODO: specify your value
        self.addPowerParam(power_key="device_type", m5_key="unknown", default_value=options.cache_device_type) #TODO: specify your value
        ##statistics
        self.addPowerStat(power_key="read_accesses", m5_key="ReadReq_accesses", default_value="0")
        self.addPowerStat(power_key="write_accesses", m5_key="ReadExReq_accesses", default_value="0")
        self.addPowerStat(power_key="read_misses", m5_key="ReadReq_misses", default_value="0")
        self.addPowerStat(power_key="write_misses", m5_key="ReadExReq_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="replacements", default_value="0")
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1.0")

class SharedCacheL3(Translator):
    def __init__(self, options):
        super(SharedCacheL3, self).__init__(options)
        #params
        self.addPowerParam(power_key="L3_config", m5_key="L3_config")
        self.addPowerParam(power_key="buffer_sizes", m5_key="buffer_sizes")
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="NaV")
        self.addPowerParam(power_key="ports", m5_key="unknown", default_value="1,1,1") #TODO: specify your value
        self.addPowerParam(power_key="device_type", m5_key="unknown", default_value=options.cache_device_type) #TODO: specify your value
        ##statistics
        self.addPowerStat(power_key="read_accesses", m5_key="ReadReq_accesses", default_value="0")
        self.addPowerStat(power_key="write_accesses", m5_key="ReadExReq_accesses", default_value="0")
        self.addPowerStat(power_key="read_misses", m5_key="ReadReq_misses", default_value="0")
        self.addPowerStat(power_key="write_misses", m5_key="ReadExReq_misses", default_value="0")
        self.addPowerStat(power_key="conflicts", m5_key="replacements", default_value="0")

class Mesh(Translator):
    def __init__(self, options):
        super(Mesh, self).__init__(options)
        #params
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="1400")
        self.addPowerParam(power_key="horizontal_nodes", m5_key="horizontal_nodes", default_value="2")
        self.addPowerParam(power_key="vertical_nodes", m5_key="vertical_nodes", default_value="1")
        self.addPowerParam(power_key="has_global_link", m5_key="has_global_link", default_value="0")
        self.addPowerParam(power_key="link_throughput", m5_key="link_throughput", default_value="1")
        self.addPowerParam(power_key="link_latency", m5_key="link_latency", default_value="1")
        self.addPowerParam(power_key="input_ports", m5_key="input_ports", default_value="9")
        self.addPowerParam(power_key="output_ports", m5_key="output_ports", default_value="8")
        self.addPowerParam(power_key="virtual_channel_per_port", m5_key="unknown", default_value="1") #FIXME: what is this?
        self.addPowerParam(power_key="flit_bits", m5_key="unknown", default_value="136") #FIXME: what is this?
        self.addPowerParam(power_key="input_buffer_entries_per_vc", m5_key="unknown", default_value="16")#FIXME
        self.addPowerParam(power_key="chip_coverage", m5_key="unknown", default_value="1")

        #statistics
        self.addPowerStat(power_key="total_accesses", m5_key="total_packets_received", default_value="0")
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="0.1")


class BusConn(Translator):
    def __init__(self, options):
        super(BusConn, self).__init__(options)
        #params
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="1400")
        self.addPowerParam(power_key="type", m5_key="unknown", default_value="0")
        self.addPowerParam(power_key="vertical_nodes", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="has_global_link", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="link_throughput", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="link_latency", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="input_ports", m5_key="input_ports", default_value="9")
        self.addPowerParam(power_key="output_ports", m5_key="output_ports", default_value="8")
        self.addPowerParam(power_key="virtual_channel_per_port", m5_key="unknown", default_value="2") #FIXME: what is this?
        self.addPowerParam(power_key="flit_bits", m5_key="unknown", default_value="40") #FIXME: what is this?
        self.addPowerParam(power_key="input_buffer_entries_per_vc", m5_key="unknown", default_value="128")#FIXME
        self.addPowerParam(power_key="chip_coverage", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="link_routing_over_percentage", m5_key="unknown", default_value="1.0")

        #statistics
        self.addPowerStat(power_key="total_accesses", m5_key="total_packets_received", default_value="0")
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1")

class Bus(Translator):
    def __init__(self, options):
        super(Bus, self).__init__(options)
        #params
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="0")
        self.addPowerParam(power_key="type", m5_key="unknown", default_value="0") # 0 for BUS
        self.addPowerParam(power_key="horizontal_nodes", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="vertical_nodes", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="has_global_link", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="link_throughput", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="link_latency", m5_key="unknown", default_value="1")
        self.addPowerParam(power_key="input_ports", m5_key="input_ports", default_value="0")
        self.addPowerParam(power_key="output_ports", m5_key="output_ports", default_value="0")
        self.addPowerParam(power_key="virtual_channel_per_port", m5_key="unknown", default_value="2") #FIXME: what is this?
        self.addPowerParam(power_key="input_buffer_entries_per_vc", m5_key="unknown", default_value="128")#FIXME
        self.addPowerParam(power_key="flit_bits", m5_key="unknown", default_value="40") #FIXME: what is this?

        self.addPowerParam(power_key="chip_coverage", m5_key="unknown", default_value="1") #really should be a function of the number of nocs
        self.addPowerParam(power_key="link_routing_over_percentage", m5_key="unknown", default_value="0.5")

        #statistics
        self.addPowerStat(power_key="total_accesses", m5_key="total_packets_received", default_value="0")
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1")

class Crossbar(Translator):
    def __init__(self, options):
        super(Crossbar, self).__init__(options)
        #params
        self.addPowerParam(power_key="clock", m5_key="clock")
        self.addPowerParam(power_key="port", m5_key="port")
        self.addPowerParam(power_key="type", m5_key="type")
        self.addPowerParam(power_key="bandwidth", m5_key="bandwidth_Mbps")
        #statistics
        self.addPowerStat(power_key="accesses", m5_key="accesses")

class Predictor(Translator):
    def __init__(self, options):
        super(Predictor, self).__init__(options)
        #params
        self.addPowerParam(power_key="local_predictor_size", m5_key="unknown", default_value="10,3")
        self.addPowerParam(power_key="local_predictor_entries", m5_key="unkown", default_value="1024")
        self.addPowerParam(power_key="global_predictor_entries", m5_key="unknown", default_value="4096")
        self.addPowerParam(power_key="global_predictor_bits", m5_key="unknown", default_value="2")
        self.addPowerParam(power_key="chooser_predictor_entries", m5_key="unknown", default_value="4096")
        self.addPowerParam(power_key="chooser_predictor_bits", m5_key="unknown", default_value="2")
        #self.addPowerParam(power_key="prediction_width", m5_key="unknown", default_value="2")
        #statistics

class System(Translator):

    Translator.registerComponentClass("system", SystemComponent)

    def __init__(self, options):
        super(System, self).__init__(options)
        #params
        self.addPowerParam(power_key="number_of_cores", m5_key="number_of_cores", default_value="NaV")
        self.addPowerParam(power_key="number_of_L1Directories", m5_key="number_of_L2s", default_value="NaV")
        self.addPowerParam(power_key="number_of_L2Directories", m5_key="number_of_L2Directories", default_value="NaV") #Shadow L4 with 0 latency back memory is our L2 directory
        self.addPowerParam(power_key="number_of_L2s", m5_key="number_of_L2s", default_value="NaV")
        self.addPowerParam(power_key="number_of_L3s", m5_key="number_of_L3s", default_value="NaV")
        self.addPowerParam(power_key="number_of_NoCs", m5_key="number_of_nocs", default_value="NaV")
        self.addPowerParam(power_key="homogeneous_cores", m5_key="homogeneous_cores", default_value="0")
        self.addPowerParam(power_key="homogeneous_L2s", m5_key="homogeneous_L2s", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="homogeneous_L1Directories", m5_key="homogeneous_L1Directories", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="homogeneous_L2Directories", m5_key="homogeneous_L2Directories", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="homogeneous_L3s", m5_key="homogeneous_L3s", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="homogeneous_ccs", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="homogeneous_NoCs", m5_key="homogeneous_nocs", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="core_tech_node", m5_key="unknown", default_value=options.core_tech_node) #TODO: set your value
        if options.sys_vdd_scale != None:
            self.addPowerParam(power_key="sys_vdd_scale", m5_key="unknown", default_value=options.sys_vdd_scale) #TODO: set your value
        self.addPowerParam(power_key="target_core_clockrate", m5_key="unknown", default_value="2000") #TODO: set your value
        self.addPowerParam(power_key="temperature", m5_key="unknown", default_value="380") #TODO: set your value
        self.addPowerParam(power_key="number_cache_levels", m5_key="number_cache_levels", default_value="NaV")
        self.addPowerParam(power_key="interconnect_projection_type", m5_key="unknown", default_value=options.interconnect_projection_type) #TODO: set your value
        self.addPowerParam(power_key="device_type", m5_key="unknown", default_value=options.core_device_type) #TODO: set your value
        self.addPowerParam(power_key="longer_channel_device", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="machine_bits", m5_key="unknown", default_value="64") #TODO: set your value
        self.addPowerParam(power_key="virtual_address_width", m5_key="unknown", default_value="64") #TODO: set your value
        self.addPowerParam(power_key="physical_address_width", m5_key="unknown", default_value="52") #TODO: set your value
        self.addPowerParam(power_key="virtual_memory_page_size", m5_key="unknown", default_value="4096") #TODO: set your value
        self.addPowerParam(power_key="number_of_dir_levels", m5_key="number_of_dir_levels", default_value="0") #TODO: set your value
        #self.addPowerParam(power_key="first_level_dir", m5_key="first_level_dir", default_value="NaV") #REMOVED: ask Sheng what this stat is all about
        #self.addPowerParam(power_key="domain_size", m5_key="unknown", default_value="NaV") #REMOVED: ask Sheng about domain size


        self.addPowerStat(power_key="total_cycles", m5_key="total_cycles", default_value="0") #FIXME: ask Sheng about domain size
        self.addPowerStat(power_key="idle_cycles", m5_key="unknown", default_value="0") #FIXME: ask Sheng about domain size
        self.addPowerStat(power_key="busy_cycles", m5_key="total_cycles", default_value="0") #FIXME: ask Sheng about domain size

class BTB(Translator):
    def __init__(self, options):
        super(BTB, self).__init__(options)
        #params
        self.addPowerParam(power_key="BTB_config", m5_key="unknown", default_value="6144,4,2,1,1,3")
        #statistics
        self.addPowerParam(power_key="read_accesses", m5_key="BPredUnit.BTBLookup", default_value="0")
        self.addPowerParam(power_key="write_accesses", m5_key="unknown", default_value="0")

class L1Directory(Translator):
    def __init__(self, options):
        super(L1Directory, self).__init__(options)
        #params
        self.addPowerParam(power_key="Directory_type", m5_key="unknown", default_value="1") #TODO: specify your value
        self.addPowerParam(power_key="Dir_config", m5_key="Dir_config", default_value="NaV")
        self.addPowerParam(power_key="buffer_sizes", m5_key="unknown", default_value="8,8,8,8") #TODO: specify your value
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="NaV")
        self.addPowerParam(power_key="ports", m5_key="unknown", default_value="1,1,1") #TODO: specify your value
        self.addPowerParam(power_key="device_type", m5_key="unknown", default_value=options.cache_device_type) #TODO: specify your value
        #statistics
        self.addPowerStat(power_key="read_accesses", m5_key="read_accesses", default_value="NaV")
        self.addPowerStat(power_key="write_accesses", m5_key="write_accesses", default_value="NaV")
        self.addPowerStat(power_key="read_misses", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache
        self.addPowerStat(power_key="write_misses", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache
        self.addPowerStat(power_key="conflicts", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache


class L2Directory(Translator):
    def __init__(self, options):
        super(L2Directory, self).__init__(options)
        #params
        self.addPowerParam(power_key="Directory_type", m5_key="unknown", default_value="1") #TODO: specify your value
        self.addPowerParam(power_key="Dir_config", m5_key="Dir_config", default_value="NaV")
        self.addPowerParam(power_key="buffer_sizes", m5_key="unknown", default_value="8,8,8,8") #TODO: specify your value
        self.addPowerParam(power_key="clockrate", m5_key="clockrate", default_value="NaV")
        self.addPowerParam(power_key="ports", m5_key="unknown", default_value="1,1,1") #TODO: specify your value
        self.addPowerParam(power_key="device_type", m5_key="unknown", default_value=options.cache_device_type) #TODO: specify your value
        #statistics
        self.addPowerStat(power_key="read_accesses", m5_key="read_accesses", default_value="NaV")
        self.addPowerStat(power_key="write_accesses", m5_key="write_accesses", default_value="NaV")
        self.addPowerStat(power_key="read_misses", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache
        self.addPowerStat(power_key="write_misses", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache
        self.addPowerStat(power_key="conflicts", m5_key="unknown", default_value="0") #FIXME: Add this stat to M5. My model does not treat directory as a cache

class PhysicalMemory(Translator):
    def __init__(self, options):
        super(PhysicalMemory, self).__init__(options)

        self.addPowerParam(power_key="mem_tech_node", m5_key="unknown", default_value=options.mem_tech_node) #TODO: Set your value

        self.addPowerParam(power_key="device_clock", m5_key="unknown", default_value="200") #TODO: Set your value
        self.addPowerParam(power_key="peak_transfer_rate", m5_key="unknown", default_value="6400") #TODO: set your value
        self.addPowerParam(power_key="internal_prefetch_of_DRAM_chip", m5_key="unknown", default_value="4") #FIXME: add this param to M5
        self.addPowerParam(power_key="capacity_per_channel", m5_key="unknown", default_value="4096") #TODO: set your value
        self.addPowerParam(power_key="number_ranks", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="num_banks_of_DRAM_chip", m5_key="unknown", default_value="8") #TODO: set your value
        self.addPowerParam(power_key="Block_width_of_DRAM_chip", m5_key="unknown", default_value="64") #TODO: set your value
        self.addPowerParam(power_key="output_width_of_DRAM_chip", m5_key="unknown", default_value="8") #TODO: set your value
        self.addPowerParam(power_key="page_size_of_DRAM_chip", m5_key="unknown", default_value="8") #TODO: set your value
        self.addPowerParam(power_key="burstlength_of_DRAM_chip", m5_key="unknown", default_value="8") #TODO: set your value
        #statistcs
        self.addPowerStat(power_key="memory_accesses", m5_key="num_phys_mem_accesses", default_value="0")
        self.addPowerStat(power_key="memory_reads", m5_key="num_phys_mem_reads", default_value="0")
        self.addPowerStat(power_key="memory_writes", m5_key="num_phys_mem_writes", default_value="0")

#Memory Controller
class MC(Translator):
    def __init__(self, options):
        super(MC, self).__init__(options)
        self.addPowerParam(power_key="mc_clock", m5_key="unknown", default_value="800") #TODO: set your value
        self.addPowerParam(power_key="peak_transfer_rate", m5_key="1600", default_value="1600") #TODO: set your value
        self.addPowerParam(power_key="llc_line_length", m5_key="unknown", default_value="16") #TODO: set your value
        self.addPowerParam(power_key="number_mcs", m5_key="unknown", default_value="1") #TODO: set this value
        self.addPowerParam(power_key="memory_channels_per_mc", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="number_ranks", m5_key="unknown", default_value="2") #TODO: set your value
        self.addPowerParam(power_key="req_window_size_per_channel", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="IO_buffer_size_per_channel", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="databus_width", m5_key="unknown", default_value="32") #TODO: set your value
        self.addPowerParam(power_key="addressbus_width", m5_key="unknown", default_value="32") #TODO: set your value
        #statistcs
        self.addPowerStat(power_key="memory_accesses", m5_key="num_phys_mem_accesses", default_value="0")
        self.addPowerStat(power_key="memory_reads", m5_key="num_phys_mem_reads", default_value="0")
        self.addPowerStat(power_key="memory_writes", m5_key="num_phys_mem_writes", default_value="0")


# Network Interface Controller
class NIC(Translator):
    def __init__(self, options):
        super(NIC, self).__init__(options)
        self.addPowerParam(power_key="type", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="clockrate", m5_key="unknown", default_value="350") #TODO: set your value
        self.addPowerParam(power_key="number_units", m5_key="unknown", default_value="0") #TODO: set your value
        #statistics
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1.0") #TODO: set your value
        self.addPowerStat(power_key="total_load_perc", m5_key="unknown", default_value="0.7") #TODO: set your value

# PCI Express Controller
class PCIE(Translator):
    def __init__(self, options):
        super(PCIE, self).__init__(options)
        self.addPowerParam(power_key="type", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="withPHY", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="clockrate", m5_key="unknown", default_value="350") #TODO: set your value
        self.addPowerParam(power_key="number_units", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="num_channels", m5_key="unknown", default_value="8") #TODO: set your value
        #statistic
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1.0") #TODO: set your value
        self.addPowerStat(power_key="total_load_perc", m5_key="unknown", default_value="0.7") #TODO: set your value


# Flash Controller
class Flash(Translator):
    def __init__(self, options):
        super(Flash, self).__init__(options)
        self.addPowerParam(power_key="number_flashcs", m5_key="unknown", default_value="0") #TODO: set your value
        self.addPowerParam(power_key="type", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="withPHY", m5_key="unknown", default_value="1") #TODO: set your value
        self.addPowerParam(power_key="peak_transfer_rate", m5_key="unknown", default_value="200") #TODO: set your value
        #statistics
        self.addPowerStat(power_key="duty_cycle", m5_key="unknown", default_value="1.0") #TODO: set your value
        self.addPowerStat(power_key="total_load_perc", m5_key="unknown", default_value="0.7") #TODO: set your value
