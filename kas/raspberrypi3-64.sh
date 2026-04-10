#!/bin/bash

set -e

docker run \
    --rm \
    -it \
    -e "SSH_AUTH_SOCK=/ssh-agent" \
    -v "${SSH_AUTH_SOCK}:/ssh-agent" \
    -v "${HOME}/.ssh/known_hosts:/home/kas/.ssh/known_hosts:ro" \
    -v "$(pwd)/..:/home/kas/meta-helios9:z" \
    -w /home/kas/meta-helios9/kas/yocto \
    meta-helios9 uv run kas build raspberrypi3-64.yaml
