import html
import json
from typing import Any

from fastpluggy.core.tools.install import is_installed
from loguru import logger


def from_json_filter(value):
    try:
        return json.loads(value)
    except Exception:
        return []


def is_valid_json(json_string: str) -> bool:
    """
    Validates whether the provided string is valid JSON.

    Parameters:
        json_string (str): The string to validate.

    Returns:
        bool: True if valid JSON, False otherwise.
    """
    if not json_string:
        return False
    try:
        json.loads(json_string)
    except ValueError as e:
        logger.debug("Invalid JSON:", e)
        return False
    return True


def convert_to_html_list(data: Any) -> str:
    """
    Converts JSON data to an HTML unordered list.
    Detects data types and renders accordingly.

    Parameters:
        data (Any): The JSON data to convert.

    Returns:
        str: HTML string representing the data as a list.
    """
    if isinstance(data, dict):
        html_content = "<ul>\n"
        for key, val in data.items():
            html_content += f"  <li><strong>{html.escape(str(key))}:</strong> "
            html_content += render_element(val)
            html_content += "</li>\n"
        html_content += "</ul>"
        return html_content
    elif isinstance(data, list):
        html_content = "<ul>\n"
        for item in data:
            html_content += "  <li>"
            html_content += render_element(item)
            html_content += "</li>\n"
        html_content += "</ul>"
        return html_content
    else:
        return render_element(data)


def render_element(element: Any) -> str:
    """
    Detects the type of the element and renders it appropriately.

    Parameters:
        element (Any): The element to render.

    Returns:
        str: HTML string representing the element.
    """
    if isinstance(element, dict) or isinstance(element, list):
        return convert_to_html_list(element)
    elif isinstance(element, str):
        if is_installed('PIL'):
            from .image_tools import is_base64_image, render_image
            logger.info(f"Element type {type(element)}")
            logger.info(f"is_base64_image : {is_base64_image(element)}")
            if is_base64_image(element):
                logger.info(f"Try to render image {element}")
                return render_image(element)
            else:
                return html.escape(element)
        else:
            return html.escape(element)
    elif isinstance(element, bool):
        return "True" if element else "False"
    elif element is None:
        return "null"
    else:
        # For numbers and other types
        return html.escape(str(element))


def render_data_field(value: str, safe_mode=False) -> str:
    """
    Renders the provided value as an HTML list if it's a valid JSON string.
    If not, returns the original value safely escaped or as a hyperlink if applicable.

    Parameters:
        value (str): The string to render.

    Returns:
        str: HTML list string or the original value.
    """
    if is_valid_json(value):
        data = json.loads(value)
        return convert_to_html_list(data)
    elif is_image_data(value):
        return render_raw_image(value, format='image/png')
    else:
        if safe_mode:
            escaped_content = html.escape(value.decode('utf-8') if isinstance(value, bytes) else value)
            return f'<pre><code>{escaped_content}</code></pre>'
        else:
            # Handle non-JSON strings:
            return value


def render_safe_data_field(value: str) -> str:
    """
    Renders the provided value as an HTML list if it's a valid JSON string.
    If not, returns the original value safely escaped or as a hyperlink if applicable.

    Parameters:
        value (str): The string to render.

    Returns:
        str: HTML list string or the original value.
    """
    return render_data_field(value, safe_mode=True)
