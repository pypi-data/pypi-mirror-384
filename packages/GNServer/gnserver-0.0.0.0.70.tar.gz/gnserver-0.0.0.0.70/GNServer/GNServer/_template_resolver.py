
import re
from typing import List

# regex для !{var}, поддерживает вложенность через точку
TPL_VAR_RE = re.compile(r'(?<!\\)!\{([A-Za-z_][A-Za-z0-9_\.]*)\}')

# список mime, которые считаем текстовыми
TEXTUAL_MIME_PREFIXES = [
    "text/",                       # text/html, text/css, text/plain
]
TEXTUAL_MIME_EXACT = {
    "application/javascript",
    "application/json",
    "application/xml",
    "application/xhtml+xml"
}
TEXTUAL_MIME_SUFFIXES = (
    "+xml",  # например application/rss+xml
    "+json", # application/ld+json
)

def extract_template_vars(filedata: bytes, mime: str) -> List[str]:
    """
    Ищет все !{var} в тексте, если MIME относится к текстовым.
    """
    mime = (mime or "").lower().strip()

    # определяем, текстовый ли mime
    is_textual = (
        mime.startswith(tuple(TEXTUAL_MIME_PREFIXES))
        or mime in TEXTUAL_MIME_EXACT
        or mime.endswith(TEXTUAL_MIME_SUFFIXES)
        or "javascript" in mime
        or "json" in mime
        or "xml" in mime
    )

    if not is_textual:
        return []

    try:
        text = filedata.decode("utf-8", errors="ignore")
    except Exception:
        return []

    return list(set(m.group(1) for m in TPL_VAR_RE.finditer(text)))

