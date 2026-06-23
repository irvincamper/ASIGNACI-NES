from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import APP_TITLE_STYLE, MODULE_TITLE_STYLE, SUBTITLE_STYLE, apply_shadow, table_card_height
from app.theme import CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.objetos_service import ObjetosService
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard
from widgets.search_bar import SearchBar


class ObjetosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = ObjetosService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(8)
        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        app_title.setStyleSheet(APP_TITLE_STYLE)
        module_title = QLabel("Objetos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(MODULE_TITLE_STYLE)
        subtitle = QLabel("Catalogo de objetos y recursos asignables")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        title_block.addWidget(app_title)
        title_block.addSpacing(8)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(16)
        for index, item in enumerate(self.service.get_kpis()):
            card = KpiCard(item["icon"], item["value"], item["title"], item["color"])
            card.setFixedWidth(245)
            kpi_grid.addWidget(card, 0, index)

        header.addLayout(title_block, 1)
        header.addLayout(kpi_grid)
        layout.addLayout(header)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
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
        btn_new.clicked.connect(lambda: ConfirmDialog.show_mock(self))

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
        table_card.setMinimumHeight(table_card_height(8))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.columns = [
            ("nombre", "Objeto"),
            ("categoria", "Categoria"),
            ("requiere", "Requiere devolucion"),
            ("estado", "Estado"),
            ("acciones", "Acciones"),
        ]
        self.table = DataTable()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
        layout.addStretch(1)
        self.refresh_data()

    def refresh_data(self) -> None:
        rows = self.service.list_objetos(self.search.text(), self.category.currentText(), self.status.currentText())
        self.table.set_data(
            self.columns,
            [{**row, "acciones": ""} for row in rows],
            badge_columns={"estado"},
            category_columns={"categoria"},
            action_columns={"acciones"},
            center_columns={"requiere"},
            action_callback=lambda _row: ConfirmDialog.show_mock(self),
        )
