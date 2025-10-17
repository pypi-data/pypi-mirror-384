import io
import logging
from typing import Tuple, Union

from PIL import Image as Pilimage
from PIL import ImageDraw, ImageFont

from .modules import Displaylist, Group, Image, Levelline, Text
from .type import Direction, LayoutType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Canvas:
    def __init__(
        self,
        size: Tuple[int, int] = (100, 100),
        display: Union[LayoutType, None] = None,
        default_font: Union[
            ImageFont.FreeTypeFont, ImageFont.ImageFont, str, None
        ] = None,
        default_font_size: int = 20,
        debug: bool = False,
    ):
        self._size: Tuple[int, int] = size
        self._image: Pilimage.Image = Pilimage.new("RGBA", size)
        self._draw: ImageDraw.ImageDraw = ImageDraw.Draw(self._image)
        self._spacing: int = 2
        self._display: Union[LayoutType, None] = display
        self._debug: bool = debug

        if default_font is None:
            try:
                self._default_font = ImageFont.truetype(
                    "C:/Windows/Fonts/msjh.ttc", default_font_size
                )
                logger.debug("Loaded Microsoft JhengHei font")
            except Exception:
                try:
                    self._default_font = ImageFont.truetype(
                        "C:/Windows/Fonts/msyh.ttc", default_font_size
                    )
                    logger.debug("Loaded Microsoft YaHei font")
                except Exception:
                    try:
                        self._default_font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                            default_font_size,
                        )
                    except Exception:
                        logger.warning("No Chinese font found, using default font")
                        self._default_font = ImageFont.load_default()
        elif isinstance(default_font, str):
            self._default_font = ImageFont.truetype(default_font, default_font_size)
        else:
            self._default_font = default_font

        self.root_group: Group = Group(display=display, direction=Direction.COLUMN)
        self.root_group.set_parent(self)
        self.root_group.spacing = self._spacing
        self.root_group.poss = (0, 0, self._size[0], self._size[1])
        self.root_group.draw = self._draw
        self.root_group.debug = self._debug

    def add_component(
        self, component: Union[Text, Image, Group, Levelline, Displaylist]
    ):
        return self.root_group.add(component)

    def render(self) -> Pilimage.Image:
        logger.debug("Starting canvas render")
        self.root_group.render()
        logger.debug("Finished canvas render")
        return self._image

    def group(self, direction: Direction = Direction.ROW) -> Group:
        return Group(direction=direction)

    def text(self, content: str) -> Text:
        return Text(content)

    def image(self, image: Union[Pilimage.Image, io.BytesIO, str]) -> Image:
        return Image(self._image, image)

    def levelline(self, nowlevel: int, nextlevel: int, linestyle: str) -> Levelline:
        return Levelline(nowlevel, nextlevel, linestyle)

    def displaylist(
        self, images: list[Pilimage.Image | str], size: tuple[int, int]
    ) -> Displaylist:
        return Displaylist(self._image, images, size)

    def get_spacing(self) -> int:
        return self._spacing

    def get_poss(self) -> Tuple[int, int, int, int]:
        return (0, 0, self._size[0], self._size[1])

    def get_draw(self) -> ImageDraw.ImageDraw:
        return self._draw

    def get_debug(self) -> bool:
        return self._debug

    def get_default_font(self) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
        return self._default_font
