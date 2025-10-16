"""
Enhanced data types for Kalibr app-level framework
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from datetime import datetime
import uuid
import io

class FileUpload(BaseModel):
    """Enhanced file upload handling for AI model integrations"""
    filename: str
    content_type: str
    size: int
    content: bytes
    upload_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uploaded_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class ImageData(BaseModel):
    """Image data type for AI vision capabilities"""
    filename: str
    content_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: str  # jpeg, png, webp, etc.
    content: bytes
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    class Config:
        arbitrary_types_allowed = True

class TableData(BaseModel):
    """Structured table data for AI analysis"""
    headers: List[str]
    rows: List[List[Any]]
    table_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = None

class StreamingResponse(BaseModel):
    """Base class for streaming responses"""
    chunk_id: str
    content: Any
    is_final: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)

class Session(BaseModel):
    """Session management for stateful interactions"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    
    def get(self, key: str, default=None):
        """Get session data"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set session data"""
        self.data[key] = value
        self.last_accessed = datetime.now()
    
    def delete(self, key: str):
        """Delete session data"""
        if key in self.data:
            del self.data[key]

class AuthenticatedUser(BaseModel):
    """Authenticated user context"""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    auth_method: str  # "jwt", "oauth", "api_key", etc.
    
class FileDownload(BaseModel):
    """File download response"""
    filename: str
    content_type: str
    content: bytes
    
    class Config:
        arbitrary_types_allowed = True

class AnalysisResult(BaseModel):
    """Generic analysis result structure"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str  # "success", "error", "pending"
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class WorkflowState(BaseModel):
    """Workflow state management"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)