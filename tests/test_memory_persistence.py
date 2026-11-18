
from app.memory.semantic_memory import SemanticMemory


def test_memory_persistence(tmp_path):

    # First agent session
    memory1 = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    memory1.add_memory(
        "Kishan is building an AI-powered AutoAgent."
    )

    memory1.add_memory(
        "The project uses FAISS for semantic search."
    )

    # Simulate a new session
    memory2 = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    results = memory2.search_memory(
        "Which project uses FAISS?",
        top_k=2
    )

    assert len(results) == 2

    assert any(
        "FAISS" in item["memory"]
        for item in results
    )
