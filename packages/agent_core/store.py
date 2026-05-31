import json
from abc import ABC, abstractmethod
from pathlib import Path

import psycopg

from packages.agent_core.config import settings
from packages.agent_core.models import FailureSample, Task, TaskStatus


class BaseStore(ABC):
    @abstractmethod
    def create_task(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def update_task(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: str) -> Task | None:
        raise NotImplementedError

    @abstractmethod
    def list_pending_tasks(self, limit: int) -> list[Task]:
        raise NotImplementedError

    @abstractmethod
    def add_failure_sample(self, sample: FailureSample) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_failure_samples(self, limit: int) -> list[FailureSample]:
        raise NotImplementedError


class MemoryStore(BaseStore):
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.failure_samples: list[FailureSample] = []

    def create_task(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    def update_task(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def list_pending_tasks(self, limit: int) -> list[Task]:
        return [task for task in self.tasks.values() if task.status == TaskStatus.pending][:limit]

    def add_failure_sample(self, sample: FailureSample) -> None:
        self.failure_samples.append(sample)

    def list_failure_samples(self, limit: int) -> list[FailureSample]:
        return self.failure_samples[-limit:]


class FileStore(MemoryStore):
    def __init__(self, data_path: Path) -> None:
        super().__init__()
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def create_task(self, task: Task) -> Task:
        saved = super().create_task(task)
        self._persist()
        return saved

    def update_task(self, task: Task) -> Task:
        saved = super().update_task(task)
        self._persist()
        return saved

    def add_failure_sample(self, sample: FailureSample) -> None:
        super().add_failure_sample(sample)
        self._persist()

    def _load(self) -> None:
        if not self.data_path.exists():
            return
        payload = json.loads(self.data_path.read_text())
        self.tasks = {item["id"]: Task.model_validate(item) for item in payload.get("tasks", [])}
        self.failure_samples = [FailureSample.model_validate(item) for item in payload.get("failure_samples", [])]

    def _persist(self) -> None:
        payload = {
            "tasks": [task.model_dump(mode="json") for task in self.tasks.values()],
            "failure_samples": [sample.model_dump(mode="json") for sample in self.failure_samples],
        }
        self.data_path.write_text(json.dumps(payload, indent=2))


class PostgresStore(BaseStore):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._init_tables()

    def create_task(self, task: Task) -> Task:
        with self._connect() as conn:
            conn.execute(
                """
                insert into tasks (id, input, status, output, error, created_at, updated_at)
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (task.id, task.input, task.status.value, task.output, task.error, task.created_at, task.updated_at),
            )
            conn.commit()
        return task

    def update_task(self, task: Task) -> Task:
        with self._connect() as conn:
            conn.execute(
                """
                update tasks
                set input = %s, status = %s, output = %s, error = %s, updated_at = %s
                where id = %s
                """,
                (task.input, task.status.value, task.output, task.error, task.updated_at, task.id),
            )
            conn.commit()
        return task

    def get_task(self, task_id: str) -> Task | None:
        with self._connect() as conn:
            row = conn.execute(
                "select id, input, status, output, error, created_at, updated_at from tasks where id = %s",
                (task_id,),
            ).fetchone()
        return self._task_from_row(row) if row else None

    def list_pending_tasks(self, limit: int) -> list[Task]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select id, input, status, output, error, created_at, updated_at
                from tasks
                where status = %s
                order by created_at asc
                limit %s
                """,
                (TaskStatus.pending.value, limit),
            ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def add_failure_sample(self, sample: FailureSample) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert into failure_samples (task_id, input, error, created_at) values (%s, %s, %s, %s)",
                (sample.task_id, sample.input, sample.error, sample.created_at),
            )
            conn.commit()

    def list_failure_samples(self, limit: int) -> list[FailureSample]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select task_id, input, error, created_at
                from failure_samples
                order by created_at desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        return [
            FailureSample(task_id=row[0], input=row[1], error=row[2], created_at=row[3])
            for row in rows
        ]

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url)

    def _init_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists tasks (
                    id text primary key,
                    input text not null,
                    status text not null,
                    output text,
                    error text,
                    created_at timestamptz not null,
                    updated_at timestamptz not null
                )
                """
            )
            conn.execute(
                """
                create table if not exists failure_samples (
                    id bigserial primary key,
                    task_id text not null,
                    input text not null,
                    error text not null,
                    created_at timestamptz not null
                )
                """
            )
            conn.commit()

    def _task_from_row(self, row: tuple[object, ...]) -> Task:
        return Task(
            id=str(row[0]),
            input=str(row[1]),
            status=TaskStatus(str(row[2])),
            output=row[3],
            error=row[4],
            created_at=row[5],
            updated_at=row[6],
        )


_store: BaseStore | None = None


def get_store() -> BaseStore:
    global _store
    if _store is not None:
        return _store
    if settings.store_backend == "postgres":
        _store = PostgresStore(settings.database_url)
    elif settings.store_backend == "file":
        _store = FileStore(settings.artifact_path / "store.json")
    else:
        _store = MemoryStore()
    return _store
