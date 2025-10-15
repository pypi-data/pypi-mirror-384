import os
import importlib.util
import sys
import math
import time
from .shaders import ComputeShader
import moderngl
import numpy as np

# -----------------------------
# Vector 2D
# -----------------------------
class vector2d:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    @property
    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    @property
    def sqr_magnitude(self):
        return self.x ** 2 + self.y ** 2

    def normalize(self):
        magnitude = self.magnitude
        self.x = self.x / magnitude
        self.y = self.y / magnitude

    @property
    def normalized(self):
        magnitude = self.magnitude
        return vector2d(self.x, self.y) / magnitude

    def __add__(self, other):
        if isinstance(other, vector2d):
            return vector2d(self.x + other.x, self.y + other.y)
        else:
            return vector2d(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, vector2d):
            return vector2d(self.x - other.x, self.y - other.y)
        else:
            return vector2d(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, vector2d):
            return vector2d(self.x * other.x, self.y * other.y)
        else:
            return vector2d(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, vector2d):
            return vector2d(self.x / other.x, self.y / other.y)
        else:
            return vector2d(self.x / other, self.y / other)

    def totuple(self):
        return (self.x, self.y)

    def __radd__(self, other):
        return vector2d(self.x + other, self.y + other)

    def __rsub__(self, other):
        return vector2d(self.x - other, self.y - other)

    def __rtruediv__(self, other):
        return vector2d(self.x / other, self.y / other)

    def __rmul__(self, other):
        return vector2d(self.x * other, self.y * other)

    @classmethod
    def fromtuple(cls, tuple):
        cls.x, cls.y = tuple
        return vector2d(cls.x, cls.y)

    def __repr__(self):
        return f"vector2d({self.x}, {self.y})"

    def copy(self):
        return vector2d(self.x, self.y)

    def __neg__(self):
        return vector2d(-self.x, -self.y)

    def __lt__(self, other):
        return self.x < other.x and self.y < other.y

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def __gt__(self, other):
        return self.x > other.x and self.y > other.y

    def __ge__(self, other):
        return self.x >= other.x and self.y >= other.y

vector2d.up = vector2d(0, 1)
vector2d.down = vector2d(0, -1)
vector2d.right = vector2d(1, 0)
vector2d.left = vector2d(-1, 0)
vector2d.one = vector2d(1, 1)
vector2d.zero = vector2d(0, 0)

def rotate(pos: vector2d, angle):
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    x = pos.x * cos_a - pos.y * sin_a
    y = pos.x * sin_a + pos.y * cos_a
    return vector2d(x, y)

# -----------------------------
# Color
# -----------------------------
class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def RGB(r, g, b): return Color(r, g, b)
    @staticmethod
    def hex(hex_string):
        if not hex_string.startswith("#"): raise Exception("String must start with #")
        if not len(hex_string) == 7: raise Exception("String must contain 7 characters")
        r = int(hex_string[1:3], 16)
        g = int(hex_string[3:5], 16)
        b = int(hex_string[5:7], 16)
        return Color(r, g, b)

    def __eq__(self, other):
        if self.r == other.r and self.g == other.g and self.b == other.b:
            return True
        return False

    def to_hex(self):
        if not all(0 <= x <= 255 for x in (self.r, self.g, self.b)):
            raise ValueError("RGB values must be in the range 0-255")
        return "#{:02X}{:02X}{:02X}".format(self.r, self.g, self.b)

    def to_rgb(self):
        return self.r, self.g, self.b

Color.black   =      Color(0, 0, 0)
Color.white   =      Color(255, 255, 255)
Color.red     =      Color(255, 0, 0)
Color.green   =      Color(0, 255, 0)
Color.blue    =      Color(0, 0, 255)
Color.yellow  =      Color(255, 255, 0)
Color.cyan    =      Color(0, 255, 255)
Color.magenta =      Color(255, 0, 255)
Color.grey =         Color(33, 33, 33)
Color.light_grey =   Color(80, 80, 80)
Color.light_red =    Color.hex("#fd596f")
Color.light_green =  Color.hex("#00bea0")
Color.light_yellow = Color.hex("#fed05f")
Color.orange =       Color.hex("#fea65d")
Color.light_blue =   Color.hex("#6d9ada")

class Delay:
    def __init__(self, delay, start_time, callback):
        self.delay = delay
        self.start_time = start_time
        self.callback = callback
        self.finished = False

    def update(self):
        if time.monotonic() - self.start_time > self.delay:
            self.callback()
            self.finished = True
            return

# -----------------------------
# Context / Functions
# -----------------------------
class Functions:
    def __init__(self):
        self.draw_circle = None
        self.is_colliding = None
        self.draw_text = None
        self.draw_rect = None
        self.get_objects_with_prefix = None
        self.add_sound = None
        self.create_sound = None
        self.is_colliding_pos = None
        self.draw_circle_outline = None
        self.draw_line = None
        self.draw_line_start_end = None

class Context:
    def __init__(self):
        self.functions = Functions()
        self.screen_size = vector2d(0, 0)  # <-- added
        self.settings = []
        self.pause = False
        self.hide_all = False
        self.start_time = None
        self.runtime_vars = {}
        self.game_objects = []
        self.ui_elements = []
        self.delays = []
        self.sounds = {}
        self.mouse_down_pos = None
        self.mouse_pos_screen = None
        self.mouse_pos_world = None
        self.mouse_hold_pos = None
        self.compute_shaders: list[ComputeShader] = []
        self.moderngl_context = moderngl.create_standalone_context()

    def get(self, name):
        for obj in self.game_objects:
            if obj.name == name:
                return obj
        else:
            raise EngineError(f"Error, name '{name}' not found")

    def remove_object(self, obj):
        self.game_objects.remove(obj)

    def add_delay(self, delay, callback):
        self.delays.append(Delay(delay, time.monotonic(), callback))

    def compute_shader(self, name, filename):
        self.compute_shaders.append(ComputeShader(context=self.moderngl_context, name=name, filename=filename))

    def run_shader(self, name, group_x=1, group_y=1, group_z=1):
        for compute_shader in self.compute_shaders:
            if compute_shader.name == name:
                compute_shader.run(group_x=group_x, group_y=group_y, group_z=group_z)
                break
        else:
            raise EngineError(f"Error, no shader has name {name}")

    def bind_buffer(self, shader_name, data=None, reserve=None, buffer_name=None, dtype=np.int32):
        for compute_shader in self.compute_shaders:
            if compute_shader.name == shader_name:
                buffer = compute_shader.new_buffer(data=data, reserve=reserve, name=buffer_name)
                compute_shader.bind_buffer(binding=0, buffer=buffer)

                break

    def read_buffer(self, shader_name, buffer_name):
        for compute_shader in self.compute_shaders:
            if compute_shader.name == shader_name:
                buffer = compute_shader.read_buffer(buffer_name=buffer_name)
                return buffer

        raise EngineError(f"Error, no shader has name {shader_name}")

    def set_uniform(self, shader_name, uniform_name, value):
        for compute_shader in self.compute_shaders:
            if compute_shader.name == shader_name:
                compute_shader.set_uniform(uniform_name, value)

# -----------------------------
# Script
# -----------------------------
class Script:
    def __init__(self, obj, script_path, context):
        self.obj = obj
        self.context = context
        self.script_path = script_path
        self.module = None
        self.cls = None
        self.instance = None
        self.load(script_path)

    def load(self, path):
        if not os.path.exists(path):
            print(f"[Script] File not found: {path}")
            return
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[Script] Error loading module {path}: {e}")
            return
        self.module = module

        # Class is PascalCase version of file name
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        if hasattr(module, class_name):
            self.cls = getattr(module, class_name)
        else:
            print(f"[Script] No class '{class_name}' found in {path}")

    def init_instance(self):
        """Instantiate the class, passing the owner object and context."""
        if self.cls is None or self.instance is not None:
            return
        try:
            self.instance = self.cls(self.obj, self.context)
        except Exception as e:
            print(f"[Script] Failed to instantiate script for {self.obj.name}: {e}")
            self.instance = None

        if self.instance and hasattr(self.instance, "start"):
            try:
                self.instance.start()
            except Exception:
                pass

    def update(self, dt):
        if self.instance is None:
            return
        self.instance.update(dt)
# -----------------------------
# Camera
# -----------------------------
class Camera:
    def __init__(self, pos=None, zoom=1, screen_size=None):
        self.pos = pos or vector2d(0, 0)
        self.zoom = zoom
        self.screen_size = screen_size or vector2d(800, 600)
        self.min_zoom = 0.1
        self.max_zoom = 10

    def world_to_screen(self, world_pos: vector2d):
        screen_pos = vector2d(
            (world_pos.x - self.pos.x) * self.zoom,
            (-world_pos.y + self.pos.y) * self.zoom  # invert Y
        )
        screen_pos += vector2d(self.screen_size.x / 2, self.screen_size.y / 2)
        return screen_pos

    def screen_to_world(self, screen_pos: vector2d):
        world_pos = screen_pos - vector2d(self.screen_size.x / 2, self.screen_size.y / 2)
        world_pos = world_pos * (1 / self.zoom) + self.pos
        return world_pos

    def zoom_at(self, zoom_factor, pivot: vector2d):
        old_zoom = self.zoom
        self.zoom *= zoom_factor
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))
        self.pos += (pivot - self.pos) * (1 - old_zoom / self.zoom)

class EngineError(Exception):
    pass

def project_polygon(axis, vertices):
    dots = [v.x * axis.x + v.y * axis.y for v in vertices]
    return min(dots), max(dots)

def overlap(p1, p2):
    return p1[0] <= p2[1] and p2[0] <= p1[1]

def is_colliding(poly1, poly2):
    # poly1, poly2 = lists of vector2d
    for polygon in (poly1, poly2):
        for i in range(len(polygon)):
            # get edge
            p1, p2 = polygon[i], polygon[(i + 1) % len(polygon)]
            edge = vector2d(p2.x - p1.x, p2.y - p1.y)
            # perpendicular axis
            axis = vector2d(-edge.y, edge.x)
            # project both polygons
            proj1 = project_polygon(axis, poly1)
            proj2 = project_polygon(axis, poly2)
            # check overlap
            if not overlap(proj1, proj2):
                return False
    return True

def point_near_line(p, a, b, threshold=5):
    """Check if point p is within threshold pixels of line segment a-b."""
    ax, ay = a
    bx, by = b
    px, py = p

    lab2 = (bx - ax) ** 2 + (by - ay) ** 2
    if lab2 == 0:
        return (px - ax) ** 2 + (py - ay) ** 2 < threshold ** 2

    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / lab2))
    projx = ax + t * (bx - ax)
    projy = ay + t * (by - ay)

    dist2 = (px - projx) ** 2 + (py - projy) ** 2
    return dist2 < threshold ** 2


def get_edge_point(obj, direction_angle):
    """Return world position of the edge in given direction (degrees)."""
    angle = math.radians(direction_angle)
    dx, dy = math.cos(angle), math.sin(angle)

    # Half-size projected onto this direction
    half_extent = (obj.size.x / 2 * abs(dx)) + (obj.size.y / 2 * abs(dy))
    return obj.pos + vector2d(dx, dy) * half_extent

class UIElement:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.scripts = []
        self.call_update = True

    def attach(self, file_path, context):
        script = Script(self, file_path, context)
        script.init_instance()
        self.scripts.append(script)

    def init_scripts(self):
        for script in self.scripts:
            script.init_instance()

    def update_internal(self, mouse_down_pos, mouse_pos):
        if not self.call_update:
            return

        self.update_scripts(mouse_pos)
        if mouse_down_pos is not None:
            if self.is_inside(mouse_down_pos):
                self.on_click(mouse_down_pos)

        if mouse_pos is not None:
            if self.is_inside(mouse_pos):
                self.on_hover(mouse_pos)

        return

    def update_scripts(self, mouse_pos):
        for script in self.scripts:
            script.update(mouse_pos)

    def is_inside(self, pos):
        half_size = self.size / 2
        obj_pos = self.pos
        return (obj_pos.x - half_size.x <= pos.x <= obj_pos.x + half_size.x) and \
            (obj_pos.y - half_size.y <= pos.y <= obj_pos.y + half_size.y)

    def on_click(self, mouse_pos):
        for script in self.scripts:
            script.instance.on_click(mouse_pos)

    def on_hover(self, mouse_pos):
        for script in self.scripts:
            script.instance.on_hover(mouse_pos)

    def draw(self, screen, camera: Camera, mouse_down_pos, mouse_pos):
        pass

