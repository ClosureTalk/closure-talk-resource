from typing import Any

import numpy as np
from PIL import Image


def scale_and_crop(img: Image, size: int, config: dict[str, Any]) -> Image:
    w, h = img.width, img.height
    scale = size / min(w, h)
    img = img.resize((int(np.round(w*scale)), int(np.round(h*scale))), resample=Image.ANTIALIAS)

    w, h = img.width, img.height
    img = np.array(img)
    if w > h:
        cw = (w - h) // 2
        img = img[:, cw:cw+h]
    elif h > w:
        h_crop = config.get("h_crop", "center")
        if h_crop == "top":
            ch = 0
        elif h_crop == "bottom":
            ch = h-w
        else:
            ch = (h - w) // 2
        img = img[ch:ch+w]

    return Image.fromarray(img)


def process_image(src: str, dst: str, size: int, config: dict[str, Any]):
    img = Image.open(src)
    img = scale_and_crop(img, size, config)
    img.save(dst, quality=95, method=6)
