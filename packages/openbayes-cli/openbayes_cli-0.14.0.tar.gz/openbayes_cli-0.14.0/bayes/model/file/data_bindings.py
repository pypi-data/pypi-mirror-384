from typing import List, Optional
from pydantic import BaseModel, Field
import yaml
from pathlib import Path
import typer


class OpenBayesDataBinding(BaseModel):
    data: str
    name: Optional[str] = None
    path: str
    type: str


class DataBindings(BaseModel):
    data_binding: Optional[List[OpenBayesDataBinding]] = Field(None)
    binding: Optional[List[str]] = Field(None)
    data_bindings: List[OpenBayesDataBinding] = Field(default_factory=list)
    bindings: Optional[List[str]] = Field(None)

    def get_data_bindings(self) -> List[OpenBayesDataBinding]:
        if self.data_bindings:
            return self.data_bindings
        if self.data_binding:
            return self.data_binding
        if self.bindings:
            binding_list = []
            for b in self.bindings:
                parts = b.split(":")
                data_binding = OpenBayesDataBinding(
                    data=parts[0],
                    path=parts[1],
                    type=parts[2] if len(parts) > 2 else "ro"
                )
                binding_list.append(data_binding)
            return binding_list
        return []

    def get_bindings(self) -> List[str]:
        if self.bindings:
            return self.bindings
        return self.binding or []
