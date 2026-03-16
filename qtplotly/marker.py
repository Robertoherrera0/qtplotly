from dataclasses import dataclass


@dataclass
class Marker:

    name: str
    x: float

    color: str = "black"
    width: int = 0.6

    persistent: bool = False