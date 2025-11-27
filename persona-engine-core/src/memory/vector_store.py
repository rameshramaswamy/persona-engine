import asyncio
from typing import List, Dict
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding,SparseTextEmbedding  # OPTIMIZATION: Rust-based embeddings
import logging
from flashrank import Ranker, RerankRequest

logger = logging.getLogger("uvicorn")

class LoreStore:
    def __init__(self, host: str = "localhost", port: int = 6333):
        # OPTIMIZATION: Connect asynchronously where possible, 
        # but Qdrant python client is sync by default for search, so we wrap it.
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "character_lore"
        
        # OPTIMIZATION: Load Multilingual model (supports EN & RU)
        # fastembed downloads quantized ONNX models automatically.
        self.embedding_model = TextEmbedding(model_name="intfloat/multilingual-e5-large")

        # Load Models (Lazy loading recommended in prod, strict here for simplicity)
        # Dense Model (Semantic)
        self.dense_model = TextEmbedding(model_name="intfloat/multilingual-e5-large")
        # Sparse Model (Keyword/BM25)
        self.sparse_model = SparseTextEmbedding(model_name="prithivida/splade-pp-e5-large") 
        self.reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")
        self._init_collection()

    def _init_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams()
                },
                # OPTIMIZATION 1: Quantization (Int8)
                # Reduces RAM by 4x. 
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                ),
                # OPTIMIZATION 2: HNSW Tuning
                # m=16, ef_construct=100 are good defaults, but we make them explicit
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10000
                )
            )
            # OPTIMIZATION: Create payload index for faster filtering by char_id
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="char_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

    async def _get_embeddings(self, text: str):
        """Generate Dense + Sparse vectors."""
        loop = asyncio.get_running_loop()
        def compute():
            dense = list(self.dense_model.embed([text]))[0]
            sparse = list(self.sparse_model.embed([text]))[0]
            return dense.tolist(), models.SparseVector(
                indices=sparse.indices.tolist(),
                values=sparse.values.tolist()
            )
        return await loop.run_in_executor(None, compute)


    async def add_lore(self, char_id: str, text: str):
        dense, sparse = await self._get_embeddings(text)
        point = models.PointStruct(
            id=models.uuid.uuid4().hex,
            vector={"dense": dense, "sparse": sparse},
            payload={"char_id": char_id, "text": text}
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])

    async def search_lore(self, char_id: str, query: str, limit: int = 3) -> str:
        """
        Flow: Hybrid Search (Retrieve 10) -> Rerank (Keep Top 3)
        """
        dense, sparse = await self._get_embeddings(query)
        search_filter = models.Filter(
            must=[models.FieldCondition(key="char_id", match=models.MatchValue(value=char_id))]
        )

        # 1. RETRIEVE (Fetch more than we need: top_k=10)
        loop = asyncio.get_running_loop()
        hits = await loop.run_in_executor(
            None, 
            lambda: self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="dense", vector=dense),
                query_filter=search_filter,
                limit=10, # Fetch candidate pool
                with_payload=True
            )
        )
        
        if not hits:
            return ""

        # 2. RERANK
        # Reranker checks the actual text relevance, fixing "vector drift"
        passages = [
            {"id": hit.id, "text": hit.payload["text"], "meta": hit.payload} 
            for hit in hits
        ]
        
        rerank_request = RerankRequest(query=query, passages=passages)
        
        # Run Rerank in executor
        ranked_results = await loop.run_in_executor(
            None, 
            lambda: self.reranker.rerank(rerank_request)
        )
        
        # 3. RETURN TOP K
        top_results = ranked_results[:limit]
        return "\n".join([f"- {res['text']}" for res in top_results])