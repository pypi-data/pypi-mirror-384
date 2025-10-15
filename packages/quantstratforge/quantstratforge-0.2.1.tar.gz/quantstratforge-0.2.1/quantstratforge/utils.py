import logging
import hashlib

logger = logging.getLogger("quantstratforge")
logging.basicConfig(level=logging.INFO)

def add_watermark(text: str, key: str = "secret") -> str:
    wm = hashlib.md5(key.encode()).hexdigest()[:6]
    return f"{text} [WM:{wm}]"