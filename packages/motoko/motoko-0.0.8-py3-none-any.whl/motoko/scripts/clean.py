#!/usr/bin/env python3

import subprocess

from motoko.workflow import Workflow

command = "clean"
command_help = "Clean all bd studies"


def populate_arg_parser(parser):
    parser.add_argument(
        "--delete", action="store_true", help="delete the runs (destructive)"
    )
    parser.add_argument(
        "--bd_study",
        "-bd",
        type=str,
        default="all",
        help="The study to clean",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        help="The selection constraints",
    )


def main(args):
    fullpath = "motoko.yaml"
    wf = Workflow(fullpath)

    for name, task_manager in wf.task_managers.items():
        if args.bd_study != "all" and args.bd_study != name:
            continue

        print(f"clean study: {task_manager.study}")
        cmd = "canYouDigIt runs clean --truerun --yes"

        if hasattr(args, "constraints") and args.constraints:
            cmd += " --constraints {args.constraints}"
        if args.delete:
            cmd += " --delete"

        print(cmd)
        subprocess.call(cmd, cwd=task_manager.study_dir, shell=True)
