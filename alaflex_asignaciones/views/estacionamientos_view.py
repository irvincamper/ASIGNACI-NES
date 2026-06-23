from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import APP_TITLE_STYLE, MODULE_TITLE_STYLE, SUBTITLE_STYLE, apply_shadow, table_card_height
from app.theme import CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.estacionamientos_service import EstacionamientosService
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard
from widgets.search_bar import SearchBar


class EstacionamientosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = EstacionamientosService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(8)
        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        app_title.setStyleSheet(APP_TITLE_STYLE)
        module_title = QLabel("Estacionamientos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(MODULE_TITLE_STYLE)
        subtitle = QLabel("Control de espacios y asignaciones")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        title_block.addWidget(app_title)
        title_block.addSpacing(8)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        refresh = AppButton("Actualizar", "fa5s.sync-alt", "primary")
        refresh.clicked.connect(self.refresh_data)
        header.addLayout(title_block, 1)
        header.addWidget(refresh, 0, Qt.AlignTop)
        layout.addLayout(header)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setHorizontalSpacing(22)
        layout.addLayout(self.kpi_grid)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        apply_shadow(filter_card)
        filters = QHBoxLayout(filter_card)
        filters.setContentsMargins(20, 18, 20, 18)
        filters.setSpacing(18)

        self.search = SearchBar("Buscar por cajón o matrícula")
        self.search.textChanged.connect(lambda _text: self.refresh_data())
        self.status = QComboBox()
        self.status.addItems(["Todos los estados", "Libre", "Ocupado", "Conflicto"])
        self.status.currentTextChanged.connect(lambda _text: self.refresh_data())
        assign = AppButton("Asignar estacionamiento", "fa5s.plus", "primary")
        assign.clicked.connect(lambda: ConfirmDialog.show_mock(self))
        self.search.setFixedWidth(380)
        self.status.setFixedWidth(300)
        filters.addWidget(self.search)
        filters.addWidget(self.status)
        filters.addStretch(1)
        filters.addWidget(assign)
        layout.addWidget(filter_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(8))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.columns = [
            ("cajon", "Cajón"),
            ("estado", "Estado"),
            ("matricula", "Matrícula"),
            ("empleado", "Empleado"),
            ("tipo", "Tipo de asignación"),
        ]
        self.table = DataTable()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
        layout.addStretch(1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self._refresh_kpis()
        rows = self.service.list_estacionamientos(self.search.text(), self.status.currentText())
        self.table.set_data(
            self.columns,
            rows,
            badge_columns={"estado"},
            center_columns={"cajon"},
        )

    def _refresh_kpis(self) -> None:
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, item in enumerate(self.service.get_kpis()):
            self.kpi_grid.addWidget(KpiCard(item["icon"], item["value"], item["title"], item["color"]), 0, index)
