from __future__ import annotations
import os
import warnings
from datetime import datetime, timezone
from typing import Iterable, Optional, Literal, Any

from langchain_core.embeddings import Embeddings
from langgraph.store.base import (
    IndexConfig,
    Item,
    Result,
)
from neo4j import AsyncGraphDatabase, GraphDatabase, Query
from eagle.stores.graphstore import (
    PutNodeOp, PutTripleOp, GraphOp, GetNodeOp, GetTripleOp, 
    SearchNodeOp, SearchTripleOp, Node, Relation, GraphBaseStore,
    DeleteNodeOp, DeleteTripleOp
)
class Neo4jStoreConfig(IndexConfig):
    """Configuration for the Neo4j store."""
    pass 


class Neo4jStore(GraphBaseStore):
    """
    A triplestore implementation using Neo4j as the backend.

    This store maps namespaces, keys, and values to nodes in a Neo4j graph.
    """

    def __init__(
        self, 
        *, 
        embeddings: Optional[Embeddings] = None, 
        embedding_dims: Optional[int] = None, 
        index: Optional[Neo4jStoreConfig] = None, 
        database: Optional[str] = 'neo4j'
    ) -> None:
        neo4j_url = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        self.driver = GraphDatabase.driver(neo4j_url, auth=(username, password), database=database)
        self.async_driver = AsyncGraphDatabase.driver(
            neo4j_url, auth=(username, password), database=database
        )
        self._closed = False
        self.index_config = index

        super().__init__(
            self.driver, 
            embeddings=embeddings, 
            embedding_dims=embedding_dims, 
            database=database
        )

    def close(self) -> None:
        """Close the synchronous driver connection."""
        if not self._closed:
            self.driver.close()
            self._closed = True

    async def aclose(self) -> None:
        """Close the asynchronous driver connection."""
        if not self._closed:
            await self.async_driver.close()
            self._closed = True

    def __del__(self) -> None:
        """Ensure drivers are closed when the object is deleted."""
        try:
            self.close()
        except Exception:
            pass

    ## SYNC

    def batch(self, ops: Iterable[GraphOp]) -> list[Result]:
        """
        Execute a batch of graph operations synchronously.
        """
        with self.driver.session(database=self.database) as session:
            return [self._execute_op(session, op) for op in ops]

    def _execute_op(self, session, op: GraphOp) -> Result:
        """
        Execute a single graph operation.

        This method dispatches the operation to the appropriate handler.
        """
        if isinstance(op, PutNodeOp):
            return self._handle_put_node(session, op)
        elif isinstance(op, PutTripleOp):
            return self._handle_put_triple(session, op)
        elif isinstance(op, GetTripleOp):
            return self._handle_get_triple(session, op)  
        elif isinstance(op, SearchTripleOp):
            return self._handle_search_triple(session, op)
        elif isinstance(op, GetNodeOp):
            return self._handle_get_node(session, op)
        elif isinstance(op, SearchNodeOp):
            return self._handle_search_node(session, op)
        elif isinstance(op, DeleteNodeOp):
            return self._handle_delete_node(session, op)
        elif isinstance(op, DeleteTripleOp):
            return self._handle_delete_triple(session, op)
        else:
            raise ValueError(f"Unsupported operation: {type(op)}")

    def _handle_put_node(self, session, op: PutNodeOp) -> Optional[Item]:
        """
        Handle the PutNodeOp operation to create or update a node.

        If embedding is configured, it also generates and stores the node's embedding.
        """
        try:
            labels = ":".join(op.node.labels)
            cypher = f"""
                    MERGE (n:{labels} {{id: $id}})
                    SET n += $props
                    RETURN n
                    """
            vector = None

            if op.embed_fields and self.embeddings:
                text = "\n".join([str(op.node.properties.get(embed_field, "")) for embed_field in op.embed_fields]) 

                if text:
                    vector = self.embeddings.embed_query(text)
                    op.node.properties["embedding"] = vector
            

            result = session.run(cypher, id=op.node.id, props=op.node.properties).single()

            return Item(namespace=op.namespace, key=op.node.id, value=dict(result["n"]), 
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc))
        except Exception as e:
            print(e)
            return None

    def _handle_put_triple(self, session, op: PutTripleOp) -> Optional[Item]:
        """
        Handle the PutTripleOp operation to create or update a triple (relationship).
        """
        rel = op.relation
        cypher = f"""
        MERGE (s:{':'.join(rel.subject.labels)} {{id: $sid}})
        SET s += $sprops
        MERGE (o:{':'.join(rel.object.labels)} {{id: $oid}})
        SET o += $oprops
        MERGE (s)-[r:`{rel.predicate}`]->(o)
        SET r += $rprops
        RETURN r
        """
        result = session.run(
            cypher,
            sid=rel.subject.id, sprops=rel.subject.properties,
            oid=rel.object.id, oprops=rel.object.properties,
            rprops=rel.properties,
        ).single()
        return Item(
            namespace=op.namespace,
            key=f"{rel.subject.id}-{rel.predicate}-{rel.object.id}",
            value={"relation": dict(result["r"]), **rel.to_dict()},
            created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
        )
    
    def _handle_get_triple(self, session, op: GetTripleOp) -> Optional[Item]:
        """
        Handle the GetTripleOp operation to retrieve a specific triple.
        """
        object_labels = ":".join(op.object_labels) if op.object_labels else ""
        subject_labels = ":".join(op.subject_labels) if op.subject_labels else ""

        cypher = f"""
        MATCH (s{subject_labels} {{id: $subject}})-[r:`{op.predicate}`]->(o{object_labels} {{id: $object}})
        RETURN s, r, o
        """
        record = session.run(
            cypher, subject=op.subject, object=op.object
        ).single()
        if not record:
            return None
        
        rel = Relation.from_cypher(
            subject=dict(record["s"]),
            predicate=op.predicate,
            obj=dict(record["o"]),
            rel_props=dict(record["r"]),
        )

        return Item(
            namespace=op.namespace,
            key=f"{op.subject}-{op.predicate}-{op.object}",
            value=rel.to_dict(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def _handle_search_triple(self, session, op: SearchTripleOp) -> list[Item]:
        """
        Handle the SearchTripleOp operation to search for triples based on criteria.
        """
        where = []
        params = {}
        if op.subject:
            where.append("s.id = $subject")
            params["subject"] = op.subject
        if op.predicate:
            where.append("type(r) = $predicate")
            params["predicate"] = op.predicate
        if op.object:
            where.append("o.id = $object")
            params["object"] = op.object

        where_clause = "WHERE " + " AND ".join(where) if where else ""

        object_labels = ":".join(op.object_labels) if op.object_labels else ""
        subject_labels = ":".join(op.subject_labels) if op.subject_labels else ""

        cypher = f"""
        MATCH (s{subject_labels})-[r]->(o{object_labels})
        {where_clause}
        RETURN s, type(r) as predicate, r, o
        LIMIT $limit
        """
        params["limit"] = op.limit

        result = session.run(cypher, **params)
        return [
            Item(
                namespace=op.namespace,
                key=f"{rec['s']['id']}-{rec['predicate']}-{rec['o']['id']}",
                value={
                    "subject": dict(rec["s"]),
                    "predicate": rec["predicate"],
                    "object": dict(rec["o"]),
                    "relation": dict(rec["r"]),
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            for rec in result
        ]

    def _handle_get_node(self, session, op: GetNodeOp) -> Optional[Item]:
        """
        Handle the GetNodeOp operation to retrieve a specific node by its ID and labels.
        """
        labels = ":".join(str(label) for label in op.labels)
        cypher = f"""
                MATCH (n{labels} {{id: $id}})
                RETURN n
                """
        
        result = session.run(cypher, id=op.node_id, ).single()

        if not result:
            return None
        
        return Item(namespace=op.namespace, key=op.node_id, value=dict(result["n"]), 
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc))
    
    def _handle_search_node(self, session, op: SearchNodeOp) -> list[Item]:
        """
        Handle the SearchNodeOp operation to search for nodes by their properties and labels.
        """
        labels = f":{':'.join(op.labels)}" if op.labels else ""

        where_clauses = []
        params = {}

        for key, value in op.properties.items():
            param_name = f"prop_{key}"
            where_clauses.append(f"n.{key} = ${param_name}")
            params[param_name] = value

        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)

        cypher = f"""
        MATCH (n{labels})
        {where_clause}
        RETURN n
        LIMIT $limit
        """
        params["limit"] = op.limit

        result = session.run(cypher, **params)
        return [
            Item(namespace=op.namespace, key=rec["n"]["id"], value=dict(rec["n"]), created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)) for rec in result
        ]
    
    def _handle_delete_node(self, session, op: DeleteNodeOp) -> Optional[Item]:
        """
        Handle the DeleteNodeOp operation to delete a node by its ID.
        """
        cypher = f"""
                MATCH (n {{id: $id}})
                {"DETACH" if op.detach else ""} DELETE n
                """
        result = session.run(cypher, id=op.node_id)
        return None

    def _handle_delete_triple(self, session, op: DeleteTripleOp):
        """
        Handle the DeleteTripleOp operation to delete a triple by its subject, predicate, and object.
        """
        cypher = f"""
                MATCH (s)-[r:`{op.predicate}`]->(o)
                WHERE s.id = $subject AND o.id = $object
                DELETE r
                """
        result = session.run(cypher, subject=op.subject, object=op.object)
        return None

    ## ASYNC

    async def abatch(self, ops: Iterable[GraphOp]) -> list[Result]:
        """Execute a batch of graph operations asynchronously."""
        async with self.async_driver.session(database=self.database) as session:
            results = []
            for op in ops:
                result = await self._aexecute_op(session, op)
                results.append(result)
            return results

    async def _aexecute_op(self, session, op: GraphOp) -> Result:
        """Execute a single graph operation (async)."""
        if isinstance(op, PutNodeOp):
            return await self._ahandle_put_node(session, op)
        elif isinstance(op, PutTripleOp):
            return await self._ahandle_put_triple(session, op)
        elif isinstance(op, GetTripleOp):
            return await self._ahandle_get_triple(session, op)  
        elif isinstance(op, SearchTripleOp):
            return await self._ahandle_search_triple(session, op)
        elif isinstance(op, GetNodeOp):
            return await self._ahandle_get_node(session, op)
        elif isinstance(op, SearchNodeOp):
            return await self._ahandle_search_node(session, op)
        elif isinstance(op, DeleteNodeOp):
            return self._ahandle_delete_node(session, op)
        elif isinstance(op, DeleteTripleOp):
            return self._ahandle_delete_triple(session, op)
        else:
            raise ValueError(f"Unsupported operation: {type(op)}")

    async def _ahandle_put_node(self, session, op: PutNodeOp) -> Optional[Item]:
        """Handle the PutNodeOp operation (async)."""
        try:
            labels = ":".join(op.node.labels)
            cypher = f"""
                MERGE (n:{labels} {{id: $id}})
                SET n += $props
                RETURN n
            """
            
            props = op.node.properties.copy()
            
            if op.embed_fields and self.embeddings:
                text = "\n".join([
                    str(op.node.properties.get(field, "")) 
                    for field in op.embed_fields
                ]) 
                if text:
                    # Note: Most embedding models don't have async methods
                    # You may need to use asyncio.to_thread for sync embeddings
                    vector = self.embeddings.embed_query(text)
                    props["embedding"] = vector

            result = await session.run(cypher, id=op.node.id, props=props)
            record = await result.single()
            
            if not record:
                return None

            return Item(
                namespace=op.namespace, 
                key=op.node.id, 
                value=dict(record["n"]), 
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"Error in _ahandle_put_node: {e}")
            return None

    async def _ahandle_put_triple(self, session, op: PutTripleOp) -> Optional[Item]:
        """Handle the PutTripleOp operation (async)."""
        try:
            rel = op.relation
            cypher = f"""
                MERGE (s:{':'.join(rel.subject.labels)} {{id: $sid}})
                SET s += $sprops
                MERGE (o:{':'.join(rel.object.labels)} {{id: $oid}})
                SET o += $oprops
                MERGE (s)-[r:`{rel.predicate}`]->(o)
                SET r += $rprops
                RETURN r
            """
            result = await session.run(
                cypher,
                sid=rel.subject.id, sprops=rel.subject.properties,
                oid=rel.object.id, oprops=rel.object.properties,
                rprops=rel.properties,
            )
            record = await result.single()
            
            if not record:
                return None
                
            return Item(
                namespace=op.namespace,
                key=f"{rel.subject.id}-{rel.predicate}-{rel.object.id}",
                value={"relation": dict(record["r"]), **rel.to_dict()},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"Error in _ahandle_put_triple: {e}")
            return None
    
    async def _ahandle_get_triple(self, session, op: GetTripleOp) -> Optional[Item]:
        """Handle the GetTripleOp operation (async)."""
        object_labels = f":{':'.join(op.object_labels)}" if op.object_labels else ""
        subject_labels = f":{':'.join(op.subject_labels)}" if op.subject_labels else ""

        cypher = f"""
            MATCH (s{subject_labels} {{id: $subject}})-[r:`{op.predicate}`]->(o{object_labels} {{id: $object}})
            RETURN s, r, o
        """
        result = await session.run(cypher, subject=op.subject, object=op.object)
        record = await result.single()
        
        if not record:
            return None
        
        rel = Relation.from_cypher(
            subject=dict(record["s"]),
            predicate=op.predicate,
            obj=dict(record["o"]),
            rel_props=dict(record["r"]),
        )

        return Item(
            namespace=op.namespace,
            key=f"{op.subject}-{op.predicate}-{op.object}",
            value=rel.to_dict(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def _ahandle_search_triple(self, session, op: SearchTripleOp) -> list[Item]:
        """Handle the SearchTripleOp operation (async)."""
        where = []
        params = {}
        
        if op.subject:
            where.append("s.id = $subject")
            params["subject"] = op.subject
        if op.predicate:
            where.append("type(r) = $predicate")
            params["predicate"] = op.predicate
        if op.object:
            where.append("o.id = $object")
            params["object"] = op.object

        where_clause = "WHERE " + " AND ".join(where) if where else ""

        object_labels = f":{':'.join(op.object_labels)}" if op.object_labels else ""
        subject_labels = f":{':'.join(op.subject_labels)}" if op.subject_labels else ""

        cypher = f"""
            MATCH (s{subject_labels})-[r]->(o{object_labels})
            {where_clause}
            RETURN s, type(r) as predicate, r, o
            LIMIT $limit
        """
        params["limit"] = op.limit

        result = await session.run(cypher, **params)
        records = [rec async for rec in result]
        
        return [
            Item(
                namespace=op.namespace,
                key=f"{rec['s']['id']}-{rec['predicate']}-{rec['o']['id']}",
                value={
                    "subject": dict(rec["s"]),
                    "predicate": rec["predicate"],
                    "object": dict(rec["o"]),
                    "relation": dict(rec["r"]),
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            for rec in records
        ]

    async def _ahandle_get_node(self, session, op: GetNodeOp) -> Optional[Item]:
        """Handle the GetNodeOp operation (async)."""
        labels = f":{':'.join(str(label) for label in op.labels)}" if op.labels else ""
        cypher = f"""
            MATCH (n{labels} {{id: $id}})
            RETURN n
        """
        
        result = await session.run(cypher, id=op.node_id)
        record = await result.single()
        
        if not record:
            return None

        return Item(
            namespace=op.namespace, 
            key=op.node_id, 
            value=dict(record["n"]), 
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def _ahandle_search_node(self, session, op: SearchNodeOp) -> list[Item]:
        """Handle the SearchNodeOp operation (async)."""
        labels = f":{':'.join(op.labels)}" if op.labels else ""

        where_clauses = []
        params = {}

        for key, value in op.properties.items():
            param_name = f"prop_{key}"
            where_clauses.append(f"n.{key} = ${param_name}")
            params[param_name] = value

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cypher = f"""
            MATCH (n{labels})
            {where_clause}
            RETURN n
            LIMIT $limit
        """
        params["limit"] = op.limit

        result = await session.run(cypher, **params)
        records = [rec async for rec in result]
        
        return [
            Item(
                namespace=op.namespace, 
                key=rec["n"]["id"], 
                value=dict(rec["n"]), 
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) 
            for rec in records
        ]
    
    def _ahandle_delete_node(self, session, op: DeleteNodeOp) -> Optional[Item]:
        """Handle the DeleteNodeOp operation (async)."""
        pass

    def _ahandle_delete_triple(self, session, op: DeleteTripleOp) -> Optional[Item]:
        """Handle the DeleteTripleOp operation (async)."""
        pass


    # convinience 

    def put_node(self, namespace: tuple[str, ...], node: Node, embed_fields: list[str] | None = None) -> Result:
        """Convenience method to put a single node into the store."""
        op = PutNodeOp(namespace, node, embed_fields)
        return self.batch([op])[0]
    
    async def aput_node(self, namespace: tuple[str, ...], node: Node, embed_fields: list[str] | None = None) -> Result:
        """Async convenience method to put a single node into the store."""
        op = PutNodeOp(namespace, node, embed_fields)
        return (await self.abatch([op]))[0]

    def put_triple(self, namespace: tuple[str, ...], relation: Relation) -> Result:
        """Convenience method to put a single triple into the store."""
        op = PutTripleOp(namespace, relation)
        return self.batch([op])[0]

    async def aput_triple(self, namespace: tuple[str, ...], relation: Relation) -> Result:
        """Async convenience method to put a single triple into the store."""
        op = PutTripleOp(namespace, relation)
        return (await self.abatch([op]))[0]
    
    def get_node(self, namespace: tuple[str, ...], node_id: str, labels: list[str] = []) -> Result | None:
        """Convenience method to get a single node from the store."""
        return self.batch([GetNodeOp(namespace, node_id, node_labels=labels)])[0]
    
    async def aget_node(self, namespace: tuple[str, ...], node_id: str, labels:list[str] = []) -> Result | None:
        """Async convenience method to get a single node from the store."""
        return (await self.abatch([GetNodeOp(namespace, node_id, node_labels=labels)]))[0]
    
    def get_triple(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str) -> Result | None:
        """Convenience method to get a single triple from the store."""
        return self.batch([GetTripleOp(namespace, subject, predicate, object)])[0]

    async def aget_triple(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str) -> Result | None:
        """Async convenience method to get a single triple from the store."""
        return (await self.abatch([GetTripleOp(namespace, subject, predicate, object)]))[0]
    
    def get_triples(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str) -> Result:
        """Convenience method to get triples from the store."""
        return self.batch([GetTripleOp(namespace, subject, predicate, object)])[0]
    
    async def aget_triples(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str) -> Result:
        """Async convenience method to get triples from the store."""
        return (await self.abatch([GetTripleOp(namespace, subject, predicate, object)]))[0]

    def search_nodes(self, namespace: tuple[str, ...], properties: dict[str, Any], labels: list[str] = [], limit: int = 10) -> Result:
        """Convenience method to search for nodes in the store."""
        return self.batch([SearchNodeOp(namespace, labels, properties, limit)])[0]
    
    def search_triples(
        self, namespace: tuple[str, ...], subject: str | None = None, predicate: str | None = None, object: str | None = None, limit: int = 10
    ) -> Result:
        """Convenience method to search for triples in the store."""
        return self.batch([SearchTripleOp(namespace, subject, predicate, object, limit)])[0]
    
    async def asearch_triples(
        self, 
        namespace: tuple[str, ...], 
        subject: str | None = None, 
        predicate: str | None = None, 
        object: str | None = None, 
        limit: int = 10
    ) -> Result:
        """Async convenience method to search for triples in the store."""
        return (await self.abatch([SearchTripleOp(namespace, subject, predicate, object, limit)]))[0]
    
    def delete_node(self, namespace: tuple[str, ...], node_id: str, labels: list[str] = [], detach: bool = False):
        """Convenience method to delete a node from the store."""
        return self.batch([DeleteNodeOp(namespace, node_id, labels, detach)])[0]
    
    async def adelete_node(self, namespace: tuple[str, ...], node_id: str, labels: list[str] = [], detach: bool = False):
        """Async convenience method to delete a node from the store."""
        return (await self.abatch([DeleteNodeOp(namespace, node_id, labels, detach)]))[0]
    
    def delete_triple(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str):
        """Convenience method to delete a triple from the store."""
        return self.batch([DeleteTripleOp(namespace, subject, predicate, object)])[0]

    async def adelete_triple(self, namespace: tuple[str, ...], subject: str, predicate: str, object: str):
        """Async convenience method to delete a triple from the store."""
        return (await self.abatch([DeleteTripleOp(namespace, subject, predicate, object)]))[0]
    
    # vector search
    
    def search_nodes_by_embedding(self, query: str, indexName: str, top_k: int = 5) -> list[tuple[Node, float]]:
        """Search for nodes by vector similarity using a pre-existing vector index."""
        if not self.embeddings:
            raise ValueError("No embeddings model configured")

        query_vector = self.embeddings.embed_query(query)

        cypher = """
        CALL db.index.vector.queryNodes($indexName, $topK, $queryVector)
        YIELD node, score
        RETURN node, score
        """

        with self.driver.session(database=self.database) as session:
            results = session.run(cypher,indexName=indexName, topK=top_k, queryVector=query_vector)
            return [
                (Node.from_record(dict(record["node"])), record["score"]) for record in results
            ]
        
    async def asearch_nodes_by_embedding(self, query: str, index_name: str, top_k: int = 5) -> list[tuple[Node, float]]:
        """Async search for nodes by vector similarity."""
        if not self.embeddings:
            raise ValueError("No embeddings model configured")

        query_vector = self.embeddings.embed_query(query)

        cypher = """
            CALL db.index.vector.queryNodes($indexName, $topK, $queryVector)
            YIELD node, score
            RETURN node, score
        """

        async with self.async_driver.session(database=self.database) as session:
            result = await session.run(cypher, indexName=index_name, topK=top_k, queryVector=query_vector)
            records = [rec async for rec in result]
            return [
                (Node.from_record(dict(record["node"])), record["score"]) 
                for record in records
            ]

    def create_vector_index(
    self,
    index_name: str,
    label: str,
    property_name: str = "embedding",
    similarity_function: Literal["cosine", "euclidean", "dot"] = "cosine"
    ):
        """
        Create a vector index in Neo4j for similarity search.
        """

        query = """
        CALL db.index.vector.createNodeIndex(
            $index_name,
            $label,
            $property_name,
            $embedding_dims,
            $similarity_function
        )
        """
        
        params = {
            "index_name": index_name,
            "label": label,
            "property_name": property_name,
            "embedding_dims": self.embedding_dims,
            "similarity_function": similarity_function.lower()
        }

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params)
                record = result.single()
                summary = result.consume()
                
                return {
                    "index_name": index_name,
                    "success": True,
                    "result": dict(record) if record else None
                }
        except Exception as e:
            return { 
                "index_name": index_name,
                "success": False,
                "error": str(e),
                "result": None
            }

    def list_vector_indexes(self):
        """
        List all vector indexes in the database.
        """
        query = """
        SHOW INDEXES
        YIELD name, type, labelsOrTypes, properties, options
        WHERE type = 'VECTOR'
        RETURN name, labelsOrTypes, properties, options
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def drop_vector_index(self, index_name: str):
        """Drop a vector index by name."""

        query = """
        DROP INDEX $index_name IF EXISTS
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, index_name=index_name)
                summary = result.consume()
                
                return {
                    "success": True,
                    "index_name": index_name,
                    "indexes_removed": summary.counters.indexes_removed,
                    "message": f"Index '{index_name}' dropped successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "index_name": index_name,
                "error": str(e)
            }

    def load_from_turtle(self, file_path: str):
        """
        Load a graph from a Turtle file into Neo4j using n10s.

        This method requires the Neosemantics (n10s) plugin to be installed in Neo4j.

        Args:
            file_path (str): The absolute path to the Turtle (.ttl) file.

        Returns:
            dict: A dictionary containing the results of the import operation.
        """
        # The n10s procedure requires a 'file:///' URI.
        # We'll convert the local path to the correct format.
        absolute_file_path = os.path.abspath(file_path)
        file_uri = f"file:///{absolute_file_path.replace(os.path.sep, '/')}"

        query = """
        CALL n10s.rdf.import.fetch($file_uri, 'Turtle')
        YIELD terminationStatus, triplesLoaded, triplesParsed, extraInfo
        RETURN terminationStatus, triplesLoaded, triplesParsed, extraInfo
        """

        params = {"file_uri": file_uri}

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    return dict(record)
                return {"error": "Import procedure did not return any results."}
        except Exception as e:
            # This can happen if n10s is not installed or if there's a file access issue.
            return {"error": str(e)}
        
    def query(self, query: Any, params: dict = {}):
        # show warning of dangerous operation
        warnings.warn('Dangerous operation')
        try: 
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params)
                return [dict(record) for record in result]
        except Exception as e:
            return {"error": str(e)}
    
    # TODO:
    #   - BULK import
    #   - methods to load knowledge graphs from ohter formats like ttl or json
    #   - Import from turtle or jsonld files
