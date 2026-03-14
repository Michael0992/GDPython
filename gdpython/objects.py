from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from typing import List
import math


class Objects:

    def __init__(self, name:str, pos_x:int, pos_y:int, z_index:int = 0):
        self.name = name
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.z_index = z_index
        self.object_var = {}
        self.object_group:List[str] = []
        self.scene = None

        self.rotation = 0
        self.rotation_point_x = 0
        self.rotation_point_y = 0

    def move_toward_angle(self, angle, distance):
        """Bewegt ein Objekt in Richtung eines Winkels mit einer Geschwindigkeit von x Pixel pro Sekunde."""
        radians = math.radians(angle)
        vx = distance * math.cos(radians)
        vy = distance * math.sin(radians)

        self.pos_x += vx
        self.pos_y += vy

        if self.scene:
            self.scene.update_scene()

    def rotate_toward_position(self, target_x, target_y, speed):
        """Dreht das Objekt mit der Geschwindigkeit 'speed' pro Sekunde zur Zielposition."""
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y

        target_angle = math.degrees(math.atan2(dy, dx))

        angle_diff = (target_angle - self.rotation) % 360

        if angle_diff > 180:
            angle_diff -= 360

        if abs(angle_diff) < speed:
            self.rotation = target_angle
        else:
            self.rotation += speed if angle_diff > 0 else -speed

        self.rotation %= 360

        if self.scene:
            self.scene.update_scene()

    def move_toward_position(self, x, y, speed):
        """Bewegt das Objekt schrittweise zur Zielposition."""
        if self.pos_x < x: self.pos_x += speed
        if self.pos_x > x: self.pos_x -= speed
        if self.pos_y < y: self.pos_y += speed
        if self.pos_y > y: self.pos_y -= speed

        if self.scene:
            self.scene.update_scene()

    def get_distance_to_position(self, x, y):
        """Gibt die Distanz zwischen dem Objekt und einer Position zurück."""
        return math.sqrt((x - self.pos_x)**2 + (y - self.pos_x)**2)

    def get_absolute_position(self, layer=None):
        """Gibt die Koordinaten eines Objekts zurück im Verhältnis zu einem Layer."""
        if layer:
            return self.pos_x + layer.pos_x, self.pos_y + layer.pos_y
        else:
            return self.pos_x, self.pos_y


class Sprite(Objects):
    def __init__(self, name:str, pos_x:int, pos_y:int, z_index:int = 0, size_x:int = 0, size_y:int = 0):
        super().__init__(name, pos_x, pos_y, z_index)
        self.size_x = size_x
        self.size_y = size_y
        self.image = QPixmap()
        self.animations = {}
        self.current_animation = None
        self.played = False
        self.animation_timer = QTimer()
        self.current_frame = 0
        self.scene = None
        self.animation_timer.timeout.connect(self.update_animation)

    def add_animation(self, name, paths, loop=True, time_between=100):
        """Füge eine Animation hinzu."""
        self.animations[name] = {
            "paths": paths,
            "loop": loop,
            "time_between": time_between
        }

    def play_animation(self, name):
        """Spiele eine Animation ab."""
        if name in self.animations:
            self.current_animation = self.animations[name]
            self.current_frame = 0
            self.played = False

            frames = self.current_animation["paths"]
            if frames:
                self.image = QPixmap(frames[0])
                self.animation_timer.start(self.current_animation["time_between"])

    def update_animation(self):
        """Aktualisiert das Animations-Frame."""
        if self.current_animation and not self.played:
            frames = self.current_animation["paths"]

            if self.current_frame < len(frames) - 1:
                self.current_frame += 1
            else:
                if self.current_animation["loop"]:
                    self.current_frame = 0
                else:
                    self.animation_timer.stop()
                    self.played = True
                    return
            self.image = QPixmap(frames[self.current_frame])

    def check_collision(self, other:"Sprite") -> bool:
        """Prüft, ob sich die Collision-Boxes dieses Sprites und eines anderen überschneiden."""
        if not isinstance(other, Sprite):
            return False
        return (
            self.pos_x < other.pos_x + other.size_x and
            self.pos_x + self.size_x > other.pos_x and
            self.pos_y < other.pos_y + other.size_y and
            self.pos_y + self.size_y > other.pos_y
        )


class Camera(Objects):
    def __init__(self, name, pos_x, pos_y, scene_width=800, scene_height=800, layer=None):
        super().__init__(name, pos_x, pos_y)
        self.layer = layer
        self.width = scene_width
        self.height = scene_height

    def set_layer(self, layer):
        """Verknüpft die Kamera mit einem Layer."""
        self.layer = layer


class Layer(Objects):

    def __init__(self, name, pos_x, pos_y, z_index=0):
        super().__init__(name, pos_x, pos_y, z_index)
        self.objects = []

    def add_object(self, obj):
        """Fügt ein Objekt hinzu und sortiert nach z_index."""
        self.objects.append(obj)
        self.objects.sort(key=lambda x: x.z_index)
        if self.scene:
            self.scene.update_scene()

    def get_object_by_name(self, name):
        """Gibt ein Objekt anhand seines Namens zurück."""
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None

    def delete_objects(self, name:str):
        """Löscht alle Objekte mit dem angegebenen Namen."""
        self.objects = [obj for obj in self.objects if obj.name != name]
        if self.scene:
            self.scene.update_scene()


class Text(Objects):
    def __init__(self, name:str, pos_x, pos_y, z_index=0, text:str="New text", font_family:str="Arial", font_size:int=16, color:str="#FFFFFF"):
        super().__init__(name, pos_x, pos_y, z_index)
        self.text = text
        self.font = QFont(font_family, font_size)
        self.color = QColor(color.lower())

    def set_text(self, new_text):
        """Ändert den Text."""
        self.text = new_text
        if self.scene:
            self.scene.update_scene()

    def set_font(self, font_family, font_size):
        """Ändert die Schriftart und Schriftgröße."""
        self.font = QFont(font_family, font_size)
        if self.scene:
            self.scene.update_scene()

    def set_color(self, color:str):
        """Ändert die Schriftfarbe."""
        self.color = QColor(color.lower())
        if self.scene:
            self.scene.update_scene()


class Sound(Objects):
    def __init__(self, name, file_path, pos_x=0, pos_y=0, volume=0.5):
        super().__init__(name, pos_x, pos_y)
        self.sound = QSoundEffect()
        self.sound.setSource(QUrl.fromLocalFile(file_path))
        self.sound.setVolume(volume)

    def play(self):
        """Spielt den Soundeffekt ab."""
        self.sound.play()