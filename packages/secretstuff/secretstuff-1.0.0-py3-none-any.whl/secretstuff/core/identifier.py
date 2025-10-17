import json
from typing import List, Dict, Any, Optional
from gliner import GLiNER
from ..config.labels import DEFAULT_LABELS


class PIIIdentifier:
    """
    Identifies personally identifiable information (PII) in text using GLiNER model.
    
    This class provides functionality to detect and extract various types of PII
    from text documents using a pre-trained GLiNER model.
    """
    
    def __init__(self, model_name: str = "aksman18/gliner-multi-pii-domains-v2", labels: Optional[List[str]] = None, token: Optional[str] = None):
        """
        Initialize the PII identifier.
        
        Args:
            model_name: Name of the GLiNER model to use
            labels: List of PII labels to identify. If None, uses DEFAULT_LABELS
            token: Token for the GLiNER model
        """
        self.identifier = GLiNER.from_pretrained(model_name, token=token)
        self.labels = labels or DEFAULT_LABELS.copy()
        
    def chunk_text(self, text: str, chunk_size: int = 384, chunk_overlap: int = 50) -> List[str]:
        """
        Split text into chunks of specified size.
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk in characters
            
        Returns:
            List of text chunks
        """
        chunks = []
        i = 0
        while i < len(text):
            chunk = text[i:min(i+chunk_size, len(text))]  
            chunks.append(chunk)
            if i+chunk_size>=len(text):
                return chunks
            i += chunk_size - chunk_overlap
    
    def identify_entities(self, text: str, chunk_size: int = 384, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Identify PII entities in the given text.
        
        Args:
            text: Input text to analyze
            chunk_size: Size of chunks for processing
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of identified entities with text, label, start, and end positions
        """
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)
        all_entities = []
        
        for i, chunk in enumerate(chunks):
            entities = self.identifier.predict_entities(chunk, self.labels)
            # Adjust entity positions to account for chunking
            offset = i * (chunk_size - chunk_overlap)
            for entity in entities:
                entity['start'] += offset
                entity['end'] += offset
            all_entities.extend(entities)
        
        return self._remove_duplicates(all_entities, text)
    
    def _remove_duplicates(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities while preserving order.
        
        Args:
            entities: List of entities to deduplicate
            text: Original text
        Returns:
            List of unique entities
        """
        entities = sorted(entities, key=lambda e: (e["start"], e["end"]))
        merged = []

        for entity in entities:
            if not merged:
                merged.append(entity)
                continue

            last = merged[-1]

            # Check if overlapping
            overlaps = not (entity["end"] <= last["start"] or entity["start"] >= last["end"])

            if overlaps:
                # For overlapping entities, always keep the longer span regardless of label
                last_len = last["end"] - last["start"]
                curr_len = entity["end"] - entity["start"]

                if curr_len > last_len:
                    merged[-1] = entity
                # else keep the last one (implicitly)

            else:
                merged.append(entity)

        return merged
    
    def create_entity_mapping(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create a mapping of entity labels to their text values.
        
        Args:
            entities: List of identified entities
            
        Returns:
            Dictionary mapping labels to lists of entity texts
        """
        entity_mapping = {}
        for entity in entities:
            entity_text = entity["text"]
            entity_label = entity["label"]
            
            if entity_label not in entity_mapping:
                entity_mapping[entity_label] = []
            
            if entity_text not in entity_mapping[entity_label]:
                entity_mapping[entity_label].append(entity_text)
        
        return entity_mapping
    
    def identify_and_save(self, text: str, output_file: str = "identified.json", 
                         chunk_size: int = 384, chunk_overlap: int = 50) -> Dict[str, List[str]]:
        """
        Identify PII entities and save results to JSON file.
        
        Args:
            text: Input text to analyze
            output_file: Path to save the identified entities JSON
            chunk_size: Size of chunks for processing
            
        Returns:
            Dictionary mapping labels to lists of entity texts
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        
        entities = self.identify_entities(text, chunk_size, chunk_overlap)
        entity_mapping = self.create_entity_mapping(entities)
        
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(entity_mapping, json_file, indent=2, ensure_ascii=False)
        
        return entity_mapping
    
    def add_custom_labels(self, custom_labels: List[str]) -> None:
        """
        Add custom labels to the existing label set.
        
        Args:
            custom_labels: List of additional labels to include
        """
        self.labels.extend(custom_labels)
    
    def set_labels(self, labels: List[str]) -> None:
        """
        Set the labels to use for PII identification.
        
        Args:
            labels: List of labels to use
        """
        self.labels = labels.copy()
    
    def get_labels(self) -> List[str]:
        """
        Get the current list of labels.
        
        Returns:
            Current list of PII labels
        """
        return self.labels.copy()
