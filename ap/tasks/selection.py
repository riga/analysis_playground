# coding: utf-8

"""
Tasks related to obtaining, preprocessing and selecting events.
"""

import law

from ap.tasks.base import DatasetTask, HTCondorWorkflow
from ap.util import ensure_proxy, determine_xrd_redirector


class SelectEvents(DatasetTask, HTCondorWorkflow):

    def workflow_requires(self):
        return GetDatasetLFNs.req(self)

    def requires(self):
        return GetDatasetLFNs.req(self)

    def output(self):
        return self.local_target("data_{}.npz".format(self.branch))

    @law.decorator.notify
    @law.decorator.safe_output
    @ensure_proxy
    def run(self):
        # get the lfn of the file referenced by this branch
        lfn = str(self.input().random_target().load(formatter="json")[self.branch])
        self.logger.debug("using LFN {}".format(lfn))

        # determine the best redirector and build the pfn
        rdr = determine_xrd_redirector(lfn)
        pfn = "root://{}/{}".format(rdr, lfn)
        self.logger.info("using redirector {}".format(rdr))

        # copy the file to a local target for further processing
        with self.publish_step("fetch input file ..."):
            tmp = law.LocalFileTarget(is_tmp=".root")
            cmd = "xrdcp {} {}".format(pfn, tmp.uri())
            code = law.util.interruptable_popen(cmd, shell="True", executable="/bin/bash")[0]
            if code != 0:
                raise Exception("xrdcp command failed")

        # open with uproot / coffea / etc and process
        pass


# trailing imports
from ap.tasks.external import GetDatasetLFNs
