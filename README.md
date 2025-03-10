
## GDPython

GDPython ist eine QT6/Python-basierte Game-Engine für die einfache Erstellung von 2D-Spielen.
Sie unterstützt Sprites, Animationen, Szenenhandling, Multi-Layer, Textdarstellung,
Kollisionserkennung sowie Soundeffekte und Musik.

Für mehr Infos über die nutzung von GDPython siehe **doku.md**

#### Installation

```pip install gdpython```

#### Erstellung eines neuen Spiels

Um ein neues Spiel zu erstellen reicht es die Vorlage von void_game_file.py zu nutzen. Der Aufbau einer Spieldatei sollte immer so aussehen:

```python

import random
from gdpython import *

class MyGame(Game):

    scene : Scene
    game_window : RenderManager

    def start(self): #Einmaliger aufruf am Anfang des Spiels
        pass

    def update(self): #Aufruf pro Frame
        pass

        
MyGame()
```
