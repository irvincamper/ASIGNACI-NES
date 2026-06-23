from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import APP_TITLE_STYLE, MODULE_TITLE_STYLE, SUBTITLE_STYLE, apply_shadow, rgba, table_card_height
from app.theme import COLOR_BORDER, COLOR_WARNING, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.relaciones_service import RelacionesService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard


class RelacionesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = RelacionesService()
        self.puestos: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        app_title.setStyleSheet(APP_TITLE_STYLE)
        module_title = QLabel("Relación Puesto-Objetos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(MODULE_TITLE_STYLE)
        subtitle = QLabel("Asignaciones definidas por puesto")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(app_title)
        layout.addWidget(module_title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        left = QVBoxLayout()
        puesto_label = QLabel("Puesto")
        puesto_label.setStyleSheet("font-size: 13px; font-weight: 800;")
        self.puesto_combo = QComboBox()
        self.puesto_combo.setFixedWidth(420)
        self.puesto_combo.currentIndexChanged.connect(lambda _index: self.refresh_relaciones())
        left.addWidget(puesto_label)
        left.addWidget(self.puesto_combo)

        add = AppButton("Agregar relación", "fa5s.plus", "outline")
        save = AppButton("Guardar cambios", "fa5s.save", "primary")
        add.clicked.connect(lambda: ConfirmDialog.show_mock(self))
        save.clicked.connect(lambda: ConfirmDialog.show_mock(self))

        controls.addLayout(left)
        controls.addStretch(1)
        controls.addWidget(add, 0, Qt.AlignBottom)
        controls.addWidget(save, 0, Qt.AlignBottom)
        layout.addLayout(controls)

        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(18)
        for index, item in enumerate(self.service.get_kpis()):
            kpi_grid.addWidget(KpiCard(item["icon"], item["value"], item["title"], item["color"]), 0, index)
        layout.addLayout(kpi_grid)

        warning = QFrame()
        warning.setStyleSheet(
            f"""
            QFrame {{
                background: {rgba(COLOR_WARNING, 0.08)};
                border: 1px solid {rgba(COLOR_WARNING, 0.34)};
                border-radius: 8px;
            }}
            """
        )
        warning_layout = QHBoxLayout(warning)
        warning_layout.setContentsMargins(18, 12, 18, 12)
        icon = QLabel()
        icon.setPixmap(icon_from_name("fa5s.exclamation-triangle", COLOR_WARNING).pixmap(22, 22))
        text = QLabel("Los cambios realizados en esta configuración afectarán únicamente a las asignaciones futuras.")
        text.setStyleSheet("color: #B7791F; font-size: 14px; font-weight: 700; border: none;")
        warning_layout.addWidget(icon)
        warning_layout.addWidget(text)
        warning_layout.addStretch(1)
        layout.addWidget(warning)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(8))
        table_card.setStyleSheet(f"QFrame#Card {{ border: 1px solid {COLOR_BORDER}; border-radius: 16px; }}")
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.columns = [
            ("puesto", "Puesto"),
            ("objeto", "Objeto"),
            ("cantidad", "Cantidad"),
            ("obligatorio", "Obligatorio"),
            ("devolucion", "Requiere devolución"),
            ("estado", "Estado"),
        ]
        self.table = DataTable()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
        layout.addStretch(1)
        self.refresh_puestos()

    def refresh_puestos(self) -> None:
        self.puestos = self.service.list_puestos()
        self.puesto_combo.blockSignals(True)
        self.puesto_combo.clear()
        for puesto in self.puestos:
            self.puesto_combo.addItem(puesto["nombre"], puesto["id"])
        self.puesto_combo.blockSignals(False)
        self.refresh_relaciones()

    def refresh_relaciones(self) -> None:
        puesto_id = self.puesto_combo.currentData()
        rows = self.service.list_relaciones(int(puesto_id)) if puesto_id else []
        self.table.set_data(
            self.columns,
            rows,
            badge_columns={"obligatorio", "devolucion", "estado"},
            center_columns={"cantidad"},
        )
