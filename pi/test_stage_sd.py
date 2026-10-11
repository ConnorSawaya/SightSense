"""SD staging against temporary files, never a real disk."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from stage_sd import normal_cmdline, remove_boot_spin, stage


USER_DATA = '''#cloud-config
hostname: sightsense
user:
  name: sightsense
  password: example-only
write_files:
- path: /opt/sightsense/spin_test.py
  encoding: b64
  content: example-bench-code
- path: /etc/systemd/system/sightsense-spin-test.service
  content: example-bench-unit
- path: /etc/example-kept
  content: keep-me
runcmd:
  - [ systemctl, enable, --now, ssh ]
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, sightsense-spin-test.service ]
  - [ systemctl, start, --no-block, sightsense-spin-test.service ]
'''


class Staging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.boot = self.root / "bootfs"
        self.boot.mkdir()
        for name, text in {"issue.txt": "Raspberry Pi reference 2026-10-06",
                           "config.txt": "arm_64bit=1\n", "kernel_2712.img": "example-kernel",
                           "cmdline.txt": "", "cmdline.txt.bak": "console=tty1 root=PARTUUID=12345678-02 rootfstype=ext4 rootwait\n",
                           "user-data": USER_DATA, "network-config": "example-network-unchanged\n",
                           "meta-data": "instance-id: keep-existing\n", "spin-test-enabled": "bench-only"}.items():
            (self.boot / name).write_text(text)

    def test_empty_cmdline_is_recovered_only_from_matching_backup(self):
        self.assertIn("root=PARTUUID=12345678-02", normal_cmdline(self.boot, "12345678-02"))
        with self.assertRaises(ValueError):
            normal_cmdline(self.boot, "ffffffff-02")

    def test_spin_removal_preserves_unrelated_configuration(self):
        updated = remove_boot_spin(USER_DATA)
        self.assertNotIn("sightsense-spin-test", updated)
        self.assertNotIn("/opt/sightsense/spin_test.py", updated)
        self.assertIn("password: example-only", updated)
        self.assertIn("/etc/example-kept", updated)
        self.assertIn("systemctl, enable, --now, ssh", updated)

    def test_empty_write_files_section_is_removed(self):
        data = USER_DATA.replace("- path: /etc/example-kept\n  content: keep-me\n", "")
        updated = remove_boot_spin(data)
        self.assertNotIn("write_files:", updated)
        self.assertIn("runcmd:", updated)

    def test_staging_backup_manifest_boot_hook_and_existing_network(self):
        backup = self.root / "backup"
        result = stage(self.boot, backup, "12345678-02", "100.108.5.67:8766")
        self.assertGreater(result["files_verified"], 10)
        self.assertEqual((backup / "cmdline.txt").read_text(), "")
        self.assertEqual((backup / "user-data").read_text(), USER_DATA)
        self.assertEqual((self.boot / "network-config").read_text(), (backup / "network-config").read_text())
        self.assertEqual((self.boot / "meta-data").read_text(), (backup / "meta-data").read_text())
        self.assertEqual((self.boot / "kernel_2712.img").read_bytes(), (backup / "kernel_2712.img").read_bytes())
        self.assertFalse((self.boot / "spin-test-enabled").exists())
        self.assertIn("gpio=18,23,24,25=op,dl,pd", (self.boot / "config.txt").read_text())
        self.assertIn("arm_64bit=1", (self.boot / "config.txt").read_text())
        self.assertIn("--wheel-drive", (self.boot / "sightsense.env").read_text())
        self.assertEqual((self.boot / "cmdline.txt").read_text().count("\n"), 1)
        self.assertIn('systemd.run="/bin/bash ', (self.boot / "cmdline.txt").read_text())
        self.assertIn("systemd.unit=kernel-command-line.target", (self.boot / "cmdline.txt").read_text())
        target = self.boot / "sightsense-update"
        for line in (target / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), digest)

    def test_wrong_disk_is_rejected_before_writing(self):
        with self.assertRaises(ValueError):
            stage(self.boot, self.root / "backup", "ffffffff-02", "100.108.5.67:8766")
        self.assertFalse((self.boot / "sightsense-update").exists())

    def test_private_wifi_profile_is_copied_and_hashed_without_logging_secret(self):
        profile = self.root / "private.nmconnection"
        text = "[connection]\nid=example\ntype=wifi\n[wifi]\nssid=example\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=example$only%\n"
        profile.write_text(text)
        result = stage(self.boot, self.root / "backup", "12345678-02", "100.108.5.67:8766",
                       wifi_profile=profile)
        target = self.boot / "sightsense-update"
        self.assertEqual((target / "wifi.nmconnection").read_text(), text)
        self.assertIn(hashlib.sha256(text.encode()).hexdigest() + "  wifi.nmconnection",
                      (target / "SHA256SUMS").read_text())
        self.assertNotIn("example$only%", json.dumps(result))
        self.assertNotIn("example$only%", (target / "release.json").read_text())
        self.assertEqual((self.boot / "network-config").read_text(), "example-network-unchanged\n")

    def test_further_wifi_profiles_are_staged_beside_the_first_as_fallbacks(self):
        texts = [f"[connection]\nid=net{n}\n[wifi-security]\npsk=secret{n}\n" for n in (1, 2, 3)]
        files = []
        for n, text in enumerate(texts, 1):
            files.append(self.root / f"net{n}.nmconnection")
            files[-1].write_text(text)
        result = stage(self.boot, self.root / "backup", "12345678-02", "100.108.5.67:8766",
                       wifi_profile=files[0], more_wifi_profiles=files[1:])
        target = self.boot / "sightsense-update"
        self.assertEqual((target / "wifi.nmconnection").read_text(), texts[0])
        self.assertEqual((target / "wifi-2.nmconnection").read_text(), texts[1])
        self.assertEqual((target / "wifi-3.nmconnection").read_text(), texts[2])
        sums = (target / "SHA256SUMS").read_text()
        self.assertIn("  wifi-2.nmconnection", sums)
        self.assertIn("  wifi-3.nmconnection", sums)
        self.assertNotIn("secret", json.dumps(result))

    def test_a_further_wifi_profile_needs_a_first_one(self):
        extra = self.root / "extra.nmconnection"
        extra.write_text("[connection]\nid=extra\n")
        with self.assertRaises(ValueError):
            stage(self.boot, self.root / "backup", "12345678-02", "100.108.5.67:8766", more_wifi_profiles=[extra])
        self.assertFalse((self.boot / "sightsense-update").exists())

    def test_staging_twice_does_not_repeat_the_boot_settings(self):
        stage(self.boot, self.root / "backup", "12345678-02", "100.108.5.67:8766")
        (self.boot / "sightsense-update").rename(self.root / "previous-update")  # as after an install, moved aside
        (self.boot / "cmdline.txt").write_text("console=tty1 root=PARTUUID=12345678-02 rootfstype=ext4 rootwait\n")  # as the installer leaves it
        stage(self.boot, self.root / "backup2", "12345678-02", "100.108.5.67:8766")
        self.assertEqual((self.boot / "config.txt").read_text().count("gpio=18,23,24,25=op,dl,pd"), 1)

    def test_the_installer_installs_further_profiles(self):
        script = (Path(__file__).parent / "install_from_boot.sh").read_text()
        self.assertIn('for extra in "$STAGE"/wifi-[0-9]*.nmconnection; do', script)
        self.assertIn('install -D -m 600 -o root -g root "$extra"', script)

    def test_missing_wifi_profile_fails_before_card_or_backup_changes(self):
        backup = self.root / "backup"
        with self.assertRaises(FileNotFoundError):
            stage(self.boot, backup, "12345678-02", "100.108.5.67:8766",
                  wifi_profile=self.root / "missing.nmconnection")
        self.assertFalse(backup.exists())
        self.assertFalse((self.boot / "sightsense-update").exists())

    def test_invalid_address_is_rejected(self):
        for address in ("http://100.108.5.67:8000/", "host:0", "host:65536", "host;touch-file:8766"):
            with self.assertRaises(ValueError):
                stage(self.boot, self.root / "backup", "12345678-02", address)

    def test_old_boot_hook_is_replaced_without_duplication(self):
        (self.boot / "cmdline.txt").write_text('root=PARTUUID=12345678-02 rootwait systemd.unit=kernel-command-line.target systemd.run="/bin/bash old.sh" systemd.run_success_action=reboot\n')
        clean = normal_cmdline(self.boot, "12345678-02")
        self.assertEqual(clean, "root=PARTUUID=12345678-02 rootwait\n")
