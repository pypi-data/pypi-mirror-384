# Each Qt binding is different, so...
# pyright: reportIncompatibleMethodOverride=false
import logging
from collections.abc import Callable

from qtpy.QtCore import Signal  # type: ignore[reportPrivateImportUsage]
from qtpy.QtCore import QEvent, QSize, Qt, QTimer
from qtpy.QtGui import QColor, QContextMenuEvent, QFocusEvent, QPainter, QPixmap
from qtpy.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QWidget,
)

from .other_utils import RemoveBtn


class CustomList(QListWidget):
    lost_focus = Signal()
    ListChanged = Signal()
    newItemSelected = Signal(object)
    removedItem = Signal(str)

    def __init__(self, max_n_row: int = 5):
        super().__init__()
        self.max_n_row = max_n_row

        self.setAlternatingRowColors(True)

        self.ListChanged.connect(  # we give time to the list to update
            lambda: QTimer.singleShot(100, self.update_height)
        )
        self.model().rowsInserted.connect(lambda x: self.ListChanged.emit())
        self.model().rowsRemoved.connect(lambda x: self.ListChanged.emit())
        self.model().rowsMoved.connect(lambda x: self.ListChanged.emit())
        self.itemPressed.connect(self.item_selected)
        self.currentItemChanged.connect(lambda x, y: self.item_selected(x))
        self.selected_item = None

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if event.reason() is Qt.FocusReason.ActiveWindowFocusReason:
            return  # this fixes drag and drop errors on Wayland
        self.clearSelection()
        item = self.itemWidget(self.selected_item)
        if item:
            item.lost_focus()
        self.newItemSelected.emit(None)
        self.selected_item = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.indexAt(event.pos()).isValid():
            self.clearFocus()

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self.update_height()

    def update_height(self):
        if self.max_n_row:
            n_rows = max(1, min(5, self.count()))
            item_widget = self.itemWidget(self.item(0))
            row_height = item_widget.height() if item_widget else 25
            self.setFixedHeight(row_height * n_rows + 2 * self.frameWidth())

    def item_selected(self, item: QListWidgetItem | None):
        if self.selected_item == item:
            return
        if self.selected_item is not None:
            widget = self.itemWidget(self.selected_item)
            if isinstance(widget, CustomListItem):
                widget.lost_focus()

        if item is not None:
            self.itemWidget(item).gain_focus()
        self.newItemSelected.emit(item)
        self.selected_item = item

    def remove_item(self):
        item = self.itemAt(self.sender().parent().pos())
        self.item_selected(None)
        self.removedItem.emit(item.data(Qt.ItemDataRole.UserRole))
        self.takeItem(self.row(item))
        self.clearFocus()

    def add_str(self, text: str, color: QColor | int | None = None):
        item = QListWidgetItem()
        cw = CustomListItem(
            text, remove_func=self.remove_item, parent=item, color=color
        )
        item.setData(Qt.ItemDataRole.UserRole, text)
        self.insertItem(-1, item)
        self.setItemWidget(item, cw)

    def getValue(self) -> list[str]:
        return [
            self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())
        ][::-1]


class CustomListItem(QWidget):
    def __init__(
        self,
        text,
        parent: QListWidgetItem,
        remove_func: Callable,
        color: None | int | QColor = None,
    ):
        self.list_item = parent
        super().__init__()
        self.selected = False
        self.text = QLabel(text)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(11, 0, 11, 0)

        if color is not None:
            icon = QLabel()
            icon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            icon.setFixedSize(10, 10)
            pixmap = QPixmap(icon.size())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pixmap.rect())
            painter.end()
            icon.setPixmap(pixmap)
            self.layout().addWidget(icon)

        self.rm_btn = RemoveBtn()
        self.rm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rm_btn.clicked.connect(remove_func)
        self.layout().addWidget(self.text)
        self.layout().addWidget(self.rm_btn)
        self.text.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_item.setSizeHint(QSize(10, self.rm_btn.sizeHint().height() + 4))
        self.update_label_colors()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu()
        copy_action = menu.addAction("Copy")
        remove_action = menu.addAction("Remove")
        action = menu.exec(event.globalPos())
        clipboard = QApplication.clipboard()

        if action == copy_action and clipboard is not None:
            clipboard.setText(self.text.text())
            logging.info(f'Copied to clipboard: "{clipboard.text()}"')
        elif action == remove_action:
            self.rm_btn.click()

    def gain_focus(self):
        self.selected = True
        self.text.setStyleSheet(self.selected_stylesheet)

    def lost_focus(self):
        self.selected = False
        self.text.setStyleSheet(self.non_selected_stylesheet)

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() in (
            QEvent.Type.PaletteChange,
            QEvent.Type.EnabledChange,
            QEvent.Type.FontChange,
        ):
            self.list_item.setSizeHint(QSize(10, self.rm_btn.sizeHint().height() + 4))
            self.update_label_colors()

    def update_label_colors(self):
        self.selected_stylesheet = (
            "QLabel {color : #"
            + f"{self.palette().highlightedText().color().rgb():x}"
            + f"; font-size:{self.font().pointSize()}pt"
            + "; }"
        )
        self.non_selected_stylesheet = (
            "QLabel {color : #"
            + f"{self.palette().text().color().rgb():x}"
            + f"; font-size:{self.font().pointSize()}pt"
            + "; }"
        )
        if self.selected:
            self.text.setStyleSheet(self.selected_stylesheet)
        else:
            self.text.setStyleSheet(self.non_selected_stylesheet)
