from .core import Scene, RenderManager, InputHandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

class Game():
    def __init__(self, title="GPython Game", sizeX=800, sizeY=600, background="#000000"):
        self.app =  QApplication(sys.argv)
        self.scene = Scene(title,sizeX,sizeY,background)
        self.inputHandler = InputHandler(self.scene)
        self.game_window = RenderManager(self.scene, self.inputHandler)
        self.game_window.setWindowTitle(title)

        if hasattr(self ,"start"):
            self.start()
        
        self.gameloop()
        sys.exit(self.app.exec())


    def gameloop(self):
        if hasattr(self, "update"):
            self.update()
        self.scene.updateScene()
        QTimer.singleShot(16, self.gameloop)