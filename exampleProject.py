from gdpython import *
import random


class MeinSpiel(Game):

    scene: Scene

    def start(self):
        self.background_layer = Layer("background", 0, 0, -1)
        self.scene.add_layer(self.background_layer)
        self.ui = Layer("ui", 0, 0, 2)
        self.scene.add_layer(self.ui)

        for i in range(30):
            star = Sprite(f"star{i}", random.randint(0, 800), random.randint(0, 600), 0)
            star.add_animation("0", [f"rsc/Star{random.randint(1,3)}"], loop=False, time_between=0)
            star.play_animation("0")
            self.background_layer.add_object(star)

        self.mypoints = 0
        self.points = Text("points", 30, 50, 0, f"Punkte:{self.mypoints}")
        self.ui.add_object(self.points)

        self.ship = Sprite("ship", 0, 0, 0, 26, 27)
        self.ship.add_animation("0", ["rsc/ship"], False, 0)
        self.ship.play_animation("0")
        self.scene.default_layer.add_object(self.ship)

        for i in range(20):
            astero = Sprite(f"astero{i}", 0, 0, 0, 32, 32)
            astero.add_animation("0", ["rsc/asteroid7"], False, 0)
            astero.rotation_point_x = 27
            astero.rotation_point_y = 28
            while astero.get_distance_to_position(self.ship.pos_x, self.ship.pos_y) < 300:
                astero.pos_x = random.randint(-400, 400)
                astero.pos_y = random.randint(-400, 400)
            astero.play_animation("0")
            astero.object_var = {"speed_move": random.randint(0, 5) / 10, "speed_rot": random.randint(1, 5)}
            astero.object_group.append("astero")
            astero.rotation = random.randint(0, 359)
            self.scene.default_layer.add_object(astero)

        self.explosion = Sprite("explosion", 0, 0, 10)
        self.explosion.add_animation("0", [
            "rsc/Explosion8",
            "rsc/Explosion7",
            "rsc/Explosion6",
            "rsc/Explosion5",
            "rsc/Explosion4",
            "rsc/Explosion3",
            "rsc/Explosion2",
            "rsc/Explosion",
        ], loop=False, time_between=100)

        self.explosion_sound = Sound("explosionSound", "rsc/Explosion.wav", volume=0.2)

        self.scene_timer = Timer()
        self.scene_timer.start()

        self.shoot_interval = Timer()
        self.shoot_interval.start()

    def update(self):
        for astero in self.scene.default_layer.objects:
            astero: Sprite
            bullet: Sprite
            if "astero" in astero.object_group:
                astero.rotation += astero.object_var["speed_rot"]
                if self.scene.default_layer.get_object_by_name("ship") is not None:
                    astero.move_toward_position(self.ship.pos_x, self.ship.pos_y, astero.object_var["speed_move"])
                    if astero.check_collision(self.ship):
                        self.scene.default_layer.delete_objects("ship")
                        self.explosion.pos_x = astero.pos_x
                        self.explosion.pos_y = astero.pos_y
                        self.explosion.object_group.append("explosion")
                        self.scene.default_layer.add_object(self.explosion)
                        self.explosion.play_animation("0")
                        self.explosion_sound.play()

                for bullet in self.scene.default_layer.objects:
                    if "bullet" in bullet.object_group:
                        if bullet.check_collision(astero):
                            explosion = Sprite(f"explosion{self.scene_timer.get_time()}", bullet.pos_x, bullet.pos_y, 10)
                            explosion.add_animation("0", [
                                "rsc/Explosion8",
                                "rsc/Explosion7",
                                "rsc/Explosion6",
                                "rsc/Explosion5",
                                "rsc/Explosion4",
                                "rsc/Explosion3",
                                "rsc/Explosion2",
                                "rsc/Explosion",
                            ], loop=False, time_between=100)
                            self.scene.default_layer.add_object(explosion)
                            explosion.object_group.append("explosion")
                            explosion.play_animation("0")
                            self.scene.default_layer.delete_objects(bullet.name)
                            self.scene.default_layer.delete_objects(astero.name)
                            self.mypoints += 100
                            self.points.set_text(f"Points:{self.mypoints}")
                            self.explosion_sound.play()

        if self.scene.default_layer.get_object_by_name("ship") is not None:
            self.ship.move_toward_angle(self.ship.rotation, 2)
            self.ship.rotate_toward_position(
                self.scene.mouse_x - self.scene.default_layer.pos_x,
                self.scene.mouse_y - self.scene.default_layer.pos_y,
                2
            )

        for explosion in self.scene.default_layer.objects:
            explosion: Sprite
            if "explosion" in explosion.object_group:
                if explosion.current_frame == len(explosion.current_animation["paths"]) - 1:
                    self.scene.default_layer.delete_objects(explosion.name)

        for bullet in self.scene.default_layer.objects:
            if "bullet" in bullet.object_group:
                bullet.move_toward_angle(bullet.object_var["rot"], 5)

        self.scene.default_camera.pos_x = self.ship.pos_x
        self.scene.default_camera.pos_y = self.ship.pos_y

        if self.scene.is_key_pressed("space") and self.shoot_interval.get_time() > 200 and self.scene.default_layer.get_object_by_name("ship") is not None:
            bullet = Sprite(f"bullet{self.scene_timer.get_time()}", self.ship.pos_x, self.ship.pos_y, 0, 10, 10)
            bullet.add_animation("0", ["rsc/Bullet.png"], loop=False, time_between=0)
            bullet.object_var = {"rot": self.ship.rotation}
            bullet.object_group.append("bullet")
            bullet.play_animation("0")
            self.scene.default_layer.add_object(bullet)
            self.shoot_interval.reset()

        if self.mypoints == 2000:
            scene2 = Scene("Win", size_x=800, size_y=600, background="#000000")
            scene2.default_layer.add_object(Text("YouWin", -170, 0, 0, text="You Win", font_size=60, color="#ffff00"))
            self.game_window.change_scene(scene2)

        if self.scene.default_layer.get_object_by_name("ship") is None:
            scene3 = Scene("GameOver", size_x=800, size_y=600, background="#000000")
            scene3.default_layer.add_object(Text("gameOver", -190, 0, 0, text="Game Over", font_size=60, color="#ff0000"))
            self.game_window.change_scene(scene3)


MeinSpiel()