from typing import Union

import numpy as np
import torch


def get_margin(patch_size):
    """
    Determine the margin length that cannot be the central point of the patch of which cannot fit the size of patch_size.
    Return a len(patch_size) X 2 matrix with left and right (before and after, top and bottom) margin size.

    Args:
        patch_size (sequence):

    Returns:

    """
    if not isinstance(patch_size, np.ndarray):
        patch_size = np.asarray(patch_size)

    return np.where(patch_size % 2 == 1, np.asarray([patch_size // 2, patch_size // 2]),
                    np.asarray([patch_size / 2 - 1, patch_size / 2])).astype(np.int16).T


def get_non_margin_region(image_shape: Union[tuple, list], patch_size: Union[tuple, list]):
    """
    Build a mask that cover the area which can be view as the central point of the patch with the size of
    patch_size. Mask the central area that can be extracted. Left the margin area.

    Args:
        image_shape (sequence):
        patch_size (sequence):

    Returns:

    """
    assert len(image_shape) == len(patch_size)
    margin = get_margin(patch_size)
    mask = np.zeros(image_shape, dtype=bool)
    mask[tuple([slice(j[0], i - j[1]) for i, j in zip(image_shape, margin)])] = 1
    return mask


def encode_one_hot(data):
    shape = data.shape
    data = data.flatten().astype(np.uint8)
    num_classes = int(data.max() + 1)

    result = np.zeros((data.size, num_classes), dtype=bool)
    index = np.arange(data.size)
    result[index, data] = 1
    result_shape = tuple(list(shape) + [num_classes])
    if result.shape != result_shape:
        result = result.reshape(result_shape)

    # move category axis to the first. [C, ...]
    result = np.moveaxis(result, -1, 0)
    return result


def central_crop(data: Union[np.ndarray, torch.Tensor], center, shape):
    """
    Crop patch with the shape from data at the central coordinate.

    Args:
        data (numpy.ndarray or torch.Tensor):
        center (sequence):
        shape (sequence):

    Returns:

    """
    assert len(data.shape) >= len(shape) == len(center)
    center = np.asarray(center)
    margin = get_margin(shape)[:, 0]
    # coordinate is the corner coordinate responding to the central.
    coordinate = center - margin
    assert (coordinate >= 0).all(), "center {} or shape {} error".format(center, shape)
    cropped = crop_patch(data, coordinate, shape)
    return cropped


def crop_patch(data: Union[np.ndarray, torch.Tensor], coordinate, patch_size):
    """
    Crop patch from `data` at the left/superior/anterior `coordinate`. If data has larger dimensions than shape
    dimensions N, the last N dimensions will be cropped.

    Args:
        data  (numpy.ndarray or torch.Tensor):
        coordinate (sequence):
        patch_size (sequence):

    Returns:

    """
    data_shape = data.shape
    assert len(data_shape) >= len(coordinate) == len(patch_size)
    end = coordinate + patch_size
    slice_sequence = [slice(i, j) for i, j in zip(coordinate, end)]
    # append the extra dimensions, batch/channel...
    slice_sequence = [slice(None)] * (len(data_shape) - len(end)) + slice_sequence
    cropped = data[tuple(slice_sequence)]
    return cropped
