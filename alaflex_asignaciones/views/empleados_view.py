from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.styles import apply_shadow, table_card_height
from app.theme import COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED, CONTENT_PADDING_X, CONTENT_PADDING_Y
from utils.mock_data import EMPLEADOS
from widgets.app_button import AppButton
from widgets.confirm_dialog import ConfirmDialog
from widgets.data_table import DataTable
from widgets.search_bar import SearchBar
from widgets.status_badge import StatusBadge
from utils.formatters import icon_from_name


class EmpleadosView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CONTENT_PADDING_X, CONTENT_PADDING_Y, CONTENT_PADDING_X, CONTENT_PADDING_Y)
        layout.setSpacing(22)

        app_title = QLabel("Sistema de Asignaciones")
        app_title.setObjectName("AppTitle")
        module_title = QLabel("Empleados")
        module_title.setObjectName("ModuleTitle")
        subtitle = QLabel("Gestión integral del personal")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(app_title)
        layout.addWidget(module_title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(18)
        search = SearchBar("Buscar por matrícula o nombre...")
        search.setFixedWidth(320)
        status_filter = QComboBox()
        status_filter.addItems(["Estado: Todos", "Activo", "Inactivo"])
        status_filter.setFixedWidth(220)

        btn_new = AppButton("Nuevo empleado", "fa5s.user-plus", "primary")
        btn_edit = AppButton("Editar", "fa5s.edit", "outline")
        btn_down = AppButton("Dar de baja", "fa5s.user-times", "danger")
        for button in (btn_new, btn_edit, btn_down):
            button.clicked.connect(lambda _checked=False: ConfirmDialog.show_mock(self))

        controls.addWidget(search)
        controls.addWidget(status_filter)
        controls.addStretch(1)
        controls.addWidget(btn_new)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_down)
        layout.addLayout(controls)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(table_card_height(len(EMPLEADOS)))
        apply_shadow(table_card)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(4, 4, 4, 4)

        self.table = DataTable()
        self.table.set_data(
            [
                ("matricula", "Matrícula"),
                ("nombre", "Nombre"),
                ("puesto", "Puesto"),
                ("estado", "Estado"),
                ("objetos", "Objetos asignados"),
                ("estacionamiento", "Estacionamiento"),
            ],
            EMPLEADOS,
            badge_columns={"estado"},
            center_columns={"objetos", "estacionamiento"},
        )
        self.table.itemSelectionChanged.connect(self._update_summary)
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

        self.summary_card = QFrame()
        self.summary_card.setObjectName("Card")
        apply_shadow(self.summary_card)
        self.summary_layout = QHBoxLayout(self.summary_card)
        self.summary_layout.setContentsMargins(22, 20, 22, 20)
        self.summary_layout.setSpacing(18)
        layout.addWidget(self.summary_card)
        layout.addStretch(1)
        self._update_summary()

    def _update_summary(self) -> None:
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row = max(self.table.currentRow(), 0)
        empleado = EMPLEADOS[row] if EMPLEADOS else {}
        blocks = [
            ("fa5s.users", "Nombre", empleado.get("nombre", "")),
            ("fa5s.briefcase", "Puesto", empleado.get("puesto", "")),
            ("fa5s.shield-alt", "Estado", empleado.get("estado", "")),
            ("fa5s.cube", "Objetos asignados", str(empleado.get("objetos", ""))),
            ("fa5s.parking", "Estacionamiento", empleado.get("estacionamiento", "")),
            ("fa5s.clock", "Pendientes", str(empleado.get("pendientes", ""))),
        ]
        for index, block in enumerate(blocks):
            self.summary_layout.addWidget(self._summary_block(*block))
            if index < len(blocks) - 1:
                line = QFrame()
                line.setFixedWidth(1)
                line.setStyleSheet(f"background: {COLOR_BORDER};")
                self.summary_layout.addWidget(line)

    def _summary_block(self, icon_name: str, label: str, value: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon = QLabel()
        icon.setFixedSize(46, 46)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name(icon_name, "#0057E7").pixmap(22, 22))
        icon.setStyleSheet("QLabel { background: #EAF1FF; border-radius: 23px; }")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        if label == "Estado":
            value_widget = StatusBadge(value)
            value_widget.setFixedWidth(78)
        else:
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 800;")
        text_layout.addWidget(label_widget)
        text_layout.addWidget(value_widget)

        layout.addWidget(icon)
        layout.addLayout(text_layout)
        return container
