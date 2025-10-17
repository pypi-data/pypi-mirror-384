# mace-descriptor

A lightweight fork of the [MACE](https://github.com/ACEsuit/mace), focused exclusively on **descriptor extraction** using pretrained foundation models.

This package strips away all training, logging, CLI, and experimental tracking code from MACE, providing a fast generation of pretrained MACE descriptor.

---

## 🔧 Installation

```bash
pip install mace-descriptor
```

---

## 🚀 Quick Start

```python
from mace_descriptor.calculators import mace_mp
from ase.build import molecule

atoms = molecule("CH4")
calc = mace_mp(model="small")
desc = calc.get_descriptors(atoms)  
# shape: (n_atoms, descriptor_dim)
```

To compute **numerical gradients** of the MACE descriptors with respect to atomic positions:

```python
from mace_descriptor.tools import numerical_descriptor_gradient

grad = numerical_descriptor_gradient(atoms, calc)
# shape: (n_atoms, n_atoms, 3, descriptor_dim)
```

---

## 📚 Reference Models

mace-descriptor uses pretrained MACE foundation models such as:

* **MACE-MP-0a** (Materials Project DFT data)
* **MACE-OFF23** (Organic force fields)

For more, visit: [https://github.com/ACEsuit/mace-foundations](https://github.com/ACEsuit/mace-foundations)

---

## 📖 Citing MACE

If you use this package or the underlying pretrained models, please cite the original MACE paper:

```bibtex
@inproceedings{Batatia2022mace,
  title={{MACE}: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields},
  author={Ilyes Batatia and David Peter Kovacs and Gregor N. C. Simm and Christoph Ortner and Gabor Csanyi},
  booktitle={Advances in Neural Information Processing Systems},
  editor={Alice H. Oh and Alekh Agarwal and Danielle Belgrave and Kyunghyun Cho},
  year={2022},
  url={https://openreview.net/forum?id=YPpSngE-ZU}
}

@misc{Batatia2022Design,
  title = {The Design Space of E(3)-Equivariant Atom-Centered Interatomic Potentials},
  author = {Batatia, Ilyes and Batzner, Simon and Kov{\'a}cs, D{\'a}vid P{\'e}ter and Musaelian, Albert and Simm, Gregor N. C. and Drautz, Ralf and Ortner, Christoph and Kozinsky, Boris and Cs{\'a}nyi, G{\'a}bor},
  year = {2022},
  number = {arXiv:2205.06643},
  eprint = {2205.06643},
  eprinttype = {arxiv},
  doi = {10.48550/arXiv.2205.06643},
  archiveprefix = {arXiv}
 }
```

---

## 📄 License

MIT License (c) 2022 ACEsuit/mace, modified by In Won Yeu 2025

This is a reduced version focused solely on descriptor extraction. See `LICENSE.md` for details.
