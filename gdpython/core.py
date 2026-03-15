from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QTransform
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QUrl, QElapsedTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from .objects import Layer, Camera, Sprite, Text

#Konstanten
DEBUG = False


class Scene(QObject):

    scene_updated = pyqtSignal()
    mouse_x = 0
    mouse_y = 0

    def __init__(self, name:str, size_x:int = 800, size_y:int = 800, background:str = "#000000"):
        """Erlaubt es, verschiedene Szenen zu erstellen, die zur Verwaltung von Layern dienen
        und es ermöglichen, Spiel-Level zu erstellen."""
        super().__init__()
        self.name = name
        self.size_x = size_x
        self.size_y = size_y
        self.background = background
        self.layers = []
        self.cameras = []
        self.default_layer = Layer("DefaultLayer", 0, 0, 0)
        self.default_camera = Camera("DefaultCamera", 0, 0, scene_width=self.size_x, scene_height=self.size_y, layer=self.default_layer)
        self.key_pressed = set()
        self.active_camera_index = 0

        self.add_layer(self.default_layer)
        self.add_camera(self.default_camera)

    def update_scene(self):
        """Sendet ein Signal, um die Szene zu aktualisieren."""
        active_cam = self.get_active_camera()
        if active_cam and active_cam.layer:
            active_cam.layer.pos_x = -active_cam.pos_x + active_cam.width / 2
            active_cam.layer.pos_y = -active_cam.pos_y + active_cam.height / 2

        self.scene_updated.emit()

    def set_background(self, new_color:str):
        """Setzt die Hintergrundfarbe und sendet ein Signal."""
        self.background = new_color
        self.update_scene()

    def is_key_pressed(self, key):
        """Überprüft, ob eine bestimmte Taste gedrückt wird."""
        return key.lower() in self.key_pressed

    def add_camera(self, camera):
        """Fügt eine Kamera zur Szene hinzu."""
        self.cameras.append(camera)
        self.update_scene()

    def get_active_camera(self):
        """Gibt die aktive Kamera zurück."""
        if self.cameras:
            return self.cameras[self.active_camera_index]
        else:
            return None

    def set_active_camera(self, index):
        """Wechselt zur Kamera mit dem gegebenen Index."""
        if 0 <= index < len(self.cameras):
            self.active_camera_index = index
            self.update_scene()

    def add_layer(self, layer):
        """Fügt einer Szene einen Layer hinzu."""
        layer.scene = self
        self.layers.append(layer)
        self.layers.sort(key=lambda layer_item: layer_item.z_index)
        self.update_scene()

    def get_object_by_name(self, name:str):
        """Durchsucht alle Layer nach einem Objekt mit dem gegebenen Namen."""
        for layer in self.layers:
            obj = layer.get_object_by_name(name)
            if obj:
                return obj
        return None


class InputHandler(QObject):
    """Steuert die Tastatureingaben und speichert gedrückte Tasten."""
    def __init__(self, scene):
        super().__init__()
        self.scene:Scene = scene

    def key_press_event(self, event):
        """Wird aufgerufen, wenn eine Taste gedrückt wird."""
        key = self.key_to_string(event.key())
        if key:
            self.scene.key_pressed.add(key)

    def key_release_event(self, event):
        """Wird aufgerufen, wenn eine Taste losgelassen wird."""
        key = self.key_to_string(event.key())
        if key and key in self.scene.key_pressed:
            self.scene.key_pressed.remove(key)

    def key_to_string(self, qtkey):
        """Wandelt Qt-Tasten in String-Form für spätere Abfragen um."""
        key_map = {
            Qt.Key.Key_W: "w",
            Qt.Key.Key_A: "a",
            Qt.Key.Key_S: "s",
            Qt.Key.Key_D: "d",
            Qt.Key.Key_Space: "space"
        }
        return key_map.get(qtkey, None)


class RenderManager(QMainWindow):
    """Verwaltet das Hauptfenster und leitet Eingaben weiter."""
    def __init__(self, scene:Scene, input_handler:InputHandler):
        super().__init__()
        self.scene = scene
        self.input_handler = input_handler
        self.size_x = scene.size_x
        self.size_y = scene.size_y
        self.init_windows()

    def init_windows(self):
        """Initialisiert das Fenster und die Zeichenfläche."""
        self.setWindowTitle("New Game")
        self.setGeometry(0, 0, self.size_x, self.size_y)
        self.canvas = Canvas(self.scene)
        self.setCentralWidget(self.canvas)
        self.show()

    def keyPressEvent(self, event):
        """Leitet Tastendruck an den InputHandler weiter."""
        self.input_handler.key_press_event(event)

    def keyReleaseEvent(self, event):
        """Leitet Tastenloslassen an den InputHandler weiter."""
        self.input_handler.key_release_event(event)

    def change_scene(self, new_scene:"Scene"):
        """Wechselt zu einer neuen Szene."""
        self.scene.scene_updated.disconnect(self.canvas.update)
        self.scene = new_scene
        self.canvas.scene = new_scene
        new_scene.scene_updated.connect(self.canvas.update)
        self.canvas.update()


class Canvas(QWidget):
    """Zeichenfläche für die Szene."""
    def __init__(self, scene:Scene):
        super().__init__()
        self.scene:Scene = scene
        self.scene.scene_updated.connect(self.update)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        """Speichert die aktuelle Mausposition in der Szene."""
        self.scene.mouse_x = event.position().x()
        self.scene.mouse_y = event.position().y()

    def paintEvent(self, event):
        """Zeichnet alle Layer und Objekte der Szene."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.scene.background))

        for layer in sorted(self.scene.layers, key=lambda layer_item: layer_item.z_index):
            painter.save()
            transform = QTransform()
            transform.translate(layer.pos_x, layer.pos_y)
            transform.rotate(layer.rotation)
            painter.setTransform(transform)

            for obj in sorted(layer.objects, key=lambda x: x.z_index):
                if isinstance(obj, Sprite) and not obj.image.isNull():

                    obj_transform = QTransform()
                    obj_transform.translate(obj.pos_x + layer.pos_x, obj.pos_y + layer.pos_y)
                    obj_transform.translate(obj.rotation_point_x, obj.rotation_point_y)
                    obj_transform.rotate(obj.rotation)
                    obj_transform.translate(-obj.rotation_point_x, -obj.rotation_point_y)

                    painter.setTransform(obj_transform)
                    painter.drawPixmap(0, 0, obj.image)

                    # Debug: Kollisionsbox anzeigen
                    if DEBUG and obj.collidable:
                        painter.save()
                        debug_transform = QTransform()
                        debug_transform.translate(layer.pos_x, layer.pos_y)
                        painter.setTransform(debug_transform)
                        painter.setPen(QColor("#00FF00"))
                        painter.drawRect(int(obj.pos_x), int(obj.pos_y), obj.size_x, obj.size_y)
                        painter.restore()

                elif isinstance(obj, Text):
                    painter.setFont(obj.font)
                    painter.setPen(obj.color)
                    painter.drawText(int(obj.pos_x), int(obj.pos_y), obj.text)

                elif obj.image.isNull():
                    raise Exception(f"\nBild {obj.name} >> {obj.image} konnte nicht geladen werden\n")

            painter.restore()
        painter.end()


class Music(QObject):
    """Spielt Hintergrundmusik ab."""
    def __init__(self, file_path, volume=0.5):
        super().__init__()
        self.audio_output = QAudioOutput()
        self.music = QMediaPlayer()
        self.music.setAudioOutput(self.audio_output)
        self.music.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(volume)

    def play(self, loop=True):
        """Startet die Wiedergabe, optional als Endlosschleife."""
        if loop:
            self.music.setLoops(QMediaPlayer.Loops.Infinite)
        self.music.play()

    def stop(self):
        """Stoppt die Wiedergabe."""
        self.music.stop()


class Timer(QObject):
    """Stoppuhr zum Messen von Zeitabständen im Spiel."""
    timer_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.elapsed_timer = QElapsedTimer()
        self.running = False

    def start(self):
        """Startet die Stoppuhr."""
        if not self.running:
            self.elapsed_timer.start()
            self.running = True

    def pause(self):
        """Pausiert die Stoppuhr."""
        self.running = False

    def reset(self):
        """Setzt die Stoppuhr zurück."""
        self.elapsed_timer.start()

    def get_time(self):
        """Gibt die aktuelle Zeit der Stoppuhr in Millisekunden zurück."""
        if self.running:
            return self.elapsed_timer.elapsed()
        return 0.0