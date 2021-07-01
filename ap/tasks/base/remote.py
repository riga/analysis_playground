# coding: utf-8

"""
Base classes and tools for working with remote tasks and targets.
"""

import os
import re
import math

import luigi
import law

from ap.tasks.base import AnalysisTask


law.contrib.load("git", "htcondor")


class HTCondorWorkflow(law.htcondor.HTCondorWorkflow):

    transfer_logs = luigi.BoolParameter(
        default=True,
        significant=False,
        description="transfer job logs to the output directory; default: True",
    )
    max_runtime = law.DurationParameter(
        default=2.0,
        unit="h",
        significant=False,
        description="maximum runtime; default unit is hours; default: 2",
    )
    htcondor_cpus = luigi.IntParameter(
        default=law.NO_INT,
        significant=False,
        description="number of CPUs to request; empty value leads to the cluster default setting; "
        "no default",
    )
    htcondor_flavor = luigi.ChoiceParameter(
        default=os.getenv("AP_HTCONDOR_FLAVOR", "cern"),
        choices=("cern",),
        significant=False,
        description="the 'flavor' (i.e. configuration name) of the batch system; choices: cern; "
        "default: {}".format(os.getenv("AP_HTCONDOR_FLAVOR", "cern")),
    )
    htcondor_getenv = luigi.BoolParameter(
        default=False,
        significant=False,
        description="whether to use htcondor's getenv feature to set the job enrivonment to the "
        "current one, instead of using repository and software bundling; default: False",
    )
    htcondor_group = luigi.Parameter(
        default=law.NO_STR,
        significant=False,
        description="the name of an accounting group on the cluster to handle user priority; not "
        "used when empty; no default",
    )

    exclude_params_branch = {
        "max_runtime", "htcondor_cpus", "htcondor_flavor", "htcondor_getenv", "htcondor_group",
    }

    def htcondor_workflow_requires(self):
        reqs = law.htcondor.HTCondorWorkflow.htcondor_workflow_requires(self)

        # add repo and software bundling as requirements when getenv is not requested
        if not self.htcondor_getenv:
            reqs["repo"] = BundleRepo.req(self, replicas=3)
            reqs["software"] = BundleSoftware.req(self, replicas=3)

        return reqs

    def htcondor_output_directory(self):
        # the directory where submission meta data and logs should be stored
        return self.local_target(store="$AP_STORE_REPO", dir=True)

    def htcondor_bootstrap_file(self):
        # each job can define a bootstrap file that is executed prior to the actual job
        # in order to setup software and environment variables
        return os.path.expandvars("$AP_BASE/ap/tasks/base/remote_bootstrap.sh")

    def htcondor_job_config(self, config, job_num, branches):
        # use cc7 at CERN (http://batchdocs.web.cern.ch/batchdocs/local/submit.html#os-choice)
        if self.htcondor_flavor == "cern":
            config.custom_content.append(("requirements", '(OpSysAndVer =?= "CentOS7")'))
        # copy the entire environment when requests
        if self.htcondor_getenv:
            config.custom_content.append(("getenv", "true"))

        # the CERN htcondor setup requires a "log" config, but we can safely set it to /dev/null
        # if you are interested in the logs of the batch system itself, set a meaningful value here
        config.custom_content.append(("log", "/dev/null"))

        # max runtime
        config.custom_content.append(("+MaxRuntime", int(math.floor(self.max_runtime * 3600)) - 1))

        # request cpus
        if self.htcondor_cpus > 0:
            config.custom_content.append(("RequestCpus", self.htcondor_cpus))

        # accounting group for priority on the cluster
        if self.htcondor_group and self.htcondor_group != law.NO_STR:
            config.custom_content.append(("+AccountingGroup", self.htcondor_group))

        # render_variables are rendered into all files sent with a job
        if self.htcondor_getenv:
            config.render_variables["ap_bootstrap_name"] = "htcondor_getenv"
        else:
            reqs = self.htcondor_workflow_requires()
            config.render_variables["ap_bootstrap_name"] = "htcondor_standalone"
            config.render_variables["ap_software_pattern"] = reqs["software"].get_file_pattern()
            config.render_variables["ap_repo_pattern"] = reqs["repo"].get_file_pattern()
        config.render_variables["ap_env_path"] = os.environ["PATH"]
        config.render_variables["ap_env_pythonpath"] = os.environ["PYTHONPATH"]
        config.render_variables["ap_htcondor_flavor"] = self.htcondor_flavor
        config.render_variables["ap_base"] = os.environ["AP_BASE"]
        config.render_variables["ap_user"] = os.environ["AP_USER"]
        config.render_variables["ap_store"] = os.environ["AP_STORE"]
        config.render_variables["ap_task_namespace"] = os.environ["AP_TASK_NAMESPACE"]
        config.render_variables["ap_local_scheduler"] = os.environ["AP_LOCAL_SCHEDULER"]

        return config

    def htcondor_use_local_scheduler(self):
        # remote jobs should not communicate with ther central scheduler but with a local one
        return True


class BundleRepo(AnalysisTask, law.git.BundleGitRepository, law.tasks.TransferLocalFile):

    replicas = luigi.IntParameter(
        default=5,
        description="number of replicas to generate; default: 5",
    )

    exclude_files = ["docs", "data", ".law", ".setups"]

    version = None
    task_namespace = None
    default_store = "$AP_STORE_BUNDLES"

    def get_repo_path(self):
        # required by BundleGitRepository
        return os.environ["AP_BASE"]

    def single_output(self):
        repo_base = os.path.basename(self.get_repo_path())
        return self.local_target("{}.{}.tgz".format(repo_base, self.checksum))

    def get_file_pattern(self):
        path = os.path.expandvars(os.path.expanduser(self.single_output().path))
        return self.get_replicated_path(path, i=None if self.replicas <= 0 else "*")

    def output(self):
        return law.tasks.TransferLocalFile.output(self)

    @law.decorator.safe_output
    def run(self):
        # create the bundle
        bundle = law.LocalFileTarget(is_tmp="tgz")
        self.bundle(bundle)

        # log the size
        self.publish_message("bundled repository archive, size is {:.2f} {}".format(
            *law.util.human_bytes(bundle.stat.st_size)))

        # transfer the bundle
        self.transfer(bundle)


class BundleSoftware(AnalysisTask, law.tasks.TransferLocalFile):

    replicas = luigi.IntParameter(
        default=5,
        description="number of replicas to generate; default: 5",
    )

    version = None
    default_store = "$AP_STORE_BUNDLES"

    def __init__(self, *args, **kwargs):
        super(BundleSoftware, self).__init__(*args, **kwargs)

        self._checksum = None

    @property
    def checksum(self):
        if not self._checksum:
            # read content of all software flag files and create a hash
            contents = []
            for flag_file in os.environ["AP_SOFTWARE_FLAG_FILES"].strip().split():
                if os.path.exists(flag_file):
                    with open(flag_file, "r") as f:
                        contents.append((flag_file, f.read().strip()))
            self._checksum = law.util.create_hash(contents)

        return self._checksum

    def single_output(self):
        return self.local_target("software.{}.tgz".format(self.checksum))

    def get_file_pattern(self):
        path = os.path.expandvars(os.path.expanduser(self.single_output().path))
        return self.get_replicated_path(path, i=None if self.replicas <= 0 else "*")

    @law.decorator.safe_output
    def run(self):
        software_path = os.environ["AP_SOFTWARE"]

        # create the local bundle
        bundle = law.LocalFileTarget(software_path + ".tgz", is_tmp=True)

        def _filter(tarinfo):
            if re.search(r"(\.pyc|\/\.git|\.tgz|__pycache__|black)$", tarinfo.name):
                return None
            return tarinfo

        # create the archive with a custom filter
        bundle.dump(software_path, filter=_filter)

        # log the size
        self.publish_message("bundled software archive, size is {:.2f} {}".format(
            *law.util.human_bytes(bundle.stat.st_size)))

        # transfer the bundle
        self.transfer(bundle)
