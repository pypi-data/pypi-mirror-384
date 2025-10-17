"""Tests for SecretStuffPipeline class."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from secretstuff.api.pipeline import SecretStuffPipeline
from secretstuff.config.labels import DEFAULT_LABELS
from secretstuff.config.dummy_values import DEFAULT_DUMMY_VALUES


class TestSecretStuffPipeline:
    """Test cases for SecretStuffPipeline functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('secretstuff.core.identifier.GLiNER'):
            self.pipeline = SecretStuffPipeline()
        
        self.sample_text = """
        Mr. John Doe lives at 123 Main Street, New York.
        His phone number is +1-555-123-4567 and email is john.doe@email.com.
        """
        self.sample_entities = {
            "person": ["John Doe"],
            "email": ["john.doe@email.com"],
            "phone number": ["+1-555-123-4567"]
        }
        self.sample_replacement_mapping = {
            "John Doe": "PERSON_1",
            "john.doe@email.com": "EMAIL_REDACTED",
            "+1-555-123-4567": "PHONE_REDACTED"
        }
    
    def test_initialization(self):
        """Test SecretStuffPipeline initialization with new defaults."""
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            pipeline = SecretStuffPipeline()
            
            # Check new default model name
            mock_gliner.from_pretrained.assert_called_with(
                "aksman18/gliner-multi-pii-domains-v2", 
                token=None
            )
            assert pipeline.identifier.labels == DEFAULT_LABELS
            assert pipeline.redactor.dummy_values == DEFAULT_DUMMY_VALUES
    
    def test_initialization_with_token(self):
        """Test SecretStuffPipeline initialization with token."""
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            token = "test-token"
            pipeline = SecretStuffPipeline(token=token)
            
            mock_gliner.from_pretrained.assert_called_with(
                "aksman18/gliner-multi-pii-domains-v2", 
                token=token
            )
    
    def test_custom_initialization(self):
        """Test SecretStuffPipeline with custom parameters."""
        custom_labels = ["person", "email"]
        custom_dummy_values = {"person": "REDACTED_PERSON"}
        custom_model = "custom-model"
        token = "test-token"
        
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            pipeline = SecretStuffPipeline(
                model_name=custom_model,
                labels=custom_labels,
                dummy_values=custom_dummy_values,
                token=token
            )
            
            mock_gliner.from_pretrained.assert_called_with(custom_model, token=token)
            assert pipeline.identifier.labels == custom_labels
            assert pipeline.redactor.dummy_values == custom_dummy_values
    
    @patch('secretstuff.core.identifier.PIIIdentifier.identify_and_save')
    def test_identify_pii_with_overlap(self, mock_identify):
        """Test PII identification with chunk overlap."""
        mock_identify.return_value = self.sample_entities
        
        result = self.pipeline.identify_pii(self.sample_text, chunk_size=384, chunk_overlap=50)
        
        assert result == self.sample_entities
        assert self.pipeline._last_identified_entities == self.sample_entities
        mock_identify.assert_called_once_with(self.sample_text, "identified_entities.json", 384, 50)
    
    def test_redact_pii_with_entities(self):
        """Test PII redaction with provided entities."""
        with patch.object(self.pipeline.redactor, 'redact_from_identified_entities') as mock_redact:
            mock_redact.return_value = "redacted text"
            
            result = self.pipeline.redact_pii(self.sample_text, self.sample_entities)
            
            assert result == "redacted text"
            mock_redact.assert_called_once_with(self.sample_text, self.sample_entities)
    
    def test_redact_pii_with_last_entities(self):
        """Test PII redaction using last identified entities."""
        self.pipeline._last_identified_entities = self.sample_entities
        
        with patch.object(self.pipeline.redactor, 'redact_from_identified_entities') as mock_redact:
            mock_redact.return_value = "redacted text"
            
            result = self.pipeline.redact_pii(self.sample_text)
            
            assert result == "redacted text"
            mock_redact.assert_called_once_with(self.sample_text, self.sample_entities)
    
    def test_redact_pii_without_entities_raises_error(self):
        """Test that redacting without entities raises error."""
        with pytest.raises(ValueError, match="No identified entities available"):
            self.pipeline.redact_pii(self.sample_text)
    
    @patch('secretstuff.api.pipeline.SecretStuffPipeline.identify_pii')
    @patch('secretstuff.api.pipeline.SecretStuffPipeline.redact_pii')
    def test_identify_and_redact_with_overlap(self, mock_redact, mock_identify):
        """Test combined identify and redact operation with overlap."""
        mock_identify.return_value = self.sample_entities
        mock_redact.return_value = "redacted text"
        self.pipeline._last_replacement_mapping = self.sample_replacement_mapping
        
        redacted_text, entities, mapping = self.pipeline.identify_and_redact(
            self.sample_text, chunk_size=384, chunk_overlap=50
        )
        
        assert redacted_text == "redacted text"
        assert entities == self.sample_entities
        assert mapping == self.sample_replacement_mapping
        mock_identify.assert_called_once_with(self.sample_text, 384, 50)
        mock_redact.assert_called_once_with(self.sample_text, self.sample_entities)
    
    def test_process_text_file_with_overlap(self):
        """Test processing a complete text file with overlap."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "input.txt")
            
            # Create input file
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(self.sample_text)
            
            # Mock the components
            with patch.object(self.pipeline.identifier, 'identify_and_save') as mock_identify, \
                 patch.object(self.pipeline.redactor, 'redact_from_file') as mock_redact:
                
                mock_identify.return_value = self.sample_entities
                mock_redact.return_value = "redacted text"
                self.pipeline.redactor.replacement_mapping = self.sample_replacement_mapping
                
                result = self.pipeline.process_text_file(
                    input_file, chunk_size=384, chunk_overlap=50
                )
                
                assert result["input_file"] == input_file
                assert result["entities_count"] == len(self.sample_replacement_mapping)
                assert result["labels_found"] == list(self.sample_entities.keys())
                
                # Verify overlap parameter was passed
                mock_identify.assert_called_once()
                args = mock_identify.call_args[0]
                kwargs = mock_identify.call_args[1] if mock_identify.call_args[1] else {}
                
                # Check that chunk_overlap was passed (either as positional or keyword arg)
                if len(args) >= 4:
                    assert args[3] == 50  # chunk_overlap as positional arg
                else:
                    assert kwargs.get('chunk_overlap') == 50  # chunk_overlap as keyword arg
    
    # ... (keep all other existing tests from the original test_pipeline.py)
    
    def test_reverse_redaction_with_mapping(self):
        """Test reverse redaction with provided mapping."""
        redacted_text = "PERSON_1's email is EMAIL_REDACTED"
        
        with patch.object(self.pipeline.reverse_mapper, 'reverse_redaction') as mock_reverse:
            mock_reverse.return_value = ("restored text", 2, {"PERSON_1": 1, "EMAIL_REDACTED": 1})
            
            result = self.pipeline.reverse_redaction(redacted_text, self.sample_replacement_mapping)
            
            assert result == ("restored text", 2, {"PERSON_1": 1, "EMAIL_REDACTED": 1})
            mock_reverse.assert_called_once_with(redacted_text)
    
    def test_get_last_identified_entities(self):
        """Test getting last identified entities."""
        self.pipeline._last_identified_entities = self.sample_entities
        
        entities = self.pipeline.get_last_identified_entities()
        
        assert entities == self.sample_entities
        assert entities is not self.pipeline._last_identified_entities  # Should be a copy
    
    def test_reset_pipeline(self):
        """Test resetting pipeline state."""
        # Set some state
        self.pipeline._last_identified_entities = self.sample_entities
        self.pipeline._last_replacement_mapping = self.sample_replacement_mapping
        self.pipeline.redactor.replacement_mapping = self.sample_replacement_mapping
        
        # Reset
        self.pipeline.reset_pipeline()
        
        # Check that state is cleared
        assert self.pipeline._last_identified_entities == {}
        assert self.pipeline._last_replacement_mapping == {}
        assert self.pipeline.redactor.replacement_mapping == {}
        assert self.pipeline.reverse_mapper.replacement_mapping == {}
        assert self.pipeline.reverse_mapper.reverse_mapping == {}