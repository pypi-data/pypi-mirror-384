#!/bin/bash
# create a "snapshot" of a git repo.
# - write output from git commands to files
# - keep the folder of those contents if they are unique
#
# usage: cli_snapshot_state.sh [list of rel paths]
#
# the paths are relative to the current path. the paths must be to git repos.
# the state is capture for the git repo and any submodules if present.
#
# NOTE: this is an imsi integrated tool, and assumes certain processes and
# states of execution upstream.
#
set -e

bail() {
    echo "$(basename $0) ERROR: $*"
    exit 1
}

usage () {
   echo "Usage: $0 -p <rel_path> [-i <run_dir>] [-o <out_dir>]"
}

help () {
    usage
    echo ""
    echo "Arguments:"
    echo "     -p <rel_path>"
    echo "          Relative paths to <run_dir>. Must be git repo."
    echo "          Multiple paths can be supplied by repeating -p."
    echo ""
    echo "Options:"
    echo "     -i <run_dir>"
    echo "          Input directory, usually run directory (default pwd)."
    echo "     -o <out_dir>"
    echo "          Parent path to where the log artefacts are written"
    echo "          (as <out_dir>/.imsi/states) (default pwd)."
    echo "     -h"
    echo "          Display usage information."
    echo ""
}

# defaults / init
rel_paths=()
run_dir=$(pwd)
out_dir=$(pwd)

# note: since this is an integrated imsi tool, pwd is usually the
# work dir (runid) folder from where the imsi command is issued.
# this should be left as-is for most applications.
# other internal imsi tools may call this tool, which then would require
# setting -i and -o explicitly.

OPTSTRING=":p:i:o:h"

while getopts ${OPTSTRING} opt; do
    case $opt in
        p)
            rel_paths+=("$OPTARG")
            ;;
        i)
            run_dir=${OPTARG}
            ;;
        o)
            out_dir=${OPTARG}
            ;;
        h)
            help
            exit 0
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            exit 1
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

snapshot_git_state() {
    local path
    local log_prefix
    local cwd
    path=$1
    log_prefix=$2
    cwd=$(pwd)

    if [[ -z $log_prefix ]]; then
        log_prefix=""
    else
        log_prefix="${log_prefix}_"
    fi

    cd $path
    mh=$(git rev-parse HEAD)
    desc=$(git describe --always)
    echo $path >> $tmp_dir/${log_prefix}rev.txt
    echo $mh $(basename $path) "(${desc})" >> $tmp_dir/${log_prefix}rev.txt
    git submodule status --recursive >> $tmp_dir/${log_prefix}rev.txt
    git status --porcelain=v1 >> $tmp_dir/${log_prefix}status.txt
    git diff --submodule=diff > $tmp_dir/${log_prefix}diff.diff
    cd $cwd
}

is_git_repo() {
    local path=$1
    if [[ -d "${path}/.git" ]]; then
        echo 1
    else
        echo 0
    fi
}

#======================
# prep
#======================

[[ -d $run_dir ]] || bail No directory $run_dir
[[ -d $out_dir ]] || bail No directory $out_dir

full_paths=( "${rel_paths[@]/#/$run_dir/}" )

# validate
for p in "${full_paths[@]}"; do
    if [[ ! -d "${p}" ]]; then
        bail $p is not a valid directory
    fi
    rc=$(is_git_repo "${p}")
    if [ $rc == 0 ]; then
        bail $p is not a git repo
    fi
done

# create output folders
log_dir=$out_dir/.imsi/states
tmp_dir=$log_dir/tmp_state

mkdir -p $tmp_dir

#======================
# snapshot
#======================

# iterate over the folders -- determine naming and snapshot state by
# creating artefacts
#   account for duplicate names by creating an id for the input folder path
#   by combining the basename and (short) hash of its full folder path
#  (assume this is deterministic)
#  (the full file paths are written to the *rev.txt files for cross referencing)

for p in ${full_paths[@]}; do
    b=$(basename "$p")
    p_id=$( echo $p | md5sum | cut -c1-7 )
    b_id="${b}_${p_id}"
    snapshot_git_state $p $b_id $run_dir
done

# hash the folder of the entire state
hash=$(find $tmp_dir -type f -exec md5sum {} \; | sort -k 2 | md5sum | awk '{ print $1 }')

if [ -d $log_dir/$hash ]; then
    # if hash exists, remove the tmp_dir
    rm -rf $tmp_dir
else
    # otherwise, save this new state
    mv $tmp_dir $log_dir/$hash
fi

echo $hash
