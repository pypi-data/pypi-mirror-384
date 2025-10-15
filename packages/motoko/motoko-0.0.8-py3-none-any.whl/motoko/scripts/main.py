import argparse

from motoko.scripts import create_studies, info, kill, launcher, orchestrator, clean

commands = [create_studies, info, kill, launcher, orchestrator, clean]


def main() -> None:
    """Entry point for the command line interface."""

    args = parse_args()

    keys = [e for e in args.__dict__.keys()]
    for k in keys:
        if args.__dict__[k] is None:
            del args.__dict__[k]

    try:
        for command in commands:
            if args.command == command.command:
                command.main(args)
                break
    except Exception as e:
        if args.verbose:
            raise e
        print(f"FATAL: {e}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.prog = "motoko"

    parser.add_argument("--verbose", action="store_true", help="verbose output")

    # Create subparsers for each command
    command_parsers = parser.add_subparsers(dest="command", help="command to run")
    command_parsers.required = True

    for command in commands:
        command_parser = command_parsers.add_parser(
            command.command, help=command.command_help
        )
        command.populate_arg_parser(command_parser)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
