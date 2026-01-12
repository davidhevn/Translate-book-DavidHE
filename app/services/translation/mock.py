"""Mock translator for testing."""
from app.services.translation.base import BaseTranslator


class MockTranslator(BaseTranslator):
    """Mock translator that adds Vietnamese-looking prefix.
    
    Used for testing without requiring actual translation engine.
    """
    
    def translate(self, text: str) -> str:
        """Mock translate by adding prefix."""
        if not text or not text.strip():
            return text
        # Add a Vietnamese-like prefix to indicate translation happened
        return f"[VI] {text}"
    
    @property
    def name(self) -> str:
        return "MockTranslator"
