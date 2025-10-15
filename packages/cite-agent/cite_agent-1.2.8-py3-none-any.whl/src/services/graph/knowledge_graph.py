"""Lightweight async knowledge graph implementation used by the research synthesizer.

The production design originally assumed an external graph database, but the launch-ready
runtime needs a dependable in-process implementation that works without external services.
This module provides a minimal yet functional directed multigraph using in-memory storage.

The implementation focuses on the operations exercised by ``ResearchSynthesizer``:

* ``upsert_entity`` – register/update an entity node with typed metadata
* ``upsert_relationship`` – connect two entities with rich relationship properties
* ``get_entity`` / ``get_relationships`` – helper APIs for diagnostics and future features

Data is persisted in memory and optionally mirrored to a JSON file on disk so the graph can
survive multiple sessions during local development.  All public methods are ``async`` to keep
parity with the historical interface and to allow easy replacement with an external graph
backend in the future.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["KnowledgeGraph", "GraphEntity", "GraphRelationship"]


@dataclass
class GraphEntity:
    """Represents a node in the knowledge graph."""

    entity_id: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.entity_id,
            "type": self.entity_type,
            "properties": self.properties,
        }


@dataclass
class GraphRelationship:
    """Represents a directed, typed relationship between two entities."""

    rel_type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.rel_type,
            "source": self.source_id,
            "target": self.target_id,
            "properties": self.properties,
        }


class KnowledgeGraph:
    """A simple async-safe in-memory knowledge graph."""

    def __init__(self, *, persistence_path: Optional[Path] = None) -> None:
        self._entities: Dict[str, GraphEntity] = {}
        # Adjacency list keyed by (source_id, rel_type) -> list[target_id, props]
        self._relationships: List[GraphRelationship] = []
        self._lock = asyncio.Lock()
        self._persistence_path = persistence_path
        if self._persistence_path:
            self._load_from_disk()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_from_disk(self) -> None:
        if not self._persistence_path or not self._persistence_path.exists():
            return
        try:
            payload = json.loads(self._persistence_path.read_text())
        except Exception:
            return

        for entity in payload.get("entities", []):
            graph_entity = GraphEntity(
                entity_id=entity["id"],
                entity_type=entity.get("type", "Unknown"),
                properties=entity.get("properties", {}),
            )
            self._entities[graph_entity.entity_id] = graph_entity

        for rel in payload.get("relationships", []):
            graph_rel = GraphRelationship(
                rel_type=rel.get("type", "related_to"),
                source_id=rel.get("source"),
                target_id=rel.get("target"),
                properties=rel.get("properties", {}),
            )
            self._relationships.append(graph_rel)

    def _persist(self) -> None:
        if not self._persistence_path:
            return
        data = {
            "entities": [entity.to_dict() for entity in self._entities.values()],
            "relationships": [rel.to_dict() for rel in self._relationships],
        }
        try:
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            self._persistence_path.write_text(json.dumps(data, indent=2, sort_keys=True))
        except Exception:
            # Persistence failures should never stop the conversation flow
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def upsert_entity(self, entity_type: str, properties: Dict[str, Any]) -> str:
        """Create or update an entity.

        Args:
            entity_type: Semantic type (e.g., "Paper", "Author").
            properties: Arbitrary metadata. ``properties['id']`` is optional; when missing
                a deterministic identifier is derived from ``properties['external_id']`` or
                a hash of the payload.
        Returns:
            The entity identifier stored in the graph.
        """

        async with self._lock:
            entity_id = _determine_entity_id(entity_type, properties)
            entity = self._entities.get(entity_id)
            if entity:
                entity.properties.update(properties)
            else:
                entity = GraphEntity(entity_id=entity_id, entity_type=entity_type, properties=properties)
                self._entities[entity_id] = entity
            self._persist()
            return entity_id

    async def upsert_relationship(
        self,
        rel_type: str,
        source_id: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, str]:
        """Create or update a directed relationship between two entities."""

        properties = properties or {}
        async with self._lock:
            relationship = GraphRelationship(
                rel_type=rel_type,
                source_id=source_id,
                target_id=target_id,
                properties=properties,
            )
            self._relationships.append(relationship)
            self._persist()
            return (relationship.rel_type, relationship.source_id, relationship.target_id)

    async def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        async with self._lock:
            return self._entities.get(entity_id)

    async def get_relationships(self, entity_id: str) -> List[GraphRelationship]:
        async with self._lock:
            return [rel for rel in self._relationships if rel.source_id == entity_id or rel.target_id == entity_id]

    async def stats(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "entities": len(self._entities),
                "relationships": len(self._relationships),
            }


def _determine_entity_id(entity_type: str, properties: Dict[str, Any]) -> str:
    """Best-effort deterministic identifier for an entity."""

    # Preferred explicit IDs
    for key in ("id", "external_id", "paper_id", "author_id", "identifier"):
        value = properties.get(key)
        if value:
            return str(value)

    # Fall back to hashed representation (order-stable via JSON dumps)
    import hashlib

    payload = json.dumps({"type": entity_type, "properties": properties}, sort_keys=True)
    return f"{entity_type}:{hashlib.md5(payload.encode('utf-8')).hexdigest()}"
