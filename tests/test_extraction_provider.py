import pytest
from app.extraction.provider import FakeLLMProvider
from app.extraction.exceptions import ExtractionProviderError

def test_fake_provider_success():
    provider = FakeLLMProvider(response_dict={"test": "ok"})
    result = provider.extract("hello", {"type": "object"})
    
    assert result == {"test": "ok"}
    assert len(provider.calls) == 1
    assert provider.calls[0]["prompt"] == "hello"

def test_fake_provider_error():
    provider = FakeLLMProvider(should_raise=True)
    with pytest.raises(ExtractionProviderError, match="Fake LLM Provider Error"):
        provider.extract("hello", {"type": "object"})
    
    assert len(provider.calls) == 1
