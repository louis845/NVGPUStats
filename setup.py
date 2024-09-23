from setuptools import setup, find_packages

setup(
    name='NVGPUStats',
    version='0.4.0',
    description='A Python interface for monitoring installed NVIDIA GPUs',
    author='Louis, Chau Yu Hei',
    author_email='louis321yh@gmail.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
    ],
    entry_points={
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: Unix',
    ],
)