import pandas as pd
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtGui import Qt


class CircleNode(QGraphicsEllipseItem):
    node_counter = 1
    RADIUS = 40

    def __init__(self, func_code="", node_id=None, scene=None, mainwindow=None):
        super().__init__(-self.RADIUS, -self.RADIUS,
                         self.RADIUS*2, self.RADIUS*2)
        self.setBrush(Qt.yellow)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.func_code = func_code
        self.cached_result = None
        self.node_id = node_id or id(self)
        self.inputs = []
        self.outputs = []
        self.scene_ref = scene
        self.mainwindow = mainwindow
        self.connections = []

        self.name = f"Node{CircleNode.node_counter}"
        CircleNode.node_counter += 1
        self.label = QGraphicsTextItem(self.name, self)
        self.update_label_position()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for conn in self.connections:
                conn.update_position()
            self.update_label_position()
        return super().itemChange(change, value)

    def update_label_position(self):
        rect = self.rect()
        self.label.setPos(-self.label.boundingRect().width()/2,
                          rect.bottom() + 5)

    def execute(self, clean=False):
        if not clean and self.cached_result is not None:
            return self.cached_result

        input_data = [parent.execute(clean=clean) for parent in self.inputs]

        local_env = {"pd": pd, "input_data": input_data}
        try:
            exec(self.func_code, {}, local_env)
            if "main" in local_env:
                self.cached_result = local_env["main"](*input_data)
        except Exception as e:
            print(f"Error in node {self.node_id}: {e}")
            self.cached_result = None
        return self.cached_result

    def to_json(self):
        return {
            "node_id": self.node_id,
            "name": self.name,
            "func_code": self.func_code,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "inputs": [node.node_id for node in self.inputs],
            "outputs": [node.node_id for node in self.outputs]
        }

    @classmethod
    def from_json(cls, data, scene, mainwindow):
        node = cls(func_code=data["func_code"],
                   node_id=data["node_id"],
                   scene=scene,
                   mainwindow=mainwindow)
        node.name = data["name"]
        node.setPos(data["position"]["x"], data["position"]["y"])
        return node
