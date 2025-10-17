from enum import Enum


class LayoutType(Enum):
    PROPORTION = "proportion"
    FLEX = "flex"
    GRID = "grid"


class Direction(Enum):
    ROW = "row"
    COLUMN = "column"


class Align(Enum):
    """對齊方式枚舉"""

    START = "start"  # 開始位置（上/左）
    CENTER = "center"  # 中間位置
    END = "end"  # 結束位置（下/右）
    STRETCH = "stretch"  # 拉伸填充
