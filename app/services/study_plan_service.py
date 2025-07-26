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
    StudyPlanResponse
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
        language: str = "es"
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
            ai_plan, subject_name, exam_date, days_remaining, plan_id, language
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
        days_remaining: int
    ) -> Dict[str, Any]:
        """Generate study plan using AI service with optimized prompt"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Enhanced prompt for better study plan generation
        prompt = f"""A partir del siguiente contenido extraído del apunte, generá un plan de estudio personalizado para un estudiante que rinde el examen de {subject_name} el día {exam_date}.

Hoy es {today}. Quedan {days_remaining} días para el examen. El objetivo es ayudarlo a estudiar de forma organizada, progresiva y eficaz, utilizando técnicas activas como flashcards y trivias.

CONTENIDO DEL APUNTE:
{document_text[:8000]}  # Limit content to avoid token limits

INSTRUCCIONES:
1. Detectá y listá los temas principales del contenido ordenados por importancia
2. Identificá los 3-5 temas más difíciles que necesitan atención extra
3. Distribuí los temas entre los días disponibles hasta el examen
4. Para cada día, recomendá técnicas específicas (leer, resumir, flashcards, trivias, repaso)
5. Estimá horas de estudio por día y por tema
6. Generá recomendaciones generales y técnicas de estudio

FORMATO DE RESPUESTA (JSON estricto):
{{
    "temas_principales": [
        {{
            "nombre": "string",
            "importancia": 1-5,
            "dificultad": "easy|medium|hard",
            "descripcion": "string"
        }}
    ],
    "temas_dificiles": [
        {{
            "nombre": "string",
            "importancia": 1-5,
            "dificultad": "hard",
            "descripcion": "string"
        }}
    ],
    "plan_por_dia": [
        {{
            "dia": 1,
            "fecha": "YYYY-MM-DD",
            "temas": ["tema1", "tema2"],
            "acciones": ["acción1", "acción2"],
            "horas_estimadas": 2.5
        }}
    ],
    "recomendaciones_generales": [
        "recomendación1",
        "recomendación2"
    ],
    "tecnicas_estudio": [
        "técnica1",
        "técnica2"
    ],
    "estadisticas": {{
        "total_temas": 10,
        "horas_totales": 25.0,
        "horas_promedio_dia": 2.5
    }},
    "estado": "normal|urgente"
}}

IMPORTANTE: Responde SOLO con el JSON válido, sin texto adicional."""

        # Use AI service to generate the plan
        try:
            # Since we need a custom prompt, we'll use the lower-level AI service
            if hasattr(self.ai_service, 'claude_service') and self.ai_service.claude_service:
                response = await self._call_claude_for_study_plan(prompt, language)
            elif hasattr(self.ai_service, 'openai_service') and self.ai_service.openai_service:
                response = await self._call_openai_for_study_plan(prompt, language)
            else:
                raise Exception("No AI service available")
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI study plan: {str(e)}")
            # Fallback to basic plan structure
            return self._generate_fallback_plan(document_text, subject_name, days_remaining)
    
    async def _call_claude_for_study_plan(self, prompt: str, language: str) -> Dict[str, Any]:
        """Call Claude service for study plan generation"""
        try:
            claude_service = self.ai_service.claude_service
            
            # Use the same pattern as other Claude service methods
            response = await claude_service.client.messages.create(
                model=claude_service.model,
                max_tokens=claude_service.max_tokens,
                temperature=claude_service.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise Exception("No valid JSON found in response")
                    
        except Exception as e:
            logger.error(f"Claude study plan generation failed: {str(e)}")
            raise
    
    async def _call_openai_for_study_plan(self, prompt: str, language: str = "es") -> Dict[str, Any]:
        """Call OpenAI service for study plan generation"""
        try:
            openai_service = self.ai_service.openai_service
            
            # Use the same pattern as other OpenAI service methods
            response = await openai_service.client.chat.completions.create(
                model="gpt-4o-mini",  # Use the configured model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise Exception("No valid JSON found in response")
                    
        except Exception as e:
            logger.error(f"OpenAI study plan generation failed: {str(e)}")
            raise
    
    def _generate_fallback_plan(self, document_text: str, subject_name: str, days_remaining: int) -> Dict[str, Any]:
        """Generate a basic fallback study plan when AI fails"""
        
        # Simple topic extraction (split by paragraphs/sections)
        topics = []
        text_sections = document_text.split('\n\n')
        for i, section in enumerate(text_sections[:10]):  # Limit to 10 topics
            if len(section.strip()) > 50:  # Only meaningful sections
                topics.append({
                    "nombre": f"Tema {i+1}",
                    "importancia": 3,
                    "dificultad": "medium",
                    "descripcion": section[:100] + "..." if len(section) > 100 else section
                })
        
        # Create basic daily plan
        daily_plan = []
        topics_per_day = max(1, len(topics) // max(1, days_remaining))
        
        for day in range(min(days_remaining, 14)):  # Max 14 days
            date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
            start_topic = day * topics_per_day
            end_topic = min(start_topic + topics_per_day, len(topics))
            
            day_topics = [t["nombre"] for t in topics[start_topic:end_topic]]
            
            daily_plan.append({
                "dia": day + 1,
                "fecha": date,
                "temas": day_topics,
                "acciones": ["Leer material", "Tomar notas", "Hacer flashcards"],
                "horas_estimadas": 2.0
            })
        
        return {
            "temas_principales": topics,
            "temas_dificiles": topics[:3],  # First 3 as difficult
            "plan_por_dia": daily_plan,
            "recomendaciones_generales": [
                "Establece un horario fijo de estudio",
                "Toma descansos regulares",
                "Repasa diariamente"
            ],
            "tecnicas_estudio": [
                "Lectura activa",
                "Flashcards",
                "Resúmenes"
            ],
            "estadisticas": {
                "total_temas": len(topics),
                "horas_totales": len(daily_plan) * 2.0,
                "horas_promedio_dia": 2.0
            },
            "estado": "urgente" if days_remaining <= 7 else "normal"
        }
    
    def _structure_study_plan(
        self,
        ai_plan: Dict[str, Any],
        subject_name: str,
        exam_date: str,
        days_remaining: int,
        plan_id: str,
        language: str
    ) -> Dict[str, Any]:
        """Structure the AI-generated plan into the required response format"""
        
        # Convert AI plan to structured objects
        main_topics = [
            StudyTopic(**topic) for topic in ai_plan.get("temas_principales", [])
        ]
        
        hardest_topics = [
            StudyTopic(**topic) for topic in ai_plan.get("temas_dificiles", [])
        ]
        
        daily_plan = [
            DailyStudyPlan(**day) for day in ai_plan.get("plan_por_dia", [])
        ]
        
        # Generate timeline data
        timeline = self._generate_timeline_data(daily_plan, days_remaining)
        
        # Generate statistics
        stats = ai_plan.get("estadisticas", {})
        statistics = StudyStatistics(
            total_topics=stats.get("total_temas", len(main_topics)),
            estimated_total_hours=stats.get("horas_totales", sum(d.estimated_hours for d in daily_plan)),
            daily_average_hours=stats.get("horas_promedio_dia", 2.0),
            hardest_topics_count=len(hardest_topics)
        )
        
        return {
            "plan_id": plan_id,
            "subject_name": subject_name,
            "exam_date": exam_date,
            "created_at": datetime.now().isoformat(),
            "status": ai_plan.get("estado", "normal"),
            "main_topics": main_topics,
            "hardest_topics": hardest_topics,
            "daily_plan": daily_plan,
            "timeline": timeline,
            "statistics": statistics,
            "general_recommendations": ai_plan.get("recomendaciones_generales", []),
            "study_techniques": ai_plan.get("tecnicas_estudio", []),
            "language": language,
            "provider": getattr(self.ai_service, 'last_used_provider', 'unknown')
        }
    
    def _generate_timeline_data(self, daily_plan: List[DailyStudyPlan], days_remaining: int) -> TimelineData:
        """Generate timeline data for charts and visualization"""
        
        # Calculate weekly breakdown
        weekly_breakdown = []
        current_week = []
        week_hours = 0
        
        for day in daily_plan:
            current_week.append({
                "day": day.day,
                "date": day.date,
                "hours": day.estimated_hours,
                "topics_count": len(day.topics)
            })
            week_hours += day.estimated_hours
            
            # If we have 7 days or it's the last day, complete the week
            if len(current_week) == 7 or day == daily_plan[-1]:
                weekly_breakdown.append({
                    "week": len(weekly_breakdown) + 1,
                    "days": current_week,
                    "total_hours": week_hours,
                    "topics_count": sum(d["topics_count"] for d in current_week)
                })
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
        
        return TimelineData(
            total_days=len(daily_plan),
            days_remaining=days_remaining,
            study_intensity=intensity,
            weekly_breakdown=weekly_breakdown
        )


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
            "status": plan_data["status"]
        }
        for plan_id, plan_data in study_plans_storage.items()
    ]