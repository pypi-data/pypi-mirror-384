## Dependencies

This package depends on the following libraries:

- numpy (BSD)
- moderngl (MIT)
- pygame (LGPL)

Pygame is used for graphics, and is not modified in this package. Please see Pygame's license: [LGPL v2.1](https://www.pygame.org/docs/).

To use `gamengine2d`, You must first use the Engine class

```python
from gamengine2d import Engine, Color, Rectangle, vector2d # import the Engine Rectangle, vector2d, and Color classes

engine = Engine(width=500, height=500,           # Create the Engine object that opens a window of height 500, width 500,
                name="Unity2D", resizable=True,  # name Unity2D, and make the window resizable,
                background_color=Color.blue)   # set the background color to blue

# By default, the name is Unity2D, resizable is True, and the background color is Color.black()

rect = Rectangle(pos=vector2d(0, 0), size=vector2d(100, 400),  # Create a rectangle at 0, 0, with size 100, 400,
                 color=Color.red, rotation=10, visible=True, # and color red, and rotation 10 degrees, and make it visible,
                 name="MyRect")                                # and name it MyRect

# By default, the position is 0, 0, size is 40, 40, color is Color.white(), rotation is 0, visible is True, and name is rectangle

engine.add_object(rect) # add the rectangle object to the engine

engine.run(60, dynamic_view=True) # start the engine, and try to run at 60 fps, and dynamic view is True

# dynamic view allows the use to use the mouse wheel to zoom in or out, or left click and drag to pan around.
# by default, fps is 60, and dynamic view is True
```

To add a script to an object, use `attach`.

```python
rect.attach("scripts/rectangle.py", engine.context) # attach the script rectangle.py to the rect object with the engine context
```
Then, in ``scripts/rectangle.py``

```python
class Rectangle: # The class name should be the same as the filename
    def __init__(self, obj, context): # get the object, and the engine context
        self.obj = obj # assign self.obj to obj
        self.context = context # assign self.context to context
    
    def update(self, dt): # the update method is called every frame, and takes dt which is delta time
        self.obj.rotation += 10 * dt # rotate the object at 10 degrees per second
        self.context.functions.draw_text(text=str(self.obj.rotation), # Draw the current rotation as text
                                         pos=vector2d(400, 300),      # at 400, 300
                                         color=Color.red,           # in red
                                         font_size=18)                # with font size 18

# By default, font_size is 18
```
