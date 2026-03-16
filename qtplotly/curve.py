from dataclasses import dataclass, field
import numpy as np


@dataclass
class Curve:

    name: str
    axis: str = "y1"

    x: np.ndarray = field(default_factory=lambda: np.empty(0))
    y: np.ndarray = field(default_factory=lambda: np.empty(0))

    visible: bool = True
    color: str | None = None

    def __post_init__(self):

        if self.axis not in ("y1", "y2"):
            raise ValueError("axis must be 'y1' or 'y2'")

    def append(self, x, y):

        x = np.atleast_1d(x)
        y = np.atleast_1d(y)

        if x.shape != y.shape:
            raise ValueError("x and y must have the same shape")

        self.x = np.concatenate((self.x, x))
        self.y = np.concatenate((self.y, y))

    def set_data(self, x, y):

        x = np.asarray(x)
        y = np.asarray(y)

        if x.shape != y.shape:
            raise ValueError("x and y must have the same shape")

        self.x = x
        self.y = y

    def clear(self):

        self.x = np.empty(0)
        self.y = np.empty(0)