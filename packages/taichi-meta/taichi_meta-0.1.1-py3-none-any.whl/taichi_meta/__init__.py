import linecache, types, sys
from   collections import OrderedDict

import taichi as ti

__version__ = "0.1.1"
__author__ = 'Thomas Kirchner'

class MetaKernelLoader:
    def __init__(self):
        self.kernel_cache = OrderedDict()  # kernel_id -> module
        self.current_kernel_id = None
        self.kernel_counter = 0

    def compile_and_load(self, kernel_code, kernel_id=None):
        """Compile string to kernel and load it"""
        if kernel_id is None:
            kernel_id = f"kernel_{self.kernel_counter}"
            self.kernel_counter += 1

        # Unload previous kernel if we're replacing it
        if kernel_id in self.kernel_cache:
            self._unload_kernel(kernel_id)

        # Load new kernel
        module = self._load_kernel(kernel_code, kernel_id)

        # Update cache
        self.kernel_cache[kernel_id] = module
        self.current_kernel_id = kernel_id

    def _load_kernel(self, kernel_code, kernel_id):
        """Use linecache dark magic to help taichi ;) """
        full_code = f'''
import taichi as ti
import taichi.math as tm
{kernel_code}
'''
        virtual_filename = f"/virtual/{kernel_id}.py"

        # Populate linecache
        linecache.cache[virtual_filename] = (
            len(full_code),
            None,
            [line + '\n' for line in full_code.splitlines()],
            virtual_filename
        )

        # Compile and execute
        code = compile(full_code, virtual_filename, 'exec')
        module = types.ModuleType(kernel_id)
        module.__dict__.update({
            'ti': ti,
            'np': __import__('numpy'),
            '__name__': kernel_id
        })

        exec(code, module.__dict__)
        sys.modules[kernel_id] = module

        return module

    def _unload_kernel(self, kernel_id):
        """Clean up a specific kernel"""
        if kernel_id in sys.modules:
            del sys.modules[kernel_id]

        virtual_filename = f"/virtual/{kernel_id}.py"
        if virtual_filename in linecache.cache:
            del linecache.cache[virtual_filename]

    def __getitem__(self, kernel_id=None) -> types.ModuleType:
        """Get a loaded kernel by ID (returns current if None)"""
        if kernel_id is None:
            kernel_id = self.current_kernel_id

        if kernel_id not in self.kernel_cache:
            raise ValueError(f"Kernel {kernel_id} not loaded")

        return self.kernel_cache[kernel_id]

    def cleanup_all(self):
        """Nuclear option - clean everything"""
        for kernel_id in list(self.kernel_cache.keys()):
            self._unload_kernel(kernel_id)
        self.kernel_cache.clear()
        self.current_kernel_id = None
