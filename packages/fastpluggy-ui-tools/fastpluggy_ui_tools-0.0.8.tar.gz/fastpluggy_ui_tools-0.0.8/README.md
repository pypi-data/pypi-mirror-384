# UI Tools Module for FastPluggy

A FastPluggy module that provides a collection of Jinja2 template filters and HTML rendering utilities for building user interfaces. 
It includes base64 encoding, Pydantic model dumping, localization, JSON rendering, and image embedding.

## Features

* **Base64 Encoding**: `b64encode` filter to convert binary data to Base64 strings.
* **Pydantic Model Dump**: `pydantic_model_dump` filter to serialize Pydantic `BaseModel` or `BaseSettings` instances to dictionaries.
* **Localization**: `localizedcurrency`, `localizeddate`, and `nl2br` filters for number, date/time formatting, and newline-to-HTML conversions using Babel.
* **JSON Rendering**: `from_json` filter and HTML list conversion utilities for safely displaying JSON data.
* **Image Rendering**: Embed Base64-encoded images directly into templates with `<img>` tags.
* **Seamless Integration**: Easy registration with FastPluggy via the `UiToolsModule` plugin.

# Extra Widget

TODO: add widget description

## Requirements

* Python 3.7 or higher
* [Babel](https://pypi.org/project/Babel/)
* [Pillow](https://pypi.org/project/Pillow/)

Install dependencies:

```bash
pip install -r requirements.txt
```



## Usage

### Template Filters

| Filter                | Description                                                      |
| --------------------- |------------------------------------------------------------------|
| `b64encode`           | Base64-encode binary data (`bytes → str`).                       |
| `pydantic_model_dump` | Dump Pydantic models/settings to dictionaries.                   |
| `localizedcurrency`   | Format a number as localized currency (default: `EUR`, `fr_FR`). |
| `localizeddate`       | Format dates/datetimes with various styles/locales/timezones.    |
| `nl2br`               | Convert newline characters to `<br>` tags.                       |
| `from_json`           | Parse a JSON string into Python objects (`list`/`dict`).         |
| `render_bytes_size`   | Format a size into human readable                                |

**Example in a Jinja2 template:**

```jinja
<h2>{{ user.name }}</h2>
<p>Balance: {{ user.balance | localizedcurrency('USD', 'en_US') }}</p>
<p>Joined: {{ user.joined_at | localizeddate('long', 'short', 'en_US') }}</p>
<pre>{{ config | pydantic_model_dump | pprint }}</pre>
```

### HTML Rendering Utilities

Import and use functions from `html_render.py` to render JSON or image data in HTML:

```python
from ui_tools.html_render import render_data_field, render_safe_data_field

# Render JSON string as HTML list
html_list = render_data_field(json_string)

# Safely render arbitrary data
safe_html = render_safe_data_field(raw_input)
```

## Running Tests

Ensure you have `pytest` installed, then run:

```bash
pytest tests/
```

## Contributing

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`.
3. Commit your changes and push to your fork.
4. Open a pull request for review.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
