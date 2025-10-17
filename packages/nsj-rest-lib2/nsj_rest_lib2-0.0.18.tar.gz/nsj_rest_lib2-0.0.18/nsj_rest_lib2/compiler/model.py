import uuid

from typing import Any


class RelationDependency:
    def __init__(self):
        self.tenant: int | None = None
        self.grupo_empresarial: uuid.UUID | None = None
        self.entity_resource: str | None = None
        self.entity_scope: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant": self.tenant,
            "grupo_empresarial": (
                str(self.grupo_empresarial) if self.grupo_empresarial else None
            ),
            "entity_resource": self.entity_resource,
            "entity_scope": self.entity_scope,
        }

    def from_dict(self, data: dict[str, Any]) -> "RelationDependency":
        self.tenant = data.get("tenant")
        self.grupo_empresarial = (
            uuid.UUID(data["grupo_empresarial"])
            if data.get("grupo_empresarial")
            else None
        )
        self.entity_resource = data.get("entity_resource")
        self.entity_scope = data.get("entity_scope")

        return self


class CompilerResult:
    def __init__(self):
        self.dto_class_name: str | None = None
        self.dto_code: str | None = None
        self.entity_class_name: str | None = None
        self.entity_code: str | None = None
        self.api_expose: bool | None = None
        self.api_resource: str | None = None
        self.api_verbs: list[str] | None = None
        self.relations_dependencies: list[RelationDependency] | None = None
