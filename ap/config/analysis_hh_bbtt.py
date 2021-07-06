# coding: utf-8

"""
Configuration of the HH analysis.
"""

import order as od

import ap.config.processes as procs
from ap.config.campaign_2018 import campaign_2018


#
# the main analysis object
#

ana = analysis_hh_bbtt = od.Analysis(
    name="hh_bbtt",
    id=1,
)

# analysis-global versions
ana.set_aux("versions", {
})


#
# 2018 standard config
#

# create a config by passing the campaign, so id and name will be identical
config_hh_2018 = cfg = ana.add_config(campaign_2018)

# add processes we are interested in
cfg.add_process(procs.process_hh_ggf_bbtt)

# add datasets we need to study
dataset_names = [
    "hh_ggf_kl1_kt1",
    "hh_ggf_kl0_kt1",
    "hh_ggf_kl2p45_kt1",
    "hh_ggf_kl5_kt1",
]
for dataset_name in dataset_names:
    cfg.add_dataset(campaign_2018.get_dataset(dataset_name))

# file merging values
# key -> dataset -> files per branch (-1 or not present = all)
cfg.set_aux("file_merging", {
})

# versions per task and potentially other keys
cfg.set_aux("versions", {
})
