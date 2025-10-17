import logging

from PIL import Image as PilImage

from ..Component import BaseComponent

logger = logging.getLogger(__name__)


class Displaylist(BaseComponent):
    def __init__(self, image, images, size) -> None:
        super().__init__()
        self._image = image
        self._images = images
        self._size = size if type(size) is tuple else (size, size)

    def images(self, images: list[PilImage.Image | str]) -> "Displaylist":
        self._images = images
        return self

    def size(self, size: tuple[int, int]) -> "Displaylist":
        self._size = size
        return self

    def _render(self):
        x1, y1, x2, y2 = self.get_poss()
        logging.debug(f"x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}")

        count = len(self._images)
        logging.debug(f"count: {count}")

        width = x2 - x1
        height = y2 - y1
        logging.debug(f"width: {width}, height: {height}")

        row = min(count, int(width / self._size[0]))
        logging.debug(f"row: {row}")

        if row == 1:
            row_spacing = 0
        else:
            total_image_width = row * self._size[0]
            remaining_space = width - total_image_width
            row_spacing = remaining_space // (row - 1)
        logging.debug(f"row_spacing: {row_spacing}")

        col = (count + row - 1) // row
        if col == 1:
            col_spacing = 0
        else:
            total_image_height = col * self._size[1]
            remaining_space = height - total_image_height
            col_spacing = remaining_space // (col - 1)

        logging.debug(f"col: {col}, col_spacing: {col_spacing}")

        for i in range(count):
            if i >= row * col:
                break
            x = int(i % row)
            y = int(i / row)
            pos = (
                x1 + (x * (self._size[0] + row_spacing)),
                y1 + (y * (self._size[1] + col_spacing)),
            )
            logging.debug(f"i: {i}, x: {x}, y: {y}, pos: {pos}")
            self._image.paste(self._images[i].resize(self._size), pos)
