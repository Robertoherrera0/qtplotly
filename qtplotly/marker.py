from dataclasses import dataclass, field


@dataclass
class Marker:
    name: str
    x: float

    label: str | None = None

    color: str | None = None
    width: float = 1.0

    # where the line starts and ends (paper coords 0-1)
    y0: float = 0.0
    y1: float = 1.0

    # where the label sits (paper coords 0-1)
    label_y: float = 0.97

    visible: bool = True
    persistent: bool = False

    def __post_init__(self):
        if self.label is None:
            self.label = self.name
        if not isinstance(self.x, (int, float)):
            raise ValueError("Marker x must be numeric")

    def set_x(self, x: float):
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
            "name":    self.name,
            "label":   self.label,
            "x":       self.x,
            "color":   self.color,
            "width":   self.width,
            "y0":      self.y0,
            "y1":      self.y1,
            "label_y": self.label_y,
            "visible": self.visible,
        }