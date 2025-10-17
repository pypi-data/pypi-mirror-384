import io
import logging
from enum import Enum

import requests
from PIL import Image as PilImage

from ..Component import BaseComponent
from ..util.zoom import zoom_extent

logger = logging.getLogger(__name__)


class ShowMode(Enum):
    NORMAL = "normal"
    FILL = "fill"
    SHOWALL = "showall"
    SQUARE = "square"


class AUTO:
    pass


class Image(BaseComponent):
    def __init__(self, image, source, **kwargs):
        super().__init__()
        self._image = image
        if isinstance(source, str) and "http" in source:
            self.pastimage = PilImage.open(io.BytesIO(requests.get(source).content))
        elif PilImage.isImageType(source):
            self.pastimage = source
        else:
            self.pastimage = PilImage.open(source)

        self._size = kwargs.get("size", AUTO)
        self.showmod = (
            ShowMode(kwargs.get("showmod", "normal"))
            if isinstance(kwargs.get("showmod"), str)
            else kwargs.get("showmod")
        )
        self._mask = kwargs.get("mask")

        if self._mask is not None and self.showmod != ShowMode.SQUARE:
            raise Exception("mask can only be used in square mode")

    def showmode(self, showmod: str) -> "Image":
        self.showmod = ShowMode(showmod)
        return self

    def size(self, size: tuple[int, int]) -> "Image":
        self._size = size
        return self

    def mask(self, mask: PilImage.Image, size: int) -> "Image":
        if self.showmod != ShowMode.SQUARE:
            raise Exception("mask can only be used in square mode")
        self._mask = mask
        return self

    def _render(self):
        draw = self.get_draw()
        if not draw:
            logger.warning("No draw object available for image rendering")
            return

        poss = self.get_poss()
        if not poss:
            logger.warning("No position information for image rendering")
            return

        x1, y1, x2, y2 = poss
        mainpos = poss

        if self._size == AUTO:
            if self.showmod == ShowMode.NORMAL:
                if self.pastimage.width > self.pastimage.height and (x2 - x1) > (
                    y2 - y1
                ):
                    self._size = zoom_extent(self.pastimage, "width", x2 - x1)
                    if self._size[1] > y2 - y1:
                        self.pastimage = self.pastimage.resize(self._size)
                        self.pastimage = self.pastimage.crop(
                            (
                                0,
                                0,
                                self.pastimage.width,
                                self.pastimage.height
                                - (self.pastimage.height - (y2 - y1)),
                            )
                        )
                        self._size = self.pastimage.size
                else:
                    self._size = zoom_extent(self.pastimage, "height", y2 - y1)
                    if self._size[0] > x2 - x1:
                        self.pastimage = self.pastimage.resize(self._size)
                        self.pastimage = self.pastimage.crop(
                            (
                                0,
                                0,
                                self.pastimage.width
                                - (self.pastimage.width - (x2 - x1)),
                                self.pastimage.height,
                            )
                        )
                        self._size = self.pastimage.size
            elif self.showmod == ShowMode.FILL:
                self._size = (x2 - x1, y2 - y1)
            elif self.showmod == ShowMode.SHOWALL:
                if self.pastimage.width / self.pastimage.height > (x2 - x1) / (y2 - y1):
                    self._size = zoom_extent(self.pastimage, "width", x2 - x1)
                else:
                    self._size = zoom_extent(self.pastimage, "height", y2 - y1)
            elif self.showmod == ShowMode.SQUARE:
                if self.pastimage.width > self.pastimage.height:
                    self._size = (y2 - y1, y2 - y1)
                else:
                    self._size = (x2 - x1, x2 - x1)

        print(self._size)
        resized_image = self.pastimage.resize(self._size)

        self._image.paste(
            resized_image,
            (mainpos[0], mainpos[1]),
            mask=self._mask(self._size[0]) if self._mask else None,
        )

        if self.get_debug():
            draw = self.get_draw()
            if draw:
                x1, y1, x2, y2 = poss
                draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=(255, 200, 0), width=1)
