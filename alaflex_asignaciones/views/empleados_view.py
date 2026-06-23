from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import APP_TITLE_STYLE, MODULE_TITLE_STYLE, SUBTITLE_STYLE, apply_shadow, table_card_height
from app.theme import COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.asignaciones_service import AsignacionesService
from services.empleados_service import EmpleadosService
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.search_bar import SearchBar


class EmpleadosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = EmpleadosService()
        self.asignaciones_service = AsignacionesService()
        self.empleados: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        app_title.setStyleSheet(APP_TITLE_STYLE)
        module_title = QLabel("Empleados")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(MODULE_TITLE_STYLE)
        subtitle = QLabel("Gestión integral del personal")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(app_title)
        layout.addWidget(module_title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(18)
        self.search = SearchBar("Buscar por matrícula o nombre...")
        self.search.setFixedWidth(320)
        self.search.textChanged.connect(lambda _text: self.refresh_data())
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Estado: Todos", "Activo", "Inactivo"])
        self.status_filter.setFixedWidth(220)
        self.status_filter.currentTextChanged.connect(lambda _text: self.refresh_data())

        btn_new = AppButton("Nuevo empleado", "fa5s.user-plus", "primary")
        btn_edit = AppButton("Editar", "fa5s.edit", "outline")
        btn_down = AppButton("Dar de baja", "fa5s.user-times", "danger")
        btn_assignments = AppButton("Ver asignaciones", "fa5s.list", "outline")
        btn_assignments.clicked.connect(self._show_selected_assignments)
        btn_generate = AppButton("Generar pendientes", "fa5s.clipboard-list", "success")
        btn_generate.clicked.connect(self._generate_pending)
        for button in (btn_new, btn_edit, btn_down):
            button.clicked.connect(lambda _checked=False: ConfirmDialog.show_mock(self))

        controls.addWidget(self.search)
        controls.addWidget(self.status_filter)
        controls.addStretch(1)
        controls.addWidget(btn_new)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_down)
        controls.addWidget(btn_assignments)
        controls.addWidget(btn_generate)
        layout.addLayout(controls)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(8))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.columns = [
            ("matricula", "Matrícula"),
            ("nombre", "Nombre"),
            ("puesto", "Puesto"),
            ("estado", "Estado"),
            ("objetos", "Objetos asignados"),
            ("estacionamiento", "Estacionamiento"),
        ]
        self.table = DataTable()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

        layout.addStretch(1)
        self.refresh_data()

    def refresh_data(self) -> None:
        self.empleados = self.service.list_empleados(self.search.text(), self.status_filter.currentText())
        rows = []
        for empleado in self.empleados:
            rows.append(
                {
                    **empleado,
                    "objetos_tooltip": (
                        f"Asignados: {empleado.get('asignados', 0)}\n"
                        f"Pendientes: {empleado.get('pendientes', 0)}\n"
                        f"Pendientes de devolución: {empleado.get('pendientes_de_devolucion', 0)}"
                    ),
                }
            )
        self.table.set_data(
            self.columns,
            rows,
            badge_columns={"estado"},
            center_columns={"objetos", "estacionamiento"},
        )

    def _generate_pending(self) -> None:
        message = (
            "Se generarán asignaciones pendientes para los empleados activos usando las reglas puesto-objeto existentes.\n\n"
            "No se descontará stock y no se generará PDF.\n\n"
            "¿Deseas continuar?"
        )
        if not ConfirmDialog.ask(self, "Generar pendientes", message):
            return
        result = self.asignaciones_service.generar_pendientes_para_empleados_activos()
        summary = (
            "Generación completada.\n\n"
            f"Empleados procesados: {result.get('empleados_procesados', 0)}\n"
            f"Asignaciones creadas: {result.get('creadas', 0)}\n"
            f"Omitidas por duplicado: {result.get('omitidas_por_duplicado', 0)}\n"
            f"Puestos sin reglas: {result.get('puestos_sin_reglas', 0)}\n"
            f"Objetos inactivos: {result.get('objetos_inactivos', 0)}\n"
            f"Objetos sin stock: {result.get('objetos_sin_stock', 0)}\n"
            f"Errores: {len(result.get('errores', []))}\n\n"
            f"Diagnóstico generado en:\n{result.get('ruta_diagnostico', '')}"
        )
        ConfirmDialog.show_message(self, "Generación completada", summary)
        self.refresh_data()

    def _show_selected_assignments(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.empleados):
            ConfirmDialog.show_message(self, "Sin selección", "Selecciona un empleado para ver sus asignaciones.")
            return
        empleado = self.service.buscar_por_matricula(self.empleados[row]["matricula"])
        if not empleado:
            ConfirmDialog.show_message(self, "Empleado no encontrado", "No se encontró un empleado con esa matrícula.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Asignaciones del empleado")
        dialog.setModal(True)
        dialog.resize(860, 520)
        layout = QVBoxLayout(dialog)
        title = QLabel(f"{empleado['matricula']} - {empleado['nombre']}")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 18px; font-weight: 800;")
        subtitle = QLabel(f"{empleado.get('puesto', '')} | Turno: {empleado.get('turno', '-')}")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px;")
        table = DataTable()
        columns = [
            ("objeto", "Objeto"),
            ("cantidad", "Cantidad"),
            ("estado", "Estado"),
            ("fecha", "Fecha"),
            ("requiere_devolucion", "Requiere devolución"),
            ("observaciones", "Observaciones"),
        ]
        rows = [
            {
                **item,
                "fecha": item.get("fecha") or "",
                "observaciones": item.get("observaciones") or "",
            }
            for item in empleado.get("asignaciones", [])
        ]
        table.set_data(
            columns,
            rows,
            badge_columns={"estado", "requiere_devolucion"},
            center_columns={"cantidad", "fecha"},
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(table)
        dialog.exec()
