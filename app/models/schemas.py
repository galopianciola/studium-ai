from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ActivityType(str, Enum):
    FLASHCARD = "flashcard"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SUMMARY = "summary"
    MIXED = "mixed"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Request Models
class GenerateContentRequest(BaseModel):
    text: str = Field(..., description="Extracted text content to generate activities from")
    activity_type: ActivityType = Field(..., description="Type of activity to generate")
    count: int = Field(default=5, ge=1, le=10, description="Number of activities to generate")
    language: str = Field(default="es", description="Language for content generation (es=Spanish, en=English)")

class GenerateMixedRequest(BaseModel):
    text: str = Field(..., description="Extracted text content to generate activities from")
    language: str = Field(default="es", description="Language for content generation (es=Spanish, en=English)")

class ProcessDocumentRequest(BaseModel):
    document_id: str = Field(..., description="ID of uploaded document")

# Response Models
class UploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique identifier for uploaded document")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type/extension")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)

class ProcessingResponse(BaseModel):
    document_id: str
    status: ProcessingStatus
    progress: float = Field(ge=0, le=100, description="Processing progress percentage")
    message: Optional[str] = None
    extracted_text: Optional[str] = None
    word_count: Optional[int] = None

class Flashcard(BaseModel):
    question: str = Field(..., description="Question for the flashcard")
    answer: str = Field(..., description="Answer for the flashcard")
    difficulty: Optional[str] = Field(default="medium", description="Difficulty level")

class MultipleChoiceQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_items=2, max_items=4, description="Answer options")
    correct_answer: int = Field(..., ge=0, le=3, description="Index of correct answer")
    explanation: Optional[str] = Field(default=None, description="Explanation of the answer")

class TrueFalseQuestion(BaseModel):
    statement: str = Field(..., description="True/false statement")
    correct_answer: bool = Field(..., description="Whether the statement is true")
    explanation: Optional[str] = Field(default=None, description="Explanation of the answer")

class Summary(BaseModel):
    title: str = Field(..., description="Summary title")
    content: str = Field(..., description="Summary content")
    key_points: List[str] = Field(..., description="Key points from the content")

class ActivityResponse(BaseModel):
    activity_type: ActivityType
    count: int
    activities: List[Dict[str, Any]] = Field(..., description="Generated activities")
    processing_time: float = Field(..., description="Time taken to generate activities")
    provider: Optional[str] = Field(default=None, description="AI provider used (claude, openai)")
    language: str = Field(default="es", description="Language of generated content")

class FlashcardsResponse(ActivityResponse):
    activities: List[Flashcard]

class MultipleChoiceResponse(ActivityResponse):
    activities: List[MultipleChoiceQuestion]

class TrueFalseResponse(ActivityResponse):
    activities: List[TrueFalseQuestion]

class SummaryResponse(ActivityResponse):
    activities: List[Summary]

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    error_code: Optional[str] = Field(default=None, description="Error code for client handling")

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "1.0.0"
    timestamp: str

# Study Plan Models
class StudyPlanRequest(BaseModel):
    file_id: str = Field(..., description="ID of uploaded document")
    subject_name: str = Field(..., description="Name of the subject/course")
    exam_date: str = Field(..., description="Exam date in YYYY-MM-DD format")
    language: str = Field(default="es", description="Language for study plan generation")

class DailyStudyPlan(BaseModel):
    day: int = Field(..., description="Day number from today")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    topics: List[str] = Field(..., description="Topics to study on this day")
    actions: List[str] = Field(..., description="Suggested study actions")
    estimated_hours: float = Field(..., description="Estimated study hours for this day")

class StudyTopic(BaseModel):
    name: str = Field(..., description="Topic name")
    importance: int = Field(..., ge=1, le=5, description="Importance level (1-5)")
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    description: str = Field(..., description="Brief description of the topic")
    estimated_hours: Optional[float] = Field(default=None, description="Estimated study hours for this topic")
    subtopics: Optional[List[str]] = Field(default=None, description="List of subtopics")

class TimelineData(BaseModel):
    total_days: int = Field(..., description="Total days until exam")
    days_remaining: int = Field(..., description="Days remaining until exam")
    study_intensity: str = Field(..., description="Study intensity level")
    weekly_breakdown: List[Dict[str, Any]] = Field(..., description="Weekly study breakdown")

class StudyStatistics(BaseModel):
    total_topics: int = Field(..., description="Total number of topics identified")
    estimated_total_hours: float = Field(..., description="Total estimated study hours")
    daily_average_hours: float = Field(..., description="Average daily study hours")
    hardest_topics_count: int = Field(..., description="Number of hardest topics")

class StudyPlanResponse(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the study plan")
    subject_name: str = Field(..., description="Subject name")
    exam_date: str = Field(..., description="Exam date")
    created_at: str = Field(..., description="Plan creation timestamp")
    status: str = Field(..., description="Plan status (normal, urgent)")
    
    # Main study plan data
    main_topics: List[StudyTopic] = Field(..., description="Main topics identified from document")
    hardest_topics: List[StudyTopic] = Field(..., description="Hardest topics requiring extra attention")
    daily_plan: List[DailyStudyPlan] = Field(..., description="Day-by-day study plan")
    
    # Timeline and statistics
    timeline: TimelineData = Field(..., description="Timeline data for charts")
    statistics: StudyStatistics = Field(..., description="Study statistics")
    
    # Recommendations
    general_recommendations: List[str] = Field(..., description="General study recommendations")
    study_techniques: List[str] = Field(..., description="Recommended study techniques")
    
    # Document content for activity generation
    document_text: str = Field(..., description="Original document text for generating activities")
    
    # Metadata
    language: str = Field(default="es", description="Language of the plan")
    provider: Optional[str] = Field(default=None, description="AI provider used")
    processing_time: float = Field(..., description="Time taken to generate the plan")