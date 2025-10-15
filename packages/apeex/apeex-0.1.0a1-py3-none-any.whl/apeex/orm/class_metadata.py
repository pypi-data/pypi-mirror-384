from dataclasses import dataclass
from typing import Optional, List

@dataclass
class FieldMetadata:
    name: str
    column: str
    type: str
    id: bool = False
    nullable: bool = True

@dataclass
class AssociationMetadata:
    name: str
    target: str
    type: str  # one_to_one, many_to_one, one_to_many, many_to_many
    mapped_by: Optional[str] = None
    join_column: Optional[str] = None

@dataclass
class ClassMetadata:
    class_name: str
    table: str
    fields: List[FieldMetadata]
    associations: List[AssociationMetadata]