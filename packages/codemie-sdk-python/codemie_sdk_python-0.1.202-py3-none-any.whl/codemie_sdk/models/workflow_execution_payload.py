"""Workflow execution payload models."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkflowExecutionCreateRequest(BaseModel):
    """Request model for workflow execution creation."""

    model_config = ConfigDict(populate_by_name=True)

    user_input: Optional[str] = Field(
        None, description="User input for the workflow execution"
    )
    file_name: Optional[str] = Field(
        None, description="File name associated with the workflow execution"
    )
