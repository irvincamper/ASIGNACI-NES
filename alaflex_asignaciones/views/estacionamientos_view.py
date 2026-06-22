from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import apply_shadow, table_card_height
from app.theme import CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.mock_data import ESTACIONAMIENTOS, ESTACIONAMIENTOS_KPIS
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard
from widgets.search_bar import SearchBar


class EstacionamientosView(QWidget):
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
        module_title = QLabel("Estacionamientos")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Control de espacios y asignaciones")
        subtitle.setObjectName("Subtitle")
        title_block.addWidget(app_title)
        title_block.addSpacing(8)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        refresh = AppButton("Actualizar", "fa5s.sync-alt", "primary")
        refresh.clicked.connect(lambda: ConfirmDialog.show_mock(self))
        header.addLayout(title_block, 1)
        header.addWidget(refresh, 0, Qt.AlignTop)
        layout.addLayout(header)

        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(22)
        for index, item in enumerate(ESTACIONAMIENTOS_KPIS):
            kpi_grid.addWidget(KpiCard(item["icon"], item["value"], item["title"], item["color"]), 0, index)
        layout.addLayout(kpi_grid)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        apply_shadow(filter_card)
        filters = QHBoxLayout(filter_card)
        filters.setContentsMargins(20, 18, 20, 18)
        filters.setSpacing(18)

        search = SearchBar("Buscar por cajón o matrícula")
        status = QComboBox()
        status.addItems(["Todos los estados", "Libre", "Ocupado", "Conflicto"])
        assign = AppButton("Asignar estacionamiento", "fa5s.plus", "primary")
        assign.clicked.connect(lambda: ConfirmDialog.show_mock(self))
        search.setFixedWidth(380)
        status.setFixedWidth(300)
        filters.addWidget(search)
        filters.addWidget(status)
        filters.addStretch(1)
        filters.addWidget(assign)
        layout.addWidget(filter_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(len(ESTACIONAMIENTOS)))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        table = DataTable()
        table.set_data(
            [
                ("cajon", "Cajón"),
                ("estado", "Estado"),
                ("matricula", "Matrícula"),
                ("empleado", "Empleado"),
                ("tipo", "Tipo de asignación"),
            ],
            ESTACIONAMIENTOS,
            badge_columns={"estado"},
            center_columns={"cajon"},
        )
        table_layout.addWidget(table)
        layout.addWidget(table_card)
        layout.addStretch(1)
