from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.styles import apply_shadow
from app.theme import COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.formatters import icon_from_name
from utils.mock_data import PDF_PREVIEW, PDF_RECURSOS
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.status_badge import StatusBadge


class PdfPreviewView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(16)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        module_title = QLabel("Vista previa de expediente")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Previsualización del reporte final por empleado")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(app_title)
        layout.addWidget(module_title)
        layout.addWidget(subtitle)

        layout.addWidget(self._form_card())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._preview_card(), 1)
        body.addWidget(self._info_card())
        layout.addLayout(body, 1)

    def _form_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        apply_shadow(card)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        matricula = self._field("Matrícula", PDF_PREVIEW["matricula"], 120)
        nombre = self._field("Nombre del trabajador", PDF_PREVIEW["nombre"], 320)

        motive_block = QVBoxLayout()
        motive_label = QLabel("Motivo de entrega-recepción")
        motive_label.setStyleSheet("font-size: 12px; font-weight: 800;")
        motive = QComboBox()
        motive.addItems(["Contratación", "Cambio de puesto", "Baja"])
        motive.setCurrentText(PDF_PREVIEW["motivo"])
        motive.setFixedWidth(230)
        motive_block.addWidget(motive_label)
        motive_block.addWidget(motive)

        preview = AppButton("Generar vista previa", "fa5s.eye", "outline")
        download = AppButton("Descargar PDF", "fa5s.download", "primary")
        preview.clicked.connect(lambda: ConfirmDialog.show_mock(self))
        download.clicked.connect(lambda: ConfirmDialog.show_mock(self))

        ready = StatusBadge("PDF listo")
        ready.setFixedHeight(46)

        layout.addLayout(matricula)
        layout.addLayout(nombre)
        layout.addLayout(motive_block)
        layout.addStretch(1)
        layout.addWidget(preview)
        layout.addWidget(download)
        layout.addWidget(ready)
        return card

    def _field(self, label: str, value: str, width: int) -> QVBoxLayout:
        block = QVBoxLayout()
        block.setSpacing(6)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; font-weight: 800;")
        field = QLineEdit(value)
        field.setFixedWidth(width)
        block.addWidget(label_widget)
        block.addWidget(field)
        return block

    def _preview_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        apply_shadow(card)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(18, 14, 18, 14)

        document = QFrame()
        document.setStyleSheet(
            f"""
            QFrame {{
                background: #FFFFFF;
                border: 3px solid #2A2F35;
                border-radius: 4px;
            }}
            """
        )
        doc_layout = QVBoxLayout(document)
        doc_layout.setContentsMargins(28, 12, 28, 14)
        doc_layout.setSpacing(6)

        header = QHBoxLayout()
        logo = QLabel("A\nALAFLEX")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"color: {COLOR_BLUE}; font-size: 12px; font-weight: 900; border: none;")
        title = QLabel("Entrega-recepción de equipos, herramientas, uniformes, EPP y papelería")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 13px; font-weight: 800; border: none;")
        header.addWidget(logo)
        header.addWidget(title, 1)
        doc_layout.addLayout(header)

        person_grid = QGridLayout()
        person_grid.setSpacing(0)
        person_grid.addWidget(self._doc_cell("Nombre del trabajador:", True, COLOR_BLUE), 0, 0)
        person_grid.addWidget(self._doc_cell(PDF_PREVIEW["nombre"], False), 0, 1)
        person_grid.addWidget(self._doc_cell("Matrícula:", True, COLOR_BLUE), 0, 2)
        person_grid.addWidget(self._doc_cell(PDF_PREVIEW["matricula"], False), 0, 3)
        doc_layout.addLayout(person_grid)

        help_text = QLabel("Los motivos de entrega-recepción pueden ser: CONTRATACIÓN, CAMBIO DE PUESTO O BAJA.")
        help_text.setStyleSheet("font-size: 11px; border: none;")
        doc_layout.addWidget(help_text)

        reason = QTableWidget(2, 4)
        reason.setHorizontalHeaderLabels(["Motivo de entrega - recepción", "Puesto", "Fecha", ""])
        reason.verticalHeader().setVisible(False)
        reason.setFixedHeight(86)
        reason.setShowGrid(True)
        reason.setEditTriggers(QTableWidget.NoEditTriggers)
        reason.setStyleSheet(self._doc_table_style())
        reason.setItem(0, 0, QTableWidgetItem("X   Contratación"))
        reason.setItem(0, 1, QTableWidgetItem(PDF_PREVIEW["puesto_anterior"]))
        reason.setItem(1, 0, QTableWidgetItem("X   Cambio de puesto"))
        reason.setItem(1, 1, QTableWidgetItem(PDF_PREVIEW["puesto"]))
        reason.setItem(1, 2, QTableWidgetItem(PDF_PREVIEW["fecha"]))
        doc_layout.addWidget(reason)

        resource_title = QLabel("RECURSOS PARA ASIGNACIÓN Y/O DEVOLUCIÓN")
        resource_title.setAlignment(Qt.AlignCenter)
        resource_title.setStyleSheet("font-size: 12px; font-weight: 900; border: none;")
        doc_layout.addWidget(resource_title)

        resources = QTableWidget(len(PDF_RECURSOS), 8)
        resources.verticalHeader().setVisible(False)
        resources.setHorizontalHeaderLabels(["No.", "Asig.", "Fecha", "Categoría", "Descripción", "Cantidad", "Unidad", "Firma"])
        resources.setFixedHeight(260)
        resources.setShowGrid(True)
        resources.setEditTriggers(QTableWidget.NoEditTriggers)
        resources.setStyleSheet(self._doc_table_style())
        for row_index, item in enumerate(PDF_RECURSOS):
            values = [item["no"], item["tipo"], item["fecha"], item["categoria"], item["descripcion"], item["cantidad"], item["unidad"], item["firma"]]
            for column_index, value in enumerate(values):
                resources.setItem(row_index, column_index, QTableWidgetItem(value))
        doc_layout.addWidget(resources)

        footer = QHBoxLayout()
        left = QLabel("ALA-RH-FR-29 Entrega-recepción de equipos,\nherramientas, uniformes, EPP y papelería")
        center = QLabel("Página 1 de 2")
        right = QLabel("Revisión: 2")
        for label in (left, center, right):
            label.setStyleSheet("font-size: 10px; border: none;")
        center.setAlignment(Qt.AlignCenter)
        right.setAlignment(Qt.AlignRight)
        footer.addWidget(left)
        footer.addWidget(center, 1)
        footer.addWidget(right)
        doc_layout.addLayout(footer)

        outer.addWidget(document)
        return card

    def _doc_cell(self, text: str, bold: bool, background: str = "#FFFFFF") -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(34)
        label.setStyleSheet(
            f"""
            QLabel {{
                background: {background};
                color: {'#FFFFFF' if background != '#FFFFFF' else COLOR_TEXT};
                border: 1px solid #2A2F35;
                font-size: 11px;
                font-weight: {'800' if bold else '500'};
            }}
            """
        )
        return label

    def _doc_table_style(self) -> str:
        return f"""
        QTableWidget {{
            background: #FFFFFF;
            border: 1px solid #2A2F35;
            gridline-color: #2A2F35;
            font-size: 10px;
            color: {COLOR_TEXT};
        }}
        QHeaderView::section {{
            background: {COLOR_BLUE};
            color: #FFFFFF;
            border: 1px solid #2A2F35;
            min-height: 24px;
            font-size: 10px;
            font-weight: 800;
        }}
        QTableWidget::item {{
            border: none;
            padding: 2px;
        }}
        """

    def _info_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(360)
        apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title = QLabel("Información del documento")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        items = [
            ("fa5s.user", "Empleado seleccionado", PDF_PREVIEW["nombre"]),
            ("fa5s.id-card", "Matrícula", PDF_PREVIEW["matricula"]),
            ("fa5s.briefcase", "Puesto", PDF_PREVIEW["puesto"]),
            ("fa5s.calendar-alt", "Fecha del reporte", PDF_PREVIEW["fecha"]),
            ("fa5s.cube", "Total de recursos", PDF_PREVIEW["total_recursos"]),
            ("fa5s.file-alt", "Páginas", PDF_PREVIEW["paginas"]),
            ("fa5s.folder-open", "Ruta de salida", PDF_PREVIEW["ruta"]),
            ("fa5s.file-pdf", "Formato", PDF_PREVIEW["formato"]),
            ("fa5s.clipboard-list", "Reporte", PDF_PREVIEW["reporte"]),
            ("fa5s.sync-alt", "Revisión", PDF_PREVIEW["revision"]),
        ]
        for icon_name, label, value in items:
            layout.addWidget(self._info_row(icon_name, label, value))

        layout.addStretch(1)
        return card

    def _info_row(self, icon_name: str, label: str, value: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ border: none; border-bottom: 1px solid {COLOR_BORDER}; }}")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        icon = QLabel()
        icon.setFixedWidth(24)
        icon.setPixmap(icon_from_name(icon_name, COLOR_BLUE).pixmap(18, 18))

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; border: none;")

        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600; border: none;")

        layout.addWidget(icon)
        layout.addWidget(label_widget)
        layout.addWidget(value_widget, 1)
        return row
