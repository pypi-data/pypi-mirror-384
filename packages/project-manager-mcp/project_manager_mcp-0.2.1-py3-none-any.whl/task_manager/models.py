"""
Pydantic models for Task Manager API request/response validation.

Provides data validation models for knowledge management endpoints,
task operations, and error response formatting.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import json


class KnowledgeRequest(BaseModel):
    """Request model for creating/updating knowledge items."""

    knowledge_id: Optional[int] = Field(
        None, description="ID for update operations, omit for create"
    )
    title: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Knowledge item title"
    )
    content: Optional[str] = Field(None, min_length=1, description="Knowledge item content")
    category: Optional[str] = Field(None, max_length=100, description="Category classification")
    tags: Optional[List[str]] = Field(None, description="Array of tag strings")
    parent_id: Optional[int] = Field(None, description="Parent knowledge item ID for hierarchy")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    epic_id: Optional[int] = Field(None, description="Associated epic ID")
    task_id: Optional[int] = Field(None, description="Associated task ID")
    priority: Optional[int] = Field(0, ge=0, le=5, description="Priority level 0-5")
    is_active: Optional[bool] = Field(True, description="Whether item is active")
    created_by: Optional[str] = Field(None, max_length=100, description="Creator identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata object")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        if v is not None:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("All tags must be non-empty strings")
        return v


class KnowledgeResponse(BaseModel):
    """Response model for knowledge item operations."""

    success: bool
    message: Optional[str] = None
    knowledge_id: Optional[int] = None
    operation: Optional[str] = None  # "created" or "updated"
    version: Optional[int] = None
    knowledge_item: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LogRequest(BaseModel):
    """Request model for appending knowledge log entries."""

    action_type: str = Field(min_length=1, max_length=50, description="Type of action performed")
    change_reason: Optional[str] = Field(
        None, max_length=500, description="Reason for the action/change"
    )
    created_by: Optional[str] = Field(
        None, max_length=100, description="User who performed the action"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata object")


class LogResponse(BaseModel):
    """Response model for knowledge log operations."""

    success: bool
    message: Optional[str] = None
    log_id: Optional[int] = None
    knowledge_id: Optional[int] = None
    knowledge_title: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


class KnowledgeDetailResponse(BaseModel):
    """Response model for knowledge item retrieval with logs."""

    success: bool
    message: Optional[str] = None
    knowledge_items: Optional[List[Dict[str, Any]]] = None
    total_count: Optional[int] = None
    filters_applied: Optional[Dict[str, Any]] = None
    logs: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: str
    code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Standard success response model."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


# Utility function to create consistent error responses
def create_error_response(
    message: str, code: Optional[int] = None, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response dictionary."""
    return {"success": False, "error": message, "code": code, "details": details}


# Utility function to create consistent success responses
def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized success response dictionary."""
    return {"success": True, "message": message, "data": data}


# Assumption Intelligence API Models


class ValidationExample(BaseModel):
    """Model for recent validation example in insights response."""

    id: int
    task_id: int
    task_name: str
    ra_tag: str
    outcome: str
    confidence: int
    validator_id: str
    validated_at: str
    notes: Optional[str] = None


class InsightsSummary(BaseModel):
    """Response model for /api/assumptions/insights endpoint."""

    success: bool = True
    total_validations: int
    success_rate: float = Field(description="Success rate between 0.0 and 1.0")
    outcome_breakdown: Dict[str, int] = Field(
        description="Count by outcome: validated, rejected, partial"
    )
    tag_type_breakdown: Dict[str, int] = Field(description="Count by normalized tag type")
    recent_examples: List[ValidationExample]
    trend_data: Optional[Dict[str, Any]] = None
    cache_timestamp: Optional[str] = None


class RecentValidation(BaseModel):
    """Model for recent validation activity."""

    id: int
    task_id: int
    ra_tag_id: str = Field(description="Unique ID of the specific RA tag")
    task_name: str
    project_name: Optional[str]
    epic_name: Optional[str]
    ra_tag: str
    ra_tag_type: str = Field(description="Normalized tag type from RA utilities")
    outcome: str
    confidence: int
    validator_id: str
    validated_at: str
    notes: Optional[str] = None
    context_snapshot: Optional[str] = None


class RecentValidationsResponse(BaseModel):
    """Response model for /api/assumptions/recent endpoint."""

    success: bool = True
    validations: List[RecentValidation]
    total_count: int
    has_more: bool
    next_cursor: Optional[int] = None


class TagTypeInfo(BaseModel):
    """Model for available RA tag type information."""

    normalized_type: str
    category: str
    subcategory: str
    count: int
    example_tags: List[str] = Field(max_length=3, description="Up to 3 example original tags")


class TagTypesResponse(BaseModel):
    """Response model for /api/assumptions/tag-types endpoint."""

    success: bool = True
    tag_types: List[TagTypeInfo]
    total_types: int
    cache_timestamp: Optional[str] = None
