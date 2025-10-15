from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import httpx

from .models import (
    InstanceRecord,
    InstanceTypeSpecs,
    InstanceTypeSummary,
    RegionInfo,
    SshKeyRecord,
)

API_PREFIX = "/api/v1"


class LammyApiError(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.suggestion = suggestion

    def __str__(self) -> str:
        base = f"[{self.status_code}] {self.code}: {self.message}"
        if self.suggestion:
            base = f"{base} ({self.suggestion})"
        return base


class LammyNetworkError(RuntimeError):
    pass


@dataclass
class _ApiErrorPayload:
    code: str
    message: str
    suggestion: Optional[str] = None


class LammyClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://cloud.lambda.ai",
        *,
        timeout: float = 15.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must be provided")
        normalized = base_url.rstrip("/")
        api_base = f"{normalized}{API_PREFIX}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "lammy-cli/0.1.0",
        }
        self._client = httpx.Client(
            base_url=api_base, headers=headers, timeout=timeout, follow_redirects=True
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "LammyClient":
        return self

    def __exit__(self, *exc: object) -> None:  # type: ignore[override]
        self.close()

    def list_instances(self) -> List[InstanceRecord]:
        payload = self._request("GET", "/instances")
        records = [_parse_instance(item) for item in payload or []]
        records.sort(key=lambda inst: (inst.region.name, inst.preferred_display_name()))
        return records

    def get_instance(self, instance_id: str) -> InstanceRecord:
        payload = self._request("GET", f"/instances/{instance_id}")
        return _parse_instance(payload)

    def list_instance_types(self) -> List[InstanceTypeSummary]:
        payload = self._request("GET", "/instance-types")
        items = []
        if isinstance(payload, dict):
            for _, entry in payload.items():
                items.append(_parse_instance_type_entry(entry))
        items.sort(key=lambda item: (item.price_per_hour or 0.0, item.name))
        return items

    def list_ssh_keys(self) -> List[SshKeyRecord]:
        payload = self._request("GET", "/ssh-keys")
        records = []
        for item in payload or []:
            records.append(
                SshKeyRecord(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    public_key=item.get("public_key", ""),
                )
            )
        records.sort(key=lambda item: item.name)
        return records

    def launch_instance(
        self,
        *,
        region_name: str,
        instance_type_name: str,
        ssh_key_names: Sequence[str],
        name: Optional[str] = None,
        hostname: Optional[str] = None,
        image: Optional[dict] = None,
        tags: Optional[Sequence[dict]] = None,
        file_system_names: Optional[Sequence[str]] = None,
        user_data: Optional[str] = None,
    ) -> List[str]:
        if not ssh_key_names:
            raise ValueError("At least one SSH key name must be provided")
        body = {
            "region_name": region_name,
            "instance_type_name": instance_type_name,
            "ssh_key_names": list(ssh_key_names),
        }
        if name:
            body["name"] = name
        if hostname:
            body["hostname"] = hostname
        if image:
            body["image"] = image
        if tags:
            body["tags"] = list(tags)
        if file_system_names:
            body["file_system_names"] = list(file_system_names)
        if user_data:
            body["user_data"] = user_data
        payload = self._request("POST", "/instance-operations/launch", json=body)
        return payload.get("instance_ids", []) if isinstance(payload, dict) else []

    def restart_instances(self, instance_ids: Iterable[str]) -> List[InstanceRecord]:
        ids = [item for item in instance_ids if item]
        if not ids:
            return []
        payload = self._request(
            "POST", "/instance-operations/restart", json={"instance_ids": ids}
        )
        entries = payload.get("restarted_instances", []) if isinstance(payload, dict) else []
        return [_parse_instance(item) for item in entries]

    def terminate_instances(self, instance_ids: Iterable[str]) -> List[InstanceRecord]:
        ids = [item for item in instance_ids if item]
        if not ids:
            return []
        payload = self._request(
            "POST", "/instance-operations/terminate", json={"instance_ids": ids}
        )
        entries = (
            payload.get("terminated_instances", []) if isinstance(payload, dict) else []
        )
        return [_parse_instance(item) for item in entries]

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self._client.request(method, path.lstrip("/"), **kwargs)
        except httpx.HTTPError as exc:
            raise LammyNetworkError(str(exc)) from exc

        if response.status_code >= 400:
            error_payload = _extract_error(response)
            raise LammyApiError(
                response.status_code,
                error_payload.code,
                error_payload.message,
                error_payload.suggestion,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise LammyApiError(
                response.status_code, "invalid-json", "The Lambda API returned invalid JSON."
            ) from exc

        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload


def _parse_instance_type_entry(data: dict) -> InstanceTypeSummary:
    instance_type = data.get("instance_type") or {}
    specs_data = instance_type.get("specs") or {}
    specs = InstanceTypeSpecs(
        gpus=specs_data.get("gpus"),
        vcpus=specs_data.get("vcpus"),
        memory_gib=specs_data.get("memory_gib"),
        storage_gib=specs_data.get("storage_gib"),
    )
    regions = [
        RegionInfo(
            name=region.get("name", ""),
            description=region.get("description"),
        )
        for region in data.get("regions_with_capacity_available") or []
    ]
    return InstanceTypeSummary(
        name=instance_type.get("name", ""),
        description=instance_type.get("description"),
        gpu_description=instance_type.get("gpu_description"),
        price_cents_per_hour=instance_type.get("price_cents_per_hour"),
        specs=specs,
        regions_with_capacity=regions,
    )


def _parse_instance(data: dict) -> InstanceRecord:
    instance_type = data.get("instance_type") or {}
    specs_data = instance_type.get("specs") or {}
    specs = InstanceTypeSpecs(
        gpus=specs_data.get("gpus"),
        vcpus=specs_data.get("vcpus"),
        memory_gib=specs_data.get("memory_gib"),
        storage_gib=specs_data.get("storage_gib"),
    )
    region = data.get("region") or {}
    summary = InstanceTypeSummary(
        name=instance_type.get("name", ""),
        description=instance_type.get("description"),
        gpu_description=instance_type.get("gpu_description"),
        price_cents_per_hour=instance_type.get("price_cents_per_hour"),
        specs=specs,
    )
    actions = {}
    action_data = data.get("actions") or {}
    for key, entry in action_data.items():
        if isinstance(entry, dict):
            actions[key] = bool(entry.get("available"))
    status_raw = data.get("status")
    if isinstance(status_raw, dict):
        status_value = status_raw.get("name") or status_raw.get("state") or ""
    else:
        status_value = status_raw or ""
    return InstanceRecord(
        id=data.get("id", ""),
        status=status_value,
        region=RegionInfo(
            name=region.get("name", ""),
            description=region.get("description"),
        ),
        instance_type=summary,
        ssh_key_names=list(data.get("ssh_key_names") or []),
        name=data.get("name"),
        hostname=data.get("hostname"),
        ip=data.get("ip"),
        private_ip=data.get("private_ip"),
        jupyter_url=data.get("jupyter_url"),
        jupyter_token=data.get("jupyter_token"),
        actions=actions,
    )


def _extract_error(response: httpx.Response) -> _ApiErrorPayload:
    try:
        payload = response.json()
    except ValueError:
        return _ApiErrorPayload(
            code="http-error",
            message=f"Status {response.status_code} (no JSON body)",
        )

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        return _ApiErrorPayload(
            code=error.get("code", "unknown-error"),
            message=error.get("message", "The Lambda API returned an error."),
            suggestion=error.get("suggestion"),
        )
    return _ApiErrorPayload(
        code="unknown-error",
        message=f"Status {response.status_code}",
    )
