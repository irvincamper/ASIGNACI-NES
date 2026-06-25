from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.styles import apply_shadow, rgba
from app.theme import COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_WARNING, CONTENT_PADDING_X, CONTENT_PADDING_Y
from services.relaciones_service import RelacionesService
from utils.formatters import icon_from_name
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable


class RelacionesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = RelacionesService()
        self.puestos: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        module_title = QLabel("Relación Puesto-Objetos")
        module_title.setObjectName("ModuleTitle")
        module_title.setStyleSheet(self._module_title_style())
        subtitle = QLabel("Asignaciones definidas por puesto")
        subtitle.setObjectName("Subtitle")
        subtitle.setStyleSheet(self._subtitle_style())
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
        add.setFixedWidth(168)
        save.setFixedWidth(168)
        add.clicked.connect(self._show_relation_form)
        save.clicked.connect(self._confirm_save_changes)

        controls.addLayout(left)
        controls.addStretch(1)
        controls.addWidget(add, 0, Qt.AlignBottom)
        controls.addWidget(save, 0, Qt.AlignBottom)
        layout.addLayout(controls)

        warning = QFrame()
        warning.setStyleSheet(
            f"""
            QFrame {{
                background: {rgba(COLOR_WARNING, 0.07)};
                border: 1px solid {rgba(COLOR_WARNING, 0.22)};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )
        warning_layout = QHBoxLayout(warning)
        warning_layout.setContentsMargins(16, 10, 16, 10)
        warning_layout.setSpacing(10)
        icon = QLabel()
        icon.setFixedSize(28, 28)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name("fa5s.exclamation-triangle", COLOR_WARNING).pixmap(18, 18))
        text = QLabel("Los cambios realizados en esta configuración afectarán únicamente a las asignaciones futuras.")
        text.setStyleSheet("color: #B7791F; font-size: 14px; font-weight: 700; border: none;")
        warning_layout.addWidget(icon)
        warning_layout.addWidget(text)
        warning_layout.addStretch(1)
        layout.addWidget(warning)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(420)
        table_card.setStyleSheet(
            f"""
            QFrame#Card {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 16px;
            }}
            """
        )
        apply_shadow(table_card, blur=18, y_offset=4, alpha=22)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.columns = [
            ("puesto", "Puesto"),
            ("objeto", "Objeto"),
            ("cantidad", "Cantidad"),
            ("obligatorio", "Obligatorio"),
            ("devolucion", "Requiere devolución"),
            ("estado", "Estado"),
            ("acciones", "Acciones"),
        ]
        self.table = DataTable()
        self._configure_table()
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)
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
            [{**row, "acciones": ""} for row in rows],
            action_columns={"acciones"},
            center_columns={"puesto", "objeto", "cantidad", "obligatorio", "devolucion", "estado"},
            action_callback=self._show_relation_actions,
        )
        self._polish_table_cells()
        self._apply_column_widths()

    def _confirm_save_changes(self) -> None:
        if not ConfirmDialog.ask(
            self,
            "Guardar cambios",
            "¿Deseas guardar los cambios de relación puesto-objetos?",
            "Guardar",
        ):
            return
        self.refresh_relaciones()
        ConfirmDialog.show_message(self, "Guardar cambios", "Operación completada correctamente.")

    def _show_relation_actions(self, row: dict) -> None:
        menu = QMenu(self)
        edit = menu.addAction("Editar relación")
        deactivate = menu.addAction("Desactivar relación")
        edit.triggered.connect(lambda _checked=False, current=row: self._show_relation_form(current))
        deactivate.triggered.connect(lambda _checked=False, current=row: self._deactivate_relation(current))
        menu.exec(QCursor.pos())

    def _show_relation_form(self, row: dict | None = None) -> None:
        row = row or {}
        puesto_id = self.puesto_combo.currentData()
        if not puesto_id:
            ConfirmDialog.show_message(self, "Relación puesto-objetos", "Selecciona un puesto.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar relación" if row else "Agregar relación")
        dialog.setModal(True)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        dialog.setFixedSize(720, 430)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Editar relación" if row else "Agregar relación")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 24px; font-weight: 900;")
        subtitle = QLabel("Define qué objeto corresponde al puesto seleccionado.")
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(f"QFrame#Card {{ background: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 14px; }}")
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 16, 18, 16)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        puesto = QLabel(self.puesto_combo.currentText())
        puesto.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 800;")
        objeto = QComboBox()
        for item in self.service.list_objetos():
            objeto.addItem(item["nombre"], item["id"])
        if row.get("id_objeto"):
            index = objeto.findData(int(row["id_objeto"]))
            objeto.setCurrentIndex(max(index, 0))
        cantidad = QSpinBox()
        cantidad.setMinimum(1)
        cantidad.setMaximum(999)
        cantidad.setValue(int(row.get("cantidad") or 1))
        obligatorio = QComboBox()
        obligatorio.addItems(["Sí", "No"])
        obligatorio.setCurrentText("Sí" if row.get("obligatorio", "Sí") in {"Sí", "Si"} else "No")
        devolucion = QComboBox()
        devolucion.addItems(["Sí", "No"])
        devolucion.setCurrentText("Sí" if row.get("devolucion", "Sí") in {"Sí", "Si"} else "No")
        estado = QComboBox()
        estado.addItems(["Activo", "Inactivo"])
        estado.setCurrentText(str(row.get("estado", "Activo")))

        fields = [
            ("Puesto", puesto),
            ("Objeto", objeto),
            ("Cantidad", cantidad),
            ("Obligatorio", obligatorio),
            ("Requiere devolución", devolucion),
            ("Estado", estado),
        ]
        for index, (label_text, widget) in enumerate(fields):
            container = QWidget()
            block = QVBoxLayout(container)
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(6)
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 800;")
            block.addWidget(label)
            block.addWidget(widget)
            grid.addWidget(container, index // 2, index % 2)
        layout.addWidget(card, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = AppButton("Cancelar", "fa5s.times", "outline")
        save = AppButton("Guardar", "fa5s.save", "primary")
        cancel.clicked.connect(dialog.reject)

        def submit() -> None:
            result = self.service.guardar_relacion(
                {
                    "id_puesto": puesto_id,
                    "id_objeto": objeto.currentData(),
                    "cantidad": cantidad.value(),
                    "obligatorio": obligatorio.currentText(),
                    "requiere_devolucion": devolucion.currentText(),
                    "estado": estado.currentText(),
                },
                int(row["id"]) if row.get("id") else None,
            )
            ConfirmDialog.show_message(dialog, "Relación puesto-objetos", result.get("mensaje", "Operación completada correctamente."))
            if result.get("ok"):
                dialog.accept()
                self.refresh_relaciones()

        save.clicked.connect(submit)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        dialog.exec()

    def _deactivate_relation(self, row: dict) -> None:
        if str(row.get("estado", "")) == "Inactivo":
            ConfirmDialog.show_message(self, "Relación inactiva", "Esta relación ya se encuentra inactiva.")
            return
        if not ConfirmDialog.ask(self, "Desactivar relación", "¿Deseas desactivar esta relación?", "Desactivar"):
            return
        result = self.service.desactivar_relacion(int(row["id"]))
        ConfirmDialog.show_message(self, "Desactivar relación", result.get("mensaje", "Operación completada correctamente."))
        self.refresh_relaciones()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_column_widths()

    def _module_title_style(self) -> str:
        return f"color: {COLOR_TEXT}; font-size: 42px; font-weight: 900;"

    def _subtitle_style(self) -> str:
        return f"color: {COLOR_TEXT_MUTED}; font-size: 18px;"

    def _configure_table(self) -> None:
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(64)
        self.table.horizontalHeader().setFixedHeight(58)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {COLOR_CARD};
                border: none;
                gridline-color: transparent;
                selection-background-color: #EAF2FF;
                selection-color: {COLOR_TEXT};
                outline: none;
                font-size: 14px;
                color: {COLOR_TEXT};
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #E8EEF6;
                padding-left: 10px;
                padding-right: 10px;
                color: {COLOR_TEXT};
            }}
            QTableWidget::item:hover {{
                background: #F7FAFF;
            }}
            QTableWidget::item:selected {{
                background: #EAF2FF;
                color: {COLOR_TEXT};
            }}
            QHeaderView::section {{
                background: {COLOR_CARD};
                color: {COLOR_TEXT};
                border: none;
                border-bottom: 1px solid {COLOR_BORDER};
                padding-left: 8px;
                padding-right: 8px;
                font-size: 14px;
                font-weight: 800;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: #B9C4D6;
                border-radius: 5px;
                min-height: 36px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

    def _polish_table_cells(self) -> None:
        for column, (_, label) in enumerate(self.columns):
            header = QTableWidgetItem(label)
            header.setTextAlignment(Qt.AlignCenter)
            self.table.setHorizontalHeaderItem(column, header)

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 64)
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if not item:
                    continue
                item.setForeground(QColor(COLOR_TEXT))
                item.setTextAlignment(Qt.AlignCenter)

    def _apply_column_widths(self) -> None:
        if not hasattr(self, "table") or self.table.columnCount() == 0:
            return
        scrollbar_width = self.table.verticalScrollBar().sizeHint().width() if self.table.verticalScrollBar() else 0
        width = max(self.table.viewport().width() - scrollbar_width - 8, 900)
        ratios = (0.22, 0.22, 0.10, 0.12, 0.16, 0.10, 0.08)
        assigned = 0
        for index, ratio in enumerate(ratios[:-1]):
            column_width = int(width * ratio)
            self.table.setColumnWidth(index, column_width)
            assigned += column_width
        self.table.setColumnWidth(len(ratios) - 1, max(width - assigned, 72))
