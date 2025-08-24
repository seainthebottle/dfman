import json
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPen

from .scene import CustomScene
from .graphics_view import GraphicsView
from .node import CircleNode
from .connection import ConnectionLineObj


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Flow Editor (Right-Click to Add)")

        self.scene = CustomScene(self)
        self.scene.setSceneRect(-1000000, -1000000, 2000000, 2000000)

        self.view = GraphicsView(self.scene, self)
        self.nodes = []

        self.temp_line = None
        self.connecting_node = None

        self.btn_save = QPushButton("Save to JSON")
        self.btn_load = QPushButton("Load from JSON")

        layout = QVBoxLayout()
        layout.addWidget(self.view)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_load)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.btn_save.clicked.connect(self.save_to_json)
        self.btn_load.clicked.connect(self.load_from_json)

    def add_circle_at(self, pos):
        node = CircleNode(func_code=self.default_func(),
                          scene=self.scene, mainwindow=self)
        node.setPos(pos)
        self.scene.addItem(node)
        self.nodes.append(node)

    def add_circle(self):
        node = CircleNode(func_code=self.default_func(),
                          scene=self.scene, mainwindow=self)
        node.setPos(QPointF(len(self.nodes) * 120, 0))
        self.scene.addItem(node)
        self.nodes.append(node)

    def start_connection(self, node):
        self.connecting_node = node
        start_pos = node.sceneBoundingRect().center()
        self.temp_line = self.scene.addLine(
            start_pos.x(), start_pos.y(),
            start_pos.x(), start_pos.y(),
            QPen(Qt.red, 2, Qt.DashLine)
        )
        self.temp_line.setAcceptedMouseButtons(Qt.NoButton)

    def default_func(self):
        return """def main(*args):
    import pandas as pd
    return pd.DataFrame({'a':[1,2,3], 'b':[4,5,6]})
"""

    def save_to_json(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Flow to JSON", "", "JSON Files (*.json)"
            )
            if not file_path:
                return

            nodes_data = [node.to_json() for node in self.nodes]
            connections_data = []
            for node in self.nodes:
                for conn in node.connections:
                    if conn.start_node.node_id < conn.end_node.node_id:
                        connections_data.append(conn.to_json())

            flow_data = {
                "version": "1.0",
                "nodes": nodes_data,
                "connections": connections_data,
                "scene_info": {
                    "scene_rect": {
                        "x": self.scene.sceneRect().x(),
                        "y": self.scene.sceneRect().y(),
                        "width": self.scene.sceneRect().width(),
                        "height": self.scene.sceneRect().height()
                    }
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(flow_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")

    def load_from_json(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Flow from JSON", "", "JSON Files (*.json)"
            )
            if not file_path:
                return

            self.clear_scene()

            with open(file_path, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)

            node_id_map = {}
            for node_data in flow_data["nodes"]:
                node = CircleNode.from_json(node_data, self.scene, self)
                self.scene.addItem(node)
                self.nodes.append(node)
                node_id_map[node_data["node_id"]] = node

            for conn_data in flow_data["connections"]:
                start_node = node_id_map.get(conn_data["start_node_id"])
                end_node = node_id_map.get(conn_data["end_node_id"])
                if start_node and end_node:
                    start_node.outputs.append(end_node)
                    end_node.inputs.append(start_node)
                    ConnectionLineObj(start_node, end_node, self.scene)

            if "scene_info" in flow_data:
                scene_rect = flow_data["scene_info"]["scene_rect"]
                self.scene.setSceneRect(scene_rect["x"], scene_rect["y"],
                                        scene_rect["width"], scene_rect["height"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")

    def clear_scene(self):
        self.scene.clear()
        self.nodes.clear()
        self.temp_line = None
        self.connecting_node = None
