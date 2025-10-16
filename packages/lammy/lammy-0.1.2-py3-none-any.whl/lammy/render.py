from __future__ import annotations

from typing import Iterable

from rich.table import Table

from .models import InstanceRecord, InstanceTypeSummary, SshKeyRecord


def instance_table(instances: Iterable[InstanceRecord]) -> Table:
    table = Table(show_lines=False, pad_edge=False, title="Running Instances")
    table.add_column("ID", overflow="fold")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("GPUs", justify="right")
    table.add_column("Price/hr", justify="right")
    table.add_column("Status")
    table.add_column("IP")
    table.add_column("Region")

    for inst in instances:
        specs = inst.instance_type.specs
        table.add_row(
            inst.id,
            inst.preferred_display_name(),
            inst.instance_type.name,
            _maybe(specs.gpus),
            _format_price(inst.instance_type.price_per_hour),
            inst.status or "unknown",
            inst.ip or "",
            inst.region.name,
        )
    return table


def instance_types_table(items: Iterable[InstanceTypeSummary]) -> Table:
    table = Table(show_lines=False, pad_edge=False, title="Instance Types")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("GPUs", justify="right")
    table.add_column("vCPUs", justify="right")
    table.add_column("RAM (GiB)", justify="right")
    table.add_column("Storage (GiB)", justify="right")
    table.add_column("Price/hr", justify="right")
    table.add_column("Regions")

    for item in items:
        specs = item.specs
        regions = ", ".join(region.name for region in item.regions_with_capacity) or "—"
        table.add_row(
            item.name,
            item.description or "",
            _maybe(specs.gpus),
            _maybe(specs.vcpus),
            _maybe(specs.memory_gib),
            _maybe(specs.storage_gib),
            _format_price(item.price_per_hour),
            regions,
        )
    return table


def ssh_keys_table(keys: Iterable[SshKeyRecord]) -> Table:
    table = Table(show_lines=False, pad_edge=False, title="SSH Keys")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Fingerprint")
    for key in keys:
        table.add_row(
            key.name,
            key.id,
            _fingerprint(key.public_key),
        )
    return table


def _maybe(value: object | None) -> str:
    if value in (None, "", []):
        return "—"
    return str(value)


def _format_price(price: float | None) -> str:
    if price is None:
        return "—"
    return f"${price:.2f}"


def _fingerprint(public_key: str | None) -> str:
    if not public_key:
        return "—"
    parts = public_key.strip().split()
    if len(parts) >= 2:
        key_body = parts[1]
    else:
        key_body = parts[0]
    if len(key_body) <= 16:
        return key_body
    return f"{key_body[:8]}…{key_body[-8:]}"
