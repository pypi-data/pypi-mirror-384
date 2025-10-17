from setuptools import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='taichi-meta',
    version='0.1.1',
    description='A Simple Taichi Addon that allows you to compile AND recompile kernels directly from strings.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pythagorasDesaster/taichi-meta',
    author='Thomas Kirchner',
    author_email='thomas.kirchner5@web.de',
    license='MIT License',
    packages=['taichi_meta'],
    install_requires=['taichi>=1.0.0',
                      ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ],
)
