
from app.memory.semantic_memory import SemanticMemory


def test_add_and_search_memory(tmp_path):

    memory = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    memory.add_memory(
        "Kishan is building an AutoAgent project using Python."
    )

    memory.add_memory(
        "The project uses FAISS for semantic search."
    )

    results = memory.search_memory(
        "Which project is Kishan developing?",
        top_k=2
    )

    assert len(results) == 2

    assert any(
        "AutoAgent" in item["memory"]
        for item in results
    )


def test_empty_memory(tmp_path):

    memory = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    results = memory.search_memory(
        "Find something",
        top_k=3
    )

    assert results == []


def test_empty_memory_text(tmp_path):

    memory = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    try:
        memory.add_memory("")
        assert False
    except ValueError:
        assert True


def test_memory_metadata(tmp_path):

    memory = SemanticMemory(
        storage_dir=str(tmp_path)
    )

    memory.add_memory(
        "AutoAgent uses FAISS.",
        metadata={
            "category": "project",
            "source": "user"
        }
    )

    results = memory.search_memory(
        "Which project uses FAISS?",
        top_k=3,
        category="project"
    )

    assert len(results) == 1

    assert results[0]["metadata"]["category"] == "project"
    assert results[0]["metadata"]["source"] == "user"
    assert results[0]["id"] == 1
    assert results[0]["created_at"] is not None
