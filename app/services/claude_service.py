import logging
import time
import json
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.models.schemas import (
    ActivityType, 
    Flashcard, 
    MultipleChoiceQuestion, 
    TrueFalseQuestion, 
    Summary
)

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude service")
        
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = settings.CLAUDE_TEMPERATURE
        
    async def generate_flashcards(self, text: str, count: int = 5, language: str = "es") -> List[Flashcard]:
        prompt = self._get_flashcard_prompt(text, count, language)
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            flashcards_data = json.loads(content)
            
            flashcards = [
                Flashcard(
                    question=item["pregunta"],
                    answer=item["respuesta"],
                    difficulty=item.get("dificultad", "medio")
                )
                for item in flashcards_data["tarjetas"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(flashcards)} flashcards in Spanish in {processing_time:.2f}s")
            
            return flashcards
        
        except Exception as e:
            logger.error(f"Error generating flashcards with Claude: {str(e)}")
            raise
    
    async def generate_multiple_choice(self, text: str, count: int = 5, language: str = "es") -> List[MultipleChoiceQuestion]:
        prompt = self._get_multiple_choice_prompt(text, count, language)
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            questions_data = json.loads(content)
            
            questions = [
                MultipleChoiceQuestion(
                    question=item["pregunta"],
                    options=item["opciones"],
                    correct_answer=item["respuesta_correcta"],
                    explanation=item.get("explicacion", "")
                )
                for item in questions_data["preguntas"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(questions)} multiple choice questions in Spanish in {processing_time:.2f}s")
            
            return questions
        
        except Exception as e:
            logger.error(f"Error generating multiple choice questions with Claude: {str(e)}")
            raise
    
    async def generate_true_false(self, text: str, count: int = 5, language: str = "es") -> List[TrueFalseQuestion]:
        prompt = self._get_true_false_prompt(text, count, language)
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            questions_data = json.loads(content)
            
            questions = [
                TrueFalseQuestion(
                    statement=item["afirmacion"],
                    correct_answer=item["respuesta_correcta"],
                    explanation=item.get("explicacion", "")
                )
                for item in questions_data["preguntas"][:count]
            ]
            
            processing_time = time.time() - start_time
            logger.info(f"Generated {len(questions)} true/false questions in Spanish in {processing_time:.2f}s")
            
            return questions
        
        except Exception as e:
            logger.error(f"Error generating true/false questions with Claude: {str(e)}")
            raise
    
    async def generate_summary(self, text: str, language: str = "es") -> List[Summary]:
        prompt = self._get_summary_prompt(text, language)
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            summary_data = json.loads(content)
            
            summary = Summary(
                title=summary_data["titulo"],
                content=summary_data["contenido"],
                key_points=summary_data["puntos_clave"]
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Generated summary in Spanish in {processing_time:.2f}s")
            
            return [summary]
        
        except Exception as e:
            logger.error(f"Error generating summary with Claude: {str(e)}")
            raise
    
    def _get_flashcard_prompt(self, text: str, count: int, language: str) -> str:
        if language == "es":
            return f"""
Crea {count} tarjetas de estudio (flashcards) educativas a partir del siguiente material de estudio. 
Genera preguntas diversas y significativas que evalúen conceptos clave y datos importantes.
Usa un español claro y educativo, apropiado para estudiantes universitarios.

Material de estudio:
{text}

Devuelve la respuesta como JSON en este formato exacto:
{{
    "tarjetas": [
        {{
            "pregunta": "Pregunta clara y específica",
            "respuesta": "Respuesta completa pero concisa",
            "dificultad": "fácil|medio|difícil"
        }}
    ]
}}

Requisitos:
- Enfócate en los conceptos más importantes
- Las preguntas deben ser claras e inequívocas
- Las respuestas deben ser completas pero concisas
- Varía los niveles de dificultad
- Asegúrate de que las preguntas evalúen comprensión, no solo memorización
- Usa terminología académica apropiada en español
"""
        else:
            return f"""
Create {count} educational flashcards from the following study material. 
Generate diverse, meaningful questions that test key concepts and facts.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "tarjetas": [
        {{
            "pregunta": "Clear, specific question",
            "respuesta": "Comprehensive answer",
            "dificultad": "easy|medium|hard"
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
    
    def _get_multiple_choice_prompt(self, text: str, count: int, language: str) -> str:
        if language == "es":
            return f"""
Crea {count} preguntas de opción múltiple a partir del siguiente material de estudio.
Genera preguntas desafiantes con 4 opciones de respuesta cada una.
Usa un español académico claro y apropiado para estudiantes universitarios.

Material de estudio:
{text}

Devuelve la respuesta como JSON en este formato exacto:
{{
    "preguntas": [
        {{
            "pregunta": "Texto de la pregunta aquí",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "respuesta_correcta": 0,
            "explicacion": "Breve explicación de por qué esta respuesta es correcta"
        }}
    ]
}}

Requisitos:
- Haz preguntas que evalúen comprensión conceptual
- Incluye distractores plausibles como respuestas incorrectas
- respuesta_correcta debe ser el índice (0-3) de la opción correcta
- Asegúrate de que las explicaciones sean educativas y breves
- Varía los tipos de pregunta (factual, conceptual, aplicación)
- Usa terminología académica apropiada en español
"""
        else:
            return f"""
Create {count} multiple choice questions from the following study material.
Generate challenging questions with 4 answer options each.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "preguntas": [
        {{
            "pregunta": "Question text here",
            "opciones": ["Option A", "Option B", "Option C", "Option D"],
            "respuesta_correcta": 0,
            "explicacion": "Brief explanation of why this answer is correct"
        }}
    ]
}}

Requirements:
- Make questions test conceptual understanding
- Include plausible distractors as wrong answers
- respuesta_correcta should be the index (0-3) of the correct option
- Ensure explanations are educational and brief
- Vary question types (factual, conceptual, application)
"""
    
    def _get_true_false_prompt(self, text: str, count: int, language: str) -> str:
        if language == "es":
            return f"""
Crea {count} preguntas de verdadero/falso a partir del siguiente material de estudio.
Genera afirmaciones que evalúen conceptos clave y datos importantes.
Usa un español académico claro y apropiado para estudiantes universitarios.

Material de estudio:
{text}

Devuelve la respuesta como JSON en este formato exacto:
{{
    "preguntas": [
        {{
            "afirmacion": "Una afirmación clara que pueda evaluarse como verdadera o falsa",
            "respuesta_correcta": true,
            "explicacion": "Breve explicación de por qué esta afirmación es verdadera/falsa"
        }}
    ]
}}

Requisitos:
- Crea afirmaciones que sean definitivamente verdaderas o falsas
- Evita afirmaciones ambiguas o capciosas
- Mezcla afirmaciones tanto verdaderas como falsas
- Enfócate en conceptos importantes del material
- Incluye breves explicaciones para el aprendizaje
- Usa terminología académica apropiada en español
"""
        else:
            return f"""
Create {count} true/false questions from the following study material.
Generate statements that test key concepts and facts.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "preguntas": [
        {{
            "afirmacion": "A clear statement that can be evaluated as true or false",
            "respuesta_correcta": true,
            "explicacion": "Brief explanation of why this statement is true/false"
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
    
    def _get_summary_prompt(self, text: str, language: str) -> str:
        if language == "es":
            return f"""
Crea un resumen completo del siguiente material de estudio.
Enfócate en los conceptos principales, puntos clave y detalles importantes.
Usa un español académico claro y apropiado para estudiantes universitarios.

Material de estudio:
{text}

Devuelve la respuesta como JSON en este formato exacto:
{{
    "titulo": "Título descriptivo para el contenido",
    "contenido": "Párrafo de resumen completo que cubra las ideas principales",
    "puntos_clave": ["Punto clave 1", "Punto clave 2", "Punto clave 3", "Punto clave 4", "Punto clave 5"]
}}

Requisitos:
- El título debe ser descriptivo y específico
- El contenido debe ser un párrafo bien estructurado que resuma las ideas principales
- Incluye 5-7 puntos clave que capturen la información más importante
- Enfócate en la comprensión más que en la memorización
- Usa lenguaje educativo claro
- Usa terminología académica apropiada en español
"""
        else:
            return f"""
Create a comprehensive summary of the following study material.
Focus on the main concepts, key points, and important details.

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "titulo": "Descriptive title for the content",
    "contenido": "Comprehensive summary paragraph covering main concepts",
    "puntos_clave": ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"]
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
        count: int = 5,
        language: str = "es"
    ) -> Dict[str, Any]:
        if activity_type == ActivityType.FLASHCARD:
            activities = await self.generate_flashcards(text, count, language)
        elif activity_type == ActivityType.MULTIPLE_CHOICE:
            activities = await self.generate_multiple_choice(text, count, language)
        elif activity_type == ActivityType.TRUE_FALSE:
            activities = await self.generate_true_false(text, count, language)
        elif activity_type == ActivityType.SUMMARY:
            activities = await self.generate_summary(text, language)
        else:
            raise ValueError(f"Unsupported activity type: {activity_type}")
        
        return {
            "activity_type": activity_type,
            "count": len(activities),
            "activities": [activity.dict() for activity in activities]
        }

    async def generate_mixed_activities(self, text: str, language: str = "es") -> Dict[str, Any]:
        """Generate a mix of different activity types in a single API call to avoid rate limiting"""
        prompt = self._get_mixed_activities_prompt(text, language)
        
        try:
            start_time = time.time()
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,  # Increased for multiple activities
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            activities_data = json.loads(content)
            
            mixed_activities = []
            
            # Process flashcards
            for item in activities_data.get("tarjetas", []):
                mixed_activities.append({
                    "type": "flashcard",
                    "question": item["pregunta"],
                    "answer": item["respuesta"],
                    "difficulty": item.get("dificultad", "medio")
                })
            
            # Process multiple choice questions
            for item in activities_data.get("opcion_multiple", []):
                mixed_activities.append({
                    "type": "multiple_choice",
                    "question": item["pregunta"],
                    "options": item["opciones"],
                    "correct_answer": item["respuesta_correcta"],
                    "explanation": item.get("explicacion", "")
                })
            
            # Process true/false questions
            for item in activities_data.get("verdadero_falso", []):
                mixed_activities.append({
                    "type": "true_false",
                    "statement": item["afirmacion"],
                    "correct_answer": item["respuesta_correcta"],
                    "explanation": item.get("explicacion", "")
                })
            
            logger.info(f"Generated {len(mixed_activities)} mixed activities in {language} in {time.time() - start_time:.2f}s")
            
            return {
                "activity_type": "mixed",
                "count": len(mixed_activities),
                "activities": mixed_activities
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for mixed activities: {str(e)}")
            logger.error(f"Response content: {content}")
            raise Exception(f"Failed to parse mixed activities response: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating mixed activities with Claude: {str(e)}")
            raise

    def _get_mixed_activities_prompt(self, text: str, language: str) -> str:
        if language == "es":
            return f"""
Crea actividades de estudio mixtas a partir del siguiente material:
- 3 tarjetas de memoria (flashcards)
- 2 preguntas de opción múltiple
- 2 preguntas de verdadero/falso

Usa un español académico claro y apropiado para estudiantes universitarios.

Material de estudio:
{text}

Devuelve la respuesta como JSON en este formato exacto:
{{
    "tarjetas": [
        {{
            "pregunta": "Pregunta para la tarjeta",
            "respuesta": "Respuesta detallada",
            "dificultad": "facil|medio|dificil"
        }}
    ],
    "opcion_multiple": [
        {{
            "pregunta": "Pregunta de opción múltiple",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "respuesta_correcta": 0,
            "explicacion": "Explicación breve de la respuesta correcta"
        }}
    ],
    "verdadero_falso": [
        {{
            "afirmacion": "Afirmación que puede evaluarse como verdadera o falsa",
            "respuesta_correcta": true,
            "explicacion": "Explicación de por qué es verdadera/falsa"
        }}
    ]
}}

Requisitos:
- Enfócate en conceptos clave del material
- Varía la dificultad de las preguntas
- Asegúrate de que las respuestas sean educativas
- Usa terminología académica apropiada en español
"""
        else:
            return f"""
Create mixed study activities from the following material:
- 3 flashcards
- 2 multiple choice questions  
- 2 true/false questions

Study Material:
{text}

Return the response as JSON in this exact format:
{{
    "tarjetas": [
        {{
            "pregunta": "Question for the card",
            "respuesta": "Detailed answer",
            "dificultad": "easy|medium|hard"
        }}
    ],
    "opcion_multiple": [
        {{
            "pregunta": "Multiple choice question",
            "opciones": ["Option A", "Option B", "Option C", "Option D"],
            "respuesta_correcta": 0,
            "explicacion": "Brief explanation of correct answer"
        }}
    ],
    "verdadero_falso": [
        {{
            "afirmacion": "Statement that can be evaluated as true or false",
            "respuesta_correcta": true,
            "explicacion": "Explanation of why it's true/false"
        }}
    ]
}}

Requirements:
- Focus on key concepts from the material
- Vary question difficulty
- Ensure answers are educational
- Use clear academic language
"""