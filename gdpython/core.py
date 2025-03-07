from PyQt6.QtWidgets import QMainWindow  , QWidget
from PyQt6.QtGui import QPainter, QColor, QTransform
from PyQt6.QtCore import  QObject, pyqtSignal, Qt, QUrl, QElapsedTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from .objects import Layer, Camera, Sprite, Text


class Scene(QObject):

    sceneUpdated = pyqtSignal()
    MouseX = 0
    MouseY = 0

    def __init__(self, name:str  , sizeX:int = 800, sizeY:int = 800, background:str = "#000000" ):
        """Scene erlaubt es uns verschiedene Szenen zu erstellen die zur verwaltung von Layern dienen und es ermöglichen Spiel-Level
        zb. zu erstellen."""
        super().__init__()
        self.name = name
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.background = background
        self.layers = []
        self.cameras = []
        self.defaultLayer = Layer("DefaultLayer", 0 , 0 , 0)
        self.defaultCamera = Camera("DefaultCamera", 0, 0, scene_width = self.sizeX, scene_height = self.sizeY, layer=self.defaultLayer)
        self.keyPressed = set()
        self.activeCameraIndex = 0

        self.addLayer(self.defaultLayer)
        self.addCamera(self.defaultCamera)
        
    def updateScene(self):
        """Sendet ein Signal, um die Szene zu aktualisieren"""
        activCam = self.getActiveCamera()
        if activCam and activCam.layer:
            activCam.layer.posX = -activCam.posX + activCam.width/2
            activCam.layer.posY = -activCam.posY + activCam.height/2

        self.sceneUpdated.emit()

    def setBackground(self, newColor:str):
        """Setzt die Hintergrundfarbe und sendet ein Signal"""
        self.background = newColor
        self.updateScene()

    def isKeyPressed(self , key):
        """Überprüft ob eine bestimmte Taste gedrückt wird"""
        return key.lower() in self.keyPressed
    
    def addCamera(self, camera):
        """Fügt eine Kamera zur Szene hinzu"""
        self.cameras.append(camera)
        self.updateScene()

    def getActiveCamera(self):
        """Gibt die aktive Kamera zurück"""
        if self.cameras:
            return self.cameras[self.activeCameraIndex]
        else: return None
    def setActiveCamera(self, index):
        """Wechselt zur Kamera mit dem gegebenen Index"""
        if 0 <= index < len(self.cameras):
            self.activeCameraIndex = index
            self.updateScene()

    def addLayer(self, layer):
        """Fügt einer Szene einen Layer hinzu"""
        layer.scene = self
        self.layers.append(layer)
        self.layers.sort(key=lambda l: l.z_index)
        self.updateScene()

    def getObjectByName(self, name:str):
        """Durchsucht alle Layer nach einem Objekt mit dem gegebenen Namen"""
        for layer in self.layers:
            obj = layer.getObjectByName(name)
            if obj:
                return obj
        return None

class InputHandler(QObject):
    """Steuert die Tastatureingaben und speichert gedrückte Tasten"""
    def __init__(self, scene):
        super().__init__()
        self.scene:Scene = scene

    def keyPressEvent(self, event):
        """Wird aufgerufen wenn eine Taste gedrückt wird."""
        key = self.keyToString(event.key())
        if key:
            self.scene.keyPressed.add(key)

    def keyReleaseEvent(self, event):
        key = self.keyToString(event.key())
        if key and key in self.scene.keyPressed:
            self.scene.keyPressed.remove(key)

    def keyToString(self, qtkey):
        """umwandeln von QT-Tasten in String form für spätere Abfragen"""
        key_map = {
            Qt.Key.Key_W: "w",
            Qt.Key.Key_A: "a",
            Qt.Key.Key_S: "s",
            Qt.Key.Key_D: "d",
            Qt.Key.Key_Space: "space"
        }
        return key_map.get(qtkey, None)

class RenderManager(QMainWindow):
    def __init__(self, scene:Scene, inputHandler:InputHandler):
        super().__init__()
        self.scene = scene
        self.inputHandler = inputHandler
        self.sizeX = scene.sizeX
        self.sizeY = scene.sizeY
        self.initWindows()
    
    def initWindows(self):
        self.setWindowTitle("New Game")
        self.setGeometry(0,0, self.sizeX, self.sizeY)
        self.canvas = Canvas(self.scene)
        self.setCentralWidget(self.canvas)
        self.show()

    def keyPressEvent(self, event):
        """Leitet Tastatureingabe an den inputHandler weiter"""
        self.inputHandler.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Leitet Tastatureingabe an den inputHandler weiter"""
        self.inputHandler.keyReleaseEvent(event)

    def changeScene(self, newScene:"Scene"):
        """Wechsel zu einer neuen Szene"""
        self.scene.sceneUpdated.disconnect(self.canvas.update)
        self.scene = newScene
        self.canvas.scene = newScene
        newScene.sceneUpdated.connect(self.canvas.update)
        self.canvas.update()

class Canvas(QWidget):
    """Zeichenfläche für die Szene"""
    def __init__(self, scene:Scene):
        super().__init__()
        self.scene:Scene = scene
        self.scene.sceneUpdated.connect(self.update)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        """Speichert die aktuelle Mausposition in der Szene"""
        self.scene.MouseX = event.position().x()
        self.scene.MouseY = event.position().y()


    def paintEvent(self,event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.scene.background))

        for layer in sorted(self.scene.layers, key=lambda l: l.z_index):
            painter.save()
            transform = QTransform()
            transform.translate(layer.posX, layer.posY)
            transform.rotate(layer.rotation)
            painter.setTransform(transform)
            for obj in sorted(layer.objects, key= lambda x: x.z_index):
                if isinstance(obj, Sprite) and not obj.image.isNull():

                    obj_tranform = QTransform()
                    obj_tranform.translate(obj.posX + layer.posX, obj.posY + layer.posY)
                    obj_tranform.translate(obj.rotationPointX, obj.rotationPointY)
                    obj_tranform.rotate(obj.rotation)
                    obj_tranform.translate(-obj.rotationPointX, -obj.rotationPointY)

                    painter.setTransform(obj_tranform)
                    painter.drawPixmap(0,0,obj.image)
                
                elif isinstance(obj, Text):
                    painter.setFont(obj.font)
                    painter.setPen(obj.color)
                    painter.drawText(int(obj.posX),int(obj.posY), obj.text)

                elif obj.image.isNull():
                    raise Exception(f"\nBild {obj.name} >> {obj.image} konnte nicht geladen werden\n")

                
            painter.restore()
        painter.end()

class Music(QObject):
    def __init__(self, file_path, volume=0.5):
        super().__init__()
        self.audio_ouput = QAudioOutput()
        self.music = QMediaPlayer()
        self.music.setAudioOutput(self.audio_ouput)
        self.music.setSource(QUrl.fromLocalFile(file_path))
        self.audio_ouput.setVolume(volume)

    def play(self, loop=True):
        if loop:
            self.music.setLoops(QMediaPlayer.Loops.Infinite)
        self.music.play()

    def stop(self):
        self.music.stop()

class Timer(QObject):
    timerUpdated = pyqtSignal(float)

    def __init__(self,):
        super().__init__()
        """Erstellt eine Stopuhr"""
        self.elapsed_timer = QElapsedTimer()
        self.running = False

    def start(self):
        if not self.running:
            self.elapsed_timer.start()
            self.running = True

    def pause(self):
        self.running = False

    def reset(self):
        self.elapsed_timer.start()

    def getTime(self):
        """Gibt die zeit der Stopuhr aus"""
        if self.running:
            return self.elapsed_timer.elapsed()
        return 0.0
    