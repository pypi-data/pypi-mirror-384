import argparse

tick_parser = argparse.ArgumentParser(
    prog="py -m rob.tick",
    allow_abbrev=True,
    add_help=True,
    # usage="$(prog)s [-h] path",
    description="Periodically syncs a local cache with ticktick servers.",
    epilog="(C) Rob",
)

commands = tick_parser.add_mutually_exclusive_group()

front_options = tick_parser.add_argument_group()

commands.add_argument(
    "-d",
    "--daemon",
    action="store_true",
    default=False,
    help="Run this as a background process.",
)

commands.add_argument(
    "-g", "--get", action="store_true", default=False, help="Get today's tasks."
)


front_options.add_argument(
    "-t",
    "--token",
    action="store_true",
    default=False,
    help="Force an OAuth Token update.",
)


commands.add_argument(
    "-u", "--update", action="store_true", default=False, help="Update the task cache."
)
