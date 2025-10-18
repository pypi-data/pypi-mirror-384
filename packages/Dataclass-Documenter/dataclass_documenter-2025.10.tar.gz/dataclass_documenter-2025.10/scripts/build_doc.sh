#!/usr/bin/env bash
set -euo pipefail

SELF=$(readlink -f "${BASH_SOURCE[0]}")
DIR=${SELF%/*/*}

cd -- "$DIR"

function show_help()
{
  cat << HELP
USAGE

  ${0##*/} [-h] [-v]

OPTIONS

  -h
    Show this help message and exit.

  -v
    Use a Python virtual environment to build the documentation.

HELP
  exit "$1"
}

function ensure_venv()
{
  local venv_dir=$1
  if [[ ! -e "$venv_dir/bin/activate" ]]
  then
    if command -v uv >/dev/null 2>&1
    then
      uv venv "$venv_dir"
    else
      python3 -m venv "$venv_dir"
    fi
  fi
}

function ensure_uv()
{
  if ! command -v uv >/dev/null 2>&1
  then
    python3 -m ensurepip
    pip install -U pip
    pip install -U uv
  fi
}

venv_dir=venv
while getopts "hv:" opt
do
  case "$opt" in
    h) show_help 0 ;;
    v) venv_dir=$OPTARG ;;
    *) show_help 1 ;;
  esac
done
shift $((OPTIND - 1))

ensure_venv "$venv_dir"
# shellcheck source=/dev/null
source "$venv_dir/bin/activate"
ensure_uv

uv pip install -U -r doc/requirements.txt
sphinx-apidoc -o doc/source -f -H "API Documentation" ./src
sphinx-build -b html doc/source public
# Run again to fix cross-references.
sphinx-build -b html doc/source public
