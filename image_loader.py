# image_loader.py
from typing import Tuple
from pathlib import Path
from PIL import Image, ImageOps
import pygame

def pil_to_surface(pil_img: Image.Image) -> pygame.Surface:
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes()
    size = pil_img.size
    return pygame.image.frombuffer(data, size, "RGBA").convert_alpha()

def load_image_as_surface(path: Path, fit_rect: Tuple[int, int]) -> pygame.Surface:
    """ウィンドウ内に収まるよう contain してSurface化"""
    img = Image.open(path).convert("RGBA")
    max_w, max_h = fit_rect
    img = ImageOps.contain(img, (max_w, max_h))
    return pil_to_surface(img)
