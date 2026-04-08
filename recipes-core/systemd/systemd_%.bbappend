FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " \
    file://journald-persistent.conf \
    file://repart.d-root.conf \
    file://resolved-mdns.conf \
"

PACKAGECONFIG:remove = " \
    networkd \
"

PACKAGECONFIG:append = " \
    nss-resolve \
    openssl \
    repart \
    resolved \
    timesyncd \
"

RRECOMMENDS:${PN}-resolved += "libnss-resolve"

do_install:append() {
    # Persistent journald logging
    install -D -m 0644 ${WORKDIR}/journald-persistent.conf ${D}${systemd_unitdir}/journald.conf.d/10-persistent.conf

    # Install repart config
    install -D -m 0644 ${WORKDIR}/repart.d-root.conf ${D}${libdir}/repart.d/10-root.conf

    # Enable mDNS/LLMNR configuration
    install -D -m 0644 ${WORKDIR}/resolved-mdns.conf ${D}${systemd_unitdir}/resolved.conf.d/10-mdns.conf
}

FILES:${PN}:append = " \
    ${libdir}/repart.d/10-root.conf \
    ${systemd_unitdir}/journald.conf.d/10-persistent.conf \
    ${systemd_unitdir}/resolved.conf.d/10-mdns.conf \
"
