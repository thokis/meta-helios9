SUMMARY = "helios9 image with WWAN connectivity"
DESCRIPTION = "helios9 base image extended with cellular modem support"
LICENSE = "CLOSED"

require helios9-image-minimal.bb

IMAGE_INSTALL:append = " \
    modemmanager \
    networkmanager-wwan \
    usb-modeswitch \
    usb-modeswitch-data \
"
