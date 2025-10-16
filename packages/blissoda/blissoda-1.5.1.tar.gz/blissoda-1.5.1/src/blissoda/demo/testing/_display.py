from contextlib import contextmanager
from datetime import datetime

try:
    from bliss.shell.standard import print_html
except ImportError:
    print_html = None


MESSAGE_STYLES = {
    "assert": {
        "passed": ("<ansicyan>[PASSED {timestamp}] {msg}</ansicyan>", "[PASSED] {msg}"),
        "failed": ("<orange>[FAILED {timestamp}] {msg}</orange>", "[FAILED] {msg}"),
    },
    "test": {
        "passed": (
            "<ansigreen>[PASSED {timestamp}] {msg}</ansigreen>",
            "[PASSED] {msg}",
        ),
        "failed": ("<ansired>[FAILED {timestamp}] {msg}</ansired>", "[FAILED] {msg}"),
    },
    "warning": {
        "passed": ("<orange>[WARN {timestamp}] {msg}</orange>", "[WARN] {msg}"),
        "failed": ("<ansired>[FAILED {timestamp}] {msg}</ansired>", "[FAILED] {msg}"),
    },
    "info": {
        "passed": ("<ansicyan>[INFO {timestamp}] {msg}</ansicyan>", "[INFO] {msg}"),
        "failed": ("<ansired>[FAILED {timestamp}] {msg}</ansired>", "[FAILED] {msg}"),
    },
}


@contextmanager
def print_message_on_exit(message: str, message_type: str, indent: int = 0):
    try:
        yield
    except Exception:
        print_message(message, message_type, status="failed")
        raise
    print_message(message, message_type)


def print_message(msg: str, message_type: str, status: str = "passed") -> None:
    try:
        style = MESSAGE_STYLES[message_type][status]
    except KeyError:
        raise ValueError(f"Unknown message_type={message_type!r} or status={status!r}")

    if message_type in ("assert", "info"):
        prefix = " "
    else:
        prefix = ""

    # Time stamps are useful when comparing with Celery time stamps for debugging
    timestamp = datetime.now().strftime("%H:%M:%S,%f")[:-3]

    html_fmt, plain_fmt = style
    if print_html:
        print_html(prefix + html_fmt.format(msg=msg, timestamp=timestamp))
    else:
        print(prefix + plain_fmt.format(msg=msg, timestamp=timestamp))
