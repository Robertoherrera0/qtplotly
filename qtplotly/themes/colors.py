# qtplotly/styles/colors.py
from __future__ import annotations
import itertools

_LIGHT_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#9467bd",
    "#8c564b",
]

_DARK_COLORS = [
    "#4cc9f0",
    "#7209b7",
    "#4361ee",
    "#34d399",
    "#10b981",
]


class ColorTable:

    def __init__(self, theme="light"):

        if theme == "dark":
            palette = _DARK_COLORS
        else:
            palette = _LIGHT_COLORS

        self.palette = palette
        self._cycler = itertools.cycle(palette)
        self.table = {}

    def get(self, name: str) -> str:

        if name in self.table:
            return self.table[name]

        col = next(self._cycler)
        self.table[name] = col
        return col

    def set(self, name: str, color: str):
        self.table[name] = color

    def reset(self):
        self.table = {}