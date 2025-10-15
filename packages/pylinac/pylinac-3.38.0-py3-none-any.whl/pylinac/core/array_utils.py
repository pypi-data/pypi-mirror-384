from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
from pydicom import Dataset
from pydicom.dataset import FileMetaDataset
from pydicom.multival import MultiValue
from pydicom.uid import (
    ExplicitVRLittleEndian,
    RTImageStorage,
    SecondaryCaptureImageStorage,
    generate_uid,
)
from scipy import ndimage

from .decorators import validate
from .validators import double_dimension


def array_not_empty(array: np.ndarray) -> None:
    """Check an array isn't empty."""
    if not array.size:
        raise ValueError("Array must not be empty")


def single_dimension(array: np.ndarray) -> None:
    """Check an array is a single dimension."""
    if array.ndim > 1:
        raise ValueError(
            f"Array was multidimensional. Must pass 1D array; found {array.ndim}"
        )


@validate(array=(array_not_empty, single_dimension))
def geometric_center_idx(array: np.ndarray) -> float:
    """Returns the center index and value of the profile.

    If the profile has an even number of array the centre lies between the two centre indices and the centre
    value is the average of the two centre array else the centre index and value are returned.
    """
    return (array.shape[0] - 1) / 2.0


@validate(array=(array_not_empty, single_dimension))
def geometric_center_value(array: np.ndarray) -> float:
    """Returns the center value of the profile.

    If the profile has an even number of elements the center lies between the two centre indices and the centre
    value is the average of the two center elements else the center index and value are returned.
    """
    arr_len = array.shape[0]
    # buffer overflow can cause the below addition to give strange results
    if arr_len % 2 == 0:  # array is even and central detectors straddle CAX
        cax = (array[int(arr_len / 2)] + array[int(arr_len / 2) - 1]) / 2.0
    else:  # array is odd and we have a central detector
        cax = array[int((arr_len - 1) / 2)]
    return cax


@validate(array=array_not_empty)
def normalize(array: np.ndarray, value: float | None = None) -> np.ndarray:
    """Normalize an array to the passed value. If not value is passed, normalize to the maximum value"""
    if value is None:
        val = array.max()
    else:
        val = value
    array = array / val
    return array


@validate(array=array_not_empty)
def invert(array: np.ndarray) -> np.ndarray:
    """Invert the array. Makes the max the min and vice versa. Does NOT account for datatype"""
    return -array + array.max() + array.min()


@validate(array=array_not_empty)
def bit_invert(array: np.ndarray) -> np.ndarray:
    """Invert the array, ACCOUNTING for the datatype. I.e. 0 for an uint8 array goes to 255, whereas it goes to 65535 for unint16.
    I.e. this is a datatype-specific inversion."""
    try:
        return np.invert(array)
    except TypeError:
        raise ValueError(
            f"The datatype {array.dtype} could not be safely inverted. This usually means the array is a float-like datatype. Cast to an integer-like datatype first."
        )


@validate(array=array_not_empty)
def ground(array: np.ndarray, value: float = 0) -> np.ndarray:
    """Ground the profile. Note this will also work on profiles with negative values. I.e. this will always
    move the minimum value to 'value', regardless of whether the profile minimum was positive or negative

    Parameters
    ----------
    value
        The value to set the minimum value as.
    """
    return array - array.min() + value


@validate(array=array_not_empty)
def filter(
    array: np.ndarray, size: float | int = 0.05, kind: str = "median"
) -> np.ndarray:
    """Filter the profile.

    Parameters
    ----------
    array: np.ndarray
        The array to filter.
    size : float, int
        Size of the median filter to apply.
        If a float, the size is the ratio of the length. Must be in the range 0-1.
        E.g. if size=0.1 for a 1000-element array, the filter will be 100 elements.
        If an int, the filter is the size passed.
    kind : {'median', 'gaussian'}
        The kind of filter to apply. If gaussian, `size` is the sigma value.
    """
    if isinstance(size, float):
        if 0 < size < 1:
            size = int(round(len(array) * size))
            size = max(size, 1)
        else:
            raise ValueError("Float was passed but was not between 0 and 1")

    if kind == "median":
        filtered_array = ndimage.median_filter(array, size=size)
    elif kind == "gaussian":
        filtered_array = ndimage.gaussian_filter(array, sigma=size)
    else:
        raise ValueError(
            f"Filter type {kind} unsupported. Use one of 'median', 'gaussian'"
        )
    return filtered_array


@validate(array=array_not_empty)
def stretch(array: np.ndarray, min: int = 0, max: int = 1) -> np.array:
    """'Stretch' the profile to the fit a new min and max value. This is a utility for grounding + normalizing.

    Parameters
    ----------
    array: numpy.ndarray
        The numpy array to stretch.
    min : number
        The new minimum of the array.
    max : number
        The new maximum value of the array.
    """
    if max <= min:
        raise ValueError(
            f"Max must be larger than min. Passed max of {max} was <= {min}"
        )
    dtype_info = get_dtype_info(array.dtype)
    if max > dtype_info.max:
        raise ValueError(
            f"Max of {max} was larger than the allowed datatype maximum of {dtype_info.max}"
        )
    if min < dtype_info.min:
        raise ValueError(
            f"Min of {min} was smaller than the allowed datatype minimum of {dtype_info.min}"
        )

    return ground(normalize(ground(array)) * (max - min), value=min)


@validate(array=array_not_empty)
def convert_to_dtype(array: np.array, dtype: type[np.dtype]) -> np.array:
    """Convert an array to another datatype, accounting for the array values.
    A normal numpy dtype conversion simply changes the datatype and leaves the values alone.
    This will convert an array and also convert the values to the same relative value of the new datatype.
    E.g. an element of value 100 on an uint8 array to be converted to an uint16 array will become ~25,690 (100/255 = 0.392 = x/65535, x = 25,690)

    .. note::

        Float-like input arrays will be normalized. This is because realistic float values are never near the datatype max.
        This can cause casting to an int-like datatype being 0's for the array. Thus, all float-like
        inputs will have outputs at the max value of the output datatype. Float-to-float conversion is discouraged.
    """
    # original array info
    old_dtype_info = get_dtype_info(array.dtype)
    # float range is so large that it's better to normalize
    if isinstance(old_dtype_info, np.finfo):
        relative_values = stretch(array, min=0, max=1)
    else:
        # we have an int-like array.
        # the float conversion is to avoid integer division
        # this can help when the values are very small
        # we will cast back to int later
        relative_values = array.astype(float) / old_dtype_info.max
    # new array info
    dtype_info = get_dtype_info(dtype)
    dtype_range = dtype_info.max - dtype_info.min
    return np.array(relative_values * dtype_range - dtype_info.max - 1, dtype=dtype)


def get_dtype_info(dtype: type[np.dtype]) -> np.iinfo | np.finfo:
    """Get the datatype of the array"""
    try:
        dtype_info = np.iinfo(dtype)
    except ValueError:
        dtype_info = np.finfo(dtype)
    return dtype_info


def find_nearest_idx(array: np.array, value: float) -> int:
    """Find the nearest index to the target value"""
    return (np.abs(array - value)).argmin()


@validate(array=double_dimension)
def array_to_dicom(
    array: np.ndarray,
    sid: float,
    gantry: float,
    coll: float,
    couch: float,
    dpi: float,
    extra_tags: dict | None = None,
) -> Dataset:
    """Converts a numpy array into a **simplistic** DICOM file. Not meant to be a full-featured converter. This
    allows for the creation of DICOM files from numpy arrays usually for internal use or image analysis.

    .. note::

        This will convert the image into an uint16 datatype to match the native EPID datatype.

    Parameters
    ----------
    array
        The numpy array to be converted. Must be 2 dimensions.
    sid
        The Source-to-Image distance in mm.
    dpi
        The dots-per-inch value of the image.
    gantry
        The gantry value that the image was taken at.
    coll
        The collimator value that the image was taken at.
    couch
        The couch value that the image was taken at.
    extra_tags
        Additional arguments to pass to the DICOM constructor. These are tags that should be included in the DICOM file.
        These will override any defaults Pylinac might set.
        E.g. PatientName, etc.
    """
    file_meta = FileMetaDataset()
    # Main data elements
    ds = Dataset()
    ds.SOPClassUID = RTImageStorage
    ds.SOPInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.StudyInstanceUID = generate_uid()
    ds.StudyDate = datetime.now().strftime("%Y%m%d")
    ds.ContentDate = datetime.now().strftime("%Y%m%d")
    ds.StudyTime = datetime.now().strftime("%H%M%S")
    ds.ContentTime = datetime.now().strftime("%H%M%S")
    ds.Modality = "RTIMAGE"
    ds.OperatorsName = "Pylinac"
    ds.ConversionType = "WSD"
    ds.PatientName = "Pylinac array"
    ds.PatientID = "123456789"
    ds.PatientSex = "O"
    ds.PatientBirthDate = "20000101"
    ds.ImageType = ["ORIGINAL", "PRIMARY", "OTHER"]
    ds.RTImageLabel = "Pylinac image"
    ds.RTImagePlane = "NORMAL"
    ds.RadiationMachineName = "Pylinac"
    ds.RTImagePosition = _rt_image_position(array, dpi)
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"  # 0 is black, max is white
    ds.Rows = array.shape[0]
    ds.Columns = array.shape[1]
    ds.BitsAllocated = array.itemsize * 8
    ds.BitsStored = array.itemsize * 8
    ds.HighBit = array.itemsize * 8 - 1
    ds.ImagePlanePixelSpacing = [25.4 / dpi, 25.4 / dpi]
    ds.RadiationMachineSAD = "1000.0"
    ds.RTImageSID = sid
    ds.PrimaryDosimeterUnit = "MU"
    ds.Manufacturer = "Pylinac"
    ds.GantryAngle = f"{gantry:.2f}"
    ds.BeamLimitingDeviceAngle = f"{coll:.2f}"
    ds.PatientSupportAngle = f"{couch:.2f}"
    # Although rare, loading certain types of images/files
    # may declare endian-ness and be different from the system.
    # We want to ensure it's native to the system.
    # See here for recommendations:
    # https://pydicom.github.io/pydicom/stable/tutorials/pixel_data/creation.html#creating-float-pixel-data-and-double-float-pixel-data
    if not array.dtype.isnative:
        array = array.byteswap().view(array.dtype.newbyteorder("="))
    if np.issubdtype(array.dtype, np.floating):
        ds.FloatPixelData = array.tobytes()
    else:
        ds.PixelData = array.tobytes()
        ds.PixelRepresentation = 0  # unsigned ints; only other option is 2's complement

    ds.file_meta = file_meta
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    ds.file_meta.ImplementationClassUID = generate_uid()

    extra_tags = extra_tags or {}
    for key, value in extra_tags.items():
        setattr(ds, key, value)
    return ds


def create_dicom_files_from_3d_array(
    array: np.ndarray,
    out_dir: Path | None = None,
    slice_thickness: float = 1,
    pixel_size: float = 1,
) -> Path:
    """Create a stack of DICOM files from a 3D numpy array. This creates a pseudo-CT scan.

    Parameters
    ----------

    array : np.ndarray
        The 3D array
    out_dir : Path, optional
        The directory to save the DICOM files to. If None, a temporary directory is created.
    slice_thickness : float, optional
        The slice thickness in mm. Default is 1.
    pixel_size : float, optional
        The pixel size in mm. Default is 1.
    """
    # we iterate over the array in the last dimension and
    # create a dicom image from it.
    series_uid = generate_uid()
    pixel_spacing = MultiValue(
        iterable=(pixel_size, pixel_size), type_constructor=float
    )
    out_dir = out_dir or Path(tempfile.mkdtemp())
    out_dir.mkdir(exist_ok=True, parents=True)
    for i in range(array.shape[-1]):
        arr = array[..., i].astype(np.uint16)
        image_patient_position = MultiValue(
            iterable=(0, 0, i * slice_thickness), type_constructor=float
        )
        ds = array_to_dicom(
            arr,
            sid=1000,
            gantry=0,
            coll=0,
            couch=0,
            dpi=25.4,
            extra_tags={
                "SeriesInstanceUID": series_uid,
                "ImagePositionPatient": image_patient_position,
                "SliceThickness": slice_thickness,
                "PixelSpacing": pixel_spacing,
            },
        )
        ds.save_as(out_dir / f"{i}.dcm", write_like_original=False)
    return out_dir


@validate(array=(array_not_empty, single_dimension))
def fill_middle_zeros(array: np.ndarray, cutoff_px: int = 0) -> np.ndarray:
    """Fills in the middle 0s in a 1D array where "middle" 0s are those that are
    surrounded by 1s on both sides.

    Parameters
    ----------
    array : np.ndarray
        A 1D numpy array with values between 0 and 1.
    cutoff_px : int
        The number of pixels to ignore near the edges of the array. This is to
        account for spurious signal near the edges.

    Returns
    -------
    np.ndarray
        A 1D float NumPy array with the middle 0s filled.
    """
    # Ensure the input is an array of values between 0-1.
    array = array.astype(float)
    if np.max(array) > 1 or np.min(array) < 0:
        raise ValueError("Array values must be between 0 and 1")
    # set edges to 0; this is to account for spurious 1s near the edges
    array[:cutoff_px] = 0
    array[-cutoff_px:] = 0

    # Identify the edges where the array transitions from 1 to 0 and 0 to 1
    edges = np.diff(array)

    # Identify the start and end points of the middle sections (where 0 is surrounded by 1s)
    left_edge = np.min(np.where(edges > 0.5)[0])
    right_edge = np.max(np.where(edges < -0.5)[0])

    # Create a copy of the array to modify
    filled_arr = array.copy()
    filled_arr[left_edge + 1 : right_edge + 1] = 1.0

    return filled_arr


def _rt_image_position(array: np.ndarray, dpmm: float) -> list[float]:
    """Calculate the RT Image Position of the array."""
    rows, cols = array.shape
    pixel_size_mm = 1.0 / dpmm

    # Calculate total physical size
    width_mm = cols * pixel_size_mm
    height_mm = rows * pixel_size_mm

    # Calculate RT Image Position
    # Origin is at center, so upper-left pixel is offset by half width and height
    x_position = -(width_mm / 2) + (pixel_size_mm / 2)
    y_position = -(height_mm / 2) + (pixel_size_mm / 2)
    return [x_position, y_position]


@validate(array=(array_not_empty, single_dimension))
def is_monotonically_increasing(array: np.ndarray) -> bool:
    """Check if an array is monotonically increasing."""
    return np.all(np.diff(array) > 0)


@validate(array=(array_not_empty, single_dimension))
def is_monotonically_decreasing(array: np.ndarray) -> bool:
    """Check if an array is monotonically decreasing."""
    return np.all(np.diff(array) < 0)


@validate(array=(array_not_empty, single_dimension))
def is_monotonic(array: np.ndarray) -> bool:
    """Check if an array is monotonically increasing or decreasing."""
    return is_monotonically_increasing(array) or is_monotonically_decreasing(array)
