###########################################################################################
# Modified from ACEsuit/mace_descriptor
# Original Copyright (c) 2022 ACEsuit/mace_descriptor
# Licensed under the MIT License
###########################################################################################

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.distributed
from e3nn import o3

from mace_descriptor import data


@dataclasses.dataclass
class SubsetCollection:
    train: data.Configurations
    valid: data.Configurations
    tests: List[Tuple[str, data.Configurations]]


def log_dataset_contents(dataset: data.Configurations, dataset_name: str) -> None:
    log_string = f"{dataset_name} ["
    for prop_name in dataset[0].properties.keys():
        if prop_name == "dipole":
            log_string += f"{prop_name} components: {int(np.sum([np.sum(config.property_weights[prop_name]) for config in dataset]))}, "
        else:
            log_string += f"{prop_name}: {int(np.sum([config.property_weights[prop_name] for config in dataset]))}, "
    log_string = log_string[:-2] + "]"
    logging.info(log_string)


def extract_config_mace_model(model: torch.nn.Module) -> Dict[str, Any]:
    if model.__class__.__name__ not in ["ScaleShiftMACE", "MACELES"]:
        return {"error": "Model is not a ScaleShiftMACE or MACELES model"}

    def radial_to_name(radial_type):
        if radial_type == "BesselBasis":
            return "bessel"
        if radial_type == "GaussianBasis":
            return "gaussian"
        if radial_type == "ChebychevBasis":
            return "chebyshev"
        return radial_type

    def radial_to_transform(radial):
        if not hasattr(radial, "distance_transform"):
            return None
        if radial.distance_transform.__class__.__name__ == "AgnesiTransform":
            return "Agnesi"
        if radial.distance_transform.__class__.__name__ == "SoftTransform":
            return "Soft"
        return radial.distance_transform.__class__.__name__

    scale = model.scale_shift.scale
    shift = model.scale_shift.shift
    heads = model.heads if hasattr(model, "heads") else ["default"]
    model_mlp_irreps = (
        o3.Irreps(str(model.readouts[-1].hidden_irreps))
        if model.num_interactions.item() > 1
        else 1
    )
    try:
        correlation = (
            len(model.products[0].symmetric_contractions.contractions[0].weights) + 1
        )
    except AttributeError:
        correlation = model.products[0].symmetric_contractions.contraction_degree
    config = {
        "r_max": model.r_max.item(),
        "num_bessel": len(model.radial_embedding.bessel_fn.bessel_weights),
        "num_polynomial_cutoff": model.radial_embedding.cutoff_fn.p.item(),
        "max_ell": model.spherical_harmonics._lmax,  # pylint: disable=protected-access
        "interaction_cls": model.interactions[-1].__class__,
        "interaction_cls_first": model.interactions[0].__class__,
        "num_interactions": model.num_interactions.item(),
        "num_elements": len(model.atomic_numbers),
        "hidden_irreps": o3.Irreps(str(model.products[0].linear.irreps_out)),
        "edge_irreps": model.edge_irreps if hasattr(model, "edge_irreps") else None,
        "MLP_irreps": (
            o3.Irreps(f"{model_mlp_irreps.count((0, 1)) // len(heads)}x0e")
            if model.num_interactions.item() > 1
            else 1
        ),
        "gate": (
            model.readouts[-1]  # pylint: disable=protected-access
            .non_linearity._modules["acts"][0]
            .f
            if model.num_interactions.item() > 1
            else None
        ),
        "use_reduced_cg": (
            model.use_reduced_cg if hasattr(model, "use_reduced_cg") else False
        ),
        "use_so3": model.use_so3 if hasattr(model, "use_so3") else False,
        "use_agnostic_product": (
            model.use_agnostic_product
            if hasattr(model, "use_agnostic_product")
            else False
        ),
        "use_last_readout_only": (
            model.use_last_readout_only
            if hasattr(model, "use_last_readout_only")
            else False
        ),
        "use_embedding_readout": (hasattr(model, "embedding_readout")),
        "readout_cls": model.readouts[-1].__class__,
        "cueq_config": model.cueq_config if hasattr(model, "cueq_config") else None,
        "atomic_energies": model.atomic_energies_fn.atomic_energies.cpu().numpy(),
        "avg_num_neighbors": model.interactions[0].avg_num_neighbors,
        "atomic_numbers": model.atomic_numbers,
        "correlation": correlation,
        "radial_type": radial_to_name(
            model.radial_embedding.bessel_fn.__class__.__name__
        ),
        "embedding_specs": (
            model.embedding_specs if hasattr(model, "embedding_specs") else None
        ),
        "apply_cutoff": model.apply_cutoff if hasattr(model, "apply_cutoff") else True,
        "radial_MLP": model.interactions[0].conv_tp_weights.hs[1:-1],
        "pair_repulsion": hasattr(model, "pair_repulsion_fn"),
        "distance_transform": radial_to_transform(model.radial_embedding),
        "atomic_inter_scale": scale.cpu().numpy(),
        "atomic_inter_shift": shift.cpu().numpy(),
        "heads": heads,
    }
    if model.__class__.__name__ == "AtomicDielectricMACE":
        config["use_polarizability"] = model.use_polarizability
        config["only_dipole"] = False  # model.only_dipole
        config["gate"] = torch.nn.functional.silu
    return config


def extract_load(f: str, map_location: str = "cpu") -> torch.nn.Module:
    return extract_model(
        torch.load(f=f, map_location=map_location), map_location=map_location
    )


def remove_pt_head(
    model: torch.nn.Module, head_to_keep: Optional[str] = None
) -> torch.nn.Module:
    """Converts a multihead MACE model to a single head model by removing the pretraining head.

    Args:
        model (ScaleShiftMACE): The multihead MACE model to convert
        head_to_keep (Optional[str]): The name of the head to keep. If None, keeps the first non-PT head.

    Returns:
        ScaleShiftMACE: A new MACE model with only the specified head

    Raises:
        ValueError: If the model is not a multihead model or if the specified head is not found
    """
    if not hasattr(model, "heads") or len(model.heads) <= 1:
        raise ValueError("Model must be a multihead model with more than one head")

    # Get index of head to keep
    if head_to_keep is None:
        # Find first non-PT head
        try:
            head_idx = next(i for i, h in enumerate(model.heads) if h != "pt_head")
        except StopIteration as e:
            raise ValueError("No non-PT head found in model") from e
    else:
        try:
            head_idx = model.heads.index(head_to_keep)
        except ValueError as e:
            raise ValueError(f"Head {head_to_keep} not found in model") from e

    # Extract config and modify for single head
    model_config = extract_config_mace_model(model)
    model_config["heads"] = [model.heads[head_idx]]
    model_config["atomic_energies"] = (
        model.atomic_energies_fn.atomic_energies[head_idx]
        .unsqueeze(0)
        .detach()
        .cpu()
        .numpy()
    )
    model_config["atomic_inter_scale"] = model.scale_shift.scale[head_idx].item()
    model_config["atomic_inter_shift"] = model.scale_shift.shift[head_idx].item()
    mlp_count_irreps = model_config["MLP_irreps"].count((0, 1))
    # model_config["MLP_irreps"] = o3.Irreps(f"{mlp_count_irreps}x0e")

    new_model = model.__class__(**model_config)
    state_dict = model.state_dict()
    new_state_dict = {}

    for name, param in state_dict.items():
        if "atomic_energies" in name:
            new_state_dict[name] = param[head_idx : head_idx + 1]
        elif "scale" in name or "shift" in name:
            new_state_dict[name] = param[head_idx : head_idx + 1]
        elif "readouts" in name:
            channels_per_head = param.shape[0] // len(model.heads)
            start_idx = head_idx * channels_per_head
            end_idx = start_idx + channels_per_head
            if "linear_2.weight" in name:
                end_idx = start_idx + channels_per_head // 2
            # if (
            #     "readouts.0.linear.weight" in name
            #     or "readouts.1.linear_2.weight" in name
            # ):
            #     new_state_dict[name] = param[start_idx:end_idx] / (
            #         len(model.heads) ** 0.5
            #     )
            if "readouts.0.linear.weight" in name:
                new_state_dict[name] = param.reshape(-1, len(model.heads))[
                    :, head_idx
                ].flatten()
            elif "readouts.1.linear_1.weight" in name:
                new_state_dict[name] = param.reshape(
                    -1, len(model.heads), mlp_count_irreps
                )[:, head_idx, :].flatten()
            elif "readouts.1.linear_2.weight" in name:
                new_state_dict[name] = param.reshape(
                    len(model.heads), -1, len(model.heads)
                )[head_idx, :, head_idx].flatten() / (len(model.heads) ** 0.5)
            else:
                new_state_dict[name] = param[start_idx:end_idx]

        else:
            new_state_dict[name] = param

    # Load state dict into new model
    new_model.load_state_dict(new_state_dict)

    return new_model


def extract_model(model: torch.nn.Module, map_location: str = "cpu") -> torch.nn.Module:
    model_copy = model.__class__(**extract_config_mace_model(model))
    model_copy.load_state_dict(model.state_dict())
    return model_copy.to(map_location)
