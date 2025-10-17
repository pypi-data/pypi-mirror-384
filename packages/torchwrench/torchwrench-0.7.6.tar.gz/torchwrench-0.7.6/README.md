# torchwrench

<center>

<a href="https://www.python.org/">
    <img alt="Python" src="https://img.shields.io/badge/-Python 3.8+-blue?style=for-the-badge&logo=python&logoColor=white">
</a>
<a href="https://github.com/Labbeti/torchwrench/actions">
    <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/Labbeti/torchwrench/test.yaml?branch=main&style=for-the-badge&logo=github">
</a>
<a href='https://torchwrench.readthedocs.io/'>
    <img src='https://readthedocs.org/projects/torchwrench/badge/?version=stable&style=for-the-badge' alt='Documentation Status' />
</a>
<a href="https://pytorch.org/get-started/locally/">
    <img alt="PyTorch" src="https://img.shields.io/badge/-PyTorch 1.10+-ee4c2c?style=for-the-badge&logo=pytorch&logoColor=white">
</a>

Collection of functions and modules to help development in PyTorch.

</center>


## Installation

With pip:
```bash
pip install torchwrench
```

With uv:
```bash
uv add torchwrench
```

The main requirement is **[PyTorch](https://pytorch.org/)**.

To check if the package is installed and show the package version, you can use the following command in your terminal:
```bash
torchwrench-info
```

This library has been tested on all Python versions **3.8 - 3.13**, all PyTorch versions **1.10 - 2.6**, and on **Linux, Mac and Windows** systems.

## Examples

`torchwrench` functions and modules can be used like `torch` ones. The default acronym for `torchwrench` is `tw`.

### Label conversions
Supports **multiclass** labels conversions between probabilities, classes indices, classes names and onehot encoding.

```python
import torchwrench as tw

probs = tw.as_tensor([[0.9, 0.1], [0.4, 0.6]])
names = tw.probs_to_name(probs, idx_to_name={0: "Cat", 1: "Dog"})
# ["Cat", "Dog"]
```

This package also supports **multilabel** labels conversions between probabilities, classes multi-indices, classes multi-names and multihot encoding.

```python
import torchwrench as tw

multihot = tw.as_tensor([[1, 0, 0], [0, 1, 1], [0, 0, 0]])
indices = tw.multihot_to_indices(multihot)
# [[0], [1, 2], []]
```

Finally, this packages includes the **powerset multilabel** conversions :

```python
import torchwrench as tw

multihot = tw.as_tensor([[1, 0, 0], [0, 1, 1], [0, 0, 0]])
indices = tw.multilabel_to_powerset(multihot, num_classes=3, max_set_size=2)
# tensor([[0, 1, 0, 0, 0, 0, 0],
#         [0, 0, 0, 0, 0, 0, 1],
#         [1, 0, 0, 0, 0, 0, 0]])
```

### Typing

Typing with number of dimensions :

```python
import torchwrench as tw

x1 = tw.as_tensor([1, 2])
print(isinstance(x1, tw.Tensor2D))  # False
x2 = tw.as_tensor([[1, 2], [3, 4]])
print(isinstance(x2, tw.Tensor2D))  # True
```

Typing with tensor dtype :

```python
import torchwrench as tw

x1 = tw.as_tensor([1, 2], dtype=tw.int)
print(isinstance(x1, tw.SignedIntegerTensor))  # True

x2 = tw.as_tensor([1, 2], dtype=tw.long)
print(isinstance(x2, tw.SignedIntegerTensor1D))  # True

x3 = tw.as_tensor([1, 2], dtype=tw.float)
print(isinstance(x3, tw.SignedIntegerTensor))  # False
```

### Padding & cropping

Pad a specific dimension :

```python
import torchwrench as tw

x = tw.rand(10, 3, 1)
padded = tw.pad_dim(x, target_length=5, dim=1, pad_value=-1)
# x2 has shape (10, 5, 1), padded with -1
```

Pad nested list of tensors to a single one :

```python
import torchwrench as tw

tensors = [tw.rand(10, 2), [tw.rand(3)] * 5, tw.rand(0, 5)]
padded = tw.pad_and_stack_rec(tensors, pad_value=0)
# padded has shape (3, 10, 5), padded with 0
```

Remove values at a specific dimension :

```python
import torchwrench as tw

x = tw.rand(10, 5, 3)
cropped = tw.crop_dim(x, dim=1, target_length=2)
# cropped has shape (10, 2, 3)
```

### Masking

```python
import torchwrench as tw

x = tw.as_tensor([3, 1, 2])
mask = tw.lengths_to_non_pad_mask(x, max_len=4)
# Each row i contains x[i] True values for non-padding mask
# tensor([[True, True, True, False],
#         [True, False, False, False],
#         [True, True, False, False]])
```

```python
import torchwrench as tw

x = tw.as_tensor([1, 2, 3, 4])
mask = tw.as_tensor([True, True, False, False])
result = tw.masked_mean(x, mask)
# result contains the mean of the values marked as True: 1.5
```

### Others tensors manipulations!

```python
import torchwrench as tw

x = tw.as_tensor([1, 2, 3, 4])
result = tw.insert_at_indices(x, indices=[0, 2], values=5)
# result contains tensor with inserted values: tensor([5, 1, 2, 5, 3, 4])
```

```python
import torchwrench as tw

perm = tw.randperm(10)
inv_perm = tw.get_inverse_perm(perm)

x1 = tw.rand(10)
x2 = x1[perm]
x3 = x2[inv_perm]
# inv_perm are indices that allow us to get x3 from x2, i.e. x1 == x3 here
```

### Extra: pre-compute datasets to HDF files

Here is an example of pre-computing spectrograms of torchaudio `SPEECHCOMMANDS` dataset, using `pack_dataset` function:

```python
from torchaudio.datasets import SPEECHCOMMANDS
from torchaudio.transforms import Spectrogram
from torchwrench import nn
from torchwrench.extras.hdf import pack_to_hdf

speech_commands_root = "path/to/speech_commands"
packed_root = "path/to/packed_dataset.hdf"

dataset = SPEECHCOMMANDS(speech_commands_root, download=True, subset="validation")
# dataset[0] is a tuple, contains waveform and other metadata

class MyTransform(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.spectrogram_extractor = Spectrogram()

    def forward(self, item):
        waveform = item[0]
        spectrogram = self.spectrogram_extractor(waveform)
        return (spectrogram,) + item[1:]

pack_to_hdf(dataset, packed_root, MyTransform())
```

Then you can load the pre-computed dataset using `HDFDataset`:
```python
from torchwrench.extras.hdf import HDFDataset

packed_root = "path/to/packed_dataset.hdf"
packed_dataset = HDFDataset(packed_root)
packed_dataset[0]  # == first transformed item, i.e. transform(dataset[0])
```

## Contact
Maintainer:
- [Étienne Labbé](https://labbeti.github.io/) "Labbeti": labbeti.pub@gmail.com
