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

analysis_hh = od.Analysis(
    name="hh",
    id=1,
)

# create a config by passing the campaign, so id and name will be identical
config_hh_2018 = analysis_hh.add_config(campaign_2018)

# add processes we are interested in
config_hh_2018.add_process(procs.process_hh_ggf_bbtt)

# add datasets we need to study
dataset_names = [
    "hh_ggf_kl1_kt1",
    "hh_ggf_kl0_kt1",
    "hh_ggf_kl2p45_kt1",
    "hh_ggf_kl5_kt1",
]
for dataset_name in dataset_names:
    config_hh_2018.add_dataset(campaign_2018.get_dataset(dataset_name))
