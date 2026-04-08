#!/bin/bash

set -e

docker build --build-arg USER_ID=${UID} -t yocto.kas -f Dockerfile.kas .
