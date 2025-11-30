"""Unit tests for session manager"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from session_manager import SessionManager, Message


@pytest.mark.unit
class TestSessionManagerInitialization:
    """Test session manager initialization"""

    def test_session_manager_initializes_correctly(self):
        """Test that session manager initializes with correct defaults"""
        sm = SessionManager(max_history=5)

        assert sm.max_history == 5
        assert sm.sessions == {}
        assert sm.session_counter == 0

    def test_session_manager_default_max_history(self):
        """Test default max_history value"""
        sm = SessionManager()

        assert sm.max_history == 5


@pytest.mark.unit
class TestSessionCreation:
    """Test session creation functionality"""

    def test_create_session_generates_id(self):
        """Test that create_session generates unique session IDs"""
        sm = SessionManager()

        session_id_1 = sm.create_session()
        session_id_2 = sm.create_session()

        assert session_id_1 == "session_1"
        assert session_id_2 == "session_2"
        assert session_id_1 != session_id_2

    def test_create_session_initializes_empty_list(self):
        """Test that new sessions start with empty message list"""
        sm = SessionManager()

        session_id = sm.create_session()

        assert session_id in sm.sessions
        assert sm.sessions[session_id] == []

    def test_multiple_sessions_are_independent(self):
        """Test that multiple sessions are stored independently"""
        sm = SessionManager()

        session_1 = sm.create_session()
        session_2 = sm.create_session()

        sm.add_message(session_1, "user", "Hello from session 1")
        sm.add_message(session_2, "user", "Hello from session 2")

        assert len(sm.sessions[session_1]) == 1
        assert len(sm.sessions[session_2]) == 1
        assert sm.sessions[session_1][0].content == "Hello from session 1"
        assert sm.sessions[session_2][0].content == "Hello from session 2"


@pytest.mark.unit
class TestMessageManagement:
    """Test message management functionality"""

    def test_add_message_to_existing_session(self):
        """Test adding a message to an existing session"""
        sm = SessionManager()
        session_id = sm.create_session()

        sm.add_message(session_id, "user", "Test message")

        assert len(sm.sessions[session_id]) == 1
        assert sm.sessions[session_id][0].role == "user"
        assert sm.sessions[session_id][0].content == "Test message"

    def test_add_message_to_new_session(self):
        """Test adding a message creates session if it doesn't exist"""
        sm = SessionManager()

        sm.add_message("new_session", "user", "Test message")

        assert "new_session" in sm.sessions
        assert len(sm.sessions["new_session"]) == 1

    def test_add_exchange(self):
        """Test adding a complete question-answer exchange"""
        sm = SessionManager()
        session_id = sm.create_session()

        sm.add_exchange(session_id, "What is RAG?", "RAG is Retrieval-Augmented Generation")

        assert len(sm.sessions[session_id]) == 2
        assert sm.sessions[session_id][0].role == "user"
        assert sm.sessions[session_id][0].content == "What is RAG?"
        assert sm.sessions[session_id][1].role == "assistant"
        assert sm.sessions[session_id][1].content == "RAG is Retrieval-Augmented Generation"

    def test_message_dataclass_structure(self):
        """Test that Message dataclass has correct structure"""
        message = Message(role="user", content="Test")

        assert message.role == "user"
        assert message.content == "Test"


@pytest.mark.unit
class TestHistoryManagement:
    """Test conversation history management"""

    def test_get_conversation_history_formats_correctly(self):
        """Test that conversation history is formatted correctly"""
        sm = SessionManager()
        session_id = sm.create_session()

        sm.add_exchange(session_id, "What is RAG?", "RAG is Retrieval-Augmented Generation")
        sm.add_exchange(session_id, "Tell me more", "RAG combines retrieval with generation")

        history = sm.get_conversation_history(session_id)

        assert "User: What is RAG?" in history
        assert "Assistant: RAG is Retrieval-Augmented Generation" in history
        assert "User: Tell me more" in history
        assert "Assistant: RAG combines retrieval with generation" in history

    def test_get_conversation_history_nonexistent_session(self):
        """Test getting history for non-existent session returns None"""
        sm = SessionManager()

        history = sm.get_conversation_history("nonexistent_session")

        assert history is None

    def test_get_conversation_history_empty_session(self):
        """Test getting history for empty session returns None"""
        sm = SessionManager()
        session_id = sm.create_session()

        history = sm.get_conversation_history(session_id)

        assert history is None

    def test_get_conversation_history_with_none(self):
        """Test getting history with None session ID returns None"""
        sm = SessionManager()

        history = sm.get_conversation_history(None)

        assert history is None


@pytest.mark.unit
class TestHistoryTruncation:
    """Test conversation history truncation"""

    def test_history_truncates_when_exceeding_max(self):
        """Test that history is truncated when exceeding max_history"""
        sm = SessionManager(max_history=2)  # Keep only 2 exchanges (4 messages)
        session_id = sm.create_session()

        # Add 4 exchanges (8 messages total)
        sm.add_exchange(session_id, "Q1", "A1")
        sm.add_exchange(session_id, "Q2", "A2")
        sm.add_exchange(session_id, "Q3", "A3")
        sm.add_exchange(session_id, "Q4", "A4")

        # Should keep only last 2 exchanges (4 messages)
        assert len(sm.sessions[session_id]) == 4
        assert sm.sessions[session_id][0].content == "Q3"
        assert sm.sessions[session_id][1].content == "A3"
        assert sm.sessions[session_id][2].content == "Q4"
        assert sm.sessions[session_id][3].content == "A4"

    def test_history_keeps_messages_under_limit(self):
        """Test that history is preserved when under limit"""
        sm = SessionManager(max_history=5)
        session_id = sm.create_session()

        # Add 2 exchanges (4 messages total)
        sm.add_exchange(session_id, "Q1", "A1")
        sm.add_exchange(session_id, "Q2", "A2")

        # Should keep all messages
        assert len(sm.sessions[session_id]) == 4
        assert sm.sessions[session_id][0].content == "Q1"

    def test_history_truncation_maintains_order(self):
        """Test that truncation maintains chronological order"""
        sm = SessionManager(max_history=1)
        session_id = sm.create_session()

        sm.add_exchange(session_id, "Q1", "A1")
        sm.add_exchange(session_id, "Q2", "A2")
        sm.add_exchange(session_id, "Q3", "A3")

        # Should keep only last exchange
        assert len(sm.sessions[session_id]) == 2
        messages = sm.sessions[session_id]
        assert messages[0].role == "user"
        assert messages[0].content == "Q3"
        assert messages[1].role == "assistant"
        assert messages[1].content == "A3"


@pytest.mark.unit
class TestSessionClearing:
    """Test session clearing functionality"""

    def test_clear_session_removes_all_messages(self):
        """Test that clear_session removes all messages"""
        sm = SessionManager()
        session_id = sm.create_session()

        sm.add_exchange(session_id, "Q1", "A1")
        sm.add_exchange(session_id, "Q2", "A2")

        sm.clear_session(session_id)

        assert session_id in sm.sessions
        assert sm.sessions[session_id] == []

    def test_clear_nonexistent_session_does_nothing(self):
        """Test clearing non-existent session doesn't raise error"""
        sm = SessionManager()

        # Should not raise exception
        sm.clear_session("nonexistent_session")

        assert "nonexistent_session" not in sm.sessions


@pytest.mark.integration
class TestSessionManagerIntegration:
    """Integration tests for session manager"""

    def test_typical_conversation_flow(self):
        """Test a typical multi-turn conversation flow"""
        sm = SessionManager(max_history=3)

        # User starts conversation
        session_id = sm.create_session()
        assert session_id == "session_1"

        # First exchange
        sm.add_exchange(session_id, "What is RAG?", "RAG is Retrieval-Augmented Generation")
        history = sm.get_conversation_history(session_id)
        assert "What is RAG?" in history

        # Second exchange
        sm.add_exchange(session_id, "How does it work?", "It combines retrieval with AI")
        history = sm.get_conversation_history(session_id)
        assert "How does it work?" in history
        assert len(sm.sessions[session_id]) == 4

        # Third exchange
        sm.add_exchange(session_id, "Give an example", "For example, Q&A systems")
        history = sm.get_conversation_history(session_id)
        assert "Give an example" in history
        assert len(sm.sessions[session_id]) == 6

        # Fourth exchange (should trigger truncation)
        sm.add_exchange(session_id, "What about embeddings?", "Embeddings represent text")
        assert len(sm.sessions[session_id]) == 6  # Still 6 (3 exchanges)
        history = sm.get_conversation_history(session_id)
        assert "What is RAG?" not in history  # First exchange truncated
        assert "What about embeddings?" in history

    def test_multiple_concurrent_sessions(self):
        """Test managing multiple concurrent sessions"""
        sm = SessionManager()

        # Create multiple sessions
        session_1 = sm.create_session()
        session_2 = sm.create_session()
        session_3 = sm.create_session()

        # Add different conversations to each
        sm.add_exchange(session_1, "Tell me about RAG", "RAG info")
        sm.add_exchange(session_2, "Explain vectors", "Vector info")
        sm.add_exchange(session_3, "What is ChromaDB?", "ChromaDB info")

        # Verify independence
        history_1 = sm.get_conversation_history(session_1)
        history_2 = sm.get_conversation_history(session_2)
        history_3 = sm.get_conversation_history(session_3)

        assert "RAG info" in history_1
        assert "Vector info" in history_2
        assert "ChromaDB info" in history_3
        assert "RAG info" not in history_2
        assert "Vector info" not in history_3
