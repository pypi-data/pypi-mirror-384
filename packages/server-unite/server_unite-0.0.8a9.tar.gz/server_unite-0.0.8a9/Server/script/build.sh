#!/bin/bash
set -euo pipefail
IFS=$'\n\t'



SCRIPT="control/container/build"
[ -f "$SCRIPT" ] && "$SCRIPT"
