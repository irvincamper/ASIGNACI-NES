from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.styles import SECTION_TITLE_STYLE, apply_shadow
from app.theme import COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.empleados_service import EmpleadosService
from services.expediente_metadata_service import ExpedienteMetadataService
from services.pdf_expediente_service import PdfExpedienteService
from services.pdf_preview_service import PdfPreviewService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.status_badge import StatusBadge


PDF_PREVIEW_SCALE = 0.72
PDF_PREVIEW_BASE_WIDTH = 805
PDF_PREVIEW_BASE_HEIGHT = 1050
PDF_PREVIEW_WIDTH = int(PDF_PREVIEW_BASE_WIDTH * PDF_PREVIEW_SCALE)
PDF_PREVIEW_HEIGHT = int(PDF_PREVIEW_BASE_HEIGHT * PDF_PREVIEW_SCALE)
PDF_PREVIEW_ROWS_PER_PAGE = 16


class PdfPreviewView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = PdfPreviewService()
        self.empleados_service = EmpleadosService()
        self.pdf_service = PdfExpedienteService()
        self.expediente_metadata = ExpedienteMetadataService()
        self.json_preliminar: dict = {}
        self.preview = self._initial_preview()
        self.preview_generado = bool(self.preview.get("ok"))
        self.generated_pdf_path = ""
        self.edit_mode = False
        self.has_unsaved_changes = False
        self._loading_form = False
        self.current_matricula = str(self.preview.get("matricula", ""))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(CONTENT_PADDING_X, 24, CONTENT_PADDING_X, 22)
        self.main_layout.setSpacing(12)

        module_title = QLabel("Vista previa de expediente")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(self._module_title_style())
        subtitle = QLabel("Previsualización del reporte final por empleado")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(self._subtitle_style())
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
            data = self.service.construir_preview_data(first["matricula"], "Contrataci\u00f3n")
            if data.get("ok"):
                self.json_preliminar = data.get("json_preliminar", {})
                return data
        return self.service.empty_preview()

    def _module_title_style(self) -> str:
        return f"color: {COLOR_TEXT}; font-size: 34px; font-weight: 900;"

    def _subtitle_style(self) -> str:
        return f"color: {COLOR_TEXT_MUTED}; font-size: 16px;"

    def _form_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._panel_card_style())
        card.setMinimumHeight(126)
        card.setMaximumHeight(150)
        apply_shadow(card, blur=18, y_offset=4, alpha=22)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(18)

        self.input_matricula = self._line_field("Matrícula", self.preview.get("matricula", ""), 150)
        self.input_matricula.returnPressed.connect(lambda: self._request_load_current_matricula(show_errors=True))
        self.input_matricula.editingFinished.connect(lambda: self._request_load_current_matricula(show_errors=False))

        self.input_nombre = self._line_field("Nombre del trabajador", self.preview.get("nombre", ""), 360)
        self.input_nombre.setReadOnly(True)
        self.input_nombre.setToolTip(str(self.preview.get("nombre", "")))
        self.input_nombre.setCursorPosition(0)
        self.input_nombre.textEdited.connect(self._mark_unsaved_change)

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems(["Contratación", "Cambio de puesto", "Baja"])
        self.combo_motivo.setCurrentText(self.preview.get("motivo", "Contratación"))
        self.combo_motivo.currentTextChanged.connect(self._motivo_changed)
        self.combo_motivo.setFixedWidth(270)

        edit = AppButton("Editar PDF", "fa5s.edit", "outline")
        save = AppButton("Guardar cambios", "fa5s.save", "primary")
        download = AppButton("Descargar PDF", "fa5s.download", "primary")
        edit.setFixedSize(170, 46)
        save.setFixedSize(190, 46)
        download.setFixedSize(170, 46)
        for button in (edit, save, download):
            button.setIconSize(QSize(15, 15))
            button.setStyleSheet(
                button.styleSheet()
                + """
                QPushButton {
                    font-size: 13px;
                    padding-left: 8px;
                    padding-right: 8px;
                }
                """
            )
        edit.clicked.connect(self._enable_edit_mode)
        save.clicked.connect(self._save_changes)
        download.clicked.connect(self._download_pdf)

        self.ready_badge = StatusBadge("PDF listo")
        self.ready_badge.setFixedSize(130, 46)

        left_fields = QWidget()
        left_fields.setStyleSheet("background: transparent;")
        left_fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        fields_layout = QHBoxLayout(left_fields)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(28)
        fields_layout.addWidget(
            self._field_widget(
                "Matrícula",
                self.input_matricula,
                170,
                "La vista previa se carga automáticamente al ingresar la matrícula.",
            )
        )
        fields_layout.addWidget(self._field_widget("Nombre del trabajador", self.input_nombre, 360))
        fields_layout.addWidget(self._field_widget("Motivo de entrega-recepción", self.combo_motivo, 270))
        fields_layout.addStretch(1)

        actions = QGridLayout()
        actions.setHorizontalSpacing(12)
        actions.setVerticalSpacing(10)
        actions.addWidget(edit, 0, 0)
        actions.addWidget(save, 0, 1)
        actions.addWidget(download, 1, 0)
        actions.addWidget(self.ready_badge, 1, 1)

        layout.addWidget(left_fields, 1)
        layout.addLayout(actions)
        return card

    def _combo_layout(self, label: str, combo: QComboBox) -> QVBoxLayout:
        block = QVBoxLayout()
        block.setSpacing(6)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; font-weight: 800;")
        block.addWidget(label_widget)
        block.addWidget(combo)
        return block

    def _line_field(self, _label: str, value: str, width: int) -> QLineEdit:
        field = QLineEdit(value)
        field.setFixedWidth(width)
        field.setMinimumHeight(42)
        return field

    def _field_layout(self, label: str, field: QLineEdit) -> QVBoxLayout:
        block = QVBoxLayout()
        block.setSpacing(6)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; font-weight: 800;")
        block.addWidget(label_widget)
        block.addWidget(field)
        return block

    def _field_widget(self, label: str, field: QWidget, width: int, hint: str | None = None) -> QWidget:
        container = QWidget()
        container.setFixedWidth(width)
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; font-weight: 800; border: none;")
        layout.addWidget(label_widget)
        layout.addWidget(field)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet(f"color: {COLOR_BLUE}; font-size: 11px; border: none;")
            layout.addWidget(hint_label)
        else:
            layout.addSpacing(28)
        return container

    def _request_load_current_matricula(self, show_errors: bool) -> None:
        target = self.input_matricula.text().strip()
        if not target or target == self.current_matricula:
            return
        if self.has_unsaved_changes:
            decision = self._ask_unsaved_changes()
            if decision == "cancel":
                self._loading_form = True
                self.input_matricula.setText(self.current_matricula)
                self._loading_form = False
                return
            if decision == "save" and not self._save_changes(silent=True):
                self.input_matricula.setText(self.current_matricula)
                return
            if decision == "discard":
                self.has_unsaved_changes = False
                self.edit_mode = False
        self._load_preview_from_matricula(show_errors=show_errors)

    def _motivo_changed(self, _text: str) -> None:
        if self._loading_form:
            return
        if self.edit_mode:
            self._mark_unsaved_change()
            self._apply_form_edits_to_preview()
            self._render_body()
            return
        self._load_preview_from_matricula(show_errors=False)

    def _enable_edit_mode(self) -> None:
        if not self.preview_generado:
            ConfirmDialog.show_message(self, "Vista previa requerida", "Ingresa una matr\u00edcula v\u00e1lida antes de editar el expediente.")
            return
        self.edit_mode = True
        self.input_nombre.setReadOnly(False)
        self.input_nombre.setFocus()
        ConfirmDialog.show_message(self, "Editar PDF", "Modo edici\u00f3n activado. Puedes modificar los campos permitidos del expediente.")

    def _mark_unsaved_change(self, *_args) -> None:
        if self._loading_form or not self.edit_mode:
            return
        self.has_unsaved_changes = True
        self._apply_form_edits_to_preview()

    def _apply_form_edits_to_preview(self) -> None:
        nombre = self.input_nombre.text().strip()
        motivo = self.combo_motivo.currentText()
        empleado = dict(self.preview.get("empleado", {}))
        empleado["nombre"] = nombre
        self.preview = {**self.preview, "nombre": nombre, "motivo": motivo, "empleado": empleado}
        if self.json_preliminar:
            self.json_preliminar = {
                **self.json_preliminar,
                "motivo": motivo,
                "empleado": {**self.json_preliminar.get("empleado", {}), "nombre": nombre},
            }

    def _save_changes(self, silent: bool = False) -> bool:
        if not self.has_unsaved_changes:
            if not silent:
                ConfirmDialog.show_message(self, "Guardar cambios", "No hay cambios pendientes.")
            return True
        self._apply_form_edits_to_preview()
        self.has_unsaved_changes = False
        self.edit_mode = False
        self.input_nombre.setReadOnly(True)
        self.generated_pdf_path = ""
        self._render_body()
        if not silent:
            ConfirmDialog.show_message(self, "Guardar cambios", "Cambios guardados en la vista previa del expediente.")
        return True

    def _ask_unsaved_changes(self) -> str:
        dialog = QDialog(self)
        dialog.setWindowTitle("Cambios sin guardar")
        dialog.setModal(True)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setFixedWidth(620)
        dialog.setStyleSheet("QDialog { background: #F4F6FA; }")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 20)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._panel_card_style())
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 22)
        card_layout.setSpacing(16)

        title = QLabel("Cambios sin guardar")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 20px; font-weight: 900;")
        message = QLabel("Tienes cambios sin guardar. ¿Deseas guardar antes de continuar con la nueva matrícula?")
        message.setWordWrap(True)
        message.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        save = QPushButton("Guardar y continuar")
        discard = QPushButton("No guardar y continuar")
        cancel = QPushButton("Cancelar")
        save.setStyleSheet(self._dialog_button_style("primary"))
        discard.setStyleSheet(self._dialog_button_style("outline"))
        cancel.setStyleSheet(self._dialog_button_style("secondary"))
        for button in (save, discard, cancel):
            button.setCursor(Qt.PointingHandCursor)
            buttons.addWidget(button)

        result = {"value": "cancel"}
        save.clicked.connect(lambda: (result.update(value="save"), dialog.accept()))
        discard.clicked.connect(lambda: (result.update(value="discard"), dialog.accept()))
        cancel.clicked.connect(dialog.reject)

        card_layout.addWidget(title)
        card_layout.addWidget(message)
        card_layout.addLayout(buttons)
        layout.addWidget(card)
        self._center_dialog(dialog)
        dialog.exec()
        return result["value"]

    def _center_dialog(self, dialog: QDialog) -> None:
        parent_window = self.window()
        if not parent_window:
            return
        parent_geo = parent_window.frameGeometry()
        dialog_geo = dialog.frameGeometry()
        dialog_geo.moveCenter(parent_geo.center())
        dialog.move(dialog_geo.topLeft())

    def _dialog_button_style(self, variant: str) -> str:
        if variant == "primary":
            return f"background: {COLOR_BLUE}; color: #FFFFFF; border: 1px solid {COLOR_BLUE}; border-radius: 8px; min-height: 42px; font-weight: 700;"
        if variant == "outline":
            return f"background: #FFFFFF; color: {COLOR_BLUE}; border: 1px solid {COLOR_BLUE}; border-radius: 8px; min-height: 42px; font-weight: 700;"
        return f"background: #FFFFFF; color: {COLOR_TEXT_MUTED}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; min-height: 42px; font-weight: 700;"

    def _load_preview_from_matricula(self, show_errors: bool) -> None:
        matricula = self.input_matricula.text().strip()
        if not matricula:
            return
        data = self.service.construir_preview_data(matricula, self.combo_motivo.currentText())
        if not data.get("ok"):
            self.input_nombre.clear()
            if show_errors:
                ConfirmDialog.show_message(self, "Vista previa", data.get("mensaje", "No se pudo cargar la matr\u00edcula."))
            return
        self._loading_form = True
        self.preview = data
        self.json_preliminar = data.get("json_preliminar", {})
        self.preview_generado = True
        self.has_unsaved_changes = False
        self.edit_mode = False
        self.generated_pdf_path = ""
        self.current_matricula = data.get("matricula", "")
        self.input_matricula.setText(data.get("matricula", ""))
        self.input_nombre.setText(data.get("nombre", ""))
        self.input_nombre.setCursorPosition(0)
        self.input_nombre.setReadOnly(True)
        self.combo_motivo.setCurrentText(data.get("motivo", "Contrataci\u00f3n"))
        self._loading_form = False
        self._render_body()

    def _download_pdf(self) -> None:
        if not self.preview_generado or not self.json_preliminar:
            ConfirmDialog.show_message(self, "Vista previa requerida", "Ingresa una matr\u00edcula v\u00e1lida antes de descargar el PDF.")
            return
        if self.has_unsaved_changes:
            ConfirmDialog.show_message(self, "Cambios sin guardar", "Guarda los cambios pendientes antes de descargar el PDF.")
            return
        if not self.preview.get("recursos"):
            ConfirmDialog.show_message(self, "Sin asignaciones", "El empleado no tiene asignaciones para generar el expediente.")
            return
        if self.generated_pdf_path:
            ConfirmDialog.show_message(self, "PDF listo", f"PDF generado correctamente.\n\n{self.generated_pdf_path}")
            return
        if not ConfirmDialog.ask(self, "Descargar PDF", "\u00bfDeseas generar y registrar el expediente PDF?"):
            return
        try:
            snapshot = dict(self.json_preliminar)
            ruta_pdf = self.pdf_service.generar_pdf_expediente(snapshot)
            snapshot["ruta_pdf"] = ruta_pdf
            expediente_id = self.expediente_metadata.registrar(snapshot, ruta_pdf)
            self.json_preliminar = snapshot
            self.generated_pdf_path = ruta_pdf
            self.preview = {**self.preview, "ruta_pdf": ruta_pdf, "expediente_id": expediente_id}
            self._render_body()
            ConfirmDialog.show_message(self, "PDF generado", "PDF generado correctamente.")
        except Exception:  # noqa: BLE001 - mensaje operativo requerido
            ConfirmDialog.show_message(self, "Error PDF", "No fue posible generar el PDF. Revisa los datos del expediente.")

    def _render_body(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.body.addWidget(self._preview_card(), 1)
        self.body.addWidget(self._info_card(), 0)

    def _preview_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._panel_card_style())
        apply_shadow(card, blur=18, y_offset=4, alpha=22)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._viewer_toolbar())

        viewport = QScrollArea()
        viewport.setWidgetResizable(True)
        viewport.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        viewport.setMinimumHeight(320)
        viewport.setFrameShape(QFrame.NoFrame)
        viewport.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        viewport.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        viewport.setStyleSheet(
            """
            QScrollArea {
                background: #EEF3FA;
                border: none;
                border-top: 1px solid #E1E6F0;
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #B9C4D6;
                border-radius: 5px;
                min-height: 36px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )
        canvas = QWidget()
        canvas.setStyleSheet("background: #EEF3FA;")
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(14, 18, 14, 18)
        canvas_layout.setSpacing(18)
        page_count = self._preview_page_count()
        for page_index in range(page_count):
            canvas_layout.addWidget(self._document_sheet(page_index, page_count), 0, Qt.AlignHCenter | Qt.AlignTop)
        canvas_layout.addStretch(1)
        viewport.setWidget(canvas)
        outer.addWidget(viewport, 1)
        return card

    def _preview_page_count(self) -> int:
        recursos = self.preview.get("recursos", [])
        return max(2, (len(recursos) + PDF_PREVIEW_ROWS_PER_PAGE - 1) // PDF_PREVIEW_ROWS_PER_PAGE)

    def _viewer_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: none;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            """
        )
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)
        toolbar.setFixedHeight(58)

        title = QLabel("Vista previa del documento")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 800; border: none;")
        layout.addWidget(title)
        layout.addStretch(1)

        for text, icon in [
            ("", "fa5s.chevron-left"),
            ("", "fa5s.chevron-right"),
        ]:
            layout.addWidget(self._viewer_button(text, icon))
        page = QLabel(f"1 de {self._preview_page_count()}")
        page.setAlignment(Qt.AlignCenter)
        page.setFixedWidth(56)
        page.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: 700; border: none;")
        layout.addWidget(page)

        layout.addSpacing(8)
        layout.addWidget(self._viewer_button("", "fa5s.minus"))
        zoom = QComboBox()
        zoom.addItems(["70%"])
        zoom.setCurrentText("70%")
        zoom.setFixedWidth(84)
        layout.addWidget(zoom)
        layout.addWidget(self._viewer_button("", "fa5s.plus"))
        layout.addSpacing(8)
        layout.addWidget(self._viewer_button("", "fa5s.expand"))
        layout.addWidget(self._viewer_button("", "fa5s.print"))
        return toolbar

    def _viewer_button(self, text: str, icon_name: str) -> AppButton:
        button = AppButton(text, icon_name, "outline")
        button.setFixedSize(38, 36)
        button.setEnabled(False)
        button.setStyleSheet(
            button.styleSheet()
            + """
            QPushButton {
                padding-left: 0px;
                padding-right: 0px;
            }
            """
        )
        return button

    def _document_sheet(self, page_index: int, page_count: int) -> QFrame:
        document = QFrame()
        document.setFixedSize(PDF_PREVIEW_WIDTH, PDF_PREVIEW_HEIGHT)
        document.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        document.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
            }
            """
        )
        apply_shadow(document, blur=18, y_offset=5, alpha=20)
        doc_layout = QVBoxLayout(document)
        doc_layout.setContentsMargins(22, 16, 22, 16)
        doc_layout.setSpacing(7)

        header = QHBoxLayout()
        logo = QLabel("A\nALAFLEX")
        logo.setAlignment(Qt.AlignCenter)
        logo.setMinimumWidth(88)
        logo.setStyleSheet(f"color: {COLOR_BLUE}; font-size: 10px; font-weight: 900; border: none;")
        title = QLabel("Entrega-recepci\u00f3n de equipos, herramientas, uniformes, EPP y papeler\u00eda")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 12px; font-weight: 800; border: none;")
        header.addWidget(logo)
        header.addWidget(title, 1)
        doc_layout.addLayout(header)

        person_grid = QGridLayout()
        person_grid.setSpacing(0)
        person_grid.setColumnStretch(0, 13)
        person_grid.setColumnStretch(1, 35)
        person_grid.setColumnStretch(2, 7)
        person_grid.setColumnStretch(3, 5)
        person_grid.addWidget(self._doc_cell("Nombre del trabajador:", True, COLOR_BLUE), 0, 0)
        person_grid.addWidget(self._doc_cell(self.preview.get("nombre", ""), False), 0, 1)
        person_grid.addWidget(self._doc_cell("Matr\u00edcula:", True, COLOR_BLUE), 0, 2)
        person_grid.addWidget(self._doc_cell(self.preview.get("matricula", ""), False), 0, 3)
        doc_layout.addLayout(person_grid)

        help_text = QLabel("Los motivos de entrega-recepci\u00f3n pueden ser: CONTRATACI\u00d3N, CAMBIO DE PUESTO O BAJA.")
        help_text.setStyleSheet("font-size: 9px; border: none;")
        doc_layout.addWidget(help_text)

        reason = QTableWidget(3, 3)
        reason.setHorizontalHeaderLabels(["Motivo", "Puesto", "Fecha"])
        reason.verticalHeader().setVisible(False)
        reason.setFixedHeight(94)
        reason.setShowGrid(True)
        reason.setEditTriggers(QAbstractItemView.NoEditTriggers)
        reason.verticalHeader().setMinimumSectionSize(1)
        reason.verticalHeader().setDefaultSectionSize(20)
        for row in range(3):
            reason.setRowHeight(row, 20)
        reason.horizontalHeader().setFixedHeight(24)
        reason.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        reason.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        reason.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        reason.setStyleSheet(self._doc_table_style())
        motivo = self.preview.get("motivo", "Contrataci\u00f3n")
        rows = ["Contrataci\u00f3n", "Cambio de puesto", "Baja"]
        for index, value in enumerate(rows):
            mark = "X" if value == motivo else ""
            reason.setItem(index, 0, QTableWidgetItem(f"{mark}   {value}"))
            reason.setItem(index, 1, QTableWidgetItem(self.preview.get("puesto", "")))
            reason.setItem(index, 2, QTableWidgetItem(self.preview.get("fecha", "")))
        doc_layout.addWidget(reason)

        resource_title = QLabel("RECURSOS PARA ASIGNACI\u00d3N Y/O DEVOLUCI\u00d3N")
        resource_title.setAlignment(Qt.AlignCenter)
        resource_title.setStyleSheet("font-size: 11px; font-weight: 900; border: none;")
        doc_layout.addWidget(resource_title)
        doc_layout.addWidget(self._resources_table(page_index))
        doc_layout.addStretch(1)

        footer = QHBoxLayout()
        left = QLabel("ALA-RH-FR-29 Entrega-recepci\u00f3n de equipos,\nherramientas, uniformes, EPP y papeler\u00eda")
        center = QLabel(f"P\u00e1gina {page_index + 1} de {page_count}")
        right = QLabel("Revisi\u00f3n: 2")
        for label in (left, center, right):
            label.setStyleSheet("font-size: 8px; border: none;")
        center.setAlignment(Qt.AlignCenter)
        right.setAlignment(Qt.AlignRight)
        footer.addWidget(left)
        footer.addWidget(center, 1)
        footer.addWidget(right)
        doc_layout.addLayout(footer)
        return document

    def _resources_table(self, page_index: int) -> QTableWidget:
        recursos = self.preview.get("recursos", [])
        row_count = PDF_PREVIEW_ROWS_PER_PAGE
        table = QTableWidget(row_count, 14)
        table.verticalHeader().setVisible(False)
        table.setHorizontalHeaderLabels(
            [
                "No.",
                "Asig.",
                "Dev.",
                "Fecha",
                "Equipo",
                "Herr.",
                "Unif.",
                "EPP",
                "Papel.",
                "Otros",
                "Descripci\u00f3n",
                "Cant.",
                "Unidad",
                "Firma",
            ]
        )
        table.setFixedHeight(370)
        table.setShowGrid(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setMinimumSectionSize(1)
        table.verticalHeader().setDefaultSectionSize(21)
        table.horizontalHeader().setMinimumSectionSize(1)
        table.horizontalHeader().setFixedHeight(28)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setStyleSheet(self._doc_table_style())
        self._apply_resource_column_widths(table)

        if not recursos:
            table.setSpan(0, 0, 1, 14)
            table.setItem(0, 0, QTableWidgetItem("No hay recursos asignados para este empleado."))
            return table

        start = page_index * PDF_PREVIEW_ROWS_PER_PAGE
        for row_index in range(row_count):
            table.setRowHeight(row_index, 21)
            resource_index = start + row_index
            item = recursos[resource_index] if resource_index < len(recursos) else {}
            values = self._resource_preview_values(item, resource_index + 1) if item else [""] * 14
            for column_index, value in enumerate(values):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        return table

    def _apply_resource_column_widths(self, table: QTableWidget) -> None:
        content_width = PDF_PREVIEW_WIDTH - 52
        weights = [3.7, 3.2, 13, 12.7, 3.2, 13, 13, 13, 13, 13, 33.6, 8.6, 13, 15.7]
        total_weight = sum(weights)
        used_width = 0
        for column, weight in enumerate(weights):
            if column == len(weights) - 1:
                width = max(1, content_width - used_width)
            else:
                width = max(1, int(content_width * weight / total_weight))
                used_width += width
            table.setColumnWidth(column, width)

    def _resource_preview_values(self, item: dict, number: int) -> list[str]:
        tipo = item.get("tipo_operacion", "")
        asignacion = "X" if tipo in {"", "Asignacion", "Asignaci\u00f3n"} else ""
        devolucion = "X" if tipo in {"Devolucion", "Devoluci\u00f3n"} else ""
        category = str(item.get("categoria") or "").lower()
        category_values = ["", "", "", "", "", ""]
        if "herramient" in category:
            category_values[1] = "X"
        elif "uniform" in category or "vestimenta" in category:
            category_values[2] = "X"
        elif "seguridad" in category or "epp" in category:
            category_values[3] = "X"
        elif "papeler" in category:
            category_values[4] = "X"
        elif "equipo" in category or "tecnolog" in category:
            category_values[0] = "X"
        else:
            category_values[5] = "X"
        return [
            str(number),
            asignacion,
            devolucion,
            str(item.get("fecha") or ""),
            *category_values,
            str(item.get("objeto") or item.get("concepto") or ""),
            str(item.get("cantidad") or ""),
            str(item.get("unidad") or ""),
            "",
        ]

    def _doc_cell(self, text: str, bold: bool, background: str = "#FFFFFF") -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(28)
        label.setStyleSheet(
            f"""
            QLabel {{
                background: {background};
                color: {'#FFFFFF' if background != '#FFFFFF' else COLOR_TEXT};
                border: 1px solid #2A2F35;
                font-size: 9px;
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
            font-size: 8px;
            color: {COLOR_TEXT};
        }}
        QHeaderView::section {{
            background: {COLOR_BLUE};
            color: #FFFFFF;
            border: 1px solid #2A2F35;
            min-height: 20px;
            padding: 1px;
            font-size: 8px;
            font-weight: 800;
        }}
        QTableWidget::item {{
            border: none;
            padding: 1px;
        }}
        """

    def _info_card(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(430)
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        panel.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        info_scroll.setMinimumHeight(260)
        info_scroll.setFrameShape(QFrame.NoFrame)
        info_scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #B9C4D6;
                border-radius: 4px;
                min-height: 32px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )
        info_scroll.setWidget(self._document_info_panel())

        layout.addWidget(info_scroll, 1)
        return panel

    def _document_info_panel(self) -> QFrame:
        card = self._side_card("Informaci\u00f3n del documento")
        layout = card.layout()

        empleado = self.preview.get("empleado", {})
        items = [
            ("fa5s.user", "Empleado seleccionado", self.preview.get("nombre", "")),
            ("fa5s.id-card", "Matr\u00edcula", self.preview.get("matricula", "")),
            ("fa5s.briefcase", "Puesto", self.preview.get("puesto", "")),
            ("fa5s.clock", "Turno", self.preview.get("turno", "")),
            ("fa5s.shield-alt", "Estado", self.preview.get("estado", "")),
            ("fa5s.cube", "Objetos asignados", str(self.preview.get("total_recursos", 0))),
            ("fa5s.parking", "Estacionamiento", empleado.get("estacionamiento", "-")),
            ("fa5s.archive", "Locker", empleado.get("locker", "-")),
            ("fa5s.cube", "Total de recursos", str(self.preview.get("total_recursos", 0))),
            ("fa5s.file-pdf", "Formato", "ALA-RH-FR-29"),
            ("fa5s.sync-alt", "Revisi\u00f3n", "2"),
            ("fa5s.clock", "\u00daltima actualizaci\u00f3n", datetime.now().strftime("%d/%m/%Y %H:%M")),
            ("fa5s.user-cog", "Generado por", "ALAFLEX"),
        ]
        if self.generated_pdf_path or self.preview.get("ruta_pdf"):
            items.append(("fa5s.folder-open", "Ruta PDF", self.generated_pdf_path or self.preview.get("ruta_pdf", "")))
        for icon_name, label, value in items:
            layout.addWidget(self._info_row(icon_name, label, str(value)))

        historial = []
        if self.preview.get("matricula"):
            historial = self.expediente_metadata.listar_por_matricula(str(self.preview.get("matricula", "")))
        if historial:
            history_title = QLabel("Expedientes anteriores")
            history_title.setObjectName("SectionTitle")
            history_title.setStyleSheet(SECTION_TITLE_STYLE + "; font-size: 15px;")
            layout.addWidget(history_title)
            for item in historial[:4]:
                file_name = Path(str(item.get("ruta_pdf") or "")).name
                label = f"{item.get('fecha_generacion', '')} | {item.get('motivo', '')}"
                value = f"{item.get('total_recursos', 0)} recursos | {file_name}"
                layout.addWidget(self._info_row("fa5s.file-pdf", label, value))

        layout.addStretch(1)
        return card

    def _side_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._panel_card_style())
        apply_shadow(card, blur=16, y_offset=4, alpha=18)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        title_label.setStyleSheet(SECTION_TITLE_STYLE + "; font-size: 17px;")
        layout.addWidget(title_label)
        return card

    def _info_row(self, icon_name: str, label: str, value: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ border: none; border-bottom: 1px solid {COLOR_BORDER}; }}")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setFixedWidth(22)
        icon.setPixmap(icon_from_name(icon_name, COLOR_BLUE).pixmap(16, 16))

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

    def _panel_card_style(self) -> str:
        return f"""
        QFrame#Card {{
            background: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 16px;
        }}
        QWidget {{
            background: transparent;
        }}
        """
