"""Provides the Klira AI Client class for API interaction and Traceloop integration."""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

# Use TYPE_CHECKING to avoid runtime import errors if traceloop isn't installed,
# while still providing type hints for static analysis.
if TYPE_CHECKING:
    from traceloop.sdk import Traceloop as TraceloopClientType

    # Assuming user_feedback has a 'create' method, define a Protocol or use Any
    # For simplicity here, we'll use Any, but a Protocol would be safer.
    from typing import Protocol

    class UserFeedbackProtocol(Protocol):
        def create(
            self, annotation_task: str, entity_instance_id: str, tags: Dict[str, Any]
        ) -> None: ...


logger = logging.getLogger("klira.client")


class Client:
    """Klira AI Client for Klira AI API interaction and Traceloop features.

    Wraps the Traceloop client, offering a unified interface for Klira AI-specific
    operations and standard Traceloop tracing/telemetry.

    Attributes:
        traceloop_client: The underlying Traceloop client instance.
        app_name: The name of the application associated with this client.
        api_key: The Klira AI API key for authentication (optional).
        user_feedback: Accessor for Traceloop's user feedback functionality.
                       May be None if not available on the Traceloop client.
    """

    traceloop_client: "TraceloopClientType"
    app_name: str
    api_key: Optional[str]
    user_feedback: Optional["UserFeedbackProtocol"]  # Hint with the protocol

    def __init__(
        self,
        traceloop_client: "TraceloopClientType",
        app_name: str,
        api_key: Optional[str] = None,
    ):
        """Initializes the Klira AI client.

        Args:
            traceloop_client: An initialized Traceloop client instance.
            app_name: The name designated for your application.
            api_key: Your Klira AI API key. Optional but needed for most Klira AI features.
        """
        self.traceloop_client = traceloop_client
        self.app_name = app_name
        self.api_key = api_key
        self.user_feedback = None  # Initialize clearly

        # Safely access user_feedback if available
        if hasattr(traceloop_client, "user_feedback"):
            # We assume the attribute matches our Protocol
            self.user_feedback = getattr(traceloop_client, "user_feedback")
        else:
            logger.debug(
                "Traceloop client instance does not have 'user_feedback' attribute."
            )

    def create_annotation(
        self,
        annotation_task: str,
        entity_id: str,
        tags: Dict[str, Any],
    ) -> None:
        """Creates an annotation via Traceloop user feedback.

        Associates structured feedback or labels (tags) with specific entities
        (identified by entity_id) within a defined annotation task.

        Args:
            annotation_task: Identifier for the annotation task.
            entity_id: Unique identifier of the entity instance being annotated.
            tags: Dictionary of key-value pairs representing annotation tags.
        """
        if self.user_feedback:
            # Assuming the parameter name is entity_instance_id based on Protocol
            self.user_feedback.create(
                annotation_task=annotation_task,
                entity_instance_id=entity_id,
                tags=tags,
            )
        else:
            logger.warning(
                "User feedback component not available or initialized. "
                "Cannot create annotation for task '%s', entity '%s'.",
                annotation_task,
                entity_id,
            )
