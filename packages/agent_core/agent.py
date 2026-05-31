import json
from datetime import datetime, timezone

from packages.agent_core.config import settings
from packages.agent_core.github_ops import GitHubPRClient
from packages.agent_core.self_improve_executor import SelfImproveExecutor
from packages.agent_core.llm import LLMClient, get_llm_client
from packages.agent_core.models import FailureSample, ImprovementSuggestion, PullRequestDraft, SelfImproveExecution, SelfImproveRun, Task, TaskStatus
from packages.agent_core.queue import BaseQueue, get_queue
from packages.agent_core.store import BaseStore


class AgentService:
    def __init__(
        self,
        store: BaseStore,
        llm_client: LLMClient | None = None,
        queue: BaseQueue | None = None,
        self_improve_executor: SelfImproveExecutor | None = None,
    ) -> None:
        self.store = store
        self.llm_client = llm_client or get_llm_client()
        self.queue = queue or get_queue()
        self.github_pr_client = GitHubPRClient()
        self.self_improve_executor = self_improve_executor or SelfImproveExecutor()

    def create_task(self, input_text: str) -> Task:
        task = Task(input=input_text)
        saved = self.store.create_task(task)
        self.queue.enqueue(saved.id)
        return saved

    def run_next_task(self) -> Task | None:
        task_id = self.queue.dequeue(timeout=1)
        if task_id is None:
            return None
        return self.run_task(task_id)

    def run_task(self, task_id: str) -> Task | None:
        task = self.store.get_task(task_id)
        if task is None:
            return None

        task.status = TaskStatus.running
        task.updated_at = self._utc_now()
        self.store.update_task(task)

        try:
            task.output = self._build_response(task.input)
            task.status = TaskStatus.succeeded
            task.error = None
        except Exception as exc:
            task.status = TaskStatus.failed
            task.error = str(exc)
            self.store.add_failure_sample(FailureSample(task_id=task.id, input=task.input, error=task.error))
        finally:
            task.updated_at = self._utc_now()
            self.store.update_task(task)

        return task

    def run_self_improve(self) -> SelfImproveRun:
        samples = self.store.list_failure_samples(settings.self_improve_sample_limit)
        suggestions = self._generate_suggestions(samples)
        pr_draft = self._build_pull_request_draft(suggestions)
        pr_url = None
        execution: SelfImproveExecution | None = None
        if pr_draft is not None:
            execution = self.self_improve_executor.execute(suggestions, pr_draft)
        if pr_draft is not None:
            head_branch = self.github_pr_client.repository_branch_ref(pr_draft.branch_name)
            created_pr = self.github_pr_client.create_pr_draft(pr_draft.title, pr_draft.body, head_branch)
            if created_pr is not None:
                pr_url = created_pr.get("url")
                pr_draft.url = pr_url
        report_path = settings.artifact_path / "self_improve_report.json"
        report_path.write_text(
            json.dumps(
                {
                    "generated_at": self._utc_now().isoformat(),
                    "sample_count": len(samples),
                    "suggestions": [item.model_dump(mode="json") for item in suggestions],
                    "pull_request": pr_draft.model_dump(mode="json") if pr_draft else None,
                },
                indent=2,
            )
        )
        return SelfImproveRun(
            sample_count=len(samples),
            suggestions=suggestions,
            report_path=str(report_path),
            pr_url=pr_url,
            branch_name=execution.branch_name if execution else None,
            commit_sha=execution.commit_sha if execution else None,
            commit_message=execution.commit_message if execution else None,
        )

    def _build_response(self, input_text: str) -> str:
        if self._should_fail(input_text):
            raise ValueError("Triggered failure sample for self-improvement pipeline")

        prompt = (
            "You are executing a user task inside a recursive self-improving software agent. "
            "Return a concise result with clear actionability.\n\n"
            f"User task:\n{input_text.strip()}"
        )
        content = self.llm_client.generate(prompt)
        return f"Task completed.\nModel target: {settings.model_name}\n{content}"

    def _generate_suggestions(self, samples: list[FailureSample]) -> list[ImprovementSuggestion]:
        if not samples:
            return [
                ImprovementSuggestion(
                    title="Seed benchmark tasks",
                    rationale="系统当前还没有失败样本，先建立评测数据集可以让后续进化有稳定目标。",
                    proposed_change="在 packages/evals/benchmarks.json 中加入真实任务样本，并在 CI 中持续执行。",
                )
            ]

        grouped_errors: dict[str, int] = {}
        for sample in samples:
            grouped_errors[sample.error] = grouped_errors.get(sample.error, 0) + 1

        suggestions: list[ImprovementSuggestion] = []
        for error_text, count in grouped_errors.items():
            suggestions.append(
                ImprovementSuggestion(
                    title=f"Stabilize repeated failure ({count})",
                    rationale=f"相同错误出现 {count} 次，说明当前 agent loop 缺少对应的恢复逻辑。",
                    proposed_change=(
                        "为失败任务增加分类、重试和回退分支，并把该错误加入回归评测集。"
                        f" Error: {error_text}"
                    ),
                )
            )
        return suggestions

    def _build_pull_request_draft(self, suggestions: list[ImprovementSuggestion]) -> PullRequestDraft | None:
        if not suggestions:
            return None
        branch_name = f"{settings.self_improve_branch_prefix}-{self._utc_now().strftime('%Y%m%d%H%M%S')}"
        title = f"chore: self-improve from {len(suggestions)} suggestions"
        body_lines = ["## Auto-generated self-improvement proposal", ""]
        for suggestion in suggestions:
            body_lines.append(f"- {suggestion.title}: {suggestion.proposed_change}")
        return PullRequestDraft(branch_name=branch_name, title=title, body="\n".join(body_lines))

    def _should_fail(self, input_text: str) -> bool:
        lowered = input_text.lower()
        return "fail" in lowered or "error" in lowered

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)
