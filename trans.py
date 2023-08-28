from PIL import Image
import numpy as np


def transp_over_back(
        base_image,
        transparent_image,
        resize=(100, 100),
        pos=(None, 50)
    ):
    transparent_image_rgba = transparent_image.convert("RGBA")
    transparent_image_rgba = transparent_image_rgba.resize(resize)
    new_pos = list(pos)
    if pos[0] == None:
        new_pos[0] = (base_image.width - transparent_image_rgba.width) // 2

    base_image.paste(transparent_image_rgba, new_pos, transparent_image_rgba)

def white_to_transparency_gradient(img):
    x = np.asarray(img.convert('RGBA')).copy()
    x[:, :, 3] = (255 - x[:, :, :3].mean(axis=2)).astype(np.uint8)
    return Image.fromarray(x)


def white_to_transparency(img):
    x = np.asarray(img.convert('RGBA')).copy()
    x[:, :, 3] = (255 * (x[:, :, :3] != 255).any(axis=2)).astype(np.uint8)
    return Image.fromarray(x)
