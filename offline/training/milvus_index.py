from typing import Any

import numpy as np
from pymilvus import DataType, MilvusClient


def create_item_collection(
    uri: str,
    dimension: int,
    collection_name: str = "item_vectors",
) -> None:
    client = MilvusClient(uri=uri)
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("item_id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dimension)
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="FLAT",
        metric_type="IP",
    )
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params,
    )
    client.close()


def insert_item_embeddings(
    uri: str,
    collection_name: str,
    item_ids: list[int],
    vectors: np.ndarray,
    batch_size: int = 2000,
) -> int:
    client = MilvusClient(uri=uri)
    vectors = np.asarray(vectors, dtype=np.float32)
    total = 0
    for start in range(0, len(item_ids), batch_size):
        end = start + batch_size
        batch = [
            {"item_id": int(item_id), "vector": vectors[index].tolist()}
            for index, item_id in enumerate(item_ids[start:end], start=start)
        ]
        client.insert(collection_name=collection_name, data=batch)
        total += len(batch)
    client.close()
    return total


def search_similar_items(
    uri: str,
    collection_name: str,
    query_vector: np.ndarray,
    limit: int = 20,
) -> list[dict[str, Any]]:
    client = MilvusClient(uri=uri)
    client.load_collection(collection_name)
    results = client.search(
        collection_name=collection_name,
        data=[np.asarray(query_vector, dtype=np.float32).tolist()],
        limit=limit,
        output_fields=["item_id"],
    )
    client.close()
    return [
        {"item_id": int(hit["item_id"]), "score": float(hit["distance"])}
        for hit in results[0]
    ]
