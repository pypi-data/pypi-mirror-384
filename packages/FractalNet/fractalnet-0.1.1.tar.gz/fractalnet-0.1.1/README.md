
# FractalNet Library

## Concept and Applications

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

## 🐛 Version History

### v0.1.0
- Initial release with core fractal architecture
- Included unintended dependency: `turtle`, causing import errors in some environments

### v0.1.1
- Removed `turtle` from dependencies
- Improved stability and compatibility across platforms
- Cleaned up setup and documentation

## 🚀 Installation

```bash
pip install fractalnet

This is a library for building neural networks inspired by fractal structures.
