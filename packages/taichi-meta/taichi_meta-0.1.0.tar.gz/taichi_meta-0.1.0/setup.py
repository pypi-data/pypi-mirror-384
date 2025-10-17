from setuptools import setup

setup(
    name='taichi-meta',
    version='0.1.0',
    description='A Simple Taichi Addon that allows you to compile AND recompile kernels directly from strings.',
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
