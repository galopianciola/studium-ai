import logging
import os
import uuid
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import pytesseract

from app.core.config import settings
from app.models.schemas import ProcessingStatus

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Configure Tesseract if custom path provided
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    async def save_uploaded_file(self, file, filename: str) -> Tuple[str, str]:
        file_extension = Path(filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {file_extension} not supported")
        
        document_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{document_id}{file_extension}"
        
        # Save file
        content = await file.read()
        
        # Check file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved: {filename} -> {file_path}")
        return document_id, str(file_path)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            logger.info(f"Extracted text from PDF: {len(text)} characters")
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_image(self, file_path: str) -> str:
        try:
            # Open and process image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            logger.info(f"Extracted text from image: {len(text)} characters")
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
    
    def process_document(self, document_id: str, file_path: str) -> dict:
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                extracted_text = self.extract_text_from_pdf(file_path)
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                extracted_text = self.extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Clean and preprocess text
            cleaned_text = self.clean_text(extracted_text)
            
            # Count words
            word_count = len(cleaned_text.split())
            
            if word_count == 0:
                raise ValueError("No text could be extracted from the document")
            
            logger.info(f"Document processed successfully: {word_count} words extracted")
            
            return {
                "document_id": document_id,
                "status": ProcessingStatus.COMPLETED,
                "progress": 100.0,
                "message": "Document processed successfully",
                "extracted_text": cleaned_text,
                "word_count": word_count
            }
        
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            return {
                "document_id": document_id,
                "status": ProcessingStatus.FAILED,
                "progress": 0.0,
                "message": f"Processing failed: {str(e)}",
                "extracted_text": None,
                "word_count": 0
            }
    
    def clean_text(self, text: str) -> str:
        # Remove excessive whitespace
        import re
        
        # Replace multiple whitespaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Strip and return
        return text.strip()
    
    def get_file_path(self, document_id: str) -> Optional[str]:
        for ext in settings.ALLOWED_EXTENSIONS:
            file_path = self.upload_dir / f"{document_id}{ext}"
            if file_path.exists():
                return str(file_path)
        return None
    
    def cleanup_document(self, document_id: str) -> bool:
        file_path = self.get_file_path(document_id)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up document: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error cleaning up document {file_path}: {str(e)}")
        return False