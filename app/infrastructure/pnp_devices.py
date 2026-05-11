from __future__ import annotations

import json
import subprocess

from app.models.entities import OperationResult


USB_PNP_QUERY = r"""
$ErrorActionPreference = 'Stop'
$devices = Get-PnpDevice -PresentOnly | Where-Object {
    $_.InstanceId -like 'USB\*' -or
    $_.InstanceId -like 'USBSTOR\*' -or
    $_.InstanceId -like 'HID\VID_*'
} | Where-Object {
    $_.InstanceId -notlike 'ROOT\*' -and
    $_.Status -eq 'OK'
} | Select-Object InstanceId, FriendlyName, Class, Status
$devices | ConvertTo-Json -Compress
"""


class PnpDeviceManager:
    def _run_powershell(self, script: str, args: list[str] | None = None, timeout: int = 90) -> OperationResult:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
            *(args or []),
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            return OperationResult(False, "unsupported", "PowerShell est introuvable sur ce poste.")
        except subprocess.TimeoutExpired:
            return OperationResult(False, "timeout", "Commande PnP trop longue.")
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "Commande PnP echouee.").strip()
            return OperationResult(False, "error", message, {"returncode": completed.returncode})
        return OperationResult(True, "ok", "Commande PnP terminee.", {"stdout": completed.stdout.strip()})

    def list_lockdown_candidates(self) -> OperationResult:
        result = self._run_powershell(USB_PNP_QUERY, timeout=60)
        if not result.success:
            return result
        raw = str(result.details.get("stdout") or "").strip()
        if not raw:
            return OperationResult(True, "empty", "Aucun peripherique USB actif detecte.", {"devices": []})
        try:
            parsed = json.loads(raw)
        except ValueError as exc:
            return OperationResult(False, "parse_error", f"Lecture PnP illisible: {exc}", {"raw": raw})
        items = parsed if isinstance(parsed, list) else [parsed]
        devices = []
        for item in items:
            if not isinstance(item, dict):
                continue
            instance_id = str(item.get("InstanceId") or "").strip()
            if not instance_id:
                continue
            devices.append(
                {
                    "instance_id": instance_id,
                    "name": str(item.get("FriendlyName") or instance_id),
                    "class": str(item.get("Class") or ""),
                    "status": str(item.get("Status") or ""),
                }
            )
        devices.sort(key=lambda device: self._disable_priority(str(device["instance_id"])))
        return OperationResult(True, "ok", f"{len(devices)} peripheriques USB actifs detectes.", {"devices": devices})

    def disable_devices(self, instance_ids: list[str]) -> OperationResult:
        return self._toggle_devices(instance_ids, enable=False)

    def enable_devices(self, instance_ids: list[str]) -> OperationResult:
        return self._toggle_devices(instance_ids, enable=True)

    def _toggle_devices(self, instance_ids: list[str], *, enable: bool) -> OperationResult:
        ids = [str(instance_id) for instance_id in instance_ids if str(instance_id).strip()]
        if not ids:
            return OperationResult(True, "empty", "Aucun peripherique PnP a modifier.", {"changed": [], "failed": {}})
        batch = self._toggle_devices_with_powershell(ids, enable=enable)
        changed = batch.details.get("changed", []) if batch.details else []
        if isinstance(changed, str):
            changed = [changed]
        failed = batch.details.get("failed", {}) if batch.details else {}
        if not isinstance(failed, dict):
            failed = {}
        pnputil_action = "/enable-device" if enable else "/disable-device"
        for instance_id in list(failed):
            result = self._run_pnputil([pnputil_action, instance_id], timeout=45)
            if result.success:
                if instance_id not in changed:
                    changed.append(instance_id)
                failed.pop(instance_id, None)
            else:
                failed[instance_id] = result.message
        if failed:
            return OperationResult(
                False,
                "partial",
                "Certains peripheriques USB PnP n'ont pas pu etre modifies.",
                {"changed": changed, "failed": failed},
            )
        status = "enabled" if enable else "disabled"
        message = "Peripheriques USB PnP restaures." if enable else "Peripheriques USB PnP desactives."
        return OperationResult(True, status, message, {"changed": changed, "failed": {}})

    def apply_policy_refresh(self) -> OperationResult:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            subprocess.Popen(
                ["gpupdate.exe", "/target:computer", "/force"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            return OperationResult(True, "started", "Rafraichissement des policies Windows lance en arriere-plan.")
        except FileNotFoundError:
            return OperationResult(False, "unsupported", "gpupdate.exe est introuvable sur ce poste.")
        except OSError as exc:
            return OperationResult(False, "error", f"Impossible de lancer gpupdate: {exc}")

    def disable_usb_device_ids(self) -> OperationResult:
        device_ids = ["USB\\Class_03", "USB\\Class_08", "USB\\Class_09", "USB\\Class_E0", "USB\\Class_FF"]
        changed = []
        failed = {}
        for device_id in device_ids:
            result = self._run_pnputil(["/disable-device", "/deviceid", device_id], timeout=60)
            if result.success:
                changed.append(device_id)
            else:
                failed[device_id] = result.message
        status = "disabled" if not failed else "partial"
        return OperationResult(not failed, status, "Classes USB PnP traitees.", {"changed": changed, "failed": failed})

    def _toggle_devices_with_powershell(self, instance_ids: list[str], *, enable: bool) -> OperationResult:
        action = "Enable-PnpDevice" if enable else "Disable-PnpDevice"
        payload = json.dumps(instance_ids)
        script = rf"""
$ErrorActionPreference = 'Continue'
$ids = ConvertFrom-Json $args[0]
$changed = @()
$failed = @{{}}
foreach ($id in $ids) {{
    try {{
        {action} -InstanceId $id -Confirm:$false -ErrorAction Stop
        $changed += $id
    }} catch {{
        $failed[$id] = $_.Exception.Message
    }}
}}
[PSCustomObject]@{{ changed = $changed; failed = $failed }} | ConvertTo-Json -Compress
"""
        result = self._run_powershell(script, [payload], timeout=max(90, len(instance_ids) * 8))
        if not result.success:
            return result
        raw = str(result.details.get("stdout") or "").strip()
        try:
            parsed = json.loads(raw) if raw else {}
        except ValueError as exc:
            return OperationResult(False, "parse_error", f"Retour PnP illisible: {exc}", {"raw": raw})
        changed = parsed.get("changed") or []
        if isinstance(changed, str):
            changed = [changed]
        failed = parsed.get("failed") or {}
        return OperationResult(not failed, "ok" if not failed else "partial", "PowerShell PnP termine.", {"changed": changed, "failed": failed})

    def _run_pnputil(self, args: list[str], timeout: int = 60) -> OperationResult:
        return self._run_process(["pnputil.exe", *args], timeout=timeout)

    def _run_process(self, command: list[str], timeout: int = 60) -> OperationResult:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            return OperationResult(False, "unsupported", f"{command[0]} est introuvable sur ce poste.")
        except subprocess.TimeoutExpired:
            return OperationResult(False, "timeout", f"Commande trop longue: {command[0]}.")
        output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip())
        if completed.returncode != 0:
            return OperationResult(False, "error", output or f"{command[0]} a echoue.", {"returncode": completed.returncode})
        return OperationResult(True, "ok", output or f"{command[0]} termine.", {"returncode": completed.returncode, "output": output})

    @staticmethod
    def _disable_priority(instance_id: str) -> int:
        upper = instance_id.upper()
        if upper.startswith("HID\\"):
            return 0
        if upper.startswith("USBSTOR\\"):
            return 1
        if "ROOT_HUB" in upper or upper.startswith("USB\\ROOT"):
            return 3
        return 2
