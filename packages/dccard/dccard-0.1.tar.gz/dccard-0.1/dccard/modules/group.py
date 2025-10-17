import logging

from ..Component import BaseComponent
from ..type import Direction

logger = logging.getLogger(__name__)


class Group(BaseComponent):
    def __init__(self, display=None, direction=Direction.ROW):
        super().__init__()
        self.background = None
        self.frame = None
        self.spacing = 1
        self.display = display
        self.direction = direction
        self.items = []

    def add(self, item):
        if isinstance(item, list):
            for i in item:
                i.set_parent(self)
                self.items.append(i)
        else:
            item.set_parent(self)
            self.items.append(item)
        return item

    def _render(self):
        logger.debug(
            f"Rendering group: direction={self.direction}, items={len(self.items)}"
        )
        if not self.items:
            logger.debug("No items to render")
            return
        poss = self.get_poss()
        if not poss:
            logger.debug("No position information")
            return
        group_width = poss[2] - poss[0]
        group_height = poss[3] - poss[1]
        if self.direction == Direction.ROW:
            self._render_row(group_width, group_height)
        elif self.direction == Direction.COLUMN:
            self._render_column(group_width, group_height)

        if self.get_debug():
            self._draw_debug_border()

    def _render_row(self, group_width, group_height):
        x = self.get_poss()[0]
        item_width = (group_width - (len(self.items) - 1) * self.get_spacing()) // len(
            self.items
        )
        for i, item in enumerate(self.items):
            base_y1 = self.get_poss()[1]
            base_y2 = self.get_poss()[3]

            if item.align_self and item.align_self != "stretch":
                if item.minheight:
                    actual_height = item.minheight
                    available_height = base_y2 - base_y1

                    if item.align_self == "start":  # 靠上
                        base_y2 = base_y1 + actual_height
                    elif item.align_self == "center":  # 居中
                        offset = (available_height - actual_height) // 2
                        base_y1 = base_y1 + offset
                        base_y2 = base_y1 + actual_height
                    elif item.align_self == "end":  # 靠下
                        base_y1 = base_y2 - actual_height

            item.poss = (
                int(x),
                int(base_y1),
                int(x + item_width),
                int(base_y2),
            )
            item.draw = self.get_draw()
            logger.debug(f"Rendering item {i} in row: {item.poss}")
            item.render()
            x += item_width + self.get_spacing()

    def _render_column(self, group_width, group_height):
        y = self.get_poss()[1]
        item_height = (
            group_height - (len(self.items) - 1) * self.get_spacing()
        ) // len(self.items)
        for i, item in enumerate(self.items):
            base_x1 = self.get_poss()[0]
            base_x2 = self.get_poss()[2]

            if item.align_self and item.align_self != "stretch":
                if item.minwidth:
                    actual_width = item.minwidth
                    available_width = base_x2 - base_x1

                    if item.align_self == "start":  # 靠左
                        base_x2 = base_x1 + actual_width
                    elif item.align_self == "center":  # 居中
                        offset = (available_width - actual_width) // 2
                        base_x1 = base_x1 + offset
                        base_x2 = base_x1 + actual_width
                    elif item.align_self == "end":  # 靠右
                        base_x1 = base_x2 - actual_width

            item.poss = (
                int(base_x1),
                int(y),
                int(base_x2),
                int(y + item_height),
            )
            item.draw = self.get_draw()
            logger.debug(f"Rendering item {i} in column: {item.poss}")
            item.render()
            y += item_height + self.get_spacing()

    def _draw_debug_border(self):
        """繪製 debug 邊界框"""
        draw = self.get_draw()
        if not draw:
            return

        poss = self.get_poss()
        if not poss:
            return

        if self.direction == Direction.ROW:
            color = (255, 0, 0)
            bg_color = (255, 200, 200)
            label = "ROW"
        else:
            color = (0, 0, 255)
            bg_color = (200, 200, 255)
            label = "COL"

        x1, y1, x2, y2 = poss
        draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=color, width=2)

        try:
            font = self.get_default_font()
            if font:
                bbox = font.getbbox(label)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                draw.rectangle(
                    [x1 + 2, y1 + 2, x1 + text_width + 8, y1 + text_height + 6],
                    fill=bg_color,
                )

                draw.text((x1 + 5, y1 + 4), label, fill=color, font=font)
        except Exception:
            pass
