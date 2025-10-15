
import moderngl
import numpy as np

class EngineError(Exception):
    pass

class Buffer:
    def __init__(self, ctx, dtype=None, data=None, reserve=None):
        self.array = data
        if reserve and dtype:
            self.buf = ctx.buffer(reserve=reserve)

        elif reserve and not dtype:
            raise EngineError(f"Error, dtype not specified for reserve")
        elif data is not None:
            self.buf = ctx.buffer(data=data.tobytes() if isinstance(data, np.ndarray) else data)
        self._dtype = dtype

    @property
    def dtype(self):
        return self.array.dtype if self.array is not None else self._dtype

    def change_buffer(self, data, offset=0):
        if isinstance(data, np.ndarray):
            data = data.tobytes()
        self.buf.write(data, offset=offset)

class ComputeShader:
    def __init__(self, context: moderngl.Context, name, filename):
        self.context = context
        self.name = name
        self.filename = filename
        self.buffers = {}
        self.shader = None
        self.create_shader()

    def new_buffer(self, name, dtype=np.int32, data=None, reserve=None):
        buffer = Buffer(self.context, data=data, reserve=reserve, dtype=dtype)
        self.buffers[name] = buffer
        return buffer

    def bind_buffer(self, buffer, binding):
        buffer.buf.bind_to_storage_buffer(binding)
        self.buffers[binding] = buffer

    def create_shader(self):
        with open(self.filename) as f:
            source = f.read()
        self.shader = self.context.compute_shader(source)

    def run(self, group_x=1, group_y=1, group_z=1):
        self.shader.run(group_x, group_y, group_z)

    def read_buffer(self, buffer_name):
        buffer = self.buffers[buffer_name]
        return np.frombuffer(buffer.buf.read(), dtype=buffer.dtype)

    def change_buffer(self, name, data, offset=0):
        buffer = self.buffers[name]
        buffer.change_buffer(data, offset)

    def set_uniform(self, name, value):
        self.shader[name].value = value
