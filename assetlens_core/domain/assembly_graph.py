from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssemblyNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    name: str
    normalized_name: str
    type: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    parent_node_id: str | None = Field(default=None)
    children: list[str] = Field(default_factory=list)
    signature: str = Field(default="")
    mesh_refs: list[str] = Field(default_factory=list)


class AssemblyGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_id: str
    nodes_by_id: dict[str, AssemblyNode]

    def root(self) -> AssemblyNode:
        if self.root_id not in self.nodes_by_id:
            raise ValueError(f"root_id not found in nodes_by_id: {self.root_id}")
        return self.nodes_by_id[self.root_id]

