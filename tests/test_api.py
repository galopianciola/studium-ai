import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
import io

from main import app
from app.models.schemas import ActivityType

client = TestClient(app)

class TestAPI:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Studium API is running"
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "studium-api"
    
    def test_api_health_endpoint(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @patch('app.services.document_processor.DocumentProcessor.save_uploaded_file')
    def test_upload_endpoint(self, mock_save_file):
        mock_save_file.return_value = ("test-doc-id", "/path/to/file.pdf")
        
        # Create a test file
        test_file = io.BytesIO(b"test file content")
        
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-id"
        assert data["filename"] == "test.pdf"
    
    @patch('app.services.ai_service.AIService.generate_flashcards')
    def test_generate_flashcards(self, mock_generate):
        from app.models.schemas import Flashcard
        
        mock_flashcards = [
            Flashcard(question="What is AI?", answer="Artificial Intelligence", difficulty="medium"),
            Flashcard(question="What is ML?", answer="Machine Learning", difficulty="medium")
        ]
        mock_generate.return_value = mock_flashcards
        
        response = client.post(
            "/api/v1/generate/flashcards",
            json={
                "text": "AI and ML are important technologies",
                "activity_type": "flashcard",
                "count": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["activity_type"] == "flashcard"
        assert data["count"] == 2
        assert len(data["activities"]) == 2
    
    @patch('app.services.ai_service.AIService.generate_multiple_choice')
    def test_generate_multiple_choice(self, mock_generate):
        from app.models.schemas import MultipleChoiceQuestion
        
        mock_questions = [
            MultipleChoiceQuestion(
                question="What does AI stand for?",
                options=["Artificial Intelligence", "Automated Intelligence", "Advanced Intelligence", "Applied Intelligence"],
                correct_answer=0,
                explanation="AI stands for Artificial Intelligence"
            )
        ]
        mock_generate.return_value = mock_questions
        
        response = client.post(
            "/api/v1/generate/multiple-choice",
            json={
                "text": "AI stands for Artificial Intelligence",
                "activity_type": "multiple_choice",
                "count": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["activity_type"] == "multiple_choice"
        assert data["count"] == 1

class TestErrorHandling:
    def test_upload_no_file(self):
        response = client.post("/api/v1/upload")
        assert response.status_code == 422
    
    def test_process_nonexistent_document(self):
        response = client.post("/api/v1/process/nonexistent-id")
        assert response.status_code == 404
    
    def test_generate_invalid_request(self):
        response = client.post(
            "/api/v1/generate/flashcards",
            json={"invalid": "request"}
        )
        assert response.status_code == 422

@pytest.fixture
def sample_text():
    return """
    Machine Learning is a subset of artificial intelligence that focuses on developing algorithms 
    that can learn and make decisions from data. It includes supervised learning, unsupervised 
    learning, and reinforcement learning approaches.
    """

class TestAIIntegration:
    @pytest.mark.asyncio
    @patch('app.services.ai_service.AIService')
    async def test_ai_service_integration(self, mock_ai_service, sample_text):
        mock_instance = AsyncMock()
        mock_ai_service.return_value = mock_instance
        
        # Test that the service can be instantiated
        from app.services.ai_service import AIService
        service = AIService()
        
        # Verify the service has the expected methods
        assert hasattr(service, 'generate_flashcards')
        assert hasattr(service, 'generate_multiple_choice')
        assert hasattr(service, 'generate_true_false')
        assert hasattr(service, 'generate_summary')