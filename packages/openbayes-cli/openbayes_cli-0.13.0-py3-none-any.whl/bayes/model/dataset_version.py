from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from bayes.client.gear_client import Link


class DatasetVersion(BaseModel):
    id: Optional[str] = None
    version: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    size: Optional[float] = None
    deletedAt: Optional[datetime] = None
    semanticBindingName: Optional[str] = None
    createdAt: Optional[datetime] = None

    def deletedString(self):
        if self.deletedAt is not None:
            return "Deleted"
        else:
            return ""

class PublicDatasetVersions(BaseModel):
    data: List[DatasetVersion]

