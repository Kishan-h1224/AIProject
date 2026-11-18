
from enum import Enum


# All possible agent states
class AgentState(str, Enum):

    THINK = "THINK"
    VALIDATE = "VALIDATE"
    AUTHORIZE = "AUTHORIZE"
    EXECUTE = "EXECUTE"
    OBSERVE = "OBSERVE"

    DONE = "DONE"
    FAILED = "FAILED"


class StateMachine:

    # Define allowed transitions
    TRANSITIONS = {

        AgentState.THINK: {
            AgentState.VALIDATE,
            AgentState.DONE,
            AgentState.FAILED
        },

        AgentState.VALIDATE: {
            AgentState.AUTHORIZE,
            AgentState.FAILED
        },

        AgentState.AUTHORIZE: {
            AgentState.EXECUTE,
            AgentState.FAILED
        },

        AgentState.EXECUTE: {
            AgentState.OBSERVE,
            AgentState.FAILED
        },

        AgentState.OBSERVE: {
            AgentState.THINK,
            AgentState.DONE,
            AgentState.FAILED
        },

        AgentState.DONE: set(),

        AgentState.FAILED: set()
    }

    def __init__(self):

        # Initial state
        self.current_state = AgentState.THINK

        # Maintain state history
        self.history = [AgentState.THINK]

    def transition(self, next_state: AgentState):

        allowed_states = self.TRANSITIONS[self.current_state]

        # Check whether transition is valid
        if next_state not in allowed_states:

            raise ValueError(
                f"Invalid transition: "
                f"{self.current_state.value} -> {next_state.value}"
            )

        # Update current state
        self.current_state = next_state

        # Record transition
        self.history.append(next_state)

        print(f"State: {next_state.value}")

    @property
    def is_terminal(self):

        return self.current_state in {
            AgentState.DONE,
            AgentState.FAILED
        }

    def get_history(self):

        return [state.value for state in self.history]


if __name__ == "__main__":

    machine = StateMachine()

    print("Initial State:", machine.current_state.value)

    machine.transition(AgentState.VALIDATE)
    machine.transition(AgentState.AUTHORIZE)
    machine.transition(AgentState.EXECUTE)
    machine.transition(AgentState.OBSERVE)
    machine.transition(AgentState.THINK)
    machine.transition(AgentState.DONE)

    print("\nState History:")
    print(machine.get_history())

    print("\nIs Terminal:", machine.is_terminal)
