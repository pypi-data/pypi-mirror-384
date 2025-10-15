from .helper import vector2d, Script, Camera, Color, rotate, EngineError
import pygame
import math
from .helper import UIElement

# -----------------------------
# GameObject
# -----------------------------
class GameObject:
    def __init__(self, name="GameObject"):
        self.scripts = []
        self.name = name

    def draw(self, screen, camera):
        pass

    def update(self, dt):
        for script in self.scripts:
            script.update(dt)

    def attach(self, file_path, context):
        script = Script(self, file_path, context)
        script.init_instance()
        self.scripts.append(script)

    def init_scripts(self):
        for script in self.scripts:
            script.init_instance()

# -----------------------------
# Rectangle
# -----------------------------
class Rectangle(GameObject):
    def __init__(self, pos=None, size=vector2d(40, 40), rotation=0, color=Color.white, visible=True, name="rectangle", texture=None):
        super().__init__(name)
        if pos is None: pos = vector2d(0, 0)
        self.pos = pos
        self.size = size
        self.color = color
        self.visible = visible
        self.rotation = rotation
        self.texture = texture  # Can be a pygame.Surface or path string

        self._surface = None
        self.update_surface()

    def update_surface(self):
        w, h = int(self.size.x), int(self.size.y)

        if self.texture:
            # Load image if a path is provided
            if isinstance(self.texture, str):
                self._surface = pygame.image.load(self.texture).convert_alpha()
            else:
                self._surface = self.texture  # already a Surface
            # Scale texture to rectangle size
            self._surface = pygame.transform.scale(self._surface, (w, h))
        else:
            # Plain colored rectangle
            self._surface = pygame.Surface((w, h), pygame.SRCALPHA)
            # Fill with fully opaque color, but leave alpha intact for blending
            self._surface.fill((self.color.r, self.color.g, self.color.b, 255))


    def get_corners(self):
        hw = self.size.x / 2
        hh = self.size.y / 2
        corners = [
            vector2d(-hw, -hh),
            vector2d(hw, -hh),
            vector2d(hw, hh),
            vector2d(-hw, hh),
        ]
        corners = [rotate(corner, self.rotation) for corner in corners]
        corners = [corner + self.pos for corner in corners]
        return corners

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return

        if self._surface:
            # Apply rotation
            rotated_surface = pygame.transform.rotate(self._surface, -self.rotation)
            rect = rotated_surface.get_rect(center=camera.world_to_screen(self.pos).totuple())
            screen.blit(rotated_surface, rect.topleft)
        else:
            # fallback to original polygon drawing
            corners = self.get_corners()
            corners = [camera.world_to_screen(c).totuple() for c in corners]
            pygame.draw.polygon(screen, self.color.to_rgb(), corners, 0)

# -----------------------------
# Circle
# -----------------------------
class Circle(GameObject):
    def __init__(self, pos=None, radius=20, color=Color.white, visible=True, name="circle"):
        super().__init__(name)
        if pos is None: pos = vector2d(0, 0)
        self.pos = pos
        self.radius = radius
        self.color = color
        self.visible = visible

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return
        screen_pos = camera.world_to_screen(self.pos).totuple()
        pygame.draw.circle(screen, self.color.to_rgb(), screen_pos, int(self.radius * camera.zoom))

# -----------------------------
# RectangleOutline
# -----------------------------
class RectangleOutline(GameObject):
    def __init__(self, pos=None, size=vector2d(40, 40),
                 color=Color.white, rotation=0, line_width=2, visible=True,
                 name="rectangle_outline"):
        super().__init__(name)
        if pos is None: pos = vector2d(0, 0)
        self.pos = pos
        self.size = size
        self.color = color
        self.visible = visible
        self.line_width = line_width
        self.rotation = rotation

    def get_corners(self):
        hw = self.size.x / 2
        hh = self.size.y / 2
        corners = [
            vector2d(-hw, -hh),
            vector2d(hw, -hh),
            vector2d(hw, hh),
            vector2d(-hw, hh),
        ]
        corners = [rotate(corner, self.rotation) for corner in corners]
        corners = [corner + self.pos for corner in corners]
        return corners

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return

        corners = self.get_corners()
        corners = [camera.world_to_screen(c).totuple() for c in corners]
        pygame.draw.polygon(screen, self.color.to_rgb(), corners, self.line_width)

class Line(GameObject):
    def __init__(self, pos=None, length=100, color=Color.white, visible=True, name="line", thickness=2, rotation=0):
        super().__init__(name)
        if pos is None: pos = vector2d(0, 0)
        self.pos = pos
        self.length = length
        self.color = color
        self.visible = visible
        self.thickness = thickness
        self.rotation = rotation

    def get_corners(self):
        hl = self.length / 2
        corners = [
            vector2d(0, hl),
            vector2d(0, -hl)
        ]
        corners = [rotate(corner, self.rotation) for corner in corners]
        corners = [corner + self.pos for corner in corners]
        return corners

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return

        corners = self.get_corners()
        corners = [camera.world_to_screen(c).totuple() for c in corners]
        pygame.draw.polygon(screen, self.color.to_rgb(), corners, self.thickness)

class Polygon(GameObject):
    def __init__(self, pos=None, vertices=None, color=Color.white, visible=True, name="polygon", rotation=0):
        if vertices is None:
            vertices = [vector2d(0, 0), vector2d(0, 100), vector2d(100, 0)]

        super().__init__(name)
        if pos is None: pos = vector2d(0, 0)
        self.pos = pos
        self.vertices = vertices
        self.color = color
        self.visible = visible
        self.rotation = rotation

    def get_corners(self):
        corners = [rotate(vertex, self.rotation) + self.pos for vertex in self.vertices]
        return corners

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return
        corners = self.get_corners()
        corners = [camera.world_to_screen(corner).totuple() for corner in corners]
        pygame.draw.polygon(screen, self.color.to_rgb(), corners)

class Ellipse(GameObject):
    def __init__(self, center, width, height, color=Color.white, visible=True, name="ellipse", rotation=0, num_points=36):
        super().__init__(name)
        if center is None: center = vector2d(0, 0)
        self.pos = center
        self.width = width
        self.height = height
        self.color = color
        self.visible = visible
        self.rotation = rotation  # in degrees
        self.num_points = num_points  # controls smoothness

    def get_corners(self):
        # return points approximating the rotated ellipse
        cx, cy = self.pos.x, self.pos.y
        angle_rad = math.radians(self.rotation)
        points = []

        for i in range(self.num_points):
            t = (2 * math.pi / self.num_points) * i
            x = cx + (self.width / 2) * math.cos(t)
            y = cy + (self.height / 2) * math.sin(t)
            xr = cx + (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad)
            yr = cy + (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad)

            points.append(vector2d(xr, yr))

        return points

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return
        corners = [camera.world_to_screen(corner).totuple() for corner in self.get_corners()]
        pygame.draw.polygon(screen, self.color.to_rgb(), corners)

class TextOverlay(GameObject):
    def __init__(self, text, pos, color=Color.white, visible=True, name="text", font_size=40,
                 font_family="Arial", bold=True, italic=False, antialiasing=True, rotation=0):
        super().__init__(name)
        self.text = text
        self.color = color
        self.visible = visible
        self.font_size = font_size
        self.font_family = font_family
        self.bold = bold
        self.italic = italic
        self.antialiasing = antialiasing
        self.pos = pos
        self.rotation = rotation  # rotation in degrees

    def draw(self, screen, camera: Camera):
        if not self.visible:
            return

        screen_size = screen.get_size()
        midpoint = ((vector2d.fromtuple(screen_size) / 2) + self.pos).totuple()

        font = pygame.font.SysFont(self.font_family, self.font_size, self.bold, self.italic)
        text_surface = font.render(self.text, self.antialiasing, self.color.to_rgb())

        # Rotate the text surface
        if self.rotation != 0:
            text_surface = pygame.transform.rotate(text_surface, -self.rotation)  # negative for clockwise
        text_rect = text_surface.get_rect(center=midpoint)

        screen.blit(text_surface, text_rect)

class Group:
    def __init__(self, *args, **kwargs):
        self.children = []
        for obj in args:
            if not isinstance(obj, GameObject):
                raise EngineError("Error, tried to group object which is not of type GameObject")
            self.children.append(obj)

        self.name = kwargs.get("name", "Group")

    def add(self, obj):
        if not isinstance(obj, GameObject):
            raise EngineError(f"Error tried to group object which is not of type GameObject")
        self.children.append(obj)

    def remove(self, obj_name):
        for child in self.children:
            if child.name == obj_name:
                self.children.remove(child)

    def set_pos(self, pos):
        for child in self.children:
            child.pos = pos.copy()

    def set_pos_rel(self, pos):
        for child in self.children:
            child.pos += pos.copy()

    def link_pos(self, pos):
        for child in self.children:
            child.pos = pos

    def hide_all(self):
        for children in self.children:
            children.visible = False

    def show_all(self):
        for children in self.children:
            children.visible = True

    def change_color(self, color):
        for child in self.children:
            child.color = color

    def get_all_children(self):
        return self.children

class UIGroup:
    def __init__(self, *args, **kwargs):
        self.children = []
        for obj in args:
            if not isinstance(obj, UIElement):
                raise EngineError("Error, tried to group object which is not of type UIElement")
            self.children.append(obj)

        self.name = kwargs.get("name", "UIGroup")

    def add(self, obj):
        if not isinstance(obj, UIElement):
            raise EngineError(f"Error tried to group object which is not of type UIElement")
        self.children.append(obj)

    def remove(self, obj_name):
        for child in self.children:
            if child.name == obj_name:
                self.children.remove(child)

    def set_pos_rel(self, pos):
        for child in self.children:
            child.pos += pos.copy()

    def set_pos(self, pos):
        for child in self.children:
            child.pos = pos.copy()

    def link_pos(self, pos):
        for child in self.children:
            child.pos = pos

    def hide_all(self):
        for child in self.children:
            child.visible = False

    def show_all(self):
        for child in self.children:
            child.visible = True

    def get_all_children(self):
        return self.children
