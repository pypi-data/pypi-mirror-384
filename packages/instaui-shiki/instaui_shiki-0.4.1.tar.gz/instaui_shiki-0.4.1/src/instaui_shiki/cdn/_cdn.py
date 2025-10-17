from typing import Optional
from instaui.zero.options import CdnResourceOption
from instaui_shiki import consts


def override(
    *,
    shiki_code_logic_js: Optional[str] = None,
    others: Optional[dict[str, str]] = None,
) -> CdnResourceOption:
    if not shiki_code_logic_js and not others:
        return default_override()

    import_maps = {}
    if others:
        import_maps.update(others)
    if shiki_code_logic_js:
        import_maps[consts.SHIKI_CODE_LOGIC_IMPORT_NAME] = shiki_code_logic_js

    return CdnResourceOption(
        import_maps=import_maps,
    )


def default_override() -> CdnResourceOption:
    return override(
        shiki_code_logic_js=consts.SHIKI_CODE_LOGIC_CDN,
    )
