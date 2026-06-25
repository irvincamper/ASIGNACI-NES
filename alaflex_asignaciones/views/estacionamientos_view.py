from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.styles import apply_shadow
from app.theme import COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.estacionamientos_service import EstacionamientosService
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.search_bar import SearchBar


TABLE_HEADER_H = 56
TABLE_ROW_H = 60


class EstacionamientosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = EstacionamientosService()
        self.rows: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(8)
        module_title = QLabel("Estacionamientos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(self._module_title_style())
        subtitle = QLabel("Control de espacios y asignaciones")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(self._subtitle_style())
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        refresh = AppButton("Actualizar", "fa5s.sync-alt", "outline")
        refresh.setFixedWidth(132)
        refresh.clicked.connect(self.refresh_data)
        header.addLayout(title_block, 1)
        header.addWidget(refresh, 0, Qt.AlignTop)
        layout.addLayout(header)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_card.setStyleSheet(self._card_style())
        apply_shadow(filter_card)
        filters = QHBoxLayout(filter_card)
        filters.setContentsMargins(20, 18, 20, 18)
        filters.setSpacing(22)
        self.search = SearchBar("Buscar por cajón o matrícula")
        self.search.setMinimumWidth(320)
        self.search.setMaximumWidth(460)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.textChanged.connect(lambda _text: self.refresh_data())
        self.status = QComboBox()
        self.status.addItems(["Todos los estados", "Libre", "Ocupado", "Conflicto"])
        self.status.setFixedWidth(360)
        self.status.currentTextChanged.connect(lambda _text: self.refresh_data())
        assign = AppButton("Asignar estacionamiento", "fa5s.plus", "primary")
        assign.setFixedWidth(250)
        assign.clicked.connect(self._show_assign_dialog)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.status)
        filters.addStretch(1)
        filters.addWidget(assign)
        layout.addWidget(filter_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setStyleSheet(self._card_style())
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(8, 10, 8, 10)

        self.columns = [
            ("cajon", "CajÃ³n"),
            ("estado", "Estado"),
            ("matricula", "MatrÃ­cula"),
            ("empleado", "Empleado"),
            ("tipo", "Tipo de asignaciÃ³n"),
            ("acciones", "Acciones"),
        ]
        self.table = QTableWidget()
        self._configure_table()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self.rows = self.service.list_estacionamientos(self.search.text(), self.status.currentText())
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            values = [str(row.get(key, "") or "-") for key, _label in self.columns[:-1]]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                item.setForeground(QColor("#111827"))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)
            self.table.setCellWidget(row_index, len(self.columns) - 1, self._action_cell(row))
            self.table.setRowHeight(row_index, TABLE_ROW_H)
        if self.rows:
            self.table.selectRow(0)
        self._apply_column_widths()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_column_widths()

    def _show_assign_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Asignar estacionamiento")
        dialog.setModal(True)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setFixedSize(700, 430)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Asignar estacionamiento")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 24px; font-weight: 900;")
        subtitle = QLabel("Relaciona un cajÃƒÂ³n libre con un empleado activo.")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._card_style())
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 16, 18, 16)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        matricula = QLineEdit()
        matricula.setPlaceholderText("MatrÃƒÂ­cula")
        cajon = QComboBox()
        for row in self.service.list_estacionamientos("", "Libre"):
            cajon.addItem(str(row["cajon"]), row["cajon"])
        tipo = QComboBox()
        tipo.addItems(["Empleado", "Temporal", "Visitante"])
        observaciones = QTextEdit()
        observaciones.setFixedHeight(90)
        observaciones.setPlaceholderText("Observaciones")

        fields = [("MatrÃƒÂ­cula", matricula), ("CajÃƒÂ³n", cajon), ("Tipo de asignaciÃƒÂ³n", tipo), ("Observaciones", observaciones)]
        for index, (label_text, widget) in enumerate(fields):
            container = QWidget()
            block = QVBoxLayout(container)
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(6)
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 800;")
            block.addWidget(label)
            block.addWidget(widget)
            grid.addWidget(container, index // 2, index % 2, 1, 2 if label_text == "Observaciones" else 1)
        layout.addWidget(card, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = AppButton("Cancelar", "fa5s.times", "outline")
        save = AppButton("Asignar", "fa5s.save", "primary")
        cancel.clicked.connect(dialog.reject)

        def submit() -> None:
            data = {
                "matricula": matricula.text(),
                "cajon": cajon.currentData(),
                "tipo_asignacion": tipo.currentText(),
                "observaciones": observaciones.toPlainText(),
            }
            result = self.service.asignar(data)
            if result.get("requiere_confirmacion"):
                if not ConfirmDialog.ask(dialog, "Reemplazar estacionamiento", result["mensaje"], "Reemplazar"):
                    return
                result = self.service.asignar(data, replace_existing=True)
            ConfirmDialog.show_message(dialog, "Asignar estacionamiento", result.get("mensaje", "OperaciÃƒÂ³n completada correctamente."))
            if result.get("ok"):
                dialog.accept()
                self.refresh_data()

        save.clicked.connect(submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        dialog.exec()

    def _action_cell(self, row: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        button = QToolButton()
        button.setFixedSize(42, 34)
        button.setCursor(Qt.PointingHandCursor)
        button.setText("...")
        button.setStyleSheet("QToolButton { background: #FFFFFF; border: 1px solid #DCE5F2; border-radius: 8px; font-weight: 800; }")
        menu = QMenu(button)
        detail = menu.addAction("Ver detalle")
        release = menu.addAction("Liberar")
        detail.triggered.connect(lambda _checked=False, current=row: self._show_detail(current))
        release.triggered.connect(lambda _checked=False, current=row: self._release_parking(current))
        button.clicked.connect(lambda _checked=False: menu.exec(QCursor.pos()))
        layout.addWidget(button)
        return container

    def _show_detail(self, row: dict) -> None:
        result = self.service.detalle(str(row.get("cajon", "")))
        if not result.get("ok"):
            ConfirmDialog.show_message(self, "Detalle", result.get("mensaje", "No se encontrÃƒÂ³ informaciÃƒÂ³n."))
            return
        detail = result["detalle"]
        message = (
            f"CajÃƒÂ³n: {detail.get('cajon', '-')}\n"
            f"Estado: {detail.get('estado', '-')}\n"
            f"MatrÃƒÂ­cula: {detail.get('matricula') or '-'}\n"
            f"Empleado: {detail.get('empleado') or '-'}\n"
            f"Tipo de asignaciÃƒÂ³n: {detail.get('tipo_asignacion') or '-'}\n"
            f"Fecha: {detail.get('updated_at') or detail.get('created_at') or '-'}\n"
            f"Observaciones: {detail.get('observaciones') or '-'}"
        )
        ConfirmDialog.show_message(self, "Detalle de estacionamiento", message)

    def _release_parking(self, row: dict) -> None:
        if str(row.get("estado", "")) == "Libre":
            ConfirmDialog.show_message(self, "Liberar estacionamiento", "El cajÃƒÂ³n ya se encuentra libre.")
            return
        if not ConfirmDialog.ask(self, "Liberar estacionamiento", "Ã‚Â¿Deseas liberar este cajÃƒÂ³n?", "Liberar"):
            return
        result = self.service.liberar(str(row.get("cajon", "")), "LiberaciÃƒÂ³n manual desde mÃƒÂ³dulo Estacionamientos.")
        ConfirmDialog.show_message(self, "Liberar estacionamiento", result.get("mensaje", "OperaciÃƒÂ³n completada correctamente."))
        self.refresh_data()

    def _configure_table(self) -> None:
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([label for _key, label in self.columns])
        for index in range(len(self.columns)):
            self.table.horizontalHeaderItem(index).setTextAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(TABLE_ROW_H)
        self.table.horizontalHeader().setFixedHeight(TABLE_HEADER_H)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setStyleSheet(self._table_style())

    def _apply_column_widths(self) -> None:
        if not hasattr(self, "table"):
            return
        scrollbar_width = self.table.verticalScrollBar().sizeHint().width() if self.table.verticalScrollBar() else 0
        width = max(self.table.viewport().width() - scrollbar_width - 8, 900)
        ratios = (0.10, 0.12, 0.12, 0.32, 0.24, 0.10)
        assigned = 0
        for index, ratio in enumerate(ratios[:-1]):
            column_width = int(width * ratio)
            self.table.setColumnWidth(index, column_width)
            assigned += column_width
        self.table.setColumnWidth(len(ratios) - 1, max(width - assigned, 220))

    def _card_style(self) -> str:
        return f"""
        QFrame#Card {{
            background: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 16px;
        }}
        QWidget {{
            background: transparent;
        }}
        """

    def _table_style(self) -> str:
        return f"""
        QTableWidget {{
            background: #FFFFFF;
            border: none;
            gridline-color: transparent;
            selection-background-color: #EAF2FF;
            selection-color: #111827;
            outline: none;
            font-size: 15px;
            color: #111827;
        }}
        QHeaderView::section {{
            background: #FFFFFF;
            color: #111827;
            border: none;
            border-bottom: 1px solid #DCE5F2;
            padding-left: 14px;
            padding-right: 14px;
            font-size: 15px;
            font-weight: 800;
        }}
        QTableWidget::item {{
            border-bottom: 1px solid #E8EEF6;
            padding-left: 14px;
            padding-right: 14px;
            background: #FFFFFF;
        }}
        QTableWidget::item:hover {{
            background: #F7FAFF;
        }}
        QTableWidget::item:selected {{
            background: #EAF2FF;
            color: #111827;
        }}
        QScrollBar:vertical {{
            width: 12px;
            background: #F7F9FC;
            margin: 8px 2px 8px 2px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: #9CA3AF;
            border-radius: 5px;
            min-height: 54px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #7D8794;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """

    def _module_title_style(self) -> str:
        return f"color: {COLOR_TEXT}; font-size: 42px; font-weight: 900;"

    def _subtitle_style(self) -> str:
        return f"color: {COLOR_TEXT_MUTED}; font-size: 18px;"
