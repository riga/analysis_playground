# coding: utf-8

"""
Different helpers and ROOT style configurations to be used with plotlib.
"""

import functools
import contextlib

from dhi.util import import_ROOT


_styles = {}


def _setup_styles():
    global _styles
    if _styles:
        return

    import plotlib.root as r

    # ap_default
    s = _styles["ap_default"] = r.styles.copy("default", "ap_default")
    s.legend_y2 = -15
    s.legend_dy = 32
    s.legend.TextSize = 20
    s.legend.FillStyle = 1
    s.style.PaintTextFormat = "1.2f"


def use_style(style_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import plotlib.root as r

            # setup styles
            _setup_styles()

            # invoke the wrapped function in that style
            with r.styles.use(style_name):
                return func(*args, **kwargs)

        return wrapper
    return decorator


@contextlib.contextmanager
def temporary_canvas(*args, **kwargs):
    ROOT = import_ROOT()

    c = ROOT.TCanvas(*args, **kwargs)

    try:
        yield c
    finally:
        if c and not c.IsZombie():
            c.Close()
