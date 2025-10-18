import json
import os.path
from base64 import b64encode, b64decode
from collections import OrderedDict
from typing import Union, Optional

import nibabel as nib
import numpy as np
import pandas as pd
from numpy.lib.format import dtype_to_descr, descr_to_dtype
from openpyxl import load_workbook
from pydicom import dcmread
from scipy.io import loadmat
from scipy.io import savemat

from jbag.dicom.dicom_tags import Rescale_Slope, Rescale_Intercept, Pixel_Padding_Value, Smallest_Image_Pixel_Value
from jbag import logger


def read_mat(input_file, key="scene"):
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")

    data = loadmat(input_file)[key]
    return data


def save_mat(output_file, data, key="scene"):
    ensure_output_file_dir_existence(output_file)
    savemat(output_file, {key: data})


def read_file_to_list(input_file):
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")

    with open(input_file, "r") as input_file:
        return [each.strip("\n") for each in input_file.readlines()]


def save_list_to_file(output_file, data_list):
    """
    Writes each item from a list to a new line in a file.

    Args:
        output_file (str):
        data_list (list):

    Returns:

    """
    ensure_output_file_dir_existence(output_file)
    with open(output_file, "w") as file:
        for i in range(len(data_list)):
            file.write(str(data_list[i]))
            if i != len(data_list) - 1:
                file.write("\n")


def save_nifti(output_file,
               data,
               voxel_spacing: Optional[Union[float, list[float], tuple[float, ...]]] = None,
               orientation="LPI"):
    """
    Save improc with nii format.

    Args:
        output_file (str):
        data (numpy.ndarray):
        voxel_spacing (sequence or None, optional, default=None): `tuple(x, y, z)`. Voxel spacing of each axis. If None,
            make `voxel_spacing` as `(1.0, 1.0, 1.0)`.
        orientation (str, optional, default="LPI"): "LPI" | "ARI". LPI: Left-Posterior-Inferior;
            ARI: Anterior-Right-Inferior.

    Returns:

    """
    if voxel_spacing is None:
        voxel_spacing = (1.0, 1.0, 1.0)  # replace this with your desired voxel spacing in millimeters

    match orientation:
        case "LPI":
            affine_matrix = np.diag(list(voxel_spacing) + [1.0])
        case "ARI":
            # calculate the affine matrix based on the desired voxel spacing and ARI orientation
            affine_matrix = np.array([
                [0, -voxel_spacing[0], 0, 0],
                [-voxel_spacing[1], 0, 0, 0],
                [0, 0, voxel_spacing[2], 0],
                [0, 0, 0, 1]
            ])
        case _:
            raise ValueError(f"Unsupported orientation {orientation}.")

    # create a NIfTI improc object

    ensure_output_file_dir_existence(output_file)
    nii_img = nib.Nifti1Image(data, affine=affine_matrix)
    nib.save(nii_img, output_file)


def read_dicom_series(input_dir: str, use_HU: bool = True, replace_padding: bool = True):
    """
    Read DICOM improc. If `use_hu` is True, the improc in HU will be returned, in which the value is rescale by `value * rescale_slope + rescale_intercept`.

    Args:
        input_dir (str):
        use_HU (boo, optional, default=True): if True, rescale the improc in HU.
        replace_padding (bool, optional, default=True): if True, rescale the padding value of out-of-field (DICOM tag: (0028,0120)) if exists.
        The padding value will be replaced by the value of Smallest Image Pixel Value (DICOM tag: 0028, 0106) if the tag exists.
        Otherwise, the padding value will be replaced by the smallest value in the pixel data except the padding value.

    Returns:

    """

    if not os.path.exists(input_dir):
        raise ValueError(f"{input_dir} does not exist.")

    instances = []
    for each in os.listdir(input_dir):
        if each.endswith(".dcm"):
            instances.append(each)

    instances.sort()
    images = []
    for slice_file_name in instances:
        slice_file = os.path.join(input_dir, slice_file_name)
        ds = dcmread(slice_file)
        slope = 1
        intercept = 0
        if use_HU:
            if Rescale_Slope in ds:
                slope = ds[Rescale_Slope].value
            else:
                logger.warning(f"Dicom file {slice_file} does not contain rescale slope. Set rescale slope to 1.")
            if Rescale_Intercept in ds:
                intercept = ds[Rescale_Intercept].value
            else:
                logger.warning(
                    f"Dicom file {slice_file} does not contain rescale intercept. Set rescale intercept to 0.")

        if "PixelData" in ds:
            pixel_data = ds.pixel_array
            if not isinstance(pixel_data, np.ndarray):
                pixel_data = np.array(pixel_data)
            pixel_data = pixel_data.astype(int)

            if replace_padding:
                if Pixel_Padding_Value in ds:
                    padding_value = ds[Pixel_Padding_Value].value
                    positions = np.where(pixel_data == padding_value)

                    if Smallest_Image_Pixel_Value in ds:
                        smallest = ds[Smallest_Image_Pixel_Value].value
                    else:
                        unique_sorted_arr = np.unique(pixel_data)
                        smallest = unique_sorted_arr[1]

                    pixel_data[positions] = smallest

            pixel_data = pixel_data * slope + intercept
            images.append(pixel_data)
        else:
            logger.warning(f"Dicom file {slice_file} does not contain pixel data.")

    image = np.stack(images).astype(int)
    return image


# JSON
def np_object_hook(dct):
    """
    Convert JSON list or scalar to numpy.

    Args:
        dct (mapping):

    Returns:

    """
    if "__ndarray__" in dct:
        shape = dct["shape"]
        dtype = descr_to_dtype(dct["dtype"])
        if shape:
            order = "C" if dct["Corder"] else "F"
            if dct["base64"]:
                np_obj = np.frombuffer(b64decode(dct["__ndarray__"]), dtype=dtype)
                np_obj = np_obj.copy(order=order)
            else:
                np_obj = np.asarray(dct["__ndarray__"], dtype=dtype, order=order)
            return np_obj.reshape(shape)

        if dct["base64"]:
            np_obj = np.frombuffer(b64decode(dct["__ndarray__"]), dtype=dtype)[0]
        else:
            t = getattr(np, dtype.name)
            np_obj = t(dct["__ndarray__"])
        return np_obj

    return dct


def read_json(input_json_file):
    """
    Read and convert `input_json_file`.

    Args:
        input_json_file (str):

    Returns:

    """
    if not os.path.isfile(input_json_file):
        raise FileNotFoundError(f"Input file {input_json_file} not found.")

    with open(input_json_file, "r") as json_file:
        dct = json.load(json_file, object_hook=np_object_hook)
    return dct


class NumpyJSONEncoder(json.JSONEncoder):
    def __init__(self, primitive=False, base64=True, **kwargs):
        """
        JSON encoder for `numpy.ndarray`.

        Args:
            primitive (bool, optional, default=False): use primitive type if `True`. In primitive schema,
                `numpy.ndarray` is stored as JSON list and `np.generic` is stored as a number.
            base64 (bool, optional, default=True): use base64 to encode.
        """
        self.primitive = primitive
        self.base64 = base64
        super().__init__(**kwargs)

    def default(self, obj):
        if isinstance(obj, (np.ndarray, np.generic)):
            if self.primitive:
                return obj.tolist()
            else:
                if self.base64:
                    data_json = b64encode(obj.data if obj.flags.c_contiguous else obj.tobytes()).decode("ascii")
                else:
                    data_json = obj.tolist()
                dct = OrderedDict(__ndarray__=data_json,
                                  dtype=dtype_to_descr(obj.dtype),
                                  shape=obj.shape,
                                  Corder=obj.flags["C_CONTIGUOUS"],
                                  base64=self.base64)
                return dct
        return super().default(obj)


def save_json(output_file, obj, primitive=False, base64=True):
    """
    Convert obj to JSON object and save as file.

    Args:
        output_file (str):
        obj (mapping):
        primitive (bool, optional, default=False): use primitive type if `True`. In primitive schema, `numpy.ndarray` is
            stored as JSON list and `np.generic` is stored as a number.
        base64 (bool, optional, default=True): use base64 to encode.

    Returns:

    """
    ensure_output_file_dir_existence(output_file)
    with open(output_file, "w") as file:
        json.dump(obj, file, cls=NumpyJSONEncoder, **{"primitive": primitive, "base64": base64})


def scp(dst_user, dst_host, dst_path, local_path, dst_port=None, recursive=False, send=False, receive=False):
    """
    Transmit file(s) through scp.

    Args:
        dst_user (str):
        dst_host (str):
        dst_path (str):
        local_path (str):
        dst_port (str or int or None, optional, default=None): if None, usually refer to port 22.
        recursive (bool, default=False): transmit directories recursively.
        send (bool, default=False): send file(s) from local to destination.
        receive (bool, default=False): receive file(s) sent from destination.

    Returns:

    """
    if not (send ^ receive):
        raise ValueError(f"Send and receive must be exclusive.")

    cmd = "scp"
    dst = f"{dst_user}@{dst_host}:{dst_path}"
    if recursive:
        cmd += " -r"
    if dst_port:
        cmd += f" -P {dst_port}"
    if send:
        cmd += f" {local_path} {dst}"
    else:
        cmd += f" {dst} {local_path}"
    os.system(cmd)


def save_excel(output_file, data: Union[dict, pd.DataFrame], sheet_name: str = "Sheet1", append: bool = False,
               overlay_sheet: bool = False,
               column_width: int = None, auto_adjust_width: bool = False, index=False):
    """
    Save data to Excel file.
    Args:
        output_file (str):
        data (dict | pd.DataFrame):
        sheet_name (str, optional, default="Sheet1"):
        append (bool, optional, default=False): if True, append to existing file.
        overlay_sheet (bool, optional, default=False): if True, overwrite existing sheet. Note that this option only works for appending mode.
        column_width (int, optional, default=None): set column width to the given value, if exist.
        auto_adjust_width (bool, optional, default=False): if True, adjust column width according to the content length.
        index (bool, optional, default=False): if True, set index column on the work sheet.

    Returns:

    """
    write_mode = "a" if append else "w"

    if write_mode == "a" and not os.path.exists(output_file):
        logger.warning(f"Try to append data to a non-existing file: {output_file}, change mode to write instead.")
        write_mode = "w"

    if write_mode == "a" and overlay_sheet:
        if_sheet_exists = "overlay"
    else:
        if_sheet_exists = None

    if isinstance(data, dict):
        data = pd.DataFrame(data)

    ensure_output_file_dir_existence(output_file)

    with pd.ExcelWriter(output_file, engine="openpyxl", mode=write_mode, if_sheet_exists=if_sheet_exists) as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=index)

    if column_width is not None or auto_adjust_width:
        book = load_workbook(output_file)
        worksheet = book[sheet_name]

        for column_cells in worksheet.columns:
            if column_width is not None:
                width = column_width
            else:
                max_length = max(len(str(cell.value)) for cell in column_cells)
                width = max_length + 5

            column_letter = column_cells[0].column_letter
            worksheet.column_dimensions[column_letter].width = width

        # Save the workbook
        book.save(output_file)


def ensure_output_dir_existence(output_dir):
    mk_output_dir = not os.path.exists(output_dir)
    if mk_output_dir:
        os.makedirs(output_dir, exist_ok=True)
    return mk_output_dir, output_dir


def ensure_output_file_dir_existence(output_file):
    output_dir = os.path.split(output_file)[0]
    return ensure_output_dir_existence(output_dir)
