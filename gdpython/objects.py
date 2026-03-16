from PyQt6.QtGui import QPixmap, QColor, QFont, QTransform
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from typing import List
import math

#Konstanten
DEBUG = False

class GameObject:

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

    def move_toward_angle(self, angle, speed):
        """Bewegt ein Objekt in Richtung eines Winkels mit einer Geschwindigkeit von x Pixel pro Frame."""
        angle_radians = math.radians(angle)
        velocity_x = speed * math.cos(angle_radians)
        velocity_y = speed * math.sin(angle_radians)

        self.pos_x += velocity_x
        self.pos_y += velocity_y

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

    def move_toward_position(self, target_x, target_y, speed):
        """Bewegt das Objekt mit der Geschwindigkeit 'speed' (Pixel pro Frame) zur Zielposition."""
        if self.pos_x < target_x:
            self.pos_x = min(self.pos_x + speed, target_x)
        if self.pos_x > target_x:
            self.pos_x = max(self.pos_x - speed, target_x)
        if self.pos_y < target_y:
            self.pos_y = min(self.pos_y + speed, target_y)
        if self.pos_y > target_y:
            self.pos_y = max(self.pos_y - speed, target_y)

        if self.scene:
            self.scene.update_scene()

    def get_distance_to_position(self, target_x, target_y):
        """Gibt die Distanz zwischen dem Objekt und einer Position zurück."""
        return math.sqrt((target_x - self.pos_x)**2 + (target_y - self.pos_y)**2)

    def get_absolute_position(self, layer=None):
        """Gibt die Koordinaten eines Objekts zurück im Verhältnis zu einem Layer."""
        if layer:
            return self.pos_x + layer.pos_x, self.pos_y + layer.pos_y
        else:
            return self.pos_x, self.pos_y
        
    def render (self, painter, layer_transform):
        """Wird von Kindklassen überschrieben, um sich selbst zu rendern."""
        pass


class Sprite(GameObject):
    def __init__(self, name:str, pos_x:int, pos_y:int, z_index:int = 0, collidable:bool = False,
                hitbox_offset_x:int = 0, hitbox_offset_y:int = 0,
                hitbox_width:int = None, hitbox_height:int = None):
        super().__init__(name, pos_x, pos_y, z_index)
        
        self.image = QPixmap()
        self.animations = {}
        self.current_animation = None
        self.animation_finished = False
        self.animation_timer = QTimer()
        self.current_frame = 0
        self.collidable = collidable

        self.hitbox_offset_x = hitbox_offset_x
        self.hitbox_offset_y = hitbox_offset_y
        self._hitbox_width = hitbox_width
        self._hitbox_height = hitbox_height
        
        self.animation_timer.timeout.connect(self._update_animation)
        
    @property
    def size_x(self):
        return self.image.width()

    @property
    def size_y(self):
        return self.image.height()
    
    @property
    def hitbox_width(self):
        return self._hitbox_width if self._hitbox_width is not None else self.size_x

    @property
    def hitbox_height(self):
        return self._hitbox_height if self._hitbox_height is not None else self.size_y
    
    def add_animation(self, name, paths, loop=True, time_between=100):
        """Füge eine Animation hinzu."""
        self.animations[name] = {
            "paths": paths,
            "loop": loop,
            "time_between": time_between
        }

    def play_animation(self, name):
        if name in self.animations:
            self.current_animation = self.animations[name]
            self.current_frame = 0
            self.animation_finished = False

            frames = self.current_animation["paths"]
            if frames:
                self.image = QPixmap(frames[0])
                self.rotation_point_x = self.image.width() // 2
                self.rotation_point_y = self.image.height() // 2
                self.animation_timer.start(self.current_animation["time_between"])

    def _update_animation(self):
        """Aktualisiert das Animations-Frame."""
        if self.current_animation and not self.animation_finished:
            frames = self.current_animation["paths"]

            if self.current_frame < len(frames) - 1:
                self.current_frame += 1
            else:
                if self.current_animation["loop"]:
                    self.current_frame = 0
                else:
                    self.animation_timer.stop()
                    self.animation_finished = True
                    return
            self.image = QPixmap(frames[self.current_frame])

    def check_collision(self, other:"Sprite") -> bool:
        if not self.collidable or not isinstance(other, Sprite) or not other.collidable:
            return False
        ax = self.pos_x + self.hitbox_offset_x
        ay = self.pos_y + self.hitbox_offset_y
        bx = other.pos_x + other.hitbox_offset_x
        by = other.pos_y + other.hitbox_offset_y
        return (
            ax < bx + other.hitbox_width and
            ax + self.hitbox_width > bx and
            ay < by + other.hitbox_height and
            ay + self.hitbox_height > by
        )

    def render(self, painter, layer_transform):
        """Zeichnet das Sprite mit korrekter Rotation."""
        if not self.image.isNull():
            obj_transform = QTransform()
            obj_transform.translate(self.pos_x + layer_transform.dx(), self.pos_y + layer_transform.dy())
            obj_transform.translate(self.rotation_point_x, self.rotation_point_y)
            obj_transform.rotate(self.rotation)
            obj_transform.translate(-self.rotation_point_x, -self.rotation_point_y)
            painter.setTransform(obj_transform)
            painter.drawPixmap(0, 0, self.image)

        if DEBUG and self.collidable:
            painter.save()
            debug_transform = QTransform()
            debug_transform.translate(layer_transform.dx(), layer_transform.dy())
            painter.setTransform(debug_transform)
            painter.setPen(QColor("#00FF00"))
            painter.drawRect(
                int(self.pos_x + self.hitbox_offset_x),
                int(self.pos_y + self.hitbox_offset_y),
                self.hitbox_width,
                self.hitbox_height
            )
            painter.restore()

class Camera(GameObject):
    def __init__(self, name, pos_x, pos_y, scene_width=800, scene_height=800, layer=None):
        super().__init__(name, pos_x, pos_y)
        self.layer = layer
        self.width = scene_width
        self.height = scene_height

    def set_layer(self, layer):
        """Verknüpft die Kamera mit einem Layer."""
        self.layer = layer


class Layer(GameObject):

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


class Text(GameObject):
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

    def render(self, painter, layer_transform):
        """Zeichnet den Text."""
        painter.setTransform(layer_transform)
        painter.setFont(self.font)
        painter.setPen(self.color)
        painter.drawText(int(self.pos_x), int(self.pos_y), self.text)

class Sound(GameObject):
    def __init__(self, name, file_path, pos_x=0, pos_y=0, volume=0.5):
        super().__init__(name, pos_x, pos_y)
        self.sound = QSoundEffect()
        self.sound.setSource(QUrl.fromLocalFile(file_path))
        self.sound.setVolume(volume)

    def play(self):
        """Spielt den Soundeffekt ab."""
        self.sound.play()