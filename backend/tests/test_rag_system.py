"""Unit tests for RAG system integration"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag_system import RAGSystem


@pytest.mark.unit
class TestRAGSystemInitialization:
    """Test RAG system initialization"""

    def test_rag_system_creates_components(self, test_config):
        """Test that RAG system initializes all components"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator'), \
             patch('rag_system.SessionManager'), \
             patch('rag_system.ToolManager'), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            assert rag.config == test_config
            assert hasattr(rag, 'document_processor')
            assert hasattr(rag, 'vector_store')
            assert hasattr(rag, 'ai_generator')
            assert hasattr(rag, 'session_manager')
            assert hasattr(rag, 'tool_manager')


@pytest.mark.unit
class TestRAGSystemQuery:
    """Test RAG system query functionality"""

    def test_query_without_session(self, test_config, mock_vector_store,
                                   mock_ai_generator, mock_session_manager,
                                   mock_tool_manager):
        """Test query processing without session ID"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Setup mocks
            mock_ai_generator.generate_response.return_value = "Test answer"
            mock_tool_manager.get_last_sources.return_value = []

            # Execute query
            answer, sources = rag.query("What is RAG?", session_id=None)

            # Assertions
            assert answer == "Test answer"
            assert sources == []
            mock_session_manager.get_conversation_history.assert_called_once_with(None)
            mock_ai_generator.generate_response.assert_called_once()
            mock_tool_manager.get_last_sources.assert_called_once()
            mock_tool_manager.reset_sources.assert_called_once()

    def test_query_with_session(self, test_config, mock_vector_store,
                               mock_ai_generator, mock_session_manager,
                               mock_tool_manager):
        """Test query processing with session ID"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Setup mocks
            mock_ai_generator.generate_response.return_value = "Follow-up answer"
            mock_tool_manager.get_last_sources.return_value = ["Source 1"]
            mock_session_manager.get_conversation_history.return_value = "User: Previous question\nAssistant: Previous answer"

            # Execute query
            answer, sources = rag.query("Tell me more", session_id="session_1")

            # Assertions
            assert answer == "Follow-up answer"
            assert sources == ["Source 1"]
            mock_session_manager.get_conversation_history.assert_called_once_with("session_1")
            mock_session_manager.add_exchange.assert_called_once_with("session_1", "Tell me more", "Follow-up answer")

    def test_query_updates_conversation_history(self, test_config, mock_vector_store,
                                               mock_ai_generator, mock_session_manager,
                                               mock_tool_manager):
        """Test that query updates conversation history"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Setup mocks
            mock_ai_generator.generate_response.return_value = "Answer"
            mock_tool_manager.get_last_sources.return_value = []

            # Execute query
            query_text = "What is prompt caching?"
            answer, _ = rag.query(query_text, session_id="session_1")

            # Verify conversation history was updated
            mock_session_manager.add_exchange.assert_called_once_with(
                "session_1", query_text, "Answer"
            )


@pytest.mark.unit
class TestRAGSystemDocumentManagement:
    """Test document management functionality"""

    def test_add_course_document_success(self, test_config, mock_vector_store,
                                        mock_ai_generator, mock_session_manager,
                                        mock_tool_manager, sample_course,
                                        sample_course_chunks):
        """Test adding a course document successfully"""
        mock_doc_processor = Mock()
        mock_doc_processor.process_course_document.return_value = (sample_course, sample_course_chunks)

        with patch('rag_system.DocumentProcessor', return_value=mock_doc_processor), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Execute
            course, num_chunks = rag.add_course_document("test_course.txt")

            # Assertions
            assert course == sample_course
            assert num_chunks == len(sample_course_chunks)
            mock_doc_processor.process_course_document.assert_called_once_with("test_course.txt")
            mock_vector_store.add_course_metadata.assert_called_once_with(sample_course)
            mock_vector_store.add_course_content.assert_called_once_with(sample_course_chunks)

    def test_add_course_document_handles_errors(self, test_config, mock_vector_store,
                                               mock_ai_generator, mock_session_manager,
                                               mock_tool_manager):
        """Test that add_course_document handles errors gracefully"""
        mock_doc_processor = Mock()
        mock_doc_processor.process_course_document.side_effect = Exception("Parse error")

        with patch('rag_system.DocumentProcessor', return_value=mock_doc_processor), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Execute
            course, num_chunks = rag.add_course_document("bad_file.txt")

            # Assertions
            assert course is None
            assert num_chunks == 0

    def test_add_course_folder_skips_existing(self, test_config, mock_vector_store,
                                             mock_ai_generator, mock_session_manager,
                                             mock_tool_manager, sample_course,
                                             sample_course_chunks, temp_docs_dir):
        """Test that add_course_folder skips existing courses"""
        mock_doc_processor = Mock()
        mock_doc_processor.process_course_document.return_value = (sample_course, sample_course_chunks)

        # Mock vector store to return existing course
        mock_vector_store.get_existing_course_titles.return_value = [sample_course.title]

        with patch('rag_system.DocumentProcessor', return_value=mock_doc_processor), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Execute
            num_courses, num_chunks = rag.add_course_folder(temp_docs_dir)

            # Assertions - course should be skipped
            assert num_courses == 0
            assert num_chunks == 0
            mock_vector_store.add_course_metadata.assert_not_called()

    def test_add_course_folder_clears_existing_when_requested(self, test_config, mock_vector_store,
                                                             mock_ai_generator, mock_session_manager,
                                                             mock_tool_manager, temp_docs_dir):
        """Test that add_course_folder clears data when requested"""
        mock_doc_processor = Mock()

        with patch('rag_system.DocumentProcessor', return_value=mock_doc_processor), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Execute with clear_existing=True
            rag.add_course_folder(temp_docs_dir, clear_existing=True)

            # Verify clear was called
            mock_vector_store.clear_all_data.assert_called_once()


@pytest.mark.unit
class TestRAGSystemAnalytics:
    """Test analytics functionality"""

    def test_get_course_analytics(self, test_config, mock_vector_store,
                                  mock_ai_generator, mock_session_manager,
                                  mock_tool_manager):
        """Test getting course analytics"""
        with patch('rag_system.DocumentProcessor'), \
             patch('rag_system.VectorStore', return_value=mock_vector_store), \
             patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
             patch('rag_system.SessionManager', return_value=mock_session_manager), \
             patch('rag_system.ToolManager', return_value=mock_tool_manager), \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            rag = RAGSystem(test_config)

            # Setup mocks
            mock_vector_store.get_course_count.return_value = 5
            mock_vector_store.get_existing_course_titles.return_value = [
                "Course 1", "Course 2", "Course 3", "Course 4", "Course 5"
            ]

            # Execute
            analytics = rag.get_course_analytics()

            # Assertions
            assert analytics["total_courses"] == 5
            assert len(analytics["course_titles"]) == 5
            assert "Course 1" in analytics["course_titles"]
            mock_vector_store.get_course_count.assert_called_once()
            mock_vector_store.get_existing_course_titles.assert_called_once()
