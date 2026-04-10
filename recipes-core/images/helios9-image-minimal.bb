SUMMARY = "helios9 minimal base image"
DESCRIPTION = "A minimal embedded Linux image for the helios9 platform"
LICENSE = "CLOSED"

inherit core-image

IMAGE_INSTALL:append = " \
    coreutils \
    e2fsprogs-resize2fs \
    networkmanager \
    openssh-sftp-server \
    procps \
    tzdata \
    tzdata-europe \
    usbutils \
    util-linux \
    \
    kernel-modules \
"

IMAGE_FEATURES:append = " ssh-server-dropbear"
