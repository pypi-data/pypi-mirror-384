import time

from ewoksjob.client import Future
from ewoksjob.client.celery.utils import get_not_finished_futures

from ._display import print_message


def wait_workflows(
    *futures: Future, timeout: int = 30, raise_on_error: bool = False
) -> None:
    if not futures:
        futures = get_not_finished_futures()

    t0 = time.time()
    for future in futures:
        timepassed = time.time() - t0
        try:
            _ = future.result(timeout=timeout - timepassed)
        except Exception as ex:
            if raise_on_error:
                raise
            print_message(f"Workflow failed: {ex}", "warning")
        print_message(f"Job {future.uuid!r} finished", "info")
