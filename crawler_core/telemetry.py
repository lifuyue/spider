class Telemetry:
    def __init__(self) -> None:
        self.success = 0
        self.errors = 0
        self.emitted = 0

    def mark_success(self) -> None:
        self.success += 1

    def mark_error(self, _err: Exception) -> None:  # pragma: no cover - trivial
        self.errors += 1

    def mark_emit(self) -> None:
        self.emitted += 1

