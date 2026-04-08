SUMMARY = "helios9 minimal base image"
DESCRIPTION = "A minimal embedded Linux image for the helios9 platform"
LICENSE = "CLOSED"

inherit core-image

IMAGE_INSTALL:append = " \
    e2fsprogs-resize2fs \
    util-linux \
    \
    networkmanager \
    \
    openssh-sftp-server \
"

IMAGE_FEATURES:append = " ssh-server-dropbear"
