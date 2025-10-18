import random
import time
from typing import Literal

import httpx
from gwproto.messages import EventBase


class SomeData(EventBase):
    TimestampUTC: float
    Reading: float
    TypeName: Literal["gridworks.event.some.data"] = "gridworks.event.some.data"


if __name__ == "__main__":
    httpx.post(
        "http://127.0.0.1:8080/events",
        json=SomeData(
            TimestampUTC=round(time.time(), 3),
            Reading=round(random.random(), 3),
        ).model_dump(),
    )
