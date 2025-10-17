"""
Data models for Table Categorization Agent

Defines the data structures used throughout the agent.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class ColumnAnalysis:
    """Analysis results for a single column"""

    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "dtype": self.dtype,
            "null_count": self.null_count,
            "null_percentage": self.null_percentage,
            "unique_count": self.unique_count,
            "unique_percentage": self.unique_percentage,
            "sample_values": self.sample_values,
        }


@dataclass
class TableAnalysis:
    """Complete analysis of a table structure"""

    table_name: str
    row_count: int
    column_count: int
    columns: List[ColumnAnalysis] = field(default_factory=list)
    data_types: Dict[str, str] = field(default_factory=dict)
    null_counts: Dict[str, int] = field(default_factory=dict)
    unique_counts: Dict[str, int] = field(default_factory=dict)
    sample_values: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [col.to_dict() for col in self.columns],
            "data_types": self.data_types,
            "null_counts": self.null_counts,
            "unique_counts": self.unique_counts,
            "sample_values": self.sample_values,
        }


@dataclass
class TableCategory:
    """Represents a categorized table with its domain mapping"""

    table_name: str
    primary_entity: str
    confidence_score: float
    mapped_attributes: Dict[str, str]
    suggested_relationships: List[str]
    data_quality_score: float
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "table_name": self.table_name,
            "primary_entity": self.primary_entity,
            "confidence_score": self.confidence_score,
            "mapped_attributes": self.mapped_attributes,
            "suggested_relationships": self.suggested_relationships,
            "data_quality_score": self.data_quality_score,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
        }

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if categorization has high confidence"""
        return self.confidence_score >= threshold

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """Check if data quality is high"""
        return self.data_quality_score >= threshold

    def get_mapping_summary(self) -> str:
        """Get summary of attribute mappings"""
        if not self.mapped_attributes:
            return "No attributes mapped"

        mapped_count = len(self.mapped_attributes)
        return f"{mapped_count} attributes mapped to domain concepts"


# @dataclass
# class CategorizationResult:
#     """Result of table categorization process"""

#     table_categories: List[TableCategory]
#     domain_coverage: float
#     data_insights: List[str]
#     next_steps: List[str]
#     total_tables: int = 0
#     high_confidence_count: int = 0
#     high_quality_count: int = 0
#     created_at: datetime = field(default_factory=datetime.now)

#     def __post_init__(self):
#         """Calculate derived fields"""
#         self.total_tables = len(self.table_categories)
#         self.high_confidence_count = sum(
#             1 for cat in self.table_categories if cat.is_high_confidence()
#         )
#         self.high_quality_count = sum(
#             1 for cat in self.table_categories if cat.is_high_quality()
#         )

#     def to_dict(self) -> Dict[str, Any]:
#         """Convert to dictionary"""
#         return {
#             "table_categories": [cat.to_dict() for cat in self.table_categories],
#             "domain_coverage": self.domain_coverage,
#             "data_insights": self.data_insights,
#             "next_steps": self.next_steps,
#             "total_tables": self.total_tables,
#             "high_confidence_count": self.high_confidence_count,
#             "high_quality_count": self.high_quality_count,
#             "created_at": self.created_at.isoformat(),
#         }

#     def get_summary_stats(self) -> Dict[str, Any]:
#         """Get summary statistics"""

#         return {
#             "total_tables": self.total_tables,
#             "domain_coverage": self.domain_coverage,
#             "high_confidence_rate": (
#                 self.high_confidence_count / self.total_tables
#                 if self.total_tables > 0
#                 else 0
#             ),
#             "high_quality_rate": (
#                 self.high_quality_count / self.total_tables
#                 if self.total_tables > 0
#                 else 0
#             ),
#             "total_insights": len(self.data_insights),
#             "total_next_steps": len(self.next_steps),
#         }

#     def export_json(self, file_path: str) -> None:
#         """Export results to JSON file"""
#         with open(file_path, "w") as f:
#             json.dump(self.to_dict(), f, indent=2)


@dataclass
class DomainSchema:
    """Domain schema information"""

    name: str
    entities: List[Dict[str, Any]]
    properties: List[Dict[str, Any]]
    namespaces: Dict[str, str]
    summary: Dict[str, Any]

    @classmethod
    def from_json(cls, file_path: str) -> "DomainSchema":
        """Create DomainSchema from JSON file"""
        with open(file_path, "r") as f:
            data = json.load(f)

        return cls(
            name=data.get("namespaces", {}).get("", "Unknown"),
            entities=data.get("entities", []),
            properties=data.get("properties", []),
            namespaces=data.get("namespaces", {}),
            summary=data.get("summary", {}),
        )

    def get_entity_names(self) -> List[str]:
        """Get list of entity names"""
        return [
            entity.get("label", entity.get("iri", "Unknown"))
            for entity in self.entities
        ]

    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get entity by name"""
        for entity in self.entities:
            if entity.get("label") == name or entity.get("iri", "").endswith(name):
                return entity
        return None

    def get_entity_attributes(self, entity_name: str) -> List[str]:
        """Get attributes for a specific entity"""
        entity = self.get_entity_by_name(entity_name)
        if not entity:
            return []

        return [
            attr.get("label", attr.get("iri", "Unknown"))
            for attr in entity.get("attributes", [])
        ]


# @dataclass
# class TableCategory:
#     """Represents a categorized table with its domain mapping"""

#     table_name: str
#     primary_entity: List[str]
#     confidence_score: float
#     mapped_attributes: Dict[str, str]
#     suggested_relationships: List[str]
#     data_quality_score: float
#     recommendations: List[str]


# @dataclass
# class CategorizationResult:
#     """Result of table categorization process"""
#     table_categories: List[TableCategory]
#     domain_coverage: float
#     data_insights: List[str]
#     next_steps: List[str]


class EntityTablesMapping(BaseModel):
    entity_name: str = Field(..., description="Entity name")
    tables: List[str] = Field(default_factory=list, description="Assigned tables")


class CategorizationResult(BaseModel):
    entities: List[EntityTablesMapping]
    unassigned: List[str]

    @classmethod
    def from_raw_json(cls, raw: Dict[str, List[str]]):
        entities = []
        unassigned = []
        for key, value in raw.items():
            if key.lower() == "unassigned":
                unassigned = value
            else:
                entities.append(EntityTablesMapping(entity_name=key, tables=value))
        return cls(entities=entities, unassigned=unassigned)
