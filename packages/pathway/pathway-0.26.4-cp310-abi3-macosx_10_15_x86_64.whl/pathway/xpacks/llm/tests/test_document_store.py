# Copyright © 2024 Pathway

from __future__ import annotations

import asyncio
import pathlib

import pytest

import pathway as pw
from pathway.engine import BruteForceKnnMetricKind
from pathway.stdlib.indexing import (
    BruteForceKnnFactory,
    HybridIndexFactory,
    LshKnnFactory,
    TantivyBM25Factory,
    UsearchKnnFactory,
)
from pathway.tests.utils import assert_table_equality
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.servers import DocumentStoreServer
from pathway.xpacks.llm.tests import mocks


class DebugStatsInputSchema(DocumentStore.StatisticsQuerySchema):
    debug: str | None = pw.column_definition(default_value=None)


def _test_vs(fake_embeddings_model):
    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )
    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    info_queries = pw.debug.table_from_rows(
        schema=DebugStatsInputSchema,
        rows=[
            (None,),
        ],
    ).select()

    info_outputs = vector_server.statistics_query(info_queries)
    assert_table_equality(
        info_outputs.select(result=pw.unwrap(pw.this.result["file_count"].as_int())),
        pw.debug.table_from_markdown(
            """
            result
            1
            """
        ),
    )

    input_queries = pw.debug.table_from_rows(
        schema=DocumentStore.InputsQuerySchema,
        rows=[
            (None, "**/*.py", False),
        ],
    )

    input_outputs = vector_server.inputs_query(input_queries)

    @pw.udf
    def get_file_name(result_js) -> str:
        if len(result_js):
            return result_js[0]["path"].value.split("/")[-1].replace('"', "")
        else:
            return str(result_js)

    assert_table_equality(
        input_outputs.select(result=pw.unwrap(get_file_name(pw.this.result))),
        pw.debug.table_from_markdown(
            """
            result
            test_vector_store.py
            """
        ),
    )

    _, rows = pw.debug.table_to_dicts(input_outputs)
    (val,) = rows["result"].values()
    val = val[0]  # type: ignore

    assert isinstance(val, pw.Json)
    input_result = val.value
    assert isinstance(input_result, dict)

    assert "path" in input_result.keys()

    # parse_graph.G.clear()
    retrieve_queries = pw.debug.table_from_markdown(
        """
        query | k | metadata_filter | filepath_globpattern
        "Foo" | 1 |                 |
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.value  # type: ignore # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["dist"] < 1.0e-6  # type: ignore # the dist is not 0 due to float normalization
    assert query_result["text"]  # just check if some text was returned


def test_sync_embedder():
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    _test_vs(fake_embeddings_model)


def test_async_embedder():
    @pw.udf
    async def fake_embeddings_model(x: str) -> list[float]:
        asyncio.sleep
        return [1.0, 1.0, 0.0]

    _test_vs(fake_embeddings_model)


@pytest.mark.parametrize(
    "glob_filter",
    [
        "",
        "**/*.py",
        "pathway/xpacks/llm/tests/test_vector_store.py",
    ],
)
@pytest.mark.parametrize(
    "index_cls",
    [
        BruteForceKnnFactory,
        UsearchKnnFactory,
        TantivyBM25Factory,
        LshKnnFactory,
    ],
)
def test_vectorstore_glob_filtering(glob_filter, index_cls):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    if index_cls == TantivyBM25Factory:
        index_factory = index_cls()
    else:
        index_factory = index_cls(
            dimensions=3,
            embedder=fake_embeddings_model,
        )

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_markdown(
        f"""
        query  | k | metadata_filter | filepath_globpattern
        "test" | 1 |                 | {glob_filter}
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["dist"] < 1.0e-6  # type: ignore # the dist is not 0 due to float normalization
    assert query_result["text"]  # just check if some text was returned


@pytest.mark.parametrize(
    "glob_filter",
    [
        "**/abc.py",
    ],
)
@pytest.mark.parametrize(
    "index_cls",
    [
        TantivyBM25Factory,
    ],
)
def test_vectorstore_tantivy_negative_glob_filtering(glob_filter, index_cls):
    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    index_factory = index_cls()

    doc_store = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_markdown(
        f"""
        query  | k | metadata_filter | filepath_globpattern
        "test" | 1 |                 | {glob_filter}
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = doc_store.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    assert len(val.as_list()) == 0


@pytest.mark.parametrize(
    "glob_filter",
    [
        "",
        "**/*.py",
        "pathway/xpacks/llm/tests/test_vector_store.py",
    ],
)
@pytest.mark.parametrize(
    "index_cls1",
    [
        BruteForceKnnFactory,
        UsearchKnnFactory,
        TantivyBM25Factory,
        LshKnnFactory,
    ],
)
@pytest.mark.parametrize(
    "index_cls2",
    [
        UsearchKnnFactory,
        TantivyBM25Factory,
    ],
)
def test_hybrid_docstore_glob_filtering(glob_filter, index_cls1, index_cls2):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    vector_index_construct_args = dict(embedder=fake_embeddings_model)

    index1_args = {}
    index2_args = {}

    if index_cls1 != TantivyBM25Factory:
        index1_args = vector_index_construct_args

    if index_cls2 != TantivyBM25Factory:
        index2_args = vector_index_construct_args

    index1 = index_cls1(**index1_args)
    index2 = index_cls2(**index2_args)

    index_factory = HybridIndexFactory(retriever_factories=[index1, index2])

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_markdown(
        f"""
        query  | k | metadata_filter | filepath_globpattern
        "test" | 1 |                 | {glob_filter}
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["dist"] < 1.0e-6  # type: ignore
    assert query_result["text"]  # just check if some text was returned


@pytest.mark.parametrize(
    "glob_filter",
    [
        "**/*xyz.py",
        "pathway/xpacks/llm/tests/abc.py",
    ],
)
@pytest.mark.parametrize(
    "index_cls1",
    [
        BruteForceKnnFactory,
        UsearchKnnFactory,
        TantivyBM25Factory,
        LshKnnFactory,
    ],
)
@pytest.mark.parametrize(
    "index_cls2",
    [
        UsearchKnnFactory,
        TantivyBM25Factory,
    ],
)
def test_hybrid_docstore_glob_filtering_negative(glob_filter, index_cls1, index_cls2):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    vector_index_construct_args = dict(embedder=fake_embeddings_model)

    index1_args = {}
    index2_args = {}

    if index_cls1 != TantivyBM25Factory:
        index1_args = vector_index_construct_args

    if index_cls2 != TantivyBM25Factory:
        index2_args = vector_index_construct_args

    index1 = index_cls1(**index1_args)
    index2 = index_cls2(**index2_args)

    index_factory = HybridIndexFactory(retriever_factories=[index1, index2])

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_markdown(
        f"""
        query  | k | metadata_filter | filepath_globpattern
        "test" | 1 |                 | {glob_filter}
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)

    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    assert len(val.as_list()) == 0


@pytest.mark.parametrize(
    "glob_filter",
    [
        "somefile.pdf",
        "**/*.txt",
        "pathway/test_vector_store.py",
        "src.py",
        "`pathway/xpacks/llm/tests/test_vector_store.py`",
    ],
)
def test_vs_filtering_negatives(glob_filter):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    # parse_graph.G.clear()
    retrieve_queries = pw.debug.table_from_markdown(
        f"""
        query | k | metadata_filter | filepath_globpattern
        "Foo" | 1 |                 | {glob_filter}
        """,
        schema=DocumentStore.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)

    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    assert len(val.as_list()) == 0


@pytest.mark.parametrize(
    "metadata_filter",
    [
        "",
        "contains(path, `test_vector_store`)",
        'contains(path, `"test_vector_store"`)',
        "contains(path, `pathway/xpacks/llm/tests/test_vector_store.py`)",
        "path == `pathway/xpacks/llm/tests/test_vector_store.py`",
        "globmatch(`pathway/xpacks/llm/tests/test_vector_store.py`, path)",
    ],
)
def test_vs_filtering_metadata(metadata_filter):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, metadata_filter, None)],
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["dist"] < 1.0e-6  # type: ignore # the dist is not 0 due to float normalization
    assert query_result["text"]  # just check if some text was returned


@pytest.mark.parametrize(
    "metadata_filter",
    [
        "",
        "contains(path, `Document Enregistrement Universel 2023 publié à l'XYZ le 28 février 2024.pdf`)",
        "path == `Document Enregistrement Universel 2023 publié à l'XYZ le 28 février 2024.pdf`",
        'path == "`Document Enregistrement Universel 2023 publié à l\'XYZ le 28 février 2024.pdf"`',
        "contains(path, `Document Enregistrement`)",
    ],
)
@pytest.mark.parametrize("globbing_filter", [None, "*.pdf"])
def test_vs_filtering_edge_cases(metadata_filter, globbing_filter):
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {
                    "path": "Document Enregistrement Universel 2023 publié à l'XYZ le 28 février 2024.pdf"
                },
            )
        ],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, metadata_filter, globbing_filter)],
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["text"]  # just check if some text was returned


@pytest.mark.parametrize(
    "cache_strategy_cls",
    [
        None,
        pw.udfs.InMemoryCache,
        pw.udfs.DiskCache,
    ],
)
def test_docstore_server_hybridindex_builds(cache_strategy_cls, tmp_path: pathlib.Path):
    if cache_strategy_cls is not None:
        cache_strategy = cache_strategy_cls()
    else:
        cache_strategy = None

    persistent_storage_path = tmp_path / "PStorage"
    persistence_config = pw.persistence.Config.simple_config(
        pw.persistence.Backend.filesystem(persistent_storage_path),
    )

    @pw.udf(cache_strategy=cache_strategy)
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )
    vector_index = UsearchKnnFactory(
        embedder=fake_embeddings_model, reserved_space=40, dimensions=3
    )
    bm25 = TantivyBM25Factory()

    hybrid_index = HybridIndexFactory([vector_index, bm25])

    document_store = DocumentStore(docs, retriever_factory=hybrid_index)

    DocumentStoreServer(host="0.0.0.0", port=8000, document_store=document_store)
    # server is not run, so host/port don't matter
    # it is just used to check if it is created correctly

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, None, None)],
    )

    retrieve_outputs = document_store.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(
        retrieve_outputs, persistence_config=persistence_config
    )
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["text"]  # just check if some text was returned


def test_docstore_on_table_without_metadata():
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes),
        rows=[("test".encode("utf-8"),)],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    document_store = DocumentStore(docs, retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, None, None)],
    )

    retrieve_outputs = document_store.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["text"] == "test"  # just check if some text was returned


def test_docstore_on_tables_with_different_schemas():
    @pw.udf
    def fake_embeddings_model(x: str) -> list[float]:
        return [1.0, 1.0, 0.0]

    docs1 = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes),
        rows=[("test".encode("utf-8"),)],
    )

    docs2 = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict, val=int),
        rows=[("test2".encode("utf-8"), {}, 1)],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    document_store = DocumentStore([docs1, docs2], retriever_factory=index_factory)

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 2, None, None)],
    )

    retrieve_outputs = document_store.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    assert len(val.as_list()) == 2


def test_docstore_post_processor():

    def add_baz(text: str, metadata: dict) -> tuple:
        return (text + "baz", metadata)

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"foo": "bar"},
            )
        ],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=mocks.fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(
        docs, retriever_factory=index_factory, doc_post_processors=[add_baz]
    )

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, None, None)],
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["text"] == "testbaz"


def test_docstore_metadata_post_processor():

    def add_id(text: str, metadata: dict) -> tuple:
        metadata["id"] = 1
        return (text, metadata)

    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"foo": "bar"},
            )
        ],
    )

    index_factory = BruteForceKnnFactory(
        dimensions=3,
        reserved_space=10,
        embedder=mocks.fake_embeddings_model,
        metric=BruteForceKnnMetricKind.COS,
    )

    vector_server = DocumentStore(
        docs, retriever_factory=index_factory, doc_post_processors=[add_id]
    )

    retrieve_queries = pw.debug.table_from_rows(
        schema=DocumentStore.RetrieveQuerySchema,
        rows=[("Foo", 1, None, None)],
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.as_list()  # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["metadata"]["id"] == 1
