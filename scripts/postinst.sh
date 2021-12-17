#!/bin/sh

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command failed with exit code $?."' ERR

python3 -m pip install --trusted-host pypi.org "workalendar>=16.0.0,<17.0.0"

