"""Tests for token decoding functionality."""

import base64
import json

import pytest

from veris_ai import veris


class TestTokenDecoding:
    """Test token decoding and session/thread ID extraction."""

    def test_decode_valid_token_with_both_ids(self):
        """Test decoding a valid token with both session_id and thread_id."""
        session_id = "test-session-123"
        thread_id = "thread-456"
        token_data = {"session_id": session_id, "thread_id": thread_id}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)

        assert veris.session_id == session_id
        assert veris.thread_id == thread_id

        veris.clear_session_id()

    def test_decode_valid_token_with_only_session_id(self):
        """Test decoding a token with only session_id (no thread_id)."""
        session_id = "test-session-789"
        token_data = {"session_id": session_id}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)

        assert veris.session_id == session_id
        assert veris.thread_id is None

        veris.clear_session_id()

    def test_decode_token_with_uuid_format(self):
        """Test decoding token with UUID-formatted IDs."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        thread_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        token_data = {"session_id": session_id, "thread_id": thread_id}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)

        assert veris.session_id == session_id
        assert veris.thread_id == thread_id

        veris.clear_session_id()

    def test_decode_invalid_base64_raises_error(self):
        """Test that invalid base64 raises ValueError."""
        invalid_token = "not-valid-base64!!!"

        with pytest.raises(ValueError, match="Invalid token format"):
            veris.set_session_id(invalid_token)

    def test_decode_invalid_json_raises_error(self):
        """Test that valid base64 but invalid JSON raises ValueError."""
        invalid_json = base64.b64encode(b"not valid json").decode("utf-8")

        with pytest.raises(ValueError, match="Invalid token format"):
            veris.set_session_id(invalid_json)

    def test_decode_non_object_json_raises_error(self):
        """Test that JSON array instead of object raises ValueError."""
        json_array = base64.b64encode(
            json.dumps(["array", "not", "object"]).encode("utf-8")
        ).decode("utf-8")

        with pytest.raises(ValueError, match="Token must decode to a JSON object"):
            veris.set_session_id(json_array)

    def test_decode_missing_session_id_raises_error(self):
        """Test that token without session_id raises ValueError."""
        token_data = {"thread_id": "thread-only"}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        with pytest.raises(ValueError, match="Token must contain 'session_id' field"):
            veris.set_session_id(token)

    def test_clear_session_id_clears_both_values(self):
        """Test that clear_session_id clears both session_id and thread_id."""
        session_id = "test-session"
        thread_id = "test-thread"
        token_data = {"session_id": session_id, "thread_id": thread_id}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)
        assert veris.session_id == session_id
        assert veris.thread_id == thread_id

        veris.clear_session_id()
        assert veris.session_id is None
        assert veris.thread_id is None

    def test_decode_token_with_additional_fields(self):
        """Test that additional fields in token are ignored."""
        session_id = "test-session"
        thread_id = "test-thread"
        token_data = {
            "session_id": session_id,
            "thread_id": thread_id,
            "extra_field": "ignored",
            "another": 123,
        }
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)

        assert veris.session_id == session_id
        assert veris.thread_id == thread_id

        veris.clear_session_id()

    def test_decode_token_with_empty_strings(self):
        """Test decoding token with empty string values."""
        session_id = ""
        thread_id = ""
        token_data = {"session_id": session_id, "thread_id": thread_id}
        token = base64.b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

        veris.set_session_id(token)

        assert veris.session_id == session_id
        assert veris.thread_id == thread_id

        veris.clear_session_id()
