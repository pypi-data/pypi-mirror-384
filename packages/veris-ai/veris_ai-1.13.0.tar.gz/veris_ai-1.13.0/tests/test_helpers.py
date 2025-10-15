"""Helper functions for tests."""

import base64
import json


def create_test_token(
    session_id: str = "test-session", thread_id: str | None = "test-thread"
) -> str:
    """Create a base64-encoded test token.

    Args:
        session_id: Session ID to include in token
        thread_id: Thread ID to include in token (optional)

    Returns:
        Base64-encoded JSON token
    """
    token_data = {"session_id": session_id}
    if thread_id is not None:
        token_data["thread_id"] = thread_id

    return base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")
