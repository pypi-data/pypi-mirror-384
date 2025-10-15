import os
import BlackDynamite as BD

# from motoko.workflow import Workflow


def doIt(run, job):
    x = job.x

    n = 1
    if run.id == 1:
        n = 2

    a = [0.342, -2.31]

    y = [0.0] * n
    for i in range(n):
        y[i] = a[i] * x

    run.y = y


################################################################

run, job = BD.getRunFromScript()
print(run)
print(job)
env_to_remove = []
for k in os.environ.keys():
    if "BLACKDYNAMITE_" in k:
        env_to_remove.append(k)

for k in env_to_remove:
    del os.environ[k]

run.start()
doIt(run, job)
run.finish()
