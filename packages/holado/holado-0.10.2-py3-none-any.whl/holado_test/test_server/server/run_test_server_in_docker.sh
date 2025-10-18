#!/bin/bash

# Script to launch Test Server as a docker image.
# 
# Test Server exposes a REST API for some docker commands.
# It is accessible on localhost, and also on a docker network if HOLADO_NETWORK is defined.
# On all networks, API is accessible on same port (HOLADO_TEST_SERVER_PORT or 8001).
#
# REST API specification is in file rest/openapi.yaml.
#
# REQUIREMENTS:
#     Have access to any HolAdo registry.
#
#     Optionally, define in .profile the following variables
#         - HOLADO_TEST_SERVER_HOST: host of test-server, or name of its container
#         - HOLADO_TEST_SERVER_PORT: REST API port to use (default: 51232)
#         - HOLADO_IMAGE_REGISTRY: docker image registry to use (default: holado/test_server)
#         - HOLADO_IMAGE_TAG: docker image tag to use (default: latest)
#         - HOLADO_OUTPUT_BASEDIR: absolute path to base output directory (default: [HOME]/.holado/output)
#         - HOLADO_USE_LOCALHOST: force the container network to 'host'.
#         - HOLADO_NETWORK: specify on which network the docker is run.
#


WORK_DIR="$(pwd)"

if [[ -z "$HOLADO_IMAGE_REGISTRY" ]]; then
    HOLADO_IMAGE_REGISTRY=holado/test_server
fi
if [[ -z "$HOLADO_IMAGE_TAG" ]]; then
    HOLADO_IMAGE_TAG=latest
fi
SERVER_IMAGE=${HOLADO_IMAGE_REGISTRY}:${HOLADO_IMAGE_TAG}

# Update docker image
echo "Updating docker image ${SERVER_IMAGE}..."
docker pull ${SERVER_IMAGE}

# Define test output directory
if [[ ! -z "$HOLADO_OUTPUT_BASEDIR" ]]; then
    OUTPUT_DIR=${HOLADO_OUTPUT_BASEDIR}
else
    OUTPUT_DIR=${HOME}/.holado/output
fi
echo "Output directory: $OUTPUT_DIR"

# Define test resources directory
if [[ ! -z "$HOLADO_LOCAL_RESOURCES_BASEDIR" ]]; then
    RESOURCES_DIR=${HOLADO_LOCAL_RESOURCES_BASEDIR}
else
    RESOURCES_DIR=${HOME}/.holado/resources
fi
echo "Resources directory: $RESOURCES_DIR"

# Make dirs
if [ ! -d ${OUTPUT_DIR} ]; then
    echo "Create output directory: ${OUTPUT_DIR}"
    mkdir -p ${OUTPUT_DIR}
fi
if [ ! -d ${RESOURCES_DIR} ]; then
    echo "Create resources directory: ${RESOURCES_DIR}"
    mkdir -p ${RESOURCES_DIR}
fi

# Define container network
if [ "$HOLADO_USE_LOCALHOST" = True ]; then
	NETWORK_DEF_COMMAND="--network=host"
else
	if [[ ! -z "$HOLADO_NETWORK" ]]; then
		NETWORK_DEF_COMMAND="--network $HOLADO_NETWORK"
	else
		NETWORK_DEF_COMMAND=""
	fi
fi

# Define port to use
if [[ -z "$HOLADO_TEST_SERVER_PORT" ]]; then
    HOLADO_TEST_SERVER_PORT=51232
fi


# Docker run 
if [[ -z "$HOLADO_TEST_SERVER_HOST" ]]; then
    HOLADO_TEST_SERVER_HOST=holado_test_server
fi

echo
echo "Running Test Server (docker name: ${HOLADO_TEST_SERVER_HOST})..."
echo "    port: ${HOLADO_TEST_SERVER_PORT}"
#echo "    NETWORK_DEF_COMMAND=${NETWORK_DEF_COMMAND}"
echo
docker run --rm --user root --name ${HOLADO_TEST_SERVER_HOST} \
    -v "${OUTPUT_DIR}":/output \
    -v "${RESOURCES_DIR}":/resources \
    -e HOLADO_OUTPUT_BASEDIR=/output \
    -e HOLADO_LOCAL_RESOURCES_BASEDIR=/resources \
    -e HOLADO_TEST_SERVER_PORT=${HOLADO_TEST_SERVER_PORT} \
    ${NETWORK_DEF_COMMAND} \
    -p ${HOLADO_TEST_SERVER_PORT}:${HOLADO_TEST_SERVER_PORT} \
    ${SERVER_IMAGE}

