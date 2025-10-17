from typing import Any, Dict, Tuple, Type, TypeVar

from PIL import ImageDraw

T = TypeVar("T", bound="BaseComponent")


class ComponentMeta(type):
    def __new__(
        mcs: Any, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> Type[T]:
        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and not attr_name.startswith("__"):
                attrs[attr_name] = mcs.chainable(attr_value)
        return super().__new__(mcs, name, bases, attrs)

    @staticmethod
    def chainable(func: Any) -> Any:
        def wrapper(self: T, *args: Any, **kwargs: Any) -> T:
            result = func(self, *args, **kwargs)
            return self if result is None else result

        return wrapper


class BaseComponent(metaclass=ComponentMeta):
    def __init__(self):
        self.pos = None
        self.proportion = None
        self.minheight = None
        self.minwidth = None
        self.group = None
        self.parent = None
        self.spacing = None
        self.poss = None
        self.draw = None
        self.align_self = None
        self.debug = None

    def set_pos(self: T, pos) -> T:
        self.pos = pos
        return self

    def set_proportion(self: T, prop) -> T:
        self.proportion = prop
        return self

    def set_minheight(self: T, minheight) -> T:
        self.minheight = minheight
        return self

    def set_minwidth(self: T, minwidth) -> T:
        self.minwidth = minwidth
        return self

    def set_parent(self: T, parent) -> T:
        self.parent = parent
        return self

    def position(self: T, align) -> T:
        """
        設置元素在容器中的位置
        align: "start"/"top"/"left" - 靠上/左對齊
               "center"/"middle" - 居中對齊
               "end"/"bottom"/"right" - 靠下/右對齊
               "stretch" - 拉伸填充（默認）
        """

        align_map = {
            "start": "start",
            "top": "start",
            "left": "start",
            "center": "center",
            "middle": "center",
            "end": "end",
            "bottom": "end",
            "right": "end",
            "stretch": "stretch",
        }
        self.align_self = align_map.get(align.lower(), "stretch")
        return self

    def get_spacing(self):
        if self.spacing is not None:
            return self.spacing
        elif self.parent:
            return self.parent.get_spacing()
        return None

    def get_poss(self):
        if self.poss is not None:
            return self.poss
        elif self.parent:
            return self.parent.get_poss()
        return None

    def get_draw(self) -> ImageDraw.ImageDraw:
        if self.draw is not None:
            return self.draw
        elif self.parent:
            return self.parent.get_draw()
        raise ValueError("No draw object found")

    def get_default_font(self):
        if self.parent:
            return self.parent.get_default_font()
        return None

    def get_debug(self) -> bool:
        """獲取 debug 模式狀態"""
        if self.debug is not None:
            return self.debug
        elif self.parent:
            return self.parent.get_debug()
        return False

    def render(self):
        self._render()

    def _render(self):
        raise NotImplementedError("Subclasses must implement _render method")
