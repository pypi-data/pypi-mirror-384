#!/bin/bash
set -euo pipefail
IFS=$'\n\t'



url=$(Git url --gitlab --registry)
status=$?

registry=registry.gitlab.com

if [ $status -ne 0 ]; then
	echo "Could not find the registry url: Exit $status"
	exit $status
fi

docker login -u $CONTAINER_REGISTRY_USER -p $CONTAINER_REGISTRY_PASSWORD "$registry"
docker pull "$url"
docker tag "$url" "${url#$registry/}"
