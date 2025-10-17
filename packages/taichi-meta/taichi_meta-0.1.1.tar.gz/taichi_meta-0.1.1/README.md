# Taichi Meta

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![Taichi](https://img.shields.io/badge/Taichi-v1.6%2B-orange)](https://www.taichi-lang.org/)

**Dynamic Taichi Kernel Compilation and Hot-Reloading for Python**

Taichi Meta enables runtime compilation and hot-reloading of Taichi kernels, making it perfect for interactive development, Jupyter notebooks, and rapid prototyping of GPU-accelerated computations.

## 🚀 Key Features

- **Dynamic Kernel Compilation** - Compile Taichi kernels from strings at runtime
- **Hot-Reloading** - Update kernel implementations without restarting your program
- **Kernel Management** - Organize and manage multiple kernels with automatic cleanup
- **Jupyter Friendly** - Perfect for interactive development and experimentation
- **Lightweight** - Minimal dependencies, built on standard Python libraries

## 📦 Installation

```bash
pip install taichi-meta
```

## ⚡ Quick Start

```python
import taichi as ti
import numpy as np
from taichi_meta import MetaKernelLoader

ti.init(arch=ti.vulkan)

# Initialize the kernel loader
loader = MetaKernelLoader()

# Create a test array
x = ti.ndarray(ti.f32, shape=10)

# Compile and load your first kernel
loader.compile_and_load('''
@ti.kernel
def add_base(x: ti.types.ndarray(), base: ti.f32):
    for i in range(x.shape[0]):
        x[i] += base
''')

# Use the kernel
x.from_numpy(np.arange(10, dtype=np.float32))
loader[None].add_base(x, 5.0)
print(f"Result: {x.to_numpy()}")
# Output: Result: [ 5.  6.  7.  8.  9. 10. 11. 12. 13. 14.]
```

## 🔥 Hot-Reloading in Action

```python
# Hot-reload the kernel with a new implementation
loader.compile_and_load('''
@ti.kernel
def add_base(x: ti.types.ndarray(), base: ti.f32):
    for i in range(x.shape[0]):
        x[i] += 2 * base  # Changed: now adds 2*base
''')

# Use the updated kernel without restarting
x.from_numpy(np.arange(10, dtype=np.float32))
loader[None].add_base(x, 5.0)
print(f"Result: {x.to_numpy()}")
# Output: Result: [ 5.  7.  9. 11. 13. 15. 17. 19. 21. 23.]
```

## 📚 Documentation

### MetaKernelLoader

The main class that manages kernel compilation and loading.

#### `__init__()`
Initializes a new kernel loader with an empty cache.

```python
loader = MetaKernelLoader()
```

#### `compile_and_load(kernel_code, kernel_id=None)`
Compiles Taichi kernel code and loads it into the current Python session.

**Parameters:**
- `kernel_code` (str): Python string containing Taichi kernel code
- `kernel_id` (str, optional): Unique identifier for the kernel. Auto-generated if not provided.

**Returns:** `None`

```python
loader.compile_and_load('''
@ti.kernel
def my_kernel(arr: ti.types.ndarray(), value: ti.f32):
    for i in range(arr.shape[0]):
        arr[i] = value * i
''', kernel_id="my_kernel")
```

#### `__getitem__(kernel_id) -> types.ModuleType`
Retrieves a loaded kernel module by its ID.

**Parameters:**
- `kernel_id` (str): Kernel identifier. Use `None` for the most recently loaded kernel.

**Returns:** Module containing the compiled kernel functions

```python
kernel_module = loader["my_kernel"]
kernel_module.my_kernel(array, 2.5)

# Or use the most recent kernel
kernel_module = loader[None]
```

#### `cleanup_all()`
Unloads all kernels and clears the cache. Useful for freeing memory.

```python
loader.cleanup_all()
```

### Advanced Usage

#### Multiple Kernel Management

```python
# Load multiple kernels with specific IDs
loader.compile_and_load('''
@ti.kernel
def kernel_a(x: ti.types.ndarray()):
    for i in x:
        x[i] = i * 2
''', kernel_id="doubler")

loader.compile_and_load('''
@ti.kernel  
def kernel_b(x: ti.types.ndarray()):
    for i in x:
        x[i] = i ** 2
''', kernel_id="squarer")

# Access specific kernels
doubler_module = loader["doubler"]
squarer_module = loader["squarer"]

# Update a specific kernel
loader.compile_and_load('''
@ti.kernel
def kernel_a(x: ti.types.ndarray()):
    for i in x:
        x[i] = i * 3  # Now triples instead of doubles
''', kernel_id="doubler")  # Replaces the existing "doubler" kernel
```

#### Interactive Development in Jupyter

```python
# Cell 1: Initial setup
import taichi as ti
from taichi_meta import MetaKernelLoader

ti.init(arch=ti.cpu)
loader = MetaKernelLoader()
data = ti.ndarray(ti.f32, shape=5)

# Cell 2: First kernel version
loader.compile_and_load('''
@ti.kernel
def process(data: ti.types.ndarray()):
    for i in data:
        data[i] = i * 10
''')
loader[None].process(data)
print(data.to_numpy())  # [0., 10., 20., 30., 40.]

# Cell 3: Improved kernel (hot-reload)
loader.compile_and_load('''
@ti.kernel  
def process(data: ti.types.ndarray()):
    for i in data:
        data[i] = ti.sin(i * 0.5)  # Different operation
''')
loader[None].process(data)  
print(data.to_numpy())  # Updated results without restarting kernel
```

## 🔧 Technical Details

Taichi Meta uses Python's `linecache` module and `compile()` function to create virtual modules that contain your dynamically compiled kernels. The system:

- Creates virtual Python files for clean tracebacks
- Manages kernel lifecycle and memory cleanup
- Maintains Taichi's JIT compilation benefits
- Provides a simple, Pythonic API


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the amazing [Taichi Lang](https://github.com/taichi-dev/taichi) framework
- Inspired by the need for interactive GPU computing in Python

---
Feel free to open issues for bug reports or feature requests.
