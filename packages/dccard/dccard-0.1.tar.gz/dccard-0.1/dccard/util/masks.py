import os

from PIL import Image

path = os.path.dirname(os.path.abspath(__file__))


def circle_mask(size):
    tpath = path.replace("util", "assets")
    mask = Image.open(os.path.join(tpath, "circle.ppm"))
    mask = mask.convert("L")
    mask = mask.resize((size, size))
    return mask
