from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from bayes.model.dataset_version import DatasetVersion


class DatasetVersionData(BaseModel):
    data: List[DatasetVersion]


class Output(BaseModel):
    path: str


class JobOutput(BaseModel):
    output: Output
    createdAt: datetime


class JobData(BaseModel):
    data: List[JobOutput]


class Party(BaseModel):
    datasetVersions: Optional[DatasetVersionData] = None
    jobs: Optional[JobData] = None


class ModeEnum(str, Enum):
    task = "task"
    workspace = "workspace"
    hypertuning = "hypertuning"