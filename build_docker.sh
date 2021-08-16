#!/bin/bash

cd "${0%/*}" || exit 1

# set the default Docker image tag to dactyl-keyboard
IMAGE_TAG="dactyl-keyboard"

# by default, don't rebuild the image
REBUILD=false;

# check for command line flags
while getopts 'ri:' flag; do
  case "${flag}" in
    r) REBUILD=true ;; # if the -r flag is set, we should rebuild the image
    i) IMAGE_TAG="${OPTARG}"
  esac
done

# get the image ID, and save the return code so we'll know if the image exists
IMAGE_ID=$(docker inspect --type=image --format={{.Id}} ${IMAGE_TAG})
INSPECT_RETURN_CODE=$?

# if we were specifically told to rebuild, or if the image doesn't exists, then build the docker image
if $REBUILD || [ $INSPECT_RETURN_CODE -ne 0 ]; then
    docker build -t ${IMAGE_TAG} -f docker/Dockerfile .
fi

# run each of the dactyl commands in temporary containers
docker run --name dm-run -d --rm -v "`pwd`/src:/app/src" -v "`pwd`/things:/app/things"  ${IMAGE_TAG} python3 -i dactyl_manuform.py > /dev/null 2>&1
docker run --name dm-config -d --rm -v "`pwd`/:/app/src" -v "`pwd`/things:/app/things" ${IMAGE_TAG} python3 -i generate_configuration.py > /dev/null 2>&1
docker run --name dm-release-build -d --rm -v "`pwd`/:/app/src" -v "`pwd`/things:/app/things" ${IMAGE_TAG} python3 -i model_builder.py > /dev/null 2>&1

# show progress indicator while until dm-run container completes
while $(docker inspect --format={{.Id}} dm-run > /dev/null 2>&1); do
    echo -n "."
    sleep 1.5
done

echo $'\n\nDactyl-Manuform export is complete!\n'