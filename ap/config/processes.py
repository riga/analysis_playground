# coding: utf-8

"""
(Nested) physics processes and cross sections.

TODO: Adapt process ids to stay unique.
"""

import order as od
import scinum as sn

from ap.config.constants import br_hh


#
# data
#

process_data = od.Process(
    name="data",
    id=1,
    is_data=True,
    label="data",
)


#
# HH production
#

process_hh = od.Process(
    name="hh",
    id=100,
    label="HH",
)

process_hh_ggf = od.Process(
    name="hh_ggf",
    id=130,
    label=r"$HH_{ggF}$",
    label_short="HH",
    xsecs={
        # https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH?rev=68#Current_recommendations_for_HH_c
        13: sn.Number(0.03105, {
            "scale": (sn.Number.REL, 0.022, 0.050),
            "pdf": (sn.Number.REL, 0.021),
            "alphas": (sn.Number.REL, 0.021),
            "mtop": (sn.Number.REL, 0.026),  # approx.
        }),
    },
)

process_hh_ggf_bbtt = process_hh_ggf.add_process(
    name="hh_ggf_bbtt",
    id=131,
    label=process_hh_ggf.label + r", $b\bar{b}\tau^{+}\tau^{-}$",
    label_short=process_hh_ggf.label_short + r" ($bb\tau\tau$)",
    xsecs={
        13: process_hh_ggf.get_xsec(13) * br_hh.bbtt,
    },
)

process_hh_ggf_bbtt_kl1_kt1 = process_hh_ggf_bbtt.add_process(
    name="hh_ggf_bbtt_kl1_kt1",
    id=132,
    label=process_hh_ggf_bbtt.label + r", $\kappa_{\lambda} = 1",
    label_short=process_hh_ggf_bbtt.label_short,
    xsecs={
        13: process_hh_ggf_bbtt.get_xsec(13),
    },
)

process_hh_ggf_bbtt_kl0_kt1 = process_hh_ggf_bbtt.add_process(
    name="hh_ggf_bbtt_kl0_kt1",
    id=133,
    label=process_hh_ggf_bbtt.label + r", $\kappa_{\lambda} = 0",
    label_short=process_hh_ggf_bbtt.label_short,
    xsecs={
        13: process_hh_ggf_bbtt.get_xsec(13) * 2.268,  # number computed with inference tools
    },
)

process_hh_ggf_bbtt_kl2p45_kt1 = process_hh_ggf_bbtt.add_process(
    name="hh_ggf_bbtt_kl2p35_kt1",
    id=134,
    label=process_hh_ggf_bbtt.label + r", $\kappa_{\lambda} = 2.45",
    label_short=process_hh_ggf_bbtt.label_short,
    xsecs={
        13: process_hh_ggf_bbtt.get_xsec(13) * 0.427,  # number computed with inference tools
    },
)

process_hh_ggf_bbtt_kl5_kt1 = process_hh_ggf_bbtt.add_process(
    name="hh_ggf_bbtt_kl5_kt1",
    id=135,
    label=process_hh_ggf_bbtt.label + r", $\kappa_{\lambda} = 5",
    label_short=process_hh_ggf_bbtt.label_short,
    xsecs={
        13: process_hh_ggf_bbtt.get_xsec(13) * 3.055,  # number computed with inference tools
    },
)
