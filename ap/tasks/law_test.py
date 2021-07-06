# coding: utf-8

"""
Test tasks. Commands to execute:

MyTask:
> law run MyTask --version v1 --text some_text

WriteWeekday (no version required):
> law run WriteWeekday --day-index 1
> law run WriteWeekday --day-index 2
> law run WriteWeekday --day-index ...

GatherWeekdays, requiring WriteWeedayWorkflow which runs on htcondor (not the one above!)
> law run GatherWeekdays --WriteWeekdayWorkflow-workflow htcondor --WriteWeekdayWorkflow-max-runtime 5min
"""

import law
import luigi

from ap.tasks.base import AnalysisTask, CommandTask, HTCondorWorkflow


class MyTask(CommandTask):
    """
    Test task that write a configurable text into a txt file using an external script (well, echo).
    This is a demonstration for local target operations, so there is no magic involved yet regarding
    the unified local / remote target API.
    """

    text = luigi.Parameter(
        # a default value that is used when none is set otherwise
        default="empty",
        # significant = a change of this parameter will case a different output
        significant=True,
        # help text to show with --help
        description="the text to write",
    )

    def output(self):
        return self.local_target("file.txt")

    def build_command(self):
        # get the output target
        output = self.output()
        return "echo '{}' > {}".format(self.text, output.path)


class WriteWeekday(AnalysisTask):
    """
    Task that takes an index from 0 to 6 and writes the corresponding day of the week into a text
    file using plain law target operations.
    """

    day_index = luigi.ChoiceParameter(
        var_type=int,
        choices=list(range(7)),
        description="the index of the weekday, starting at 0; no default",
    )

    # disable versions which was already shown with MyTask
    version = None

    def output(self):
        return self.local_target("day{}.text".format(self.day_index))

    def run(self):
        # local imports at the top
        import calendar

        # consider this line to be a heavy payload ...
        day_name = calendar.day_name[self.day_index]

        # there are multiple ways to write the output, with two methods below:
        # 1. the long, boilerplate way
        output = self.output()
        output.parent.touch()  # creates the directory (parent is the top level directory target)
        with output.open("w") as f:  # standard file object (or a proxy)
            f.write(day_name + "\n")

        # 2. the elegant way, using target formatters (load and dump, forwarded)
        output.remove()  # remove the output first to be sure the next line works
        output.dump(day_name, formatter="text")


class WriteWeekdayWorkflow(AnalysisTask, law.LocalWorkflow, HTCondorWorkflow):
    """
    Same purpose as above, but this time in a workflow. For more info, see the docs below or read
    https://law.readthedocs.io/en/latest/workflows.html.
    """

    # disable versions which was already shown with MyTask
    version = None

    def create_branch_map(self):
        # return a list of contiguous numbers starting from 0 to an arbitrary payload that each
        # "branch" task can access; since this example is overly trivial, the branch payload
        # (called branch_data) is also just a number from 0 to 6
        day_indices = list(range(7))
        return dict(enumerate(day_indices))

    def output(self):
        # for workflows, output() defines the output per branch task
        # note the use of branch_data
        return self.local_target("day{}.text".format(self.branch_data))

    def run(self):
        # for workflows, run() is executed per branch task whereas the run() method of the workflow
        # is implemented differently (e.g. to submit jobs or run the locally with multiple cores)

        # local imports at the top
        import calendar

        # consider this line to be a heavy payload ...
        # note the use of branch_data which refers to the day_index as our payload
        day_name = calendar.day_name[self.branch_data]

        # write the output
        self.output().dump(day_name, formatter="text")


class GatherWeekdays(AnalysisTask, law.tasks.RunOnceTask):
    """
    Collects all weekdays written into files by branches of the :py:class:`WriteWeekdayWorkflow`
    task and prints them. There is no output, so we need a way to tell luigi/law that the task is
    complete at some point (such that the complete() methods returns *True* and subsequent tasks can
    start). Fortunately, we can inherit from :py:class:`law.tasks.RunOnceTask` which stores a simple
    boolean that is returned once run() finished. We only have to decorate our run() method to
    trigger that.
    """

    # disable versions which was already shown with MyTask
    version = None

    def requires(self):
        return WriteWeekdayWorkflow.req(self)

    @law.tasks.RunOnceTask.complete_on_success
    def run(self):
        # the input of this task is the output of all requirements
        inputs = self.input()

        # we required a workflow, so all targets produced by its branches are stored in the
        # "collection" entry, which is a SiblingTargetCollection (targets in the same dir for faster
        # batched file operations such as "listdir")
        weekdays = [inp.load(formatter="text") for inp in inputs["collection"].targets.values()]

        # print colored
        fancy = lambda s: law.util.colored(s, color="random", background="random")
        print("\n".join(map(fancy, weekdays)))
