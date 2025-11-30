"""Shared test fixtures and configuration for pytest"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any
import tempfile
import os

# Import app components for mocking
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from models import Course, Lesson, CourseChunk


@pytest.fixture
def test_config():
    """Provide a test configuration"""
    return Config(
        ANTHROPIC_API_KEY="test-api-key",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        CHROMA_PATH="./test_chroma_db"
    )


@pytest.fixture
def sample_course():
    """Provide a sample course object for testing"""
    lessons = [
        Lesson(
            number=1,
            title="Introduction to RAG",
            link="https://example.com/lesson1",
            content="This is lesson 1 about RAG systems."
        ),
        Lesson(
            number=2,
            title="Vector Databases",
            link="https://example.com/lesson2",
            content="This is lesson 2 about vector databases."
        )
    ]

    return Course(
        title="RAG Systems 101",
        link="https://example.com/course",
        instructor="Dr. Jane Smith",
        lessons=lessons
    )


@pytest.fixture
def sample_course_chunks(sample_course):
    """Provide sample course chunks for testing"""
    return [
        CourseChunk(
            course_title=sample_course.title,
            course_link=sample_course.link,
            course_instructor=sample_course.instructor,
            lesson_number=1,
            lesson_title="Introduction to RAG",
            lesson_link="https://example.com/lesson1",
            content="Course RAG Systems 101 Lesson 1 content: This is lesson 1 about RAG systems.",
            chunk_index=0
        ),
        CourseChunk(
            course_title=sample_course.title,
            course_link=sample_course.link,
            course_instructor=sample_course.instructor,
            lesson_number=2,
            lesson_title="Vector Databases",
            lesson_link="https://example.com/lesson2",
            content="Course RAG Systems 101 Lesson 2 content: This is lesson 2 about vector databases.",
            chunk_index=0
        )
    ]


@pytest.fixture
def mock_vector_store():
    """Provide a mocked vector store"""
    mock = Mock()
    mock.add_course_metadata = Mock()
    mock.add_course_content = Mock()
    mock.search_courses = Mock(return_value=[])
    mock.search_course_content = Mock(return_value=[])
    mock.get_existing_course_titles = Mock(return_value=[])
    mock.get_course_count = Mock(return_value=0)
    mock.clear_all_data = Mock()
    return mock


@pytest.fixture
def mock_ai_generator():
    """Provide a mocked AI generator"""
    mock = Mock()
    mock.generate_response = Mock(return_value="This is a test response.")
    return mock


@pytest.fixture
def mock_session_manager():
    """Provide a mocked session manager"""
    mock = Mock()
    mock.create_session = Mock(return_value="session_1")
    mock.add_exchange = Mock()
    mock.get_conversation_history = Mock(return_value=None)
    mock.clear_session = Mock()
    return mock


@pytest.fixture
def mock_tool_manager():
    """Provide a mocked tool manager"""
    mock = Mock()
    mock.get_tool_definitions = Mock(return_value=[])
    mock.get_last_sources = Mock(return_value=[])
    mock.reset_sources = Mock()
    mock.execute_tool = Mock(return_value="Search results")
    return mock


@pytest.fixture
def mock_document_processor():
    """Provide a mocked document processor"""
    mock = Mock()
    return mock


@pytest.fixture
def temp_docs_dir(sample_course):
    """Create a temporary directory with sample course documents"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample course text file
        course_file = os.path.join(tmpdir, "sample_course.txt")
        with open(course_file, 'w', encoding='utf-8') as f:
            f.write(f"Course Title: {sample_course.title}\n")
            f.write(f"Course Link: {sample_course.link}\n")
            f.write(f"Course Instructor: {sample_course.instructor}\n\n")
            for lesson in sample_course.lessons:
                f.write(f"Lesson {lesson.number}: {lesson.title}\n")
                f.write(f"Lesson Link: {lesson.link}\n")
                f.write(f"{lesson.content}\n\n")

        yield tmpdir


@pytest.fixture
def sample_query_data():
    """Provide sample query request/response data"""
    return {
        "query": "What is RAG?",
        "session_id": "session_1",
        "expected_answer": "RAG stands for Retrieval-Augmented Generation.",
        "expected_sources": [
            "RAG Systems 101 - Lesson 1: Introduction to RAG"
        ]
    }


@pytest.fixture
def mock_rag_system(mock_vector_store, mock_ai_generator, mock_session_manager, mock_tool_manager):
    """Provide a fully mocked RAG system"""
    mock = Mock()
    mock.vector_store = mock_vector_store
    mock.ai_generator = mock_ai_generator
    mock.session_manager = mock_session_manager
    mock.tool_manager = mock_tool_manager

    # Mock query method
    mock.query = Mock(return_value=("Test answer", []))

    # Mock analytics method
    mock.get_course_analytics = Mock(return_value={
        "total_courses": 1,
        "course_titles": ["RAG Systems 101"]
    })

    # Mock document adding methods
    mock.add_course_document = Mock(return_value=(None, 0))
    mock.add_course_folder = Mock(return_value=(1, 2))

    return mock


@pytest.fixture
def api_test_data():
    """Provide test data for API endpoint testing"""
    return {
        "valid_query": {
            "query": "What is prompt caching?",
            "session_id": None
        },
        "valid_query_with_session": {
            "query": "Tell me more about that",
            "session_id": "session_1"
        },
        "invalid_query": {
            "query": "",
            "session_id": None
        },
        "expected_response": {
            "answer": "Prompt caching is a feature...",
            "sources": [],
            "session_id": "session_1"
        },
        "expected_courses": {
            "total_courses": 3,
            "course_titles": [
                "RAG Systems 101",
                "Vector Databases Advanced",
                "AI Engineering Basics"
            ]
        }
    }
