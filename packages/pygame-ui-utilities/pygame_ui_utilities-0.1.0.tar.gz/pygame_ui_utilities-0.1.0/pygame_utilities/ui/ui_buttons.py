"""
Button classes for Pygame applications.

Provides Button and ImageButton classes with hover/press effects,
flexible anchoring, and automatic state management.
"""

import pygame as pg
from .text_drawing import draw_text
from typing import Optional, Literal

AnchorX = Literal["left", "center", "right"]
AnchorY = Literal["top", "center", "bottom"]
Colour = tuple[int, int, int]

WHITE: Colour = (255, 255, 255)
BLACK: Colour = (0, 0, 0)


class Button:
    def __init__(
        self,
        surface: pg.Surface,
        x: int,
        y: int,
        colour: Colour = BLACK,
        width: int = 50,
        height: int = 50,
        text: str = "",
        text_size: int = 20,
        text_font: str = "arial",
        text_colour: Colour = WHITE,
        anchor_x: AnchorX = "left",
        anchor_y: AnchorY = "top",
        border_radius: int = 0,
        is_clickable: bool = True,
    ) -> None:
        """
        Create a rectangular button with hover and press effects.

        Args:
            surface: Pygame surface to draw the button on
            x: X coordinate of the anchor point
            y: Y coordinate of the anchor point
            colour: Button background color as RGB tuple
            width: Button width in pixels
            height: Button height in pixels
            text: Text displayed on the button
            text_size: Font size for the button text
            text_colour: Text color as RGB tuple
            anchor_x: Horizontal reference point for positioning
            anchor_y: Vertical reference point for positioning
            border_radius: Corner radius for rounded corners (0 = square)
            is_clickable: flag to disable ability to click button

        Example:
            ### Button centered at (400, 300)
            button = Button(screen, 400, 300, anchor_x="center", anchor_y="center")

            ### Button with top-left at (100, 100)
            button = Button(screen, 100, 100, colour=(255, 0, 0), text="Click me")
        """
        if anchor_x == "center":
            x -= width // 2
        elif anchor_x == "right":
            x -= width

        if anchor_y == "center":
            y -= height // 2
        elif anchor_y == "bottom":
            y -= height

        self.surface = surface
        self.border_radius = border_radius
        self.text = text
        self.text_size = text_size
        self.text_font = text_font
        self.text_colour = text_colour
        self.normal_colour = colour
        self.hovered_colour = tuple(min(c + 75, 255) for c in self.normal_colour)
        self.pressed_colour = tuple(max(c - 75, 0) for c in self.normal_colour)
        self.rect = pg.Rect((x, y, width, height))
        self.is_hovered = False
        self.is_pressed = False
        self._is_clickable = is_clickable

    @property
    def is_clickable(self) -> bool:
        return self._is_clickable

    @is_clickable.setter
    def is_clickable(self, value: bool) -> None:
        self._is_clickable = value
        if not value:
            self.is_hovered = False
            self.is_pressed = False

    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update button state based on mouse position."""
        self.check_hover(mouse_pos)

    def check_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Check if mouse is hovering over the button."""
        if not self.is_clickable:
            return

        if self.rect.collidepoint(mouse_pos):
            self.is_hovered = True
        else:
            self.is_hovered = False

    def handle_event(self, event: pg.Event) -> bool:
        """
        Handle mouse events for the button.

        Returns:
            bool: True if button was clicked, False otherwise
        """
        if not self.is_clickable:
            return False

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return False
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                return True
            self.is_pressed = False
        return False

    def draw(self) -> None:
        """Draw the button on the surface."""
        if self.is_pressed:
            pg.draw.rect(
                self.surface,
                self.pressed_colour,
                self.rect,
                border_radius=self.border_radius,
            )
        elif self.is_hovered:
            pg.draw.rect(
                self.surface,
                self.hovered_colour,
                self.rect,
                border_radius=self.border_radius,
            )
        else:
            pg.draw.rect(
                self.surface,
                self.normal_colour,
                self.rect,
                border_radius=self.border_radius,
            )

        draw_text(
            self.surface,
            self.text,
            self.text_size,
            self.rect.centerx,
            self.rect.centery,
            font_name=self.text_font,
            colour=self.text_colour,
            align_x="center",
            align_y="center",
        )


class ImageButton:
    def __init__(
        self,
        surface: pg.Surface,
        x: int,
        y: int,
        normal_image: pg.Surface,
        hover_image: Optional[pg.Surface] = None,
        pressed_image: Optional[pg.Surface] = None,
        text: str = "",
        text_size: int = 20,
        text_font: str = "arial",
        text_colour: Colour = WHITE,
        border_radius: int = 0,
        anchor_x: AnchorX = "left",
        anchor_y: AnchorY = "top",
        is_clickable: bool = True,
    ) -> None:
        """
        Create a button using images instead of colored rectangles.

        Uses composition with the Button class for core functionality.

        Args:
            surface: Pygame surface to draw the button on
            x: X coordinate of the anchor point
            y: Y coordinate of the anchor point
            normal_image: Image to display when button is in normal state
            hover_image: Optional image for hover state (auto-generated if None)
            pressed_image: Optional image for pressed state (auto-generated if None)
            text: Text displayed on the button
            text_size: Font size for the button text
            text_colour: Text color as RGB tuple
            border_radius: Corner radius for rounded corners (0 = square)
            anchor_x: Horizontal reference point for positioning
            anchor_y: Vertical reference point for positioning
            is_clickable: flag to disable ability to click button

        Example:
            ### Basic image button
            button = ImageButton(screen, 100, 100, normal_image=play_icon)

            ### Image button with custom states and text
            button = ImageButton(
                screen, 200, 200,
                normal_image=normal_img,
                hover_image=hover_img,
                pressed_image=pressed_img,
                text="Play",
                anchor_x="center"
            )
        """
        self.button = Button(
            surface,
            x,
            y,
            width=normal_image.get_width(),
            height=normal_image.get_height(),
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            is_clickable=is_clickable,
        )
        self.normal_image = normal_image
        self.hover_image = hover_image
        self.pressed_image = pressed_image
        self.text = text
        self.text_size = text_size
        self.text_font = text_font
        self.text_colour = text_colour

    @property
    def is_clickable(self) -> bool:
        return self.button.is_clickable

    @is_clickable.setter
    def is_clickable(self, value: bool) -> None:
        self.button.is_clickable = value

    def update(self, mouse_pos) -> None:
        """Update button state based on mouse position."""
        return self.button.update(mouse_pos)

    def handle_event(self, event) -> bool:
        """
        Handle mouse events for the button.

        Returns:
            bool: True if button was clicked, False otherwise
        """
        return self.button.handle_event(event)

    def draw(self) -> None:
        """Draw the image button on the surface."""
        if self.button.is_pressed:
            image = self.pressed_image or self._tint_image(
                self.normal_image, (25, 25, 25)
            )
        elif self.button.is_hovered:
            image = self.hover_image or self._highlight_image(
                self.normal_image, (25, 25, 25)
            )
        else:
            image = self.normal_image

        self.button.surface.blit(image, self.button.rect)

        draw_text(
            self.button.surface,
            self.text,
            self.text_size,
            self.button.rect.centerx,
            self.button.rect.centery,
            font_name=self.text_font,
            colour=self.text_colour,
            align_x="center",
            align_y="center",
        )

    def _highlight_image(
        self, image: pg.Surface, tint_colour: tuple[int, ...]
    ) -> pg.Surface:
        """Create a highlighted version of the image for hover state."""
        tinted = image.copy()
        tinted.fill(tint_colour, special_flags=pg.BLEND_RGB_ADD)
        return tinted

    def _tint_image(
        self, image: pg.Surface, tint_colour: tuple[int, ...]
    ) -> pg.Surface:
        """Create a darkened version of the image for pressed state."""
        tinted = image.copy()
        tinted.fill(tint_colour, special_flags=pg.BLEND_RGB_SUB)
        return tinted
