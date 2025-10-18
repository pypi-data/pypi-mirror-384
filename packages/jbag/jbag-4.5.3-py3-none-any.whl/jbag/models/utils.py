from typing import Callable

import torch.nn as nn
from torch.nn.modules.conv import _ConvNd


def get_conv_op(dims):
    match dims:
        case 1:
            return nn.Conv1d
        case 2:
            return nn.Conv2d
        case 3:
            return nn.Conv3d
        case _:
            raise ValueError()


def get_norm_op(op_name, dims):
    match op_name:
        case "InstanceNorm":
            match dims:
                case 2:
                    return nn.InstanceNorm2d
        case "BatchNorm":
            match dims:
                case 2:
                    return nn.BatchNorm2d
    return None


def get_act(op_name):
    match op_name:
        case "leaky_relu":
            return nn.LeakyReLU
        case "relu":
            return nn.ReLU
    return None


def get_matching_conv_transpose_op(conv_op: Callable[..., _ConvNd]):
    match conv_op:
        case nn.Conv1d:
            return nn.ConvTranspose1d
        case nn.Conv2d:
            return nn.ConvTranspose2d
        case nn.Conv3d:
            return nn.ConvTranspose3d
        case _:
            raise ValueError(f"Unknown conv op {conv_op}")


def get_conv_dimensions(conv_op: Callable[..., _ConvNd]):
    match conv_op:
        case nn.Conv1d:
            return 1
        case nn.Conv2d:
            return 2
        case nn.Conv3d:
            return 3
        case _:
            raise ValueError(f"Unknown conv op {conv_op}")
