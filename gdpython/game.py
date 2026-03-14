from .core import Scene, RenderManager, InputHandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

class Game():
    def __init__(self, title="GDPython Game", size_x=800, size_y=600, background="#000000"):
        self.app = QApplication(sys.argv)
        self.scene = Scene(title, size_x, size_y, background)
        self.input_handler = InputHandler(self.scene)
        self.game_window = RenderManager(self.scene, self.input_handler)
        self.game_window.setWindowTitle(title)

        if hasattr(self, "start"):
            self.start()
        
        self.game_loop()
        sys.exit(self.app.exec())

    def game_loop(self):
        if hasattr(self, "update"):
            self.update()
        self.scene.update_scene()
        QTimer.singleShot(16, self.game_loop)