# coding: utf-8

"""
Tasks related to obtaining, preprocessing and selecting events.
"""

import law

from ap.tasks.base import DatasetTask, HTCondorWorkflow
from ap.util import ensure_proxy, determine_xrd_redirector


class SelectEvents(DatasetTask, law.LocalWorkflow, HTCondorWorkflow):

    sandbox = "bash::$AP_BASE/sandboxes/hh_bbtt_cmssw_default.sh"

    def workflow_requires(self):
        # workflow super classes might already define requirements, so extend them
        reqs = super(SelectEvents, self).workflow_requires()
        reqs["lfns"] = GetDatasetLFNs.req(self)
        return reqs

    def requires(self):
        # workflow branches are normal tasks, so define requirements the normal way
        return {"lfns": GetDatasetLFNs.req(self)}

    def output(self):
        return self.wlcg_target("data_{}.npz".format(self.branch))

    @law.decorator.notify
    @law.decorator.safe_output
    @ensure_proxy
    def run(self):
        import numpy as np

        # get the lfn of the file referenced by this branch
        lfn = str(self.input()["lfns"].random_target().load(formatter="json")[self.branch])
        self.publish_message("found LFN {}".format(lfn))

        # determine the best redirector and build the pfn
        rdr = determine_xrd_redirector(lfn)
        pfn = "root://{}/{}".format(rdr, lfn)
        self.publish_message("using redirector {}".format(rdr))

        # copy the file to a local target for further processing
        with self.publish_step("fetch input file ..."):
            tmp = law.LocalFileTarget(is_tmp=".root")
            cmd = "xrdcp {} {}".format(pfn, tmp.uri())
            code = law.util.interruptable_popen(cmd, shell="True", executable="/bin/bash")[0]
            if code != 0:
                raise Exception("xrdcp command failed")

        # open with uproot / coffea / etc and process
        data = tmp.load(formatter="uproot")
        events = data["Events"]
        self.publish_message("found {} events".format(events.numentries))

        # dummy task: get all jet 1 pt values
        jet1_pt = []
        with self.publish_step("load jet pts ..."):
            for batch in events.iterate(["nJet", "Jet_pt"], entrysteps=1000):
                print("batch")
                mask = batch["nJet"] >= 1
                jet1_pt.append(batch["Jet_pt"][mask][:, 0])

        jet1_pt = np.concatenate(jet1_pt, axis=0)
        self.output().dump(data=jet1_pt, formatter="numpy")


# trailing imports
from ap.tasks.external import GetDatasetLFNs
