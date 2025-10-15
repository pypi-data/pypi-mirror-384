"""Workflow execution thoughts models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class WorkflowExecutionThought(BaseModel):
    """Model for workflow execution thought."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    execution_state_id: str
    parent_id: Optional[str] = None
    author_name: str
    author_type: str
    input_text: str
    content: str
    date: datetime
    children: List["WorkflowExecutionThought"] = []


# Update forward references for recursive model
WorkflowExecutionThought.model_rebuild()
