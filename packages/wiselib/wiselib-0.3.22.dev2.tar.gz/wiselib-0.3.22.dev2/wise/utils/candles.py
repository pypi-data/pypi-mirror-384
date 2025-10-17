import math
from datetime import timedelta, datetime

from django.db import models
from django.utils.timezone import make_aware
from pydantic import BaseModel


class Resolution(models.TextChoices):
    R1M = "1m", "1m"
    R3M = "3m", "3m"
    R5M = "5m", "5m"
    R15M = "15m", "15m"
    R30M = "30m", "30m"
    R1H = "1h", "1h"
    R4H = "4h", "4h"

    def get_timedelta(self) -> timedelta:
        match self:
            case Resolution.R1M:
                return timedelta(minutes=1)
            case Resolution.R3M:
                return timedelta(minutes=3)
            case Resolution.R5M:
                return timedelta(minutes=5)
            case Resolution.R15M:
                return timedelta(minutes=15)
            case Resolution.R30M:
                return timedelta(minutes=30)
            case Resolution.R1H:
                return timedelta(hours=1)
            case Resolution.R4H:
                return timedelta(hours=4)
            case _:
                raise ValueError


class Candle(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0
    close_time: datetime = datetime.min

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.close_time = self.time

    def __add__(self, other):
        if not isinstance(other, Candle):
            return NotImplemented

        if self.time > other.time:
            return other + self

        if self.time == other.time or other.high == -math.inf or other.low == math.inf:
            return self.copy()

        return Candle(
            time=min(self.time, other.time),
            open=self.open,
            high=max(self.high, other.high),
            low=min(self.low, other.low),
            close=other.close,
            volume=self.volume + other.volume,
            close_time=max(self.close_time, other.close_time),
        )

    def __mul__(self, other):
        if not isinstance(other, Candle):
            return NotImplemented

        return Candle(
            time=self.time,
            close_time=self.close_time,
            volume=self.volume,
            open=self.open * other.open,
            high=self.high * other.high,
            low=self.low * other.low,
            close=self.close * other.close,
        )


ZERO_CANDLE = Candle(
    time=make_aware(datetime.max),
    open=0,
    high=-math.inf,
    low=math.inf,
    close=0,
    volume=0,
    close_time=make_aware(datetime.min),
)


def sum_candles(candles: list[Candle]) -> Candle:
    return sum(candles, start=ZERO_CANDLE)
