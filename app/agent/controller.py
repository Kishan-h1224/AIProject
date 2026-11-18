
import json
import hashlib
from typing import Any

from app.memory.semantic_memory import SemanticMemory
from app.agent.mock_llm import MockLLM
from app.agent.state_machine import (
    StateMachine,
    AgentState
)

from app.tools.registry import get_tool, list_tools
from app.tools import basic_tools


class AutoAgent:

    def __init__(
        self,
        llm,
        allowed_tools: set[str],
        max_steps: int = 5,
        max_retries: int = 2,
        max_identical_calls: int = 2,
        memory=None
    ):

        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if max_identical_calls < 1:
            raise ValueError(
                "max_identical_calls must be at least 1"
            )

        self.llm = llm
        self.allowed_tools = allowed_tools
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.max_identical_calls = max_identical_calls

        # Initialize semantic memory
        self.memory = memory if memory is not None else SemanticMemory()

    # ---------------------------------
    # Retry mechanism
    # ---------------------------------

    def execute_with_retries(self, tool, arguments):

        for attempt in range(1, self.max_retries + 2):

            try:
                result = tool.func(**arguments)
                return result, attempt

            except (TimeoutError, ConnectionError):

                if attempt > self.max_retries:
                    raise

                print(
                    f"Temporary error. Retrying "
                    f"({attempt}/{self.max_retries})..."
                )

    # ---------------------------------
    # Main agent execution
    # ---------------------------------

    def run(
    self,
    user_request: str,
    allowed_tools: set[str] | None = None,
    conversation_history: list | None = None,
    approved_tool_calls: set[str] | None = None
    ) -> dict[str, Any]:

        machine = StateMachine()
        effective_allowed_tools = (
            allowed_tools
            if allowed_tools is not None
            else self.allowed_tools
        )
        approved_tool_calls = approved_tool_calls or set()
        # Retrieve relevant memories
        memory_results = self.memory.search_memory(
            user_request,
            top_k=3
        )

        observations = []

        # Add semantic memory observations.
        for item in memory_results:
            observations.append({
                "type": "memory",
                "content": item["memory"],
                "score": item["score"]
            })

        # Add previous conversation messages.
        if conversation_history:
            for item in conversation_history:
                observations.append({
                    "type": "conversation",
                    "role": item["role"],
                    "message": item["message"]
                })

        tool_calls = 0
        execution_attempts = 0

        call_counts = {}

        response = None
        tool_definition = None
        validated_args = None

        final_answer = None
        error = None
        error_details = None

        print("\nStarting AutoAgent...")
        print("User Request:", user_request)

        while not machine.is_terminal:

            try:

                # 1. THINK
                if machine.current_state == AgentState.THINK:

                    print("\n[THINK] Asking LLM...")

                    response = self.llm.decide(
                        user_request,
                        observations
                    )

                    if response.response_type == "final":

                        if response.answer is None:
                            raise ValueError(
                                "Final answer is missing"
                            )

                        final_answer = response.answer

                        machine.transition(AgentState.DONE)

                    else:

                        if response.tool_name is None:
                            raise ValueError(
                                "Tool name is missing"
                            )

                        print("Selected Tool:", response.tool_name)

                        machine.transition(AgentState.VALIDATE)

                # 2. VALIDATE
                elif machine.current_state == AgentState.VALIDATE:

                    print("\n[VALIDATE] Checking arguments...")

                    tool_definition = get_tool(
                        response.tool_name
                    )

                    validated_args = (
                        tool_definition.args_model.model_validate(
                            response.arguments
                        )
                    )

                    print("Arguments are valid.")

                    machine.transition(AgentState.AUTHORIZE)

                # 3. AUTHORIZE
                elif machine.current_state == AgentState.AUTHORIZE:

                    print("\n[AUTHORIZE] Checking permissions...")

                    if response.tool_name not in effective_allowed_tools:

                        raise PermissionError(
                            f"Tool '{response.tool_name}' "
                            "is not authorized"
                        )

                    # Generate unique tool-call signature
                    signature = json.dumps(
                        {
                            "tool": response.tool_name,
                            "arguments": validated_args.model_dump()
                        },
                        sort_keys=True
                    )

                    call_counts[signature] = (
                        call_counts.get(signature, 0) + 1
                    )

                    # Detect repeated identical calls
                    # Detect repeated identical calls
                    if (
                        call_counts[signature]
                        > self.max_identical_calls
                    ):
                        raise RuntimeError(
                            "Repeated identical tool call detected"
                        )

                    # Generate an approval ID bound to this exact tool call.
                    approval_id = hashlib.sha256(
                        signature.encode("utf-8")
                    ).hexdigest()

                    # Check whether this operation requires approval.
                    approval_required = tool_definition.needs_approval(
                        validated_args.model_dump()
                    )

                    # Stop before execution if approval is missing.
                    if approval_required and approval_id not in approved_tool_calls:

                        print("\n[APPROVAL] Human approval required.")

                        return {
                            "status": "approval_required",
                            "answer": None,
                            "error": None,
                            "error_details": None,
                            "tool_calls": tool_calls,
                            "execution_attempts": execution_attempts,
                            "pending_approval": {
                                "approval_id": approval_id,
                                "tool_name": response.tool_name,
                                "arguments": validated_args.model_dump()
                            },
                            "observations": observations,
                            "state_history": machine.get_history()
                        }

                    print("Tool is authorized and approved.")

                    machine.transition(AgentState.EXECUTE)

                # 4. EXECUTE
                elif machine.current_state == AgentState.EXECUTE:

                    print("\n[EXECUTE] Running tool...")

                    if tool_calls >= self.max_steps:

                        raise RuntimeError(
                            "Maximum tool execution budget exceeded"
                        )

                    tool_calls += 1

                    result, attempts = self.execute_with_retries(
                        tool_definition,
                        validated_args.model_dump()
                    )

                    execution_attempts += attempts

                    print("Tool Result:", result)

                    machine.transition(AgentState.OBSERVE)

                # 5. OBSERVE
                elif machine.current_state == AgentState.OBSERVE:

                    print("\n[OBSERVE] Recording result...")

                    observations.append({

                        "kind": "tool_result",

                        "tool_name": response.tool_name,

                        "arguments": validated_args.model_dump(),

                        "result": result,

                        "attempts": attempts

                    })

                    print("Observation:", observations[-1])

                    machine.transition(AgentState.THINK)

            except Exception as exc:

                error = str(exc)

                error_details = {

                    "type": type(exc).__name__,

                    "message": str(exc),

                    "state": machine.current_state.value

                }

                observations.append({

                    "kind": "error",

                    "error": error_details

                })

                print("\n[ERROR]", error_details)

                if not machine.is_terminal:

                    machine.transition(AgentState.FAILED)

        # Store successful interaction in semantic memory
        if machine.current_state == AgentState.DONE:

            self.memory.add_memory(
                f"User request: {user_request}. "
                f"Agent answer: {final_answer}"
            )

        return {

            "status": (
                "completed"
                if machine.current_state == AgentState.DONE
                else "failed"
            ),

            "answer": final_answer,

            "error": error,

            "error_details": error_details,

            "tool_calls": tool_calls,

            "execution_attempts": execution_attempts,

            "observations": observations,

            "state_history": machine.get_history(),

            "pending_approval": None

        }


# ---------------------------------
# Run AutoAgent
# ---------------------------------

if __name__ == "__main__":

    llm = MockLLM()

    allowed_tools = set(list_tools())

    agent = AutoAgent(
        llm=llm,
        allowed_tools=allowed_tools,
        max_steps=5,
        max_retries=2,
        max_identical_calls=2
    )

    request = (
        "Calculate 25 multiplied by 4 "
        "and then add 10"
    )

    result = agent.run(request)

    print("\n========== FINAL RESULT ==========")

    print("Status:", result["status"])
    print("Answer:", result["answer"])
    print("Tool Calls:", result["tool_calls"])

    print("Execution Attempts:", result["execution_attempts"])

    print("State History:", result["state_history"])
