from __future__ import annotations
from typing import Dict, Iterable, List, Literal, Optional
from instaui import ui, custom
from instaui.runtime import get_app_slot
from . import consts


_IMPORT_MAPS = {
    "@shiki/transformers": consts.SHIKI_TRANSFORMERS_FILE,
    consts.SHIKI_CODE_LOGIC_IMPORT_NAME: consts.STATIC_DIR / "shiki_code_logic.js",
    consts.LANGS_IMPORT_NAME: consts.LANG_DIR,
    consts.THEMES_IMPORT_NAME: consts.THEME_DIR,
}

_ZERO_IMPORT_MAPS = {
    "@shiki/transformers": consts.SHIKI_TRANSFORMERS_FILE,
    consts.SHIKI_CODE_LOGIC_IMPORT_NAME: consts.STATIC_DIR / "shiki_code_logic.js",
    f"{consts.LANGS_IMPORT_NAME}python.mjs": consts.LANG_DIR / "python.mjs",
    f"{consts.THEMES_IMPORT_NAME}vitesse-light.mjs": consts.THEME_DIR
    / "vitesse-light.mjs",
    f"{consts.THEMES_IMPORT_NAME}vitesse-dark.mjs": consts.THEME_DIR
    / "vitesse-dark.mjs",
}


class Code(
    custom.element,
    esm="./static/shiki_code.js",
    externals=_IMPORT_MAPS,
    css=[consts.SHIKI_STYLE_FILE],
):
    # _language_folder: ClassVar[Path] = _LANGUAGE_DIR

    def __init__(
        self,
        code: ui.TMaybeRef[str],
        *,
        language: Optional[ui.TMaybeRef[str]] = None,
        theme: Optional[ui.TMaybeRef[str]] = None,
        themes: Optional[Dict[str, str]] = None,
        transformers: Optional[List[TTransformerNames]] = None,
        line_numbers: Optional[ui.TMaybeRef[bool]] = None,
    ):
        super().__init__()
        self.props({"code": code, "useDark": custom.convert_reference(ui.use_dark())})

        if language:
            self.props({"language": language})

        if theme:
            self.props({"theme": theme})

        if themes:
            self.props({"themes": themes})

        if transformers:
            self.props({"transformers": transformers})

        if line_numbers is not None:
            self.props({"lineNumbers": line_numbers})

    def _to_json_dict(self):
        self.use_zero_dependency()
        return super()._to_json_dict()

    def use_zero_dependency(self):
        app = get_app_slot()
        tag_name = self.dependency.tag_name  # type: ignore

        if app.mode != "zero" or app.has_temp_component_dependency(tag_name):
            return

        self.update_dependencies(
            css=[consts.SHIKI_STYLE_FILE], externals=_ZERO_IMPORT_MAPS, replace=True
        )

    @staticmethod
    def update_zero_dependency(add_languages: Optional[Iterable[str]] = None):
        if isinstance(add_languages, str):
            add_languages = [add_languages]

        for lang in add_languages or []:
            name = f"{consts.LANGS_IMPORT_NAME}{lang}.mjs"
            path = consts.LANG_DIR / f"{lang}.mjs"
            _ZERO_IMPORT_MAPS[name] = path


TTransformerNames = Literal["notationDiff"]
