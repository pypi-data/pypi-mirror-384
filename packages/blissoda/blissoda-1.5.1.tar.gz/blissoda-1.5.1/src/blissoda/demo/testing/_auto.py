"""Define all fixtures that will be used for all tests."""

from ewoksjob.client.celery.utils import get_not_finished_futures

from ._display import print_message
from ._fixtures import integration_fixture


@integration_fixture(autouse=True)
def _cleanup_celery_jobs():
    yield
    futures = get_not_finished_futures()
    if futures:
        print_message(
            f"{len(futures)} workflows are still running: abort them.", "warning"
        )
    for future in futures:
        _ = future.abort()
        try:
            _ = future.result(timeout=5)
        except Exception as ex:
            print_message(f"Aborted workflow: {ex}", "warning")
