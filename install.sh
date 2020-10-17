#!/usr/bin/env bash

cd $(dirname "$(readlink -f "$0")")

sudoecho() {
    echo sudo "$@"
    sudo "$@" || exit 1
}

echo "# Installing udpproxy.py"
sudoecho cp udpproxy.py /usr/bin/udpproxy.py
for fn in udpproxy*.service; do
    echo
    echo "# Installing ${fn}:"
    svc_dest="/etc/systemd/system/${fn}"
    if [ -f "$svc_dest" ]; then
        sudoecho systemctl stop "$fn"
    fi
    sudoecho cp "./$fn" "$svc_dest"
    sudoecho systemctl enable "$fn"
    sudoecho systemctl reload-or-restart "$fn"
    sudoecho systemctl --no-pager status "$fn"
done

