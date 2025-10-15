"""Backwards-compatible import facade for :mod:`whale.io.volume`."""

from whale.io.volume import (
    ensure_nibabel_for_real_data,
    generate_synthetic_volume,
    load_mri_volume,
    volume_to_point_cloud,
)

__all__ = [
    "ensure_nibabel_for_real_data",
    "generate_synthetic_volume",
    "load_mri_volume",
    "volume_to_point_cloud",
]
