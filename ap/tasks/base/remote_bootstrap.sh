#!/usr/bin/env bash

# Bootstrap file that is executed in remote jobs submitted by law to set up the environment. This
# file contains multiple different bootstrap functions of which only one is invoked by the last line
# of this file. So-called render variables, denoted by "{{name}}", are replaced with variables
# configured in the remote workflow tasks, e.g. in HTCondorWorkflow.htcondor_job_config() upon job
# submission.

# Bootstrap function for htcondor jobs that have the getenv feature enabled, i.e., environment
# variables of the submitting shell and the job node will be identical.
bootstrap_htcondor_getenv() {
    # on the CERN HTCondor batch, the PATH and PYTHONPATH variables are changed even though "getenv"
    # is set, in the job file, so set them manually to the desired values
    if [ "{{ap_htcondor_flavor}}" = "cern" ]; then
        export PATH="{{ap_env_path}}"
        export PYTHONPATH="{{ap_env_pythonpath}}"
    fi

    # set env variables
    export AP_ON_HTCONDOR="1"
    export AP_REMOTE_JOB="1"

    return "0"
}

# Bootstrap function for standalone htcondor jobs, i.e., each jobs fetches a software and repository
# code bundle and unpacks them to have a standalone environment, independent of the submitting one.
# The setup script of the repository is sourced with a few environment variables being set before,
# tailored for remote jobs.
bootstrap_htcondor_standalone() {
    # set env variables
    export AP_BASE="$LAW_JOB_HOME/repo"
    export AP_DATA="$LAW_JOB_HOME/ap_data"
    export AP_SOFTWARE="$AP_DATA/software"
    export AP_STORE="{{ap_store}}"
    export AP_USER="{{ap_user}}"
    export AP_TASK_NAMESPACE="{{ap_task_namespace}}"
    export AP_LOCAL_SCHEDULER="{{ap_local_scheduler}}"
    export AP_ON_HTCONDOR="1"
    export AP_REMOTE_JOB="1"

    # load the software bundle
    mkdir -p "$AP_SOFTWARE"
    cd "$AP_SOFTWARE"
    fetch_local_file "{{ap_software_pattern}}" software.tgz || return "$?"
    tar -xzf "software.tgz" || return "$?"
    rm "software.tgz"
    cd "$LAW_JOB_HOME"

    # load the repo bundle
    mkdir -p "$AP_BASE"
    cd "$AP_BASE"
    fetch_local_file "{{ap_repo_pattern}}" repo.tgz || return "$?"
    tar -xzf "repo.tgz" || return "$?"
    rm "repo.tgz"
    cd "$LAW_JOB_HOME"

    # source the repo setup
    source "$AP_BASE/setup.sh" "default" || return "$?"

    return "0"
}

# Copies a local, potentially replicated file to a certain location. When the file to copy contains
# pattern characters, e.g. "/path/to/some/file.*.tgz", a random existing file matching that pattern
# is selected.
# Arguments:
#   1. src_pattern: Path of a file or pattern matching multiple files of which one is copied.
#   2. dst_path   : Path where the source file should be copied to.
fetch_local_file() {
    # get arguments
    local src_pattern="$1"
    local dst_path="$2"

    # select one random file matched by pattern with two attempts
    local src_path
    for i in 1 2; do
        src_path="$( ls $src_pattern | shuf -n 1 )"
        if [ ! -z "$src_path" ]; then
            echo "using source file $src_path"
            break
        fi

        local msg="could not determine src file from pattern $src_pattern"
        if [ "$i" != "2" ]; then
            echo "$msg, next attempt in 5 seconds"
            sleep 5
        else
            2>&1 echo "$msg, stopping"
            return "1"
        fi
    done

    # create the target directory if it does not exist yet
    local dst_dir="$( dirname "$dst_path" )"
    [ ! -d "$dst_dir" ] && mkdir -p "$dst_dir"

    # copy the file
    cp "$src_path" "$dst_path"
}

bootstrap_{{ap_bootstrap_name}} "$@"
