# SecretStuff

A production-ready Python library for identifying, redacting, and reversing personally identifiable information (PII) in text using advanced NLP models.

## Key Features
- **PII Identification**: Detect 150+ types of PII using GLiNER models
- **Flexible Redaction**: Replace PII with configurable dummy values
- **Reverse Mapping**: Restore original PII from redacted text
- **Production Ready**: Type hints, comprehensive tests, robust error handling

## Quick Example
```python
from secretstuff import SecretStuffPipeline

pipeline = SecretStuffPipeline()
redacted_text, entities, mapping = pipeline.identify_and_redact(
    "John Doe's email is john@example.com and phone is +1-555-123-4567"
)
```

## Documentation
For complete documentation, examples, and API reference, visit:
https://github.com/adw777/secretStuff/blob/main/README.md