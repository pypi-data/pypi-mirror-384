
from setuptools import setup, find_packages
import os

# Get the directory of the setup.py file
here = os.path.abspath(os.path.dirname(__file__))

# Read the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='FractalNet',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'torch',
        'torchvision',
        'matplotlib',

    ],
    author='Aleksandar Kitipov',
    author_email='aeksandar.kitipov@gmail.com',
    description='A poetic and technical library inspired by fractal geometry, neural networks, and visual art.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/AlexKitipov/FractalNet--0.1.1.ipynb',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Graphics',
    ],
    python_requires='>=3.8',
)
