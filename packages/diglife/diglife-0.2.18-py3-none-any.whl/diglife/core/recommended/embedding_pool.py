
import qdrant_client
from qdrant_client import QdrantClient, models
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.core import Document
from .embedding_model import VolcanoEmbedding
from diglife import logger

from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

import os


class EmbeddingPool:
    def __init__(self):
        self.reload()

    def create_collection(
        self, collection_name: str, vector_dimension: str = 2560
    ):
        distance_metric = models.Distance.COSINE  # 使用余弦相似度

        # 2. 定义 Collection 参数

        client = qdrant_client.QdrantClient(
            host=os.getenv("host", "localhost"),
            port=os.getenv("port", 6333) 
        )

        # 3. 创建 Collection (推荐使用 recreate_collection)
        try:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dimension, distance=distance_metric
                ),
            )
        except Exception as e:
            raise Exception("创建collection失败") from e
        finally:
            client.close()

    def reload(self):
        logger.info("reload")
        # 默认仓库要被创建的
        self.postprocess = SimilarityPostprocessor(
            similarity_cutoff=float(os.getenv("similarity_cutoff", 0.5))
        )
        client = qdrant_client.QdrantClient(
            host=os.getenv("host", "localhost"), 
            port=os.getenv("port", 6333) 
        )
        vector_store = QdrantVectorStore(
            client=client, collection_name=os.getenv("collection_name", "diglife")
        )
        self.embed_model = VolcanoEmbedding(
            model_name=os.getenv("model_name", "doubao-embedding-text-240715"),
            api_key=os.getenv("api_key", ""),
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store, embed_model=self.embed_model
        )
        """
            # TODO add more operators
            EQ = "=="  # default operator (string, int, float)
            GT = ">"  # greater than (int, float)
            LT = "<"  # less than (int, float)
            NE = "!="  # not equal to (string, int, float)
            GTE = ">="  # greater than or equal to (int, float)
            LTE = "<="  # less than or equal to (int, float)
            IN = "in"  # In array (string or number)
            NIN = "nin"  # Not in array (string or number)
            ANY = "any"  # Contains any (array of strings)
            ALL = "all"  # Contains all (array of strings)
            TEXT_MATCH = "text_match"  # full text match (allows you to search for a specific substring, token or phrase within the text field)
            TEXT_MATCH_INSENSITIVE = (
                "text_match_insensitive"  # full text match (case insensitive)
            )
            CONTAINS = "contains"  # metadata array contains value (string or number)
            IS_EMPTY = "is_empty"  # the field is not exist or empty (null or empty array)

        """
        filters_bac = MetadataFilters(
            filters=[MetadataFilter(key="type", value=1, operator=FilterOperator.LTE)]
        )

        self.retriver_bac = self.index.as_retriever(
            filters=filters_bac, similarity_top_k=int(os.getenv("similarity_top_k", 10))
        )

        filters_figure_person = MetadataFilters(
            filters=[MetadataFilter(key="type", value=2, operator=FilterOperator.EQ)]
        )

        self.retriver_figure_person = self.index.as_retriever(
            filters=filters_figure_person,
            similarity_top_k=int(os.getenv("similarity_top_k", 10)),
        )


    def update(self, text: str, id: str, type: int) -> str:
        doc = Document(
            text=text,
            id_=id,
            metadata={"type": type, "id": id},
            excluded_embed_metadata_keys=["type", "id"],
        )
        self.index.update(document=doc)

    def delete(self, id: str):
        logger.info("delete")
        # 2025-09-18 10:37:32,238 - 警告 - llama_index.core.indices.base - base：310 - delete() 方法现已弃用，请使用 delete_ref_doc() 删除已导入的文档和节点，或使用 delete_nodes 删除节点列表。如需异步实现，请使用 delete_ref_docs() 。
        self.index.delete(doc_id=id)

    def search_bac(self, query: str) -> str:
        results = self.retriver_bac.retrieve(query)
        output = []
        for i, result in enumerate(results):
            dct = result.node.metadata
            dct.update({"order": i})
            output.append(dct)

        return output

    def search_figure_person(self, query: str) -> str:
        results = self.retriver_figure_person.retrieve(query)
        output = []
        for i, result in enumerate(results):
            dct = result.node.metadata
            dct.update({"order": i})
            output.append(dct)

        return output

