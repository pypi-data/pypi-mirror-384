from PIL import Image, ImageDraw


def zoom_magnification(image, prrp):
    return image.resize((int(image.width * prrp), int(image.height * prrp)))


def zoom_extent(image, where, extent):
    if extent <= 0:
        raise ValueError("extent must be greater than 0")
    if where == "height":
        mult = image.height / extent
        return (int(image.width / mult), int(extent))

    elif where == "width":
        mult = image.width / extent
        return (int(extent), int(image.height / mult))
