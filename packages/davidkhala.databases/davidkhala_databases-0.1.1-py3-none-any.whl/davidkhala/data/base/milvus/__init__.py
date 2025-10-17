from typing import TypedDict, Optional, Literal

import pandas as pd
from pymilvus import MilvusClient, model, CollectionSchema, FieldSchema, DataType


class Field(TypedDict):
    field_id: int
    name: str
    description: str
    type: type
    params: dict
    is_primary: Optional[bool]
    functions: list
    aliases: list
    collection_id: int
    consistency_level: int
    properties: dict
    num_partitions: int
    enable_dynamic_field: bool
    created_timestamp: int
    update_timestamp: int


class Collection(TypedDict):
    collection_name: str
    auto_id: bool
    num_shards: int
    description: str
    fields: list[Field]

def vector_field_of(c:Collection):
    v = next((f for f in c['fields'] if f['type'] in [DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR]), None)
    assert v is not None
    return v

def dimension_of(c: Collection):
    v = vector_field_of(c)
    return v['params']['dim']


def empty_schema(index_column='id', index_type: Literal[DataType.INT64, DataType.VARCHAR] = DataType.INT64,
                 **kwargs) -> CollectionSchema:
    kwargs["enable_dynamic_field"] = True  # no schema enforce
    return CollectionSchema([
        FieldSchema(name=index_column, dtype=index_type, is_primary=True, auto_id=index_type == DataType.INT64),
    ], **kwargs)


class Client:
    def __init__(self, client: MilvusClient):
        self.client = client
        self.embedding_fn = model.DefaultEmbeddingFunction()  # small embedding model "paraphrase-albert-small-v2"

    def get_collection(self, collection_name: str) -> Collection:
        return self.client.describe_collection(collection_name)

    def disconnect(self):
        self.client.close()

    def create_collection(self, collection_name: str,
                          *,
                          schema: CollectionSchema = None,
                          dimension: int = None
                          ):
        if not self.client.has_collection(collection_name):
            if schema:
                self.client.create_collection(collection_name, schema=schema)
            else:
                if not dimension:
                    dimension = self.embedding_fn.dim
                self.client.create_collection(collection_name, dimension)
        return self.get_collection(collection_name)

    def list_collections(self) -> list[str]:
        return self.client.list_collections()

    def insert_dataframe(self, collection_name: str, df: pd.DataFrame):
        self.client.insert(collection_name, df.to_dict(orient="records"))
