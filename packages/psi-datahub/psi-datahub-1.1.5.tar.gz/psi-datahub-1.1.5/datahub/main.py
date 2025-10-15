"""CLI interface """
import sys
import traceback

from datahub import *
import argparse
import logging
import json
import inspect
from datahub.utils.reflection import get_meta

logger = logging.getLogger(__name__)

CHANNEL_SEPARATOR = ","
EMPTY_SOURCE = [{}]

def run_json(task):
    try:
        if type(task) == str:
            task = json.loads(task)
        hdf5 = task.get("hdf5", None)
        if type(hdf5) == list:
            hdf5 = hdf5[0]
        txt = task.get("txt", None)
        if type(txt) == list:
            txt = txt[0]
        prnt = task.get("print", None)
        plot = task.get("plot", None)
        pshell = task.get("pshell", None)
        start = task.get("start", None)
        end = task.get("end", None)
        path = task.get("path", None)
        decompress = task.get("decompress", False)
        compression = task.get("compression", Compression.GZIP)
        interval = task.get("interval", None)
        bins = task.get("bins", None)
        last = task.get("last", None)
        timeout = task.get("timeout", None)
        modulo = task.get("modulo", None)
        filter = task.get("filter", None)
        search = task.get("search", None)
        verbose = task.get("verbose", None)
        icase = task.get("icase", None)
        prefix = task.get("prefix", None)
        append = task.get("append", None)
        query_id = task.get("id", None)
        query_time = task.get("time", None)
        time_type = task.get("timetype", None)
        channels = task.get("channels", None)
        backend = task.get("backend", None)
        url = task.get("url", None)
        align = task.get("align", None)
        if compression == "lz4":
            compression = Compression.BITSHUFFLE_LZ4
        elif compression.lower() in ["null", "none"]:
            compression = None

        valid_sources = {}
        for name in KNOWN_SOURCES.keys():
            value = task.get(name, None)
            no = 0 if value is None else len(value)
            for i in range(no):
                if value[i] is not None:
                    valid_sources[f"{name}_{i}"] = (value[i], KNOWN_SOURCES[name])

        consumers = []
        if hdf5 is not None:
            consumers.append(HDF5Writer(hdf5, default_compression=compression, timetype=time_type,  append=append))
        if txt is not None:
            consumers.append(TextWriter(txt, timetype=time_type, append=append))
        if prnt is not None:
            consumers.append(Stdout(timetype=time_type))
        try:
            if pshell is not None:
                if pshell==True:
                    pshell={}
                consumers.append(PShell(**pshell))
        except Exception as ex:
            logger.exception(ex)
        try:
            if plot is not None:
                if plot==True:
                    plot = {}
                consumers.append(Plot(**plot))
        except Exception as ex:
            logger.exception(ex)
        sources = []

        #If does nt have query arg, construct based on channels arg and start/end
        def get_query(source):
            nonlocal start, end, interval, modulo, prefix, channels, bins, last, timeout
            query = source.get("query", None)
            if query is None:
                source_channels = source.pop("channels", None)
                if source_channels is None:
                    source_channels =  [] if channels is None else channels
                if type(source_channels) == str:
                    source_channels = source_channels.split(CHANNEL_SEPARATOR)
                    source_channels = [s.lstrip("'\"").rstrip("'\"") for s in source_channels]
                query = {"channels": source_channels}
                query.update(source)
            if "start" not in query:
                query["start"] = start
            if "end" not in query:
                query["end"] = end
            if "interval" not in query:
                if interval:
                    query["interval"] = interval
            if "modulo" not in query:
                if modulo:
                    query["modulo"] = modulo
            if "prefix" not in query:
                if prefix:
                    query["prefix"] = prefix
            if "filter" not in query:
                if filter:
                    query["filter"] = filter
            if "bins" not in query:
                if bins:
                    query["bins"] = bins
            if "last" not in query:
                if last:
                    query["last"] = last
            if "timeout" not in query:
                if timeout:
                    query["timeout"] = timeout

            force_id = False
            if type (query_id)== str:
                try:
                    QueryRange.MAX_REL_ID = int(float(query_id))
                except:
                    pass

            if type(query_time) == str:
                if type(query_id) == str:
                    try:
                        QueryRange.MAX_REL_TIME = int(float(query_time))
                    except:
                        pass

            query_by_id = query_id is not None
            if "id" in query:
                force_id = query_by_id = str_to_bool(str(query["id"]))

            query_by_time = False if force_id else query_time is not None
            if "time" in query:
                query_by_time = str_to_bool(str(query["time"]))
                if query_by_time:
                    query_by_id = False

            for arg in "start", "end":
                    try:
                        if type(query[arg]) != str or not is_null_str(query[arg]):
                            if query_by_id:
                                query[arg] = int(float(query[arg])) #Verbose to be able co convert "0.0"
                            elif query_by_time:
                                query[arg] = float(query[arg])
                    except:
                        pass
            if (query["start"] is None) and (query["end"] is None):
                return None

            try:
                if "bins" in query.keys():
                    query["bins"] = int(query["bins"])
            except Exception as ex:
                pass

            try:
                if "last" in query.keys():
                    query["last"] = bool(query["last"])
            except Exception as ex:
                del query["last"]

            try:
                if "timeout" in query.keys():
                    query["timeout"] = float(query["timeout"])
            except Exception as ex:
                del query["timeout"]


            return query

        def add_source(cfg, src):
            nonlocal channels
            src.query = get_query(cfg)
            sources.append(src)

        #Create source removing constructor parameters from the query dictionary
        def get_source_constructor(cls, typ, cfg):
            nonlocal backend, url
            signature = inspect.signature(cls)
            pars = signature.parameters
            ret = cls.__name__+"("
            index = 0
            for name, par in pars.items():
                if par.kind != inspect.Parameter.VAR_KEYWORD:
                    if index > 0:
                        ret = ret + ", "
                    if par.default == inspect.Parameter.empty:
                        ret = ret + name + "=" + typ + ".pop('" + name + "')"
                    else:
                        default_val = par.default
                        if (name == "backend") and backend:
                            default_val = backend
                        if (name == "url") and url:
                            default_val = url
                        if type (default_val) == str:
                            dflt = "'" + default_val + "'"
                        else:
                            dflt = str(default_val)
                        ret = ret + name + "=" + typ + ".pop('" + name + "', " + dflt + ")"
                    index = index + 1
            if index > 0:
                ret = ret + ", "
            ret = ret + f"auto_decompress={str(decompress)}, prefix='{str(prefix)}'"

            #Source class additional arguments
            if cfg:
                 source_pars = inspect.signature(Source).parameters
                 for name, par in cfg.items():
                     #Aliases
                     if not name in pars.keys() and name in source_pars:
                         ret = ret + ", " + name + "='" + str(par) + "'" #Only accept string  as arguments

            ret = ret + ")"
            return ret

        if len(valid_sources)==0:
            if channels or (search!=None):
                # Add default source
                valid_sources[DEFAULT_SOURCE+ "_0"] = ({}, KNOWN_SOURCES[DEFAULT_SOURCE])

        for name, (cfg,source) in valid_sources.items():
            if cfg is not None:
                local_vars = {name: cfg}
                # Get the source constructor expression as a string
                constructor_expr = get_source_constructor(source, name, cfg)  # This returns a string
                instance = eval(constructor_expr, globals(), local_vars)
                if instance is not None:
                    add_source(cfg, instance)

        for source in sources:
            if verbose is not None:
                source.verbose = verbose
            if path is not None:
                if source.path is None:
                    source.path = path

        if search is not None:
            if search == []:
                search = [""]
            for source in sources:
                # By default seach all available backends, unless requested specifically in command line
                source.set_backend(backend)
                try:
                    for regex in search:
                        source.print_search(regex, False if icase else True)
                except:
                    logger.exception(f"Error searching source: {str(source)}")
        else:
            if align:
                partial = align == "partial"
                merger = Merger(filter=filter, partial_msg=partial)
                for source in sources:
                    merger.add_source(source)
                src = merger.to_source()

                for consumer in consumers:
                    src.add_listener(consumer)
            else:
                for source in sources:
                    for consumer in consumers:
                        source.add_listener(consumer)

            for source in sources:
                if source is not None:
                    if source.query is None:
                        source.print_help()
                    else:
                        source.request(source.query, background=True)

            for source in sources:
                source.join()

    finally:
        cleanup()


def parse_args():
    """Parse cli arguments with argparse"""

    class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def _format_action_invocation(self, action):
            if not action.option_strings:
                metavar, = self._metavar_formatter(action, action.dest)(1)
                return metavar
            else:
                parts = []
                    # if the Optional doesn't take a value, format is:
                #    -s, --long
                if action.nargs == 0:
                    parts.extend(action.option_strings)

                # if the Optional takes a value, format is:
                #    -s ARGS, --long ARGS
                # change to
                #    -s, --long ARGS
                else:
                    default = action.dest.upper()
                    args_string = self._format_args(action, default)
                    for option_string in action.option_strings:
                        # parts.append('%s %s' % (option_string, args_string))
                        parts.append('%s' % option_string)
                    parts[-1] += ' %s' % args_string
                return ', '.join(parts)

        def _format_args(self, action, default_metavar):
            if action.nargs == argparse.ZERO_OR_MORE:
                if action.metavar:
                    return '[{}]'.format(action.metavar)
                else:
                    return ""
            else:
                return action.metavar or default_metavar

    usage = "datahub [--GLOBAL_ARG_1 VALUE]...[--GLOBAL_ARG_N VALUE] [--<SOURCE 1>] [SOURCE_1_ARG_1 VALUE]...[SOURCE_1_ARG_N VALUE]...[--<SOURCE M>] [SOURCE_M_ARG_1 VALUE]...[SOURCE_M_ARG_N VALUE]"
    desc='Command line interface for ' + datahub.package_name()
    epilog =f"Sources: {','.join(KNOWN_SOURCES.keys())}"
    epilog = epilog + f"\nConsumers: {','.join(KNOWN_CONSUMERS.keys())}"
    if DEFAULT_SOURCE:
        epilog = epilog + f"\nDefault Source (can be set by the env var DEFAULT_DATA_SOURCE): {DEFAULT_SOURCE}"
    epilog = epilog + f"\nThe source argument can be omited if only the default source is used."
    epilog = epilog + '\n\nFor source specific documentation:  datahub --<SOURCE>'
    parser = argparse.ArgumentParser(usage=usage, description=desc, prefix_chars='--', formatter_class=CustomHelpFormatter, epilog=epilog)
    parser.add_argument("-j", "--json", help="Complete query defined as JSON", required=False)

    for name, (abbr, cls) in KNOWN_CONSUMERS.items():
        meta = eval("get_meta(" + cls.__name__ + ")")
        eval(f'parser.add_argument("-{abbr}", "--{name}", metavar="{meta}", help="{name} options", required=False, nargs="*")')

    parser.add_argument("-s", "--start", help="Relative or absolute start time or ID", required=False)
    parser.add_argument("-e", "--end", help="Relative or absolute end time or ID", required=False)
    parser.add_argument("-r", "--range", help="Range definitions: " + str(QueryRange.RANGE_STR_OPTIONS), required=False)
    #parser.add_argument("-i", "--id", action='store_true', help="Force query by id", required=False)
    #parser.add_argument("-t", "--time", action='store_true', help="Force query by time", required=False)
    parser.add_argument("-i", "--id", help="Force query by id - options: [maximum relative value]", required=False, nargs="?", const=True)
    parser.add_argument("-t", "--time", help="Force query by time - options: [maximum relative value]", required=False, nargs="?", const=True)
    parser.add_argument("-c", "--channels", help="Channel list (comma-separated)", required=False)
    parser.add_argument("-n", "--bins", help="Number of data bins (integer) or bin width(ending with s, m, h or d)", required=False)
    parser.add_argument("-l", "--last",  action='store_true', help="Include last value before range", required=False)
    parser.add_argument("-a", "--align", help="Merge sources aligning the message ids - options: [complete(default) or partial]",required=False, nargs="?", const=True)
    parser.add_argument("-u", "--url", help="URL of default source", required=False)
    parser.add_argument("-b", "--backend", help="Backend of default source (use \"null\" for all backends)", required=False)
    parser.add_argument("-to", "--timeout",  help="Query timeout in seconds", required=False)
    parser.add_argument("-ll", "--loglevel", help="Set console log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", required=False)
    parser.add_argument("-fi", "--filter", help="Set a filter for data", required=False)
    parser.add_argument("-di", "--interval", help="Downsampling interval between samples in seconds", required=False)
    parser.add_argument("-dm", "--modulo", help="Downsampling modulo of the samples", required=False)
    parser.add_argument("-tt", "--timetype", help="Timestamp type: nano/int (default), sec/float or str", required=False)
    parser.add_argument("-cp", "--compression", help="Compression: gzip (default), szip, lzf, lz4 or none", required=False)
    parser.add_argument("-dc", "--decompress", action='store_true', help="Auto-decompress compressed images", required=False)
    parser.add_argument("-px", "--prefix", action='store_true', help="Add source ID to channel names", required=False)
    parser.add_argument("-pt", "--path", help="Path to data in the file", required=False)
    parser.add_argument("-ap", "--append", action='store_true', help="Append data to existing files", required=False)
    parser.add_argument("-sr", "--search", help="Search channel names given a pattern (instead of fetching data)", required=False , nargs="*")
    parser.add_argument("-ic", "--icase", action='store_true', help="Case-insensitive search", required=False)
    parser.add_argument("-v", "--verbose", action='store_true', help="Display complete search results, not just channels names", required=False)

    for name, source in KNOWN_SOURCES.items():
        meta = eval("get_meta(" + source.__name__ + ")")
        meta = f"channels {meta}start=None end=None"
        eval(f'parser.add_argument("--{name}", metavar="{meta}", help="{name} query arguments", action="append", required=False, nargs="*")')
    args = parser.parse_args()
    return parser, args

def get_full_argument_name(parser, abbr):
    for action in parser._actions:
        if '-' + abbr in action.option_strings:
            return action.dest
    return None

def print_help():
    print(datahub.package_name())
    if DEFAULT_SOURCE:
        print("Default Source (can be set by the env var DEFAULT_DATA_SOURCE):")
        print(f"\t{DEFAULT_SOURCE}")
    print("Sources:")
    for source in KNOWN_SOURCES.keys():
        print(f"\t{source}")
    print("Consumers:")
    for consumer in KNOWN_CONSUMERS.keys():
        print(f"\t{consumer}")
    print(f"For help use the option:\n\t-h")
    print(f"For help on a specific source use the option:\n\t--<source_name>")


def main():
    """Main function"""
    if len(sys.argv) <= 1:
        print_help()
        return
    parser, args = parse_args()

    def parse_arg_dict(parser, val):
        ret = {}
        if val:
            for arg, val in zip(val[::2], val[1::2]):
                full_name = get_full_argument_name(parser, arg)
                if full_name:
                    arg = full_name
                try:
                    ret[arg] = json.loads(val)
                except:
                    ret[arg] = val
        return ret
    try:
        if args.loglevel is not None:
            logging.basicConfig(
                level=logging._nameToLevel[args.loglevel],  # Or DEBUG, WARNING, etc.
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                handlers=[logging.StreamHandler(sys.stdout)]
            )

        #if args.action == 'search':
        #    return search(args)
        if args.json:
            run_json(args.json)
        else:
            task={}
            task["hdf5"] = args.hdf5
            task["txt"] = args.txt
            task["print"] = None if args.print is None else bool(args.print)
            if args.plot is not None:
                task["plot"] = parse_arg_dict(parser, args.plot)
            if args.pshell is not None:
                task["pshell"] = parse_arg_dict(parser, args.pshell)
            if args.range:
                task["start"], task["end"] = QueryRange.get_range(args.range)
            else:
                if args.start:
                    task["start"] = args.start
                if args.end:
                    task["end"] = args.end
            #if args.id:
            #    task["id"] = bool(args.id)
            #if args.time:
            #    task["time"] = bool(args.time)
            if args.id:
                task["id"] = args.id
            if args.time:
                task["time"] = args.time
            if args.timetype:
                task["timetype"] = args.timetype
            if args.path:
                task["path"] = args.path
            if args.decompress:
                task["decompress"] = bool(args.decompress)
            if args.compression:
                task["compression"] = args.compression
            if args.interval:
                task["interval"] = args.interval
            if args.bins:
                task["bins"] = args.bins
            if args.last:
                task["last"] = bool(args.last)
            if args.timeout:
                task["timeout"] = float(args.timeout)
            if args.modulo:
                task["modulo"] = args.modulo
            if args.filter:
                task["filter"] = args.filter
            if args.search is not None:
                task["search"] = args.search
            if args.icase is not None:
                task["icase"] = args.icase
            if args.align is not None:
                task["align"] = args.align
            if args.prefix is not None:
                task["prefix"] = args.prefix
            if args.append is not None:
                task["append"] = args.append
            if args.channels is not None:
                task["channels"] = args.channels
            if args.backend is not None:
                task["backend"] = args.backend
            if args.url is not None:
                task["url"] = args.url

            for source in KNOWN_SOURCES.keys():
                source_entries = eval("args." + source)
                if source_entries:
                    if len(source_entries) == 1 and type(source_entries[0]) == list and len(source_entries[0]) == 0:
                        task[source] = EMPTY_SOURCE
                    else:
                        task[source] = []
                        for source_str in source_entries:
                            if type(source_str) == list:
                                if len(source_str) == 1:
                                    task[source].append(json.loads(source_str[0]))
                                else:
                                    task[source].append(parse_arg_dict(parser, source_str))

            run_json(task)

    except RuntimeError as e:
        logger.error(e)
    return 0
if __name__ == '__main__':
    main()

