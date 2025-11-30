"""API endpoint tests for FastAPI application"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def create_test_app(mock_rag_system):
    """
    Create a test FastAPI app without static file mounting.
    This avoids the issue where frontend directory doesn't exist in tests.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from pydantic import BaseModel
    from typing import List, Optional, Union

    # Use the same models from the main app
    from app import QueryRequest, QueryResponse, SourceItem, CourseStats

    # Create test app
    test_app = FastAPI(title="Course Materials RAG System - Test", root_path="")

    # Add middleware
    test_app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Store mock in app state
    test_app.state.rag_system = mock_rag_system

    # Define test endpoints (same as production but using mock)
    @test_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            rag_system = test_app.state.rag_system

            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            # Process query using RAG system
            answer, sources = rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            rag_system = test_app.state.rag_system
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/")
    async def root():
        """Root endpoint for health check"""
        return {"status": "ok", "message": "RAG System API is running"}

    return test_app


@pytest.fixture
def test_client(mock_rag_system):
    """Provide a test client for the FastAPI app"""
    app = create_test_app(mock_rag_system)
    return TestClient(app)


@pytest.mark.api
class TestQueryEndpoint:
    """Test cases for /api/query endpoint"""

    def test_query_without_session(self, test_client, mock_rag_system):
        """Test query endpoint without existing session"""
        # Setup mock
        mock_rag_system.session_manager.create_session.return_value = "session_1"
        mock_rag_system.query.return_value = ("Test answer", [])

        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": "What is RAG?"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "session_1"
        assert data["answer"] == "Test answer"

        # Verify mocks were called
        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once_with("What is RAG?", "session_1")

    def test_query_with_existing_session(self, test_client, mock_rag_system):
        """Test query endpoint with existing session"""
        # Setup mock
        mock_rag_system.query.return_value = ("Follow-up answer", [])

        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": "session_1"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session_1"
        assert data["answer"] == "Follow-up answer"

        # Verify session creation was NOT called
        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("Tell me more", "session_1")

    def test_query_with_sources(self, test_client, mock_rag_system):
        """Test query endpoint returns sources"""
        # Setup mock with sources
        sources = [
            "RAG Systems 101 - Lesson 1: Introduction",
            "Vector DB Course - Lesson 3: Embeddings"
        ]
        mock_rag_system.session_manager.create_session.return_value = "session_1"
        mock_rag_system.query.return_value = ("Answer with sources", sources)

        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": "Explain embeddings"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2
        assert data["sources"] == sources

    def test_query_with_empty_query(self, test_client, mock_rag_system):
        """Test query endpoint with empty query string"""
        # Setup mock
        mock_rag_system.session_manager.create_session.return_value = "session_1"
        mock_rag_system.query.return_value = ("Please provide a question", [])

        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )

        # Should still return 200 (validation happens at AI level)
        assert response.status_code == 200

    def test_query_endpoint_error_handling(self, test_client, mock_rag_system):
        """Test query endpoint handles errors gracefully"""
        # Setup mock to raise exception
        mock_rag_system.session_manager.create_session.return_value = "session_1"
        mock_rag_system.query.side_effect = Exception("AI service unavailable")

        # Make request
        response = test_client.post(
            "/api/query",
            json={"query": "What is RAG?"}
        )

        # Assertions
        assert response.status_code == 500
        assert "AI service unavailable" in response.json()["detail"]

    def test_query_invalid_json(self, test_client):
        """Test query endpoint with invalid JSON"""
        # Make request with missing required field
        response = test_client.post(
            "/api/query",
            json={"invalid_field": "value"}
        )

        # Should return validation error
        assert response.status_code == 422


@pytest.mark.api
class TestCoursesEndpoint:
    """Test cases for /api/courses endpoint"""

    def test_get_courses_success(self, test_client, mock_rag_system):
        """Test courses endpoint returns analytics"""
        # Setup mock
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": [
                "RAG Systems 101",
                "Vector Databases",
                "AI Engineering"
            ]
        }

        # Make request
        response = test_client.get("/api/courses")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "RAG Systems 101" in data["course_titles"]

        # Verify mock was called
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_courses_empty_catalog(self, test_client, mock_rag_system):
        """Test courses endpoint with no courses"""
        # Setup mock
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        # Make request
        response = test_client.get("/api/courses")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_error_handling(self, test_client, mock_rag_system):
        """Test courses endpoint handles errors"""
        # Setup mock to raise exception
        mock_rag_system.get_course_analytics.side_effect = Exception("Database error")

        # Make request
        response = test_client.get("/api/courses")

        # Assertions
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


@pytest.mark.api
class TestRootEndpoint:
    """Test cases for root endpoint"""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns health check"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "message" in data


@pytest.mark.api
class TestCORSAndMiddleware:
    """Test CORS and middleware configuration"""

    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are set correctly"""
        response = test_client.options(
            "/api/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_api_accepts_cross_origin_requests(self, test_client, mock_rag_system):
        """Test that API accepts requests from different origins"""
        mock_rag_system.session_manager.create_session.return_value = "session_1"
        mock_rag_system.query.return_value = ("Answer", [])

        response = test_client.post(
            "/api/query",
            json={"query": "Test"},
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
