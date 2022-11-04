###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main application window implementation."""
from __future__ import annotations

__all__ = (
    'AppWindow',
    'size_label_for',
)

import json
import string
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..._version import __version__
from ...constants import *
from ...events import EventBus
from ...exception_hook import ExceptionEvent
from ...models import DeferredCallable
from ...models import DistributedCallable
from ...models import Singleton
from ...tomlfile import TomlEvents
from ...utils.gui import init_layouts
from ...utils.gui import init_objects
from ...utils.gui import scroll_to_top
from ...utils.network import decode_url
from ...utils.network import http_code_map
from ..app import app
from ..app import tr
from ..menus import *
from ..widgets import *
from ..workers import RecursiveSearch
from .exception_reporter import ExceptionReporter


def size_label_for(num: int) -> str:
    """Return the best display unit to describe the given data's size.

    Ex: Bytes, KiB, MiB, GiB, TiB
    """
    display_unit = 'Bytes'
    for size_label, size in BYTE_UNITS.items():
        if num >= (size // 2):
            display_unit = size_label
        else:
            break
    return display_unit


class AppWindow(Singleton, QMainWindow):
    """Main window for the HaloInfiniteGetter application."""
    _singleton_base_type = QMainWindow
    _singleton_check_ref = False
    shown_key_warning: bool = False

    def __init__(self, size: QSize) -> None:
        """Create the window for the application."""
        super().__init__()
        app().client.receivedError.connect(self.update_error)
        app().client.receivedData.connect(self.update_image)
        app().client.receivedJson.connect(self.update_text)

        self.current_image: QPixmap | None = None
        self.detached: dict[str, QMainWindow | None] = {'media': None, 'text': None}
        self.change_title(tr('app.name') + f' v{__version__}')
        self.resize(size)

        for subscribe_params in (
            (DeferredCallable(self.resize_image), TomlEvents.Set, lambda event: event.key.startswith('gui/media_output/')),
            (lambda val: self.text_output.setLineWrapMode(val.new), TomlEvents.Set, lambda event: event.key == 'gui/text_output/line_wrap_mode'),
        ): EventBus['settings'].subscribe(*subscribe_params)

        self.exception_reporter: ExceptionReporter
        self.input_field: HistoryComboBox
        self.media_frame: QFrame
        self.image_size_label: QLabel
        self.image_detach_button: QPushButton
        self.media_output: QGraphicsView
        self.text_frame: QFrame
        self.text_size_label: QLabel
        self.text_detach_button: QPushButton
        self.text_output: ExternalTextBrowser
        self.clear_picture: QPushButton
        self.copy_picture: QPushButton
        self.clear_text: QPushButton
        self.copy_text: QPushButton

        self._init_toolbar()
        self._init_ui()

    def _init_toolbar(self) -> None:
        """Initialize toolbar widgets."""
        from .settings import SettingsWindow

        def context_menu_handler(menu_class: type[QMenu]) -> None:
            """Create a new :py:class:`QMenu` and show it at the cursor's position."""
            if not issubclass(menu_class, QMenu):
                raise TypeError(f'{menu_class} is not a subclass of {QMenu}')

            menu: QMenu = menu_class(self)
            menu.exec(self.cursor().pos())
            menu.deleteLater()

        init_objects({
            (menu_bar := QToolBar(self)): {},

            (status_bar := QToolBar(self)): {
                'movable': False,
            },

            (file := QAction(self)): {
                'menuRole': QAction.MenuRole.ApplicationSpecificRole,
                'triggered': DeferredCallable(context_menu_handler, FileContextMenu)
            },

            (settings := QAction(self)): {
                'menuRole': QAction.MenuRole.PreferencesRole,
                'triggered': DistributedCallable((
                    SettingsWindow.instance().show,
                    SettingsWindow.instance().activateWindow,
                    SettingsWindow.instance().raise_
                ))
            },

            (tools := QAction(self)): {
                'menuRole': QAction.MenuRole.ApplicationSpecificRole,
                'triggered': DeferredCallable(context_menu_handler, ToolsContextMenu)
            },

            (help := QAction(self)): {
                'menuRole': QAction.MenuRole.AboutRole,
                'triggered': DeferredCallable(context_menu_handler, HelpContextMenu)
            },

            (logger := ExceptionLogger(self)): {
                'size': {'fixed': (None, 20)},
                'clicked': DistributedCallable((
                    logger.reporter.show,
                    logger.reporter.activateWindow,
                    logger.reporter.raise_
                ))
            }
        })

        app().init_translations({
            menu_bar.setWindowTitle: 'gui.menu_bar.title',
            status_bar.setWindowTitle: 'gui.status_bar.title',
            file.setText: 'gui.menus.file',
            settings.setText: 'gui.menus.settings',
            tools.setText: 'gui.menus.tools',
            help.setText: 'gui.menus.help',
            logger.label.setText: 'gui.status.default'
        })

        self.exception_reporter = logger.reporter

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, menu_bar)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, status_bar)

        EventBus['exceptions'].subscribe(lambda e: logger.label.setText(f'{e.exception}...'), ExceptionEvent)
        for action in (file, settings, tools, help):
            menu_bar.addSeparator()
            menu_bar.addAction(action)

        status_bar.addWidget(logger)
        status_bar.addSeparator()
        status_bar.addWidget(logger.label)

    # noinspection PyTypeChecker
    def _init_ui(self) -> None:
        """Initialize the UI, including Layouts and widgets."""

        def setup_detached_window(id_: str, frame: QFrame, handler: Callable, title: str = None) -> QMainWindow:
            """Set up a detached window, with the layout represented as a :py:class:`QFrame`.

            :param id_: unique name for the window
            :param frame: Set the window's central widget as this QFrame.
            :param handler: Callable to execute when closed, to reattach the frame to the parent window.
            :param title: The window title.
            """
            init_objects({
                (window := QMainWindow()): {
                    'windowTitle': title if title is not None else self.windowTitle(),
                    'centralWidget': frame,
                    'size': {'minimum': (300, 200)}
                }
            })

            window.closeEvent = lambda *_: handler() if self.detached[id_] is not None else None
            return window

        def toggle_media_detach() -> None:
            """Handler for detaching and reattaching the media output."""
            if self.detached['media'] is None:
                self.detached['media'] = window = setup_detached_window(
                    'media',
                    self.media_frame, toggle_media_detach,
                    tr('gui.outputs.image.detached')
                )
                self.image_detach_button.setText(tr('gui.outputs.reattach'))
                window.resizeEvent = DeferredCallable(self.resize_image)
                window.show()
            else:
                window = self.detached['media']
                self.detached['media'] = None
                window.close()

                self.outputs.insertWidget(0, self.media_frame)
                self.image_detach_button.setText(tr('gui.outputs.detach'))

        def toggle_text_detach() -> None:
            """Handler for detaching and reattaching the text output."""
            if self.detached['text'] is None:
                self.detached['text'] = window = setup_detached_window(
                    'text',
                    self.text_frame, toggle_text_detach,
                    tr('gui.outputs.text.detached')
                )
                self.text_detach_button.setText(tr('gui.outputs.reattach'))
                window.show()
            else:
                window = self.detached['text']
                self.detached['text'] = None
                window.close()

                self.outputs.insertWidget(-1, self.text_frame)
                self.text_detach_button.setText(tr('gui.outputs.detach'))

        def clear_current_pixmap() -> None:
            """Clear the current image from the media output."""
            self.image_size_label.setText(tr('gui.outputs.image.label_empty'))
            self.clear_picture.setDisabled(True)
            self.copy_picture.setDisabled(True)
            self.media_output.scene().clear()
            self.current_image = None

        def clear_current_text() -> None:
            """Clear the current text from the text output."""
            self.text_size_label.setText(tr('gui.outputs.text.label_empty'))
            self.clear_text.setDisabled(True)
            self.copy_text.setDisabled(True)
            self.text_output.setDisabled(True)
            self.text_output.clear()

        def next_in_history() -> None:
            """View the next license."""
            # Qt automatically rolls over to -1, so we handle it like prev_in_history
            self.input_field.setCurrentIndex(self.input_field.currentIndex() + 1)
            if self.input_field.currentIndex() < 0:
                self.input_field.setCurrentIndex(0)
            self.use_input()

        def prev_in_history() -> None:
            """View the previous license."""
            self.input_field.setCurrentIndex(self.input_field.currentIndex() - 1)
            if self.input_field.currentIndex() < 0:
                self.input_field.setCurrentIndex(self.input_field.count() - 1)
            self.use_input()

        def open_file_in_view(file_path: str) -> None:
            if not Path(file_path).is_file():
                return

            if file_path.endswith(tuple(SUPPORTED_IMAGE_EXTENSIONS)):
                self.update_image(file_path, Path(file_path).read_bytes())
            else:
                self.update_text(file_path, Path(file_path).read_text(encoding='utf8'))

        # Define widget attributes
        # Cannot be defined in init_objects() as walrus operators are not allowed for object attribute assignment.
        # This works in the standard AST, but is a seemingly arbitrary limitation set by the interpreter.
        # See: https://stackoverflow.com/questions/64055314/why-cant-pythons-walrus-operator-be-used-to-set-instance-attributes#answer-66617839
        (
            self.input_field, self.image_size_label, self.text_size_label,
            self.image_detach_button, self.text_detach_button, self.clear_picture, self.copy_picture,
            self.clear_text, self.copy_text, self.media_frame, self.text_frame,
            self.media_output, self.text_output, self.cache_explorer
        ) = (
            HistoryComboBox(self), QLabel(self), QLabel(self),
            QPushButton(self), QPushButton(self), QPushButton(self), QPushButton(self),
            QPushButton(self), QPushButton(self), QFrame(self), QFrame(self),
            QGraphicsView(self), ExternalTextBrowser(self), CacheExplorer(self)
        )

        init_objects({
            # Labels
            self.image_size_label: {
                'size': {'minimum': (50, None)}
            },
            self.text_size_label: {
                'size': {'minimum': (50, None)}
            },

            # Buttons
            self.image_detach_button: {
                'size': {'maximum': (80, None)},
                'clicked': toggle_media_detach
            },
            self.text_detach_button: {
                'size': {'maximum': (80, None)},
                'clicked': toggle_text_detach
            },
            self.clear_picture: {
                'disabled': True,
                'size': {'maximum': (80, None), 'minimum': (40, None)},
                'clicked': clear_current_pixmap
            },
            self.copy_picture: {
                'disabled': True,
                'size': {'maximum': (160, None), 'minimum': (80, None)},
                'clicked': DeferredCallable(app().clipboard().setPixmap, lambda: self.current_image)
            },
            self.clear_text: {
                'disabled': True,
                'size': {'maximum': (80, None), 'minimum': (40, None)},
                'clicked': clear_current_text
            },
            self.copy_text: {
                'disabled': True,
                'size': {'maximum': (160, None), 'minimum': (80, None)},
                'clicked': DeferredCallable(app().clipboard().setText, self.text_output.toPlainText)
            },
            (get_button := QPushButton(self)): {
                'size': {'maximum': (40, None)},
                'clicked': self.use_input
            },
            (scan_button := QPushButton(self)): {
                'size': {'maximum': (55, None)},
                'clicked': DeferredCallable(self.use_input, scan=True)
            },

            # Line editors
            self.input_field: {
                'items': (HI_SAMPLE_RESOURCE,)
            },
            self.input_field.lineEdit(): {
                'returnPressed': self.use_input
            },
            (subdomain_field := PasteLineEdit(self)): {
                'text': app().client.sub_host, 'disabled': True,
                'size': {'fixed': (125, None)}
            },
            (root_folder_field := PasteLineEdit(self)): {
                'text': app().client.parent_path, 'disabled': True,
                'size': {'fixed': (28, None)}
            },

            self.cache_explorer: {
                'openFileInView': open_file_in_view
            },

            # Outputs
            self.media_output: {
                'disabled': True, 'size': {'minimum': (None, 28)},
                'scene': QGraphicsScene(self), 'autoFillBackground': False,
                'horizontalScrollBarPolicy': Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
                'verticalScrollBarPolicy': Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            },
            self.text_output: {
                'disabled': True, 'size': {'minimum': (None, 28)},
                'lineWrapMode': QTextEdit.LineWrapMode(app().settings['gui/text_output/line_wrap_mode']),
                'openLinks': False, 'anchorClicked': self.navigate_to
            }
        })

        app().init_translations({
            self.change_title: 'app.name',

            # Labels
            self.image_size_label.setText: 'gui.outputs.image.label_empty',
            self.text_size_label.setText: 'gui.outputs.text.label_empty',

            # Buttons
            self.image_detach_button.setText: 'gui.outputs.detach',
            self.text_detach_button.setText: 'gui.outputs.detach',
            self.clear_picture.setText: 'gui.outputs.clear',
            self.copy_picture.setText: 'gui.outputs.image.copy',
            self.clear_text.setText: 'gui.outputs.clear',
            self.copy_text.setText: 'gui.outputs.text.copy',
            get_button.setText: 'gui.input_field.get',
            scan_button.setText: 'gui.input_field.scan'
        })

        self.text_output.connect_key_to(Qt.Key_Left, prev_in_history)
        self.text_output.connect_key_to(Qt.Key_Right, next_in_history)
        self.outputs = QHBoxLayout()

        init_layouts({
            # Text widget layouts
            (text_bottom := QHBoxLayout()): {
                'items': [
                    (self.clear_text, Qt.AlignLeft),
                    (self.copy_text, Qt.AlignLeft)
                ]
            },
            (text_top := QHBoxLayout()): {
                'items': [
                    (self.text_size_label, Qt.AlignLeft),
                    (self.text_detach_button, Qt.AlignRight)
                ]
            },
            QVBoxLayout(self.text_frame): {
                'items': [
                    text_top, self.text_output, text_bottom
                ]
            },

            # Media widget layouts
            (media_bottom := QHBoxLayout()): {
                'items': [
                    (self.clear_picture, Qt.AlignLeft),
                    (self.copy_picture, Qt.AlignLeft)
                ]
            },
            (media_top := QHBoxLayout()): {
                'items': [
                    (self.image_size_label, Qt.AlignLeft),
                    (self.image_detach_button, Qt.AlignRight)
                ]
            },
            QVBoxLayout(self.media_frame): {
                'items': [
                    media_top, self.media_output, media_bottom
                ]
            },

            # Middle parent layouts
            self.outputs: {
                'items': [
                    self.media_frame, self.text_frame
                ]
            },
            (middle := QHBoxLayout()): {
                'items': [
                    (self.cache_explorer, Qt.AlignLeft),
                    (self.outputs, Qt.AlignHCenter)
                ]
            },

            # Top widget layout
            (top := QHBoxLayout()): {
                'items': [
                    subdomain_field, root_folder_field, self.input_field,
                    get_button, scan_button
                ]
            },

            # Main layout
            (layout := QGridLayout()): {
                'items': [
                    (top, 10, 0, Qt.AlignTop),
                    (middle, 20, 0, Qt.AlignHCenter),
                    # (bottom, 30, 0, Qt.AlignBottom)
                ]
            }
        })

        init_objects({
            (main_widget := QWidget()): {'layout': layout},

            text_bottom: {'spacing': 5},
            top: {'spacing': 2},

            self: {'centralWidget': main_widget}
        })

    def change_title(self, name: str) -> None:
        """Change the window title, includes the version number."""
        self.setWindowTitle(f'{name} v{__version__}')

    def navigate_to(self, path: QUrl) -> None:
        """Set input field text to path and get resource."""
        str_path = decode_url(path.toDisplayString())
        if (  # Open local absolute resource locations
                sys.platform.startswith('win') and (str_path[0] in string.ascii_letters and str_path[1:].startswith(':\\'))
                or
                sys.platform.startswith('linux') and str_path.startswith('/')
        ):
            QDesktopServices.openUrl(QUrl(str_path))
        else:
            self.input_field.addItem(str_path)
            self.input_field.setCurrentIndex(self.input_field.count() - 1)
            self.use_input()

    def use_input(self, scan: bool = False) -> None:
        """Use the current input field's text to search through the Client for data.

        Automatically handles media and text data.

        :param scan: Whether to recursively scan a resource.
        """
        user_input = self.input_field.currentText()
        if not user_input:
            return

        search_path = user_input.strip()

        if '/file/' not in user_input:
            if search_path.split('.')[-1] in SUPPORTED_IMAGE_EXTENSIONS:
                search_path = f'images/file/{search_path}'
            else:
                search_path = f'progression/file/{search_path}'

        if search_path:
            if scan:
                app().start_worker(RecursiveSearch(app().client, search_path))
            else:
                app().client.get_hi_data(search_path)

    def update_image(self, _: str, data: bytes) -> None:
        """Update the image output with the given data."""
        display_unit: str = size_label_for(len(data))
        display_size: int = round(len(data) / BYTE_UNITS[display_unit], 4)

        self.clear_picture.setDisabled(False)
        self.copy_picture.setDisabled(False)
        self.current_image = QPixmap()
        self.current_image.loadFromData(data)
        self.image_size_label.setText(tr(
            'gui.outputs.image.label',
            self.current_image.size().width(), self.current_image.size().height(),  # Image dimensions
            display_size, display_unit                                              # Size in given unit
        ))
        self.resize_image()

    def update_text(self, search_path: str, data: str | dict[str, Any]) -> None:
        """Update the text output with the given data."""
        if isinstance(data, dict):
            data = json.dumps(data, indent=2)

        scroll_to_top(self.text_output)
        self.clear_text.setDisabled(False)
        self.copy_text.setDisabled(False)
        self.text_output.setDisabled(False)
        self.text_output.clear()

        display_unit: str = size_label_for(len(data.encode('utf8', errors='ignore')))
        display_size: int = round(len(data) / BYTE_UNITS[display_unit], 4)

        # Load up to 8 MiB of text data
        if len(data) <= BYTE_UNITS['MiB'] * 8:
            output = data
        else:
            output = tr(
                'gui.outputs.text.errors.too_large',
                app().client.to_os_path(search_path)
            )

        original_output = output

        replaced = set()
        for match in HI_PATH_PATTERN.finditer(original_output):
            match = match[0].replace('"', '')
            if match not in replaced:
                output = output.replace(match, f'<a href="{match}" style="color: #2A5DB0">{match}</a>')
                replaced.add(match)

        self.text_size_label.setText(tr(
            'gui.outputs.text.label',
            len(data.splitlines()), len(data),  # Line and character count
            display_size, display_unit          # Size in given unit
        ))

        self.text_output.setHtml(
            '<body style="white-space: pre-wrap">'
            f'{output}'
            '</body>'
        )

    def update_error(self, search_path: str, data: int) -> None:
        """Update the text output with the given data."""
        scroll_to_top(self.text_output)
        self.clear_text.setDisabled(False)
        self.copy_text.setDisabled(False)
        self.text_output.setDisabled(False)
        self.text_output.clear()

        error: str = tr(
            'gui.outputs.text.errors.http',
            app().client.api_root + search_path,  # Search path
            data, http_code_map[data][0],         # Error code and phrase
            http_code_map[data][1]                # Error description
        )
        self.text_size_label.setText(tr('gui.outputs.text.label_empty'))
        self.text_output.setPlainText(error)

    def resize_image(self) -> None:
        """Refresh the media output with a resized version of the current image."""
        if self.current_image is not None:
            new = self.current_image.copy()
            self.media_output.scene().clear()  # Clear buffer, otherwise causes memory leak

            if self.current_image.size() != self.media_output.viewport().size():
                # Create a new image from the copied source image, scaled to fit the window.
                new = new.scaled(
                    self.media_output.viewport().size(),
                    Qt.AspectRatioMode(app().settings['gui/media_output/aspect_ratio_mode']),
                    Qt.TransformationMode(app().settings['gui/media_output/transformation_mode'])
                )

            # Add image to buffer
            self.media_output.scene().addPixmap(new)

    # # # # # Events

    def show(self) -> None:
        """After window is displayed, show warnings if not already warned."""
        super().show()

        if app().first_launch:
            app().windows['readme_viewer'].show()
            app().show_dialog('information.first_launch', self)

        elif not self.shown_key_warning and app().client.token is None:
            app().show_dialog('warnings.empty_token', self)
            self.__class__.shown_key_warning = True

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resize image on resize of window."""
        super().resizeEvent(event)
        self.resize_image()
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Closes all detached/children windows and quit application."""
        super().closeEvent(event)
        # Remember window size
        app().settings.reload()
        app().settings['gui/window/x_size'] = self.size().width()
        app().settings['gui/window/y_size'] = self.size().height()
        app().settings.save()

        app().quit()
        event.accept()
