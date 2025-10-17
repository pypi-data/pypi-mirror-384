import base64
import html
import io
import logging

from PIL import Image



def is_base64_image(data_str: str) -> bool:
    """
    Checks if the provided string is a base64-encoded image.

    Parameters:
        data_str (str): The string to check.

    Returns:
        bool: True if the string is base64-encoded image data, False otherwise.
    """
    try:
        # Decode the base64 string
        decoded_data = base64.b64decode(data_str)
        res = is_image_data(decoded_data)
        logging.info(f"is_base64_image({data_str}): {res}")
        return res
    except (base64.binascii.Error, ValueError):
        logging.debug(f"Invalid base64 image: {data_str}")
        return False


def is_image_data(data: bytes) -> bool:
    """
    Checks if the provided bytes represent valid image data.

    Parameters:
        data (bytes): The data to check.

    Returns:
        bool: True if data is a valid image, False otherwise.
    """
    try:
        Image.open(io.BytesIO(data))
        return True
    except (IOError, ValueError, TypeError):
        return False


def render_image(data_str: str) -> str:
    """
    Renders a base64-encoded image string as an HTML <img> tag.

    Parameters:
        data_str (str): The base64-encoded image string.

    Returns:
        str: HTML <img> tag with the image embedded, or escaped string if invalid.
    """
    try:
        # Decode the base64 string
        decoded_data = base64.b64decode(data_str)
        if is_image_data(decoded_data):
            # Detect image format
            image = Image.open(io.BytesIO(decoded_data))
            format = image.format.lower()
            # Encode back to base64 to ensure it's clean
            return render_raw_image(decoded_data, format)
        else:
            return html.escape(data_str)
    except (base64.binascii.Error, ValueError, IOError) as e:
        logging.error(f"Error in render_image : {e}")
        return html.escape(data_str)


def render_raw_image(decoded_data, format):
    encoded_image = base64.b64encode(decoded_data).decode('utf-8')
    # Create data URI
    data_uri = f"data:image/{format};base64,{encoded_image}"
    # Return HTML <img> tag
    return f'<img src="{data_uri}" alt="Image" style="max-width:500px; max-height:500px;">'
