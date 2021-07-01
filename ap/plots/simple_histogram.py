# coding: utf-8

"""
Example plots using ROOT.
"""

import numpy as np

from dhi.plots.util import use_style


@use_style("ap_default")
def plot_histogram(
    paths,
    data,
    n_bins=20,
    x_min=None,
    x_max=None,
    y_min=None,
    y_max=None,
):
    """
    Creates a histogram of data and stores it at *paths*.

    *x_min*, *x_max*, *y_min* and *y_max* define the axes ranges and default to the ranges of the
    given values.
    """
    import plotlib.root as r
    ROOT = r.ROOT

    # make sure data is a numpy array
    data = np.array(data)

    # set default ranges
    if x_min is None:
        x_min = data.min()
    if x_max is None:
        x_max = data.max()

    # start plotting
    r.setup_style()
    canvas, (pad,) = r.routines.create_canvas()
    pad.cd()
    draw_objs = []

    # dummy histogram to control axes
    h_dummy = ROOT.TH1F("dummy", ";;Entries", 1, x_min, x_max)
    r.setup_hist(h_dummy, pad=pad, props={"LineWidth": 0})
    draw_objs.append((h_dummy, "HIST"))

    # create and fill the histogram
    h_data = ROOT.TH1F("h", "", n_bins, x_min, x_max)
    r.setup_hist(h_data)
    draw_objs.append((h_data, "SAME,HIST"))
    for value in data:
        h_data.Fill(value)

    # set y limits
    h_dummy.SetMinimum(0.0)
    h_dummy.SetMaximum(h_data.GetMaximum() * 1.2)

    # cms label
    cms_labels = r.routines.create_cms_labels(pad=pad)
    draw_objs.extend(cms_labels)

    # some top-right label
    top_right_label = r.routines.create_top_right_label("Test plot", pad=pad)
    draw_objs.append(top_right_label)

    # draw all objects
    r.routines.draw_objects(draw_objs)

    # save
    r.update_canvas(canvas)
    for path in paths:
        canvas.SaveAs(path)
