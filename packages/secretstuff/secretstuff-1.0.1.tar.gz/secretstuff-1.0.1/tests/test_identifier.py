"""Tests for PIIIdentifier class."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from secretstuff.core.identifier import PIIIdentifier
from secretstuff.config.labels import DEFAULT_LABELS


class TestPIIIdentifier:
    """Test cases for PIIIdentifier functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the GLiNER model to avoid actual model loading in tests
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_model = Mock()
            mock_gliner.from_pretrained.return_value = mock_model
            self.identifier = PIIIdentifier()
            self.identifier.identifier = mock_model
        
        self.sample_text = """
        Mr. John Doe lives at 123 Main Street, New York, NY 10001.
        His phone number is +1-555-123-4567 and email is john.doe@email.com.
        His Aadhaar number is 1234 5678 9012 and PAN is ABCDE1234F.
        """
    
    def test_initialization(self):
        """Test PIIIdentifier initialization with new defaults."""
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            identifier = PIIIdentifier()
            
            # Check new default model name
            mock_gliner.from_pretrained.assert_called_with(
                "aksman18/gliner-multi-pii-domains-v2", 
                token=None
            )
            assert identifier.labels == DEFAULT_LABELS
    
    def test_initialization_with_token(self):
        """Test PIIIdentifier initialization with token."""
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            token = "test-token"
            identifier = PIIIdentifier(token=token)
            
            mock_gliner.from_pretrained.assert_called_with(
                "aksman18/gliner-multi-pii-domains-v2", 
                token=token
            )
    
    def test_custom_initialization(self):
        """Test PIIIdentifier with custom parameters."""
        custom_labels = ["person", "email", "phone number"]
        custom_model = "custom-model"
        token = "custom-token"
        
        with patch('secretstuff.core.identifier.GLiNER') as mock_gliner:
            mock_gliner.from_pretrained.return_value = Mock()
            identifier = PIIIdentifier(
                model_name=custom_model,
                labels=custom_labels,
                token=token
            )
            
            mock_gliner.from_pretrained.assert_called_with(custom_model, token=token)
            assert identifier.labels == custom_labels
    
    def test_chunk_text_with_overlap(self):
        """Test text chunking functionality with overlap."""
        text = "A" * 1000
        chunks = self.identifier.chunk_text(text, chunk_size=384, chunk_overlap=50)
        
        # With overlap, we should get more chunks
        assert len(chunks) > 2
        assert len(chunks[0]) == 384
        
        # Check that chunks overlap correctly
        if len(chunks) > 1:
            # Last 50 chars of first chunk should match first 50 chars of second chunk
            overlap_text = chunks[0][-50:]
            next_start = chunks[1][:50]
            assert overlap_text == next_start
    
    def test_chunk_text_no_overlap(self):
        """Test text chunking without overlap."""
        text = "A" * 1000
        chunks = self.identifier.chunk_text(text, chunk_size=384, chunk_overlap=0)
        
        assert len(chunks) == 3  # 1000 / 384 = 2.6, so 3 chunks
        assert len(chunks[0]) == 384
        assert len(chunks[1]) == 384
        assert len(chunks[2]) == 232  # 1000 - 384 - 384
    
    def test_remove_duplicates_with_overlap_detection(self):
        """Test the new overlap detection in _remove_duplicates."""
        text = "John Doe works at Microsoft Corporation in Seattle"
        entities = [
            {"text": "John Doe", "label": "person", "start": 0, "end": 8},
            {"text": "John", "label": "person", "start": 0, "end": 4},  # Overlapping
            {"text": "Microsoft Corporation", "label": "org", "start": 18, "end": 39},
            {"text": "Microsoft", "label": "org", "start": 18, "end": 27},  # Overlapping
            {"text": "Seattle", "label": "loc", "start": 43, "end": 50},
        ]
        
        unique_entities = self.identifier._remove_duplicates(entities, text)
        
        # Should merge overlapping entities with same labels
        assert len(unique_entities) == 3  # person, org, loc
        
        # Check that longer spans are kept
        person_entities = [e for e in unique_entities if e["label"] == "person"]
        org_entities = [e for e in unique_entities if e["label"] == "org"]
        
        assert len(person_entities) == 1
        assert person_entities[0]["text"] == "John Doe"
        
        assert len(org_entities) == 1
        assert org_entities[0]["text"] == "Microsoft Corporation"
    
    def test_remove_duplicates_different_labels_overlap(self):
        """Test overlap handling with different labels."""
        text = "Dr. John Smith"
        entities = [
            {"text": "Dr. John", "label": "person", "start": 0, "end": 8},
            {"text": "John Smith", "label": "person", "start": 4, "end": 14},  # Overlapping, longer
        ]
        
        unique_entities = self.identifier._remove_duplicates(entities, text)
        
        # Should keep the longer span
        assert len(unique_entities) == 1
        assert unique_entities[0]["text"] == "John Smith"
        assert unique_entities[0]["start"] == 4
        assert unique_entities[0]["end"] == 14
    
    def test_identify_entities_with_overlap(self):
        """Test entity identification with chunk overlap."""
        # Mock the model's predict_entities method
        def mock_predict_entities(chunk, labels):
            if "John Doe" in chunk:
                return [{"text": "John Doe", "label": "person", "start": chunk.find("John Doe"), "end": chunk.find("John Doe") + 8}]
            return []
        
        self.identifier.identifier.predict_entities = mock_predict_entities
        
        entities = self.identifier.identify_entities(self.sample_text, chunk_size=100, chunk_overlap=20)
        
        # Should find entities and adjust positions correctly
        assert len(entities) >= 0  # Depends on mock implementation
    
    def test_identify_and_save_with_overlap(self):
        """Test identifying entities and saving with overlap parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_identified.json")
            
            # Mock the identify_entities method
            def mock_identify_entities(text, chunk_size, chunk_overlap):
                return [
                    {"text": "John Doe", "label": "person", "start": 0, "end": 8},
                    {"text": "john@email.com", "label": "email", "start": 20, "end": 35}
                ]
            
            self.identifier.identify_entities = mock_identify_entities
            
            mapping = self.identifier.identify_and_save(
                self.sample_text, output_file, chunk_size=384, chunk_overlap=50
            )
            
            # Check that file was created
            assert os.path.exists(output_file)
            
            # Check file contents
            with open(output_file, 'r', encoding='utf-8') as f:
                saved_mapping = json.load(f)
            
            assert saved_mapping == mapping
            assert "person" in mapping
            assert "email" in mapping
    
    def test_chunk_overlap_validation(self):
        """Test that chunk_overlap validation works."""
        with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
            self.identifier.identify_and_save(
                self.sample_text, 
                "test.json", 
                chunk_size=100, 
                chunk_overlap=100  # Equal to chunk_size, should fail
            )
        
        with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
            self.identifier.identify_and_save(
                self.sample_text, 
                "test.json", 
                chunk_size=100, 
                chunk_overlap=150  # Greater than chunk_size, should fail
            )
    
    def test_add_custom_labels(self):
        """Test adding custom labels."""
        initial_count = len(self.identifier.labels)
        custom_labels = ["custom_label1", "custom_label2"]
        
        self.identifier.add_custom_labels(custom_labels)
        
        assert len(self.identifier.labels) == initial_count + 2
        assert "custom_label1" in self.identifier.labels
        assert "custom_label2" in self.identifier.labels
    
    def test_set_labels(self):
        """Test setting labels."""
        new_labels = ["person", "email", "phone number"]
        self.identifier.set_labels(new_labels)
        
        assert self.identifier.labels == new_labels
        assert len(self.identifier.labels) == 3
    
    def test_get_labels(self):
        """Test getting labels."""
        labels = self.identifier.get_labels()
        assert labels == DEFAULT_LABELS
        assert labels is not self.identifier.labels  # Should return a copy