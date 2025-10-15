
import pygame
from .objects import TextOverlay
from .helper import Color, EngineError, rotate, vector2d, Camera, Script, UIElement


class Box(UIElement):
    def __init__(self, pos=None, size=None, fill: Color = Color.grey, outline: Color = Color.light_red, name: str = "Box", visible: bool = True, corner_radius = 5, border_width = 4):
        super().__init__(name, size)
        self.name = name
        if pos is None:
            pos = vector2d.zero
        if size is None:
            size = vector2d(40, 40)

        self.pos = pos
        self.size = size
        self.fill = fill
        self.outline = outline
        self.visible = visible
        self.corner_radius = corner_radius
        self.border_width = border_width

    def draw(self, screen, camera: Camera, mouse_down_pos, mouse_pos):
        screen_size = vector2d(*screen.get_size())
        self.update_internal(mouse_down_pos, mouse_pos)
        if not self.visible:
            return

        half_size = self.size / 2

        pos = (self.pos - half_size + screen_size / 2).totuple()
        rect = pygame.Rect(pos, self.size.totuple())

        pygame.draw.rect(screen, self.fill.to_rgb(), rect, border_radius=self.corner_radius)
        pygame.draw.rect(screen, self.outline.to_rgb(), rect, border_radius=self.corner_radius, width=self.border_width)


class Button(UIElement):
    def __init__(self, pos=None, size=None, fill: Color = Color.grey, outline: Color = Color.light_red, name: str = "Button", visible: bool = True, corner_radius = 5, border_width = 4, text="Button", font_size=18, font_color=Color.white, font_family="Arial", text_rotation=0, bold=False, italic=False, antialias=True):
        super().__init__(name, size)
        self.name = name
        if pos is None:
            pos = vector2d.zero
        if size is None:
            size = vector2d(40, 40)
        self.pos = pos
        self.size = size
        self.fill = fill
        self.outline = outline
        self.visible = visible
        self.corner_radius = corner_radius
        self.border_width = border_width
        self.text = text
        self.font_size = font_size
        self.font_color = font_color
        self.font_family = font_family
        self.text_rotation = text_rotation
        self.bold = bold
        self.italic = italic
        self.antialias = antialias

        self.text_overlay = TextOverlay(text=text, pos=pos, color=font_color, font_size=font_size, visible=visible, font_family=font_family, rotation=text_rotation, bold=bold, italic=italic, antialiasing=antialias)

    def draw(self, screen, camera: Camera, mouse_down_pos, mouse_pos):
        screen_size = vector2d(*screen.get_size())
        self.update_internal(mouse_down_pos, mouse_pos)
        if not self.visible:
            return

        half_size = self.size / 2

        pos = (self.pos - half_size + screen_size / 2).totuple()
        rect = pygame.Rect(pos, self.size.totuple())

        pygame.draw.rect(screen, self.fill.to_rgb(), rect, border_radius=self.corner_radius)
        pygame.draw.rect(screen, self.outline.to_rgb(), rect, border_radius=self.corner_radius, width=self.border_width)

        self.text_overlay.text = self.text
        self.text_overlay.color = self.font_color
        self.text_overlay.font_size = self.font_size
        self.text_overlay.visible = self.visible
        self.text_overlay.font_family = self.font_family
        self.text_overlay.text_rotation = self.text_rotation
        self.text_overlay.bold = self.bold
        self.text_overlay.italic = self.italic
        self.text_overlay.antialias = self.antialias

        self.text_overlay.draw(screen, camera)


class Circle(UIElement):
    def __init__(self, pos=None, radius=None, fill: Color = Color.grey, outline: Color = Color.light_red, name: str = "Circle", visible: bool = True, outline_width: int = 10):
        super().__init__(name, pos)
        if pos is None:
            pos = vector2d.zero

        if radius is None:
            radius = 30

        self.name = name
        self.pos = pos
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.visible = visible
        self.outline_width = outline_width

    def is_inside(self, pos):
        return (pos.x - self.pos.x) ** 2 + (pos.y - self.pos.y) ** 2 <= self.radius ** 2

    def draw(self, screen, camera: Camera, mouse_down_pos, mouse_pos):
        screen_size = vector2d(*screen.get_size())
        self.update_internal(mouse_down_pos, mouse_pos)
        if not self.visible:
            return

        pos = (self.pos + screen_size / 2).totuple()

        pygame.draw.circle(screen, self.fill.to_rgb(), pos, self.radius)
        pygame.draw.circle(screen, self.outline.to_rgb(), pos, self.radius, width=self.outline_width)


# ---------------------------
# Functional Slider (centered)
# ---------------------------
class Slider(UIElement):
    def __init__(self, pos=None, size=None, fill: Color = Color.grey, slider_color: Color = Color.light_red, name: str = "Slider", visible: bool = True, corner_radius: int = 5, slider_radius=10, min_value=0, max_value=1, start_value=0.5):
        super().__init__(name, size)
        if size is None:
            size = vector2d(100, 10)
        if pos is None:
            pos = vector2d.zero

        self.size = size
        self.pos = pos
        self.slider_color = slider_color
        self.fill = fill
        self.name = name
        self.visible = visible
        self.corner_radius = corner_radius
        self.slider_radius = slider_radius

        # Value range
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(self.min_value, min(start_value, self.max_value))
        self.dragging = False

        # Internal UI parts
        self.box_obj = Box(pos=self.pos, size=self.size, fill=self.fill, outline=self.fill, name=name, visible=self.visible, corner_radius=self.corner_radius)
        self.circle_obj = Circle(pos=self._get_slider_pos(), radius=slider_radius, fill=self.slider_color, outline=self.slider_color, outline_width=1, name=self.name, visible=self.visible)

        self.box_obj.call_update = False
        self.circle_obj.call_update = False

    def _get_slider_pos(self):
        """Compute circle knob position (centered) based on value"""
        left = self.pos.x - self.size.x / 2
        t = (self.value - self.min_value) / (self.max_value - self.min_value)
        x = left + t * self.size.x
        return vector2d(x, self.pos.y)

    def draw(self, screen, camera: Camera, mouse_down_pos, mouse_pos):
        if not self.visible:
            return

        self.update_internal(mouse_down_pos, mouse_pos)

        # Drag logic
        if mouse_pos is not None:
            mx, my = mouse_pos.totuple() if isinstance(mouse_pos, vector2d) else mouse_pos
            if pygame.mouse.get_pressed()[0]:
                if not self.dragging and self.circle_obj.is_inside(vector2d(mx, my)):
                    self.dragging = True
                if self.dragging:
                    left = self.pos.x - self.size.x / 2
                    right = self.pos.x + self.size.x / 2
                    t = max(0, min(1, (mx - left) / (right - left)))
                    self.value = self.min_value + t * (self.max_value - self.min_value)
            else:
                self.dragging = False

        # Update visuals
        self.circle_obj.pos = self._get_slider_pos()
        self.box_obj.fill = self.fill
        self.box_obj.outline = self.fill
        self.circle_obj.fill = self.slider_color
        self.circle_obj.outline = self.slider_color

        # Draw both parts
        self.box_obj.draw(screen, camera, mouse_down_pos, mouse_pos)
        self.circle_obj.draw(screen, camera, mouse_down_pos, mouse_pos)
