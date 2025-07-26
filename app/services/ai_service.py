import logging
import time
import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from app.core.config import settings
from app.models.schemas import (
    ActivityType, 
    Flashcard, 
    MultipleChoiceQuestion, 
    TrueFalseQuestion, 
    Summary
)

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        
    async def create_vector_store(self, text: str) -> FAISS:
        try:
            documents = [Document(page_content=text)]
            texts = self.text_splitter.split_documents(documents)
            
            if not texts:
                texts = [Document(page_content=text)]
            
            vector_store = await FAISS.afrom_documents(texts, self.embeddings)
            logger.info(f"Created vector store with {len(texts)} chunks")
            return vector_store
        
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    async def generate_flashcards(self, text: str, count: int = 5) -> List[Flashcard]:
        prompt = self._get_flashcard_prompt(text, count)
        
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            content = response.choices[0].message.content
            flashcards_data = json.loads(content)
            
            flashcards = [
                Flashcard(
                    question=item["question"],
                    answer=item["answer"],
                    difficulty=item.get("difficulty", "medium")
                )
                for item in flashcards_data["flashcards"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(flashcards)} flashcards in {processing_time:.2f}s")
            
            return flashcards
        
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            raise
    
    async def generate_multiple_choice(self, text: str, count: int = 5) -> List[MultipleChoiceQuestion]:
        prompt = self._get_multiple_choice_prompt(text, count)
        
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            content = response.choices[0].message.content
            questions_data = json.loads(content)
            
            questions = [
                MultipleChoiceQuestion(
                    question=item["question"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=item.get("explanation", "")
                )
                for item in questions_data["questions"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(questions)} multiple choice questions in {processing_time:.2f}s")
            
            return questions
        
        except Exception as e:
            logger.error(f"Error generating multiple choice questions: {str(e)}")
            raise
    
    async def generate_true_false(self, text: str, count: int = 5) -> List[TrueFalseQuestion]:
        prompt = self._get_true_false_prompt(text, count)
        
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            content = response.choices[0].message.content
            questions_data = json.loads(content)
            
            questions = [
                TrueFalseQuestion(
                    statement=item["statement"],
                    correct_answer=item["correct_answer"],
                    explanation=item.get("explanation", "")
                )
                for item in questions_data["questions"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(questions)} true/false questions in {processing_time:.2f}s")
            
            return questions
        
        except Exception as e:
            logger.error(f"Error generating true/false questions: {str(e)}")
            raise
    
    async def generate_summary(self, text: str) -> List[Summary]:
        prompt = self._get_summary_prompt(text)
        
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE
            )
            
            content = response.choices[0].message.content
            summary_data = json.loads(content)
            
            summary = Summary(
                title=summary_data["title"],
                content=summary_data["content"],
                key_points=summary_data["key_points"]
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Generated summary in {processing_time:.2f}s")
            
            return [summary]
        
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    def _get_flashcard_prompt(self, text: str, count: int) -> str:
        return f"""
Create {count} educational flashcards from the following study material. 
Generate diverse, meaningful questions that test key concepts and facts.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "flashcards": [
        {{
            "question": "Clear, specific question",
            "answer": "Comprehensive answer",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}

Requirements:
- Focus on the most important concepts
- Questions should be clear and unambiguous
- Answers should be complete but concise
- Vary difficulty levels
- Ensure questions test understanding, not just memorization
"""
    
    def _get_multiple_choice_prompt(self, text: str, count: int) -> str:
        return f"""
Create {count} multiple choice questions from the following study material.
Generate challenging questions with 4 answer options each.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "questions": [
        {{
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Brief explanation of why this answer is correct"
        }}
    ]
}}

Requirements:
- Make questions test conceptual understanding
- Include plausible distractors as wrong answers
- correct_answer should be the index (0-3) of the correct option
- Ensure explanations are educational and brief
- Vary question types (factual, conceptual, application)
"""
    
    def _get_true_false_prompt(self, text: str, count: int) -> str:
        return f"""
Create {count} true/false questions from the following study material.
Generate statements that test key concepts and facts.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "questions": [
        {{
            "statement": "A clear statement that can be evaluated as true or false",
            "correct_answer": true,
            "explanation": "Brief explanation of why this statement is true/false"
        }}
    ]
}}

Requirements:
- Create statements that are definitively true or false
- Avoid ambiguous or trick statements
- Mix both true and false statements
- Focus on important concepts from the material
- Include brief explanations for learning
"""
    
    def _get_summary_prompt(self, text: str) -> str:
        return f"""
Create a comprehensive summary of the following study material.
Focus on the main concepts, key points, and important details.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "title": "Descriptive title for the content",
    "content": "Comprehensive summary paragraph covering main concepts",
    "key_points": ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"]
}}

Requirements:
- Title should be descriptive and specific
- Content should be a well-structured paragraph summarizing main ideas
- Include 5-7 key points that capture the most important information
- Focus on understanding rather than memorization
- Use clear, educational language
"""

    async def generate_content(
        self, 
        text: str, 
        activity_type: ActivityType, 
        count: int = 5
    ) -> Dict[str, Any]:
        if activity_type == ActivityType.FLASHCARD:
            activities = await self.generate_flashcards(text, count)
        elif activity_type == ActivityType.MULTIPLE_CHOICE:
            activities = await self.generate_multiple_choice(text, count)
        elif activity_type == ActivityType.TRUE_FALSE:
            activities = await self.generate_true_false(text, count)
        elif activity_type == ActivityType.SUMMARY:
            activities = await self.generate_summary(text)
        else:
            raise ValueError(f"Unsupported activity type: {activity_type}")
        
        return {
            "activity_type": activity_type,
            "count": len(activities),
            "activities": [activity.dict() for activity in activities]
        }