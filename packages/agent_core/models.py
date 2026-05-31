from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    input: str
    status: TaskStatus = TaskStatus.pending
    output: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FailureSample(BaseModel):
    task_id: str
    input: str
    error: str
    created_at: datetime = Field(default_factory=utc_now)


class ImprovementSuggestion(BaseModel):
    title: str
    rationale: str
    proposed_change: str


class SelfImproveRun(BaseModel):
    sample_count: int
    suggestions: list[ImprovementSuggestion]
    report_path: str
    pr_url: str | None = None
    branch_name: str | None = None
    commit_sha: str | None = None
    commit_message: str | None = None


class PullRequestDraft(BaseModel):
    branch_name: str
    title: str
    body: str
    url: str | None = None


class SelfImproveExecution(BaseModel):
    branch_name: str
    commit_message: str
    commit_sha: str | None = None
    changed_files: list[str]


class TaskCreateRequest(BaseModel):
    input: str


class TaskResponse(BaseModel):
    id: str
    input: str
    status: TaskStatus
    output: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
