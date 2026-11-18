from app.memory.semantic_memory import SemanticMemory

memory = SemanticMemory()

# Store some information
memory.add_memory(
    "The AutoAgent project is built using Python."
)

memory.add_memory(
    "The project uses FAISS for semantic memory retrieval."
)

memory.add_memory(
    "The agent supports web search, Python execution, and SQL execution."
)

# Retrieve relevant information
query = "Which technology is used for semantic memory?"

results = memory.search_memory(query, top_k=2)

print("\nRetrieved Memories:")

for result in results:
    print(result["memory"])
    print("Similarity:", result["score"])
    print("------------------")