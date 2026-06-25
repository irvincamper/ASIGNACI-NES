from __future__ import annotations

from PySide6.QtCore import QDate, QSize, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.styles import apply_shadow
from app.theme import COLOR_BG, COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.asignaciones_service import AsignacionesService
from services.empleados_service import EmpleadosService
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.search_bar import SearchBar


EMPLOYEE_HEADER_H = 58
EMPLOYEE_ROW_H = 72
ASSIGNMENT_HEADER_H = 58
ASSIGNMENT_ROW_H = 68


class EmpleadosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = EmpleadosService()
        self.asignaciones_service = AsignacionesService()
        self.empleados: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        title_block = QVBoxLayout()
        title_block.setSpacing(8)
        app_title = QLabel("Sistema de Asignaciones")
        app_title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 38px; font-weight: 900;")
        module_title = QLabel("Empleados")
        module_title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 27px; font-weight: 900;")
        subtitle = QLabel("Consulta del personal y objetos asignados")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px;")
        title_block.addWidget(app_title)
        title_block.addSpacing(6)
        title_block.addWidget(module_title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.search = SearchBar("Buscar por matricula o nombre...")
        self.search.setMinimumWidth(210)
        self.search.setMaximumWidth(280)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.textChanged.connect(lambda _text: self.refresh_data())
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Estado: Todos", "Activo", "Inactivo", "Baja"])
        self.status_filter.setFixedWidth(150)
        self.status_filter.currentTextChanged.connect(lambda _text: self.refresh_data())

        btn_new = AppButton("Nuevo empleado", "fa5s.user-plus", "primary")
        btn_edit = AppButton("Editar", "fa5s.edit", "outline")
        btn_down = AppButton("Dar de baja", "fa5s.user-times", "danger")
        btn_assignments = AppButton("Ver asignaciones", "fa5s.list", "outline")
        self._compact_action_button(btn_new, 138)
        self._compact_action_button(btn_edit, 88)
        self._compact_action_button(btn_down, 118)
        self._compact_action_button(btn_assignments, 142)
        btn_new.clicked.connect(self._show_new_employee_dialog)
        btn_edit.clicked.connect(self._show_edit_employee_dialog)
        btn_down.clicked.connect(self._show_down_employee_dialog)
        btn_assignments.clicked.connect(self._show_selected_assignments)

        controls.addWidget(self.search, 1)
        controls.addWidget(self.status_filter)
        controls.addWidget(btn_new)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_down)
        controls.addWidget(btn_assignments)
        layout.addLayout(controls)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setStyleSheet(self._card_style())
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(8, 10, 8, 10)

        self.columns = [
            ("matricula", "Matricula"),
            ("nombre", "Nombre"),
            ("puesto", "Puesto"),
            ("estado", "Estado"),
            ("objetos", "Objetos\nasignados"),
            ("locker", "Locker"),
        ]
        self.table = QTableWidget()
        self._configure_table(self.table, EMPLOYEE_HEADER_H, EMPLOYEE_ROW_H)
        self.table.setColumnCount(len(self.columns))
        self._set_centered_headers(self.table, [label for _, label in self.columns])
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        self.refresh_data()

    def refresh_data(self) -> None:
        self.empleados = self.service.list_empleados(self.search.text(), self.status_filter.currentText())
        self.table.setRowCount(len(self.empleados))
        for row_index, empleado in enumerate(self.empleados):
            values = [
                str(empleado.get("matricula", "")),
                str(empleado.get("nombre", "")),
                str(empleado.get("puesto", "")),
                str(empleado.get("estado", "")),
                str(empleado.get("total_asignaciones", empleado.get("objetos", 0))),
                str(empleado.get("locker", "-") or "-"),
            ]
            for column_index, value in enumerate(values):
                self._set_item(self.table, row_index, column_index, value, Qt.AlignCenter)
            self.table.setRowHeight(row_index, EMPLOYEE_ROW_H)
        if self.empleados:
            self.table.selectRow(0)
        self._apply_employee_column_widths()

    def _compact_action_button(self, button: AppButton, width: int) -> None:
        button.setFixedWidth(width)
        button.setIconSize(QSize(15, 15))
        button.setStyleSheet(
            button.styleSheet()
            + """
            QPushButton {
                padding-left: 6px;
                padding-right: 6px;
                font-size: 12px;
            }
            """
        )

    def _show_selected_assignments(self) -> None:
        empleado = self._selected_employee()
        if not empleado:
            return

        asignaciones = self.asignaciones_service.listar_asignaciones_por_empleado(int(empleado["id_empleado"]))
        total_objetos = self.asignaciones_service.contar_objetos_por_empleado(int(empleado["id_empleado"]))

        dialog = QDialog(self)
        dialog.setWindowTitle("Objetos asignados al empleado")
        dialog.setModal(True)
        self._enable_dialog_minimize(dialog)
        screen = QApplication.screenAt(self.window().geometry().center()) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        dialog_width = min(1660, int(available.width() * 0.88)) if available else 1500
        dialog_height = min(860, int(available.height() * 0.82)) if available else 800
        dialog.resize(max(dialog_width, 1240), max(dialog_height, 720))
        dialog.setStyleSheet(
            """
            QDialog {
                background: #F6F8FC;
            }
            """
        )
        self._center_dialog(dialog)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(48, 28, 48, 18)
        layout.setSpacing(16)

        title = QLabel("Objetos asignados al empleado")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 30px; font-weight: 800;")
        subtitle = QLabel("Consulta de objetos asignados, locker y datos del empleado seleccionado")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        summary = QFrame()
        summary.setObjectName("Card")
        summary.setStyleSheet(self._card_style())
        apply_shadow(summary, blur=16, y_offset=3, alpha=18)
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(24, 14, 24, 14)
        summary_layout.setSpacing(0)
        summary_items = [
            ("Matrícula", str(empleado.get("matricula", "")), 1),
            ("Empleado", str(empleado.get("nombre", "")), 3),
            ("Puesto", str(empleado.get("puesto", "")), 3),
            ("Total de objetos", str(total_objetos), 1),
            ("Locker", str(empleado.get("locker", "-") or "-"), 1),
        ]
        for index, (label, value, stretch) in enumerate(summary_items):
            summary_layout.addWidget(self._summary_value(label, value), stretch)
            if index < len(summary_items) - 1:
                summary_layout.addWidget(self._vertical_separator())
        layout.addWidget(summary)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setStyleSheet(self._card_style())
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 12, 10, 12)

        table = QTableWidget()
        assignment_columns = ["No.", "Objeto", "Categoría", "Cantidad", "Requiere devolución", "Observaciones"]
        table.setColumnCount(len(assignment_columns))
        self._set_centered_headers(table, assignment_columns)
        table.setRowCount(len(asignaciones))
        self._configure_table(table, ASSIGNMENT_HEADER_H, ASSIGNMENT_ROW_H)
        table.setWordWrap(True)
        if not asignaciones:
            table.setRowCount(1)
            empty = QTableWidgetItem("Este empleado no tiene objetos asignados.")
            empty.setForeground(QColor(COLOR_TEXT_MUTED))
            empty.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, empty)
            table.setSpan(0, 0, 1, len(assignment_columns))
            table.setRowHeight(0, ASSIGNMENT_ROW_H)
        else:
            for row_index, item in enumerate(asignaciones):
                values = [
                    str(row_index + 1),
                    str(item.get("objeto", "")),
                    str(item.get("categoria", "")),
                    str(item.get("cantidad", "")),
                    str(item.get("requiere_devolucion", "No")),
                    str(item.get("observaciones", "") or "Asignación pendiente generada automáticamente por reglas puesto-objeto."),
                ]
                for column_index, value in enumerate(values):
                    align = Qt.AlignVCenter | (Qt.AlignCenter if column_index in {0, 3, 4} else Qt.AlignLeft)
                    self._set_item(table, row_index, column_index, value, align)
                table.setRowHeight(row_index, ASSIGNMENT_ROW_H)
            table.selectRow(0)
        table_layout.addWidget(table)
        layout.addWidget(table_card, 1)
        QTimer.singleShot(0, lambda: self._apply_assignment_column_widths(table))

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close = AppButton("Cerrar", "fa5s.times", "outline")
        close.clicked.connect(dialog.accept)
        close.setFixedWidth(138)
        close_row.addWidget(close)
        layout.addLayout(close_row)
        dialog.exec()

    def _show_new_employee_dialog(self) -> None:
        dialog, fields = self._employee_form("Nuevo empleado")
        fields["estado"].setCurrentText("Activo")
        if dialog.exec() != QDialog.Accepted:
            return
        result = self.service.crear_empleado(self._employee_form_data(fields, include_matricula=True))
        ConfirmDialog.show_message(self, "Nuevo empleado", result.get("mensaje", "Operacion completada."))
        if result.get("ok"):
            self.refresh_data()

    def _show_edit_employee_dialog(self) -> None:
        empleado = self._selected_employee()
        if not empleado:
            return
        dialog, fields = self._employee_form("Editar empleado", empleado)
        fields["matricula"].setReadOnly(True)
        fields["fecha_ingreso"].setEnabled(False)
        if dialog.exec() != QDialog.Accepted:
            return
        data = self._employee_form_data(fields, include_matricula=False)
        nuevo_puesto = int(data["id_puesto"])
        if nuevo_puesto != int(empleado["id_puesto"]):
            preview = self.service.previsualizar_cambio_puesto(int(empleado["id_empleado"]), nuevo_puesto)
            if preview.get("ok"):
                message = (
                    "Se detecto un cambio de puesto.\n\n"
                    f"Puesto anterior: {preview.get('puesto_anterior', '')}\n"
                    f"Puesto nuevo: {preview.get('puesto_nuevo', '')}\n\n"
                    f"Objetos que conserva: {len(preview.get('conserva', []))}\n"
                    f"Objetos nuevos: {len(preview.get('nuevos', []))}\n"
                    f"Objetos que ya no corresponden: {len(preview.get('salen', []))}\n\n"
                    "El sistema actualizara los objetos asignados segun el nuevo puesto y conservara el historial del movimiento.\n\n"
                    "Deseas continuar?"
                )
                if not ConfirmDialog.ask(self, "Cambio de puesto", message):
                    return
        result = self.service.editar_empleado(int(empleado["id_empleado"]), data)
        ConfirmDialog.show_message(self, "Editar empleado", result.get("mensaje", "Operacion completada."))
        if result.get("ok"):
            self.refresh_data()

    def _show_down_employee_dialog(self) -> None:
        empleado = self._selected_employee()
        if not empleado:
            return
        if empleado.get("estado") != "Activo":
            ConfirmDialog.show_message(self, "Dar de baja", "El empleado seleccionado ya se encuentra dado de baja.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Dar de baja")
        dialog.setModal(True)
        self._enable_dialog_minimize(dialog)
        dialog.setFixedSize(640, 500)
        dialog.setStyleSheet(self._dialog_style())
        self._center_dialog(dialog)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)
        title = QLabel("Dar de baja empleado")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 28px; font-weight: 900;")
        detail = QLabel(
            f"{empleado.get('matricula', '')} - {empleado.get('nombre', '')}\n"
            f"Puesto: {empleado.get('puesto', '')} | Turno: {empleado.get('turno', '')}\n"
            f"Estacionamiento: {empleado.get('estacionamiento', '-')} | Locker: {empleado.get('locker', '-')}"
        )
        detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setStyleSheet(self._card_style())
        apply_shadow(form_card, blur=18, y_offset=4, alpha=20)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(10)
        fecha = QDateEdit()
        fecha.setCalendarPopup(True)
        fecha.setDate(QDate.currentDate())
        observaciones = QTextEdit()
        observaciones.setFixedHeight(116)
        observaciones.setPlaceholderText("Motivo / observaciones de baja")
        layout.addWidget(title)
        layout.addWidget(detail)
        self._add_labeled(form_layout, "Fecha de baja", fecha)
        self._add_labeled(form_layout, "Motivo / observaciones", observaciones)
        layout.addWidget(form_card, 1)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = AppButton("Cancelar", "fa5s.times", "outline")
        save = AppButton("Confirmar baja", "fa5s.user-times", "danger")
        cancel.setFixedWidth(126)
        save.setFixedWidth(160)
        cancel.clicked.connect(dialog.reject)
        save.clicked.connect(dialog.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        if dialog.exec() != QDialog.Accepted:
            return
        result = self.service.dar_de_baja(
            int(empleado["id_empleado"]),
            fecha.date().toString("yyyy-MM-dd"),
            observaciones.toPlainText().strip(),
        )
        ConfirmDialog.show_message(self, "Dar de baja", result.get("mensaje", "Operacion completada."))
        if result.get("ok"):
            self.refresh_data()

    def _selected_employee(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.empleados):
            ConfirmDialog.show_message(self, "Sin seleccion", "Selecciona un empleado.")
            return None
        empleado = self.service.buscar_por_matricula(self.empleados[row]["matricula"])
        if not empleado:
            ConfirmDialog.show_message(self, "Empleado no encontrado", "No se encontro un empleado con esa matricula.")
            return None
        return empleado

    def _employee_form(self, title_text: str, empleado: dict | None = None) -> tuple[QDialog, dict]:
        empleado = empleado or {}
        dialog = QDialog(self)
        dialog.setWindowTitle(title_text)
        dialog.setModal(True)
        self._enable_dialog_minimize(dialog)
        dialog.setFixedSize(840, 680)
        dialog.setStyleSheet(self._dialog_style())
        self._center_dialog(dialog)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 28px; font-weight: 900;")
        subtitle_text = (
            "Registra los datos principales del trabajador y su asignación inicial."
            if not empleado
            else "Actualiza los datos principales del trabajador seleccionado."
        )
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        fields: dict[str, object] = {}
        errors: dict[str, QLabel] = {}
        fields["matricula"] = QLineEdit(str(empleado.get("matricula", "")))
        fields["matricula"].setPlaceholderText("Ej. 1173")
        fields["nombre"] = QLineEdit(str(empleado.get("nombre", "")))
        fields["nombre"].setPlaceholderText("Nombre completo")
        fields["puesto"] = QComboBox()
        for puesto in self.service.list_puestos():
            fields["puesto"].addItem(puesto["nombre"], puesto["id"])
        if empleado.get("id_puesto"):
            index = fields["puesto"].findData(int(empleado["id_puesto"]))
            fields["puesto"].setCurrentIndex(max(index, 0))
        fields["turno"] = QLineEdit(str(empleado.get("turno", "")))
        fields["turno"].setPlaceholderText("Turno")
        fields["fecha_ingreso"] = QDateEdit()
        fields["fecha_ingreso"].setCalendarPopup(True)
        if empleado.get("fecha_ingreso"):
            fields["fecha_ingreso"].setDate(QDate.fromString(str(empleado["fecha_ingreso"]), "yyyy-MM-dd"))
        else:
            fields["fecha_ingreso"].setDate(QDate.currentDate())
        fields["estado"] = QComboBox()
        fields["estado"].addItems(["Activo", "Inactivo"])
        fields["estado"].setCurrentText(str(empleado.get("estado", "Activo")))
        fields["estacionamiento"] = QComboBox()
        fields["estacionamiento"].addItem("-")
        fields["estacionamiento"].addItems(self.service.list_estacionamientos())
        fields["estacionamiento"].setCurrentText(str(empleado.get("estacionamiento", "-") or "-"))
        fields["locker"] = QComboBox()
        fields["locker"].addItem("-")
        fields["locker"].addItems(self.service.list_lockers())
        fields["locker"].setCurrentText(str(empleado.get("locker", "-") or "-"))
        fields["observaciones"] = QTextEdit(str(empleado.get("observaciones", "")))
        fields["observaciones"].setPlaceholderText("Notas internas u observaciones")
        fields["observaciones"].setFixedHeight(104)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(self._card_style())
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        form_body = QWidget()
        form_body.setStyleSheet("background: transparent;")
        grid = QGridLayout(form_body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)

        self._add_form_field(grid, errors, 0, 0, "Matrícula", "matricula", fields["matricula"])
        self._add_form_field(grid, errors, 0, 1, "Estado", "estado", fields["estado"])
        self._add_form_field(grid, errors, 1, 0, "Nombre completo", "nombre", fields["nombre"])
        self._add_form_field(grid, errors, 1, 1, "Turno", "turno", fields["turno"])
        self._add_form_field(grid, errors, 2, 0, "Puesto", "puesto", fields["puesto"])
        self._add_form_field(grid, errors, 2, 1, "Fecha de ingreso", "fecha_ingreso", fields["fecha_ingreso"])
        self._add_form_field(grid, errors, 3, 0, "Estacionamiento", "estacionamiento", fields["estacionamiento"])
        self._add_form_field(grid, errors, 3, 1, "Locker", "locker", fields["locker"])
        self._add_form_field(grid, errors, 4, 0, "Observaciones", "observaciones", fields["observaciones"], column_span=2)
        scroll.setWidget(form_body)
        card_layout.addWidget(scroll)
        layout.addWidget(card, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = AppButton("Cancelar", "fa5s.times", "outline")
        save_text = "Crear empleado" if not empleado else "Guardar"
        save = AppButton(save_text, "fa5s.save", "primary")
        cancel.setFixedWidth(126)
        save.setFixedWidth(166 if not empleado else 126)
        cancel.clicked.connect(dialog.reject)

        def submit_form() -> None:
            if self._validate_employee_form(fields, errors, include_matricula=not bool(empleado)):
                dialog.accept()

        save.clicked.connect(submit_form)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        fields["_errors"] = errors
        return dialog, fields

    def _employee_form_data(self, fields: dict, *, include_matricula: bool) -> dict:
        data = {
            "nombre": fields["nombre"].text(),
            "id_puesto": fields["puesto"].currentData(),
            "turno": fields["turno"].text(),
            "fecha_ingreso": fields["fecha_ingreso"].date().toString("yyyy-MM-dd"),
            "estado": fields["estado"].currentText(),
            "estacionamiento": fields["estacionamiento"].currentText(),
            "locker": fields["locker"].currentText(),
            "observaciones": fields["observaciones"].toPlainText(),
        }
        if include_matricula:
            data["matricula"] = fields["matricula"].text()
        return data

    def _add_labeled(self, layout: QVBoxLayout, label_text: str, widget: QWidget) -> None:
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 800;")
        layout.addWidget(label)
        layout.addWidget(widget)

    def _add_form_field(
        self,
        grid: QGridLayout,
        errors: dict[str, QLabel],
        row: int,
        column: int,
        label_text: str,
        key: str,
        widget: QWidget,
        *,
        column_span: int = 1,
    ) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 800;")
        error = QLabel("")
        error.setVisible(False)
        error.setStyleSheet("color: #E11D48; font-size: 11px; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(widget)
        layout.addWidget(error)
        errors[key] = error
        grid.addWidget(container, row, column, 1, column_span)

    def _validate_employee_form(self, fields: dict, errors: dict[str, QLabel], *, include_matricula: bool) -> bool:
        labels = {
            "matricula": "La matrícula es obligatoria.",
            "nombre": "El nombre completo es obligatorio.",
            "puesto": "Selecciona un puesto.",
            "turno": "El turno es obligatorio.",
            "fecha_ingreso": "La fecha de ingreso es obligatoria.",
            "estado": "Selecciona un estado.",
        }
        required = ["nombre", "puesto", "turno", "fecha_ingreso", "estado"]
        if include_matricula:
            required.insert(0, "matricula")

        ok = True
        for key, error in errors.items():
            error.setText("")
            error.setVisible(False)
            widget = fields.get(key)
            if isinstance(widget, (QLineEdit, QComboBox, QDateEdit, QTextEdit)):
                widget.setProperty("invalid", False)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

        for key in required:
            widget = fields[key]
            value = ""
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QComboBox):
                value = str(widget.currentText()).strip()
                if key == "puesto" and widget.currentData() is None:
                    value = ""
            elif isinstance(widget, QDateEdit):
                value = widget.date().toString("yyyy-MM-dd")
            if not value:
                ok = False
                errors[key].setText(labels[key])
                errors[key].setVisible(True)
                widget.setProperty("invalid", True)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        if ok and include_matricula and self.service.buscar_por_matricula(fields["matricula"].text()):
            ok = False
            errors["matricula"].setText("Ya existe un empleado con esta matrícula.")
            errors["matricula"].setVisible(True)
            fields["matricula"].setProperty("invalid", True)
            fields["matricula"].style().unpolish(fields["matricula"])
            fields["matricula"].style().polish(fields["matricula"])
        return ok

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_employee_column_widths()

    def _configure_table(self, table: QTableWidget, header_height: int, row_height: int) -> None:
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.horizontalHeader().setFixedHeight(header_height)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        table.setStyleSheet(self._table_style())

    def _apply_employee_column_widths(self) -> None:
        if not hasattr(self, "table"):
            return
        width = max(self.table.viewport().width(), 1000)
        for index, ratio in enumerate((0.10, 0.24, 0.30, 0.10, 0.16, 0.10)):
            self.table.setColumnWidth(index, int(width * ratio))

    def _set_centered_headers(self, table: QTableWidget, labels: list[str]) -> None:
        for column, label in enumerate(labels):
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignCenter)
            table.setHorizontalHeaderItem(column, item)

    def _apply_assignment_column_widths(self, table: QTableWidget) -> None:
        scrollbar_width = table.verticalScrollBar().sizeHint().width() if table.verticalScrollBar() else 0
        width = max(table.viewport().width() - scrollbar_width - 8, 1000)
        ratios = (0.06, 0.22, 0.23, 0.09, 0.15, 0.25)
        assigned = 0
        for index, ratio in enumerate(ratios[:-1]):
            column_width = int(width * ratio)
            table.setColumnWidth(index, column_width)
            assigned += column_width
        table.setColumnWidth(len(ratios) - 1, max(width - assigned, 220))

    def _set_item(self, table: QTableWidget, row: int, column: int, value: str, alignment: Qt.AlignmentFlag) -> None:
        item = QTableWidgetItem(value)
        item.setToolTip(value)
        item.setForeground(QColor(COLOR_TEXT))
        item.setTextAlignment(alignment)
        table.setItem(row, column, item)

    def _summary_value(self, label: str, value: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; font-weight: 700;")
        value_widget = QLabel(value)
        value_widget.setToolTip(value)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 16px; font-weight: 700;")
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        return container

    def _vertical_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFixedWidth(1)
        line.setStyleSheet("color: #E3E9F3; background: #E3E9F3; margin-left: 18px; margin-right: 18px;")
        return line

    def _enable_dialog_minimize(self, dialog: QDialog) -> None:
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

    def _center_dialog(self, dialog: QDialog) -> None:
        parent_window = self.window()
        if not parent_window:
            return
        parent_geo = parent_window.frameGeometry()
        dialog_geo = dialog.frameGeometry()
        dialog_geo.moveCenter(parent_geo.center())
        dialog.move(dialog_geo.topLeft())

    def _card_style(self) -> str:
        return f"""
        QFrame#Card {{
            background: {COLOR_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 14px;
        }}
        QWidget {{
            background: transparent;
        }}
        """

    def _dialog_style(self) -> str:
        return f"""
        QDialog {{
            background: {COLOR_BG};
        }}
        QLineEdit[invalid="true"],
        QComboBox[invalid="true"],
        QDateEdit[invalid="true"],
        QTextEdit[invalid="true"] {{
            border: 1px solid #E11D48;
            background: #FFF7F8;
        }}
        """

    def _table_style(self) -> str:
        return f"""
        QTableWidget {{
            background: #FFFFFF;
            border: none;
            gridline-color: transparent;
            selection-background-color: #EAF2FF;
            selection-color: {COLOR_TEXT};
            outline: none;
            font-size: 13px;
        }}
        QHeaderView::section {{
            background: #FFFFFF;
            color: #061B4F;
            border: none;
            border-bottom: 1px solid #DCE5F2;
            padding-left: 16px;
            padding-right: 16px;
            font-size: 13px;
            font-weight: 800;
        }}
        QTableWidget::item {{
            border-bottom: 1px solid #E8EEF6;
            padding-left: 16px;
            padding-right: 16px;
            background: #FFFFFF;
        }}
        QTableWidget::item:hover {{
            background: #F7FAFF;
        }}
        QTableWidget::item:selected {{
            background: #EAF2FF;
            color: {COLOR_TEXT};
        }}
        QScrollBar:vertical {{
            width: 10px;
            background: #F7F9FC;
            margin: 8px 2px 8px 2px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: #9CA3AF;
            border-radius: 5px;
            min-height: 54px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #7D8794;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """
