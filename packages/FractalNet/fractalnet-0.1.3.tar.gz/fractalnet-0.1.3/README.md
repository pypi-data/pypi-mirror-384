# FractalNet-0.1.3
FractalNet 0.1.3 е библиотека за невронни мрежи, вдъхновена от фракталната геометрия. Включва 7 генератора, модулна архитектура, и готови PyTorch датасети за обучение върху фрактални изображения, сигнали и космически структури. Лека, поетична и разширяема.

🐛 Version History
v0.1.0
Initial release with core fractal architecture

Included unintended dependency: turtle, causing import errors in some environments

v0.1.1
Removed turtle from dependencies

Improved stability and compatibility across platforms

Cleaned up setup and documentation

v0.1.3
Added 7 fractal generators: Koch, Sierpinski, L-System, Dragon Curve, Mandelbrot, Julia Set, Lindenmayer

Included PyTorch Dataset classes for each fractal form

Introduced ReducedFractalDataset for efficient training

Improved project structure: clearly separated modules (ml/, fractals/, datasets/)

Finalized __init__.py with clean imports and __all__ definition

Ready for PyPI publication as version 0.1.3

# FractalNet Library

## 🧠 Concept and Applications

FractalNet is a lightweight PyTorch-based library for building neural networks inspired by fractal geometry. It uses recursive block structures to simulate depth and variation, enabling efficient learning across multiple scales.

Originally designed for image classification, FractalNet has evolved into a flexible framework for pattern recognition in various domains — including financial signals, audio analysis, and even cosmic wave detection.

## ⚙️ Features

- **Fractal Blocks**: Recursive architecture with adjustable depth and branching
- **Stem Layer**: Initial convolutional layer for input normalization
- **Adaptive Classifier**: Final layer that adapts to task-specific output dimensions
- **Modular Design**: Easy to extend for 1D, 2D, or even multimodal inputs
- **Training Utilities**: Includes training loop, evaluation metrics, and visualization tools

## 🧠 Applications

- Image classification (CIFAR-10, custom datasets)
- Financial time series pattern recognition
- Audio signal classification
- Medical image diagnostics
- Gravitational wave pattern analysis

## 📦 Import and Usage

After installing the library (`pip install fractalnet`), you can import and use its components as follows:

```python
from FractalNet.ml.fractal_layers import FractalNet as FractalNetModel
from FractalNet.fractals.koch import KochDataset
from FractalNet.fractals.sierpinski import SierpinskiDataset
from FractalNet.fractals.l_system import LSystemDataset
from FractalNet.fractals.dragon import DragonDataset
from FractalNet.fractals.mandelbrot import MandelbrotDataset
from FractalNet.fractals.julia import JuliaDataset
from FractalNet.fractals.lindenmayer import LindenmayerDataset
from FractalNet.datasets.reduced import ReducedFractalDataset

model = FractalNetModel()
dataset = KochDataset(num_samples=10)

print(model)
print(f"Number of images: {len(dataset)}")

