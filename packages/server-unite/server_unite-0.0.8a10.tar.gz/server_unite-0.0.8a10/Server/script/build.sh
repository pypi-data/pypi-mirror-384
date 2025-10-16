#!/bin/bash
set -euo pipefail
IFS=$'\n\t'



if [ -f "control/container/build" ]; then
	control/container/build
else
	exit 0
fi
