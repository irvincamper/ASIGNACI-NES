from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import apply_shadow, rgba
from app.theme import COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.mock_data import DASHBOARD_ALERTS, DASHBOARD_KPIS
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.kpi_card import KpiCard


class DashboardView(QWidget):
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
        module_title = QLabel("Panel General")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Resumen operativo del sistema")
        subtitle.setObjectName("Subtitle")

        title_block.addWidget(app_title)
        title_block.addSpacing(10)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        refresh = AppButton("Actualizar", "fa5s.sync-alt", "primary")
        refresh.clicked.connect(lambda: ConfirmDialog.show_mock(self))

        header.addLayout(title_block, 1)
        header.addWidget(refresh, 0, Qt.AlignTop)
        layout.addLayout(header)

        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(22)
        kpi_grid.setVerticalSpacing(18)
        for index, item in enumerate(DASHBOARD_KPIS):
            card = KpiCard(item["icon"], item["value"], item["title"], item["color"])
            kpi_grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(kpi_grid)

        alerts = QFrame()
        alerts.setObjectName("Card")
        apply_shadow(alerts)
        alerts_layout = QVBoxLayout(alerts)
        alerts_layout.setContentsMargins(24, 22, 24, 24)
        alerts_layout.setSpacing(14)

        section = QLabel("Alertas operativas")
        section.setObjectName("SectionTitle")
        alerts_layout.addWidget(section)

        for alert in DASHBOARD_ALERTS:
            alerts_layout.addWidget(self._alert_row(alert))

        layout.addWidget(alerts)
        layout.addStretch(1)

    def _alert_row(self, alert: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"""
            QFrame {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            """
        )
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 10, 18, 10)
        row_layout.setSpacing(18)

        icon = QLabel()
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name(alert["icon"], alert["color"]).pixmap(20, 20))
        icon.setStyleSheet(f"QLabel {{ background: {rgba(alert['color'], 0.12)}; border-radius: 20px; }}")

        text = QLabel(alert["text"])
        text.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; border: none;")

        value = QLabel(alert["value"])
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value.setStyleSheet(f"color: {alert['color']}; font-size: 15px; font-weight: 800; border: none;")

        row_layout.addWidget(icon)
        row_layout.addWidget(text, 1)
        row_layout.addWidget(value)
        return row
