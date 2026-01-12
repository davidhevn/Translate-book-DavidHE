"""Tests for translation service."""
from app.services.translation import MockTranslator, get_translator, reset_translator


def test_mock_translator_adds_prefix():
    """Test that MockTranslator adds [VI] prefix."""
    translator = MockTranslator()
    
    result = translator.translate("Hello world")
    
    assert result == "[VI] Hello world"
    assert translator.name == "MockTranslator"


def test_mock_translator_handles_empty():
    """Test MockTranslator handles empty strings."""
    translator = MockTranslator()
    
    assert translator.translate("") == ""
    assert translator.translate("   ") == "   "


def test_get_translator_returns_mock_by_default():
    """Test that default translator is MockTranslator."""
    reset_translator()
    translator = get_translator()
    
    assert translator.name == "MockTranslator"


def test_translator_singleton():
    """Test that get_translator returns same instance."""
    reset_translator()
    t1 = get_translator()
    t2 = get_translator()
    
    assert t1 is t2
