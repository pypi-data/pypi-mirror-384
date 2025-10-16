from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Cpu(BaseModel):
    count: float
    millicores: int
    type: str


class Gpu(BaseModel):
    name: str
    verboseName: Optional[str] = Field(None)
    vendor: str
    description: Optional[str] = Field(None)
    mode: str
    group: Optional[str] = Field(None)
    count: int
    memory: int
    type: str


class Disk(BaseModel):
    size: int
    type: str


class WhiteListUserItem(BaseModel):
    username: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)


class Group(BaseModel):
    id: str
    name: str
    description: Optional[str] = Field(None)
    created_at: datetime


# class Resource(BaseModel):
#     name: str
#     memory: int
#     cpu: ResourceCpu
#     gpu: ResourceGpu
#     disk: ResourceDisk
#     gpuResource: bool
#     verboseName: str
#     type: Optional[str] = Field(None)


class ResourceData(BaseModel):
    name: str
    memory: int
    cpu: Cpu
    gpu: Gpu
    disk: Disk
    gpuResource: Optional[bool] = Field(None)
    verboseName: str
    type: str
    users: Optional[List[WhiteListUserItem]] = Field(None)
    groups: Optional[List[Group]] = Field(None)
    labels: Optional[List[str]] = Field(None)
    locked_count: Optional[int] = Field(None)
    free_count: Optional[int] = Field(None)
    total_count: Optional[int] = Field(None)
    available: Optional[bool] = Field(None)

    def get_resource_desc(self) -> str:
        return self.verboseName

    def gpu_string(self) -> str:
        if self.gpu.memory == 0 and self.gpu.count == 0:
            return "-"
        gpu = byte_size(self.gpu.memory)
        if self.gpu.count > 1:
            gpu += f" x {self.gpu.count}"
        return gpu

    def cpu_string(self) -> str:
        cores = self.cpu.millicores / 1000.0
        cpu = f"{cores:.1f}".rstrip('0').rstrip('.')
        if cores > 1:
            cpu += " cores"
        else:
            cpu += " core"
        return cpu

    def memory_string(self) -> str:
        return byte_size(self.memory)

    def disk_string(self) -> str:
        return byte_size(self.disk.size)


class TotalComputationQuota(BaseModel):
    # maxQuotaReservedMonth: int
    # debtMinutes: int
    # quotaItems: [ComputationQuota]
    availableMinutes: int


class ComputationQuotaPair(BaseModel):
    key: str
    value: TotalComputationQuota


class Quota(BaseModel):
    computationQuota: Optional[List[ComputationQuotaPair]]


class ResourceCurrentLimitFreeCount(BaseModel):
    current: int
    limit: int


class ResourcesLimitation(BaseModel):
    key: str
    value: ResourceCurrentLimitFreeCount


class Limitations(BaseModel):
    resources: List[ResourcesLimitation]


class ComputingResouce(BaseModel):
    resource: ResourceData
    limitation: int
    quota: int


def byte_size(mb):
    MB = 1
    GB = MB * 1000
    TB = GB * 1000

    value = float(mb)
    unit = " GB"
    if value >= TB:
        unit = " TB"
        value /= TB
    else:
        value /= GB

    result = f"{value:.0f}{unit}"
    return result
