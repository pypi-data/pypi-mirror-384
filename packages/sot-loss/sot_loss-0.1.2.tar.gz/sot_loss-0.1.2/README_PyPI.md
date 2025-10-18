# Spectral Optimal Transport Losses for PyTorch 


[![Paper (arXiv)](https://img.shields.io/badge/arXiv-2312.14507-b31b1b.svg)](https://arxiv.org/abs/2312.14507)

This repository contains an implementation of Spectral Optimal Transport (SOT) loss functions for PyTorch, with a pip-installable package `sot-loss`. SOT loss functions are differentiable spectral losses which compare the spectra of two audio signals using optimal transport principles. These loss functions can be used for training neural networks in audio processing tasks, particularly those involving DDSP. It can also be used more generally as a metric for audio signal comparison. 

## Installation

You can install the `sot-loss` package using pip:

```bash
pip install sot-loss
```

## Usage

The primary components of this package are the `Wasserstein1DLoss` and `MultiResolutionSOTLoss` classes, which can be used as PyTorch loss functions. Here is a basic example of how to use the `Wasserstein1DLoss`:

```python
import torch
from sot import Wasserstein1DLoss

# Create some dummy audio signals
x = torch.randn(4, 16000)
y = torch.randn(4, 16000)

# Initialize the SOT loss
sot_loss = Wasserstein1DLoss(transform='stft', fft_size=1024, hop_length=256)

# Compute the loss
loss = sot_loss(x, y)
print(loss)
```

## Citation


If you find our work useful or use it in your research, you can cite it using:

```bibtex
@inproceedings{torres2024unsupervised,
  title={Unsupervised harmonic parameter estimation using differentiable DSP and spectral optimal transport},
  author={Torres, Bernardo and Peeters, Geoffroy and Richard, Ga{\"e}l},
  booktitle={ICASSP 2024-2024 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
  pages={1176--1180},
  year={2024},
  organization={IEEE}
}

```
