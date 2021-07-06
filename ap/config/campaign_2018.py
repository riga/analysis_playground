# coding: utf-8

"""
Common (analysis independent!) definition of the 2018 data-taking campaign.
See https://python-order.readthedocs.io/en/latest/quickstart.html#analysis-campaign-and-config.
"""

import order as od

import ap.config.processes as procs


#
# campaigns
# (the overall container of the 2018 data-taking period)
#

# campaign
campaign_2018 = od.Campaign(
    name="run2_pp_2018",
    id=1,
    ecm=13,
    bx=25,
)


#
# datasets
#

# place datasets in a uniqueness context so that names and ids won't collide with other campaigns
with od.uniqueness_context(campaign_2018.name):
    campaign_2018.add_dataset(
        name="hh_ggf_kl1_kt1",
        id=1,
        n_files=38,
        n_events=973400,
        keys=[
            "/GluGluToHHTo2B2Tau_node_cHHH1_TuneCP5_PSWeights_13TeV-powheg-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
        ],
        processes=[procs.process_hh_ggf_bbtt_kl1_kt1],
    )
    campaign_2018.add_dataset(
        name="hh_ggf_kl0_kt1",
        id=2,
        n_files=35,
        n_events=971000,
        keys=[
            "/GluGluToHHTo2B2Tau_node_cHHH0_TuneCP5_PSWeights_13TeV-powheg-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
        ],
        processes=[procs.process_hh_ggf_bbtt_kl0_kt1],
    )
    campaign_2018.add_dataset(
        name="hh_ggf_kl2p45_kt1",
        id=3,
        n_files=50,
        n_events=967100,
        keys=[
            "/GluGluToHHTo2B2Tau_node_cHHH2p45_TuneCP5_PSWeights_13TeV-powheg-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
        ],
        processes=[procs.process_hh_ggf_bbtt_kl2p45_kt1],
    )
    campaign_2018.add_dataset(
        name="hh_ggf_kl5_kt1",
        id=4,
        n_files=33,
        n_events=974700,
        keys=[
            "/GluGluToHHTo2B2Tau_node_cHHH5_TuneCP5_PSWeights_13TeV-powheg-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
        ],
        processes=[procs.process_hh_ggf_bbtt_kl5_kt1],
    )
