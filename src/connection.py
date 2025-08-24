from PySide6.QtGui import QPen
from PySide6.QtCore import Qt


class ConnectionLineObj:
    def __init__(self, start_node, end_node, scene):
        self.start_node = start_node
        self.end_node = end_node

        self.line_item = scene.addLine(0, 0, 0, 0, QPen(Qt.white, 2))
        self.line_item.setZValue(-1)

        self.update_position()

        start_node.connections.append(self)
        end_node.connections.append(self)

    def update_position(self):
        start_pos = self.start_node.sceneBoundingRect().center()
        end_pos = self.end_node.sceneBoundingRect().center()
        self.line_item.setLine(start_pos.x(), start_pos.y(),
                               end_pos.x(), end_pos.y())

    def to_json(self):
        return {
            "start_node_id": self.start_node.node_id,
            "end_node_id": self.end_node.node_id
        }

    @classmethod
    def from_json(cls, start_node, end_node, scene):
        return cls(start_node, end_node, scene)
