import sys

sys.path.append("../dccard")
from PIL import Image

from dccard.canvas import Canvas
from dccard.type import Direction

canvas = Canvas((500, 500))

row_group = canvas.group(Direction.ROW)
canvas.add_component(row_group)  # 將行組添加到根組
row_group.add(canvas.text("Text 1").color("red"))
row_group.add(canvas.text("Text 2").color("red"))
row_group.add(canvas.text("Text 3").color("red"))

col_group = canvas.group(Direction.COLUMN)
canvas.add_component(col_group)  # 將列組添加到根組
col_group.add(canvas.text("Text 3").set_minheight(50).color("red"))
col_group.add(canvas.text("Text 4").set_minheight(50).color("red"))
col_group.add(canvas.text("Text 5").set_minheight(50).color("red"))
col_group.add(canvas.text("Text 6").set_minheight(50).color("red"))

canvas.text("Text tese").color("red").font("arial.ttf").set_minheight(50)

image1 = Image.open(
    "C:\\Users\\whitecloud\\Pictures\\VRChat\\2024-08\\VRChat_2024-08-01_21-39-43.124_1920x1080.png"
)
image2 = Image.open(
    "C:\\Users\\whitecloud\\Pictures\\VRChat\\2024-08\\VRChat_2024-08-01_21-39-48.289_1920x1080.png"
)
canvas.add_component(canvas.text("Text 7").set_minheight(200).color("red"))
canvas.add_component(
    canvas.displaylist(
        [image1, image2, image1, image1, image1, image1, image1], (40, 40)
    )
)
result_image = canvas.render()
result_image.show()
