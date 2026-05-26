from __future__ import annotations

import json
import shlex
import subprocess
import time

from .config import AppSettings
from .models import ManagedServiceStatus
from .models import ServiceControlResponse


class ServiceRuntimeManager:
    _ALLOWED_ACTIONS = {"status", "start", "stop", "restart"}

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def status(self) -> ServiceControlResponse:
        return self._run("status")

    def start(self) -> ServiceControlResponse:
        return self._queue("start")

    def stop(self) -> ServiceControlResponse:
        return self._queue("stop")

    def restart(self) -> ServiceControlResponse:
        return self._queue("restart")

    def _run(self, action: str) -> ServiceControlResponse:
        if action not in self._ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported service action: {action}")

        completed = subprocess.run(
            [str(self._settings.service_manager_script), action, "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        services = [ManagedServiceStatus.model_validate(item) for item in payload.get("services", [])]
        return ServiceControlResponse(
            action=action,
            success=bool(payload.get("success", False)),
            message=str(payload.get("message") or "服务操作已完成。"),
            services=services,
        )

    def _queue(self, action: str) -> ServiceControlResponse:
        if action not in self._ALLOWED_ACTIONS or action == "status":
            raise ValueError(f"Unsupported service action: {action}")

        unit_name = f"sage-faculty-twin-control-{action}-{int(time.time() * 1000)}"
        script = shlex.quote(str(self._settings.service_manager_script))
        command = f"sleep 1 && exec {script} {action}"
        subprocess.run(
            ["systemd-run", "--user", "--unit", unit_name, "/usr/bin/env", "bash", "-lc", command],
            check=True,
            capture_output=True,
            text=True,
        )
        snapshot = self.status()
        return ServiceControlResponse(
            action=action,
            success=True,
            message=f"Service action '{action}' has been queued.",
            services=snapshot.services,
        )