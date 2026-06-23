from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.styles import APP_TITLE_STYLE, MODULE_TITLE_STYLE, SECTION_TITLE_STYLE, SUBTITLE_STYLE, apply_shadow
from app.theme import COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.empleados_service import EmpleadosService
from services.pdf_preview_service import PdfPreviewService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.status_badge import StatusBadge


class PdfPreviewView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = PdfPreviewService()
        self.empleados_service = EmpleadosService()
        self.preview = self._initial_preview()
        self.json_preliminar: dict = {}

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        self.main_layout.setSpacing(16)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        app_title.setStyleSheet(APP_TITLE_STYLE)
        module_title = QLabel("Vista previa de expediente")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(MODULE_TITLE_STYLE)
        subtitle = QLabel("Previsualización del reporte final por empleado")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        self.main_layout.addWidget(app_title)
        self.main_layout.addWidget(module_title)
        self.main_layout.addWidget(subtitle)

        self.main_layout.addWidget(self._form_card())

        self.body = QHBoxLayout()
        self.body.setSpacing(16)
        self.main_layout.addLayout(self.body, 1)
        self._render_body()

    def _initial_preview(self) -> dict:
        first = self.empleados_service.get_first_employee()
        if first:
            data = self.service.construir_preview_data(first["matricula"], "Contratación")
            if data.get("ok"):
                self.json_preliminar = data.get("json_preliminar", {})
                return data
        return self.service.empty_preview()

    def _form_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        apply_shadow(card)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        self.input_matricula = self._line_field("Matrícula", self.preview.get("matricula", ""), 120)
        self.input_matricula.returnPressed.connect(lambda: self._load_preview_from_matricula(show_errors=True))
        self.input_matricula.editingFinished.connect(lambda: self._load_preview_from_matricula(show_errors=False))

        self.input_nombre = self._line_field("Nombre del trabajador", self.preview.get("nombre", ""), 320)
        self.input_nombre.setReadOnly(True)

        motive_block = QVBoxLayout()
        motive_label = QLabel("Motivo de entrega-recepción")
        motive_label.setStyleSheet("font-size: 12px; font-weight: 800;")
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems(["Contratación", "Cambio de puesto", "Baja"])
        self.combo_motivo.setCurrentText(self.preview.get("motivo", "Contratación"))
        self.combo_motivo.currentTextChanged.connect(lambda _text: self._load_preview_from_matricula(show_errors=False))
        self.combo_motivo.setFixedWidth(230)
        motive_block.addWidget(motive_label)
        motive_block.addWidget(self.combo_motivo)

        search = AppButton("Generar vista previa", "fa5s.eye", "outline")
        download = AppButton("Descargar PDF", "fa5s.download", "primary")
        search.clicked.connect(self._generate_preview)
        download.clicked.connect(self._show_pdf_stage_3)

        ready = StatusBadge("PDF listo")
        ready.setFixedHeight(46)

        layout.addLayout(self._field_layout("Matrícula", self.input_matricula))
        layout.addLayout(self._field_layout("Nombre del trabajador", self.input_nombre))
        layout.addLayout(motive_block)
        layout.addStretch(1)
        layout.addWidget(search)
        layout.addWidget(download)
        layout.addWidget(ready)
        return card

    def _line_field(self, _label: str, value: str, width: int) -> QLineEdit:
        field = QLineEdit(value)
        field.setFixedWidth(width)
        return field

    def _field_layout(self, label: str, field: QLineEdit) -> QVBoxLayout:
        block = QVBoxLayout()
        block.setSpacing(6)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; font-weight: 800;")
        block.addWidget(label_widget)
        block.addWidget(field)
        return block

    def _load_preview_from_matricula(self, show_errors: bool) -> None:
        matricula = self.input_matricula.text().strip()
        if not matricula:
            return
        data = self.service.construir_preview_data(matricula, self.combo_motivo.currentText())
        if not data.get("ok"):
            self.input_nombre.clear()
            if show_errors:
                ConfirmDialog.show_message(self, "Vista previa", data.get("mensaje", "No se pudo cargar la matrícula."))
            return
        self.preview = data
        self.json_preliminar = data.get("json_preliminar", {})
        self.input_matricula.setText(data.get("matricula", ""))
        self.input_nombre.setText(data.get("nombre", ""))
        self._render_body()

    def _generate_preview(self) -> None:
        if not self.input_matricula.text().strip():
            ConfirmDialog.show_message(self, "Matrícula requerida", "Ingresa una matrícula para continuar.")
            return
        data = self.service.construir_preview_data(self.input_matricula.text(), self.combo_motivo.currentText())
        if not data.get("ok"):
            ConfirmDialog.show_message(self, "Vista previa", data.get("mensaje", "Primero busca una matrícula válida para generar la vista previa."))
            return
        self.preview = data
        self.json_preliminar = data.get("json_preliminar", {})
        self.input_matricula.setText(data.get("matricula", ""))
        self.input_nombre.setText(data.get("nombre", ""))
        self._render_body()
        ConfirmDialog.show_message(self, "Vista previa generada", "La maqueta se actualizó con datos reales. No se generó ningún PDF.")

    def _show_pdf_stage_3(self) -> None:
        ConfirmDialog.show_message(
            self,
            "Etapa 3",
            "La generación del PDF real se implementará en la Etapa 3. En esta etapa solo se muestra la vista previa con datos reales.",
        )

    def _render_body(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.body.addWidget(self._preview_card(), 1)
        self.body.addWidget(self._info_card())

    def _preview_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        apply_shadow(card)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(18, 14, 18, 14)

        document = QFrame()
        document.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: 3px solid #2A2F35;
                border-radius: 4px;
            }
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
        person_grid.addWidget(self._doc_cell(self.preview.get("nombre", ""), False), 0, 1)
        person_grid.addWidget(self._doc_cell("Matrícula:", True, COLOR_BLUE), 0, 2)
        person_grid.addWidget(self._doc_cell(self.preview.get("matricula", ""), False), 0, 3)
        doc_layout.addLayout(person_grid)

        help_text = QLabel("Los motivos de entrega-recepción pueden ser: CONTRATACIÓN, CAMBIO DE PUESTO O BAJA.")
        help_text.setStyleSheet("font-size: 11px; border: none;")
        doc_layout.addWidget(help_text)

        reason = QTableWidget(3, 3)
        reason.setHorizontalHeaderLabels(["Motivo", "Puesto", "Fecha"])
        reason.verticalHeader().setVisible(False)
        reason.setFixedHeight(112)
        reason.setShowGrid(True)
        reason.setEditTriggers(QAbstractItemView.NoEditTriggers)
        reason.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        reason.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        reason.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        reason.setStyleSheet(self._doc_table_style())
        motivo = self.preview.get("motivo", "Contratación")
        rows = ["Contratación", "Cambio de puesto", "Baja"]
        for index, value in enumerate(rows):
            mark = "X" if value == motivo else ""
            reason.setItem(index, 0, QTableWidgetItem(f"{mark}   {value}"))
            reason.setItem(index, 1, QTableWidgetItem(self.preview.get("puesto", "")))
            reason.setItem(index, 2, QTableWidgetItem(self.preview.get("fecha", "")))
        doc_layout.addWidget(reason)

        resource_title = QLabel("RECURSOS PARA ASIGNACIÓN Y/O DEVOLUCIÓN")
        resource_title.setAlignment(Qt.AlignCenter)
        resource_title.setStyleSheet("font-size: 12px; font-weight: 900; border: none;")
        doc_layout.addWidget(resource_title)
        doc_layout.addWidget(self._resources_table())

        footer = QHBoxLayout()
        left = QLabel("ALA-RH-FR-29 Entrega-recepción de equipos,\nherramientas, uniformes, EPP y papelería")
        center = QLabel(f"Página 1 de {self.preview.get('paginas_estimadas', 1)}")
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

    def _resources_table(self) -> QTableWidget:
        recursos = self.preview.get("recursos", [])
        table = QTableWidget(max(len(recursos), 1), 8)
        table.verticalHeader().setVisible(False)
        table.setHorizontalHeaderLabels(["No.", "Asignación", "Devolución", "Fecha", "Categoría", "Descripción", "Cantidad", "Firma"])
        table.setFixedHeight(260)
        table.setShowGrid(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setStyleSheet(self._doc_table_style())

        if not recursos:
            table.setSpan(0, 0, 1, 8)
            table.setItem(0, 0, QTableWidgetItem("No hay recursos asignados o pendientes para este empleado."))
            return table

        for row_index, item in enumerate(recursos):
            estado = item.get("estado", "")
            asignacion = "X" if estado in {"Pendiente", "Asignado"} else ""
            devolucion = "X" if estado == "Pendiente de devolución" else ""
            values = [
                str(row_index + 1),
                asignacion,
                devolucion,
                str(item.get("fecha") or ""),
                str(item.get("categoria") or ""),
                str(item.get("objeto") or item.get("concepto") or ""),
                str(item.get("cantidad") or ""),
                "",
            ]
            for column_index, value in enumerate(values):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        return table

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
        title.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(title)

        empleado = self.preview.get("empleado", {})
        plantilla = "FORMATO ENTREGA-RECEPCIÓN.xlsx detectado" if self.preview.get("plantilla_detectada") else "Plantilla no encontrada"
        items = [
            ("fa5s.user", "Empleado seleccionado", self.preview.get("nombre", "")),
            ("fa5s.id-card", "Matrícula", self.preview.get("matricula", "")),
            ("fa5s.briefcase", "Puesto", self.preview.get("puesto", "")),
            ("fa5s.clock", "Turno", self.preview.get("turno", "")),
            ("fa5s.shield-alt", "Estado", self.preview.get("estado", "")),
            ("fa5s.check-circle", "Asignados", str(empleado.get("asignados", 0))),
            ("fa5s.hourglass-half", "Pendientes", str(empleado.get("pendientes", 0))),
            ("fa5s.undo-alt", "Pendientes de devolución", str(empleado.get("pendientes_de_devolucion", 0))),
            ("fa5s.parking", "Estacionamiento", empleado.get("estacionamiento", "-")),
            ("fa5s.archive", "Locker", empleado.get("locker", "-")),
            ("fa5s.file-excel", "Plantilla detectada", plantilla),
            ("fa5s.cube", "Total de recursos", str(self.preview.get("total_recursos", 0))),
            ("fa5s.file-alt", "Páginas estimadas", str(self.preview.get("paginas_estimadas", 1))),
            ("fa5s.file-pdf", "Formato", "PDF"),
            ("fa5s.clipboard-list", "Reporte", "ALA-RH-FR-29"),
            ("fa5s.sync-alt", "Revisión", "2"),
        ]
        for icon_name, label, value in items:
            layout.addWidget(self._info_row(icon_name, label, str(value)))

        layout.addStretch(1)
        return card

    def _info_row(self, icon_name: str, label: str, value: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ border: none; border-bottom: 1px solid {COLOR_BORDER}; }}")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)

        icon = QLabel()
        icon.setFixedWidth(24)
        icon.setPixmap(icon_from_name(icon_name, COLOR_BLUE).pixmap(18, 18))

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; border: none;")

        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px; font-weight: 600; border: none;")

        layout.addWidget(icon)
        layout.addWidget(label_widget)
        layout.addWidget(value_widget, 1)
        return row
