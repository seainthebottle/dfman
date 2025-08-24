from PySide6.QtWidgets import QGraphicsView, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QAction, QShortcut
from .node import CircleNode


class GraphicsView(QGraphicsView):
    def __init__(self, scene, mainwindow):
        super().__init__(scene)
        self.mainwindow = mainwindow
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._dragging = False
        self._last_mouse_pos = None

        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._dragging = True
            self._last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_mouse_pos:
            delta = event.position().toPoint() - self._last_mouse_pos
            self._last_mouse_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif event.modifiers() & Qt.ShiftModifier:
            delta_x = event.angleDelta().y() / 4
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
            delta_y = event.angleDelta().x() / 4
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        if self.scale_factor < self.max_scale:
            self.scale(1.25, 1.25)
            self.scale_factor *= 1.25

    def zoom_out(self):
        if self.scale_factor > self.min_scale:
            self.scale(0.8, 0.8)
            self.scale_factor *= 0.8

    def contextMenuEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())
        if isinstance(item, CircleNode):
            menu = QMenu(self)
            action_connect = QAction("Start Connection", menu)
            action_connect.triggered.connect(lambda: self.mainwindow.start_connection(item))
            menu.addAction(action_connect)
            menu.exec(event.globalPos())
        else:
            menu = QMenu(self)
            action_add = QAction("Add Circle", menu)
            action_add.triggered.connect(lambda: self.mainwindow.add_circle_at(scene_pos))
            menu.addAction(action_add)
            menu.exec(event.globalPos())
