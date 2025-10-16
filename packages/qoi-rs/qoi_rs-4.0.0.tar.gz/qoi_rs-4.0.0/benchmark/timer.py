from time import perf_counter_ns
from typing import Self

class Timer:
    __slots__ = ("name", "_execution_time", "_start_time", "count")
    name: str
    count: int
    _execution_time: int


    def __init__(self, name: str) -> None:
        self.name = name
        self._execution_time = 0
        self.count = 0

    def get_ms(self) -> float:
        return self.get_ns() / 1_000_000

    def get_ns(self) -> int:
        assert not hasattr(self, "_start_time"), "Timer not stopped yet"
        return self._execution_time

    def __enter__(self) -> Self:
        assert not hasattr(self, "_start_time"), "Timer not stopped yet"
        self._start_time = perf_counter_ns()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._execution_time += perf_counter_ns() - self._start_time
        del self._start_time
        self.count += 1

    def __str__(self) -> str:
        return f"{self.name}: {self.get_ms() / self.count:.4} ms"
