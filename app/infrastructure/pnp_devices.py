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
        action = "Enable-PnpDevice" if enable else "Disable-PnpDevice"
        payload = json.dumps(ids)
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
        result = self._run_powershell(script, [payload], timeout=max(90, len(ids) * 8))
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
