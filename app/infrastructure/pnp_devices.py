from __future__ import annotations

import json
import subprocess

from app.models.entities import OperationResult


USB_PNP_QUERY = r"""
$ErrorActionPreference = 'Stop'
$devices = Get-PnpDevice -PresentOnly | Where-Object {
    $_.Class -eq 'USB' -or
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
        changed = []
        failed = {}
        pnputil_action = "/enable-device" if enable else "/disable-device"
        pnputil_extra = [] if enable else ["/force"]
        for instance_id in ids:
            result = self._run_pnputil([pnputil_action, instance_id, *pnputil_extra], timeout=45)
            if result.success:
                if instance_id not in changed:
                    changed.append(instance_id)
            else:
                failed[instance_id] = result.message
        if failed:
            fallback = self._toggle_devices_with_powershell(list(failed), enable=enable)
            fallback_changed = fallback.details.get("changed", []) if fallback.details else []
            if isinstance(fallback_changed, str):
                fallback_changed = [fallback_changed]
            for instance_id in fallback_changed:
                if instance_id not in changed:
                    changed.append(instance_id)
                failed.pop(instance_id, None)
            fallback_failed = fallback.details.get("failed", {}) if fallback.details else {}
            if isinstance(fallback_failed, dict):
                failed.update({str(key): str(value) for key, value in fallback_failed.items() if str(key) not in changed})
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
        return self._run_process(["gpupdate.exe", "/target:computer", "/force"], timeout=90)

    def repair_usb_stack(self) -> OperationResult:
        script = r"""
$ErrorActionPreference = 'Continue'
$classes = @('USB', 'USBDevice', 'HIDClass', 'Mouse', 'Keyboard', 'SCSIAdapter', 'DiskDrive', 'WPD')
$devices = Get-PnpDevice | Where-Object {
    $classes -contains $_.Class -and (
        $_.Class -eq 'USB' -or
        $_.InstanceId -like 'USB\*' -or
        $_.InstanceId -like 'USBSTOR\*' -or
        $_.InstanceId -like 'HID\VID_*' -or
        $_.FriendlyName -like '*USB*'
    )
}
$changed = @()
$failed = @{}
foreach ($device in $devices) {
    try {
        Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction Stop
        $changed += $device.InstanceId
    } catch {
        $failed[$device.InstanceId] = $_.Exception.Message
    }
}
[PSCustomObject]@{ changed = $changed; failed = $failed } | ConvertTo-Json -Compress
"""
        result = self._run_powershell(script, timeout=120)
        if not result.success:
            return result
        raw = str(result.details.get("stdout") or "").strip()
        try:
            parsed = json.loads(raw) if raw else {}
        except ValueError as exc:
            return OperationResult(False, "parse_error", f"Retour reparation USB illisible: {exc}", {"raw": raw})
        changed = parsed.get("changed") or []
        if isinstance(changed, str):
            changed = [changed]
        failed = parsed.get("failed") or {}
        if not isinstance(failed, dict):
            failed = {}
        scan = self._run_pnputil(["/scan-devices"], timeout=90)
        return OperationResult(
            True,
            "repaired" if not failed else "partial",
            "Reparation de la pile USB demandee.",
            {"changed": changed, "failed": failed, "scan": scan.details, "scan_status": scan.status},
        )

    def disable_usb_device_ids(self) -> OperationResult:
        device_ids = ["USB\\Class_03", "USB\\Class_08", "USB\\Class_09", "USB\\Class_E0", "USB\\Class_FF"]
        changed = []
        failed = {}
        for device_id in device_ids:
            result = self._run_pnputil(["/disable-device", "/deviceid", device_id, "/force"], timeout=60)
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
            if "already enabled" in output.lower():
                return OperationResult(True, "ok", output, {"returncode": completed.returncode, "output": output})
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
