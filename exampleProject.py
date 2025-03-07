
from gdpython import *
import random


class MeinSpiel(Game):

    scene: Scene 


    def start(self):
        self.backgroundLayer = Layer("background", 0, 0, -1)
        self.scene.addLayer(self.backgroundLayer)
        self.ui = Layer("ui", 0, 0, 2)
        self.scene.addLayer(self.ui)

        for i in range(30):
            star = Sprite(f"star{i}", random.randint(0,800), random.randint(0,600), 0)
            star.addAnimation("0", [f"rsc/Star{random.randint(1,3)}"], loop=False, timeBetween=0)
            star.playAnimation("0")
            self.backgroundLayer.addObject(star)

        self.mypoints = 0
        self.points = Text("points", 30, 50, 0, f"Punkte:{self.mypoints}")
        self.ui.addObject(self.points)
        

        self.ship = Sprite("ship", 0, 0, 0, 26, 27)
        self.ship.addAnimation("0", ["rsc/ship"], False, 0)
        self.ship.playAnimation("0")
        self.scene.defaultLayer.addObject(self.ship)

        for i in range(20):
            astero = Sprite(f"astero{i}",0, 0, 0, 32, 32)
            astero.addAnimation("0", ["rsc/asteroid7"], False, 0)
            astero.rotationPointX = 27
            astero.rotationPointY = 28
            while(astero.getDistanceToPosition(self.ship.posX , self.ship.posY) < 300):
                astero.posX = random.randint(-400, 400)
                astero.posY = random.randint(-400, 400)
            astero.playAnimation("0")
            astero.objectVar = {"speedMove":random.randint(0,5)/10, "speedRot":random.randint(1,5)}
            astero.objectGroup.append("astero")
            astero.rotation = random.randint(0,359)
            self.scene.defaultLayer.addObject(astero)
        
        self.explosion = Sprite("explosion", 0 , 0 , 10)
        self.explosion.addAnimation("0", [
            "rsc/Explosion8",
            "rsc/Explosion7",
            "rsc/Explosion6",
            "rsc/Explosion5",
            "rsc/Explosion4",
            "rsc/Explosion3",
            "rsc/Explosion2",
            "rsc/Explosion",
        ], loop=False, timeBetween=100)
        
        self.explosionSound = Sound("explosionSound", "rsc/Explosion.wav", volume=0.2)

        self.sceneTimer = Timer()
        self.sceneTimer.start()

        self.shootInterval = Timer()
        self.shootInterval.start()

    def update(self):
        for astero in self.scene.defaultLayer.objects:
            astero:Sprite
            bullet:Sprite
            if "astero" in astero.objectGroup:
                astero.rotation += astero.objectVar["speedRot"]
                if self.scene.defaultLayer.getObjectByName("ship") != None: 
                    astero.moveTowardPosition(self.ship.posX, self.ship.posY, astero.objectVar["speedMove"])
                    if astero.checkCollision(self.ship):
                        self.scene.defaultLayer.deleteObjects("ship")
                        self.explosion.posX = astero.posX          
                        self.explosion.posY = astero.posY
                        self.explosion.objectGroup.append("explosion")
                        self.scene.defaultLayer.addObject(self.explosion)
                        self.explosion.playAnimation("0")
                        self.explosionSound.play()

                for bullet in self.scene.defaultLayer.objects:
                    if "bullet" in bullet.objectGroup:                     

                        if bullet.checkCollision(astero):
                            explosion = Sprite(f"explosion{self.sceneTimer.getTime()}", bullet.posX , bullet.posY , 10)
                            explosion.addAnimation("0", [
                                "rsc/Explosion8",
                                "rsc/Explosion7",
                                "rsc/Explosion6",
                                "rsc/Explosion5",
                                "rsc/Explosion4",
                                "rsc/Explosion3",
                                "rsc/Explosion2",
                                "rsc/Explosion",
                            ], loop=False, timeBetween=100)    
                            self.scene.defaultLayer.addObject(explosion)
                            explosion.objectGroup.append("explosion")
                            explosion.playAnimation("0")
                            self.scene.defaultLayer.deleteObjects(bullet.name)
                            self.scene.defaultLayer.deleteObjects(astero.name)
                            self.mypoints +=100
                            self.points.setText(f"Points:{self.mypoints}")
                            self.explosionSound.play()



        if self.scene.defaultLayer.getObjectByName("ship") != None:
            # ship:Sprite = self.scene.getObjectByName("ship")
            self.ship.moveTowardAngle(self.ship.rotation, 2)
            self.ship.rotateTowardPosition(self.scene.MouseX - self.scene.defaultLayer.posX , self.scene.MouseY - self.scene.defaultLayer.posY, 2)

        for explosion in self.scene.defaultLayer.objects:
            explosion:Sprite
            if "explosion" in explosion.objectGroup:
                if explosion.currentFrame == len(explosion.currentAnimation["paths"]) - 1:
                    self.scene.defaultLayer.deleteObjects(explosion.name)


   
        for bullet in self.scene.defaultLayer.objects:
            if "bullet" in bullet.objectGroup:
                bullet.moveTowardAngle(bullet.objectVar["rot"], 5)

        
        self.scene.defaultCamera.posX = self.ship.posX
        self.scene.defaultCamera.posY = self.ship.posY

        if self.scene.isKeyPressed("space") and self.shootInterval.getTime() > 200 and self.scene.defaultLayer.getObjectByName("ship") != None:
            bullet = Sprite(f"bullet{self.sceneTimer.getTime()}",self.ship.posX ,self.ship.posY,0,10,10)
            bullet.addAnimation("0", ["rsc/Bullet.png"],loop=False, timeBetween=0)
            bullet.objectVar = {"rot":self.ship.rotation}
            bullet.objectGroup.append("bullet")
            bullet.playAnimation("0")
            self.scene.defaultLayer.addObject(bullet)
            self.shootInterval.reset()



        if self.mypoints == 2000:
            scene2 = Scene("Win", sizeX=800, sizeY=600, background="#000000")
            scene2.defaultLayer.addObject(Text("YouWin", -170, 0, 0, text="You Win",font_size=60 ,color="#ffff00"))
            self.game_window.changeScene(scene2)


        if self.scene.defaultLayer.getObjectByName("ship") == None:
            scene3 = Scene("GameOver", sizeX=800, sizeY=600, background="#000000")
            scene3.defaultLayer.addObject(Text("gameOver", -190, 0, 0, text="Game Over",font_size=60 ,color="#ff0000"))
            self.game_window.changeScene(scene3)


MeinSpiel()
