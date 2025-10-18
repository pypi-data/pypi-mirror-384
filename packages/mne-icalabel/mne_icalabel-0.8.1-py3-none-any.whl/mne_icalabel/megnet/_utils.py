from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _make_head_outlines(sphere: NDArray, pos: NDArray, clip_origin: tuple) -> dict:
    """Generate head outlines for topomap plotting.

    This is a modified version of mne.viz.topomap._make_head_outlines.
    The difference between this function and the original one is that
    head_x and head_y here are scaled by a factor of 1.01 to make topomap
    fit the 120x120 pixel size.
    Also, removed the ear and nose outlines, not needed in MEGnet.

    Parameters
    ----------
    sphere : NDArray
        The sphere parameters (x, y, z, radius).
    pos : NDArray
        The 2D sensor positions.
    clip_origin : tuple
        The origin of the clipping circle.

    Returns
    -------
    dict
        Dictionary containing the head outlines and mask positions.
    """
    x, y, _, radius = sphere
    ll = np.linspace(0, 2 * np.pi, 101)
    head_x = np.cos(ll) * radius * 1.01 + x
    head_y = np.sin(ll) * radius * 1.01 + y

    mask_scale = max(1.0, np.linalg.norm(pos, axis=1).max() * 1.01 / radius)
    clip_radius = radius * mask_scale

    outlines_dict = {
        "head": (head_x, head_y),
        "mask_pos": (mask_scale * head_x, mask_scale * head_y),
        "clip_radius": (clip_radius,) * 2,
        "clip_origin": clip_origin,
    }
    return outlines_dict
