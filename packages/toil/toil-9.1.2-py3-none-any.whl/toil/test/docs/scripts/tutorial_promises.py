import os

from toil.common import Toil
from toil.job import Job
from toil.lib.io import mkdtemp


def fn(job, i):
    job.log("i is: %s" % i, level=100)
    return i + 1


if __name__ == "__main__":
    jobstore: str = mkdtemp("tutorial_promises")
    os.rmdir(jobstore)
    options = Job.Runner.getDefaultOptions(jobstore)
    options.logLevel = "INFO"
    options.clean = "always"

    j1 = Job.wrapJobFn(fn, 1)
    j2 = j1.addChildJobFn(fn, j1.rv())
    j3 = j1.addFollowOnJobFn(fn, j2.rv())

    with Toil(options) as toil:
        toil.start(j1)
