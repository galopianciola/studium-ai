# Studium Backend API

AI-powered educational content generation backend for Spanish-speaking university students. Transforms study materials into interactive learning activities using Claude Sonnet 4.

## Features

- **Document Upload & Processing**: PDF and image support with OCR
- **Spanish-Optimized AI Content**: Flashcards, multiple choice, true/false questions, and summaries
- **Claude Sonnet 4 Integration**: Premium educational content generation with fallback support
- **Multi-language Support**: Spanish (primary) and English content generation
- **Intelligent Fallback System**: Claude → OpenAI automatic failover
- **REST API**: Comprehensive endpoints for mobile app integration
- **Async Processing**: Background document processing with status tracking

## Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key (for Claude Sonnet 4)
- OpenAI API key (optional, for fallback)
- Tesseract OCR (for image processing)

### Installation

1. Clone and navigate to project:
```bash
cd studium
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Anthropic API key and optionally OpenAI API key
```

5. Run the API:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Document Processing
- `POST /api/v1/upload` - Upload PDF or image file
- `POST /api/v1/process/{document_id}` - Start document processing
- `GET /api/v1/process/{document_id}/status` - Check processing status
- `GET /api/v1/documents/{document_id}/text` - Get extracted text

### Content Generation (Spanish-Optimized)
- `POST /api/v1/generate/flashcards` - Generate flashcards
- `POST /api/v1/generate/multiple-choice` - Generate multiple choice questions
- `POST /api/v1/generate/true-false` - Generate true/false questions
- `POST /api/v1/generate/summary` - Generate content summary
- `POST /api/v1/generate` - Generate any content type

### Utility
- `GET /api/v1/health` - Health check
- `GET /api/v1/ai-status` - AI services status and configuration
- `DELETE /api/v1/documents/{document_id}` - Delete document

## Usage Example

```python
import requests

# 1. Upload document
with open("study_material.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload",
        files={"file": f}
    )
document_id = response.json()["document_id"]

# 2. Process document
requests.post(f"http://localhost:8000/api/v1/process/{document_id}")

# 3. Check processing status
status = requests.get(f"http://localhost:8000/api/v1/process/{document_id}/status")

# 4. Generate Spanish flashcards
flashcards_response = requests.post(
    "http://localhost:8000/api/v1/generate/flashcards",
    json={
        "text": status.json()["extracted_text"],
        "count": 5,
        "language": "es"
    }
)
```

## Configuration

Key environment variables in `.env`:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `CLAUDE_MODEL`: Claude model to use (default: claude-3-5-sonnet-20241022)
- `OPENAI_API_KEY`: Your OpenAI API key (optional, for fallback)
- `DEFAULT_LANGUAGE`: Default language for content generation (default: es)
- `PRIMARY_AI_SERVICE`: Primary AI service (default: claude)
- `MAX_FILE_SIZE`: Maximum upload size in bytes
- `UPLOAD_DIRECTORY`: Directory for uploaded files
- `LOG_LEVEL`: Logging level

## Project Structure

```
studium/
├── main.py                 # FastAPI application entry point
├── app/
│   ├── api/
│   │   └── routes.py       # API endpoints
│   ├── core/
│   │   ├── config.py       # Configuration settings
│   │   └── logging.py      # Logging setup
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   └── services/
│       ├── claude_service.py      # Claude AI integration
│       ├── unified_ai_service.py  # Multi-AI service with fallback
│       ├── ai_service.py          # OpenAI integration
│       └── document_processor.py  # Document processing
├── requirements.txt
└── .env.example
```

## Development

### Running Tests
```bash
# Test Spanish AI content generation
python test_spanish_ai.py

# Run unit tests
pytest
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## Hackathon Ready

This backend provides all core functionality needed for the Spanish-speaking Studium hackathon MVP:

✅ Document upload and processing  
✅ Claude Sonnet 4 AI-powered content generation in Spanish  
✅ Intelligent fallback system (Claude → OpenAI)  
✅ Mobile-optimized API design  
✅ Comprehensive error handling  
✅ Background processing  
✅ Production-ready structure  
✅ Spanish-optimized educational prompts  
✅ Multi-language support (Spanish/English)  

Perfect for Saturday's 12-hour development sprint targeting Spanish-speaking university students!