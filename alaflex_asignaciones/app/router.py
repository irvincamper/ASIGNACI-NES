from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStackedWidget

from views.dashboard_view import DashboardView
from views.empleados_view import EmpleadosView
from views.estacionamientos_view import EstacionamientosView
from views.objetos_view import ObjetosView
from views.pdf_preview_view import PdfPreviewView
from views.relaciones_view import RelacionesView


class Router(QObject):
    view_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.stack = QStackedWidget()
        self.views = {
            "dashboard": DashboardView(),
            "empleados": EmpleadosView(),
            "objetos": ObjetosView(),
            "relaciones": RelacionesView(),
            "estacionamientos": EstacionamientosView(),
            "pdf": PdfPreviewView(),
        }

        for view in self.views.values():
            self.stack.addWidget(view)

    def navigate(self, module_key: str) -> None:
        view = self.views.get(module_key)
        if view is None:
            return
        self.stack.setCurrentWidget(view)
        self.view_changed.emit(module_key)
