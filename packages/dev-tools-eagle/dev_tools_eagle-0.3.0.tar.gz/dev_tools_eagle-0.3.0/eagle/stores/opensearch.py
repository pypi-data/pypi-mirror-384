from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import  Any, Iterable, List, Optional, Dict
from langchain_community.query_constructors.opensearch import OpenSearchTranslator
from langchain_community.vectorstores.opensearch_vector_search import (
    SCRIPT_SCORING_SEARCH,
    PAINLESS_SCRIPTING_SEARCH,
    MATCH_ALL_QUERY,
    _approximate_search_query_with_boolean_filter,
    _approximate_search_query_with_efficient_filter,
    _default_approximate_search_query,
    _default_script_query,
    _default_painless_scripting_query,
    _is_aoss_enabled,
    _validate_aoss_with_engines,
    _default_text_mapping,
    _default_scripting_text_mapping,
)
import warnings
from langgraph.store.base import (
    GetOp,
    IndexConfig,
    Item,
    ListNamespacesOp,
    MatchCondition,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
    ensure_embeddings,
    get_text_at_path,
    tokenize_path,
)
from langchain_community.vectorstores.opensearch_vector_search import (
    _is_aoss_enabled,
    _validate_aoss_with_engines,
    _default_text_mapping,
    _default_scripting_text_mapping,
)
from langchain.chains.query_constructor.ir import (
    Comparator,
    Operator
)
from langchain_core.structured_query import (
    Comparison
)

from langchain.chains.query_constructor.base import AttributeInfo
from langchain_community.vectorstores.opensearch_vector_search import _get_opensearch_client, _get_async_opensearch_client
from opensearchpy import AsyncOpenSearch, OpenSearch
from contextlib import AbstractAsyncContextManager
from eagle.utils.stores import translate_to_structured_query
from eagle.stores.base import EagleBaseStore, SearchOp

# Constants

ALLOWED_COMPARATORS = tuple(Comparator)
ALLOWED_OPERATORS = tuple(Operator)

# OpenSearchTranslator modified
class OpenSearchTranslatorModified(OpenSearchTranslator):

    def visit_comparison(self, comparison: Comparison) -> Dict:
        field = f"metadata.{comparison.attribute}"

        if comparison.comparator in [
            Comparator.LT,
            Comparator.LTE,
            Comparator.GT,
            Comparator.GTE,
        ]:
            if isinstance(comparison.value, dict):
                if "date" in comparison.value:
                    return {
                        "range": {
                            field: {
                                self._format_func(
                                    comparison.comparator
                                ): comparison.value["date"]
                            }
                        }
                    }
            else:
                return {
                    "range": {
                        field: {
                            self._format_func(comparison.comparator): comparison.value
                        }
                    }
                }

        if comparison.comparator == Comparator.LIKE:
            return {
                self._format_func(comparison.comparator): {
                    field: {"value": comparison.value}
                }
            }

        if isinstance(comparison.value, dict):
            if "date" in comparison.value:
                comparison.value = comparison.value["date"]

        return {self._format_func(comparison.comparator): {field: comparison.value}}

# Auxiliar functions

def translate_query(
    query: str,
    filter: str,
    limit: int,
    attribute_info: list
):
    
    return translate_to_structured_query(
        query=query,
        filter_as_str=filter,
        limit=limit,
        translator=OpenSearchTranslatorModified(),
        attribute_info=attribute_info,
        allowed_comparators=ALLOWED_COMPARATORS,
        allowed_operators=ALLOWED_OPERATORS
    )
    
def _apply_operator(value: Any, operator: str, op_value: Any) -> bool:
    """Apply a comparison operator, matching PostgreSQL's JSONB behavior."""
    if operator == "$eq":
        return value == op_value
    elif operator == "$gt":
        return float(value) > float(op_value)
    elif operator == "$gte":
        return float(value) >= float(op_value)
    elif operator == "$lt":
        return float(value) < float(op_value)
    elif operator == "$lte":
        return float(value) <= float(op_value)
    elif operator == "$ne":
        return value != op_value
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def _compare_values(item_value: Any, filter_value: Any) -> bool:
    """Compare values in a JSONB-like way, handling nested objects."""
    if isinstance(filter_value, dict):
        if any(k.startswith("$") for k in filter_value):
            return all(
                _apply_operator(item_value, op_key, op_value)
                for op_key, op_value in filter_value.items()
            )
        if not isinstance(item_value, dict):
            return False
        return all(
            _compare_values(item_value.get(k), v) for k, v in filter_value.items()
        )
    elif isinstance(filter_value, (list, tuple)):
        return (
            isinstance(item_value, (list, tuple))
            and len(item_value) == len(filter_value)
            and all(_compare_values(iv, fv) for iv, fv in zip(item_value, filter_value))
        )
    else:
        return item_value == filter_value

def _create_mapping(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Cria um mapping para um índice no OpenSearch com base nos metadados fornecidos.
    Aplica o tratamento recursivamente para strings como keyword em todos os níveis.

    Args:
        metadata: Dicionário com os metadados a serem mapeados.
    """
    def process_value(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            return {"type": "keyword"}
        elif isinstance(value, int):
            # Treat long as long and integer as integer
            if value > 2147483647 or value < -2147483648:
                return {"type": "long"}
            else:
                return {"type": "integer"}  # Garante que inteiros sejam mapeados corretamente
        elif isinstance(value, float):
            return {"type": "float"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value) and value:
                # Lista de dicionários
                return {
                    "type": "nested",
                    "properties": process_dict(value[0])  # Assume estrutura consistente
                }
            else:
                return {"type": "keyword"}  # Lista de valores simples
        elif isinstance(value, dict):
            return {"type": "object", "properties": process_dict(value)}
        else:
            return {"type": "keyword"}  # Fallback para tipos desconhecidos

    def process_dict(data: dict[str, Any]) -> dict[str, Any]:
        return {key: process_value(val) for key, val in data.items()}

    # Processa os metadados recursivamente
    properties = process_dict(metadata)

    return {
        "properties": {
            "metadata": {
                "properties": properties
            }
        }
    }

def _raw_similarity_search_with_score_by_vector(
    embedding: List[float],
    k: int = 4,
    score_threshold: Optional[float] = 0.0,
    is_aoss: bool = False,
    engine: str = "nmslib",
    **kwargs: Any,
) -> List[dict]:
    """Return raw opensearch documents (dict) including vectors,
    scores most similar to the embedding vector.

    By default, supports Approximate Search.
    Also supports Script Scoring and Painless Scripting.

    Args:
        embedding: Embedding vector to look up documents similar to.
        k: Number of Documents to return. Defaults to 4.
        score_threshold: Specify a score threshold to return only documents
        above the threshold. Defaults to 0.0.

    Returns:
        List of dict with its scores most similar to the embedding.

    Optional Args:
        same as `similarity_search`
    """
    k = min(k, 10000)
    search_type = kwargs.get("_search_type", "approximate_search")
    vector_field = kwargs.get("vector_field", "vector_field")
    filter = kwargs.get("filter", {})

    if (
        is_aoss
        and search_type != "approximate_search"
        and search_type != SCRIPT_SCORING_SEARCH
    ):
        raise ValueError(
            "Amazon OpenSearch Service Serverless only "
            "supports `approximate_search` and `script_scoring`"
        )

    if search_type == "approximate_search":
        boolean_filter = kwargs.get("boolean_filter", {})
        subquery_clause = kwargs.get("subquery_clause", "must")
        efficient_filter = kwargs.get("efficient_filter", {})
        # `lucene_filter` is deprecated, added for Backwards Compatibility
        lucene_filter = kwargs.get("lucene_filter", {})

        if boolean_filter != {} and efficient_filter != {}:
            raise ValueError(
                "Both `boolean_filter` and `efficient_filter` are provided which "
                "is invalid"
            )

        if lucene_filter != {} and efficient_filter != {}:
            raise ValueError(
                "Both `lucene_filter` and `efficient_filter` are provided which "
                "is invalid. `lucene_filter` is deprecated"
            )

        if lucene_filter != {} and boolean_filter != {}:
            raise ValueError(
                "Both `lucene_filter` and `boolean_filter` are provided which "
                "is invalid. `lucene_filter` is deprecated"
            )

        if (
            efficient_filter == {}
            and boolean_filter == {}
            and lucene_filter == {}
            and filter != {}
        ):
            if engine in ["faiss", "lucene"]:
                efficient_filter = filter
            else:
                boolean_filter = filter

        if boolean_filter != {}:
            search_query = _approximate_search_query_with_boolean_filter(
                embedding,
                boolean_filter,
                k=k,
                vector_field=vector_field,
                subquery_clause=subquery_clause,
                score_threshold=score_threshold,
            )
        elif efficient_filter != {}:
            search_query = _approximate_search_query_with_efficient_filter(
                embedding,
                efficient_filter,
                k=k,
                vector_field=vector_field,
                score_threshold=score_threshold,
            )
        elif lucene_filter != {}:
            warnings.warn(
                "`lucene_filter` is deprecated. Please use the keyword argument"
                " `efficient_filter`"
            )
            search_query = _approximate_search_query_with_efficient_filter(
                embedding,
                lucene_filter,
                k=k,
                vector_field=vector_field,
                score_threshold=score_threshold,
            )
        else:
            search_query = _default_approximate_search_query(
                embedding,
                k=k,
                vector_field=vector_field,
                score_threshold=score_threshold,
            )
    elif search_type == SCRIPT_SCORING_SEARCH:
        space_type = kwargs.get("space_type", "l2")
        pre_filter = kwargs.get("pre_filter", MATCH_ALL_QUERY)
        search_query = _default_script_query(
            embedding,
            k,
            space_type,
            pre_filter,
            vector_field,
            score_threshold=score_threshold,
        )
    elif search_type == PAINLESS_SCRIPTING_SEARCH:
        space_type = kwargs.get("space_type", "l2Squared")
        pre_filter = kwargs.get("pre_filter", MATCH_ALL_QUERY)
        search_query = _default_painless_scripting_query(
            embedding,
            k,
            space_type,
            pre_filter,
            vector_field,
            score_threshold=score_threshold,
        )
    else:
        raise ValueError("Invalid `search_type` provided as an argument")
    
    return search_query

def create_index(client: OpenSearch, index_name: str, dimension: int, metadata_example: dict, **kwargs: Any) -> None:
    """Create an OpenSearch index with the specified configuration."""
    number_of_shards = kwargs.get("number_of_shards", 1)
    number_of_replicas = kwargs.get("number_of_replicas", 1)

    is_appx_search = kwargs.get("is_appx_search", True)
    vector_field = kwargs.get("vector_field", "vector_field")
    kwargs.get("text_field", "text")
    http_auth = kwargs.get("http_auth")
    is_aoss = _is_aoss_enabled(http_auth=http_auth)

    if is_aoss and not is_appx_search:
        raise ValueError(
            "Amazon OpenSearch Service Serverless only "
            "supports `approximate_search`"
        )

    if is_appx_search:
        engine = kwargs.get("engine", "nmslib")
        space_type = kwargs.get("space_type", "l2")
        ef_search = kwargs.get("ef_search", 512)
        ef_construction = kwargs.get("ef_construction", 512)
        m = kwargs.get("m", 16)

        _validate_aoss_with_engines(is_aoss, engine)

        mapping = _default_text_mapping(
            dimension,
            engine,
            space_type,
            ef_search,
            ef_construction,
            m,
            vector_field,
        )
    else:
        mapping = _default_scripting_text_mapping(dimension)
    
    mapping["settings"]["index"]["number_of_shards"] = number_of_shards
    mapping["settings"]["index"]["number_of_replicas"] = number_of_replicas

    if client.indices.exists(index=index_name):
        raise RuntimeError(f"The index '{index_name}' already exists.")

    client.indices.create(index=index_name, body=mapping)
    mapping = _create_mapping(metadata_example)
    client.indices.put_mapping(index=index_name, body=mapping)

class OpenSearchIndexConfig(IndexConfig):
    """Specialized IndexConfig for OpenSearch with an additional index_name parameter."""
    index_name: str
    """Name of the index to be used in OpenSearch."""
    value_example: dict[str, Any]
    """Example value to be used for mapping."""
    attribute_info: list[AttributeInfo]  # Added attribute_info for structured queries


class OpenSearchStore(EagleBaseStore, AbstractAsyncContextManager):
    """OpenSearch-backed store with optional vector search."""

    def __init__(self, *, index: Optional[OpenSearchIndexConfig] = None) -> None:
        opensearch_url = os.getenv("OPENSEARCH_HOST", "http://localhost")
        opensearch_port = os.getenv("OPENSEARCH_PORT", "9200")
        username = os.getenv("OPENSEARCH_USERNAME", None)
        password = os.getenv("OPENSEARCH_PASSWORD", None)
        general_index_prefix = os.getenv("OPENSEARCH_GENERAL_INDEX_PREFIX", "")
        use_ssl = os.getenv("OPENSEARCH_USE_SSL", "False").lower() == "true"
        verify_certs = os.getenv("OPENSEARCH_VERIFY_CERTS", "True").lower() == "true"
        ssl_assert_hostname = os.getenv("OPENSEARCH_SSL_ASSERT_HOSTNAME", "True").lower() == "true"
        ssl_show_warn = os.getenv("OPENSEARCH_SSL_SHOW_WARN", "True").lower() == "true"

        self.connection_kwargs = {
            "http_auth": (username, password) if username and password else None,
            "use_ssl": use_ssl,
            "verify_certs": verify_certs,
            "ssl_assert_hostname": ssl_assert_hostname,
            "ssl_show_warn": ssl_show_warn,
        }

        self.full_url = f"{opensearch_url}:{opensearch_port}" if opensearch_port else opensearch_url
        self.index_config = index
        if self.index_config:
            if not self.index_config['index_name']:
                raise ValueError("Index name must be provided.")
            self.index_config['index_name'] = f"{general_index_prefix}{self.index_config['index_name'].lower()}"
            self.embeddings = ensure_embeddings(self.index_config.get("embed"))
            self.index_config["__tokenized_fields"] = [
                (p, tokenize_path(p)) if p != "$" else (p, p)
                for p in (self.index_config.get("fields") or ["$"])
            ]
            # Forcefully include metadata.namespace in attribute_info
            self.index_config['attribute_info'].append(
                AttributeInfo(name="metadata.namespace", type="string", description="Namespace of the document")
            )
        else:
            self.embeddings = None

        self.namespace_field = "metadata.namespace"
        self.ttl_field = "metadata.ttl"

    def with_client(self, func, *args, **kwargs):
        """Context manager for sync client usage."""
        client = _get_opensearch_client(self.full_url, **self.connection_kwargs)
        try:
            return func(client, *args, **kwargs)
        finally:
            client.transport.close()

    async def with_async_client(self, func, *args, **kwargs):
        """Context manager for async client usage."""
        async_client = _get_async_opensearch_client(self.full_url, **self.connection_kwargs)
        try:
            return await func(async_client, *args, **kwargs)
        finally:
            await async_client.close()

    def close(self) -> None:
        """No-op: clients are closed after each use."""
        pass

    async def aclose(self) -> None:
        """No-op: clients are closed after each use."""
        pass

    async def __aenter__(self) -> OpenSearchStore:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the async context manager."""
        await self.aclose()

    def __del__(self) -> None:
        """No-op: clients are closed after each use."""
        pass

    def delete_index(self) -> None:
        """Delete the current index."""
        def _delete(client):
            if client.indices.exists(index=self.index_config['index_name']):
                client.indices.delete(index=self.index_config['index_name'])
            else:
                warnings.warn(f"The index {self.index_config['index_name']} you are trying to delete does not exist.")
        self.with_client(_delete)

    def create_index(self) -> Optional[str]:
        """Create a new Index with given arguments."""
        metadata_example = {
            "namespace": "namespace_example",
            "key": "key_example",
            "value": self.index_config['value_example'],
        }
        def _create(client):
            create_index(
                client,
                index_name=self.index_config['index_name'],
                dimension=self.index_config['dims'],
                metadata_example=metadata_example,
            )
        self.with_client(_create)

    def delete_by_namespace(self, namespace: tuple[str, ...]) -> None:
        """
        Delete all documents in the index that match the given namespace.
        """
        namespace_prefix_str = "/".join(namespace)
        query = {"query": {"prefix": {self.namespace_field: f"{namespace_prefix_str}"}}}

        def _delete_by_query(client):
            response = client.delete_by_query(
                index=self.index_config['index_name'],
                body=query,
                conflicts="proceed"
            )
            if response.get("failures"):
                raise RuntimeError(f"Failed to delete some documents: {response['failures']}")
        self.with_client(_delete_by_query)

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Interpret and execute a batch of operations."""
        def _batch(client):
            results = []
            for op in ops:
                if isinstance(op, PutOp):
                    # Handle PutOp
                    metadata = {
                        "namespace": "/".join(op.namespace),
                        "key": op.key,
                        "value": op.value,
                    }
                    doc_id = f"{metadata['namespace']}_{op.key}"
                    if op.value is None:  # Deletion
                        client.delete(index=self.index_config['index_name'], id=doc_id, ignore=[404])
                        results.append(None)
                    else:  # Insertion/Update
                        body = {"metadata": metadata}
                        if self.embeddings and op.index is not False:
                            texts_to_embed = []
                            for path, field in self.index_config["__tokenized_fields"]:
                                texts = get_text_at_path(op.value, field)
                                if texts:
                                    texts_to_embed.extend(texts)
                        if texts_to_embed:
                            body["vector_field"] = self.embeddings.embed_documents(texts_to_embed)[0]
                        client.index(index=self.index_config['index_name'], id=doc_id, body=body)
                        results.append(Item(
                            namespace=op.namespace,
                            key=op.key,
                            value=op.value,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        ))
                elif isinstance(op, GetOp):
                    # Handle GetOp
                    doc_id = f"{'/'.join(op.namespace)}_{op.key}"
                    try:
                        response = client.get(index=self.index_config['index_name'], id=doc_id)
                        doc = response["_source"]["metadata"]
                        results.append(Item(
                            namespace=tuple(doc["namespace"].split("/")),
                            key=doc["key"],
                            value=doc["value"],
                            created_at=doc.get("created_at"),
                            updated_at=doc.get("updated_at"),
                        ))
                    except Exception:
                        results.append(None)
                elif isinstance(op, SearchOp):
                    # Handle SearchOp with semantic similarity and sorting
                    namespace_prefix_str = "/".join(op.namespace_prefix)
                    namespace_query = {"prefix": {"metadata.namespace": f"{namespace_prefix_str}"}}

                    # Translate query and external filter
                    translated_query, translated_search_kwargs = translate_query(
                        query=op.query or "",
                        filter=op.filter or "NO_FILTER",
                        limit=op.limit,
                        attribute_info=self.index_config['attribute_info'],
                    )

                    # Combine namespace filter and translated filter
                    filter_query = translated_search_kwargs.pop("filter", [])
                    if not isinstance(filter_query, list):
                        filter_query = [filter_query]

                    # Semantic similarity search
                    if op.query and self.embeddings:
                        query_embedding = self.embeddings.embed_query(translated_query)
                        search_query = _raw_similarity_search_with_score_by_vector(
                            embedding=query_embedding,
                            filter={"bool": {"filter": [namespace_query] + filter_query}},
                            vector_field="vector_field",
                            **translated_search_kwargs
                        )
                        response = client.search(index=self.index_config['index_name'], body=search_query)
                    else:
                        # Fallback to regular filtering if no query is provided
                        bool_query = {"bool": {"filter": [namespace_query] + filter_query}}
                        body = {
                            "query": bool_query,
                            "size": op.limit,
                            "from": op.offset,
                        }
                        if op.sort:
                            body["sort"] = [{f"metadata.{field}": {"order": order}} for field, order in op.sort.items()]
                        response = client.search(index=self.index_config['index_name'], body=body)

                    results.append([
                        SearchItem(
                            namespace=tuple(hit["_source"]["metadata"]["namespace"].split("/")),
                            key=hit["_source"]["metadata"]["key"],
                            value=hit["_source"]["metadata"]["value"],
                            created_at=hit["_source"]["metadata"].get("created_at"),
                            updated_at=hit["_source"]["metadata"].get("updated_at"),
                            score=hit["_score"],
                        )
                        for hit in response["hits"]["hits"]
                    ])
                elif isinstance(op, ListNamespacesOp):
                    # Handle ListNamespacesOp
                    response = client.search(
                        index=self.index_config["index_name"],
                        body={"size": 0, "aggs": {"namespaces": {"terms": {"field": f"{self.namespace_field}.keyword"}}}},
                    )
                    results.append([
                        tuple(bucket["key"].split("/")) for bucket in response["aggregations"]["namespaces"]["buckets"]
                    ])
                else:
                    raise ValueError(f"Unsupported operation: {type(op)}")
            return results
        return self.with_client(_batch)

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Asynchronously interpret and execute a batch of operations."""
        async def _abatch(async_client):
            results = []
            for op in ops:
                if isinstance(op, PutOp):
                    # Handle PutOp asynchronously
                    metadata = {
                        "namespace": "/".join(op.namespace),
                        "key": op.key,
                        "value": op.value,
                    }
                    doc_id = f"{metadata['namespace']}_{op.key}"
                    if op.value is None:  # Deletion
                        await async_client.delete(index=self.index_config['index_name'], id=doc_id, ignore=[404])
                        results.append(None)
                    else:  # Insertion/Update
                        body = {"metadata": metadata}
                        if self.embeddings and op.index is not False:
                            texts_to_embed = []
                            for path, field in self.index_config["__tokenized_fields"]:
                                texts = get_text_at_path(op.value, field)
                                if texts:
                                    texts_to_embed.extend(texts)
                        if texts_to_embed:
                            body["vector_field"] = (await self.embeddings.aembed_documents(texts_to_embed))[0]
                        await async_client.index(index=self.index_config['index_name'], id=doc_id, body=body)
                        results.append(Item(
                            namespace=op.namespace,
                            key=op.key,
                            value=op.value,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        ))
                elif isinstance(op, GetOp):
                    # Handle GetOp asynchronously
                    doc_id = f"{'/'.join(op.namespace)}_{op.key}"
                    try:
                        response = await async_client.get(index=self.index_config['index_name'], id=doc_id)
                        doc = response["_source"]["metadata"]
                        results.append(Item(
                            namespace=tuple(doc["namespace"].split("/")),
                            key=doc["key"],
                            value=doc["value"],
                            created_at=doc.get("created_at"),
                            updated_at=doc.get("updated_at"),
                        ))
                    except Exception:
                        results.append(None)
                elif isinstance(op, SearchOp):
                    # Handle SearchOp with semantic similarity and sorting
                    namespace_prefix_str = "/".join(op.namespace_prefix)
                    namespace_query = {"prefix": {"metadata.namespace": f"{namespace_prefix_str}"}}

                    # Translate query and external filter
                    translated_query, translated_search_kwargs = translate_query(
                        query=op.query or "",
                        filter=op.filter or "NO_FILTER",
                        limit=op.limit,
                        attribute_info=self.index_config['attribute_info'],
                    )

                    # Combine namespace filter and translated filter
                    filter_query = translated_search_kwargs.pop("filter", [])
                    if not isinstance(filter_query, list):
                        filter_query = [filter_query]

                    # Semantic similarity search
                    if op.query and self.embeddings:
                        query_embedding = self.embeddings.embed_query(translated_query)
                        search_query = _raw_similarity_search_with_score_by_vector(
                            embedding=query_embedding,
                            filter={"bool": {"filter": [namespace_query] + filter_query}},
                            vector_field="vector_field",
                            **translated_search_kwargs
                        )
                        response = await async_client.search(index=self.index_config['index_name'], body=search_query)
                    else:
                        # Fallback to regular filtering if no query is provided
                        bool_query = {"bool": {"filter": [namespace_query] + filter_query}}
                        body = {
                            "query": bool_query,
                            "size": op.limit,
                            "from": op.offset,
                        }
                        if op.sort:
                            body["sort"] = [{f"metadata.{field}": {"order": order}} for field, order in op.sort.items()]
                        response = await async_client.search(index=self.index_config['index_name'], body=body)

                    results.append([
                        SearchItem(
                            namespace=tuple(hit["_source"]["metadata"]["namespace"].split("/")),
                            key=hit["_source"]["metadata"]["key"],
                            value=hit["_source"]["metadata"]["value"],
                            created_at=hit["_source"]["metadata"].get("created_at"),
                            updated_at=hit["_source"]["metadata"].get("updated_at"),
                            score=hit["_score"],
                        )
                        for hit in response["hits"]["hits"]
                    ])
                elif isinstance(op, ListNamespacesOp):
                    # Handle ListNamespacesOp asynchronously
                    response = await async_client.search(
                        index=self.index_config["index_name"],
                        body={"size": 0, "aggs": {"namespaces": {"terms": {"field": f"{self.namespace_field}.keyword"}}}},
                    )
                    results.append([
                        tuple(bucket["key"].split("/")) for bucket in response["aggregations"]["namespaces"]["buckets"]
                    ])
                else:
                    raise ValueError(f"Unsupported operation: {type(op)}")
            return results
        return await self.with_async_client(_abatch)