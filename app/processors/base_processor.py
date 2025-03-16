"""
Base Processor Interface

Defines the interface that all document processors must implement.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseProcessor(ABC):
    """
    Base class for document processors that handle different aspects of document processing.
    """
    
    @abstractmethod
    def process_document(self, content: str, file_path: Path) -> None:
        """
        Process a single document.
        
        Args:
            content: The document content as text
            file_path: Path to the source document
        """
        pass
    
    @abstractmethod
    def finalize(self) -> None:
        """
        Perform any final operations after all documents have been processed.
        """
        pass
