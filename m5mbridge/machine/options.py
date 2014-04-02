'''The m5parser library uses command line options for configuration.

We use command line options, due to the library's roots as a monolithic command
line utility, where the global options object was accessed from everywhere.'''

from m5mbridge import bug, panic, warning, debug
from m5mbridge import setup
import optparse

class M5OptionParser(optparse.OptionParser):
    def error(self, msg):
        raise optparse.OptParseError(msg)

def checkRawArgs(parser, args):
    try:
        # Make sure that --record is called with an argument, otherwise it can
        # lead to suprising behavior/errors down the road, because the
        # OptionParser parser does not raise an error if args is of the form
        # ['--record', '--cpu_name', 'cpu']. It simply treats --cpu_name as the
        # value of the --record argument.
        idx = args.index('--record')
        if idx == len(args)-1 or args[idx+1].startswith('-'):
            parser.error('--record needs an argument!')
    except ValueError:
        # --record not used, everything is ok.
        return

def checkArgs(parser, options):
    if not len(options.power_output):
        parser.error("--power-output requires a non-zero argument (see --help output).")
    if not 'systemConfig' in options.power_output:
        warning('--power-output should not be used without systemConfig argument (the generated XML file is not a valid McPat input file).')

def parse(args, usage=None):
    parser = M5OptionParser(
            formatter=optparse.TitledHelpFormatter(),
            usage=usage,
            version='m5parser')
    parser.add_option('-o', '--m5dir', action='store', type='string', default='m5out', help='m5 output directory (default: m5out)')
    parser.add_option ('-v', '--verbose', action='store_true',
            default=False, help='Verbose output for McPat config.xml creation. Obsolete, use --debug=mcpat.exporter instead.')
    parser.add_option ('-f', '--process_run_dirs_by_filter', action='store',
            default=None, help="process a series of run directories by some specificed filter string")
    parser.add_option('--old_m5_stats', action="store_true", default=False, help='processing old m5 stats')
    parser.add_option('-c', '--cpu_name', action='store', type='string', default="switch_cpus", help="the string used cpu comparisons")
    parser.add_option('-s', '--stats_fn', action='store', type='string', default='stats.txt', help="the name of the stats file to use. Use -s /dev/stdin to read from stdin and --stats_fn= to skip stats.")
    parser.add_option('-C', '--config_fn', action='store', type='string', default='config.ini', help="the name of the config file to use")
    parser.add_option('-y', '--summary_fn', action='store', type='string', default='summary.xml', help="the name of the summary output file name. Use --summary_fn= to inhibit.")
    parser.add_option('-p', '--power_fn', action='store', type='string', default='power.xml', help="the name of the McPAT config output file name. Use -p /dev/stdout to write to stdout.")
    parser.add_option('-S', '--system_name', action='store', type='string', default='system', help="the name the system we are consider for stats")
    parser.add_option('-l', '--l1_cache_cpu_name', action='store', type='string', default='cpu', help="the name of the cpu to which the l1 dcache and icache were first attached")
    parser.add_option('-i', '--itb_name', action='store', type='string', default='itb', help="The name associated with M5's itb")
    parser.add_option('-d', '--dtb_name', action='store', type='string', default='dtb', help="The name associated with M5's dtb")
    parser.add_option('-I', '--interconn_names', action='store', type='string', default='tol2bus,0.5', help="The name of the interconnects to consider")
    parser.add_option('-m', '--mem_tech_node', action='store', type='string', default='32', help="The technology node of the memory")
    parser.add_option('-t', '--core_tech_node', action='store', type='string', default='32', help="The technology node of the core")
    parser.add_option('-D', '--core_device_type', action='store', type='string', default='0', help="The core device type: 0=High Performance,1=Low Standby Power,2=Low Operating Power")
    parser.add_option('-E', '--cache_device_type', action='store', type='string', default='0', help="The cache device type: 0=High Performance,1=Low Standby Power,2=Low Operating Power")
    parser.add_option('-P', '--interconnect_projection_type', action='store', type='string', default='0', help="The cache device type: 0=High Performance,1=Low Standby Power,2=Low Operating Power")
    parser.add_option('--sys_vdd_scale', action='store', type='string', default=None, help="The amount to scale vdd by in the system.")
    parser.add_option('--do_vdd_scaling', action='store_true', default=False, help="The amount to scale vdd by in the system.")
    parser.add_option('-O', '--power-output', action='store', type='string', default='systemConfig,systemStats', help="A comma separated list of output data the parser should include in the McPAT XML file. Currently supported operations are: systemConfig and systemStats. systemConfig creates the <param> entries and systemStats the <stat> entries. This configuration option is at the moment broken. -O systemStats does not generate a valid McPAT input file.")
    #parser.add_options('-N', '--num_cores', action='store', type='int', default=1, help="The number of cores that must be processed.")
    parser.add_option('-X', '--debug', action='store', type='string', default='', help="Enable debugging for one or more parts of m5mbridge. Format is a list of one or more (partial) partrefs separated by a colon, for example --debug=mcpat:m5.importer. For a complete list consult m5mbridge/debug.py.")
    parser.add_option('--record', action='store', type='string', default='', help="Record all listed events. Multiple events must be separated by a colon, for example --record=m5stats:pat. To record all events use --record=all")
    parser.add_option('--record-file', action='store', type='string', default='events.log', help="Sets the output file for recorded events.")
    parser.add_option('--modules', action='store', type='string', default='all', help="Load only the listed simulator modules. Multiple modules must be separated by a colon. The special module 'all' loads all simulator modules and is the default. Possible values are: {0} and all.".format(', '.join(setup.ALL_MODULES.keys())))
    parser.add_option('--tick-interval', action='store', type='int', default=1e10, help="The update interval used by the m5mbridge simulator modules. Lower values cause a higher cpu overhead, but return simulator results early. A higher value does the opposite. By default the simulator runs with 1THz, i.e., 1e12 ticks per simulated seconds. For a 2GHz CPU the simulator executes 500ticks per CPU cycle. The default value for the tick interval is 1e10.")
    parser.add_option('--playback', action='store', type='string', default='all', help="Play back events recorded with --record. The syntax is the same as in --record. The default is to play back all events.")
    parser.add_option('--playback-file', action='store', type='string', default=None, help="Read recorded events from file.")
    parser.add_option('--playback-speed', action='store', type='float', default=1.0, help="Playback speed scaling. A value of 1 replays events with the same delays as recorded. A value of 0.5 replays events with the delays doubled and a value of 2 would play back events twice as fast. The argument is a decimal. The default is 1.")
    parser.add_option('--playback-offset', action='store', type='int', default=None, help="Tick offset when play back should start. By default play back starts immediately.")

    checkRawArgs(parser, args)
    (options, unused) = parser.parse_args(args)
    checkArgs(parser, options)
    # Add support for obsolete --verbose option
    if options.verbose:
        options.debug += ':mcpat.exporter'
    # Handle debugging
    if options.debug:
        # Exclude all empty options created for example by--debug=:mcpat
        debug.enable_debugging_from_options(filter(len, options.debug.split(':')))


    return options
