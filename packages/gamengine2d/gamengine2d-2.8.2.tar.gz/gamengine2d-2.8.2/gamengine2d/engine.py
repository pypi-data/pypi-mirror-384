import time
import pygame

from .helper import vector2d, Context, Color, Camera, EngineError, is_colliding, rotate
from .objects import GameObject, Group, UIGroup
import tkinter as tk
from tkinter import ttk

from .ui_elements import UIElement


# -----------------------------
# Number / String Input Objects
# -----------------------------
class NumberInputObj:
    def __init__(self, var: tk.DoubleVar, default=0, dtype="int"):
        self.var = var
        self.default = default
        self.dtype = dtype

    @property
    def value(self):
        try:
            # Try converting to float; fallback to default if empty or invalid
            val = self.var.get()
            if val == "":
                return self.default
            if self.dtype == "int":
                return int(val)
            return float(val)
        except Exception:
            return self.default

    @value.setter
    def value(self, v):
        self.var.set(v)

class StringInputObj:
    def __init__(self, var: tk.StringVar, default=""):
        self.var = var
        self.default = default

    @property
    def value(self):
        val = self.var.get()
        if val == "":
            return self.default
        return val

    @value.setter
    def value(self, v):
        self.var.set(v)

# -----------------------------
# Settings Window
# -----------------------------
class SettingsWindow:
    _root = None  # single hidden root

    def __init__(self, title="Settings"):
        if SettingsWindow._root is None:
            SettingsWindow._root = tk.Tk()
            SettingsWindow._root.withdraw()  # hide main root

        self.root = tk.Toplevel(SettingsWindow._root)
        self.root.title(title)
        self.inputs = {}

        self.container = ttk.Frame(self.root, padding=20)
        self.container.pack(fill="both", expand=True)

        self.linked_inputs = {}

    def add_number_input(self, label, default=0, dtype="int"):
        var = tk.StringVar(master=self.root, value=str(default))
        frame = ttk.Frame(self.container)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text=label).pack(side="left")
        ttk.Entry(frame, textvariable=var).pack(side="right")
        input_obj = NumberInputObj(var, default, dtype)
        self.inputs[label] = input_obj
        return input_obj

    def add_string_input(self, label, default=""):
        var = tk.StringVar(master=self.root, value=default)
        frame = ttk.Frame(self.container)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text=label).pack(side="left")
        ttk.Entry(frame, textvariable=var).pack(side="right")
        input_obj = StringInputObj(var, default)
        self.inputs[label] = input_obj
        return input_obj


    def add_linked_number_input(self, label, obj, attr_name, default=None, dtype="int"):
        initial_value = default if default is not None else getattr(obj, attr_name)
        self.add_number_input(label, initial_value, dtype=dtype)
        self.linked_inputs[label] = (obj, attr_name)

    def update(self):
        self.root.update()
        for linked_input, (obj, attr_name) in self.linked_inputs.items():
            setattr(obj, attr_name, self.inputs[linked_input].value)

# -----------------------------
# Engine
# -----------------------------
class Engine:
    def __init__(self, width=500, height=500, name="GamEngine2D", resizable=True, background_color=Color.black):
        if not pygame.get_init():
            pygame.init()

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        flags = pygame.RESIZABLE if resizable else 0
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption(name)

        self.clock = pygame.time.Clock()
        self.camera = Camera(screen_size=vector2d(width, height))
        self.objects = []
        self.groups = []
        self.ui_groups = []
        self.ui_elements = []
        self.background_color = background_color

        # Context setup
        self.context = Context()
        self.context.functions.draw_circle = self.draw_circle
        self.context.functions.draw_circle_outline = self.draw_circle_outline
        self.context.functions.draw_text = self.draw_text
        self.context.functions.is_colliding = self.is_colliding
        self.context.functions.draw_rect = self.draw_rect
        self.context.functions.get_objects_with_prefix = self.get_objects_starting_with
        self.context.functions.create_sound = self.create_sound
        self.context.functions.play_sound = self.play_sound
        self.context.functions.is_colliding_pos = self.is_colliding_pos
        self.context.functions.draw_line_start_end = self.draw_line_start_end
        self.context.groups = self.groups
        self.context.ui_groups = self.ui_groups
        self.context.screen_size = vector2d(width, height)
        self.context.game_objects = self.objects
        self.context.ui_elements = self.ui_elements

    def on_frame(self, context, objects, camera):
        pass

    def on_pause(self, context, objects, camera, dt, screen):
        pass

    def draw_circle(self, pos: vector2d, radius: int, color: Color):
        screen_pos = self.camera.world_to_screen(pos).totuple()
        pygame.draw.circle(surface=self.screen, color=color.to_rgb(), center=screen_pos, radius=int(radius * self.camera.zoom))

    def is_colliding(self, obj1, obj2_name):
        try:
            obj2 = [obj for obj in self.objects if obj.name == obj2_name][0]
        except IndexError:
            raise EngineError(f"Error, game object with name '{obj2_name}' not found")

        if not isinstance(obj1, GameObject):
            raise EngineError(f"Error, {obj1.name} is not the name of a game object")

        if not isinstance(obj2, GameObject):
            raise EngineError(f"Error, {obj2.name} is not the name of a game object")

        if not hasattr(obj1, "get_corners"):
            raise EngineError(f"Error, game object with name '{obj1.name}' has no get_corners method")

        if not hasattr(obj2, "get_corners"):
            raise EngineError(f"Error, game object with name '{obj2.name}' has no get_corners method")

        return is_colliding(obj1.get_corners(), obj2.get_corners())

    def is_colliding_pos(self, pos, name):
        try:
            obj = [obj for obj in self.objects if obj.name == name][0]
        except IndexError:
            raise EngineError(f"Error, game object with name '{name}' not found")

        if not hasattr(obj, "get_corners"):
            raise EngineError(f"Error, game object with name '{obj.name}' has no get_corners method")

        return is_colliding(obj.get_corners(), [pos])

    def draw_text(self, text: str, pos: vector2d, color: Color, font_size=18, center=False):
        """Draw text at world position (pos)."""
        font = pygame.font.SysFont("Arial", font_size)
        text_surface = font.render(text, True, color.to_rgb())
        screen_pos = self.camera.world_to_screen(pos).totuple()

        if center:
            rect = text_surface.get_rect(center=(int(screen_pos[0]), int(screen_pos[1])))
        else:
            rect = text_surface.get_rect(topleft=(int(screen_pos[0]), int(screen_pos[1])))

        self.screen.blit(text_surface, rect)

    def draw_circle_outline(self, pos, radius, color, line_thickness):
         screen_pos = self.camera.world_to_screen(pos).totuple()
         pygame.draw.circle(self.screen, color.to_rgb(), screen_pos, int(radius * self.camera.zoom), width=line_thickness)

    def draw_line(self, pos, length, rotation=0, thickness=10, color=Color.white):
        screen_pos = self.camera.world_to_screen(pos).totuple()
        ends = [screen_pos + length / 2, screen_pos - length / 2]
        for i in range(len(ends)):
            ends[i] = rotate(ends[i], rotation)

        pygame.draw.line(self.screen, color.to_rgb(), ends[0], ends[1], thickness)

    def draw_line_start_end(self, start, end, thickness=10, color=Color.white):
        start = self.camera.world_to_screen(start)
        end = self.camera.world_to_screen(end)
        pygame.draw.line(self.screen, color.to_rgb(), start.totuple(), end.totuple(), thickness)

    def draw_rect(self, pos: vector2d, color: Color, size: vector2d):
        screen_pos = self.camera.world_to_screen(pos)
        half_size = size / 2
        half_size.x = int(half_size.x)
        half_size.y = int(half_size.y)
        corners = [
            vector2d(half_size.x, half_size.y),
            vector2d(-half_size.x, half_size.y),
            vector2d(-half_size.x, -half_size.y),
            vector2d(half_size.x, -half_size.y),
        ]

        corners = [(corner + screen_pos).totuple() for corner in corners]

        pygame.draw.polygon(self.screen, color.to_rgb(), corners, 0)

    def add_object(self, obj: GameObject):
        self.objects.append(obj)

    def add_ui_element(self, element: UIElement):
        self.ui_elements.append(element)

    def init_all_scripts(self):
        for obj in self.objects:
            obj.init_scripts()

    def get_objects_starting_with(self, prefix):
        objs = []
        for obj in self.objects:
            if obj.name.startswith(prefix):
                objs.append(obj)

        return objs

    def run(self, fps=60, dynamic_view=True):
        self.context.start_time = time.monotonic()
        self.init_all_scripts()
        running = True

        dragging = False
        last_mouse_pos = None
        mouse_holding = False  # track holding state

        while running:
            dt = self.clock.get_time() / 1000
            self.on_frame(self.context, self.objects, self.camera)

            # reset each frame
            self.context.mouse_down_pos = None
            self.context.mouse_hold_pos = None
            self.context.mouse_up_pos = None  # optional if you want release pos
            self.context.mouse_down = None  # <-- NEW: single click tracking
            self.context.mouse_down_screen = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if dynamic_view:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            # save click start position
                            screen_pos = vector2d.fromtuple(event.pos)
                            world_pos = self.camera.screen_to_world(screen_pos)
                            self.context.mouse_down_pos = world_pos
                            dragging = True
                            last_mouse_pos = screen_pos

                            # --- NEW: single click stored ---
                            if self.context.mouse_down is None:
                                self.context.mouse_down = world_pos
                                self.context.mouse_down_screen = screen_pos - self.context.screen_size / 2

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            dragging = False
                            # save release position
                            screen_pos = vector2d.fromtuple(event.pos)
                            world_pos = self.camera.screen_to_world(screen_pos)
                            self.context.mouse_up_pos = world_pos

                    elif event.type == pygame.MOUSEMOTION and dragging:
                        mouse_pos = vector2d(*event.pos)
                        delta = mouse_pos - last_mouse_pos
                        delta.y = -delta.y
                        self.camera.pos -= delta * (1 / self.camera.zoom)
                        last_mouse_pos = mouse_pos

                    elif event.type == pygame.MOUSEWHEEL:
                        zoom_factor = 1.1 if event.y > 0 else 0.9
                        mouse_world = self.camera.screen_to_world(vector2d(*pygame.mouse.get_pos()))
                        self.camera.zoom_at(zoom_factor, mouse_world)

            screen_mouse = vector2d.fromtuple(pygame.mouse.get_pos())
            self.context.mouse_pos_screen = screen_mouse
            world_pos = self.camera.screen_to_world(screen_mouse)
            self.context.mouse_pos_world = vector2d(world_pos.x, -world_pos.y)  # flip Y

            pressed = pygame.mouse.get_pressed()
            if pressed[0]:  # left mouse is held
                self.context.mouse_hold_pos = self.context.mouse_pos_world

            # update screen size and mouse
            w, h = self.screen.get_size()
            self.context.screen_size = vector2d(w, h)
            self.camera.screen_size = vector2d(w, h)

            self.screen.fill(self.background_color.to_rgb())

            if not self.context.pause:
                for obj in self.objects:
                    obj.update(dt)

            if not self.context.hide_all:
                for obj in self.objects:
                    obj.draw(self.screen, self.camera)

            for element in self.ui_elements:
                element.draw(self.screen, self.camera, self.context.mouse_down_screen, self.context.mouse_pos_screen - self.context.screen_size / 2)

            if self.context.pause:
                self.on_pause(self.context, self.objects, self.camera, dt, self.screen)

            for setting in self.context.settings:
                setting.update()

            for di, delay in enumerate(self.context.delays):
                delay.update()
                if delay.finished:
                    self.context.delays.pop(di)

            pygame.display.flip()
            self.clock.tick(fps)

            # always track live mouse
            screen_mouse = vector2d.fromtuple(pygame.mouse.get_pos())
            self.context.mouse_pos_screen = screen_mouse
            self.context.mouse_pos_world = self.camera.screen_to_world(screen_mouse)

        pygame.quit()


    def remove_object(self, name):
        for io, obj in enumerate(self.objects):
            if obj.name == name:
                self.objects.pop(io)

    def create_sound(self, name, path):
        sound = pygame.mixer.Sound(path)
        self.context.sounds[name] = sound

    def play_sound(self, name):
        sound = self.context.sounds[name]
        sound.play()

    def add_group(self, group):
        if not isinstance(group, Group):
            raise EngineError("Error, tried to add group that isn't of type Group")

        self.groups.append(group)
        self.objects += group.get_all_children()

    def add_ui_group(self, group):
        if not isinstance(group, UIGroup):
            raise EngineError("Error, tried to add group that isn't of type UIGroup")

        self.ui_groups.append(group)
        self.ui_elements += group.get_all_children()
