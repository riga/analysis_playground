# coding: utf-8

"""
Generic tools and base tasks that are defined along typical objects in an analysis.
"""

import os
from collections import OrderedDict

import luigi
import law


law.contrib.load("numpy", "telegram", "root", "tasks")


class BaseTask(law.Task):

    notify_telegram = law.telegram.NotifyTelegramParameter(significant=False)

    exclude_params_req = {"notify_telegram"}

    task_namespace = os.getenv("AP_TASK_NAMESPACE")


class AnalysisTask(BaseTask):

    version = luigi.Parameter(description="mandatory version that is encoded into output paths")

    output_collection_cls = law.SiblingFileCollection
    default_store = "$AP_STORE"
    store_by_family = False

    @classmethod
    def modify_param_values(cls, params):
        """
        Hook to modify command line arguments before instances of this class are created.
        """
        return params

    @classmethod
    def req_params(cls, inst, **kwargs):
        """
        Returns parameters that are jointly defined in this class and another task instance of some
        other class. The parameters are used when calling ``Task.req(self)``.
        """
        # always prefer certain parameters given as task family parameters (--TaskFamily-parameter)
        _prefer_cli = law.util.make_list(kwargs.get("_prefer_cli", []))
        if "version" not in _prefer_cli:
            _prefer_cli.append("version")
        kwargs["_prefer_cli"] = _prefer_cli

        return super(AnalysisTask, cls).req_params(inst, **kwargs)

    def store_parts(self):
        """
        Returns an ordered dictionary whose values are used to create a store path. For instance,
        the parts ``{"keyA": "a", "keyB": "b", 2: "c"}`` lead to the path "a/b/c". The keys can be
        used by subclassing tasks to overwrite values.
        """
        parts = OrderedDict()

        # in this base clas, just add the task family (namespace + class name) or task class name
        parts["task_class"] = self.task_family if self.store_by_family else self.__class__.__name__

        return parts

    def store_parts_ext(self):
        """
        Similar to :py:meth:`store_parts` but these external parts are appended to the end of paths
        created with (e.g.) :py:meth:`local_path`.
        """
        parts = OrderedDict()

        # add the version when set
        if self.version is not None:
            parts["version"] = self.version

        return parts

    def local_path(self, *path, **kwargs):
        """ local_path(*path, store=None)
        Joins several path fragments in the following order:

            - *store* (defaulting to :py:attr:`default_store`)
            - Values of :py:meth:`store_parts` (in that order)
            - Values of :py:meth:`store_parts_ext` (in that order)
            - *path* fragments passed to this method
        """
        # determine the main store directory
        store = kwargs.get("store") or self.default_store

        # concatenate all parts that make up the path
        parts = tuple(self.store_parts().values()) + tuple(self.store_parts_ext().values()) + path

        # join
        path = os.path.join(store, *(str(p) for p in parts))

        return path

    def local_target(self, *path, **kwargs):
        """ local_target(*path, dir=False, store=None, **kwargs)
        Creates either a local file or directory target, depending on *dir*, forwarding all *path*
        fragments and *store* to :py:meth:`local_path` and all *kwargs* the respective target class.
        """
        # select the target class
        cls = law.LocalDirectoryTarget if kwargs.pop("dir", False) else law.LocalFileTarget

        # create the local path
        path = self.local_path(*path, store=kwargs.pop("store", None))

        # create the target instance and return it
        return cls(path, **kwargs)


class CommandTask(AnalysisTask):
    """
    A task that provides convenience methods to work with shell commands, i.e., printing them on the
    command line and executing them with error handling.
    """

    print_command = law.CSVParameter(
        default=(),
        significant=False,
        description="print the command that this task would execute but do not run any task; this "
        "CSV parameter accepts a single integer value which sets the task recursion depth to also "
        "print the commands of required tasks (0 means non-recursive)",
    )
    custom_args = luigi.Parameter(
        default="",
        description="custom arguments that are forwarded to the underlying command; they might not "
        "be encoded into output file paths; no default",
    )

    exclude_index = True
    exclude_params_req = {"custom_args"}
    interactive_params = AnalysisTask.interactive_params + ["print_command"]

    run_command_in_tmp = False

    def _print_command(self, args):
        max_depth = int(args[0])

        print("print task commands with max_depth {}".format(max_depth))

        for dep, _, depth in self.walk_deps(max_depth=max_depth, order="pre"):
            offset = depth * ("|" + law.task.interactive.ind)
            print(offset)

            print("{}> {}".format(offset, dep.repr(color=True)))
            offset += "|" + law.task.interactive.ind

            if isinstance(dep, CommandTask):
                # when dep is a workflow, take the first branch
                text = law.util.colored("command", style="bright")
                if isinstance(dep, law.BaseWorkflow) and dep.is_workflow():
                    dep = dep.as_branch(0)
                    text += " (from branch {})".format(law.util.colored("0", "red"))
                text += ": "

                cmd = dep.build_command()
                if cmd:
                    cmd = law.util.quote_cmd(cmd) if isinstance(cmd, (list, tuple)) else cmd
                    text += law.util.colored(cmd, "cyan")
                else:
                    text += law.util.colored("empty", "red")
                print(offset + text)
            else:
                print(offset + law.util.colored("not a CommandTask", "yellow"))

    def build_command(self):
        # this method should build and return the command to run
        raise NotImplementedError

    def touch_output_dirs(self):
        # keep track of created uris so we can avoid creating them twice
        handled_parent_uris = set()

        for outp in law.util.flatten(self.output()):
            # get the parent directory target
            parent = None
            if isinstance(outp, law.SiblingFileCollection):
                parent = outp.dir
            elif isinstance(outp, law.FileSystemFileTarget):
                parent = outp.parent

            # create it
            if parent and parent.uri() not in handled_parent_uris:
                parent.touch()
                handled_parent_uris.add(parent.uri())

    def run_command(self, cmd, optional=False, **kwargs):
        # proper command encoding
        cmd = (law.util.quote_cmd(cmd) if isinstance(cmd, (list, tuple)) else cmd).strip()

        # when no cwd was set and run_command_in_tmp is True, create a tmp dir
        if "cwd" not in kwargs and self.run_command_in_tmp:
            tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
            tmp_dir.touch()
            kwargs["cwd"] = tmp_dir.path
        self.publish_message("cwd: {}".format(kwargs.get("cwd", os.getcwd())))

        # call it
        with self.publish_step("running '{}' ...".format(law.util.colored(cmd, "cyan"))):
            p, lines = law.util.readable_popen(cmd, shell=True, executable="/bin/bash", **kwargs)
            for line in lines:
                print(line)

        # raise an exception when the call failed and optional is not True
        if p.returncode != 0 and not optional:
            raise Exception("command failed with exit code {}: {}".format(p.returncode, cmd))

        return p

    @law.decorator.log
    @law.decorator.notify
    @law.decorator.safe_output
    def run(self, **kwargs):
        self.pre_run_command()

        # default run implementation
        # first, create all output directories
        self.touch_output_dirs()

        # build the command
        cmd = self.build_command()

        # run it
        self.run_command(cmd, **kwargs)

        self.post_run_command()

    def pre_run_command(self):
        return

    def post_run_command(self):
        return
