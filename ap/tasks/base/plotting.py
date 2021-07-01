# coding: utf-8

"""
Tools and classes for task based plotting.
"""

import importlib

import law
import luigi
import six

from ap.tasks.base import AnalysisTask


class PlotTask(AnalysisTask):

    MISSING_AXIS_LIMIT = -1234.5

    view_cmd = luigi.Parameter(
        default=law.NO_STR,
        significant=False,
        description="a command to execute after the task has run to visualize plots right in the "
        "terminal; no default",
    )
    x_min = luigi.FloatParameter(
        default=MISSING_AXIS_LIMIT,
        significant=False,
        description="the lower x-axis limit; no default",
    )
    x_max = luigi.FloatParameter(
        default=MISSING_AXIS_LIMIT,
        significant=False,
        description="the upper x-axis limit; no default",
    )
    y_min = luigi.FloatParameter(
        default=MISSING_AXIS_LIMIT,
        significant=False,
        description="the lower y-axis limit; no default",
    )
    y_max = luigi.FloatParameter(
        default=MISSING_AXIS_LIMIT,
        significant=False,
        description="the upper y-axis limit; no default",
    )

    def get_axis_limit(self, value):
        if isinstance(value, six.string_types):
            value = getattr(self, value)
        return None if value == self.MISSING_AXIS_LIMIT else value

    def get_plot_func(self, func_id):
        if "." not in func_id:
            raise ValueError("invalid func_id format: {}".format(func_id))
        module_id, name = func_id.rsplit(".", 1)

        try:
            mod = importlib.import_module(module_id)
        except ImportError as e:
            raise ImportError("cannot import plot function {} from module {}: {}".format(
                name, module_id, e))

        func = getattr(mod, name, None)
        if func is None:
            raise Exception("module {} does not contain plot function {}".format(module_id, name))

        return func

    def call_plot_func(self, func_id, **kwargs):
        self.get_plot_func(func_id)(**(self.update_plot_kwargs(kwargs)))

    def update_plot_kwargs(self, kwargs):
        return kwargs


@law.decorator.factory(accept_generator=True)
def view_output_plots(fn, opts, task, *args, **kwargs):
    def before_call():
        return None

    def call(state):
        return fn(task, *args, **kwargs)

    def after_call(state):
        view_cmd = getattr(task, "view_cmd", None)
        if not view_cmd or view_cmd == law.NO_STR:
            return

        # prepare the view command
        if "{}" not in view_cmd:
            view_cmd += " {}"

        # collect all paths to view
        view_paths = []
        outputs = law.util.flatten(task.output())
        while outputs:
            output = outputs.pop(0)
            if isinstance(output, law.TargetCollection):
                outputs.extend(output._flat_target_list)
                continue
            if not getattr(output, "path", None):
                continue
            if output.path.endswith((".pdf", ".png")) and output.path not in view_paths:
                view_paths.append(output.path)

        # loop through paths and view them
        for path in view_paths:
            task.publish_message("showing {}".format(path))
            law.util.interruptable_popen(view_cmd.format(path), shell=True, executable="/bin/bash")

    return before_call, call, after_call
