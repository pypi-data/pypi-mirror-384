###########################################################################################
# Modified from ACEsuit/mace_descriptor
# Original Copyright (c) 2022 ACEsuit/mace_descriptor
# Licensed under the MIT License
###########################################################################################

import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

import numpy as np
import torch


def compute_mae(delta: np.ndarray) -> float:
    return np.mean(np.abs(delta)).item()


def compute_rel_mae(delta: np.ndarray, target_val: np.ndarray) -> float:
    target_norm = np.mean(np.abs(target_val))
    return np.mean(np.abs(delta)).item() / (target_norm + 1e-9) * 100


def compute_rmse(delta: np.ndarray) -> float:
    return np.sqrt(np.mean(np.square(delta))).item()


def compute_rel_rmse(delta: np.ndarray, target_val: np.ndarray) -> float:
    target_norm = np.sqrt(np.mean(np.square(target_val))).item()
    return np.sqrt(np.mean(np.square(delta))).item() / (target_norm + 1e-9) * 100


def compute_q95(delta: np.ndarray) -> float:
    return np.percentile(np.abs(delta), q=95)


def compute_c(delta: np.ndarray, eta: float) -> float:
    return np.mean(np.abs(delta) < eta).item()


def get_tag(name: str, seed: int) -> str:
    return f"{name}_run-{seed}"


def setup_logger(
    level: Union[int, str] = logging.INFO,
    tag: Optional[str] = None,
    directory: Optional[str] = None,
    rank: Optional[int] = 0,
):
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add filter for rank
    logger.addFilter(lambda _: rank == 0)

    # Create console handler
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if directory is not None and tag is not None:
        os.makedirs(name=directory, exist_ok=True)

        # Create file handler for non-debug logs
        main_log_path = os.path.join(directory, f"{tag}.log")
        fh_main = logging.FileHandler(main_log_path)
        fh_main.setLevel(level)
        fh_main.setFormatter(formatter)
        logger.addHandler(fh_main)

        # Create file handler for debug logs
        debug_log_path = os.path.join(directory, f"{tag}_debug.log")
        fh_debug = logging.FileHandler(debug_log_path)
        fh_debug.setLevel(logging.DEBUG)
        fh_debug.setFormatter(formatter)
        fh_debug.addFilter(lambda record: record.levelno >= logging.DEBUG)
        logger.addHandler(fh_debug)


class AtomicNumberTable:
    def __init__(self, zs: Sequence[int]):
        self.zs = zs

    def __len__(self) -> int:
        return len(self.zs)

    def __str__(self):
        return f"AtomicNumberTable: {tuple(s for s in self.zs)}"

    def index_to_z(self, index: int) -> int:
        return self.zs[index]

    def z_to_index(self, atomic_number: str) -> int:
        return self.zs.index(atomic_number)


def get_atomic_number_table_from_zs(zs: Iterable[int]) -> AtomicNumberTable:
    z_set = set()
    for z in zs:
        z_set.add(z)
    return AtomicNumberTable(sorted(list(z_set)))


def atomic_numbers_to_indices(
    atomic_numbers: np.ndarray, z_table: AtomicNumberTable
) -> np.ndarray:
    to_index_fn = np.vectorize(z_table.z_to_index)
    return to_index_fn(atomic_numbers)


def get_cache_dir() -> Path:
    # get cache dir from XDG_CACHE_HOME if set, otherwise appropriate default
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "mace_descriptor"


def numerical_descriptor_gradient(atoms, model, delta=1e-4):
    atoms = atoms.copy()
    n_atoms = len(atoms)

    desc_0 = model.get_descriptors(atoms)
    D = desc_0.shape[1]

    # 전체 forward/backward 구조 리스트
    displaced_atoms = []

    # mapping: (atom_idx, coord_idx) -> index in descriptor list
    index_map = {}

    counter = 0
    for i in range(n_atoms):
        for j in range(3):  # x, y, z
            # forward
            atoms_f = atoms.copy()
            atoms_f.positions[i, j] += delta
            displaced_atoms.append(atoms_f)
            index_map[(i, j, "f")] = counter
            counter += 1

            # backward
            atoms_b = atoms.copy()
            atoms_b.positions[i, j] -= delta
            displaced_atoms.append(atoms_b)
            index_map[(i, j, "b")] = counter
            counter += 1

    all_desc = model.get_descriptors_batch(displaced_atoms)
    grad = torch.empty((n_atoms, n_atoms, 3, D))

    for i in range(n_atoms):
        for j in range(3):
            f_idx = index_map[(i, j, "f")]
            b_idx = index_map[(i, j, "b")]

            desc_f = all_desc[f_idx]
            desc_b = all_desc[b_idx]

            grad[:, i, j, :] = (desc_f - desc_b) / (2 * delta)

    return grad
