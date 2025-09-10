class RateLimiter:
    def __init__(self, qps: float = 1.0):
        self.qps = qps

    def acquire(self):  # pragma: no cover - not used in tests
        pass

