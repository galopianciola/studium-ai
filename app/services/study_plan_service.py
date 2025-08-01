import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio

from app.models.schemas import (
    StudyTopic,
    DailyStudyPlan,
    TimelineData,
    StudyStatistics,
    StudyPlanResponse,
)

logger = logging.getLogger(__name__)


class StudyPlanService:
    """Service for generating comprehensive study plans using AI"""

    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def generate_study_plan(
        self,
        document_text: str,
        subject_name: str,
        exam_date: str,
        language: str = "es",
    ) -> StudyPlanResponse:
        """Generate a comprehensive study plan based on document content and exam date"""

        start_time = datetime.now()
        plan_id = str(uuid.uuid4())

        # Parse exam date and calculate days remaining
        exam_datetime = datetime.strptime(exam_date, "%Y-%m-%d")
        today = datetime.now().date()
        exam_date_obj = exam_datetime.date()
        days_remaining = (exam_date_obj - today).days

        # Determine urgency status
        status = "urgente" if days_remaining <= 7 else "normal"

        # Generate AI-based study plan
        ai_plan = await self._generate_ai_study_plan(
            document_text, subject_name, exam_date, language, days_remaining
        )

        # Process and structure the AI response
        structured_plan = self._structure_study_plan(
            ai_plan, subject_name, exam_date, days_remaining, plan_id, language, document_text
        )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        structured_plan["processing_time"] = processing_time

        return StudyPlanResponse(**structured_plan)

    async def _generate_ai_study_plan(
        self,
        document_text: str,
        subject_name: str,
        exam_date: str,
        language: str,
        days_remaining: int,
    ) -> Dict[str, Any]:
        """Generate study plan using AI service with optimized prompt"""

        today = datetime.now().strftime("%Y-%m-%d")

        # Intelligent content truncation to avoid token limits
        # Estimate ~4 chars per token for conservative calculation
        MAX_CONTENT_CHARS = 80000  # ~20K tokens for content, leaving room for prompt
        if len(document_text) > MAX_CONTENT_CHARS:
            # Truncate but try to end at a sentence boundary
            truncated_text = document_text[:MAX_CONTENT_CHARS]
            last_period = truncated_text.rfind('.')
            last_newline = truncated_text.rfind('\n')
            
            # Use the last sentence or paragraph boundary
            cutoff = max(last_period, last_newline) if max(last_period, last_newline) > MAX_CONTENT_CHARS * 0.9 else MAX_CONTENT_CHARS
            document_text = truncated_text[:cutoff] + "\n\n[DOCUMENTO TRUNCADO - ANÁLISIS BASADO EN CONTENIDO MOSTRADO]"

        # Prompt completamente en español optimizado para generar planes de estudio
        prompt = f"""Eres un tutor experto especializado en crear planes de estudio personalizados. A partir del siguiente contenido de estudio, genera un plan completo y detallado para un estudiante que debe rendir el examen de {subject_name} el día {exam_date}.

CONTEXTO:
- Fecha actual: {today}
- Días disponibles para estudiar: {days_remaining} días
- Materia: {subject_name}
- Fecha del examen: {exam_date}

CONTENIDO A ANALIZAR:
{document_text}

INSTRUCCIONES:
1. Detecta y lista los temas principales del contenido ordenados por importancia
2. Identifica los 3-5 temas más difíciles que necesitan atención extra
3. Distribuye los temas a lo largo de los días disponibles hasta el examen
4. Estima las horas de estudio por día y por tema

REQUERIMIENTOS ADICIONALES:
- Crea un cronograma día por día hasta el examen
- Incluye técnicas de estudio específicas para cada tema
- Proporciona recomendaciones generales de estudio
- Estima el tiempo necesario para cada actividad
- Identifica subtemas importantes dentro de cada tema principal
- Crea hitos importantes en el cronograma (repasos generales, evaluaciones intermedias, etc.)
- Establece fechas clave como puntos de control del progreso

IMPORTANTE: Todos los nombres de temas, descripciones y recomendaciones deben estar en ESPAÑOL.

REQUIRED JSON FORMAT (strict format, valid JSON only):
{{
    "main_topics": [
        {{
            "name": "Nombre del Tema",
            "importance": 5,
            "difficulty": "easy",
            "description": "Descripción del tema",
            "estimated_hours": 2.5,
            "subtopics": ["subtema1", "subtema2"]
        }}
    ],
    "difficult_topics": [
        {{
            "name": "Tema Difícil", 
            "importance": 5,
            "difficulty": "hard",
            "description": "Descripción del tema difícil",
            "estimated_hours": 4.0,
            "subtopics": ["subtema1", "subtema2"]
        }}
    ],
    "daily_plan": [
        {{
            "day": 1,
            "date": "2025-01-01", 
            "topics": ["topic1", "topic2"],
            "actions": ["action1", "action2"],
            "estimated_hours": 2.5
        }}
    ],
    "general_recommendations": [
        "recommendation1",
        "recommendation2"
    ],
    "study_techniques": [
        "technique1",
        "technique2"
    ],
    "milestones": [
        {{
            "date": "2025-01-10",
            "title": "Primera Evaluación",
            "description": "Revisar los primeros temas estudiados",
            "type": "checkpoint",
            "topics": ["topic1", "topic2"],
            "completion_target": 30,
            "study_focus": "Consolidar conceptos básicos y fundamentos",
            "study_activities": ["Resúmenes de conceptos clave", "Práctica con ejercicios básicos", "Flashcards de definiciones"],
            "learning_objectives": ["Dominar vocabulario fundamental", "Entender conceptos básicos", "Identificar patrones principales"]
        }},
        {{
            "date": "2025-01-15",
            "title": "Repaso General Parcial",
            "description": "Revisar todos los temas estudiados hasta la fecha",
            "type": "review",
            "topics": ["topic1", "topic2", "topic3"],
            "completion_target": 60,
            "study_focus": "Integrar conocimientos y hacer conexiones entre temas",
            "study_activities": ["Mapas conceptuales", "Resolución de problemas complejos", "Simulacros de examen"],
            "learning_objectives": ["Conectar diferentes temas", "Aplicar conocimientos en casos prácticos", "Identificar áreas débiles"]
        }},
        {{
            "date": "2025-01-20",
            "title": "Repaso Final",
            "description": "Repaso intensivo de todos los temas antes del examen",
            "type": "final_review",
            "topics": ["all_topics"],
            "completion_target": 90,
            "study_focus": "Repaso intensivo y perfeccionamiento de todos los temas",
            "study_activities": ["Exámenes de práctica", "Repaso de notas y resúmenes", "Técnicas de memorización"],
            "learning_objectives": ["Perfeccionar conocimientos", "Ganar confianza", "Optimizar estrategias de examen"]
        }}
    ],
    "statistics": {{
        "total_topics": 10,
        "total_hours": 25.0,
        "average_hours_per_day": 2.5
    }},
    "status": "normal"
}}

CRITICAL: Return ONLY valid JSON. No additional text, explanations, or markdown formatting. Ensure all field names match exactly as shown above."""

        # Use AI service to generate the plan
        try:
            # Since we need a custom prompt, we'll use the lower-level AI service
            if (
                hasattr(self.ai_service, "claude_service")
                and self.ai_service.claude_service
            ):
                response = await self._call_claude_for_study_plan(prompt, language)
            elif (
                hasattr(self.ai_service, "openai_service")
                and self.ai_service.openai_service
            ):
                response = await self._call_openai_for_study_plan(prompt, language)
            else:
                raise Exception("No AI service available")

            return response

        except Exception as e:
            logger.error(f"Error generating AI study plan: {str(e)}")
            # Fallback to basic plan structure
            return self._generate_fallback_plan(
                document_text, subject_name, days_remaining
            )

    async def _call_claude_for_study_plan(
        self, prompt: str, language: str
    ) -> Dict[str, Any]:
        """Call Claude service for study plan generation"""
        try:
            claude_service = self.ai_service.claude_service

            # Use the same pattern as other Claude service methods
            response = await claude_service.client.messages.create(
                model=claude_service.model,
                max_tokens=claude_service.max_tokens,
                temperature=claude_service.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Parse JSON response with enhanced error handling
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(
                    f"Content around error: {content[max(0, e.pos-50):e.pos+50]}"
                )

                # Try to extract JSON from response
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    # Clean up common JSON issues
                    json_str = json_str.replace("\n", " ").replace("\r", " ")
                    # Remove potential trailing commas
                    import re

                    json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e2:
                        logger.error(f"Cleaned JSON still invalid: {str(e2)}")
                        logger.error(f"Cleaned JSON: {json_str[:500]}...")
                        raise Exception(f"Invalid JSON in AI response: {str(e2)}")
                else:
                    raise Exception("No valid JSON found in response")

        except Exception as e:
            logger.error(f"Claude study plan generation failed: {str(e)}")
            raise

    async def _call_openai_for_study_plan(
        self, prompt: str, language: str = "es"
    ) -> Dict[str, Any]:
        """Call OpenAI service for study plan generation"""
        try:
            openai_service = self.ai_service.openai_service

            # Use the same pattern as other OpenAI service methods
            response = await openai_service.client.chat.completions.create(
                model="gpt-4o-mini",  # Use the configured model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )

            content = response.choices[0].message.content

            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise Exception("No valid JSON found in response")

        except Exception as e:
            logger.error(f"OpenAI study plan generation failed: {str(e)}")
            raise

    def _generate_fallback_plan(
        self, document_text: str, subject_name: str, days_remaining: int
    ) -> Dict[str, Any]:
        """Generate a basic fallback study plan when AI fails"""

        # Simple topic extraction (split by paragraphs/sections)
        topics = []
        text_sections = document_text.split("\n\n")
        for i, section in enumerate(text_sections[:10]):  # Limit to 10 topics
            if len(section.strip()) > 50:  # Only meaningful sections
                topics.append(
                    {
                        "name": f"Tema {i+1}",
                        "importance": 3,
                        "difficulty": "medium",
                        "description": (
                            section[:100] + "..." if len(section) > 100 else section
                        ),
                        "estimated_hours": 2.0,
                        "subtopics": [],
                    }
                )

        # Create basic daily plan
        daily_plan = []
        topics_per_day = max(1, len(topics) // max(1, days_remaining))

        for day in range(min(days_remaining, 14)):  # Max 14 days
            date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
            start_topic = day * topics_per_day
            end_topic = min(start_topic + topics_per_day, len(topics))

            day_topics = [t["name"] for t in topics[start_topic:end_topic]]

            daily_plan.append(
                {
                    "day": day + 1,
                    "date": date,
                    "topics": day_topics,
                    "actions": ["Leer material", "Tomar notas", "Crear flashcards"],
                    "estimated_hours": 2.0,
                }
            )

        return {
            "main_topics": topics,
            "difficult_topics": topics[:3],  # First 3 as difficult
            "daily_plan": daily_plan,
            "general_recommendations": [
                "Establece un horario fijo de estudio",
                "Toma descansos regulares",
                "Repasa diariamente",
            ],
            "study_techniques": ["Lectura activa", "Flashcards", "Resúmenes"],
            "statistics": {
                "total_topics": len(topics),
                "total_hours": len(daily_plan) * 2.0,
                "average_hours_per_day": 2.0,
            },
            "status": "urgent" if days_remaining <= 7 else "normal",
        }

    def _structure_study_plan(
        self,
        ai_plan: Dict[str, Any],
        subject_name: str,
        exam_date: str,
        days_remaining: int,
        plan_id: str,
        language: str,
        document_text: str,
    ) -> Dict[str, Any]:
        """Structure the AI-generated plan into the required response format"""

        # Convert AI plan to structured objects
        main_topics = [StudyTopic(**topic) for topic in ai_plan.get("main_topics", [])]

        hardest_topics = [
            StudyTopic(**topic) for topic in ai_plan.get("difficult_topics", [])
        ]

        daily_plan = [DailyStudyPlan(**day) for day in ai_plan.get("daily_plan", [])]

        # Generate timeline data
        milestones_data = ai_plan.get("milestones", [])
        timeline = self._generate_timeline_data(daily_plan, days_remaining, exam_date, milestones_data)

        # Generate statistics
        stats = ai_plan.get("statistics", {})
        statistics = StudyStatistics(
            total_topics=stats.get("total_topics", len(main_topics)),
            estimated_total_hours=stats.get(
                "total_hours", sum(d.estimated_hours for d in daily_plan)
            ),
            daily_average_hours=stats.get("average_hours_per_day", 2.0),
            hardest_topics_count=len(hardest_topics),
        )

        return {
            "plan_id": plan_id,
            "subject_name": subject_name,
            "exam_date": exam_date,
            "created_at": datetime.now().isoformat(),
            "status": ai_plan.get("status", "normal"),
            "main_topics": main_topics,
            "hardest_topics": hardest_topics,
            "daily_plan": daily_plan,
            "timeline": timeline,
            "statistics": statistics,
            "general_recommendations": ai_plan.get("general_recommendations", []),
            "study_techniques": ai_plan.get("study_techniques", []),
            "document_text": document_text,
            "language": language,
            "provider": getattr(self.ai_service, "last_used_provider", "unknown"),
        }

    def _generate_timeline_data(
        self, daily_plan: List[DailyStudyPlan], days_remaining: int, exam_date: str, milestones_data: List[Dict[str, Any]]
    ) -> TimelineData:
        """Generate timeline data for charts and visualization"""

        # Calculate weekly breakdown
        weekly_breakdown = []
        current_week = []
        week_hours = 0

        for day in daily_plan:
            current_week.append(
                {
                    "day": day.day,
                    "date": day.date,
                    "hours": day.estimated_hours,
                    "topics_count": len(day.topics),
                }
            )
            week_hours += day.estimated_hours

            # If we have 7 days or it's the last day, complete the week
            if len(current_week) == 7 or day == daily_plan[-1]:
                weekly_breakdown.append(
                    {
                        "week": len(weekly_breakdown) + 1,
                        "days": current_week,
                        "total_hours": week_hours,
                        "topics_count": sum(d["topics_count"] for d in current_week),
                    }
                )
                current_week = []
                week_hours = 0

        # Determine study intensity
        total_hours = sum(d.estimated_hours for d in daily_plan)
        avg_daily_hours = total_hours / max(1, len(daily_plan))

        if avg_daily_hours >= 4:
            intensity = "alta"
        elif avg_daily_hours >= 2:
            intensity = "media"
        else:
            intensity = "baja"

        # Process milestones from AI response
        from ..models.schemas import TimelineMilestone
        milestones = []
        for milestone_data in milestones_data:
            milestones.append(TimelineMilestone(**milestone_data))
        
        # Generate automatic milestones if not enough provided by AI
        if len(milestones) < 2 and days_remaining > 7:
            self._add_automatic_milestones(milestones, daily_plan, days_remaining, exam_date)
        
        # Add exam date as final milestone
        milestones.append(TimelineMilestone(
            date=exam_date,
            title="¡Día del Examen!",
            description="Fecha del examen final",
            type="exam",
            topics=[],
            completion_target=100
        ))
        
        # Sort milestones by date
        milestones.sort(key=lambda m: datetime.strptime(m.date, "%Y-%m-%d"))
        
        # Create exam countdown information
        exam_countdown = {
            "days_left": days_remaining,
            "exam_date": exam_date,
            "countdown_message": f"¡Quedan {days_remaining} días para el examen!",
            "urgency_level": "high" if days_remaining <= 7 else "medium" if days_remaining <= 14 else "low"
        }

        return TimelineData(
            total_days=len(daily_plan),
            days_remaining=days_remaining,
            study_intensity=intensity,
            weekly_breakdown=weekly_breakdown,
            milestones=milestones,
            exam_countdown=exam_countdown,
        )

    def _add_automatic_milestones(self, milestones: List, daily_plan: List[DailyStudyPlan], days_remaining: int, exam_date: str):
        """Generate automatic milestones when AI doesn't provide enough"""
        from ..models.schemas import TimelineMilestone
        
        today = datetime.now()
        
        # Create milestones at strategic intervals
        if days_remaining >= 21:  # 3+ weeks
            # Add milestones at 1/3, 2/3, and 90% of the way
            intervals = [0.33, 0.66, 0.9]
            titles = ["Revisión Temprana", "Revisión Intermedia", "Repaso Final"]
            types = ["checkpoint", "review", "final_review"]
            targets = [30, 70, 95]
        elif days_remaining >= 14:  # 2+ weeks
            intervals = [0.5, 0.85]
            titles = ["Revisión Intermedia", "Repaso Final"]
            types = ["review", "final_review"]
            targets = [50, 90]
        elif days_remaining >= 7:  # 1+ week
            intervals = [0.7]
            titles = ["Repaso Final"]
            types = ["final_review"]
            targets = [85]
        else:
            return  # Too close to exam for automatic milestones
        
        for interval, title, milestone_type, target in zip(intervals, titles, types, targets):
            milestone_date = today + timedelta(days=int(days_remaining * interval))
            milestone_date_str = milestone_date.strftime("%Y-%m-%d")
            
            # Get topics covered by this point
            covered_topics = []
            milestone_day = int(days_remaining * interval)
            for day in daily_plan[:milestone_day]:
                covered_topics.extend(day.topics)
            
            # Remove duplicates while preserving order
            unique_topics = []
            for topic in covered_topics:
                if topic not in unique_topics:
                    unique_topics.append(topic)
            
            # Generate study content based on milestone type
            study_focus, study_activities, learning_objectives = self._generate_milestone_content(milestone_type)
            
            milestone = TimelineMilestone(
                date=milestone_date_str,
                title=title,
                description=f"Revisar progreso y evaluar comprensión de los temas estudiados hasta ahora",
                type=milestone_type,
                topics=unique_topics[:5],  # Limit to first 5 topics
                completion_target=target,
                study_focus=study_focus,
                study_activities=study_activities,
                learning_objectives=learning_objectives
            )
            
            milestones.append(milestone)

    def _generate_milestone_content(self, milestone_type: str) -> tuple:
        """Generate study content for automatic milestones"""
        
        if milestone_type == "checkpoint":
            study_focus = "Consolidar fundamentos y verificar comprensión inicial"
            study_activities = [
                "Resumen de conceptos principales",
                "Autoevaluación con preguntas básicas",
                "Identificación de conceptos clave",
                "Creación de flashcards"
            ]
            learning_objectives = [
                "Dominar vocabulario y términos fundamentales",
                "Entender conceptos básicos del área de estudio",
                "Establecer bases sólidas para temas avanzados"
            ]
            
        elif milestone_type == "review":
            study_focus = "Integrar conocimientos y fortalecer conexiones entre temas"
            study_activities = [
                "Mapas conceptuales de temas relacionados",
                "Resolución de problemas intermedios",
                "Práctica con casos de estudio",
                "Simulacros de evaluación parcial"
            ]
            learning_objectives = [
                "Conectar diferentes temas y conceptos",
                "Aplicar conocimientos en contextos diversos",
                "Identificar y reforzar áreas de debilidad",
                "Desarrollar pensamiento crítico"
            ]
            
        elif milestone_type == "final_review":
            study_focus = "Repaso intensivo y perfeccionamiento para el examen final"
            study_activities = [
                "Exámenes de práctica completos",
                "Repaso intensivo de todos los temas",
                "Técnicas de memorización y retención",
                "Estrategias de manejo del tiempo en exámenes"
            ]
            learning_objectives = [
                "Perfeccionar conocimientos en todos los temas",
                "Ganar confianza y reducir ansiedad",
                "Optimizar estrategias de examen",
                "Lograr el máximo rendimiento académico"
            ]
        else:
            # Default content
            study_focus = "Revisar y consolidar conocimientos adquiridos"
            study_activities = [
                "Repaso de material estudiado",
                "Práctica adicional",
                "Autoevaluación"
            ]
            learning_objectives = [
                "Reforzar comprensión",
                "Mejorar retención",
                "Prepararse para siguientes temas"
            ]
        
        return study_focus, study_activities, learning_objectives


# In-memory storage for study plans (use database in production)
study_plans_storage: Dict[str, Dict[str, Any]] = {}


def save_study_plan(plan: StudyPlanResponse) -> None:
    """Save study plan to storage"""
    study_plans_storage[plan.plan_id] = plan.dict()


def get_study_plan(plan_id: str) -> Optional[StudyPlanResponse]:
    """Retrieve study plan from storage"""
    plan_data = study_plans_storage.get(plan_id)
    if plan_data:
        return StudyPlanResponse(**plan_data)
    return None


def list_study_plans() -> List[Dict[str, Any]]:
    """List all study plans"""
    return [
        {
            "plan_id": plan_id,
            "subject_name": plan_data["subject_name"],
            "exam_date": plan_data["exam_date"],
            "created_at": plan_data["created_at"],
            "status": plan_data["status"],
        }
        for plan_id, plan_data in study_plans_storage.items()
    ]
