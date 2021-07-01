# coding: utf-8

"""
Helpers and utilities.
"""

import os
import uuid


# modules and objects from lazy imports
_plt = None
_ROOT = None


def import_plt():
    """
    Lazily imports and configures matplotlib pyplot.
    """
    global _plt

    if not _plt:
        import matplotlib

        matplotlib.use("Agg")
        matplotlib.rc("text", usetex=True)
        matplotlib.rcParams["text.latex.preamble"] = [r"\usepackage{amsmath}"]
        matplotlib.rcParams["legend.edgecolor"] = "white"
        import matplotlib.pyplot as plt

        _plt = plt

    return _plt


def import_ROOT():
    """
    Lazily imports and configures ROOT.
    """
    global _ROOT

    if not _ROOT:
        import ROOT

        ROOT.PyConfig.IgnoreCommandLineOptions = True
        ROOT.gROOT.SetBatch()

        _ROOT = ROOT

    return _ROOT


class DotDict(dict):
    """
    Dictionary providing item access via attributes.
    """

    def __getattr__(self, attr):
        return self[attr]

    def copy(self):
        return self.__class__(super(DotDict, self).copy())


def create_random_name():
    return str(uuid.uuid4())


def expand_path(path):
    """
    Takes a *path* and recursively expands all contained environment variables.
    """
    while "$" in path or "~" in path:
        path = os.path.expandvars(os.path.expanduser(path))

    return path


def real_path(path):
    """
    Takes a *path* and returns its real, absolute location with all variables expanded.
    """
    return os.path.realpath(expand_path(path))
