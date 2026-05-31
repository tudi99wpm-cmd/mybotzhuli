import respx
from httpx import Response

from packages.agent_core.agent import AgentService
from packages.agent_core.github_ops import GitHubPRClient
from packages.agent_core.llm import OpenAICompatibleLLMClient
from packages.agent_core.models import FailureSample, ImprovementSuggestion
from packages.agent_core.queue import MemoryQueue
from packages.agent_core.self_improve_executor import SelfImproveExecutor
from packages.agent_core.store import MemoryStore
from packages.evals.evaluator import run_benchmarks


def test_run_task_success() -> None:
    class StubLLM:
        def generate(self, prompt: str) -> str:
            return "Repository summary with api and worker details"

    service = AgentService(store=MemoryStore(), llm_client=StubLLM(), queue=MemoryQueue())
    task = service.create_task("Describe this repository")

    result = service.run_task(task.id)

    assert result is not None
    assert result.status.value == "succeeded"
    assert result.output is not None
    assert "Task completed" in result.output
    assert "worker" in result.output


def test_run_task_failure_collects_sample() -> None:
    store = MemoryStore()
    service = AgentService(store=store, llm_client=object(), queue=MemoryQueue())
    task = service.create_task("fail the task for testing")

    result = service.run_task(task.id)

    assert result is not None
    assert result.status.value == "failed"
    assert len(store.list_failure_samples(limit=10)) == 1


def test_run_self_improve_generates_report(tmp_path, monkeypatch) -> None:
    from packages.agent_core import config as config_module

    class StubExecutor:
        def execute(self, suggestions, pull_request):
            return type(
                "Execution",
                (),
                {
                    "branch_name": pull_request.branch_name,
                    "commit_message": pull_request.title,
                    "commit_sha": "abc123",
                },
            )()

    monkeypatch.setattr(config_module.settings, "artifact_dir", str(tmp_path))
    monkeypatch.setattr(config_module.settings, "github_token", "")
    monkeypatch.setattr(config_module.settings, "github_repository", "")

    store = MemoryStore()
    store.add_failure_sample(FailureSample(task_id="1", input="fail", error="boom"))
    service = AgentService(
        store=store,
        llm_client=object(),
        queue=MemoryQueue(),
        self_improve_executor=StubExecutor(),
    )

    report = service.run_self_improve()

    assert report.sample_count == 1
    assert report.suggestions
    assert tmp_path.joinpath("self_improve_report.json").exists()
    assert report.branch_name is not None
    assert report.commit_sha == "abc123"


@respx.mock
def test_openai_compatible_client() -> None:
    route = respx.post("https://token.sensenova.cn/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Model response"
                        }
                    }
                ]
            },
        )
    )

    from packages.agent_core import config as config_module

    monkey_settings = config_module.settings
    monkey_settings.openai_base_url = "https://token.sensenova.cn/v1"
    monkey_settings.openai_api_key = "test-key"
    monkey_settings.model_name = "deepseek-v4-flash"

    client = OpenAICompatibleLLMClient()
    result = client.generate("hello")

    assert route.called
    assert result == "Model response"


@respx.mock
def test_github_pr_client() -> None:
    route = respx.post("https://api.github.com/repos/tudi99wpm-cmd/mybotzhuli/pulls").mock(
        return_value=Response(201, json={"html_url": "https://github.com/pr/1", "number": 1})
    )

    from packages.agent_core import config as config_module

    config_module.settings.github_token = "test-token"
    config_module.settings.github_repository = "tudi99wpm-cmd/mybotzhuli"
    config_module.settings.github_api_url = "https://api.github.com"

    client = GitHubPRClient()
    result = client.create_pr_draft("test", "body", "branch")

    assert route.called
    assert result == {"url": "https://github.com/pr/1", "number": "1"}
    assert client.repository_branch_ref("feature") == "tudi99wpm-cmd:feature"


def test_self_improve_executor(tmp_path, monkeypatch) -> None:
    from packages.agent_core import config as config_module

    class StubGitClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def create_branch(self, branch_name: str) -> None:
            self.calls.append(("branch", branch_name))

        def add_files(self, *paths: str) -> None:
            self.calls.append(("add", paths))

        def commit(self, message: str) -> str:
            self.calls.append(("commit", message))
            return "commit-sha"

        def push_branch(self, branch_name: str) -> None:
            self.calls.append(("push", branch_name))

    monkeypatch.setattr(config_module.settings, "self_improve_auto_push", True)

    git_client = StubGitClient()
    executor = SelfImproveExecutor(repo_path=tmp_path, git_client=git_client)
    execution = executor.execute(
        suggestions=[
            ImprovementSuggestion(
                title="Improve retry flow",
                rationale="Repeated failures need a recovery branch.",
                proposed_change="Add retry and fallback handling for repeated task errors.",
            )
        ],
        pull_request=type(
            "PR",
            (),
            {
                "branch_name": "self-improve-1",
                "title": "chore: self-improve",
                "body": "body",
            },
        )(),
    )

    assert execution.commit_sha == "commit-sha"
    assert (tmp_path / "docs" / "self_improve" / "auto_improvements.md").exists()
    assert ("push", "self-improve-1") in git_client.calls


def test_benchmark_runner() -> None:
    summary = run_benchmarks()

    assert summary["total"] == 3
    assert summary["passed"] == 3
