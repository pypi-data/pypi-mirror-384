from typing import Final
from pathlib import Path
from instaui_shiki import __version__

STATIC_DIR: Final = Path(__file__).parent / "static"
THEME_DIR: Final = STATIC_DIR / "themes"
LANG_DIR: Final = STATIC_DIR / "langs"
SHIKI_TRANSFORMERS_FILE: Final = STATIC_DIR / "shiki-transformers.js"
SHIKI_STYLE_FILE: Final = STATIC_DIR / "shiki-style.css"


LANGS_IMPORT_NAME: Final = "@shiki/langs/"
THEMES_IMPORT_NAME: Final = "@shiki/themes/"
SHIKI_CODE_LOGIC_IMPORT_NAME: Final = "@/shiki_code_logic"

# cdn
SHIKI_CODE_LOGIC_CDN: Final = f"https://cdn.jsdelivr.net/gh/instaui-python/instaui-shiki@v{__version__}/shiki-dist/shiki_code_logic.js"
