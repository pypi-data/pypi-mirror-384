import os

from toil.common import Toil
from toil.job import Job
from toil.lib.io import mkdtemp


class LocalFileStoreJob(Job):
    def run(self, fileStore):
        # self.tempDir will always contain the name of a directory within the allocated disk space reserved for the job
        scratchDir = self.tempDir

        # Similarly create a temporary file.
        scratchFile = fileStore.getLocalTempFile()


if __name__ == "__main__":
    jobstore: str = mkdtemp("tutorial_managing")
    os.rmdir(jobstore)
    options = Job.Runner.getDefaultOptions(jobstore)
    options.logLevel = "INFO"
    options.clean = "always"

    # Create an instance of FooJob which will have at least 2 gigabytes of storage space.
    j = LocalFileStoreJob(disk="2G")

    # Run the workflow
    with Toil(options) as toil:
        toil.start(j)
