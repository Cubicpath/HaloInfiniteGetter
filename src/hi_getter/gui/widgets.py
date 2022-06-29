###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing miscellaneous :py:class:`QWidget` Widgets."""

__all__ = (
    'ExceptionReporter',
    'ExceptionLogger',
    'ExternalTextBrowser',
    'HistoryComboBox',
    'LicenseViewer',
    'PasteLineEdit',
    'ReadmeViewer',
)

import traceback
import webbrowser
from collections import defaultdict
from collections import namedtuple
from collections.abc import Callable
from collections.abc import Sequence
from datetime import datetime
from importlib.metadata import metadata
from types import TracebackType
from typing import Any
from typing import Final
from typing import Optional

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .._version import __version__
from ..constants import *
from ..events import EventBus
from ..exceptions import ExceptionEvent
from ..models import DeferredCallable
from ..models import DistributedCallable
from ..network import encode_url_params
from ..utils import current_requirement_licenses
from .app import app
from .utils import delete_layout_widgets
from .utils import init_objects
from .utils import PARENT_PACKAGE
from .utils import scroll_to_top


class ExceptionReporter(QWidget):
    """A :py:class:`QWidget` that displays logged exceptions and their traceback."""

    def __init__(self, logger: 'ExceptionLogger') -> None:
        super().__init__()
        EventBus['exceptions'].subscribe(DeferredCallable(self.reload_exceptions), ExceptionEvent)

        self.selected: int = 0
        self.logger:   ExceptionLogger = logger
        self.setWindowTitle(app().translator('gui.exception_reporter.title'))
        self.setWindowIcon(self.logger.icon())
        self.resize(QSize(750, 400))
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        self.left_panel = QFrame(self)
        self.right_panel = QFrame(self)

        left_label = QLabel(self.left_panel)
        right_label = QLabel(self.right_panel)
        clear_all_button = QPushButton(self.left_panel)
        self.trace_back_viewer = ExternalTextBrowser(self)
        self.clear_button = QPushButton(self.right_panel)
        self.report_button = QPushButton(self.right_panel)

        # Define the scroll area/widget for the left panel
        self.scroll_area = QScrollArea(self)
        self.scroll_widget = QWidget(self.scroll_area)
        self.scroll_widget.setLayout(QVBoxLayout())
        self.scroll_widget.layout().setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)

        init_objects({
            self.scroll_area: {
                'widgetResizable': True
            },
            clear_all_button: {
                'clicked': self.clear_all_exceptions
            },
            self.trace_back_viewer: {
                'disabled': True,
                'font': QFont('consolas', 10),
                'lineWrapMode': QTextEdit.NoWrap
            },
            self.clear_button: {
                'disabled': True,
                'size': {'maximum': (self.report_button.width() // 1, None)},
                'clicked': self.clear_current_exception
            },
            self.report_button: {
                'disabled': True,
                'clicked': self.report_current_exception
            }
        })

        app().init_translations({
            self.setWindowTitle: 'gui.exception_reporter.title',

            # Labels
            left_label.setText: 'gui.exception_reporter.exception_list',
            right_label.setText: 'gui.exception_reporter.traceback_label',

            # Buttons
            clear_all_button.setText: 'gui.exception_reporter.clear_all',
            self.clear_button.setText: 'gui.exception_reporter.clear',
            self.report_button.setText: 'gui.exception_reporter.report_clear'
        })

        layout.addWidget(self.left_panel)
        layout.addWidget(self.right_panel)
        self.left_panel.setLayout(QVBoxLayout())
        self.right_panel.setLayout(QVBoxLayout())
        buttons = QHBoxLayout()

        self.left_panel.layout().addWidget(left_label)
        self.left_panel.layout().addWidget(self.scroll_area)
        self.left_panel.layout().addWidget(clear_all_button)

        self.right_panel.layout().addWidget(right_label)
        self.right_panel.layout().addWidget(self.trace_back_viewer)
        self.right_panel.layout().addLayout(buttons)
        buttons.addWidget(self.report_button)
        buttons.addWidget(self.clear_button)

    def report_current_exception(self) -> None:
        """Report the current exception to the exception logger."""
        exc_name: str = type(self.logger.exception_log[self.selected].exception).__name__
        exc_msg:  str = str(self.logger.exception_log[self.selected].exception).rstrip(".")
        exc_tb:   str = traceback.format_tb(self.logger.exception_log[self.selected].traceback)[0].strip()
        base:     str = 'https://github.com/Cubicpath/HaloInfiniteGetter/issues/new'
        params:   dict[str, str] = {
            'template': 'bug-report.yaml',
            'assignees': 'Cubicpath',
            'labels': 'bug',
            'projects': 'Cubicpath/HaloInfiniteGetter/2',
            'title': f'[Bug]: ({exc_name}) {exc_msg}',
            'version': f'v{__version__}',
            'logs': f'{exc_name}: {exc_msg}\n\n{exc_tb}'
        }
        webbrowser.open(f'{base}?{encode_url_params(params)}')

    def disable_exception_widgets(self) -> None:
        """Disables the widgets on the right pane."""
        self.trace_back_viewer.clear()
        self.trace_back_viewer.setDisabled(True)
        self.report_button.setDisabled(True)
        self.clear_button.setDisabled(True)

    def clear_all_exceptions(self) -> None:
        """Clear all exceptions from the list."""
        self.logger.clear_exceptions()
        self.disable_exception_widgets()
        delete_layout_widgets(self.scroll_widget.layout())

    def clear_current_exception(self) -> None:
        """Clears the currently selected exception and removes it from the log."""
        if (item := self.scroll_widget.layout().takeAt(self.selected)) is not None:
            self.logger.remove_exception(self.selected)
            item.widget().deleteLater()
        self.reload_exceptions()
        self.disable_exception_widgets()

    def reload_exceptions(self) -> None:
        """Load the exceptions from the logger."""
        delete_layout_widgets(self.scroll_widget.layout())
        for i, error in enumerate(self.logger.exception_log):
            button = QPushButton(f'{type(error.exception).__name__}: {error.exception}', self.scroll_widget)
            button.clicked.connect(DeferredCallable(setattr, self, 'selected', i))
            button.clicked.connect(DistributedCallable((
                self.clear_button.setDisabled,
                self.report_button.setDisabled,
                self.trace_back_viewer.setDisabled
            ), False))
            button.clicked.connect(DeferredCallable(self.trace_back_viewer.setText, DeferredCallable(
                app().translator, 'gui.exception_reporter.traceback_view',
                type(error.exception).__name__, error.exception, traceback.format_tb(error.traceback)[0]
            )))

            button.setStyleSheet("text-align:left;")
            button.setMaximumWidth((self.size().width() // 3) - 50)

            self.scroll_widget.layout().addWidget(button)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resizes the left panel to better fit the window."""
        super().resizeEvent(event)
        self.left_panel.setMaximumWidth(event.size().width() // 3)
        for i in range(self.scroll_widget.layout().count()):
            self.scroll_widget.layout().itemAt(i).widget().setMaximumWidth((event.size().width() // 3) - 50)
        event.accept()


class ExceptionLogger(QPushButton):
    """A :py:class:`QPushButton` that logs exceptions to the event bus."""
    LoggedException: tuple[int, Exception, TracebackType, datetime] = namedtuple('LoggedException', [
        'severity', 'exception', 'traceback', 'timestamp'
    ], defaults=[None])
    """A named tuple that contains the severity of the exception, the exception itself, and an optional traceback."""

    level_icon_list: list = [
        QStyle.SP_MessageBoxInformation,  # 0, Not a concern
        QStyle.SP_MessageBoxWarning,      # 1, Warning
        QStyle.SP_MessageBoxCritical      # 2, Error
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the ExceptionLogger."""
        super().__init__(*args, **kwargs)
        EventBus['exceptions'].subscribe(self.on_exception, ExceptionEvent)

        self.label:          QLabel = QLabel(self)
        self.exception_log:  list[ExceptionLogger.LoggedException] = []
        self.reporter:       ExceptionReporter = ExceptionReporter(self)
        self.severity:       int = 0

        self.reporter.setMinimumWidth(300)

    def clear_exceptions(self) -> None:
        """Clear the exception log and disable the button."""
        self.exception_log.clear()
        self.severity = 0
        self.setText('')
        self.label.setText(app().translator('gui.status.default'))

    def remove_exception(self, index: int) -> None:
        """Remove an exception from the log and update the current severity."""
        if self.exception_log:
            self.exception_log.pop(index)

        if len(self.exception_log) == 0:
            self.clear_exceptions()
        else:
            logged = len(self.exception_log)
            self.setText(f'({logged})' if logged < 10 else '(9+)')
            self.severity = self.exception_log[0].severity

    def on_exception(self, event: ExceptionEvent) -> None:
        """Update the exception log and change set the max level."""
        if isinstance(event.exception, Warning) and self.severity < 1:
            level = 1
        else:
            level = 2
        if self.severity < level:
            self.severity = level

        self.exception_log.append(self.LoggedException(level, event.exception, event.traceback, datetime.now()))
        self.sort_exceptions()

        logged = len(self.exception_log)
        self.setText(f'({logged})' if logged < 10 else '(9+)')

    def sort_exceptions(self) -> None:
        """Sort the exception log by severity."""
        if self.exception_log:
            self.exception_log = list(reversed(sorted(self.exception_log, key=lambda x: x.severity)))
            self.severity = self.exception_log[0].severity
        else:
            self.severity = 0

    @property
    def severity(self) -> int:
        """Get the max level of the exception log."""
        return self._severity

    @severity.setter
    def severity(self, value: int) -> None:
        """Set the max level of the exception log and update the icon."""
        self._severity = value
        self.setIcon(self.style().standardIcon(self.level_icon_list[self.severity]))
        self.reporter.setWindowIcon(self.icon())


class ExternalTextBrowser(QTextBrowser):
    """:py:class:`QTextBrowser` with ability to map keys to :py:class:`Callable`'s.

    Also supports external image loading and caching.
    """
    remote_image_cache: dict[str, bytes] = {}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # default factory producing empty DeferredCallables
        self.key_callable_map: defaultdict[int, Callable] = defaultdict(DeferredCallable)
        self.cached_text: str = ''
        self.cached_type: str = ''

    def hot_reload(self) -> None:
        """Reload cached text using the cached type's function."""
        # Remember scroll position
        scroll = self.verticalScrollBar().sliderPosition()

        # Reload all resources and replace text with cached text
        self.clear()
        match self.cached_type:
            case 'markdown':
                self.setMarkdown(self.cached_text)
            case 'html':
                self.setHtml(self.cached_text)
            case 'text':
                self.setPlainText(self.cached_text)
        self.verticalScrollBar().setSliderPosition(scroll)

    def set_hot_reloadable_text(self, text: str, text_type: str) -> None:
        """Set text that is designated to be hot-reloadable."""
        self.cached_text = text
        self.cached_type = text_type
        self.hot_reload()

    def loadResource(self, resource_type: QTextDocument.ResourceType, url: QUrl) -> Any:
        """Load a resource from an url.

        If resource type is an image and the url is external, download it using requests and cache it.
        """
        if resource_type == QTextDocument.ResourceType.ImageResource and not url.isLocalFile():
            image:      QImage = QImage()
            url_string: str = url.toDisplayString()
            if url_string not in self.remote_image_cache:
                reply = app().session.get(url)

                def handle_reply():
                    data: bytes = reply.readAll()
                    image.loadFromData(data)
                    self.remote_image_cache[url_string] = data

                    if self.cached_type:
                        self.hot_reload()
                    reply.deleteLater()

                reply.finished.connect(handle_reply)
            else:
                image.loadFromData(self.remote_image_cache[url_string])
            return image
        else:
            return super().loadResource(int(resource_type), url)

    def setLineWrapMode(self, mode: int | QTextEdit.LineWrapMode) -> None:
        """Set the line wrap mode. Allows use of ints."""
        super().setLineWrapMode(QTextEdit.LineWrapMode(mode))

    # noinspection PyTypeChecker
    def connect_key_to(self, key: Qt.Key, func: Callable) -> None:
        """Connect a :py:class:`Callable` to a key press."""
        self.key_callable_map[int(key)] = func

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Execute :py:class:`Callable` mapped to the key press."""
        super().keyPressEvent(event)
        self.key_callable_map[event.key()]()
        event.accept()


class PasteLineEdit(QLineEdit):
    """A :py:class:`QLineEdit` with an added paste listener."""
    pasted = Signal(name='pasted')

    def __init__(self, *args, pasted: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if pasted is not None:
            self.pasted.connect(pasted)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Call self.pasted on paste."""
        super().keyPressEvent(event)
        if event.matches(QKeySequence.Paste):
            self.pasted.emit()
        event.accept()


class HistoryComboBox(QComboBox):
    """Editable :py:class:`QComboBox` acting as a history wrapper over :py:class:`BetterLineEdit`; has no duplicate values."""
    line_edit_class = PasteLineEdit

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.setDuplicatesEnabled(False)
        self.setLineEdit(self.line_edit_class(parent=self))

    # noinspection PyTypeChecker
    def addItem(self, text: str, **kwargs) -> None:
        """Filters already-present strings from being added using addItem.

        addItem(self,
        icon: Union[PySide6.QtGui.QIcon, PySide6.QtGui.QPixmap],
        text: str,
        userData: Any = Invalid(typing.Any)
        ) -> None
        addItem(self,
        text: str,
        userData: Any = Invalid(typing.Any)
        ) -> None"""
        result = self.findText(text, Qt.MatchFlag.MatchFixedString)
        if result != -1:
            self.removeItem(result)

        super().addItem(text, **kwargs)

    def addItems(self, texts: Sequence[str], **_) -> None:
        """self.addItem for text in texts."""
        for text in texts:
            self.addItem(text)


class LicenseViewer(QWidget):
    """Widget that formats and shows the project's (and all of its requirements') license files."""
    LICENSE_DATA: Final[dict[str, tuple[str, str]]] = current_requirement_licenses(PARENT_PACKAGE)

    def __init__(self, *args, **kwargs) -> None:
        """Create a new LicenseViewer. Gets license from the HI_RESOURCE_PATH/LICENSE file

        Has a fixed size of 750x380.
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle(app().translator('gui.license_viewer.title'))
        self.setWindowIcon(app().icon_store['copyright'])
        self.resize(QSize(750, 550))
        self.current_license_index = 0

        self.license_label:       QLabel
        self.license_index_label: QLabel
        self.license_text_edit:   ExternalTextBrowser
        self.next_license_button: QPushButton
        self.prev_license_button: QPushButton
        self._init_ui()

    def _init_ui(self) -> None:
        self.license_label:       QLabel = QLabel(self)
        self.license_index_label: QLabel = QLabel(f'{self.current_license_index + 1} of {len(self.LICENSE_DATA)}', self)
        self.license_text_edit:   ExternalTextBrowser = ExternalTextBrowser(self)
        self.next_license_button: QPushButton = QPushButton(app().translator('gui.license_viewer.next'), clicked=self.next_license)
        self.prev_license_button: QPushButton = QPushButton(app().translator('gui.license_viewer.previous'), clicked=self.prev_license)

        self.license_text_edit.connect_key_to(Qt.Key_Left, self.prev_license)
        self.license_text_edit.connect_key_to(Qt.Key_Right, self.next_license)
        self.view_package(PARENT_PACKAGE)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        layout.addLayout(top)
        top.addWidget(self.license_label)
        top.addWidget(self.prev_license_button)
        top.addWidget(self.next_license_button)
        top.addWidget(self.license_index_label)
        layout.addWidget(self.license_text_edit)

        cursor = self.license_text_edit.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)
        self.next_license_button.setMaximumWidth(100)
        self.prev_license_button.setMaximumWidth(100)
        self.license_index_label.setMaximumWidth(50)
        self.license_text_edit.setFont(QFont('consolas', 11))
        self.license_text_edit.setOpenExternalLinks(True)

    def next_license(self) -> None:
        """View the next license."""
        self.current_license_index += 1
        if self.current_license_index + 1 > len(self.LICENSE_DATA):
            self.current_license_index = 0
        self.view_current_index()

    def prev_license(self) -> None:
        """View the previous license."""
        self.current_license_index -= 1
        if self.current_license_index < 0:
            self.current_license_index = len(self.LICENSE_DATA) - 1
        self.view_current_index()

    def view_current_index(self) -> None:
        """Views the license data at the current index."""
        self.view_package(tuple(self.LICENSE_DATA)[self.current_license_index])

    def view_package(self, package: str) -> None:
        """Views the license data of the given package name."""
        license_text = self.LICENSE_DATA[package][1] or app().translator('gui.license_viewer.not_found')
        self.current_license_index = tuple(self.LICENSE_DATA).index(package)
        self.license_label.setText(f'{package} -- "{self.LICENSE_DATA[package][0]}" {app().translator("gui.license_viewer.license")}')
        self.license_index_label.setText(f'{self.current_license_index + 1} of {len(self.LICENSE_DATA)}')

        output = license_text
        replaced = set()
        for match in HI_URL_PATTERN.finditer(license_text):
            match = match[0]
            if match not in replaced:
                output = output.replace(match, f'<a href="{match}" style="color: #2A5DB0">{match}</a>')
                replaced.add(match)

        stripped_output = ''
        for line in output.splitlines():
            stripped_output += line.strip() + '\n'
        stripped_output = stripped_output.strip()
        self.license_text_edit.setHtml(
            f'<body style="white-space: pre-wrap">'
            f'<center>{stripped_output}</center>'
            f'</body>'
        )

        scroll_to_top(self.license_text_edit)


class ReadmeViewer(QWidget):
    """Widget that formats and shows the project's README.md, stored in the projects 'Description' metadata tag."""
    README_TEXT: Final[str] = metadata(PARENT_PACKAGE)['Description']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(app().translator('gui.readme_viewer.title'))
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.resize(QSize(750, 750))
        self.readme_viewer: ExternalTextBrowser
        self._init_ui()

    def _dummy_func(self) -> None:
        """Must exist otherwise ReadmeViewer instances will be garbage collected through Context Menu deletion. Don't ask, just accept."""

    def _init_ui(self) -> None:
        self.readme_viewer = ExternalTextBrowser(self)
        close_button = QPushButton("Close", self, clicked=self.close)

        self.readme_viewer.connect_key_to(Qt.Key_Any, self._dummy_func)  # Refer to self._dummy_func

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self.readme_viewer)
        layout.addWidget(close_button)

        self.readme_viewer.setOpenExternalLinks(True)
        self.readme_viewer.set_hot_reloadable_text(self.README_TEXT, 'markdown')
        self.readme_viewer.setFont(QFont(self.readme_viewer.font().family(), 10))
        close_button.setMinimumHeight(40)
        close_button.setFont(QFont(close_button.font().family(), 16))

    def closeEvent(self, event: QCloseEvent) -> None:
        """Manually signal the readme_viewer for garbage collection."""
        super().closeEvent(event)
        self.readme_viewer.deleteLater()
        event.accept()
