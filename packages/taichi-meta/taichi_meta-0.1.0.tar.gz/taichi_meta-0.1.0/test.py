import taichi as ti
import numpy  as np

from taichi_meta import MetaKernelLoader

ti.init(arch=ti.vulkan)

# Test
x = ti.ndarray(ti.f32, shape=10)
loader = MetaKernelLoader()

loader.compile_and_load('''
@ti.kernel
def add_base(x: ti.types.ndarray(), base: ti.f32):
    for i in range(x.shape[0]):
        x[i] += base
''')

x.from_numpy(np.arange(10, dtype=np.float32))
result = loader[None].add_base(x, 5.0)
print(f"Result: {x.to_numpy()}")

loader.compile_and_load('''
@ti.kernel
def add_base(x: ti.types.ndarray(), base: ti.f32):
    for i in range(x.shape[0]):
        x[i] += 2*base
''')

x.from_numpy(np.arange(10, dtype=np.float32))
result = loader[None].add_base(x, 5.0)
print(f"Result2: {x.to_numpy()}")
