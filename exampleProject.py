from gdpython import Game, Scene, Layer, Sprite, Text, Sound, Timer
import random

#Konstanten
SCREEN_WIDTH = 800                  #Breite des Spielfensters in Pixeln
SCREEN_HEIGHT = 600                 #Höhe des Spielfensters in Pixeln
STAR_COUNT = 30                     #Anzahl der Sterne, die im Hintergrund erscheinen
ASTEROID_COUNT = 20                 #Anzahl der Asteroiden, die zu Beginn gespawnt werden
ASTEROID_MIN_SPAWN_DISTANCE = 300   #Mindestabstand, den ein Asteroid zum Schiff haben muss, wenn er gespawnt wird
ASTEROID_SPAWN_RANGE = 400          #Bereich um das Schiff, in dem Asteroiden spawnen können (außerhalb des Mindestabstands)
SHOOT_COOLDOWN = 200                #Zeit in Millisekunden, die zwischen zwei Schüssen vergehen muss
SHIP_SPEED = 2                      #Geschwindigkeit, mit der sich das Schiff bewegt (Pixel pro Frame)
SHIP_ROTATION_SPEED = 2             #Geschwindigkeit, mit der sich das Schiff dreht (Grad pro Frame)
BULLET_SPEED = 5                    #Geschwindigkeit, mit der sich die Schüsse bewegen (Pixel pro Frame)
WIN_SCORE = 2000                    #Punktzahl, die erreicht werden muss, um zu gewinnen
POINTS_PER_ASTEROID = 100           #Punkte, die für das Zerstören eines Asteroiden vergeben werden
EXPLOSION_FRAME_DELAY = 100         #Zeit in Millisekunden zwischen den Frames der Explosion-Animation

class MeinSpiel(Game):

    scene: Scene

    def start(self):
        self.background_layer = Layer("background", 0, 0, -1)
        self.scene.add_layer(self.background_layer)
        self.ui = Layer("ui", 0, 0, 2)
        self.scene.add_layer(self.ui)

        for i in range(STAR_COUNT):
            star = Sprite(f"star{i}", random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), 0)
            star.add_animation("0", [f"rsc/Star{random.randint(1,3)}"], loop=False, time_between=0)
            star.play_animation("0")
            self.background_layer.add_object(star)

        self.mypoints = 0
        self.points = Text("points", 30, 50, 0, f"Punkte:{self.mypoints}")
        self.ui.add_object(self.points)

        self.ship = Sprite("ship", 0, 0, 0, collidable=True)
        self.ship.add_animation("0", ["rsc/ship"], False, 0)
        self.ship.play_animation("0")
        self.scene.default_layer.add_object(self.ship)

        for i in range(ASTEROID_COUNT):
            astero = Sprite(f"astero{i}", 0, 0, 0, collidable=True)
            astero.add_animation("0", ["rsc/asteroid7"], False, 0)

            while astero.get_distance_to_position(self.ship.pos_x, self.ship.pos_y) < ASTEROID_MIN_SPAWN_DISTANCE:
                astero.pos_x = random.randint(-ASTEROID_SPAWN_RANGE, ASTEROID_SPAWN_RANGE)
                astero.pos_y = random.randint(-ASTEROID_SPAWN_RANGE, ASTEROID_SPAWN_RANGE)
            astero.play_animation("0")
            astero.object_var = {"speed_move": random.randint(0, 5) / 10, "speed_rot": random.randint(1, 5)}
            astero.object_group.append("astero")
            astero.rotation = random.randint(0, 359)
            self.scene.default_layer.add_object(astero)

        self.explosion_sound = Sound("explosionSound", "rsc/Explosion.wav", volume=0.01)

        self.scene_timer = Timer()
        self.scene_timer.start()

        self.shoot_interval = Timer()
        self.shoot_interval.start()

    def update(self):
        self._update_asteroids()
        self._update_ship()
        self._update_bullets()
        self._cleanup_explosions()
        self._handle_shoot_input()
        self._check_win_conditions()

    def _spawn_explosion(self, x, y):
        exp = Sprite(f"explosion{self.scene_timer.get_time()}", x, y, 10)
        exp.add_animation("0", [
            "rsc/Explosion8",
            "rsc/Explosion7",
            "rsc/Explosion6",
            "rsc/Explosion5",
            "rsc/Explosion4",
            "rsc/Explosion3",
            "rsc/Explosion2",
            "rsc/Explosion",
        ], loop=False, time_between=EXPLOSION_FRAME_DELAY)
        exp.object_group.append("explosion")
        exp.play_animation("0")
        self.scene.default_layer.add_object(exp)
        self.explosion_sound.play()

    def _update_asteroids(self):
        ship = self.scene.default_layer.get_object_by_name("ship")
        for obj in list(self.scene.default_layer.objects):
            if "astero" not in obj.object_group:
                continue
            obj.rotation += obj.object_var["speed_rot"]
            if ship:
                obj.move_toward_position(self.ship.pos_x, self.ship.pos_y,
                                         obj.object_var["speed_move"])
                if obj.check_collision(self.ship):
                    self._spawn_explosion(obj.pos_x, obj.pos_y)
                    self.scene.default_layer.delete_objects("ship")
            self._check_bullet_collisions(obj)

    def _check_bullet_collisions(self, asteroid):
        for obj in list(self.scene.default_layer.objects):
            if "bullet" not in obj.object_group:
                continue
            if obj.check_collision(asteroid):
                self._spawn_explosion(obj.pos_x, obj.pos_y)
                self.scene.default_layer.delete_objects(obj.name)
                self.scene.default_layer.delete_objects(asteroid.name)
                self.mypoints += POINTS_PER_ASTEROID
                self.points.set_text(f"Points:{self.mypoints}")

    def _update_ship(self):
        if self.scene.default_layer.get_object_by_name("ship") is None:
            return
        self.ship.move_toward_angle(self.ship.rotation, SHIP_SPEED)
        self.ship.rotate_toward_position(
            self.scene.mouse_x - self.scene.default_layer.pos_x,
            self.scene.mouse_y - self.scene.default_layer.pos_y,
            SHIP_ROTATION_SPEED
        )
        self.scene.default_camera.pos_x = self.ship.pos_x
        self.scene.default_camera.pos_y = self.ship.pos_y

    def _update_bullets(self):
        for obj in list(self.scene.default_layer.objects):
            if "bullet" in obj.object_group:
                obj.move_toward_angle(obj.object_var["rot"], BULLET_SPEED)

    def _cleanup_explosions(self):
        for obj in list(self.scene.default_layer.objects):
            if "explosion" in obj.object_group:
                if obj.current_frame == len(obj.current_animation["paths"]) - 1:
                    self.scene.default_layer.delete_objects(obj.name)

    def _handle_shoot_input(self):
        if not self.scene.is_key_pressed("space"):
            return
        if self.shoot_interval.get_time() <= SHOOT_COOLDOWN:
            return
        if self.scene.default_layer.get_object_by_name("ship") is None:
            return
        bullet = Sprite(f"bullet{self.scene_timer.get_time()}",
                        self.ship.pos_x, self.ship.pos_y, 0, collidable=True)
        bullet.add_animation("0", ["rsc/Bullet.png"], loop=False, time_between=0)
        bullet.object_var = {"rot": self.ship.rotation}
        bullet.object_group.append("bullet")
        bullet.play_animation("0")
        self.scene.default_layer.add_object(bullet)
        self.shoot_interval.reset()

    def _check_win_conditions(self):
        if self.mypoints >= WIN_SCORE:
            scene2 = Scene("Win", size_x=SCREEN_WIDTH, size_y=SCREEN_HEIGHT, background="#000000")
            scene2.default_layer.add_object(
                Text("YouWin", -170, 0, 0, text="You Win", font_size=60, color="#ffff00"))
            self.game_window.change_scene(scene2)
        if self.scene.default_layer.get_object_by_name("ship") is None:
            scene3 = Scene("GameOver", size_x=SCREEN_WIDTH, size_y=SCREEN_HEIGHT, background="#000000")
            scene3.default_layer.add_object(
                Text("gameOver", -190, 0, 0, text="Game Over", font_size=60, color="#ff0000"))
            self.game_window.change_scene(scene3)


MeinSpiel()