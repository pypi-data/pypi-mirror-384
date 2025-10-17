"""State Manager

Manages client state machine and state transitions.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from ..models.enums import ClientState
from ..utils.exceptions import InvalidStateError

logger = logging.getLogger(__name__)


@dataclass
class StateTransition:
    """State transition definition"""
    from_state: ClientState
    to_state: ClientState
    action: str
    condition: Callable[[], bool] | None = None


class ClientStateMachine:
    """Client state machine"""

    def __init__(self) -> None:
        self._current_state = ClientState.DISCONNECTED
        self._state_history: list[tuple[ClientState, datetime]] = []
        self._transitions: dict[tuple[ClientState, str], ClientState] = {}
        self._state_callbacks: dict[ClientState, list[Callable[[ClientState, ClientState], None]]] = {}

        # Define allowed state transitions
        self._setup_transitions()

    def _setup_transitions(self) -> None:
        """Set up allowed state transitions"""
        transitions = [
            # From disconnected state
            (ClientState.DISCONNECTED, "connect", ClientState.CONNECTING),

            # From connecting state
            (ClientState.CONNECTING, "connected", ClientState.CONNECTED),
            (ClientState.CONNECTING, "failed", ClientState.ERROR),
            (ClientState.CONNECTING, "timeout", ClientState.ERROR),
            (ClientState.CONNECTING, "disconnect", ClientState.DISCONNECTED),

            # From connected state
            (ClientState.CONNECTED, "create_session", ClientState.SESSION_ACTIVE),
            (ClientState.CONNECTED, "disconnect", ClientState.DISCONNECTED),
            (ClientState.CONNECTED, "error", ClientState.ERROR),

            # From session active state
            (ClientState.SESSION_ACTIVE, "start_synthesis", ClientState.SYNTHESIZING),
            (ClientState.SESSION_ACTIVE, "end_session", ClientState.CONNECTED),
            (ClientState.SESSION_ACTIVE, "disconnect", ClientState.DISCONNECTED),
            (ClientState.SESSION_ACTIVE, "error", ClientState.ERROR),

            # From synthesizing state
            (ClientState.SYNTHESIZING, "end_synthesis", ClientState.SESSION_ACTIVE),
            (ClientState.SYNTHESIZING, "end_session", ClientState.CONNECTED),
            (ClientState.SYNTHESIZING, "disconnect", ClientState.DISCONNECTED),
            (ClientState.SYNTHESIZING, "error", ClientState.ERROR),

            # From error state
            (ClientState.ERROR, "reset", ClientState.DISCONNECTED),
            (ClientState.ERROR, "connect", ClientState.CONNECTING),

            # From closing state
            (ClientState.CLOSING, "closed", ClientState.DISCONNECTED),
        ]

        for from_state, action, to_state in transitions:
            self._transitions[(from_state, action)] = to_state

    @property
    def current_state(self) -> ClientState:
        """Current state"""
        return self._current_state

    @property
    def state_history(self) -> list[tuple[ClientState, datetime]]:
        """State history"""
        return self._state_history.copy()

    def can_transition(self, action: str) -> bool:
        """Check if the specified state transition can be executed"""
        return (self._current_state, action) in self._transitions

    def transition(self, action: str) -> ClientState:
        """Execute state transition"""
        if not self.can_transition(action):
            raise InvalidStateError(
                f"Cannot execute action '{action}' from state {self._current_state}"
            )

        old_state = self._current_state
        new_state = self._transitions[(self._current_state, action)]

        # Record state change
        self._current_state = new_state
        self._state_history.append((new_state, datetime.now()))

        logger.debug(f"State transition: {old_state} --[{action}]--> {new_state}")

        # Trigger state callbacks
        self._trigger_state_callbacks(old_state, new_state)

        return new_state

    def force_state(self, new_state: ClientState) -> None:
        """Force set state (use with caution)"""
        old_state = self._current_state
        self._current_state = new_state
        self._state_history.append((new_state, datetime.now()))

        logger.warning(f"Force state change: {old_state} --> {new_state}")

        # Trigger state callbacks
        self._trigger_state_callbacks(old_state, new_state)

    def add_state_callback(
        self,
        state: ClientState,
        callback: Callable[[ClientState, ClientState], None]
    ) -> None:
        """Add state change callback"""
        if state not in self._state_callbacks:
            self._state_callbacks[state] = []
        self._state_callbacks[state].append(callback)

    def _trigger_state_callbacks(self, old_state: ClientState, new_state: ClientState) -> None:
        """Trigger state change callbacks"""
        # Trigger callbacks for entering new state
        if new_state in self._state_callbacks:
            for callback in self._state_callbacks[new_state]:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    logger.error(f"State callback execution failed: {e}")

    def get_available_actions(self) -> list[str]:
        """Get available actions in current state"""
        actions = []
        for (state, action), _ in self._transitions.items():
            if state == self._current_state:
                actions.append(action)
        return actions

    def reset(self) -> None:
        """Reset state machine"""
        old_state = self._current_state
        self._current_state = ClientState.DISCONNECTED
        self._state_history.clear()
        self._state_history.append((ClientState.DISCONNECTED, datetime.now()))

        logger.info(f"State machine reset: {old_state} --> {ClientState.DISCONNECTED}")


class StateManager:
    """State manager"""

    def __init__(self) -> None:
        self.state_machine = ClientStateMachine()
        self._state_lock = None  # Use asyncio.Lock in async environment

    @property
    def current_state(self) -> ClientState:
        """Current state"""
        return self.state_machine.current_state

    @property
    def is_connected(self) -> bool:
        """Whether connected"""
        return self.current_state in (
            ClientState.CONNECTED,
            ClientState.SESSION_ACTIVE,
            ClientState.SYNTHESIZING
        )

    @property
    def is_active(self) -> bool:
        """Whether in active state"""
        return self.current_state in (
            ClientState.SESSION_ACTIVE,
            ClientState.SYNTHESIZING
        )

    @property
    def has_error(self) -> bool:
        """Whether in error state"""
        return self.current_state == ClientState.ERROR

    async def transition(self, action: str) -> ClientState:
        """Async state transition"""
        # In actual implementation, should use asyncio.Lock
        # if self._state_lock:
        #     async with self._state_lock:
        #         return self.state_machine.transition(action)
        # else:
        return self.state_machine.transition(action)

    def can_transition(self, action: str) -> bool:
        """Check if state transition can be executed"""
        return self.state_machine.can_transition(action)

    def reset(self) -> None:
        """Reset state manager"""
        self.state_machine.reset()
