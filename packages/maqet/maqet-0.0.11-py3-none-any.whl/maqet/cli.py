import argparse
import os
from pathlib import Path

from benedict import benedict

from maqet.logger import LOG, configure_file_logging
from maqet.maqet import Maqet


def cli():
    LOG.debug("Maqet CLI started")
    parser = argparse.ArgumentParser(
        prog="MAQET - m4x0n QEMU Tool",
        description="Using YAML file for running QEMU VM and automate actions",
        epilog="Still in development"
    )

    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="yaml with config"  # TODO: Write more
    )
    parser.add_argument(
        "stages",
        nargs="*",
        help="stages to run. If not stated - just start VM",
    )
    parser.add_argument(
        "-v", "--verbose",
        action='count',
        help="increase verbose level",
        default=0
    )
    parser.add_argument(
        "-a", "--argument",
        nargs="*",
        help="Plain arguments to pass to qemu,"
        "use with quotes: -a '-arg_a ... -arg_z' "
    )


    cli_args = parser.parse_args()

    # Set console handler level based on verbosity, but leave file handler at DEBUG
    console_handler = LOG.handlers[0]
    console_handler.setLevel(50 - cli_args.verbose * 10 if cli_args.verbose < 5 else 10)

    if cli_args.file is not None:
        os.chdir(cli_args.file.parent)
        raw_config = benedict.from_yaml(cli_args.file.name)
        # NOTE: should rise Exception if yaml incorrect
    else:
        raw_config = benedict({})

    if 'log_file' in raw_config:
        configure_file_logging(raw_config['log_file'])

    raw_config.plain_arguments = cli_args.argument

    LOG.debug(f"CLI Arguments: {cli_args}")

    maqet = Maqet(*cli_args.stages, **raw_config)
    LOG.debug(f"Maqet initialized, stages to run: {cli_args.stages}")
    maqet()
    LOG.debug("Maqet finished")


def main():
    """Entry point for the maqet command."""
    cli()
