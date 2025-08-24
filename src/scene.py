from PySide6.QtWidgets import QGraphicsScene, QGraphicsTextItem
from PySide6.QtCore import Qt

from .node import CircleNode
from .connection import ConnectionLineObj


class CustomScene(QGraphicsScene):
    def __init__(self, mainwindow):
        super().__init__()
        self.mainwindow = mainwindow

    def mouseMoveEvent(self, event):
        if self.mainwindow.temp_line and self.mainwindow.connecting_node:
            start_node = self.mainwindow.connecting_node
            start_pos = start_node.sceneBoundingRect().center()
            end_pos = event.scenePos()
            self.mainwindow.temp_line.setLine(start_pos.x(), start_pos.y(),
                                              end_pos.x(), end_pos.y())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mainwindow.connecting_node:
            items = self.items(event.scenePos())
            item = None
            for it in items:
                if isinstance(it, CircleNode):
                    item = it
                    break
                if isinstance(it, QGraphicsTextItem) and isinstance(it.parentItem(), CircleNode):
                    item = it.parentItem()
                    break

            if isinstance(item, CircleNode):
                start_node = self.mainwindow.connecting_node
                end_node = item
                if start_node != end_node:
                    start_node.outputs.append(end_node)
                    end_node.inputs.append(start_node)

                    if self.mainwindow.temp_line:
                        self.removeItem(self.mainwindow.temp_line)

                    ConnectionLineObj(start_node, end_node, self)

            self.mainwindow.temp_line = None
            self.mainwindow.connecting_node = None
            return

        super().mousePressEvent(event)
