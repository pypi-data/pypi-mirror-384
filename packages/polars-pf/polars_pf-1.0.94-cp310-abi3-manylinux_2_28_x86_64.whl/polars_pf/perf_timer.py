import time


class PerfTimer:
    """A performance timer that provides elapsed time with human-readable formatting.

    Reference: https://github.com/milaboratory/platforma/blob/9b497ed833c523d13f9be9edeb950e2eac9278a8/lib/util/helpers/src/perfTimer.ts

    Examples:
        >>> timer = PerfTimer.start()
        >>> # ... do some work ...
        >>> elapsed = timer.elapsed()
        >>> print(f"Operation took {elapsed}")
    """

    def __init__(self, start_time: int) -> None:
        """Initialize timer with start time. Use PerfTimer.start() instead."""
        self._start_time = start_time

    @classmethod
    def start(cls) -> "PerfTimer":
        """Start a new performance timer."""
        return cls(time.perf_counter_ns())

    def elapsed(self) -> str:
        """Get the elapsed time since the timer was started."""
        ms = (time.perf_counter_ns() - self._start_time) // int(1e6)

        units = [
            (ms // (24 * 60 * 60 * 1000), "d"),  # days
            ((ms // (60 * 60 * 1000)) % 24, "h"),  # hours
            ((ms // (60 * 1000)) % 60, "m"),  # minutes
            ((ms // 1000) % 60, "s"),  # seconds
            (ms % 1000, "ms"),  # milliseconds
        ]

        # Find the first non-zero unit
        first_non_zero = next(
            (i for i, (value, _) in enumerate(units) if value > 0), None
        )

        if first_non_zero is None:
            return "0ms"

        parts = [f"{units[first_non_zero][0]}{units[first_non_zero][1]}"]

        # Add the next unit if it exists and is non-zero
        if first_non_zero + 1 < len(units) and units[first_non_zero + 1][0] > 0:
            parts.append(
                f"{units[first_non_zero + 1][0]}{units[first_non_zero + 1][1]}"
            )

        return " ".join(parts)
