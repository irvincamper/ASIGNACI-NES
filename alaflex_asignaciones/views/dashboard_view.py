from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.styles import SECTION_TITLE_STYLE, apply_shadow, rgba
from app.theme import COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.dashboard_service import DashboardService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.kpi_card import KpiCard


class DashboardView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = DashboardService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(8)

        module_title = QLabel("Panel General")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(self._module_title_style())
        subtitle = QLabel("Resumen operativo del sistema")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(self._subtitle_style())

        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)

        refresh = AppButton("Actualizar", "fa5s.sync-alt", "primary")
        refresh.clicked.connect(self.refresh_data)

        header.addLayout(title_block, 1)
        header.addWidget(refresh, 0, Qt.AlignTop)
        layout.addLayout(header)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setHorizontalSpacing(22)
        self.kpi_grid.setVerticalSpacing(18)
        layout.addLayout(self.kpi_grid)

        alerts = QFrame()
        alerts.setObjectName("Card")
        alerts.setMinimumHeight(330)
        apply_shadow(alerts)
        alerts_layout = QVBoxLayout(alerts)
        alerts_layout.setContentsMargins(24, 22, 24, 24)
        alerts_layout.setSpacing(14)

        section = QLabel("Alertas operativas")
        section.setObjectName("SectionTitle")
        section.setStyleSheet(SECTION_TITLE_STYLE + "; border: none;")
        alerts_layout.addWidget(section)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        rows_container = QWidget()
        rows_container.setStyleSheet("background: transparent;")
        self.alerts_layout = QVBoxLayout(rows_container)
        self.alerts_layout.setContentsMargins(0, 0, 0, 0)
        self.alerts_layout.setSpacing(10)
        scroll.setWidget(rows_container)
        alerts_layout.addWidget(scroll, 1)

        layout.addWidget(alerts)
        layout.addStretch(1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self._clear_grid(self.kpi_grid)
        for index, item in enumerate(self.service.get_kpis()):
            card = KpiCard(item["icon"], item["value"], item["title"], item["color"])
            self.kpi_grid.addWidget(card, index // 3, index % 3)

        while self.alerts_layout.count():
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for alert in self.service.get_alerts():
            self.alerts_layout.addWidget(self._alert_row(alert))
        self.alerts_layout.addStretch(1)

    def _clear_grid(self, layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _module_title_style(self) -> str:
        return f"color: {COLOR_TEXT}; font-size: 42px; font-weight: 900;"

    def _subtitle_style(self) -> str:
        return f"color: {COLOR_TEXT_MUTED}; font-size: 18px;"

    def _alert_row(self, alert: dict) -> QFrame:
        row = QFrame()
        row.setFixedHeight(48)
        row.setStyleSheet(
            f"""
            QFrame#AlertRow {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            """
        )
        row.setObjectName("AlertRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 5, 18, 5)
        row_layout.setSpacing(18)

        icon = QLabel()
        icon.setFixedSize(34, 34)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name(alert["icon"], alert["color"]).pixmap(17, 17))
        icon.setStyleSheet(f"QLabel {{ background: {rgba(alert['color'], 0.12)}; border: none; border-radius: 17px; }}")

        text = QLabel(alert["text"])
        text.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; border: none;")

        value = QLabel(alert["value"])
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value.setStyleSheet(f"color: {alert['color']}; font-size: 15px; font-weight: 800; border: none;")

        row_layout.addWidget(icon)
        row_layout.addWidget(text, 1)
        row_layout.addWidget(value)
        return row
