import logging
from typing import Any, Callable

from PIL import ImageFont

from ..Component import BaseComponent

logger = logging.getLogger(__name__)


class Text(BaseComponent):
    def __init__(self, content, **kwargs):
        super().__init__()
        self.content = content
        self.textsize = kwargs.get("size", (50, 50))
        self._font = kwargs.get("font", None)
        self._color = kwargs.get("fill", "#000")
        self.xalign = kwargs.get("xalign", "left")
        self.yalign = kwargs.get("yalign", "top")

    def font(self, font):
        self._font = font
        return self

    def get_font(self):
        """獲取當前使用的字體，如果未設定則使用預設字體"""
        if self._font is not None:
            return self._font
        default_font = self.get_default_font()
        if default_font is not None:
            return default_font
        return ImageFont.load_default()

    def color(self, color):
        self._color = color
        return self

    def size(self, size):
        self.textsize = size
        return self

    def align(self, xalign=None, yalign=None):
        if xalign:
            self.xalign = xalign
        if yalign:
            self.yalign = yalign
        return self

    def _render(self):
        logger.debug(f"Rendering text: {self.content}")

        draw = self.get_draw()
        if not draw:
            logger.warning("No draw object available for text rendering")
            return

        poss = self.get_poss()
        if not poss:
            logger.warning("No position information for text rendering")
            return

        x, y, right, bottom = poss
        width = right - x
        height = bottom - y

        current_font = self.get_font()
        left, top, right, bottom = current_font.getbbox(self.content)
        text_width = right - left
        text_height = bottom - top

        if self.xalign == "left":
            pos_x = x
        elif self.xalign == "center":
            pos_x = x + (width - text_width) / 2
        elif self.xalign == "right":
            pos_x = right - text_width

        if self.yalign == "top":
            pos_y = y
        elif self.yalign == "center":
            pos_y = y + (height - text_height) / 2
        elif self.yalign == "bottom":
            pos_y = bottom - text_height

        draw.text((pos_x, pos_y), self.content, font=current_font, fill=self._color)

        logger.debug(f"Text rendered at position: ({pos_x}, {pos_y})")

        if self.get_debug():
            poss = self.get_poss()
            x1, y1, x2, y2 = poss
            draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=(0, 200, 0), width=1)
