import json
from pathlib import Path

from packages.agent_core.agent import AgentService
from packages.agent_core.llm import LLMClient
from packages.agent_core.queue import MemoryQueue
from packages.agent_core.store import MemoryStore


class BenchmarkLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "repository structure" in lowered:
            return "Repository summary:\n1. api handles HTTP requests\n2. worker consumes queued tasks\n3. packages contains agent logic"
        return "1. add stronger evals\n2. persist task state\n3. automate pull request creation"


def run_benchmarks() -> dict[str, object]:
    benchmark_path = Path(__file__).with_name("benchmarks.json")
    cases = json.loads(benchmark_path.read_text())
    store = MemoryStore()
    service = AgentService(store=store, llm_client=BenchmarkLLMClient(), queue=MemoryQueue())

    passed = 0
    results: list[dict[str, object]] = []

    for case in cases:
        task = service.create_task(case["input"])
        result = service.run_task(task.id)

        case_passed = True
        if "must_include" in case:
            output = result.output or ""
            case_passed = all(token in output for token in case["must_include"])
        if "must_error" in case:
            error = result.error or ""
            case_passed = case["must_error"] in error

        if case_passed:
            passed += 1

        results.append(
            {
                "name": case["name"],
                "passed": case_passed,
                "status": result.status,
                "output": result.output,
                "error": result.error,
            }
        )

    return {
        "total": len(cases),
        "passed": passed,
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmarks(), indent=2, default=str))
