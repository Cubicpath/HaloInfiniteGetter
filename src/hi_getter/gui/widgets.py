###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing miscellaneous :py:class:`QWidget` Widgets."""

__all__ = (
    'BetterLineEdit',
    'HistoryComboBox',
    'LicenseViewer',
)

from collections import defaultdict
from collections.abc import Callable
from collections.abc import Sequence

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..constants import *
from ..utils import current_requirement_licenses

_PARENT_PACKAGE: str = __package__.split('.', maxsplit=1)[0]


class BetterLineEdit(QLineEdit):
    """A :py:class:`QLineEdit` with an added paste listener."""

    def __init__(self, *args, pasted: Callable | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if pasted is not None:
            vars(self)['pasted'] = pasted

    def pasted(self):
        """Function called when a paste key combo is detected."""

    def keyPressEvent(self, event: QKeyEvent):
        """Call self.pasted on paste."""
        super().keyPressEvent(event)
        if event.matches(QKeySequence.Paste):
            self.pasted()


class HistoryComboBox(QComboBox):
    """Editable :py:class:`QComboBox` acting as a history wrapper over :py:class:`BetterLineEdit`; has no duplicate values."""
    line_edit_class = BetterLineEdit

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

    def addItems(self, texts: Sequence[str]) -> None:
        """self.addItem for text in texts."""
        for text in texts:
            self.addItem(text)


class BetterTextBrowser(QTextBrowser):
    """:py:class:`QTextBrowser` with ability to map keys to :py:class:`Callable`'s."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_callable_map: defaultdict[int, Callable] = defaultdict(lambda: lambda: None)

    # noinspection PyTypeChecker
    def connect_key_to(self, key: Qt.Key, func: Callable):
        """Connect a :py:class:`Callable` to a key press."""
        self.key_callable_map[int(key)] = func

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Execute :py:class:`Callable` mapped to the key press."""
        super().keyPressEvent(event)
        self.key_callable_map[event.key()]()


class LicenseViewer(QWidget):
    """Widget that formats and shows the project's license file."""
    LICENSE_DATA = current_requirement_licenses(_PARENT_PACKAGE)

    def __init__(self, *args, **kwargs) -> None:
        """Create a new LicenseViewer. Gets license from the HI_RESOURCE_PATH/LICENSE file

        Has a fixed size of 750x380.
        """
        super().__init__(*args, **kwargs)
        self.setWindowTitle('License Viewer')
        self.setWindowIcon(QIcon(str(HI_RESOURCE_PATH / 'icons/copyright.ico')))
        self.resize(QSize(750, 380))
        self.current_license_index = 0

        self.license_label:       QLabel
        self.license_index_label: QLabel
        self.license_text_edit:   BetterTextBrowser
        self.next_license_button: QPushButton
        self.prev_license_button: QPushButton
        self._init_ui()

    def _init_ui(self) -> None:
        self.license_label:       QLabel = QLabel(self)
        self.license_index_label: QLabel = QLabel(f'{self.current_license_index + 1} of {len(self.LICENSE_DATA)}', self)
        self.license_text_edit:   BetterTextBrowser = BetterTextBrowser(self)
        self.next_license_button: QPushButton = QPushButton('Next', clicked=self.next_license)
        self.prev_license_button: QPushButton = QPushButton('Previous', clicked=self.prev_license)

        self.license_text_edit.connect_key_to(Qt.Key_Left, self.prev_license)
        self.license_text_edit.connect_key_to(Qt.Key_Right, self.next_license)
        self.view_package(_PARENT_PACKAGE)

        layout = QVBoxLayout()
        top = QHBoxLayout()
        self.setLayout(layout)

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

    def scroll_to_top(self) -> None:
        """Move text cursor to top of text document."""
        cursor = self.license_text_edit.textCursor()
        cursor.setPosition(0)
        self.license_text_edit.setTextCursor(cursor)

    def view_current_index(self) -> None:
        """Views the license data at the current index."""
        self.view_package(tuple(self.LICENSE_DATA.keys())[self.current_license_index])

    def view_package(self, package: str) -> None:
        """Views the license data of the given package name."""
        license_text = self.LICENSE_DATA[package][1] or 'LICENSE TEXT NOT FOUND -- COULD BE DUE TO EDITABLE INSTALLATION'
        self.current_license_index = tuple(self.LICENSE_DATA.keys()).index(package)
        self.license_label.setText(f'{package} -- "{self.LICENSE_DATA[package][0]}" License')
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
        self.license_text_edit.setHtml(f'<body style="white-space: pre-wrap"><center>{stripped_output}</center></body>')

        self.scroll_to_top()
