# coding: utf-8

"""
Helpers and utilities.
"""

__all__ = []


import os
import uuid
import Queue
import threading
import subprocess
import multiprocessing

import law


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


def wget(src, dst, force=False):
    """
    Downloads a file from a remote *src* to a local destination *dst*, creating intermediate
    directories when needed. When *dst* refers to an existing file, an exception is raised unless
    *force* is *True*.

    The full, normalized destination path is returned.
    """
    # check if the target directory exists
    dst = real_path(dst)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    else:
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            raise IOError("target directory '{}' does not exist".format(dst_dir))

    # remove existing dst or complain
    if os.path.exists(dst):
        if force:
            os.remove(dst)
        else:
            raise IOError("target '{}' already exists".format(dst))

    # actual download
    cmd = ["wget", src, "-O", dst]
    code, _, error = law.util.interruptable_popen(law.util.quote_cmd(cmd), shell=True,
        executable="/bin/bash", stderr=subprocess.PIPE)
    if code != 0:
        raise Exception("wget failed: {}".format(error))

    return dst


def call_thread(func, args=(), kwargs=None, timeout=None):
    """
    Execute a function *func* in a thread and aborts the call when *timeout* is reached. *args* and
    *kwargs* are forwarded to the function.

    The return value is a 3-tuple ``(finsihed_in_time, func(), err)``.
    """
    def wrapper(q, *args, **kwargs):
        try:
            ret = (func(*args, **kwargs), None)
        except Exception as e:
            ret = (None, str(e))
        q.put(ret)

    q = Queue.Queue(1)

    thread = threading.Thread(target=wrapper, args=(q,) + args, kwargs=kwargs or {})
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return (False, None, None)
    else:
        return (True,) + q.get()


def call_proc(func, args=(), kwargs=None, timeout=None):
    """
    Execute a function *func* in a process and aborts the call when *timeout* is reached. *args* and
    *kwargs* are forwarded to the function.

    The return value is a 3-tuple ``(finsihed_in_time, func(), err)``.
    """
    def wrapper(q, *args, **kwargs):
        try:
            ret = (func(*args, **kwargs), None)
        except Exception as e:
            ret = (None, str(e))
        q.put(ret)

    q = multiprocessing.Queue(1)

    proc = multiprocessing.Process(target=wrapper, args=(q,) + args, kwargs=kwargs or {})
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.terminate()
        return (False, None, None)
    else:
        return (True,) + q.get()


def determine_xrd_redirector(lfn, redirectors=None, timeout=30, check_tfile=None):
    """
    Determines the optimal XRootD redirectors for a file given by its *lfn* using a list of possible
    *redirectors* which defaults to *law.cms.Site.redirectors*. Each redirector is contacted in
    order with a certain *timeout* after which the next one is contacted. *check_tfile* can be an
    optional function that receives the opened TFile object and returns *False* in case the file is
    not accessible after all.

    The best redirector is returned.
    """
    if not redirectors:
        redirectors = ["eu", "us", "global"]
    redirectors = [law.cms.Site.redirectors.get(c, c) for c in redirectors]

    pfn = lambda rdr: "root://{}/{}".format(rdr, lfn)

    def check(pfn, check_tfile):
        with law.root.GuardedTFile.Open(pfn) as tfile:
            if callable(check_tfile) and check_tfile(tfile) is False:
                raise Exception("custom tfile check failed")

    for timeout in law.util.make_list(timeout):
        for rdr in redirectors:
            print("check redirector {} (timeout {}s)".format(rdr, timeout))
            finished, _, err = call_thread(check, (pfn(rdr), check_tfile), timeout=timeout)
            if finished and err is None:
                return rdr

    raise Exception("could not determine redirector to load {}".format(lfn))
