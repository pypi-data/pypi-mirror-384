# Main entry point for SCRY: a command-line scryfall query tool
# by thrly


from .db_setup import create_table
from .cli import build_arg_parser

from contextlib import closing
import sqlite3
from pathlib import Path
from os import makedirs

# set path (if required) for db: scry/data/cards.db
path_to_root = Path(__file__).parent.parent.parent  # project root scry/
makedirs(path_to_root / "data/", exist_ok=True)


def main(argv=None):

    # setup argument parsing (argv for testing)
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # use auto-closing context manager to create db connection, pass it to handlers
    with closing(
        sqlite3.connect(Path(path_to_root / "data" / "cards.db"))
    ) as connection:

        try:
            # setup / connect to local database
            create_table(connection)

            # execute commands from cli arguments (see cli.py for handling)
            args.func(args, connection)

        except Exception as err:
            print("Error in main(): ", err)
