from dataclasses import dataclass


@dataclass
class Marker:
    name: str
    x: float

    label: str | None = None   # display label

    color: str | None = None
    width: float = 1.0

    visible: bool = True
    persistent: bool = False

    def __post_init__(self):
        if self.label is None:
            self.label = self.name

        if not isinstance(self.x, (int, float)):
            raise ValueError("Marker x must be numeric")

    def set_x(self, x: float):

        if not isinstance(x, (int, float)):
            raise ValueError("Marker x must be numeric")

        self.x = float(x)

    def set_label(self, label: str):

        self.label = label

    def set_color(self, color: str | None):

        self.color = color

    def set_width(self, width: float):

        if width <= 0:
            raise ValueError("Marker width must be positive")

        self.width = float(width)

    def set_visible(self, visible: bool):

        self.visible = bool(visible)


    def as_dict(self):
        return {
            "name": self.name,
            "label": self.label,
            "x": self.x,
            "color": self.color,
            "width": self.width,
            "visible": self.visible,
        }