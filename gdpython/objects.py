from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from typing import List
import math


class Objects:


    def __init__(self, name:str, posX:int, posY:int , z_index:int = 0):
        self.name = name
        self.posX = posX
        self.posY = posY
        self.z_index = z_index
        self.objectVar = {}
        self.objectGroup:List[str] = []
        self.scene = None 

        self.rotation = 0 
        self.rotationPointX = 0
        self.rotationPointY = 0

    def moveTowardAngle(self,angle, distance):
        """Bewegt ein Objekt in richtung eines Winkels mit einer gewschwidikeit von x Pixel pro Sekunde"""
        radians = math.radians(angle)
        vx = distance * math.cos(radians)
        vy = distance * math.sin(radians)

        self.posX += vx
        self.posY += vy

        if self.scene:
            self.scene.updateScene()

    def rotateTowardPosition(self, targetX, targetY, speed):
        """Dreht das Objekt mit der Geschwindikeit  'speed' pro Sekunde zur Zielposition """
        dx = targetX - self.posX
        dy = targetY - self.posY

        target_angle = math.degrees(math.atan2(dy,dx))

        angle_diff = (target_angle - self.rotation) % 360

        if angle_diff >180:
            angle_diff -= 360

        if abs(angle_diff) < speed:
            self.rotation = target_angle
        else:
            self.rotation += speed if angle_diff > 0 else -speed

        self.rotation %= 360

        if self.scene:
            self.scene.updateScene()


    def moveTowardPosition(self, x, y , speed):
        if self.posX < x: self.posX += speed
        if self.posX > x: self.posX -= speed
        if self.posY < y: self.posY += speed
        if self.posY > y: self.posY -= speed
        
        if self.scene:
            self.scene.updateScene()

    def getDistanceToPosition(self, x, y):
        return math.sqrt((x - self.posX)**2 + (y - self.posX)**2)

    def getAbsolutePostion(self, layer=None):
        """Gibt die koordinaten eines Objekts zurück im verhältnis zu einem Layer"""
        if layer:
            return self.posX + layer.posX, self.posY + layer.posY
        else:
            return self.posX, self.posY
         
class Sprite(Objects):
    def __init__(self, name:str, posX:int, posY:int, z_index:int = 0, sizeX:int = 0, sizeY:int= 0):
        super().__init__(name, posX, posY, z_index)
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.image = QPixmap()
        self.animations = {}
        self.currentAnimation = None
        self.played = False
        self.animationTimer = QTimer()
        self.currentFrame = 0
        self.scene = None
        self.animationTimer.timeout.connect(self.updateAnimation)


    def addAnimation(self, name, paths, loop=True , timeBetween= 100):
        """Füge eine Animation hinzu"""
        self.animations[name] = {
            "paths":paths,
            "loop":loop,
            "timeBetween":timeBetween
        }

    def playAnimation(self, name):
        """Spiele eine Animation ab"""
        if name in self.animations:
            self.currentAnimation = self.animations[name]
            self.currentFrame = 0
            self.played = False

            frames = self.currentAnimation["paths"]
            if frames:
                self.image = QPixmap(frames[0])
                self.animationTimer.start(self.currentAnimation["timeBetween"])
    
    def updateAnimation(self):
        """Aktualisiert das AnimationsFrame"""
        if self.currentAnimation and not self.played:
            frames = self.currentAnimation["paths"]

            if self.currentFrame < len(frames) - 1:
                self.currentFrame +=1
            else:
                if self.currentAnimation["loop"]:
                    self.currentFrame = 0
                else:
                    self.animationTimer.stop()
                    self.played = True
                    return 
            self.image = QPixmap(frames[self.currentFrame])

    def checkCollision(self, other:"Sprite") -> bool:
        """Prüft ob sich die Collsion Boxes dieses Sprites und eines anderen überschneiden """
        if not isinstance(other, Sprite):
            return False
        return(
            self.posX < other.posX + other.sizeX and
            self.posX + self.sizeX > other.posX and
            self.posY < other.posY + other.sizeY and
            self.posY + self.sizeY > other.posY 
        )

class Camera(Objects):
    def __init__(self, name, posX, posY, scene_width=800, scene_height=800, layer=None):
        super().__init__(name, posX, posY)
        self.layer = layer
        self.width = scene_width
        self.height = scene_height
    
    def setLayer(self,layer):
        """Verküpft Kamera mit Layer"""
        self.layer = layer

class Layer(Objects):

    def __init__(self, name, posX, posY, z_index = 0):
        super().__init__(name, posX, posY, z_index)
        self.objects = []

    def addObject(self, obj):
        """Fügt ein Objekt hinzu und setzt seine Position relativ zum Layer """
        self.objects.append(obj)
        self.objects.sort(key=lambda x: x.z_index)
        if self.scene:
            self.scene.updateScene()

    def getObjectByName(self, name):
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None

    def deleteObjects(self, name:str):
        self.objects = [obj for obj in self.objects if obj.name != name]
        if self.scene:
            self.scene.updateScene()

class Text(Objects):
    def __init__(self, name:str, posX, posY, z_index = 0, text:str="New text", font_family:str="Arial", font_size:int=16, color:str="#FFFFFF"):
        super().__init__(name, posX, posY, z_index)
        self.text = text
        self.font = QFont(font_family, font_size)
        self.color = QColor(color.lower())

    def setText(self, new_text):
        """Ändet den Text"""
        self.text = new_text
        if self.scene:
            self.scene.updateScene()

    def setFont(self, font_family, font_size):
        """Ändert die Schriftart und Größe"""
        self.font = QFont(font_family, font_size)
        if self.scene:
            self.scene.updateScene()

    def setColor(self, color:str):
        """Ändert die Schriftfarbe"""
        self.color = QColor(color.lower())
        if self.scene:
            self.scene.updateScene()

class Sound(Objects):
    def __init__(self, name, file_path, posX=0, posY=0, volume=0.5):
        super().__init__(name, posX, posY)
        self.sound = QSoundEffect()
        self.sound.setSource(QUrl.fromLocalFile(file_path))
        self.sound.setVolume(volume)

    def play(self):
        """Spielt den Soundeefekt ab"""
        self.sound.play()

