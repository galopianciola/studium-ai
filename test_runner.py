#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.ai_service import AIService
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

async def test_document_processing():
    """Test document processing with sample file"""
    print("🔄 Testing document processing...")
    
    processor = DocumentProcessor()
    
    # Test with sample text file
    sample_file = Path("sample_documents/machine_learning_basics.txt")
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            text = f.read()
        
        # Test text cleaning
        cleaned_text = processor.clean_text(text)
        word_count = len(cleaned_text.split())
        
        print(f"✅ Text processing: {word_count} words extracted")
        return cleaned_text
    else:
        print("❌ Sample document not found")
        return None

async def test_ai_service(text):
    """Test AI service with sample text"""
    if not text:
        print("❌ No text to test with")
        return
    
    if not settings.OPENAI_API_KEY:
        print("⚠️  No OpenAI API key configured - skipping AI tests")
        return
    
    print("🔄 Testing AI service...")
    
    try:
        ai_service = AIService()
        
        # Test flashcard generation
        print("  Testing flashcard generation...")
        flashcards = await ai_service.generate_flashcards(text[:1000], count=2)
        print(f"  ✅ Generated {len(flashcards)} flashcards")
        
        # Print sample flashcard
        if flashcards:
            print(f"    Sample: Q: {flashcards[0].question}")
            print(f"            A: {flashcards[0].answer}")
        
        # Test multiple choice generation
        print("  Testing multiple choice generation...")
        questions = await ai_service.generate_multiple_choice(text[:1000], count=1)
        print(f"  ✅ Generated {len(questions)} multiple choice questions")
        
        # Print sample question
        if questions:
            print(f"    Sample: {questions[0].question}")
            for i, option in enumerate(questions[0].options):
                marker = "✓" if i == questions[0].correct_answer else " "
                print(f"            {marker} {option}")
        
        # Test summary generation
        print("  Testing summary generation...")
        summaries = await ai_service.generate_summary(text[:1500])
        print(f"  ✅ Generated summary")
        
        if summaries:
            print(f"    Title: {summaries[0].title}")
            print(f"    Key points: {len(summaries[0].key_points)}")
    
    except Exception as e:
        print(f"❌ AI service test failed: {str(e)}")

def test_api_structure():
    """Test that all modules can be imported"""
    print("🔄 Testing API structure...")
    
    try:
        from app.models.schemas import (
            ActivityType, Flashcard, MultipleChoiceQuestion, 
            TrueFalseQuestion, Summary
        )
        from app.api.routes import router
        from app.core.config import settings
        
        print("✅ All modules import successfully")
        print(f"  Project: {settings.PROJECT_NAME}")
        print(f"  Max file size: {settings.MAX_FILE_SIZE} bytes")
        print(f"  Allowed extensions: {settings.ALLOWED_EXTENSIONS}")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Studium Backend Test Suite")
    print("=" * 50)
    
    # Test API structure
    test_api_structure()
    print()
    
    # Test document processing
    text = await test_document_processing()
    print()
    
    # Test AI service
    await test_ai_service(text)
    print()
    
    print("=" * 50)
    print("🎉 Test suite completed!")
    print()
    print("📝 Next steps:")
    print("1. Set your OPENAI_API_KEY in .env file")
    print("2. Run: python main.py")
    print("3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())