from tenacity import retry, stop_after_attempt, wait_exponential


def retryable(max_attempts: int = 3):  # pragma: no cover - not used in tests
    return retry(stop=stop_after_attempt(max_attempts), wait=wait_exponential())

