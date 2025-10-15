import time
from typing import Callable, TypeVar

T = TypeVar("T")
NoTarget = object()


class DeveloperError(Exception):
    """
    An exception which indicates a developer error. This is used instead of assertions in testcases because if
    one were to check for AssertionErrors and an assertion is raised not because of a tested condition, but
    because the test-utils were used incorrectly, then there is no way to distinguish between those.

    Use only in testcases, use normal assertions for service code. you can still use assertions in
    setUp(), tearDown(), setUpClass(), tearDownClass() code, because nobody would catch assertions there
    """


def wait_for_value(getter: Callable[[], T | None], target: T | None = NoTarget, invert_target: bool = False,
                   timeout: float = 3, sleep_time: float = 0.01) -> T:
    """
    Waits until the getter returns the target value or the target value.
    If no target is specified, waits until the getter returns a value different from the first value it returned.
        WARNING: your code might be fast enough that the first value is already the 'changed' value, in that case
            this function will wait for the timeout. If you want to avoid this, specify a target.
    If invert_target is True, waits until the getter returns a value different from the target value.
    """
    start = current = getter()
    end_time = time.time() + timeout
    while (target is NoTarget and current == start) or (
            target is not NoTarget and (current == target) == invert_target):
        time.sleep(sleep_time)
        current = getter()
        if time.time() > end_time:
            raise TimeoutError(f"Timeout waiting for value {target}. Current value: {current}")
    return current
