from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from bayes.client.gear_client import Link


class Dataset(BaseModel):
    id: str
    name: str
    status: Optional[str] = None
    latestVersion: Optional[int] = None
    size: Optional[float] = None
    updatedAt: Optional[datetime] = None
    links: Optional[List[Link]] = []

    def get_link_value(self, link_name: str) -> Optional[str]:
        for link in self.links:
            if link.name == link_name:
                return link.value
        return None

