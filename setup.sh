#!/usr/bin/env bash

setup() {
    #
    # prepare local variables
    #

    local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
    local orig="$PWD"
    local setup_name="${1:-default}"
    local setup_is_default="false"
    [ "$setup_name" = "default" ] && setup_is_default="true"
    local shell_is_bash="false"
    [ ! -z "$BASH_VERSION" ] && shell_is_bash="true"


    #
    # global variables
    # (AP = Analysis Playground)
    #

    export AP_BASE="$this_dir"
    interactive_setup "$setup_name" || return "$?"
    export AP_STORE_REPO="$AP_BASE/data/store"
    export AP_ORIG_PATH="$PATH"
    export AP_ORIG_PYTHONPATH="$PYTHONPATH"
    export AP_ORIG_PYTHON3PATH="$PYTHON3PATH"
    export AP_ORIG_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
    export AP_SLACK_TOKEN="${AP_SLACK_TOKEN:-}"
    export AP_SLACK_CHANNEL="${AP_SLACK_CHANNEL:-}"
    export AP_TELEGRAM_TOKEN="${AP_TELEGRAM_TOKEN:-}"
    export AP_TELEGRAM_CHAT="${AP_TELEGRAM_CHAT:-}"

    # lang defaults
    [ -z "$LANGUAGE" ] && export LANGUAGE="en_US.UTF-8"
    [ -z "$LANG" ] && export LANG="en_US.UTF-8"
    [ -z "$LC_ALL" ] && export LC_ALL="en_US.UTF-8"


    #
    # helper functions
    #

    # pip install helper
    ap_pip_install() {
        PYTHONUSERBASE="$AP_SOFTWARE" pip install --user --no-cache-dir "$@"
    }
    $shell_is_bash && export -f ap_pip_install


    #
    # minimal local software stack
    #

    # update paths and flags
    local pyv="$( python -c "import sys; print('{0.major}.{0.minor}'.format(sys.version_info))" )"
    export PATH="$AP_BASE/bin:$AP_BASE/ap/scripts:$AP_BASE/modules/law/bin:$AP_SOFTWARE/bin:$PATH"
    export PYTHONPATH="$AP_SOFTWARE/lib/python${pyv}/site-packages:$AP_SOFTWARE/lib64/python${pyv}/site-packages:$PYTHONPATH"
    export PYTHONPATH="$AP_BASE/modules/law:$AP_BASE/modules/scinum:$AP_BASE/modules/order:$AP_BASE/modules/plotlib:$PYTHONPATH"
    export PYTHONPATH="$AP_BASE:$PYTHONPATH"
    export PYTHONWARNINGS="ignore"
    export PYTHONNOUSERSITE="1"
    export GLOBUS_THREAD_MODEL="none"
    ulimit -s unlimited

    # local stack
    local sw_version="1"
    local flag_file_sw="$AP_SOFTWARE/.sw_good"
    [ "$AP_REINSTALL_SOFTWARE" = "1" ] && rm -f "$flag_file_sw"
    if [ ! -f "$flag_file_sw" ]; then
        echo "installing software stack at $AP_SOFTWARE"
        rm -rf "$AP_SOFTWARE/lib"
        mkdir -p "$AP_SOFTWARE"

        # python packages
        ap_pip_install six==1.15.0 || return "$?"
        ap_pip_install luigi==2.8.13 || return "$?"
        ap_pip_install python-telegram-bot==12.3.0 || return "$?"

        date "+%s" > "$flag_file_sw"
        echo "version $sw_version" >> "$flag_file_sw"
    fi
    export AP_SOFTWARE_FLAG_FILES="$flag_file_sw"

    # check the version in the sw flag file and show a warning when there was an update
    if [ "$( cat "$flag_file_sw" | grep -Po "version \K\d+.*" )" != "$sw_version" ]; then
        2>&1 echo ""
        2>&1 echo "WARNING: your local software stack is not up to date, please consider updating it in a new shell with"
        2>&1 echo "         > AP_REINSTALL_SOFTWARE=1 source setup.sh $( $setup_is_default || echo "$setup_name" )"
        2>&1 echo ""
    fi

    # gfal2 bindings (optional)
    local lcg_dir="/cvmfs/grid.cern.ch/centos7-ui-4.0.3-1_umd4v3/usr"
    if [ ! -d "$lcg_dir" ]; then
        2>&1 echo "lcg directory $lcg_dir not existing, skipping gfal2 setup"
    else
        export AP_GFAL_DIR="$AP_SOFTWARE/gfal2"
        export GFAL_PLUGIN_DIR="$AP_GFAL_DIR/plugins"
        export PYTHONPATH="$AP_GFAL_DIR:$PYTHONPATH"

        local flag_file_gfal="$AP_SOFTWARE/.gfal_good"
        [ "$AP_REINSTALL_GFAL" = "1" ] && rm -f "$flag_file_gfal"
        if [ ! -f "$flag_file_gfal" ]; then
            echo "linking gfal2 bindings"

            rm -rf "$AP_GFAL_DIR"
            mkdir -p "$GFAL_PLUGIN_DIR"

            ln -s $lcg_dir/lib64/python2.7/site-packages/gfal2.so "$AP_GFAL_DIR" || return "$?"
            ln -s $lcg_dir/lib64/gfal2-plugins/libgfal_plugin_* "$GFAL_PLUGIN_DIR" || return "$?"

            date "+%s" > "$flag_file_gfal"
        fi
        export AP_SOFTWARE_FLAG_FILES="$AP_SOFTWARE_FLAG_FILES $flag_file_gfal"
    fi


    #
    # initialze submodules
    #

    if [ -d "$AP_BASE/.git" ]; then
        for m in law order scinum plotlib; do
            local mpath="$AP_BASE/modules/$m"
            # initialize the submodule when the directory is empty
            local mfiles=( "$mpath"/* )
            if [ "${#mfiles}" = "0" ]; then
                git submodule update --init --recursive "$mpath"
            else
                # update when not on a working branch and there are no changes
                local detached_head="$( ( cd "$mpath"; git symbolic-ref -q HEAD &> /dev/null ) && echo true || echo false )"
                local changed_files="$( cd "$mpath"; git status --porcelain=v1 2> /dev/null | wc -l )"
                if ! $detached_head && [ "$changed_files" = "0" ]; then
                    git submodule update --init --recursive "$mpath"
                fi
            fi
        done
    fi


    #
    # law setup
    #

    export LAW_HOME="$AP_BASE/.law"
    export LAW_CONFIG_FILE="$AP_BASE/law.cfg"

    if which law &> /dev/null; then
        # source law's bash completion scipt
        source "$( law completion )" ""

        # silently index
        law index -q
    fi
}

interactive_setup() {
    local setup_name="${1:-default}"
    local env_file="${2:-$AP_BASE/.setups/$setup_name.sh}"
    local env_file_tmp="$env_file.tmp"

    # check if the setup is the default one
    local setup_is_default="false"
    [ "$setup_name" = "default" ] && setup_is_default="true"

    # when the setup already exists and it's not the default one,
    # source the corresponding env file and stop
    if ! $setup_is_default; then
        if [ -f "$env_file" ]; then
            echo -e "using variables for setup '\x1b[0;49;35m$setup_name\x1b[0m' from $env_file"
            source "$env_file" ""
            return "0"
        else
            echo -e "no setup file $env_file found for setup '\x1b[0;49;35m$setup_name\x1b[0m'"
        fi
    fi

    export_and_save() {
        local varname="$1"
        local value="$2"

        export $varname="$value"
        ! $setup_is_default && echo "export $varname=\"$value\"" >> "$env_file_tmp"
    }

    query() {
        local varname="$1"
        local text="$2"
        local default="$3"
        local default_text="${4:-$default}"

        # when the setup is the default one, use the default value when the env variable is empty,
        # otherwise, query interactively
        local value="$default"
        if $setup_is_default; then
            [ ! -z "${!varname}" ] && value="${!varname}"
        else
            printf "$text (\x1b[1;49;39m$varname\x1b[0m, default \x1b[1;49;39m$default_text\x1b[0m):  "
            read query_response
            [ "X$query_response" = "X" ] && query_response="$default"

            # repeat for boolean flags that were not entered correctly
            while true; do
                ( [ "$default" != "True" ] && [ "$default" != "False" ] ) && break
                ( [ "$query_response" = "True" ] || [ "$query_response" = "False" ] ) && break
                printf "please enter either '\x1b[1;49;39mTrue\x1b[0m' or '\x1b[1;49;39mFalse\x1b[0m':  " query_response
                read query_response
                [ "X$query_response" = "X" ] && query_response="$default"
            done

            # save the expanded value
            value="$( eval "echo $query_response" )"
            # strip " and ' on both sides
            value=${value%\"}
            value=${value%\'}
            value=${value#\"}
            value=${value#\'}
        fi

        export_and_save "$varname" "$value"
    }

    # prepare the tmp env file
    if ! $setup_is_default; then
        rm -rf "$env_file_tmp"
        mkdir -p "$( dirname "$env_file_tmp" )"

        echo -e "Start querying variables for setup '\x1b[0;49;35m$setup_name\x1b[0m', press enter to accept default values\n"
    fi

    # start querying for variables
    query AP_USER "CERN / WLCG username" "$( whoami )"
    query AP_DATA "Local data directory" "$AP_BASE/data" "./data"
    query AP_STORE "Default local output store" "$AP_DATA/store" "\$AP_DATA/store"
    query AP_STORE_BUNDLES "Output store for software bundles when submitting jobs" "$AP_STORE" "\$AP_STORE"
    query AP_SOFTWARE "Directory for installing software" "$AP_DATA/software" "\$AP_DATA/software"
    query AP_JOB_DIR "Directory for storing job files" "$AP_DATA/jobs" "\$AP_DATA/jobs"
    query AP_TASK_NAMESPACE "Namespace (i.e. the prefix) of law tasks" "" "''"
    query AP_LOCAL_SCHEDULER "Use a local scheduler for law tasks" "True"
    if [ "$AP_LOCAL_SCHEDULER" != "True" ]; then
        query AP_SCHEDULER_HOST "Address of a central scheduler for law tasks" "USER:PASS@HOST.TLD"
        query AP_SCHEDULER_PORT "Port of a central scheduler for law tasks" "80"
    else
        export_and_save AP_SCHEDULER_HOST "USER:PASS@HOST.TLD"
        export_and_save AP_SCHEDULER_PORT "80"
    fi

    # move the env file to the correct location for later use
    if ! $setup_is_default; then
        mv "$env_file_tmp" "$env_file"
        echo -e "\nsetup variables written to $env_file"
    fi
}

action() {
    if setup "$@"; then
        echo -e "\x1b[0;49;35manalysis playground successfully setup\x1b[0m"
        return "0"
    else
        local code="$?"
        echo -e "\x1b[0;49;31msetup failed with code $code\x1b[0m"
        return "$code"
    fi
}
action "$@"
