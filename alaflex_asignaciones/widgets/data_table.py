from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QWidget,
)

from app.theme import COLOR_BLUE, COLOR_TEXT, COLOR_TEXT_MUTED, TABLE_ROW_HEIGHT
from utils.formatters import icon_from_name
from widgets.status_badge import StatusBadge

Column = tuple[str, str]


class DataTable(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setFocusPolicy(Qt.NoFocus)

    def set_data(
        self,
        columns: Sequence[Column],
        rows: Sequence[dict],
        *,
        badge_columns: set[str] | None = None,
        category_columns: set[str] | None = None,
        icon_columns: set[str] | None = None,
        action_columns: set[str] | None = None,
        center_columns: set[str] | None = None,
        action_callback: Callable[[dict], None] | None = None,
    ) -> None:
        badge_columns = badge_columns or set()
        category_columns = category_columns or set()
        icon_columns = icon_columns or set()
        action_columns = action_columns or set()
        center_columns = center_columns or set()

        self.clear()
        self.setColumnCount(len(columns))
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels([label for _, label in columns])

        for row_index, row in enumerate(rows):
            self.setRowHeight(row_index, TABLE_ROW_HEIGHT)
            for column_index, (key, _) in enumerate(columns):
                value = row.get(key, "")
                if key in badge_columns:
                    self.setCellWidget(row_index, column_index, self._badge_cell(str(value)))
                    continue
                if key in category_columns:
                    self.setCellWidget(row_index, column_index, self._badge_cell(str(value), "category"))
                    continue
                if key in icon_columns:
                    self.setCellWidget(
                        row_index,
                        column_index,
                        self._icon_text_cell(str(value), row.get(f"{key}_icon", "fa5s.circle")),
                    )
                    continue
                if key in action_columns:
                    self.setCellWidget(row_index, column_index, self._action_cell(row, action_callback))
                    continue

                item = QTableWidgetItem(str(value))
                item.setForeground(COLOR_TEXT if row_index != 0 else COLOR_BLUE)
                alignment = Qt.AlignVCenter
                if key in center_columns:
                    alignment |= Qt.AlignCenter
                else:
                    alignment |= Qt.AlignLeft
                item.setTextAlignment(alignment)
                self.setItem(row_index, column_index, item)

        self.resizeColumnsToContents()
        if rows:
            self.selectRow(0)

    def _badge_cell(self, value: str, badge_type: str = "status") -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(StatusBadge(value, badge_type))
        return container

    def _icon_text_cell(self, text: str, icon_name: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)

        icon = QLabel()
        icon.setFixedSize(28, 28)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name(icon_name, COLOR_BLUE).pixmap(22, 22))

        label = QLabel(text)
        label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px;")

        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addStretch(1)
        return container

    def _action_cell(self, row: dict, action_callback: Callable[[dict], None] | None) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setAlignment(Qt.AlignCenter)

        button = QToolButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(icon_from_name("fa5s.ellipsis-v", COLOR_TEXT_MUTED))
        button.setStyleSheet("QToolButton { border: none; background: transparent; padding: 6px; }")
        if action_callback:
            button.clicked.connect(lambda _checked=False, current=row: action_callback(current))

        layout.addWidget(button)
        return container
