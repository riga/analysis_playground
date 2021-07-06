# coding: utf-8

"""
Scinentific constants.
"""

import scinum as sn

from ap.util import DotDict


# branching ratios at mH = 125.09 GeV
br_h = DotDict(
    ww=sn.Number(0.2152, (sn.Number.REL, 0.0153, 0.0152)),
    zz=sn.Number(0.02641, (sn.Number.REL, 0.0153, 0.0152)),
    gg=sn.Number(0.002270, (sn.Number.REL, 0.0205, 0.0209)),
    bb=sn.Number(0.5809, (sn.Number.REL, 0.0124, 0.0126)),
    tt=sn.Number(0.06256, (sn.Number.REL, 0.0165, 0.0163)),
)

br_hh = DotDict(
    bbbb=br_h.bb ** 2.0,
    bbvv=2.0 * br_h.bb * (br_h.ww + br_h.zz),
    bbww=2.0 * br_h.bb * br_h.ww,
    bbzz=2.0 * br_h.bb * br_h.zz,
    bbtt=2.0 * br_h.bb * br_h.tt,
    bbgg=2.0 * br_h.bb * br_h.gg,
    ttww=2.0 * br_h.tt * br_h.ww,
    ttzz=2.0 * br_h.tt * br_h.zz,
    tttt=br_h.tt ** 2.0,
    wwww=br_h.ww ** 2.0,
    zzzz=br_h.zz ** 2.0,
    wwzz=2.0 * br_h.ww * br_h.zz,
    wwgg=2.0 * br_h.ww * br_h.gg,
)
