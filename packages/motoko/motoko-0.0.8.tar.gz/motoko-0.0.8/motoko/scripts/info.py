#!/usr/bin/env python3

import subprocess
import argparse
from motoko.workflow import Workflow
import sys

command = "info"
command_help = "Get info from sub-studies"


def populate_arg_parser(parser):
    parser.add_argument("--verbose", action="store_true", help="show verbose details")
    parser.add_argument(
        "--bd_study",
        "-bd",
        type=str,
        help="show details for a specific substudy",
        default="all",
    )
    parser.add_argument(
        "--byobu", action="store_true", help="show tiled window of the status"
    )
    parser.add_argument(
        "-",
        dest="bd_args",
        nargs=argparse.REMAINDER,
        help="Arguments to forward to canYouDigIt",
    )


def main(args):
    fullpath = "motoko.yaml"

    if args.byobu:
        import os

        session_name = os.path.abspath(fullpath)
        session_name = os.path.dirname(session_name)
        session_name = session_name.replace("/", "_")
        subprocess.run(f"byobu kill-session -t {session_name}", shell=True)
        subprocess.run(f"byobu new-session -d -s {session_name}", shell=True)
        subprocess.run(
            f'byobu send-keys -t {session_name} "watch motoko info" C-m', shell=True
        )
        subprocess.run(f"byobu split-window -h -t {session_name}", shell=True)
        subprocess.run(
            f'byobu send-keys -t {session_name}:0.1 "motoko launcher -l" C-m',
            shell=True,
        )
        subprocess.run(f"byobu split-window -v -t {session_name}", shell=True)
        subprocess.run(
            f'byobu send-keys -t {session_name}:0.2 "while \\$(test 1); do timeout 5s motoko info - runs exec --constraints state=START tail -f *.e* *.o*; done" C-m',
            shell=True,
        )
        subprocess.run(f"byobu attach -t {session_name}", shell=True)
        return

    wf = Workflow(fullpath)

    for name, task_manager in wf.task_managers.items():
        if args.bd_study != "all" and name != args.bd_study:
            continue
        print("*" * 30, file=sys.stderr)
        print(f"TaskManager: {name}", file=sys.stderr)
        print("*" * 30, file=sys.stderr)

        if hasattr(args, "bd_args"):
            cmd = "canYouDigIt " + " ".join(args.bd_args)
            subprocess.call(cmd.split(), cwd=task_manager.study_dir)
            continue

        if not args.verbose:
            subprocess.call("canYouDigIt info".split(), cwd=task_manager.study_dir)

        else:
            subprocess.call("canYouDigIt jobs info".split(), cwd=task_manager.study_dir)
            subprocess.call("canYouDigIt runs info".split(), cwd=task_manager.study_dir)
            subprocess.call(
                "canYouDigIt launch_daemon --status".split(), cwd=task_manager.study_dir
            )
