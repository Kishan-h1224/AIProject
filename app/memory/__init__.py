def __init__(
    self,
    llm,
    allowed_tools,
    max_steps=5,
    max_retries=2,
    max_identical_calls=2,
    memory=None
):
    self.llm = llm
    self.allowed_tools = allowed_tools
    self.max_steps = max_steps
    self.max_retries = max_retries
    self.max_identical_calls = max_identical_calls

    self.memory = memory if memory is not None else SemanticMemory()