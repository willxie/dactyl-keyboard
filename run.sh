#!/bin/bash

cd "${0%/*}" || exit 1



# set the default Docker image tag to dactyl-keyboard
IMAGE_TAG="dactyl-keyboard"

# by default, don't rebuild the image
REBUILD=false;

# get the command the user would like to run
COMMAND=${1:?A command is required. Try \'run help\'}

case $COMMAND in
  help)
    echo "Usage:"
    echo "  run [command]"
    echo ""
    echo "Available Commands:"
    echo "  help        show this help"
    echo "  generate    output the keyboard files to the 'things' directory"
    echo "  configure   "
    echo "  release     "
    echo ""
    echo "Flags:"
    echo "  -r    rebuild the docker image"
    echo "  -i    the tag that should be applied to the docker image"
    exit 0
    ;;
  generate)
    SCRIPT=dactyl_manuform.py
    ;;
  configure)
    SCRIPT=generate_configuration.py
    ;;
  release)
    SCRIPT=model_builder.py
    ;;
  *)
    echo "Invalid command. Try 'run help'"
    exit 1
esac



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




# run the command in a temporary container
docker run --name dm-run -d --rm -v "`pwd`/src:/app/src" -v "`pwd`/things:/app/things"  ${IMAGE_TAG} python3 -i $SCRIPT > /dev/null 2>&1



# show progress indicator while until dm-run container completes
while $(docker inspect --format={{.Id}} dm-run > /dev/null 2>&1); do
    echo -n "."
    sleep 1.5
done

echo $'\n\nDactyl-Manuform export is complete!\n'