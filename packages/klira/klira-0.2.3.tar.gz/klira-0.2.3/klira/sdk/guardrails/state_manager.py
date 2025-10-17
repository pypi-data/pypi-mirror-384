import time
import logging
from typing import Dict, Any, List, TypedDict

logger = logging.getLogger("klira.guardrails.state_manager")


# Define the structure of the conversation state dictionary
class ConversationState(TypedDict):
    created_at: float
    last_updated: float
    policy_violations: List[
        Dict[str, Any]
    ]  # List of violation details (policy_id, reason, etc.)
    policy_warnings: List[Dict[str, Any]]  # List of warning details
    verified_statuses: Dict[str, bool]  # Track verification status per policy/check
    policy_counters: Dict[str, int]  # Counters per policy ID
    # Add other potential state fields here, e.g.:
    # user_sentiment_history: List[float]
    # escalation_level: int


class StateManager:
    """Manages in-memory state for conversations related to guardrails.

    Tracks policy violations, warnings, counters, and other relevant state
    per conversation ID. Includes time-to-live (TTL) based cleanup.

    Attributes:
        ttl_seconds: Default TTL for state entries in seconds.
        cleanup_interval: How often (in seconds) to run the cleanup task.
    """

    states: Dict[str, ConversationState]
    ttl_seconds: int
    cleanup_interval: int
    last_cleanup: float

    def __init__(self, ttl_seconds: int = 3600, cleanup_interval: int = 300):
        """Initializes the State Manager.

        Args:
            ttl_seconds: Time-to-live (TTL) for conversation state entries in seconds.
                         Entries not updated within this duration may be removed.
            cleanup_interval: Frequency (in seconds) for checking and removing expired entries.
        """
        self.states = {}
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        logger.info(
            f"StateManager initialized with TTL={ttl_seconds}s, Cleanup Interval={cleanup_interval}s"
        )

    def get_state(self, conversation_id: str) -> ConversationState:
        """Retrieves or creates the state for a given conversation ID.

        Performs cleanup of expired states before returning.

        Args:
            conversation_id: The unique identifier for the conversation.

        Returns:
            The state dictionary for the conversation.
        """
        self._maybe_cleanup()

        if conversation_id not in self.states:
            logger.debug(
                f"Creating new state entry for conversation ID: {conversation_id}"
            )
            now = time.time()
            self.states[conversation_id] = ConversationState(
                created_at=now,
                last_updated=now,
                policy_violations=[],
                policy_warnings=[],
                verified_statuses={},
                policy_counters={},
            )

        # Always update last_updated on access to refresh TTL
        self.states[conversation_id]["last_updated"] = time.time()
        return self.states[conversation_id]

    def update_state(
        self, conversation_id: str, updates: Dict[str, Any]
    ) -> ConversationState:
        """Updates the state for a given conversation ID.

        Merges the provided updates into the existing state. List-based fields
        like `policy_violations` and `policy_warnings` are appended to, while
        `policy_counters` are incremented.

        Args:
            conversation_id: The unique identifier for the conversation.
            updates: A dictionary containing the state updates to apply.

        Returns:
            The updated conversation state dictionary.
        """
        state = self.get_state(
            conversation_id
        )  # Ensures state exists & updates timestamp

        logger.debug(
            f"Updating state for conversation ID '{conversation_id}': {updates}"
        )

        for key, value in updates.items():
            if key == "policy_violations" and isinstance(value, list):
                state["policy_violations"].extend(item for item in value if item)
            elif key == "policy_warnings" and isinstance(value, list):
                state["policy_warnings"].extend(item for item in value if item)
            elif key == "policy_counters" and isinstance(value, dict):
                for counter_key, counter_value in value.items():
                    if isinstance(counter_value, int):
                        state["policy_counters"][counter_key] = (
                            state["policy_counters"].get(counter_key, 0) + counter_value
                        )
                    else:
                        logger.warning(
                            f"Invalid counter value type for '{counter_key}' in conversation '{conversation_id}': {type(counter_value)}"
                        )
            elif (
                key in ConversationState.__annotations__
            ):  # Check if it's a defined key
                # TODO: Consider adding type validation here based on ConversationState annotations
                state[key] = value  # type: ignore
            else:
                logger.warning(
                    f"Attempted to update unknown state key '{key}' for conversation '{conversation_id}'"
                )

        # No need to update timestamp here, get_state already did
        return state

    def increment_policy_counter(
        self, conversation_id: str, policy_id: str, increment: int = 1
    ) -> None:
        """Increments a specific policy counter for a conversation.

        Args:
            conversation_id: The unique identifier for the conversation.
            policy_id: The identifier of the policy whose counter should be incremented.
            increment: The amount to increment by (default: 1).
        """
        state = self.get_state(conversation_id)
        counters = state.setdefault("policy_counters", {})
        counters[policy_id] = counters.get(policy_id, 0) + increment
        # No need to update timestamp here, get_state already did
        logger.debug(
            f"Incremented counter for policy '{policy_id}' in conversation '{conversation_id}' to {counters[policy_id]}"
        )

    def get_policy_history(self, conversation_id: str) -> Dict[str, Any]:
        """Retrieves the history of policy interactions for a conversation.

        Args:
            conversation_id: The unique identifier for the conversation.

        Returns:
            A dictionary containing lists of 'violations', 'warnings', and
            a dictionary of 'counters'.
        """
        state = self.get_state(conversation_id)
        return {
            "violations": state.get("policy_violations", []),
            "warnings": state.get("policy_warnings", []),
            "counters": state.get("policy_counters", {}),
        }

    def _maybe_cleanup(self) -> None:
        """Periodically checks for and removes expired conversation states."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            logger.debug("Running state cleanup...")
            start_time = time.monotonic()
            expired_ids = [
                conv_id
                for conv_id, state in self.states.items()
                if now - state.get("last_updated", 0) > self.ttl_seconds
            ]

            if expired_ids:
                logger.info(f"Cleaning up {len(expired_ids)} expired state entries.")
                for conversation_id in expired_ids:
                    # Use pop for atomic removal and potential retrieval if needed
                    self.states.pop(conversation_id, None)

            self.last_cleanup = now
            elapsed = (time.monotonic() - start_time) * 1000
            logger.debug(
                f"State cleanup finished in {elapsed:.2f} ms. Found {len(expired_ids)} expired entries."
            )
