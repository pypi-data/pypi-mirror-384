"""Workflow execution state models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class WorkflowExecutionStatusEnum(str, Enum):
    """Workflow execution state status."""

    IN_PROGRESS = "In Progress"
    NOT_STARTED = "Not Started"
    INTERRUPTED = "Interrupted"
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"
    ABORTED = "Aborted"


class WorkflowExecutionStateThought(BaseModel):
    """Model for workflow execution state thought."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    execution_state_id: str
    parent_id: Optional[str] = None
    author_name: str
    author_type: str
    date: datetime


class WorkflowExecutionState(BaseModel):
    """Model for workflow execution state."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    execution_id: str
    name: str
    task: Optional[str] = ""
    status: WorkflowExecutionStatusEnum = WorkflowExecutionStatusEnum.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    thoughts: Optional[List[WorkflowExecutionStateThought]] = None


class WorkflowExecutionStateOutput(BaseModel):
    """Model for workflow execution state output."""

    model_config = ConfigDict(populate_by_name=True)

    output: Optional[str] = None
