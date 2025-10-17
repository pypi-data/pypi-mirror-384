import pygame as pg
from typing import Literal

AnchorX = Literal["left", "center", "right"]
AnchorY = Literal["top", "center", "bottom"]
Colour = tuple[int, int, int]


def draw_text(
    surf: pg.Surface,
    text: str,
    size: int,
    x: int,
    y: int,
    font_name: str = "arial",
    colour: Colour = (255, 255, 255),
    align_x: AnchorX = "center",
    align_y: AnchorY = "center",
) -> None:
    """
    Draw text on a Pygame surface with flexible alignment options.

    Args:
        surf: Pygame surface to draw on
        text: Text content to display
        size: Font size in pixels
        x: X coordinate for alignment point
        y: Y coordinate for alignment point
        font_name: Font family name (uses Pygame's font matching)
        colour: Text color as RGB tuple
        align_x: Horizontal alignment relative to x
        align_y: Vertical alignment relative to y

    Example:
        ### Draw text centered at (400, 300)
        draw_text(screen, "Hello World", 24, 400, 300)

        ### Draw text with top-left at (50, 50)
        draw_text(screen, "Score: 100", 18, 50, 50, align_x="left", align_y="top")
    """
    font_match = pg.font.match_font(font_name)
    font = pg.font.Font(font_match, size)
    text_surface = font.render(text, True, colour)
    text_rect = text_surface.get_rect()

    # Horizontal alignment
    if align_x == "left":
        text_rect.left = x
    elif align_x == "center":
        text_rect.centerx = x
    elif align_x == "right":
        text_rect.right = x

    # Vertical alignment
    if align_y == "top":
        text_rect.top = y
    elif align_y == "center":
        text_rect.centery = y
    elif align_y == "bottom":
        text_rect.bottom = y

    surf.blit(text_surface, text_rect)
