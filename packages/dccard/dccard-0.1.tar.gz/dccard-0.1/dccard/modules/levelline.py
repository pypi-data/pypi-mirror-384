from ..Component import BaseComponent


class Levelline(BaseComponent):
    def __init__(self, nowlevel, nextlevel, linestyle):
        super().__init__()
        self.minheight = 50 if self.minheight == None else self.minheight
        self._nextlevel = nextlevel
        self._nowlevel = nowlevel
        self._color = "red"
        self._bg_color = "black"
        self.linestype = linestyle if linestyle != None else "rectangle"

    def nextlevel(self, nextlevel: float) -> "Levelline":
        self._nextlevel = nextlevel
        return self

    def nowlevel(self, nowlevel: float) -> "Levelline":
        self._nowlevel = nowlevel
        return self

    def style(self, linestyle: str) -> "Levelline":
        self.linestype = linestyle
        return self

    def color(self, color: str) -> "Levelline":
        self._color = color
        return self

    def bg_color(self, bg_color: str) -> "Levelline":
        self._bg_color = bg_color
        return self

    def _render(self):
        x1, y1, x2, y2 = self.get_poss()
        next = self._nextlevel / (x2 - x1)
        level = round(self._nowlevel / next)
        draw = self.get_draw()
        if self.linestype == "rectangle":
            # 等級底色
            draw.rectangle((x1, y1, x2, y2), fill=self._bg_color)
            if level <= x2:
                draw.rectangle((x1, y1, level + x1, y2), fill=self._color)
            else:
                draw.rectangle((x1, y1, level, y2), fill=self._color)
        elif self.linestype == "oval":
            draw.rounded_rectangle((x1, y1, x2, y2), fill=self._bg_color, radius=10)
            if level <= x2:
                draw.rounded_rectangle(
                    (x1, y1, level + x1, y2), fill=self._color, radius=10
                )
            else:
                draw.rounded_rectangle((x1, y1, level, y2), fill=self._color, radius=10)
