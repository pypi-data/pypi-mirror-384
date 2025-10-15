#!/usr/bin/env python3

from motoko.workflow import Workflow

command = "launcher"
command_help = "Spawn the launcher daemon"


def populate_arg_parser(parser):
    parser.add_argument(
        "--generator", type=str, help="Force a generator for job submission"
    )

    parser.add_argument("--log", "-l", action="store_true", help="Show logs")
    parser.add_argument(
        "--do_not_detach",
        action="store_true",
        help="Launcher start in front ground",
    )
    parser.add_argument(
        "--bd_study",
        type=str,
        default="all",
        help="The study launcher to start",
    )


def main(args):
    fullpath = "motoko.yaml"
    wf = Workflow(fullpath)

    if not args.log:
        wf.start_launcher_daemons(args)
        return

    import subprocess
    import os

    log_files = []
    for name, task_manager in wf.task_managers.items():
        _dir = task_manager.study_dir
        log_file = os.path.join(_dir, ".bd", "launch.log")
        log_files.append(log_file)

    log_files = " ".join(log_files)
    subprocess.call(f"tail -f {log_files}", shell=True)
