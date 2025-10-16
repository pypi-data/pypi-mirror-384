from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InstanceTypeSpecs:
    gpus: Optional[int] = None
    vcpus: Optional[int] = None
    memory_gib: Optional[int] = None
    storage_gib: Optional[int] = None


@dataclass
class RegionInfo:
    name: str
    description: Optional[str] = None


@dataclass
class InstanceTypeSummary:
    name: str
    description: Optional[str]
    gpu_description: Optional[str]
    price_cents_per_hour: Optional[int]
    specs: InstanceTypeSpecs = field(default_factory=InstanceTypeSpecs)
    regions_with_capacity: List[RegionInfo] = field(default_factory=list)

    @property
    def price_per_hour(self) -> Optional[float]:
        if self.price_cents_per_hour is None:
            return None
        return self.price_cents_per_hour / 100.0


@dataclass
class InstanceRecord:
    id: str
    status: str
    region: RegionInfo
    instance_type: InstanceTypeSummary
    ssh_key_names: List[str] = field(default_factory=list)
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip: Optional[str] = None
    private_ip: Optional[str] = None
    jupyter_url: Optional[str] = None
    jupyter_token: Optional[str] = None
    actions: Dict[str, bool] = field(default_factory=dict)

    def preferred_display_name(self) -> str:
        if self.name:
            return self.name
        if self.hostname:
            return self.hostname
        return self.id


@dataclass
class SshKeyRecord:
    id: str
    name: str
    public_key: str
