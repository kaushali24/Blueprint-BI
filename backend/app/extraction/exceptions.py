class ExtractionValidationError(Exception):
    """Top-level response parse failure."""
    pass

class ExtractionEvidenceError(Exception):
    """Candidate evidence validation failure."""
    pass

class ExtractionProviderError(Exception):
    """LLM provider failure."""
    pass

class ExtractionConsistencyError(Exception):
    """Candidate business consistency failure."""
    pass
