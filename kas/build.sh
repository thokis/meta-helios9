#!/bin/bash

set -e

docker build --build-arg USER_ID=${UID} -t meta-helios9 -f Dockerfile.kas .
