
import unittest

from app.agent.state_machine import (
    StateMachine,
    AgentState
)


class TestStateMachine(unittest.TestCase):

    def test_valid_transition(self):

        machine = StateMachine()

        machine.transition(AgentState.VALIDATE)

        self.assertEqual(
            machine.current_state,
            AgentState.VALIDATE
        )

    def test_invalid_transition(self):

        machine = StateMachine()

        with self.assertRaises(ValueError):

            machine.transition(AgentState.EXECUTE)

    def test_terminal_state(self):

        machine = StateMachine()

        machine.transition(AgentState.DONE)

        self.assertTrue(machine.is_terminal)

    def test_no_transition_after_done(self):

        machine = StateMachine()

        machine.transition(AgentState.DONE)

        with self.assertRaises(ValueError):

            machine.transition(AgentState.THINK)


if __name__ == "__main__":
    unittest.main()
