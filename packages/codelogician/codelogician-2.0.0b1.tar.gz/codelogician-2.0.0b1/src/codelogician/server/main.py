#
#   CodeLogician Server
#
#   main.py
#

from termcolor import colored
import argparse, uvicorn, logging, sys, os, dotenv
from pathlib import Path

dotenv.load_dotenv(".env")
if 'IMANDRA_UNI_KEY' not in os.environ:
    print ("CodeLogician requires 'IMANDRA_UNI_KEY' to be set!")
    sys.exit(0)

log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("fsevents").setLevel(logging.WARNING)
#logging.getLogger("strategy.pyiml_strategy").setLevel(logging.WARNING)
#logging.getLogger("strategy.cl_worker").setLevel(logging.WARNING)
#logging.getLogger("strategy.metamodel").setLevel(logging.WARNING)
log.setLevel(logging.INFO)

from .cl_server import CLServer
from .oneshot import do_oneshot
from .config import ServerConfig
from .state import ServerState
from .endpoints import register_endpoints

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO) # Only show INFO and above
ch.setFormatter(logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(ch)


def do_intro():

    text = """


   █████████               █████          █████                          ███            ███                                       ████████ 
  ███░░░░░███             ░░███          ░░███                          ░░░            ░░░                                       ███░░░░███
 ███     ░░░   ██████   ███████   ██████  ░███         ██████   ███████ ████   ██████  ████   ██████   ████████      █████ █████░░░    ░███
░███          ███░░███ ███░░███  ███░░███ ░███        ███░░███ ███░░███░░███  ███░░███░░███  ░░░░░███ ░░███░░███    ░░███ ░░███    ███████ 
░███         ░███ ░███░███ ░███ ░███████  ░███       ░███ ░███░███ ░███ ░███ ░███ ░░░  ░███   ███████  ░███ ░███     ░███  ░███   ███░░░░  
░░███     ███░███ ░███░███ ░███ ░███░░░   ░███      █░███ ░███░███ ░███ ░███ ░███  ███ ░███  ███░░███  ░███ ░███     ░░███ ███   ███      █
 ░░█████████ ░░██████ ░░████████░░██████  ███████████░░██████ ░░███████ █████░░██████  █████░░████████ ████ █████     ░░█████   ░██████████
  ░░░░░░░░░   ░░░░░░   ░░░░░░░░  ░░░░░░  ░░░░░░░░░░░  ░░░░░░   ░░░░░███░░░░░  ░░░░░░  ░░░░░  ░░░░░░░░ ░░░░ ░░░░░       ░░░░░    ░░░░░░░░░░ 
                                                               ███ ░███                                                                    
                                                              ░░██████                                                                     
                                                               ░░░░░░                                                                      

                                                             
"""

    print (colored(text, "blue"))

def set_server_arguments(parser):
    """
    Set the server arguments to the command arguments parser.
    """
    parser.add_argument("-s", "--state", type=str, default=None, help="Server state file to use.")
    parser.add_argument("-d", "--dir", type=str, default=None, help="Target directory. This takes precedence over `strat_config`.")
    parser.add_argument("-c", "--clean", action="store_true", help="Start clean by disregarding any existing cache files.")
    parser.add_argument("--config", type=str, default="config/server_config.yaml", help="Server configuration YAML file.")
    parser.set_defaults(func=run_server)

def run_server(args):
    """ 
    Run the server
    """

    do_intro()

    try:
        config = ServerConfig.fromYAML(args.config)
    except Exception as e:
        print(f"Failed to load in server config: {str(e)}. Using defaults.")
        config = ServerConfig()


    if args.state:
        # We need to use the existing state
        abs_path = str(Path(args.state).resolve())

        if not os.path.exists(abs_path):
            log.error(f"Specified path for server config doesn't exist: [{abs_path}]. Using defaults.")
            state = ServerState(abs_path=abs_path)
        else:
            try:
                state = ServerState.fromFile(abs_path)
            except Exception as e:
                log.error(f"Failed to create server state from specified file: {abs_path}")
                raise Exception (f"Failed to read in server state: {str(e)}")

    else:
        # We're creating a new state 
        server_state_abs_path = os.path.join(os.getcwd(), '.cl_server')

        try:
            state = ServerState.fromFile(server_state_abs_path)
        except Exception as e:
            log.warning (f"Failed to create server state file: {e}")
            state = ServerState(abs_path=server_state_abs_path, strategy_paths=[], config=config)

        if args.dir:
            # We need to add a strategy directory to the state
            abs_path = str(Path(args.dir).resolve())

            if not (os.path.exists(abs_path) and os.path.isdir(abs_path)):
                errMsg = f"Specified path must exist and be a directory: {abs_path}"
                log.error(errMsg)
                return
            
            state.strategy_paths.append(abs_path)

            if args.clean:
                log.info(f"Starting clean, so will attempt to remove any existing caches!")
                cache_path = os.path.join(abs_path, '.cl_cache')
                if os.path.exists(cache_path):
                    try:
                        os.remove(cache_path)
                        log.info(f"Removed: {cache_path}")
                    except Exception as e:
                        log.error(f"Failed to remove {cache_path}!")
                        return
                    
    server = CLServer(state)
    register_endpoints(server)

    uvicorn.run(
        server,
        host=state.config.host,
        port=state.config.port,
        #reload=state.config.debug,
        log_level="info"
    )

def set_oneshot_arguments(parser):
    parser.add_argument("-c", "--clean", action="store_true", help="Start clean by disregarding any existing cache files.")
    parser.add_argument("-d", "--dir", type=str, required=True, help="Target directory. This takes precedence over `strat_config`.")
    parser.add_argument("--config", type=str, default="config/server_config.yaml", help="Server configuration YAML file.")
    parser.set_defaults(func=run_oneshot)

def run_oneshot(args):
    """ Run in oneshot mode """

    do_intro()

    try:
        config = ServerConfig.fromYAML(args.config)
    except Exception as e:
        print(f"Failed to load in server config: {str(e)}. Using defaults.")
        config = ServerConfig()
    
    do_oneshot(
        clean = args.clean,
        abs_path = args.dir,
        strat_config = config.strat_config("pyiml")
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="CodeLogician server", description="Run the CodeLogician server with various arguments.")
    parsers = parser.add_subparsers(title="subcommands", help="")

    # Oneshot parser
    oneshot_parser = parsers.add_parser ("oneshot", help="We should do a single run.")
    set_oneshot_arguments(oneshot_parser)

    # Server parser
    server_parser = parsers.add_parser("server", help="Start the server")
    set_server_arguments(server_parser)

    args = parser.parse_args()
    args.func(args)
