"""Argos Translate provider."""
import logging
from app.services.translation.base import BaseTranslator

logger = logging.getLogger(__name__)


class ArgosTranslator(BaseTranslator):
    """Translator using Argos Translate (offline, open source)."""
    
    def __init__(self):
        self._translator = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Argos Translate with English->Vietnamese model."""
        try:
            import argostranslate.translate
            
            # Get installed languages
            installed_languages = argostranslate.translate.get_installed_languages()
            
            # Find English and Vietnamese
            en_lang = next((l for l in installed_languages if l.code == "en"), None)
            vi_lang = next((l for l in installed_languages if l.code == "vi"), None)
            
            if en_lang and vi_lang:
                self._translator = en_lang.get_translation(vi_lang)
                if self._translator:
                    logger.info("Argos Translate EN->VI initialized successfully")
                else:
                    logger.warning("Argos Translate: EN->VI translation not available")
            else:
                logger.warning("Argos Translate: Required language packs not installed")
                logger.info("Install with: python -c \"import argostranslate.package; ...\"")
                
        except ImportError:
            logger.warning("Argos Translate not installed. Run: pip install argostranslate")
        except Exception as e:
            logger.error(f"Failed to initialize Argos Translate: {e}")
    
    def translate(self, text: str) -> str:
        """Translate text using Argos Translate."""
        if not text or not text.strip():
            return text
            
        if not self._translator:
            logger.warning("Argos translator not available, returning original text")
            return text
        
        try:
            return self._translator.translate(text)
        except Exception as e:
            logger.error(f"Argos translation failed: {e}")
            return text
    
    @property
    def name(self) -> str:
        return "ArgosTranslator"
    
    @property
    def is_available(self) -> bool:
        """Check if Argos translator is properly initialized."""
        return self._translator is not None
