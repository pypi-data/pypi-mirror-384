import re
from datetime import timedelta
from functools import cached_property
from typing import TypedDict, cast

from statsd import StatsClient
from statsd.client.base import Timer
from typing_extensions import Self

__all__ = ["Instrument"]


class DefaultRate(TypedDict, total=False):
    """Used to specify default rates for sampling stat emission."""

    counter: float
    gauge: float
    timer: float


class InstrumentMeta(type):
    def __getattr__(cls, node: str) -> "Instrument":
        return Instrument([node])


Milliseconds = int


class Instrument(metaclass=InstrumentMeta):
    """An observability instrument for collecting statsd metrics.

    Usage:
    ```python
    class ObserveMe:
        def do_something(self) -> None:
            # Increments the "ics.do_something" stat by 1
            Instrument.ics.do_something.incr(1)

        def set_value(self, value: int) -> None:
            # Sets the gauge's current value
            Instrument.ics.value.gauge(1)

        # Captures the amount of time this method takes
        @Instrument.ics.sync.timer()
        def sync(self) -> None:
            requests.get("example.com/endpoint")

    ```
    """

    _STATS_CLIENT = StatsClient()

    def __init__(
        self,
        nodes: list[str],
        default_rates: DefaultRate | None = None,
    ) -> None:
        self._nodes = nodes
        self._default_rates: DefaultRate = default_rates or {}

    def __getattr__(self, node: str) -> "Instrument":
        """Allows dot-chaining instrument nodes to build an instrument."""
        return Instrument(
            nodes=self._nodes + [node],
            default_rates=self._default_rates,
        )

    def with_default_rate(
        self,
        counter: float | None = None,
        gauge: float | None = None,
        timer: float | None = None,
    ) -> Self:
        """Override the default rates used for this instrument on different data types."""
        if counter is not None:
            self._default_rates["counter"] = counter

        if gauge is not None:
            self._default_rates["gauge"] = gauge

        if timer is not None:
            self._default_rates["timer"] = timer

        return self

    def node(self, node: str) -> "Instrument":
        """A special method to dot-chain an instrument node which is not
        known before runtime. This must be a non-empty string, otherwise
        it will be replaced with an underscore. Any uppercase characters
        will be lowered.

        NOTE: Only the `a-z0-9_` characters are allowed; all others
            will be substituted with underscores.

        Example:
        ```python
        def get_connector(connector_id: str) -> Connector | None:
            instrument = Instrument.integrations.connectors.node(connector_id).fetch
            try:
                # get the connector
                connector = ...
            except Exception:
                instrument.failure.incr()
                return None

            instrument.success.incr()
            return connector
        ```
        """
        return Instrument(
            nodes=self._nodes + [node],
            default_rates=self._default_rates,
        )

    @property
    def _stat_key(self) -> str:
        return ".".join(self._sanitize(node) for node in self._nodes)

    @cached_property
    def _counter_rate(self) -> float:
        return self._default_rates.get("counter", 1.0)

    @cached_property
    def _gauge_rate(self) -> float:
        return self._default_rates.get("gauge", 1.0)

    @cached_property
    def _timer_rate(self) -> float:
        return self._default_rates.get("timer", 1.0)

    @staticmethod
    def _sanitize(node: str) -> str:
        """Sanitizes a node to a format allowed by statsd."""
        if not node:
            return "_"

        return re.sub(r"[^a-z0-9_]", "_", node.lower())

    def incr(self, count: int = 1, rate: float | None = None) -> None:
        """Increment a stat by `count`."""
        rate = cast(int, rate if rate is not None else self._counter_rate)
        self._STATS_CLIENT.incr(self._stat_key, count=count, rate=rate)

    def decr(self, count: int = 1, rate: float | None = None) -> None:
        """Decrement a stat by `count`."""
        rate = cast(int, rate if rate is not None else self._counter_rate)
        self._STATS_CLIENT.decr(self._stat_key, count=count, rate=rate)

    def gauge(self, value: int, rate: float | None = None, delta: bool = False) -> None:
        """Set a gauge value."""
        rate = cast(int, rate if rate is not None else self._gauge_rate)
        self._STATS_CLIENT.gauge(self._stat_key, value=value, rate=rate, delta=delta)

    def timing(self, delta: Milliseconds | timedelta, rate: float | None = None) -> None:
        """Capture the amount of time some action takes.

        Args:
            delta: The amount of time in ms or `timedelta` the action took.
            rate: The rate at which this stat should be recorded.
        """
        rate = cast(int, rate if rate is not None else self._timer_rate)
        self._STATS_CLIENT.timing(self._stat_key, delta=delta, rate=rate)

    def timer(self, rate: float | None = None) -> Timer:
        """A thread-safe decorator or context manager which reports the
        amount of time some inner action takes.

        Args:
            rate: The rate at which to sample the data.
        """
        rate = cast(int, rate if rate is not None else self._timer_rate)
        return self._STATS_CLIENT.timer(self._stat_key, rate=rate)
