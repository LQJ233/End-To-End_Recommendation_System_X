import tempfile
from pathlib import Path

import numpy as np
from pymilvus import MilvusClient

from training.milvus_index import (
    create_item_collection,
    insert_item_embeddings,
    search_similar_items,
)


def test_milvus_lite_item_index_can_be_searched():
    with tempfile.TemporaryDirectory() as tmp_dir:
        uri = str(Path(tmp_dir) / "milvus.db")
        create_item_collection(uri, dimension=4, collection_name="item_vectors_test")
        insert_item_embeddings(
            uri,
            collection_name="item_vectors_test",
            item_ids=[1, 2, 3],
            vectors=np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.8, 0.2, 0.0, 0.0],
                ],
                dtype=np.float32,
            ),
        )

        hits = search_similar_items(
            uri,
            collection_name="item_vectors_test",
            query_vector=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            limit=2,
        )

    assert [hit["item_id"] for hit in hits] == [1, 3]


def test_search_reloads_released_collection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        uri = str(Path(tmp_dir) / "milvus.db")
        create_item_collection(uri, dimension=2, collection_name="item_vectors_reload")
        insert_item_embeddings(
            uri,
            collection_name="item_vectors_reload",
            item_ids=[7, 8],
            vectors=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        )
        client = MilvusClient(uri=uri)
        client.release_collection("item_vectors_reload")
        client.close()

        hits = search_similar_items(
            uri,
            collection_name="item_vectors_reload",
            query_vector=np.array([1.0, 0.0], dtype=np.float32),
            limit=1,
        )

    assert hits[0]["item_id"] == 7
