
import json
from pathlib import Path
from datetime import datetime, timezone

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer


class SemanticMemory:

    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        storage_dir="data/semantic_memory"
    ):

        self.model = SentenceTransformer(model_name)

        self.dimension = self.model.get_embedding_dimension()

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.index_path = self.storage_dir / "memory.index"
        self.memory_path = self.storage_dir / "memories.json"

        self.index = faiss.IndexFlatIP(self.dimension)

        self.memories = []

        self.load_memory()

    # ---------------------------------
    # Add memory
    # ---------------------------------

    def add_memory(self, text, metadata=None):

        if not text or not text.strip():
            raise ValueError("Memory cannot be empty")

        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        embedding = self.model.encode(
            [text],
            normalize_embeddings=True
        )

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        memory_id = len(self.memories) + 1

        memory = {
            "id": memory_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        self.index.add(embedding)

        self.memories.append(memory)

        self.save_memory()

        return memory

    # ---------------------------------
    # Search memory
    # ---------------------------------

    def search_memory(self, query, top_k=3, category=None):

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k < 1:
            raise ValueError("top_k must be positive")

        if not self.memories:
            return []

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        # Search all memories
        scores, indices = self.index.search(
            query_embedding,
            len(self.memories)
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue

            memory = self.memories[idx]

            # Optional category filtering
            if category is not None:
                if memory["metadata"].get("category") != category:
                    continue

            results.append({
                "id": memory["id"],
                "memory": memory["text"],
                "metadata": memory["metadata"],
                "created_at": memory["created_at"],
                "score": float(score)
            })

            if len(results) >= top_k:
                break

        return results

    # ---------------------------------
    # Save memory
    # ---------------------------------

    def save_memory(self):

        temp_index_path = self.storage_dir / "memory.tmp.index"

        faiss.write_index(
            self.index,
            str(temp_index_path)
        )

        temp_index_path.replace(self.index_path)

        temp_memory_path = self.storage_dir / "memories.tmp.json"

        with open(
            temp_memory_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.memories,
                file,
                ensure_ascii=False,
                indent=4
            )

        temp_memory_path.replace(self.memory_path)

    # ---------------------------------
    # Load memory
    # ---------------------------------

    
    # ---------------------------------
    # Load memory
    # ---------------------------------

    
    
    
    
    def load_memory(self):

        if not self.memory_path.exists():
            if self.index_path.exists():
                raise RuntimeError("Memory index exists without memory data.")
            return

        with open(self.memory_path, "r", encoding="utf-8") as file:
            loaded_memories = json.load(file)

        if not isinstance(loaded_memories, list):
            raise RuntimeError("Invalid memory storage format.")

        # Convert old string records into the new dictionary format
        self.memories = []

        for i, item in enumerate(loaded_memories):

            if isinstance(item, str):
                memory = {
                    "id": i + 1,
                    "text": item,
                    "metadata": {},
                    "created_at": datetime.now(timezone.utc).isoformat()
                }

            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                memory = item

            else:
                raise RuntimeError(
                    f"Invalid memory record at index {i}"
                )

            self.memories.append(memory)

        # Rebuild FAISS index from memory text
        self.index = faiss.IndexFlatIP(self.dimension)

        if self.memories:

            texts = [item["text"] for item in self.memories]

            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True
            )

            embeddings = np.asarray(embeddings, dtype=np.float32)

            self.index.add(embeddings)

        # Persist migrated data
        self.save_memory()
