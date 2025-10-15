"""
Data models for the VRIN SDK
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    """Represents a document to be processed and indexed."""
    
    content: str
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    user_id: Optional[str] = None
    document_type: str = "text"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.title is None:
            self.title = "Untitled Document"
        if self.source is None:
            self.source = "vrin-sdk"
        if self.user_id is None:
            self.user_id = "default"


@dataclass
class QueryResult:
    """Represents a search result from the knowledge base."""
    
    content: str
    score: float
    search_type: str
    metadata: Dict[str, Any]
    chunk_id: str
    graph_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.graph_context is None:
            self.graph_context = {"related_chunks": [], "graph_score": 0.0}
    
    @property
    def title(self) -> Optional[str]:
        """Get the document title from metadata."""
        return self.metadata.get('title')
    
    @property
    def tags(self) -> List[str]:
        """Get the document tags from metadata."""
        return self.metadata.get('tags', [])
    
    @property
    def source(self) -> Optional[str]:
        """Get the document source from metadata."""
        return self.metadata.get('source')


@dataclass
class JobStatus:
    """Represents the status of a processing job."""
    
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    message: str
    timestamp: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    progress: int = 0
    completed_at: Optional[int] = None
    error_details: Optional[str] = None
    estimated_completion: Optional[str] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if the job has completed successfully."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if the job has failed."""
        return self.status == "failed"
    
    @property
    def is_processing(self) -> bool:
        """Check if the job is still processing."""
        return self.status in ["queued", "processing"]
    
    @property
    def completion_time(self) -> Optional[datetime]:
        """Get the completion time as a datetime object."""
        if self.completed_at:
            return datetime.fromtimestamp(self.completed_at)
        return None
    
    @property
    def creation_time(self) -> Optional[datetime]:
        """Get the creation time as a datetime object."""
        if self.timestamp:
            return datetime.fromtimestamp(self.timestamp)
        return None


@dataclass
class SearchResponse:
    """Represents a complete search response."""
    
    query: str
    results: List[QueryResult]
    search_time: float
    total_results: int
    search_type: str
    services_available: Dict[str, bool]
    
    def __len__(self) -> int:
        return len(self.results)
    
    def __iter__(self):
        return iter(self.results)
    
    def __getitem__(self, index):
        return self.results[index] 