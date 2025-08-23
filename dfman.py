import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsTextItem, QMainWindow, QPushButton,
    QVBoxLayout, QWidget, QMenu, QGraphicsView, QGraphicsLineItem
)
from PySide6.QtGui import QAction, QPen, QColor, QKeySequence, QShortcut, QTransform
from PySide6.QtCore import Qt, QPointF


def complementary_color(color: QColor):
    r, g, b = color.red(), color.green(), color.blue()
    return QColor(255 - r, 255 - g, 255 - b)


class CustomScene(QGraphicsScene):
    def __init__(self, mainwindow):
        super().__init__()
        self.mainwindow = mainwindow

    def mouseMoveEvent(self, event):
        if self.mainwindow.temp_line and self.mainwindow.connecting_node:
            start_node = self.mainwindow.connecting_node
            start_pos = start_node.sceneBoundingRect().center()
            end_pos = event.scenePos()  # ✅ pos() 대신 scenePos()
            self.mainwindow.temp_line.setLine(start_pos.x(), start_pos.y(),
                                            end_pos.x(), end_pos.y())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        print("Scene mousePressEvent called:", event.scenePos())

        if event.button() == Qt.LeftButton and self.mainwindow.connecting_node:
            # 좌표에 있는 모든 아이템 가져오기
            items = self.items(event.scenePos())
            item = None
            for it in items:
                if isinstance(it, CircleNode):
                    item = it
                    break
                if isinstance(it, QGraphicsTextItem):
                    if isinstance(it.parentItem(), CircleNode):
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
                        print("temp_line removed")

                    ConnectionLineObj(start_node, end_node, self)

            self.mainwindow.temp_line = None
            self.mainwindow.connecting_node = None
            return

        super().mousePressEvent(event)

# ------------------------------
# 연결선 클래스
# ------------------------------
class ConnectionLineObj:
    def __init__(self, start_node, end_node, scene):
        self.start_node = start_node
        self.end_node = end_node

        self.line_item = scene.addLine(0, 0, 0, 0, QPen(Qt.white, 2))
        self.line_item.setZValue(-1)

        self.update_position()  # ✅ 여기서 좌표 확인
        print("ConnectionLine created between:",
              start_node.sceneBoundingRect().center(),
              "->", end_node.sceneBoundingRect().center())

        start_node.connections.append(self)
        end_node.connections.append(self)

    def update_position(self):
        start_pos = self.start_node.sceneBoundingRect().center()
        end_pos = self.end_node.sceneBoundingRect().center()
        print("update_position:", start_pos, "->", end_pos)
        self.line_item.setLine(start_pos.x(), start_pos.y(),
                               end_pos.x(), end_pos.y())

# ------------------------------
# 원 노드 클래스
# ------------------------------
class CircleNode(QGraphicsEllipseItem):
    node_counter = 1
    RADIUS = 40

    def __init__(self, func_code="", node_id=None, scene=None, mainwindow=None):
        # 원을 (−R,−R,R*2,R*2)로 정의 → 중심이 (0,0)
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

        # 이름 라벨 (노드 자식으로)
        self.name = f"Node{CircleNode.node_counter}"
        CircleNode.node_counter += 1
        self.label = QGraphicsTextItem(self.name, self)
        self.update_label_position()

    def itemChange(self, change, value):
        # 노드 이동 시 연결된 선 업데이트 + 라벨 위치 갱신
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

        input_data = []
        for parent in self.inputs:
            input_data.append(parent.execute(clean=clean))

        local_env = {"pd": pd, "input_data": input_data}
        try:
            exec(self.func_code, {}, local_env)
            if "main" in local_env:
                self.cached_result = local_env["main"](*input_data)
        except Exception as e:
            print(f"Error in node {self.node_id}: {e}")
            self.cached_result = None
        return self.cached_result


# ------------------------------
# 뷰 (마우스 따라다니는 임시 선 처리)
# ------------------------------
class GraphicsView(QGraphicsView):
    def __init__(self, scene, mainwindow):
        super().__init__(scene)
        self.mainwindow = mainwindow
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0

        # 줌 앵커
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # 스크롤바 제거
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 드래그 관련 상태
        self._dragging = False
        self._last_mouse_pos = None

        # Ctrl + +/- 단축키
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)

    # -----------------------
    # 마우스 드래그로 화면 이동
    # -----------------------

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
            # 화면 이동량 계산
            delta = event.position().toPoint() - self._last_mouse_pos
            self._last_mouse_pos = event.position().toPoint()

            # 스크롤바 값 갱신 (scale 영향 없음)
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)


    # -----------------------
    # 줌 (마우스 휠 + Ctrl)
    # -----------------------
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # ✅ Ctrl + 휠은 줌
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        elif event.modifiers() & Qt.ShiftModifier:
            # ✅ Shift + 휠 → 수평 스크롤 직접 제어 (속도 줄임)
            delta_x = event.angleDelta().y() / 8    # 기본 단위는 1단계 = 15°, 여기서는 1/8로 줄임
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta_x
            )
        else:
            # 기본 세로 스크롤
            super().wheelEvent(event)

    def zoom_in(self):
        if self.scale_factor < self.max_scale:
            self.scale(1.25, 1.25)
            self.scale_factor *= 1.25

    def zoom_out(self):
        if self.scale_factor > self.min_scale:
            self.scale(0.8, 0.8)
            self.scale_factor *= 0.8


    # -----------------------
    # 컨텍스트 메뉴
    # -----------------------
    def contextMenuEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())

        if isinstance(item, CircleNode):
            # 노드 위 컨텍스트 메뉴
            menu = QMenu(self)
            action_connect = QAction("Start Connection", menu)
            action_connect.triggered.connect(lambda: self.mainwindow.start_connection(item))
            menu.addAction(action_connect)
            menu.exec(event.globalPos())
        else:
            # 빈 공간 컨텍스트 메뉴
            menu = QMenu(self)
            action_add = QAction("Add Circle", menu)
            action_add.triggered.connect(lambda: self.mainwindow.add_circle_at(scene_pos))
            menu.addAction(action_add)
            menu.exec(event.globalPos())


# ------------------------------
# 메인 윈도우
# ------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Flow Editor (Right-Click to Add)")

        #self.scene = QGraphicsScene()
        self.scene = CustomScene(self)   # ✅ 커스텀 
        self.scene.setSceneRect(-1000000, -1000000, 2000000, 2000000)

        self.view = GraphicsView(self.scene, self)
        self.nodes = []

        self.temp_line = None
        self.connecting_node = None

        self.btn_run = QPushButton("Run Selected")
        self.btn_clean_run = QPushButton("Clean Run")

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_clean_run)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.btn_run.clicked.connect(self.run_selected)
        self.btn_clean_run.clicked.connect(lambda: self.run_selected(clean=True))

    def add_circle_at(self, pos):
        node = CircleNode(func_code=self.default_func(),
                        scene=self.scene, mainwindow=self)
        node.setPos(pos)  # 중심이 맞게 정의돼 있으므로 보정 불필요
        self.scene.addItem(node)
        self.nodes.append(node)

    def add_circle(self):
        node = CircleNode(func_code=self.default_func(),
                          scene=self.scene, mainwindow=self)
        node.setPos(QPointF(len(self.nodes) * 120, 0))
        self.scene.addItem(node)
        self.nodes.append(node)

    def run_selected(self, clean=False):
        for item in self.scene.selectedItems():
            if isinstance(item, CircleNode):
                result = item.execute(clean=clean)
                print("Execution result:", result)

    def start_connection(self, node):
        self.connecting_node = node
        start_pos = node.sceneBoundingRect().center()
        self.temp_line = self.scene.addLine(
            start_pos.x(), start_pos.y(),
            start_pos.x(), start_pos.y(),
            QPen(Qt.red, 2, Qt.DashLine)
        )
        # ✅ 임시선은 클릭 안 되게
        self.temp_line.setAcceptedMouseButtons(Qt.NoButton)
        print("temp_line created:", self.temp_line)

    def default_func(self):
        return """def main(*args):
    import pandas as pd
    return pd.DataFrame({'a':[1,2,3], 'b':[4,5,6]})
"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())
