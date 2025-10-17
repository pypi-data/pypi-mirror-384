import json

from pydantic import BaseModel
from pydantic.v1 import BaseSettings


def b64encode_filter(value):
    import base64
    """Filter to convert binary data to base64 string."""
    if value:
        return base64.b64encode(value).decode('utf-8')
    return ''


def pydantic_model_dump(model):
    # seems not used anymore
    if isinstance(model, BaseModel):
        return model.model_dump()
    if isinstance(model, BaseSettings):
        return model.dict()
    raise ValueError("Provided object is not a Pydantic model or settings model.")


def nl2br(value: str) -> str:
    return value.replace("\n", "<br>")

def render_bytes_size(size_bytes):
        if size_bytes == 0:
            return "0B"

        size_units = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0

        while size_bytes >= 1024 and i < len(size_units) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.2f} {size_units[i]}"


def render_json_pre(content: str):
        import json
        try:
            obj = json.loads(content) if content else {}
            return f'<pre><code>{json.dumps(obj, indent=4)}</code></pre>'
        except Exception:
            return f'<code>{content}</code>'

def render_json_cell_modal(data: dict) -> str:
    """
    Retourne le HTML complet à insérer dans un <td>,
    avec le toggle, le bouton et le <pre> caché.
    """
    pretty = json.dumps(data, indent=2)
    if data:
        return f'''
    <div class="json-modal-json-cell">
      <button type="button" class="btn btn-sm btn-primary view-json">Voir JSON</button>
      <div class="json-modal-pre-container" style="display:none;">
        <button class="json-modal-copy-btn" type="button"><i class="fa-regular fa-copy"></i></button>
        <pre class="json-content">{pretty}</pre>
      </div>
    </div>
    '''.strip()
    else:
        return f'<button type="button" class="btn btn-sm btn-primary" disabled>No data</button>'