"""
Translation Module - Client-side LLM Architecture
This module provides utilities for translation workflows but delegates LLM calls to clients
"""

import asyncio
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TranslationUtils:
    """
    Translation utilities for client-side LLM architecture
    Provides helper functions without making LLM API calls
    """
    
    def __init__(self):
        self.max_chunk_size = 3000  # Maximum characters per translation chunk
    
    def smart_chunk_content(self, content: str) -> List[str]:
        """
        Intelligently split content into chunks while preserving structure
        
        Args:
            content: Text content to chunk
            
        Returns:
            List of content chunks
        """
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line)
            
            # If adding this line would exceed the chunk size
            if current_length + line_length > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length + 1  # +1 for newline
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def calculate_translation_metrics(self, original: str, translated: str) -> Dict[str, Any]:
        """
        Calculate translation quality metrics
        
        Args:
            original: Original text
            translated: Translated text
            
        Returns:
            Dictionary with translation metrics
        """
        try:
            original_length = len(original)
            translated_length = len(translated)
            
            # Length ratio (reasonable translations should be within 50-200% of original)
            length_ratio = translated_length / original_length if original_length > 0 else 0
            
            # Structure preservation (check for headers, formatting)
            original_headers = original.count('#') if '#' in original else 0
            translated_headers = translated.count('#') if '#' in translated else 0
            
            # Word count estimates
            original_words = len(original.split()) if original else 0
            translated_words = len(translated.split()) if translated else 0
            
            return {
                "original_length": original_length,
                "translated_length": translated_length,
                "length_ratio": length_ratio,
                "original_words": original_words,
                "translated_words": translated_words,
                "word_ratio": translated_words / original_words if original_words > 0 else 0,
                "headers_preserved": original_headers == translated_headers,
                "original_headers": original_headers,
                "translated_headers": translated_headers,
                "suggested_chunks": len(self.smart_chunk_content(original)) if len(original) > self.max_chunk_size else 1
            }
            
        except Exception as e:
            logger.error(f"Error calculating translation metrics: {e}")
            return {
                "error": str(e),
                "original_length": len(original) if original else 0,
                "translated_length": len(translated) if translated else 0
            }
    
    def validate_translation_completeness(self, original: str, translated: str) -> Dict[str, Any]:
        """
        Validate that translation appears complete and well-formed
        
        Args:
            original: Original text
            translated: Translated text
            
        Returns:
            Validation results
        """
        try:
            issues = []
            warnings = []
            
            # Check for empty translation
            if not translated or not translated.strip():
                issues.append("Translation is empty")
                return {
                    "valid": False,
                    "issues": issues,
                    "warnings": warnings
                }
            
            # Check length ratio
            metrics = self.calculate_translation_metrics(original, translated)
            length_ratio = metrics.get("length_ratio", 0)
            
            if length_ratio < 0.3:
                issues.append("Translation appears too short (may be incomplete)")
            elif length_ratio > 3.0:
                warnings.append("Translation appears much longer than original")
            
            # Check structure preservation
            if not metrics.get("headers_preserved", True):
                warnings.append("Header structure may not be preserved")
            
            # Check for obvious formatting issues
            if original.count('\n\n') > 0 and translated.count('\n\n') == 0:
                warnings.append("Paragraph breaks may not be preserved")
            
            # Check for markdown formatting preservation
            markdown_elements = ['**', '*', '#', '|', '```', '`']
            for element in markdown_elements:
                original_count = original.count(element)
                translated_count = translated.count(element)
                if original_count > 0 and translated_count == 0:
                    warnings.append(f"Markdown formatting ({element}) may not be preserved")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error validating translation: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    def prepare_batch_context(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare context information for batch translation
        
        Args:
            documents: List of document information
            
        Returns:
            Batch context for consistent translation
        """
        try:
            total_content_length = 0
            total_chunks_needed = 0
            document_types = set()
            
            context = {
                "batch_info": {
                    "total_documents": len(documents),
                    "prepared_at": asyncio.get_event_loop().time()
                },
                "documents": []
            }
            
            for doc in documents:
                doc_content = doc.get("content", "")
                doc_metrics = self.calculate_translation_metrics(doc_content, "")
                chunks = self.smart_chunk_content(doc_content) if doc_content else []
                
                document_types.add(doc.get("file_type", "unknown"))
                total_content_length += len(doc_content)
                total_chunks_needed += len(chunks)
                
                context["documents"].append({
                    "file_id": doc.get("file_id"),
                    "name": doc.get("name"),
                    "file_type": doc.get("file_type"),
                    "content_length": len(doc_content),
                    "estimated_chunks": len(chunks),
                    "word_count": doc_metrics.get("original_words", 0)
                })
            
            context["batch_info"].update({
                "total_content_length": total_content_length,
                "total_chunks_needed": total_chunks_needed,
                "document_types": list(document_types),
                "average_doc_length": total_content_length / len(documents) if documents else 0
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing batch context: {e}")
            return {
                "error": str(e),
                "batch_info": {
                    "total_documents": len(documents),
                    "error": "Failed to prepare context"
                }
            }
