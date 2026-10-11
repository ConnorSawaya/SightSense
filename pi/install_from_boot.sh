#!/bin/bash
# Runs once via systemd.run, before normal services. Never operates the motor.
set -eu
BOOT=/boot/firmware
STAGE="$BOOT/sightsense-update"
exec >> "$BOOT/sightsense-install.log" 2>&1
echo "SightSense install started $(date -Is)"

finish() {
    result=$?
    trap - EXIT
    if [ "$result" -ne 0 ]; then
        printf 'FAILED (exit %s): read sightsense-install.log\n' "$result" > "$BOOT/sightsense-install-status.txt"
    fi
    # Remove the temporary boot hook on both success and failure, so a failed
    # install still returns to a normal boot with SSH rather than a reboot loop.
    cp "$STAGE/normal-cmdline.txt" "$BOOT/cmdline.txt.next"
    mv -f "$BOOT/cmdline.txt.next" "$BOOT/cmdline.txt"
    sync
    exit "$result"
}
trap finish EXIT

cd "$STAGE"
sha256sum -c SHA256SUMS
id sightsense
BACKUP="/var/backups/sightsense/$(date +%Y%m%d-%H%M%S)"
install -d -m 700 "$BACKUP"
if [ -d /home/sightsense/SightSense/pi ]; then
    tar -czf "$BACKUP/pi.tar.gz" -C /home/sightsense/SightSense pi
fi
for unit in sightsense-cane.service sightsense-setup.service sightsense-spin-test.service; do
    if [ -e "/etc/systemd/system/$unit" ] || [ -L "/etc/systemd/system/$unit" ]; then
        cp -a "/etc/systemd/system/$unit" "$BACKUP/$unit"
    fi
done

# The previous full-power boot test must not drive the attached wheel.
systemctl disable --now sightsense-spin-test.service || true
ln -sfn /dev/null /etc/systemd/system/sightsense-spin-test.service

install -d -o sightsense -g sightsense /home/sightsense/SightSense/pi
for source in payload/pi/*; do
    [ -f "$source" ] || continue
    install -m 644 -o sightsense -g sightsense "$source" "/home/sightsense/SightSense/pi/$(basename "$source")"
done
install -m 644 payload/pi/sightsense-cane.service /etc/systemd/system/sightsense-cane.service
install -m 644 payload/pi/sightsense-setup.service /etc/systemd/system/sightsense-setup.service
if [ ! -f "$BOOT/sightsense.env" ]; then
    install -m 644 sightsense.env "$BOOT/sightsense.env"
fi
if getent group gpio >/dev/null; then
    usermod -a -G gpio sightsense
fi
if command -v tailscale >/dev/null; then
    systemctl enable tailscaled.service
else
    echo 'Tailscale is not installed; the 100.x GX10 address needs a route before commands can arrive.'
fi
systemctl daemon-reload
systemctl enable sightsense-cane.service
/usr/bin/python3 -m compileall -q /home/sightsense/SightSense/pi
printf 'INSTALLED: direct wheel mode. Normal boot follows; read journalctl -u sightsense-cane.\n' > "$BOOT/sightsense-install-status.txt"
echo "SightSense files installed $(date -Is). Dependencies checked on normal boot."
