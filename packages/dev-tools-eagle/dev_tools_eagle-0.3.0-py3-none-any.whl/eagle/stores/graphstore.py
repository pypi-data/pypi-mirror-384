# graph_store.py
from __future__ import annotations
from typing import Union, Any, Dict, Optional, List
from langgraph.store.base import Op
from langgraph.store.base import GetOp, SearchOp, PutOp, ListNamespacesOp, Op
from dataclasses import dataclass, field
from langchain_core.embeddings import Embeddings

@dataclass
class Node:
    id: str
    labels: list[str] = field(default_factory=lambda: ["Resource"])
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "labels": self.labels, **self.properties}
    
    @classmethod
    def from_record(cls, record: dict) -> "Node":
        return cls(
            id=record.get("id",""),
            labels=record.get("labels", ["Resource"]),
            properties={k: v for k, v in record.items() if k not in ("id", "labels")}
        )
    
    def __repr__(self) -> str:
        return f"Node(id={self.id}, labels={self.labels})"


@dataclass
class Relation:
    subject: Node
    predicate: str
    object: Node
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "subject": self.subject.to_dict(),
            "predicate": self.predicate,
            "object": self.object.to_dict(),
            "properties": self.properties,
        }
    
    @classmethod
    def from_cypher(cls, subject: dict, predicate: str, obj: dict, rel_props: dict) -> "Relation":
        return cls(
            subject=Node.from_record(subject),
            predicate=predicate,
            object=Node.from_record(obj),
            properties=rel_props,
        )
    
    def __repr__(self) -> str:
        return f"Relation({self.subject.id}-[{self.predicate}]->{self.object.id})"


class PutNodeOp:
    def __init__(self, namespace: tuple[str, ...], node: Node, embed_fields: List[str] | None = None):
        self.namespace = namespace
        self.node = node
        self.embed_fields = embed_fields



class PutTripleOp:
    def __init__(
        self,
        namespace: tuple[str, ...],
        relation: Relation
    ):
        self.namespace = namespace
        self.relation = relation


class GetNodeOp:
    """Retrieve a specific node by its ID."""
    def __init__(self, namespace: tuple[str, ...], node_id: str, node_labels: List[str] = []):
        self.namespace = namespace
        self.node_id = node_id
        self.labels = node_labels


class SearchNodeOp:
    """Search nodes by properties."""
    def __init__(self, namespace: tuple[str, ...], labels: List[str] = [],properties: dict | None = None, limit: int = 10):
        self.namespace = namespace
        self.properties = properties or {}
        self.limit = limit
        self.labels = labels

class GetTripleOp:
    """Retrieve a specific triple by subject, predicate, object."""
    def __init__(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str, options: dict = {}):
        self.namespace = namespace
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.subject_labels = options.get("subject_labels", None)
        self.object_labels = options.get("object_labels", None)


class SearchTripleOp:
    """Search triples by subject, predicate, object (wildcards allowed)."""
    def __init__(
        self,
        namespace: tuple[str, ...],
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        limit: int = 10,
        options: dict = {}
    ):
        self.namespace = namespace
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.limit = limit
        self.subject_labels = options.get("subject_labels", None)
        self.object_labels = options.get("object_labels", None)

class DeleteNodeOp:
    """Operation to delete a node by its ID."""
    def __init__(self, namespace: tuple[str, ...], node_id: str, labels: List[str] | None = None, detach: bool = True):
        self.namespace = namespace
        self.node_id = node_id
        self.labels = labels
        self.detach = detach


class DeleteTripleOp:
    """Operation to delete a triple/relationship."""
    def __init__(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str):
        self.namespace = namespace
        self.subject = subject
        self.predicate = predicate
        self.object = object


GraphOp = Union[
    Op, 
    PutNodeOp, 
    PutTripleOp, 
    GetTripleOp, 
    SearchTripleOp, 
    GetNodeOp, 
    SearchNodeOp,
    DeleteNodeOp,
    DeleteTripleOp
]

class GraphBaseStore:
    """Base Grphstore for Eagle-specific functionality, extending"""

    def __init__(self, driver, embeddings: Optional[Embeddings] = None, embedding_dims: Optional[int] = None, database: Optional[str] = None):
        self.driver = driver
        self.embeddings = embeddings
        self.embedding_dims = embedding_dims
        self.database = database
    
    def batch(self, ops):
        """Execute a batch of operations synchronously."""
        pass

    def put_node(self,  node: Node):
        pass

    def get_node(self):
        pass

    def search_nodes(self):
        pass

    def delete_node(self):
        pass

    def put_triple(self):
        pass
    

__all__ = [
    "Node",
    "Relation",
    "PutNodeOp",
    "PutTripleOp",
    "GetNodeOp",
    "SearchNodeOp",
    "GetTripleOp",
    "SearchTripleOp",
    "DeleteNodeOp",
    "DeleteTripleOp",
    "GraphOp",
    "GraphBaseStore"
]