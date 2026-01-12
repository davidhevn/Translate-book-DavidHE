"""Base translator interface."""
from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    """Abstract base class for translation providers."""
    
    @abstractmethod
    def translate(self, text: str) -> str:
        """Translate text from English to Vietnamese.
        
        Args:
            text: English text to translate.
            
        Returns:
            Vietnamese translation.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this translator."""
        pass
