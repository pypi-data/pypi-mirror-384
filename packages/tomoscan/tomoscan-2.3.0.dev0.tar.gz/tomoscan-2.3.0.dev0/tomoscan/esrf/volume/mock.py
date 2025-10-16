# coding: utf-8
"""module to mock volume"""

from __future__ import annotations

from typing import Sized

import numpy
from silx.image.phantomgenerator import PhantomGenerator
from enum import Enum

__all__ = ["Scene", "create_volume"]


class Scene(Enum):
    SHEPP_LOGAN = "Shepp-Logan"


def create_volume(
    frame_dims: int | tuple, z_size: int, scene: Scene = Scene.SHEPP_LOGAN
) -> numpy.ndarray:
    """
    create a numpy array of the requested scheme for a total of frames_dimes*z_size elements

    :param tuple frame_dims: 2d tuple of frame dimensions
    :param z_size: number of elements on the volume on z axis
    :param Scene scene: scene to compose
    """
    scene = Scene(scene)
    if not isinstance(z_size, int):
        raise TypeError(
            f"z_size is expected to be an instance of int not {type(z_size)}"
        )
    if scene is Scene.SHEPP_LOGAN:
        if isinstance(frame_dims, Sized):
            if not len(frame_dims) == 2:
                raise ValueError(
                    f"frame_dims is expected to be an integer or a list of two integers. Not {frame_dims}"
                )
            if frame_dims[0] != frame_dims[1]:
                raise ValueError(
                    f"{scene} only handle square frame. Frame width and height should be the same"
                )
            else:
                dim = frame_dims[0]
        elif isinstance(frame_dims, int):
            dim = frame_dims
        else:
            raise TypeError(
                f"frame_dims is expected to be a list of two integers or an integer. Not {frame_dims}"
            )
        return numpy.asarray(
            [PhantomGenerator.get2DPhantomSheppLogan(dim) * 10000.0] * z_size
        )
    else:
        raise NotImplementedError
