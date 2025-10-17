#!/usr/bin/env bash

set -eux

DOCKER_DIR=resources/docker_dev
REQUIREMENTS_FILE=${DOCKER_DIR}/requirements.txt

uv export --no-editable --no-emit-project --no-hashes\
    --extra postgres --extra uvicorn --extra cache  > $REQUIREMENTS_FILE

sed -i '/argon2-cffi-bindings==21.2.0/d' $REQUIREMENTS_FILE
sed -i '/.*whl/d' $REQUIREMENTS_FILE

for file in $(ls ${DOCKER_DIR}/*.whl); do
    rm $file
done

for file in $(ls *.whl); do
    cp $file $DOCKER_DIR
done

docker compose build
