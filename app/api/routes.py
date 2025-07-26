from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime
from typing import Dict, Any

from app.models.schemas import (
    UploadResponse,
    ProcessingResponse,
    GenerateContentRequest,
    GenerateMixedRequest,
    ActivityResponse,
    ErrorResponse,
    ActivityType,
    ProcessingStatus,
    HealthResponse,
    StudyPlanRequest,
    StudyPlanResponse
)
from app.services.document_processor import DocumentProcessor
from app.services.unified_ai_service import UnifiedAIService
from app.services.study_plan_service import StudyPlanService, save_study_plan, get_study_plan, list_study_plans

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
document_processor = DocumentProcessor()
ai_service = UnifiedAIService()
study_plan_service = StudyPlanService(ai_service)

# In-memory storage for processing status (use Redis in production)
processing_status: Dict[str, Dict[str, Any]] = {}

@router.post("/upload", response_model=UploadResponse, tags=["Document Processing"])
async def upload_document(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Save uploaded file
        document_id, file_path = await document_processor.save_uploaded_file(file, file.filename)
        
        # Initialize processing status
        processing_status[document_id] = {
            "document_id": document_id,
            "status": ProcessingStatus.PENDING,
            "progress": 0.0,
            "message": "Ready for processing",
            "extracted_text": None,
            "word_count": 0,
            "upload_time": datetime.now().isoformat()
        }
        
        logger.info(f"File uploaded successfully: {file.filename} -> {document_id}")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file.size,
            file_type=file.content_type or "unknown",
            status=ProcessingStatus.PENDING
        )
    
    except ValueError as e:
        logger.error(f"Upload validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.post("/process/{document_id}", response_model=ProcessingResponse, tags=["Document Processing"])
async def process_document(document_id: str, background_tasks: BackgroundTasks):
    try:
        if document_id not in processing_status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if already processing or completed
        current_status = processing_status[document_id]["status"]
        if current_status == ProcessingStatus.PROCESSING:
            return ProcessingResponse(**processing_status[document_id])
        elif current_status == ProcessingStatus.COMPLETED:
            return ProcessingResponse(**processing_status[document_id])
        
        # Start processing in background
        background_tasks.add_task(background_process_document, document_id)
        
        # Update status to processing
        processing_status[document_id].update({
            "status": ProcessingStatus.PROCESSING,
            "progress": 10.0,
            "message": "Starting document processing..."
        })
        
        return ProcessingResponse(**processing_status[document_id])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate processing")

async def background_process_document(document_id: str):
    try:
        file_path = document_processor.get_file_path(document_id)
        if not file_path:
            processing_status[document_id].update({
                "status": ProcessingStatus.FAILED,
                "progress": 0.0,
                "message": "File not found"
            })
            return
        
        # Update progress
        processing_status[document_id].update({
            "progress": 50.0,
            "message": "Extracting text from document..."
        })
        
        # Process document
        result = document_processor.process_document(document_id, file_path)
        
        # Update processing status
        processing_status[document_id].update(result)
        
    except Exception as e:
        logger.error(f"Background processing error for {document_id}: {str(e)}")
        processing_status[document_id].update({
            "status": ProcessingStatus.FAILED,
            "progress": 0.0,
            "message": f"Processing failed: {str(e)}"
        })

@router.get("/process/{document_id}/status", response_model=ProcessingResponse, tags=["Document Processing"])
async def get_processing_status(document_id: str):
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return ProcessingResponse(**processing_status[document_id])

@router.post("/generate/flashcards", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_flashcards(request: GenerateContentRequest):
    try:
        start_time = time.time()
        
        flashcards = await ai_service.generate_flashcards(
            request.text, 
            request.count, 
            request.language
        )
        
        processing_time = time.time() - start_time
        
        return ActivityResponse(
            activity_type=ActivityType.FLASHCARD,
            count=len(flashcards),
            activities=[flashcard.dict() for flashcard in flashcards],
            processing_time=processing_time,
            language=request.language
        )
    
    except Exception as e:
        logger.error(f"Flashcard generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")

@router.post("/generate/multiple-choice", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_multiple_choice(request: GenerateContentRequest):
    try:
        start_time = time.time()
        
        questions = await ai_service.generate_multiple_choice(
            request.text, 
            request.count, 
            request.language
        )
        
        processing_time = time.time() - start_time
        
        return ActivityResponse(
            activity_type=ActivityType.MULTIPLE_CHOICE,
            count=len(questions),
            activities=[question.dict() for question in questions],
            processing_time=processing_time,
            language=request.language
        )
    
    except Exception as e:
        logger.error(f"Multiple choice generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate multiple choice questions: {str(e)}")

@router.post("/generate/true-false", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_true_false(request: GenerateContentRequest):
    try:
        start_time = time.time()
        
        questions = await ai_service.generate_true_false(
            request.text, 
            request.count, 
            request.language
        )
        
        processing_time = time.time() - start_time
        
        return ActivityResponse(
            activity_type=ActivityType.TRUE_FALSE,
            count=len(questions),
            activities=[question.dict() for question in questions],
            processing_time=processing_time,
            language=request.language
        )
    
    except Exception as e:
        logger.error(f"True/false generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate true/false questions: {str(e)}")

@router.post("/generate/summary", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_summary(request: GenerateContentRequest):
    try:
        start_time = time.time()
        
        summaries = await ai_service.generate_summary(
            request.text, 
            request.language
        )
        
        processing_time = time.time() - start_time
        
        return ActivityResponse(
            activity_type=ActivityType.SUMMARY,
            count=len(summaries),
            activities=[summary.dict() for summary in summaries],
            processing_time=processing_time,
            language=request.language
        )
    
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.post("/generate", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_content(request: GenerateContentRequest):
    try:
        start_time = time.time()
        
        result = await ai_service.generate_content_with_fallback(
            request.text, 
            request.activity_type, 
            request.count,
            request.language
        )
        
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        result["language"] = request.language
        
        return ActivityResponse(**result)
    
    except Exception as e:
        logger.error(f"Content generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@router.post("/generate/mixed", response_model=ActivityResponse, tags=["AI Content Generation"])
async def generate_mixed_activities(request: GenerateMixedRequest):
    """Generate mixed activities (flashcards, multiple choice, true/false) in a single API call to avoid rate limiting"""
    try:
        start_time = time.time()
        
        result = await ai_service.generate_mixed_activities(
            request.text,
            language=request.language
        )
        
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        result["language"] = request.language
        
        return ActivityResponse(**result)
    
    except Exception as e:
        logger.error(f"Mixed activities generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate mixed activities: {str(e)}")

@router.get("/documents/{document_id}/text", tags=["Document Processing"])
async def get_document_text(document_id: str):
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status_info = processing_status[document_id]
    if status_info["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    return {
        "document_id": document_id,
        "extracted_text": status_info["extracted_text"],
        "word_count": status_info["word_count"]
    }

@router.delete("/documents/{document_id}", tags=["Document Processing"])
async def delete_document(document_id: str):
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Clean up file
    success = document_processor.cleanup_document(document_id)
    
    # Remove from processing status
    del processing_status[document_id]
    
    return {
        "message": f"Document {document_id} deleted successfully",
        "file_cleanup": success
    }

@router.get("/health", response_model=HealthResponse, tags=["System Status"])
async def health_check():
    return HealthResponse(
        status="healthy",
        service="studium-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@router.get("/documents", tags=["Document Processing"])
async def list_documents():
    """List all uploaded documents and their processing status"""
    return {
        "documents": processing_status,
        "total_count": len(processing_status)
    }

@router.get("/ai-status", tags=["System Status"])
async def get_ai_status():
    """Get status of all AI services and configuration"""
    try:
        status = ai_service.get_service_status()
        return {
            "status": "healthy",
            "ai_services": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Study Plan Endpoints

@router.post("/student/learn/plan/generate", response_model=StudyPlanResponse, tags=["Study Plan"])
async def generate_study_plan(request: StudyPlanRequest):
    """Generate a comprehensive study plan based on document content and exam date"""
    try:
        start_time = time.time()
        
        # Validate that the document exists and is processed
        if request.file_id not in processing_status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_status = processing_status[request.file_id]
        if doc_status["status"] != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Document processing not completed. Current status: {doc_status['status']}"
            )
        
        # Get document text
        document_text = doc_status["extracted_text"]
        if not document_text:
            raise HTTPException(status_code=400, detail="No text extracted from document")
        
        # Generate study plan
        study_plan = await study_plan_service.generate_study_plan(
            document_text=document_text,
            subject_name=request.subject_name,
            exam_date=request.exam_date,
            language=request.language
        )
        
        # Save study plan for later retrieval
        save_study_plan(study_plan)
        
        processing_time = time.time() - start_time
        logger.info(f"Generated study plan {study_plan.plan_id} in {processing_time:.2f}s")
        
        return study_plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Study plan generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate study plan: {str(e)}")

@router.get("/student/learn/plan/{plan_id}", response_model=StudyPlanResponse, tags=["Study Plan"])
async def get_study_plan_by_id(plan_id: str):
    """Retrieve a study plan by its ID"""
    try:
        study_plan = get_study_plan(plan_id)
        if not study_plan:
            raise HTTPException(status_code=404, detail="Study plan not found")
        
        return study_plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study plan {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve study plan")

@router.get("/student/learn/plans", tags=["Study Plan"])
async def list_all_study_plans():
    """List all created study plans"""
    try:
        plans = list_study_plans()
        return {
            "study_plans": plans,
            "total_count": len(plans)
        }
    
    except Exception as e:
        logger.error(f"Error listing study plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list study plans")

@router.delete("/student/learn/plan/{plan_id}", tags=["Study Plan"])
async def delete_study_plan(plan_id: str):
    """Delete a study plan by its ID"""
    try:
        from app.services.study_plan_service import study_plans_storage
        
        if plan_id not in study_plans_storage:
            raise HTTPException(status_code=404, detail="Study plan not found")
        
        del study_plans_storage[plan_id]
        
        return {
            "message": f"Study plan {plan_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting study plan {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete study plan")