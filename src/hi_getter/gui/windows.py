###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing GUI elements meant to be used as windows."""
import json
import webbrowser
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from .._version import __version__
from ..client import Client
from ..constants import *
from ..tomlfile import *
from ..utils import HTTP_CODE_MAP
from .app import *
from .menus import *

__all__ = (
    'AppWindow',
    'SettingsWindow',
)


# noinspection PyArgumentList
class SettingsWindow(QWidget):
    """Window that provides user interaction with the application's settings."""

    def __init__(self, parent: 'AppWindow', size: QSize) -> None:
        """Create a new settings window. Should only have one instance."""
        super().__init__()
        self.client = parent.client
        self.clipboard: QClipboard | None = parent.clipboard
        self.getter_window = parent
        self.settings: TomlFile = parent.APP.settings
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / 'icons/settings.ico')))
        self.resize(size)
        self.setFixedWidth(self.width())
        self.settings.hook_event('$fail:import', lambda: QMessageBox.warning(
            self, 'Import Error',
            f'Could not import settings from "{self.settings.path}". Make sure both the file and '
            f'the parent folder exist, and that the file contains valid TOML.'
        ))

        self.save_button:             QPushButton
        self.theme_dropdown:          QComboBox
        self.aspect_ratio_dropdown:   QComboBox
        self.transformation_dropdown: QComboBox
        self.line_wrap_dropdown:      QComboBox
        self.key_set_button:          QPushButton
        self.key_field:               QLineEdit
        self._init_ui()

    def _init_ui(self) -> None:
        self.save_button = QPushButton('Save', clicked=self.save_settings)
        reload_button = QPushButton('Reload', clicked=self.reload_settings)
        import_button = QPushButton('Import Settings', clicked=self.import_settings)
        export_button = QPushButton('Export Settings', clicked=self.export_settings)
        theme_label = QLabel('Current Theme: ')
        aspect_ratio_label = QLabel('Aspect Ratio: ')
        transformation_label = QLabel('Image Transform: ')
        line_wrap_label = QLabel('Line Wrap: ')
        self.theme_dropdown = QComboBox(self, activated=self.set_theme)
        self.aspect_ratio_dropdown = QComboBox(self, activated=self.set_aspect_ratio_method)
        self.transformation_dropdown = QComboBox(self, activated=self.set_transformation_method)
        self.line_wrap_dropdown = QComboBox(self, activated=self.set_line_wrap_method)
        open_editor_button = QPushButton('Open Settings in Editor', clicked=self.open_editor)
        key_show_button = QPushButton('Edit Auth Key', clicked=self.show_key)
        key_copy_button = QPushButton('Copy to Clipboard', clicked=self.copy_key)
        self.key_set_button = QPushButton('Set', clicked=self.set_key)
        self.key_field = QLineEdit(returnPressed=self.key_set_button.click)

        # Define layouts
        layout = QGridLayout()  # Main layout
        top = QHBoxLayout()
        middle = QVBoxLayout()
        theme_layout = QHBoxLayout()
        output_layout = QGridLayout()
        bottom = QVBoxLayout()
        key_layout = QHBoxLayout()

        # Assign positions of layouts
        self.setLayout(layout)
        layout.addLayout(top, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(middle, 10, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bottom, 20, 0, Qt.AlignmentFlag.AlignBottom)

        # Add top widgets
        top.addWidget(self.save_button)
        top.addWidget(reload_button)
        top.addWidget(import_button)
        top.addWidget(export_button)

        # Add middle widgets
        middle.addWidget(open_editor_button)
        middle.addLayout(theme_layout)
        middle.addLayout(output_layout)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        output_layout.addWidget(aspect_ratio_label, 0, 0)
        output_layout.addWidget(self.aspect_ratio_dropdown, 0, 10)
        output_layout.addWidget(transformation_label, 0, 20)
        output_layout.addWidget(self.transformation_dropdown, 0, 30)
        output_layout.addWidget(line_wrap_label, 10, 0)
        output_layout.addWidget(self.line_wrap_dropdown, 10, 10)

        # Add bottom widgets
        bottom.addWidget(key_show_button)
        bottom.addLayout(key_layout)
        key_layout.addWidget(key_copy_button)
        key_layout.addWidget(self.key_field)
        key_layout.addWidget(self.key_set_button)

        # Modify properties of widgets
        theme_label.setMaximumWidth(85)

        self.theme_dropdown.addItems(theme.display_name for theme in self.getter_window.APP.sorted_themes)
        self.theme_dropdown.setCurrentIndex(self.getter_window.APP.theme_index_map[self.settings['gui/themes/selected']])

        aspect_ratio_label.setMaximumWidth(70)
        self.aspect_ratio_dropdown.addItems(('Ignore', 'Keep', 'Expanding'))
        self.aspect_ratio_dropdown.setCurrentIndex(self.settings['gui/media_output/aspect_ratio_mode'])
        transformation_label.setMaximumWidth(90)
        self.transformation_dropdown.addItems(('Fast', 'Smooth'))
        self.transformation_dropdown.setCurrentIndex(self.settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.addItems(('No Wrap', 'Widget', 'Fixed Pixel', 'Fixed Column'))
        self.line_wrap_dropdown.setCurrentIndex(self.settings['gui/text_output/line_wrap_mode'])

        self.save_button.setMaximumWidth(50)
        self.save_button.setDisabled(True)
        reload_button.setMaximumWidth(60)

        self.key_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_field.setMinimumWidth(220)
        self.key_field.setFont(QFont('segoe ui', 8))
        self.key_set_button.setMinimumWidth(40)

    def refresh_dropdowns(self) -> None:
        """Refresh all dropdown widgets with the current settings assigned to them."""
        self.aspect_ratio_dropdown.setCurrentIndex(self.settings['gui/media_output/aspect_ratio_mode'])
        self.transformation_dropdown.setCurrentIndex(self.settings['gui/media_output/transformation_mode'])
        self.line_wrap_dropdown.setCurrentIndex(self.settings['gui/text_output/line_wrap_mode'])
        self.theme_dropdown.setCurrentIndex(self.getter_window.APP.theme_index_map[self.settings['gui/themes/selected']])

    def save_settings(self) -> None:
        """Save current settings to the user's settings file."""
        self.save_button.setDisabled(True)
        self.settings.save()

    def reload_settings(self) -> None:
        """Reload current settings from the user's settings file."""
        self.save_button.setDisabled(True)
        if self.settings.reload():
            self.refresh_dropdowns()

    def import_settings(self) -> None:
        """Import settings from a chosen TOML file."""
        self.save_button.setDisabled(True)
        file_path = Path(QFileDialog.getOpenFileName(self, 'Import Settings', str(CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
        if file_path.is_file():
            if self.settings.import_from(file_path):
                self.refresh_dropdowns()

    def export_settings(self) -> None:
        """Export current settings to a chosen file location."""
        file_path = Path(QFileDialog.getSaveFileName(self, 'Export Settings', str(CONFIG_PATH), 'TOML Files (*.toml);;All files (*.*)')[0])
        if str(file_path) != '.':
            self.settings.export_to(file_path)

    def open_editor(self) -> None:
        """Open current settings file in the user's default text editor."""
        webbrowser.open(str(self.settings.path))

    def set_aspect_ratio_method(self) -> None:
        """Set the media output's aspect ratio method to the chosen method."""
        self.save_button.setDisabled(False)
        self.settings['gui/media_output/aspect_ratio_mode'] = self.aspect_ratio_dropdown.currentIndex()
        self.getter_window.resize_image()

    def set_transformation_method(self) -> None:
        """Set the media output's image transformation method to the chosen method."""
        self.save_button.setDisabled(False)
        self.settings['gui/media_output/transformation_mode'] = self.transformation_dropdown.currentIndex()
        self.getter_window.resize_image()

    def set_line_wrap_method(self) -> None:
        """Set the text output's line wrap method to the chosen method."""
        self.save_button.setDisabled(False)
        self.settings['gui/text_output/line_wrap_mode'] = self.line_wrap_dropdown.currentIndex()
        self.getter_window.text_output.setLineWrapMode(QTextEdit.LineWrapMode(self.settings['gui/text_output/line_wrap_mode']))

    def set_theme(self) -> None:
        """Set selected theme to the chosen theme."""
        self.save_button.setDisabled(False)
        self.settings['gui/themes/selected'] = self.getter_window.APP.sorted_themes[self.theme_dropdown.currentIndex()].id

    def hide_key(self) -> None:
        """Hide API key."""
        self.key_set_button.setDisabled(True)
        self.key_field.setDisabled(True)
        self.key_field.setText(self.hidden_key())
        self.key_field.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_key(self) -> None:
        """Toggle hiding and showing the API key."""
        if not self.key_field.isEnabled():
            self.key_field.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.key_field.setText(self.client.auth_key)
            self.key_field.setDisabled(False)
            self.key_field.setFocus()
            self.key_set_button.setDisabled(False)
        else:
            self.hide_key()

    def copy_key(self) -> None:
        """Copy the current key value to the system clipboard."""
        if self.clipboard is not None:
            self.clipboard.setText(self.client.auth_key)

    def set_key(self) -> None:
        """Set the client's auth_key to the current text in the key field."""
        self.client.auth_key = self.key_field.text().strip().removeprefix('x-343-authorization-spartan: ')
        self.show_key()

    def hidden_key(self) -> str:
        """:return: The first 5 and last 4 characters of the API key, seperated by periods."""
        key = self.client.auth_key
        if key is not None and len(key) > 10:
            return f'{key[:5]}{"." * 50}{key[-4:]}'
        return 'None'

    # # # # # Events

    def showEvent(self, event: QShowEvent) -> None:
        """Auto hides the key upon un-minimizing."""
        super().showEvent(event)
        self.key_set_button.setDisabled(True)
        self.key_field.setDisabled(True)
        self.key_field.setText(self.hidden_key())


# noinspection PyArgumentList
class AppWindow(QMainWindow):
    """Main window for the HaloInfiniteGetter application."""

    shown_key_warning: bool = False

    def __init__(self, client: Client, app: GetterApp, size: QSize) -> None:
        """Create the window for the application."""
        super().__init__()
        self.APP: GetterApp = app
        self.client = client
        self.clipboard: QClipboard | None = app.clipboard()
        self.detached: dict[str, QMainWindow | None] = {'media': None, 'text': None}
        # self.themes: dict[str, str] = themes
        self.setWindowTitle(f'HaloInfiniteGetter v{__version__}')
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / 'icons/hi.ico')))
        self.resize(size)

        self.settings_window = SettingsWindow(self, QSize(420, 600))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self._clicked_input_field: bool = False
        self.current_image: QPixmap | None = None
        self.input_field:   QLineEdit
        self.media_output:  QGraphicsView
        self.text_output:   QTextBrowser
        self.clear_picture: QPushButton
        self.copy_picture:  QPushButton
        self.clear_text: QPushButton
        self.copy_text:  QPushButton

        self._init_toolbar()
        self._init_ui()

        if self.client.auth_key is None:
            QMessageBox.warning(
                self,
                'Empty API Token', '''
The SPARTAN_AUTH environment variable is not set!
You will be unable to acquire new data until a new token is provided.

You can manually set it in the Settings window.''')

    def _init_toolbar(self) -> None:
        """Initialize toolbar widgets."""
        self.toolbar = QToolBar('Toolbar', self)
        file = QAction('File', self, triggered=self.file_context_handler)
        settings = QAction('Settings', self, triggered=self.open_settings_window)
        help_ = QAction('Help', self, triggered=self.help_context_handler)

        self.addToolBar(self.toolbar)
        for action in (file, settings, help_):
            self.toolbar.addSeparator()
            self.toolbar.addAction(action)

        file.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        settings.setMenuRole(QAction.MenuRole.PreferencesRole)
        help_.setMenuRole(QAction.MenuRole.AboutRole)

    def _init_ui(self) -> None:
        """Initialize the UI, including Layouts and widgets."""
        self.media_frame = QFrame()
        self.image_size_label = QLabel('Image Output:')
        self.image_detach_button = QPushButton('Detach', clicked=self.toggle_media_detach)
        self.media_output = QGraphicsView()

        self.text_frame = QFrame()
        self.text_size_label = QLabel('Text Output:')
        self.text_detach_button = QPushButton('Detach', clicked=self.toggle_text_detach)
        self.text_output = QTextBrowser(anchorClicked=lambda e: self.navigate_to(e.toDisplayString()))

        self.clear_picture = QPushButton('Clear', clicked=self.clear_current_pixmap)
        self.copy_picture = QPushButton('Copy Picture', clicked=self.copy_current_pixmap)
        self.clear_text = QPushButton('Clear', clicked=self.clear_current_text)
        self.copy_text = QPushButton('Copy Text', clicked=self.copy_current_text)

        subdomain_field = QLineEdit(self.client.sub_host)
        root_folder_field = QLineEdit(self.client.PARENT_PATH)
        get_button = QPushButton('GET', clicked=self.get_resource)
        scan_button = QPushButton('SCAN', clicked=self.scan_resource)

        self.input_field = QLineEdit('Progression/file/Calendars/Seasons/SeasonCalendar.json', returnPressed=get_button.click)

        main_widget = QWidget()
        layout = QGridLayout()
        top = QHBoxLayout()
        self.outputs = QHBoxLayout()
        media_layout = QVBoxLayout()
        media_top = QHBoxLayout()
        media_bottom = QHBoxLayout()
        text_layout = QVBoxLayout()
        text_top = QHBoxLayout()
        text_bottom = QHBoxLayout()
        bottom = QGridLayout()

        self.setCentralWidget(main_widget)
        main_widget.setLayout(layout)
        layout.addLayout(top, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self.outputs, 10, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(bottom, 20, 0, Qt.AlignmentFlag.AlignBottom)

        top.addWidget(subdomain_field)
        top.addWidget(root_folder_field)
        top.addWidget(self.input_field)
        top.addWidget(get_button)
        top.addWidget(scan_button)
        top.setSpacing(2)

        self.outputs.addWidget(self.media_frame)
        self.outputs.addWidget(self.text_frame)

        # noinspection Duplicates
        self.media_frame.setLayout(media_layout)
        media_layout.addLayout(media_top)
        media_layout.addWidget(self.media_output)
        media_layout.addLayout(media_bottom)
        media_top.addWidget(self.image_size_label, Qt.AlignmentFlag.AlignLeft)
        media_top.addWidget(self.image_detach_button, Qt.AlignmentFlag.AlignRight)
        media_bottom.addWidget(self.clear_picture, Qt.AlignmentFlag.AlignLeft)
        media_bottom.addWidget(self.copy_picture, Qt.AlignmentFlag.AlignLeft)

        # noinspection Duplicates
        self.text_frame.setLayout(text_layout)
        text_layout.addLayout(text_top)
        text_layout.addWidget(self.text_output)
        text_layout.addLayout(text_bottom)
        text_top.addWidget(self.text_size_label, Qt.AlignmentFlag.AlignLeft)
        text_top.addWidget(self.text_detach_button, Qt.AlignmentFlag.AlignRight)
        text_bottom.addWidget(self.clear_text, Qt.AlignmentFlag.AlignLeft)
        text_bottom.addWidget(self.copy_text, Qt.AlignmentFlag.AlignLeft)
        text_bottom.setSpacing(5)

        subdomain_field.setFixedWidth(125)
        subdomain_field.setDisabled(True)
        root_folder_field.setFixedWidth(28)
        root_folder_field.setDisabled(True)
        self.input_field.mousePressEvent = self._destroy_text_on_first_click(self.input_field.mousePressEvent)
        # subdomain_field.returnPressed.connect(lambda *_: self.client.__class__.host.fset(self.client, subdomain_field.text()))
        get_button.setMaximumWidth(40)
        scan_button.setMaximumWidth(55)
        self.image_size_label.setMinimumWidth(50)
        self.image_detach_button.setMaximumWidth(80)
        self.media_output.setScene(QGraphicsScene())
        self.media_output.setMinimumHeight(28)
        self.media_output.setAutoFillBackground(False)
        self.media_output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.media_output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.media_output.setDisabled(True)
        self.text_size_label.setMinimumWidth(50)
        self.text_detach_button.setMaximumWidth(80)
        self.text_output.setMinimumHeight(28)
        self.text_output.setLineWrapMode(QTextEdit.LineWrapMode(self.APP.settings['gui/text_output/line_wrap_mode']))
        self.text_output.setOpenLinks(False)
        self.text_output.setDisabled(True)
        self.clear_picture.setMaximumWidth(80)
        self.clear_picture.setMinimumWidth(40)
        self.clear_picture.setDisabled(True)
        self.copy_picture.setMaximumWidth(160)
        self.copy_picture.setMinimumWidth(80)
        self.copy_picture.setDisabled(True)
        self.clear_text.setMaximumWidth(80)
        self.clear_text.setMinimumWidth(40)
        self.clear_text.setDisabled(True)
        self.copy_text.setMaximumWidth(160)
        self.copy_text.setMinimumWidth(80)
        self.copy_text.setDisabled(True)

    def _destroy_text_on_first_click(self, f: Callable) -> Callable:
        """Destroys the sample text in the input field if clicked before it is used."""
        def wrapper(*args, **kwargs):
            if self._clicked_input_field:
                f(*args, **kwargs)
            else:
                self._clicked_input_field = True
                self.input_field.setText('')
        return wrapper

    def _setup_detached_window(self, frame: QFrame, handler: Callable, title: str = None) -> QMainWindow:
        """Set up a detached window, with the layout represented as a :py:class:`QFrame`.

        :param frame: Set the window's central widget as this QFrame.
        :param handler: Callable to execute when closed, to reattach the frame to the parent window.
        :param title: The window title.
        """
        window = QMainWindow(self)
        window.setWindowTitle(title if title is not None else self.windowTitle())
        window.setCentralWidget(frame)
        window.closeEvent = lambda *_: handler() if self.detached['media'] is not None else None
        window.setMinimumHeight(200)
        window.setMinimumWidth(300)
        return window

    def file_context_handler(self) -> None:
        """Create a new :py:class:`FileContextMenu` and show it at the cursor's position."""
        menu = FileContextMenu(self)
        menu.move(self.cursor().pos())
        menu.show()

    def help_context_handler(self) -> None:
        """Create a new :py:class:`HelpContextMenu` and show it at the cursor's position."""
        menu = HelpContextMenu(self)
        menu.move(self.cursor().pos())
        menu.show()

    def open_settings_window(self) -> None:
        """Show the :py:class:`SettingsWindow` and bring it the front."""
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()

    def navigate_to(self, path: str) -> None:
        """Set input field text to path and get resource."""
        self.input_field.setText(path)
        self.get_resource()

    def toggle_media_detach(self) -> None:
        """Handler for detaching and reattaching the media output."""
        if self.detached['media'] is None:
            self.detached['media'] = window = self._setup_detached_window(self.media_frame, self.toggle_media_detach, 'Detached Image Output')
            self.image_detach_button.setText('Reattach')
            window.resizeEvent = lambda *_: self.resize_image()
            window.show()
        else:
            window = self.detached['media']
            self.detached['media'] = None
            window.close()

            self.outputs.insertWidget(0, self.media_frame)
            self.image_detach_button.setText('Detach')

    def toggle_text_detach(self) -> None:
        """Handler for detaching and reattaching the text output."""
        if self.detached['text'] is None:
            self.detached['text'] = window = self._setup_detached_window(self.text_frame, self.toggle_text_detach, 'Detached Text Output')
            self.text_detach_button.setText('Reattach')
            window.show()
        else:
            window = self.detached['text']
            self.detached['text'] = None
            window.close()

            self.outputs.insertWidget(-1, self.text_frame)
            self.text_detach_button.setText('Detach')

    def clear_current_pixmap(self) -> None:
        """Clear the current image from the media output."""
        self.image_size_label.setText('Image Output: ')
        self.clear_picture.setDisabled(True)
        self.copy_picture.setDisabled(True)
        self.media_output.scene().clear()
        self.current_image = None

    def copy_current_pixmap(self) -> None:
        """Copy the current image to the system clipboard."""
        if self.clipboard is not None:
            self.clipboard.setPixmap(self.current_image)

    def clear_current_text(self) -> None:
        """Clear the current text from the text output."""
        self.text_size_label.setText('Text Output: ')
        self.clear_text.setDisabled(True)
        self.copy_text.setDisabled(True)
        self.text_output.setDisabled(True)
        self.text_output.clear()

    def copy_current_text(self) -> None:
        """Copy the current output text to the system clipboard."""
        if self.clipboard is not None:
            self.clipboard.setText(self.text_output.toPlainText())

    def get_resource(self) -> None:
        """Get a single resource from the resource path."""
        self.use_input(op_code=10)

    def scan_resource(self) -> None:
        """Recursively search through the resource path's JSON data for more links to scan, if any."""
        self.use_input(op_code=20)

    def use_input(self, op_code: int = 0) -> None:
        """Use the current input field's text to search through the Client for data.

        Automatically handles media and text data.

        :param op_code: What operation to do. Get: 10 | Scan: 20
        """
        self._clicked_input_field = True
        user_input = self.input_field.text()
        if '/file/' not in user_input:
            if user_input.endswith(('png', 'jpg', 'jpeg', 'webp', 'gif')):
                user_input = f'images/file/{user_input}'
            else:
                user_input = f'progression/file/{user_input}'

        if user_input:
            if op_code == 10:
                data = self.client.get_hi_data(user_input)
                if isinstance(data, bytes):
                    self.clear_picture.setDisabled(False)
                    self.copy_picture.setDisabled(False)
                    self.current_image = QPixmap()
                    self.current_image.loadFromData(data)
                    size = self.current_image.size()

                    self.image_size_label.setText(f'Image Output: {size.width()}x{size.height()} ({round(len(data) / 1024, 4)} KiB)')
                    self.resize_image()
                else:
                    self.clear_text.setDisabled(False)
                    self.copy_text.setDisabled(False)
                    self.text_output.setDisabled(False)

                    if isinstance(data, dict):
                        data = json.dumps(data, indent=2)
                    elif isinstance(data, int):
                        data = f'{data}: {HTTP_CODE_MAP[data][0]}\n{HTTP_CODE_MAP[data][1]}'

                    output = data
                    replaced = set()

                    for match in PATH_PATTERN.finditer(data):
                        match = match[0].replace('"', '')
                        if match not in replaced:
                            output = output.replace(match, f'<a href="{match}" style="color: #2A5DB0">{match}</a>')
                            replaced.add(match)

                    self.text_output.setHtml(f'<body style="white-space: pre-wrap">{output}</body>')
                    self.text_size_label.setText(f'Text Output: '
                                                 f'{len(data.splitlines())} lines; '
                                                 f'{len(data)} characters '
                                                 f'({round(len(data.encode("utf8")) / 1024, 4)} KiB)')
            elif op_code == 20:
                self.client.recursive_search(user_input)
                self.use_input(op_code=10)

    def resize_image(self) -> None:
        """Refresh the media output with a resized version of the current image."""
        if self.current_image is not None:
            new = self.current_image.copy()
            self.media_output.scene().clear()  # Clear buffer, otherwise causes memory leak
            if self.current_image.size() != self.media_output.viewport().size():
                # Create a new image from the source image, scaled to fit the window.
                new = new.scaled(
                    self.media_output.viewport().size(),
                    Qt.AspectRatioMode(self.APP.settings['gui/media_output/aspect_ratio_mode']),
                    Qt.TransformationMode(self.APP.settings['gui/media_output/transformation_mode'])
                )
            self.media_output.scene().addPixmap(new)

    # # # # # Events

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resize image on resize of window."""
        super().resizeEvent(event)
        self.resize_image()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Closes all detached/children windows and quit application."""
        super().closeEvent(event)
        self.APP.quit()
