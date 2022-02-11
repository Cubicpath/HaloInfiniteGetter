###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
from pathlib import Path

from PyQt6.QtCore import QDir, QFile, QTextStream
from PyQt6.QtWidgets import QApplication
from toml.decoder import CommentValue

from ..tomlfile import *

__all__ = (
    'GetterApp',
    'Theme',
)


class Theme:
    def __init__(self, id: str, style: str = '', display_name: str | None = None) -> None:
        self.id:           str = id
        self.style:        str = style
        self.display_name: str = display_name if display_name is not None else self.id


class GetterApp(QApplication):
    _legacy_style: str = None

    def __init__(self, argv: list[str], settings: TomlFile) -> None:
        super().__init__(argv)
        self.settings:        TomlFile = settings
        self.themes:          dict[str, Theme] = {}
        self.theme_index_map: dict[str, int] = {}

        self.settings.hook_event('$reload', self.load_themes)
        self.settings.hook_event('$set:gui/themes/selected', self.update_stylesheet)

    def update_stylesheet(self) -> None:
        """Set the application stylesheet to the one currently selected in settings."""
        self.setStyleSheet(self.themes[self.settings['gui/themes/selected']].style)

    def load_themes(self) -> None:
        if self._legacy_style is None:
            self.__class__._legacy_style = self.styleSheet()
        self.themes['legacy'] = Theme('legacy', self._legacy_style, 'Legacy (Default PyQt)')

        for id_, theme in self.settings['gui/themes'].items():
            if not isinstance(theme, dict):
                continue

            theme: dict = theme.copy()
            path = theme.pop('path')
            if isinstance(path, CommentValue):
                path = Path(path.val)
            if path.is_dir():
                QDir.addSearchPath(path.name, str(path))

                file = QFile(f'{path.name}:stylesheet.qss')
                file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
                theme['id'] = id_
                theme['style'] = QTextStream(file).readAll()
                self.themes[id_] = Theme(**theme)
                file.close()

        self.theme_index_map = {theme_id: i for i, theme_id in enumerate(theme.id for theme in self.sorted_themes)}
        self.update_stylesheet()

    @property
    def sorted_themes(self) -> list[Theme]:
        """List of themes sorted by their display name."""
        # FIXME: Doesn't crash, but also doesn't sort by display_name
        return sorted(self.themes.values(), key=lambda theme: theme.display_name)
