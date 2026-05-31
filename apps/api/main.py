from fastapi import FastAPI, HTTPException

from packages.agent_core.agent import AgentService
from packages.agent_core.config import settings
from packages.agent_core.models import SelfImproveRun, TaskCreateRequest, TaskResponse
from packages.agent_core.queue import get_queue
from packages.agent_core.store import get_store

app = FastAPI(title=settings.app_name)

store = get_store()
queue = get_queue()
agent_service = AgentService(store=store, queue=queue)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest) -> TaskResponse:
    task = agent_service.create_task(payload.input)
    return TaskResponse.model_validate(task)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@app.post("/tasks/{task_id}/run", response_model=TaskResponse)
def run_task(task_id: str) -> TaskResponse:
    task = agent_service.run_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@app.post("/self-improve/run", response_model=SelfImproveRun)
def run_self_improve() -> SelfImproveRun:
    return agent_service.run_self_improve()
