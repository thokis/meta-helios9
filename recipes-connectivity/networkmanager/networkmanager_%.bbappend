FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " \
    git://github.com/NetworkManager/NetworkManager.git;protocol=https;branch=nm-1-56 \
    file://conf.d/disable-hostname-mode.conf \
    file://conf.d/enable-mdns.conf \
    file://conf.d/enable-systemd-resolved.conf \
    file://system-connections/wwan0.nmconnection \
"

SRC_URI:remove = " \
    git://github.com/NetworkManager/NetworkManager.git;protocol=https;branch=nm-1-56;tag=${PV} \
"

PACKAGECONFIG:append = " \
    modemmanager \
"

PACKAGECONFIG:remove = " \
    bluez5 \
    dnsmasq \
    ifupdown \
    polkit \
    readline \
    vala \
    wifi \
"

do_install:append() {
    install -D -m 0644 ${WORKDIR}/conf.d/disable-hostname-mode.conf ${D}${nonarch_libdir}/NetworkManager/conf.d/10-disable-hostname-mode.conf
    install -D -m 0644 ${WORKDIR}/conf.d/enable-mdns.conf ${D}${nonarch_libdir}/NetworkManager/conf.d/10-enable-mdns.conf
    install -D -m 0644 ${WORKDIR}/conf.d/enable-systemd-resolved.conf ${D}${nonarch_libdir}/NetworkManager/conf.d/10-enable-systemd-resolved.conf
    install -D -m 0600 ${WORKDIR}/system-connections/wwan0.nmconnection ${D}${nonarch_libdir}/NetworkManager/system-connections/wwan0.nmconnection
}
