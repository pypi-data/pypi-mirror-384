#!/usr/bin/env python3

import subprocess

from motoko.workflow import Workflow

command = "kill"
command_help = "Kill all the running daemons"


def populate_arg_parser(parser):
    parser.add_argument("--verbose", action="store_true", help="show verbose details")
    parser.add_argument(
        "--bd_study",
        "-bd",
        type=str,
        default="all",
        help="The study launcher to kill",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset completely the studies",
    )


def main(args):
    fullpath = "motoko.yaml"

    wf = Workflow(fullpath)

    for name, task_manager in wf.task_managers.items():
        if args.bd_study != "all" and args.bd_study != name:
            continue
        print(f"Kill daemons in study: {task_manager.study}")
        cmds = ["canYouDigIt launch_daemon --stop", "canYouDigIt server stop"]
        if args.reset:
            cmds += [f"rm -fr .bd BD-{name}-runs"]
        for cmd in cmds:
            if args.verbose:
                print(f"({task_manager.study}) {cmd}")
            subprocess.call(cmd, cwd=task_manager.study_dir, shell=True)
    if args.reset:
        subprocess.call("rm -rf .wf", shell=True)
