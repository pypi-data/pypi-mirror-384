import re

def extract_plain_text(html_content: str) -> str:
    text = re.sub(r'<[^>]+>', '', html_content)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#x27;', "'")
    return text.strip()

def enum_default(o):
    if hasattr(o, 'value'):  # Enum
        return o.value
    if hasattr(o, 'model_dump'):  # Pydantic model
        return o.model_dump()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")