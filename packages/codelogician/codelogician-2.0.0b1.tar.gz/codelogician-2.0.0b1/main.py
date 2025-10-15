#
#   Imandra Inc.
#
#   main.py - main entrypoint for CodeLogician
#

import argparse
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cl.log"), logging.StreamHandler()],
)

from codelogician.server.main import set_oneshot_arguments, set_server_arguments
from codelogician.ui.app import set_tui_arguments


def run_codelogician():
    parser = argparse.ArgumentParser(prog="CodeLogician")
    subparsers = parser.add_subparsers(
        title="subcommands",
        help="CL operations",
        dest="command",
        required=True
    )

    server_parser = subparsers.add_parser(
        "server", aliases=["start"], description="Start the server"
    )
    set_server_arguments(server_parser)

    oneshot_parser = subparsers.add_parser(
        "oneshot", description="Perform oneshot operation on a specified directory"
    )
    set_oneshot_arguments(oneshot_parser)

    tui_parser = subparsers.add_parser("tui", description="Start the TUI")
    set_tui_arguments(tui_parser)

    args = parser.parse_args()
    args.func(args)  # This will kick off the actual commands


if __name__ == "__main__":
    run_codelogician()
