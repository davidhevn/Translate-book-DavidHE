"""Translation service package."""
import logging
from app.config import TRANSLATOR_BACKEND
from app.services.translation.base import BaseTranslator
from app.services.translation.mock import MockTranslator
from app.services.translation.argos import ArgosTranslator

logger = logging.getLogger(__name__)

# Singleton translator instance
_translator_instance = None


def get_translator() -> BaseTranslator:
    """Get the configured translator instance.
    
    Uses TRANSLATOR_BACKEND env var to select provider.
    Falls back to MockTranslator if configured translator unavailable.
    """
    global _translator_instance
    
    if _translator_instance is not None:
        return _translator_instance
    
    backend = TRANSLATOR_BACKEND.lower()
    logger.info(f"Initializing translator backend: {backend}")
    
    if backend == "argos":
        translator = ArgosTranslator()
        if translator.is_available:
            _translator_instance = translator
            logger.info("Using Argos Translate")
        else:
            logger.warning("Argos Translate not available, falling back to MockTranslator")
            _translator_instance = MockTranslator()
    else:
        # Default to mock
        _translator_instance = MockTranslator()
        logger.info("Using MockTranslator")
    
    return _translator_instance


def reset_translator():
    """Reset the translator instance. Useful for testing."""
    global _translator_instance
    _translator_instance = None


__all__ = ["BaseTranslator", "MockTranslator", "ArgosTranslator", "get_translator", "reset_translator"]
