#!/bin/bash

set -e

docker run \
    --rm \
    --user "$(id -u):$(id -g)" \
    -it \
    -e "SSH_AUTH_SOCK=/ssh-agent" \
    -v "${SSH_AUTH_SOCK}:/ssh-agent" \
    -v "${HOME}/.ssh/known_hosts:/home/kas/.ssh/known_hosts:ro" \
    -v "$(pwd)/yocto:/home/kas/yocto:z" \
    -v "/home/thomaskiss/.local/share/kas-builder/kas.yaml:/home/kas/yocto/.config.yaml:ro" \
    -w /home/kas/yocto \
    yocto.kas uv run kas build rpi3.yaml
