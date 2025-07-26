import logging
import time
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.config import settings
from app.models.schemas import (
    ActivityType,
    Flashcard,
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    Summary,
)
from app.services.claude_service import ClaudeService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"


class UnifiedAIService:
    def _is_valid_api_key(self, api_key: str, provider: str) -> bool:
        """Check if API key is valid (not empty and not a placeholder)"""
        if not api_key:
            return False

        # Common placeholder patterns
        placeholders = [
            "your_openai_api_key_here",
            "your_anthropic_api_key_here",
            "sk-proj-your-key-here",
            "sk-ant-your-key-here",
            "your_api_key_here",
            "your_key_here",
            "replace_with_your_key",
        ]

        # Check if it's a placeholder
        if api_key.lower() in [p.lower() for p in placeholders]:
            return False

        # Basic format validation
        if provider == "anthropic":
            # Anthropic keys start with sk-ant-api03-
            return api_key.startswith("sk-ant-api03-") and len(api_key) > 20
        elif provider == "openai":
            # OpenAI keys start with sk- and are longer than 20 chars
            return api_key.startswith("sk-") and len(api_key) > 20

        return True

    def __init__(self):
        self.claude_service = None
        self.openai_service = None

        # Initialize available services
        try:
            if self._is_valid_api_key(settings.ANTHROPIC_API_KEY, "anthropic"):
                self.claude_service = ClaudeService()
                logger.info("Claude service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Claude service: {str(e)}")

        try:
            if self._is_valid_api_key(settings.OPENAI_API_KEY, "openai"):
                self.openai_service = AIService()
                logger.info("OpenAI service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI service: {str(e)}")

        # Determine service priority
        self.service_priority = self._determine_service_priority()

        if not self.service_priority:
            raise ValueError(
                "No AI services available. Please configure ANTHROPIC_API_KEY or OPENAI_API_KEY"
            )

    def _determine_service_priority(self) -> List[AIProvider]:
        """Determine the order of AI services to try based on configuration and availability"""
        priority = []

        # Primary service from config
        if settings.PRIMARY_AI_SERVICE == "claude" and self.claude_service:
            priority.append(AIProvider.CLAUDE)
        elif settings.PRIMARY_AI_SERVICE == "openai" and self.openai_service:
            priority.append(AIProvider.OPENAI)

        # Add fallbacks
        if AIProvider.CLAUDE not in priority and self.claude_service:
            priority.append(AIProvider.CLAUDE)
        if AIProvider.OPENAI not in priority and self.openai_service:
            priority.append(AIProvider.OPENAI)

        return priority

    async def generate_content_with_fallback(
        self,
        text: str,
        activity_type: ActivityType,
        count: int = 5,
        language: str = None,
    ) -> Dict[str, Any]:
        """Generate content using primary service with fallback to secondary services"""

        if language is None:
            language = settings.DEFAULT_LANGUAGE

        last_error = None

        for provider in self.service_priority:
            try:
                logger.info(f"Attempting content generation with {provider.value}")

                if provider == AIProvider.CLAUDE and self.claude_service:
                    result = await self.claude_service.generate_content(
                        text, activity_type, count, language
                    )
                    result["provider"] = "claude"
                    return result

                elif provider == AIProvider.OPENAI and self.openai_service:
                    # OpenAI service doesn't support language parameter in original implementation
                    result = await self.openai_service.generate_content(
                        text, activity_type, count
                    )
                    result["provider"] = "openai"
                    return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Failed to generate content with {provider.value}: {str(e)}"
                )
                continue

        # If all services failed, raise the last error
        raise Exception(f"All AI services failed. Last error: {str(last_error)}")

    async def generate_flashcards(
        self, text: str, count: int = 5, language: str = None
    ) -> List[Flashcard]:
        """Generate flashcards with fallback support"""

        if language is None:
            language = settings.DEFAULT_LANGUAGE

        for provider in self.service_priority:
            try:
                if provider == AIProvider.CLAUDE and self.claude_service:
                    return await self.claude_service.generate_flashcards(
                        text, count, language
                    )
                elif provider == AIProvider.OPENAI and self.openai_service:
                    return await self.openai_service.generate_flashcards(text, count)
            except Exception as e:
                logger.warning(
                    f"Failed to generate flashcards with {provider.value}: {str(e)}"
                )
                continue

        raise Exception("All AI services failed to generate flashcards")

    async def generate_multiple_choice(
        self, text: str, count: int = 5, language: str = None
    ) -> List[MultipleChoiceQuestion]:
        """Generate multiple choice questions with fallback support"""

        if language is None:
            language = settings.DEFAULT_LANGUAGE

        for provider in self.service_priority:
            try:
                if provider == AIProvider.CLAUDE and self.claude_service:
                    return await self.claude_service.generate_multiple_choice(
                        text, count, language
                    )
                elif provider == AIProvider.OPENAI and self.openai_service:
                    return await self.openai_service.generate_multiple_choice(
                        text, count
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to generate multiple choice with {provider.value}: {str(e)}"
                )
                continue

        raise Exception("All AI services failed to generate multiple choice questions")

    async def generate_true_false(
        self, text: str, count: int = 5, language: str = None
    ) -> List[TrueFalseQuestion]:
        """Generate true/false questions with fallback support"""

        if language is None:
            language = settings.DEFAULT_LANGUAGE

        for provider in self.service_priority:
            try:
                if provider == AIProvider.CLAUDE and self.claude_service:
                    return await self.claude_service.generate_true_false(
                        text, count, language
                    )
                elif provider == AIProvider.OPENAI and self.openai_service:
                    return await self.openai_service.generate_true_false(text, count)
            except Exception as e:
                logger.warning(
                    f"Failed to generate true/false with {provider.value}: {str(e)}"
                )
                continue

        raise Exception("All AI services failed to generate true/false questions")

    async def generate_summary(self, text: str, language: str = None) -> List[Summary]:
        """Generate summary with fallback support"""

        if language is None:
            language = settings.DEFAULT_LANGUAGE

        for provider in self.service_priority:
            try:
                if provider == AIProvider.CLAUDE and self.claude_service:
                    return await self.claude_service.generate_summary(text, language)
                elif provider == AIProvider.OPENAI and self.openai_service:
                    return await self.openai_service.generate_summary(text)
            except Exception as e:
                logger.warning(
                    f"Failed to generate summary with {provider.value}: {str(e)}"
                )
                continue

        raise Exception("All AI services failed to generate summary")

    async def generate_mixed_activities(self, text: str, language: str = None) -> Dict[str, Any]:
        """Generate mixed activities (flashcards, multiple choice, true/false) in a single API call"""
        
        if language is None:
            language = settings.DEFAULT_LANGUAGE

        for provider in self.service_priority:
            try:
                if provider == AIProvider.CLAUDE and self.claude_service:
                    return await self.claude_service.generate_mixed_activities(text, language)
                elif provider == AIProvider.OPENAI and self.openai_service:
                    return await self.openai_service.generate_mixed_activities(text)
            except Exception as e:
                logger.warning(
                    f"Failed to generate mixed activities with {provider.value}: {str(e)}"
                )
                continue

        raise Exception("All AI services failed to generate mixed activities")

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all AI services"""
        return {
            "claude_available": self.claude_service is not None,
            "openai_available": self.openai_service is not None,
            "primary_service": settings.PRIMARY_AI_SERVICE,
            "service_priority": [p.value for p in self.service_priority],
            "default_language": settings.DEFAULT_LANGUAGE,
        }
