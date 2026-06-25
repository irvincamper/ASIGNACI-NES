from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.styles import apply_shadow, table_card_height
from app.theme import COLOR_BG, COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.objetos_service import ObjetosService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.search_bar import SearchBar


TABLE_HEADER_H = 54
TABLE_ROW_H = 58


class ObjetosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = ObjetosService()
        self.objetos: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(20)

        title_block = QVBoxLayout()
        title_block.setSpacing(6)
        module_title = QLabel("Objetos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(self._module_title_style())
        subtitle = QLabel("Catalogo de objetos y recursos asignables")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(self._subtitle_style())
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_card.setStyleSheet(self._card_style())
        apply_shadow(filter_card)
        filters = QHBoxLayout(filter_card)
        filters.setContentsMargins(20, 18, 20, 18)
        filters.setSpacing(18)

        self.search = SearchBar("Buscar objetos...")
        self.search.textChanged.connect(lambda _text: self.refresh_data())
        self.category = QComboBox()
        self.category.addItems(self.service.list_categories())
        self.category.currentTextChanged.connect(lambda _text: self.refresh_data())
        self.status = QComboBox()
        self.status.addItems(["Todos los estados", "Activo", "Inactivo"])
        self.status.currentTextChanged.connect(lambda _text: self.refresh_data())
        btn_new = AppButton("Nuevo objeto", "fa5s.plus", "primary")
        btn_new.clicked.connect(lambda: self._show_object_form())

        self.search.setFixedWidth(330)
        self.category.setFixedWidth(300)
        self.status.setFixedWidth(300)
        filters.addWidget(self.search)
        filters.addWidget(self.category)
        filters.addWidget(self.status)
        filters.addStretch(1)
        filters.addWidget(btn_new)
        layout.addWidget(filter_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(8) + 36)
        table_card.setStyleSheet(self._card_style())
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(6, 8, 6, 8)

        self.columns = [
            ("nombre", "Objeto"),
            ("categoria", "Categoria"),
            ("requiere", "Requiere devolucion"),
            ("estado", "Estado"),
            ("acciones", "Acciones"),
        ]
        self.table = QTableWidget()
        self._configure_table()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self.objetos = self.service.list_objetos(self.search.text(), self.category.currentText(), self.status.currentText())
        self.table.setRowCount(len(self.objetos))
        for row_index, row in enumerate(self.objetos):
            self.table.setRowHeight(row_index, TABLE_ROW_H)
            values = [
                str(row.get("nombre", "")),
                str(row.get("categoria", "")),
                str(row.get("requiere", "")),
                str(row.get("estado", "")),
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                item.setForeground(QColor(COLOR_TEXT))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, column_index, item)
            self.table.setCellWidget(row_index, 4, self._action_cell(row))
        if self.objetos:
            self.table.selectRow(0)
        self._apply_column_widths()

    def _show_object_form(self, objeto: dict | None = None) -> None:
        objeto = objeto or {}
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar objeto" if objeto else "Nuevo objeto")
        dialog.setModal(True)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setFixedSize(760, 520)
        dialog.setStyleSheet(self._dialog_style())
        self._center_dialog(dialog)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Editar objeto" if objeto else "Nuevo objeto")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 28px; font-weight: 900;")
        subtitle = QLabel("Configura los datos del recurso asignable.")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        name = QLineEdit(str(objeto.get("nombre", "")))
        name.setPlaceholderText("Nombre del objeto")
        category = QLineEdit(str(objeto.get("categoria", "")))
        category.setPlaceholderText("Categoría")
        requires = QComboBox()
        requires.addItems(["Sí", "No"])
        requires.setCurrentText("Sí" if objeto.get("requiere", "Sí") in {"Sí", "Si"} else "No")
        status = QComboBox()
        status.addItems(["Activo", "Inactivo"])
        status.setCurrentText(str(objeto.get("estado", "Activo")))
        observations = QTextEdit(str(objeto.get("observaciones", "")))
        observations.setPlaceholderText("Observaciones")
        observations.setFixedHeight(104)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setStyleSheet(self._card_style())
        apply_shadow(form_card, blur=18, y_offset=4, alpha=20)
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(12)

        save = AppButton("Guardar", "fa5s.save", "primary")
        cancel = AppButton("Cancelar", "fa5s.times", "outline")
        cancel.setFixedWidth(126)
        save.setFixedWidth(126)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        def submit() -> None:
            result = self.service.guardar_objeto(
                {
                    "nombre": name.text(),
                    "categoria": category.text(),
                    "requiere_devolucion": requires.currentText(),
                    "estado": status.currentText(),
                    "observaciones": observations.toPlainText(),
                },
                int(objeto["id"]) if objeto.get("id") else None,
            )
            ConfirmDialog.show_message(dialog, "Objetos", result.get("mensaje", "Objeto guardado."))
            if result.get("ok"):
                dialog.accept()
                self.refresh_data()

        save.clicked.connect(submit)
        cancel.clicked.connect(dialog.reject)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        fields = [
            ("Nombre del objeto", name),
            ("Categoría", category),
            ("Requiere devolución", requires),
            ("Estado", status),
            ("Observaciones", observations),
        ]
        for index, (label_text, widget) in enumerate(fields):
            row = index // 2
            column = index % 2
            column_span = 1
            if label_text == "Observaciones":
                row = 2
                column = 0
                column_span = 2
            container = QWidget()
            field_layout = QVBoxLayout(container)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 800;")
            field_layout.addWidget(label)
            field_layout.addWidget(widget)
            form_layout.addWidget(container, row, column, 1, column_span)
        layout.addWidget(form_card, 1)
        layout.addLayout(buttons)
        dialog.exec()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_column_widths()

    def _configure_table(self) -> None:
        self.table.setColumnCount(len(self.columns))
        for column_index, (_, label) in enumerate(self.columns):
            header = QTableWidgetItem(label)
            header.setTextAlignment(Qt.AlignCenter)
            self.table.setHorizontalHeaderItem(column_index, header)
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
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setStyleSheet(self._table_style())

    def _apply_column_widths(self) -> None:
        if not hasattr(self, "table"):
            return
        width = max(self.table.viewport().width(), 900)
        widths = [0.24, 0.30, 0.18, 0.14, 0.14]
        for index, ratio in enumerate(widths):
            self.table.setColumnWidth(index, int(width * ratio))

    def _action_cell(self, row: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        button = QToolButton()
        button.setFixedSize(42, 36)
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(icon_from_name("fa5s.ellipsis-v", COLOR_TEXT))
        button.setStyleSheet(
            """
            QToolButton {
                background: #FFFFFF;
                border: 1px solid #DCE5F2;
                border-radius: 8px;
                padding: 6px;
            }
            QToolButton:hover {
                background: #F5F8FD;
                border-color: #BFD0EA;
            }
            """
        )
        menu = QMenu(button)
        edit_action = menu.addAction("Editar")
        deactivate_action = menu.addAction("Desactivar")
        edit_action.triggered.connect(lambda _checked=False, current=row: self._show_object_form(current))
        deactivate_action.triggered.connect(lambda _checked=False, current=row: self._deactivate_object(current))
        button.clicked.connect(lambda _checked=False: menu.exec(button.mapToGlobal(button.rect().bottomLeft())))
        layout.addWidget(button)
        return container

    def _deactivate_object(self, row: dict) -> None:
        if str(row.get("estado", "")) == "Inactivo":
            ConfirmDialog.show_message(self, "Objeto inactivo", "Este objeto ya se encuentra inactivo.")
            return
        if not ConfirmDialog.ask(
            self,
            "Desactivar objeto",
            "¿Deseas desactivar este objeto? Ya no estará disponible para nuevas relaciones, pero se conservará el historial.",
            "Desactivar",
        ):
            return
        result = self.service.desactivar_objeto(int(row["id"]))
        ConfirmDialog.show_message(self, "Desactivar objeto", result.get("mensaje", "Operación completada correctamente."))
        self.refresh_data()

    def _card_style(self) -> str:
        return f"""
        QFrame#Card {{
            background: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 16px;
        }}
        """

    def _dialog_style(self) -> str:
        return f"""
        QDialog {{
            background: {COLOR_BG};
        }}
        """

    def _center_dialog(self, dialog: QDialog) -> None:
        parent_window = self.window()
        if not parent_window:
            return
        parent_geo = parent_window.frameGeometry()
        dialog_geo = dialog.frameGeometry()
        dialog_geo.moveCenter(parent_geo.center())
        dialog.move(dialog_geo.topLeft())

    def _module_title_style(self) -> str:
        return f"color: {COLOR_TEXT}; font-size: 42px; font-weight: 900;"

    def _subtitle_style(self) -> str:
        return f"color: {COLOR_TEXT_MUTED}; font-size: 18px;"

    def _table_style(self) -> str:
        return f"""
        QTableWidget {{
            background: #FFFFFF;
            border: none;
            gridline-color: transparent;
            selection-background-color: #EAF2FF;
            selection-color: {COLOR_BLUE};
            outline: none;
            font-size: 14px;
        }}
        QHeaderView::section {{
            background: #FFFFFF;
            color: #061B4F;
            border: none;
            border-bottom: 1px solid #DCE5F2;
            padding-left: 14px;
            padding-right: 14px;
            font-size: 14px;
            font-weight: 700;
        }}
        QTableWidget::item {{
            border-bottom: 1px solid #E8EEF6;
            padding-left: 14px;
            padding-right: 14px;
        }}
        QTableWidget::item:hover {{
            background: #F7FAFF;
        }}
        QTableWidget::item:selected {{
            background: #EAF2FF;
            color: {COLOR_TEXT};
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
