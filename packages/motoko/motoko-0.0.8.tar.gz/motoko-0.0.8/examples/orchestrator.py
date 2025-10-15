from motoko.workflow import Workflow


def populate_arg_parser(parser):
    parser.add_argument(
        "--inputs",
        "-i",
        type=float,
        required=True,
        nargs=2,
    )


######################################################


def spawn_init_tasks(workflow, **kwargs):
    print("spawn_init_tasks")
    mult_manager = workflow.mult
    mult_manager.createTask(x=kwargs["inputs"], run_params=None)


######################################################


def spawn_add_tasks(runs=None, workflow=None, **kwargs):
    for run, job in runs:
        y = run.y
        created = workflow.add.createTask(x=y)
        run.state = "FORWARDED"
        run.dependencies = [f"add.{r.id}" for r, j in created]


######################################################


def spawn_norm_tasks(workflow=None, **kwargs):
    finished_mult_runs = workflow.mult.select(["state = FORWARDED"])
    mult_ids = [r.id for r, j in finished_mult_runs]
    for r, j in finished_mult_runs:
        for tm, add_runs in workflow.get_runs(r.dependencies).items():
            for add_run in add_runs:
                add_run.state = "FORWARDED"
    workflow.norm.createTask(mult_ids=mult_ids)


######################################################


def spawn_mult_tasks(runs=None, workflow=None, **kwargs):
    for r, j in runs:
        l1_norm, l2_norm = r.getQuantity("vector").iloc[0, 1:]
        print(l1_norm, l2_norm)
        created_mult_runs = workflow.mult.createTask(x=[l1_norm, l2_norm])
        r.dependencies = [f"mult.{r['id']}" for r, j in created_mult_runs]
        r.state = "FORWARDED"


######################################################


def dummy_task(workflow, **params):
    print("dummy_task: pass here")


######################################################


def finalize(workflow, **params):
    print("terminate: workflow successful")
    import sys

    sys.exit(0)


######################################################


def report_error(runs, **params):
    for r, j in runs:
        print(f"found error: {r.id}")
        print(f"run: {r}")
        import subprocess

        subprocess.run(
            f"cat {r.run_name}.*",
            shell=True,
            cwd=r.run_path,
        )


######################################################


def main(workflow, **params):
    workflow.add_error_handler(event="state = FAILED", f=report_error)

    workflow.add_action(
        "init",
        event=lambda workflow, task_manager: len(task_manager.select([])) < 2,
        task="mult",
        f=spawn_init_tasks,
    )

    workflow.add_action(
        "mult_finished",
        task="mult",
        event=["runs.id < 3", "state = FINISHED"],
        f=spawn_add_tasks,
    )

    def condition2(workflow, task_manager):
        if len(workflow.mult.select([])) != 2:
            return False
        if len(workflow.add.select([])) != 3:
            return False
        if workflow.mult.select(["state != FORWARDED"]):
            return False
        if workflow.add.select(["state != FINISHED"]):
            return False

        return True

    # for the others I show the most direct
    workflow.add_action(
        "need_launching_norm",
        event=condition2,
        f=spawn_norm_tasks,
    )

    workflow.add_action(
        "norm_run_finished",
        task="norm",
        event="state = FINISHED",
        f=spawn_mult_tasks,
    )

    def condition3(workflow, task_manager):
        if len(workflow.mult.select([])) != 4:
            return False
        if len(workflow.add.select([])) != 3:
            return False
        if len(workflow.norm.select([])) != 1:
            return False
        if workflow.mult.select(["state != FORWARDED", "state != FINISHED"]):
            return False
        if workflow.add.select(["state != FORWARDED"]):
            return False
        if workflow.norm.select(["state != FORWARDED"]):
            return False

        return True

    workflow.add_action(
        "finish",
        event=condition3,
        f=finalize,
    )


if __name__ == "__main__":
    workflow = Workflow("motoko.yaml")
    main(workflow)
