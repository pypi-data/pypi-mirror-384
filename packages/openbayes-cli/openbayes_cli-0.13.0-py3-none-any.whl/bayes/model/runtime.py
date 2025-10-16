from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from bayes.model.resource import WhiteListUserItem, Group


class DeviceType(str, Enum):
    GPU = "GPU"
    CPU = "CPU"


class ClusterRuntime(BaseModel):
    framework: str
    version: str
    device: DeviceType
    name: str
    image: Optional[str] = Field(None)
    preserved: Optional[bool] = Field(None)
    type: str
    users: Optional[List[WhiteListUserItem]] = Field(None)
    groups: Optional[List[Group]] = Field(None)
    labels: Optional[List[str]] = Field(None)
    deprecated: bool

    def usage(self) -> str:
        return f"{self.framework}-{self.version}"

    def version_string(self) -> str:
        version_str = self.version.replace(".", "")
        if version_str.isdigit():
            return f"v{self.version}"
        return self.version
