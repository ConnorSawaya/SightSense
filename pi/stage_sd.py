"""Stage the Pi update on an existing Raspberry Pi OS boot partition.

Windows can read bootfs but not the Linux partition. This copies a verified
payload and installs it on the next boot, without formatting either partition.
The caller must verify the physical disk and supply its root PARTUUID.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def write_text(path, text):
    temporary = path.with_name(path.name + ".next")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def normal_cmdline(boot, expected_partuuid):
    current = (boot / "cmdline.txt").read_text(encoding="utf-8-sig").strip()
    if not current:
        current = (boot / "cmdline.txt.bak").read_text(encoding="utf-8-sig").strip()
    if len(current.splitlines()) != 1:
        raise ValueError("kernel command line must have one nonempty line")
    match = re.search(r"(?:^|\s)root=PARTUUID=([^\s]+)", current)
    if not match or match.group(1).lower() != expected_partuuid.lower():
        raise ValueError("boot settings do not match the verified SD root PARTUUID")
    current = re.sub(r'\s+systemd\.(?:run(?:_success_action|_failure_action)?|unit)=(?:"[^"]*"|\S+)', "", current)
    return current + "\n"


def remove_boot_spin(user_data):
    """Remove only this project's old boot bench test, preserving login/Wi-Fi settings."""
    marker = re.search(r"(?m)^write_files:[^\n]*\n", user_data)
    if marker:
        following = re.search(r"(?m)^[A-Za-z_][A-Za-z0-9_-]*:", user_data[marker.end():])
        end = marker.end() + following.start() if following else len(user_data)
        block = user_data[marker.end():end]
        for path in ("/opt/sightsense/spin_test.py", "/etc/systemd/system/sightsense-spin-test.service"):
            pattern = r"(?ms)^- path: " + re.escape(path) + r"\s*\n.*?(?=^- path:|\Z)"
            block = re.sub(pattern, "", block)
        replacement = user_data[marker.start():marker.end()] + block if block.strip() else ""
        user_data = user_data[:marker.start()] + replacement + user_data[end:]
    user_data = re.sub(r"(?m)^\s*-\s*\[\s*systemctl,\s*(?:enable|start),[^\n]*sightsense-spin-test\.service[^\n]*\]\s*\n", "", user_data)
    return user_data


def stage(boot, backup, expected_partuuid, gx10, source=ROOT / "pi"):
    boot, backup, source = Path(boot).resolve(), Path(backup).resolve(), Path(source).resolve()
    if not re.fullmatch(r"[A-Za-z0-9.-]+:[0-9]{1,5}", gx10):
        raise ValueError("GX10 must be host:port, without http:// or a path")
    if not 1 <= int(gx10.rsplit(":", 1)[1]) <= 65535:
        raise ValueError("invalid command port")
    issue = (boot / "issue.txt").read_text()
    if "Raspberry Pi" not in issue or not (boot / "config.txt").is_file():
        raise ValueError("target is not an existing Raspberry Pi OS boot partition")
    if not any((boot / f).is_file() for f in ("kernel_2712.img", "kernel8.img")):
        raise ValueError("Pi kernel missing from target")
    if backup == boot or boot in backup.parents:
        raise ValueError("backup must be outside the SD card")
    clean = normal_cmdline(boot, expected_partuuid)
    if backup.exists():
        raise ValueError("backup destination already exists")
    backup.mkdir(parents=True)
    for item in boot.iterdir():
        if item.name == "System Volume Information":
            continue
        if item.is_dir():
            shutil.copytree(item, backup / item.name)
        else:
            shutil.copy2(item, backup / item.name)

    target = boot / "sightsense-update"
    if target.exists():
        raise ValueError("an update is already staged; inspect it before replacing it")
    payload = target / "payload" / "pi"
    payload.mkdir(parents=True)
    for item in source.iterdir():
        if item.is_file() and item.suffix in (".py", ".md", ".service", ".sh", ".example"):
            text = item.read_text(encoding="utf-8-sig")
            write_text(payload / item.name, text.replace("\r\n", "\n"))
    write_text(target / "install.sh", (source / "install_from_boot.sh").read_text())
    write_text(target / "normal-cmdline.txt", clean)
    environment = f"SIGHTSENSE_GX10={gx10}\nSIGHTSENSE_CANE_ARGS=--wheel-drive --duty 0.25 --rated-rpm 120\n"
    write_text(target / "sightsense.env", environment)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    release = {"source_commit": commit, "staged_utc": datetime.now(timezone.utc).isoformat(),
               "mode": "wheel-drive", "gx10": gx10, "duty": 0.25, "rated_rpm": 120,
               "rpm_estimate": 30, "rpm_measured": False, "root_partuuid": expected_partuuid}
    write_text(target / "release.json", json.dumps(release, indent=2) + "\n")
    manifest = {}
    for file in sorted(target.rglob("*")):
        if file.is_file():
            manifest[file.relative_to(target).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    write_text(target / "SHA256SUMS", "".join(f"{digest}  {name}\n" for name, digest in manifest.items()))
    for name, digest in manifest.items():
        if hashlib.sha256((target / name).read_bytes()).hexdigest() != digest:
            raise OSError(f"SD readback mismatch: {name}")

    # Disable the old full-power boot test before activating the new boot hook.
    spin = boot / "spin-test-enabled"
    if spin.exists():
        spin.rename(boot / "spin-test-disabled-by-sightsense-update")
    user_data = boot / "user-data"
    if user_data.is_file():
        write_text(user_data, remove_boot_spin(user_data.read_text(encoding="utf-8-sig")))
    config = (boot / "config.txt").read_text(encoding="utf-8-sig").rstrip()
    config += "\n\n# SightSense motor outputs low during Pi 5 boot\n[pi5]\ngpio=18,23,24,25=op,dl,pd\n[all]\n"
    write_text(boot / "config.txt", config)
    write_text(boot / "sightsense.env", environment)
    write_text(boot / "sightsense-install-status.txt", "STAGED: insert in Pi; installer runs once and reboots.\n")
    hook = ' systemd.run="/bin/bash /boot/firmware/sightsense-update/install.sh" systemd.run_success_action=reboot systemd.run_failure_action=reboot'
    write_text(boot / "cmdline.txt", clean.strip() + hook + "\n")
    if (boot / "cmdline.txt").read_text().count("\n") != 1:
        raise OSError("boot command line readback failed")
    if (boot / "config.txt").read_text() != config or (boot / "sightsense.env").read_text() != environment:
        raise OSError("boot configuration readback failed")
    return {"boot": str(boot), "backup": str(backup), "files_verified": len(manifest), **release}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--expected-root-partuuid", required=True)
    parser.add_argument("--gx10", required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.boot, args.backup, args.expected_root_partuuid, args.gx10), indent=2))
