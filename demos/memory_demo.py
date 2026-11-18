from app.memory.semantic_memory import SemanticMemory

memory = SemanticMemory()

memory.add_memory("Kishan is a Computer Science student.")
memory.add_memory("Kishan is building an AI-powered AutoAgent.")
memory.add_memory("The project uses Python and FAISS.")

results = memory.search_memory(
    "What AI project is being developed?",
    top_k=2
)

for result in results:
    print(result["memory"])
    print("Similarity:", result["score"])