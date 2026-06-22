from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import apply_shadow, table_card_height
from app.theme import CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.mock_data import OBJETOS, OBJETOS_KPIS
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard
from widgets.search_bar import SearchBar


class ObjetosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(8)
        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        module_title = QLabel("Objetos")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Catálogo de objetos y recursos asignables")
        subtitle.setObjectName("Subtitle")
        title_block.addWidget(app_title)
        title_block.addSpacing(8)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(16)
        for index, item in enumerate(OBJETOS_KPIS):
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

        search = SearchBar("Buscar objetos...")
        category = QComboBox()
        category.addItems(["Todas las categorías", "Seguridad", "Vestimenta", "Tecnología", "Acceso", "Accesorios"])
        status = QComboBox()
        status.addItems(["Todos los estados", "Activo", "Inactivo"])
        btn_new = AppButton("Nuevo objeto", "fa5s.plus", "primary")
        btn_new.clicked.connect(lambda: ConfirmDialog.show_mock(self))

        search.setFixedWidth(330)
        category.setFixedWidth(300)
        status.setFixedWidth(300)
        filters.addWidget(search)
        filters.addWidget(category)
        filters.addWidget(status)
        filters.addStretch(1)
        filters.addWidget(btn_new)
        layout.addWidget(filter_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(len(OBJETOS)))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        table = DataTable()
        table.set_data(
            [
                ("nombre", "Objeto"),
                ("categoria", "Categoría"),
                ("stock", "Stock"),
                ("requiere", "Requiere devolución"),
                ("estado", "Estado"),
                ("acciones", "Acciones"),
            ],
            [{**row, "acciones": ""} for row in OBJETOS],
            badge_columns={"estado"},
            category_columns={"categoria"},
            icon_columns={"nombre"},
            action_columns={"acciones"},
            center_columns={"stock", "requiere"},
            action_callback=lambda _row: ConfirmDialog.show_mock(self),
        )
        table_layout.addWidget(table)
        layout.addWidget(table_card)
        layout.addStretch(1)
