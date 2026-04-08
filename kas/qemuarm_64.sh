#!/bin/bash

set -e

docker run \
    --rm \
    -it \
    -e "SSH_AUTH_SOCK=/ssh-agent" \
    -v "${SSH_AUTH_SOCK}:/ssh-agent" \
    -v "${HOME}/.ssh/known_hosts:/home/kas/.ssh/known_hosts:ro" \
    -v "$(pwd)/yocto:/home/kas/yocto:z" \
    -w /home/kas/yocto \
    yocto.kas uv run kas build qemuarm_64.yaml

docker run \
    --network=host \
    --privileged \
    --rm \
    -it \
    -e "SSH_AUTH_SOCK=/ssh-agent" \
    -v "${SSH_AUTH_SOCK}:/ssh-agent" \
    -v "${HOME}/.ssh/known_hosts:/home/kas/.ssh/known_hosts:ro" \
    -v "$(pwd)/yocto:/home/kas/yocto:z" \
    -w /home/kas/yocto \
    yocto.kas uv run kas shell qemuarm_64.yaml -c 'runqemu nographic slirp qemuparams="-device usb-host,vendorid=0x2c7c,productid=0x6002,bus=usb-bus.0,id=modem"'
