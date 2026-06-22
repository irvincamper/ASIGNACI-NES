from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import apply_shadow, rgba, table_card_height
from app.theme import COLOR_BORDER, COLOR_WARNING, CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.mock_data import PUESTOS, RELACIONES, RELACIONES_KPIS
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.kpi_card import KpiCard


class RelacionesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        module_title = QLabel("Relación Puesto-Objetos")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Asignaciones definidas por puesto")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(app_title)
        layout.addWidget(module_title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        left = QVBoxLayout()
        puesto_label = QLabel("Puesto")
        puesto_label.setStyleSheet("font-size: 13px; font-weight: 800;")
        puesto = QComboBox()
        puesto.addItems(PUESTOS)
        puesto.setFixedWidth(420)
        left.addWidget(puesto_label)
        left.addWidget(puesto)

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
        for index, item in enumerate(RELACIONES_KPIS):
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
        text.setStyleSheet(f"color: #B7791F; font-size: 14px; font-weight: 700; border: none;")
        warning_layout.addWidget(icon)
        warning_layout.addWidget(text)
        warning_layout.addStretch(1)
        layout.addWidget(warning)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(len(RELACIONES)))
        table_card.setStyleSheet(f"QFrame#Card {{ border: 1px solid {COLOR_BORDER}; border-radius: 16px; }}")
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        table = DataTable()
        table.set_data(
            [
                ("puesto", "Puesto"),
                ("objeto", "Objeto"),
                ("cantidad", "Cantidad"),
                ("obligatorio", "Obligatorio"),
                ("devolucion", "Requiere devolución"),
                ("estado", "Estado"),
            ],
            RELACIONES,
            badge_columns={"obligatorio", "devolucion", "estado"},
            center_columns={"cantidad"},
        )
        table_layout.addWidget(table)
        layout.addWidget(table_card)
        layout.addStretch(1)
