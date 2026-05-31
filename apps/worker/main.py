import time

from packages.agent_core.agent import AgentService
from packages.agent_core.queue import get_queue
from packages.agent_core.store import get_store


def main() -> None:
    store = get_store()
    queue = get_queue()
    service = AgentService(store=store, queue=queue)

    while True:
        task = service.run_next_task()
        if task is None:
            time.sleep(1)


if __name__ == "__main__":
    main()
