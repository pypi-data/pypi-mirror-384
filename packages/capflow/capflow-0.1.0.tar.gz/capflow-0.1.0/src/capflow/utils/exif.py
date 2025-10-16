"""EXIF data extraction utilities for images."""

from pathlib import Path
from typing import Union, Dict, Any, Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def extract_exif(image_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract EXIF metadata from an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary containing EXIF metadata with human-readable keys.
        Returns empty dict if no EXIF data is available.

    Example:
        >>> exif_data = extract_exif("photo.jpg")
        >>> print(exif_data.get("Make"))  # Camera manufacturer
        Canon
        >>> print(exif_data.get("Model"))  # Camera model
        Canon EOS R5
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        with Image.open(image_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                return {}

            # Convert EXIF data to human-readable format
            exif_dict = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)

                # Handle GPS data specially
                if tag_name == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag_name] = gps_value
                    exif_dict[tag_name] = gps_data
                else:
                    # Convert bytes to string if possible
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8").strip("\x00")
                        except (UnicodeDecodeError, AttributeError):
                            value = str(value)

                    exif_dict[tag_name] = value

            return exif_dict

    except Exception as e:
        raise RuntimeError(f"Failed to extract EXIF data from {image_path}: {e}")


def get_camera_info(exif_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract camera information from EXIF data.

    Args:
        exif_data: EXIF dictionary from extract_exif()

    Returns:
        Dictionary with camera make, model, and lens info, or None if unavailable

    Example:
        >>> exif_data = extract_exif("photo.jpg")
        >>> camera = get_camera_info(exif_data)
        >>> print(camera)
        {'make': 'Canon', 'model': 'Canon EOS R5', 'lens': 'RF24-70mm F2.8 L IS USM'}
    """
    if not exif_data:
        return None

    camera_info = {}

    # Extract make and model
    if "Make" in exif_data:
        camera_info["make"] = str(exif_data["Make"])
    if "Model" in exif_data:
        camera_info["model"] = str(exif_data["Model"])

    # Extract lens information
    lens_keys = ["LensModel", "LensSpecification", "Lens"]
    for key in lens_keys:
        if key in exif_data:
            camera_info["lens"] = str(exif_data[key])
            break

    return camera_info if camera_info else None


def get_capture_settings(exif_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract capture settings from EXIF data.

    Args:
        exif_data: EXIF dictionary from extract_exif()

    Returns:
        Dictionary with ISO, aperture, shutter speed, and focal length, or None

    Example:
        >>> exif_data = extract_exif("photo.jpg")
        >>> settings = get_capture_settings(exif_data)
        >>> print(settings)
        {'iso': 800, 'aperture': 2.8, 'shutter_speed': '1/250', 'focal_length': 50.0}
    """
    if not exif_data:
        return None

    settings = {}

    # ISO
    if "ISOSpeedRatings" in exif_data:
        settings["iso"] = exif_data["ISOSpeedRatings"]
    elif "PhotographicSensitivity" in exif_data:
        settings["iso"] = exif_data["PhotographicSensitivity"]

    # Aperture (F-number)
    if "FNumber" in exif_data:
        f_number = exif_data["FNumber"]
        if isinstance(f_number, tuple):
            settings["aperture"] = float(f_number[0]) / float(f_number[1])
        else:
            settings["aperture"] = float(f_number)
    elif "ApertureValue" in exif_data:
        settings["aperture"] = exif_data["ApertureValue"]

    # Shutter speed
    if "ExposureTime" in exif_data:
        exposure = exif_data["ExposureTime"]
        if isinstance(exposure, tuple):
            if exposure[0] == 1:
                settings["shutter_speed"] = f"1/{exposure[1]}"
            else:
                settings["shutter_speed"] = float(exposure[0]) / float(exposure[1])
        else:
            settings["shutter_speed"] = float(exposure)

    # Focal length
    if "FocalLength" in exif_data:
        focal = exif_data["FocalLength"]
        if isinstance(focal, tuple):
            settings["focal_length"] = float(focal[0]) / float(focal[1])
        else:
            settings["focal_length"] = float(focal)

    return settings if settings else None


def get_datetime(exif_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract the capture date/time from EXIF data.

    Args:
        exif_data: EXIF dictionary from extract_exif()

    Returns:
        ISO 8601 formatted datetime string, or None if unavailable

    Example:
        >>> exif_data = extract_exif("photo.jpg")
        >>> dt = get_datetime(exif_data)
        >>> print(dt)
        2024-03-15T14:30:22
    """
    if not exif_data:
        return None

    # Try various datetime fields
    datetime_keys = [
        "DateTimeOriginal",  # When photo was taken
        "DateTimeDigitized",  # When photo was digitized
        "DateTime",  # File modification time
    ]

    for key in datetime_keys:
        if key in exif_data:
            dt_str = str(exif_data[key])
            # Convert EXIF format "YYYY:MM:DD HH:MM:SS" to ISO 8601
            try:
                dt_str = dt_str.replace(":", "-", 2).replace(" ", "T")
                return dt_str
            except Exception:
                return dt_str

    return None
