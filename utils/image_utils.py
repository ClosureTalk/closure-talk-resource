from PIL import Image
import numpy as np


def scale_and_crop(img: Image, size: int) -> Image:
    w, h = img.width, img.height
    scale = size / min(w, h)
    img = img.resize((int(np.round(w*scale)), int(np.round(h*scale))), resample=Image.ANTIALIAS)

    w, h = img.width, img.height
    img = np.array(img)
    if w > h:
        cw = (w - h) // 2
        img = img[:, cw:cw+h]
    elif h > w:
        ch = (h - w) // 2
        img = img[ch:ch+w]

    return Image.fromarray(img)


def process_image(src: str, dst: str, size: int):
    img = Image.open(src)
    img = scale_and_crop(img, size)
    img.save(dst, quality=95, method=6)
