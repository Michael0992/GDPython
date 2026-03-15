from gdpython import Game, Scene, Layer, Sprite, Text, Sound, Timer
import random
import math

# ──────────────────────────────────────────────
#  Konstanten
# ──────────────────────────────────────────────
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600

SHIP_SPEED          = 3
SHIP_ROTATION_SPEED = 3
BULLET_SPEED        = 7
SHOOT_COOLDOWN      = 180
POINTS_PER_ASTEROID = 150
EXPLOSION_FRAME_DELAY = 80
STAR_COUNT = 40
SPAWN_DISTANCE = 500

WAVES = [
    {"count": 5,  "speed": 0.8},
    {"count": 8,  "speed": 1.2},
    {"count": 12, "speed": 1.6},
    {"count": 16, "speed": 2.0},
    {"count": 20, "speed": 2.5},
]

EXPLOSION_PATHS = [
    "rsc/Explosion8", "rsc/Explosion7", "rsc/Explosion6",
    "rsc/Explosion5", "rsc/Explosion4", "rsc/Explosion3",
    "rsc/Explosion2", "rsc/Explosion",
]


# ──────────────────────────────────────────────
#  Spiel
# ──────────────────────────────────────────────
class WaveSurvival(Game):

    scene: Scene

    def start(self):
        self._bg_layer   = Layer("bg",   0, 0, -1)
        self._game_layer = self.scene.default_layer
        self._ui_layer   = Layer("ui",   0, 0,  5)

        self.scene.add_layer(self._bg_layer)
        self.scene.add_layer(self._ui_layer)

        self.scene.default_camera.pos_x = SCREEN_WIDTH  // 2
        self.scene.default_camera.pos_y = SCREEN_HEIGHT // 2

        self._uid_timer = Timer()
        self._uid_timer.start()

        self._state = "title"
        self._score = 0
        self._wave_index = 0

        self._build_title()

    # ──────────────────────────────────────────
    #  Hilfsmethoden
    # ──────────────────────────────────────────
    def _clear_all(self):
        self._bg_layer.objects.clear()
        self._game_layer.objects.clear()
        self._ui_layer.objects.clear()

    def _uid(self):
        return int(self._uid_timer.get_time()) + random.randint(0, 99999)

    def _add_stars_bg(self, world=False):
        for i in range(STAR_COUNT):
            if world:
                x = random.randint(-1200, 1200)
                y = random.randint(-900,  900)
            else:
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
            s = Sprite(f"star_{i}", x, y, 0)
            s.add_animation("0", [f"rsc/Star{random.randint(1,3)}"], loop=True, time_between=0)
            s.play_animation("0")
            self._bg_layer.add_object(s)

    def _spawn_explosion(self, x, y):
        exp = Sprite(f"exp_{self._uid()}", x, y, 4)
        exp.add_animation("0", EXPLOSION_PATHS, loop=False, time_between=EXPLOSION_FRAME_DELAY)
        exp.object_group.append("explosion")
        self._game_layer.add_object(exp)
        exp.play_animation("0")
        if hasattr(self, "_expl_sound"):
            self._expl_sound.play()

    # ──────────────────────────────────────────
    #  Screens
    # ──────────────────────────────────────────
    def _build_title(self):
        self._clear_all()
        self._state = "title"
        self.scene.set_background("#000011")
        self.scene.default_camera.pos_x = SCREEN_WIDTH  // 2
        self.scene.default_camera.pos_y = SCREEN_HEIGHT // 2

        self._add_stars_bg(world=False)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        self._ui_layer.add_object(Text("t1", cx - 220, cy - 80, 0,
            text="WAVE SURVIVAL", font_size=52, color="#00eeff"))
        self._ui_layer.add_object(Text("t2", cx - 165, cy - 20, 0,
            text="Überlebe alle Asteroiden-Wellen!", font_size=18, color="#aaaaaa"))
        self._ui_layer.add_object(Text("t3", cx - 130, cy + 40, 0,
            text="[SPACE]  Spiel starten", font_size=22, color="#ffff00"))
        self._ui_layer.add_object(Text("t4", cx - 200, cy + 80, 0,
            text="Steuerung:  Maus = Ziel  |  SPACE = Schiessen", font_size=15, color="#666666"))

    def _build_game(self):
        self._clear_all()
        self._state  = "playing"
        self._score  = 0
        self._wave_index = 0
        self._wave_active = False
        self._wave_countdown_active = True
        self._countdown_end = 2000

        self.scene.set_background("#000008")
        self._add_stars_bg(world=True)

        self._ship = Sprite("ship", 0, 0, 0, collidable=True)
        self._ship.add_animation("0", ["rsc/ship"], False, 0)
        self._ship.play_animation("0")
        self._game_layer.add_object(self._ship)

        self._txt_score = Text("score", 10, 30, 0, text="Punkte: 0",
                               font_size=18, color="#ffffff")
        self._txt_wave  = Text("wave",  10, 55, 0, text="Welle: 1",
                               font_size=18, color="#00eeff")
        self._txt_info  = Text("info",
                               SCREEN_WIDTH // 2 - 160,
                               SCREEN_HEIGHT // 2 - 20, 0,
                               text="Welle 1 beginnt ...",
                               font_size=26, color="#ffff00")
        self._ui_layer.add_object(self._txt_score)
        self._ui_layer.add_object(self._txt_wave)
        self._ui_layer.add_object(self._txt_info)

        self._expl_sound  = Sound("expl", "rsc/Explosion.wav", volume=0.2)
        self._shoot_timer = Timer()
        self._shoot_timer.start()
        self._wave_timer  = Timer()
        self._wave_timer.start()

        self.scene.default_camera.pos_x = 0
        self.scene.default_camera.pos_y = 0

    def _build_game_over(self):
        self._clear_all()
        self._state = "gameover"
        self.scene.set_background("#110000")
        self.scene.default_camera.pos_x = SCREEN_WIDTH  // 2
        self.scene.default_camera.pos_y = SCREEN_HEIGHT // 2

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self._ui_layer.add_object(Text("go", cx-190, cy-80,  0,
            text="GAME OVER", font_size=56, color="#ff2222"))
        self._ui_layer.add_object(Text("sc", cx-120, cy-20,  0,
            text=f"Dein Score:  {self._score}", font_size=22, color="#ffffff"))
        self._ui_layer.add_object(Text("wv", cx-140, cy+20,  0,
            text=f"Erreichte Welle:  {self._wave_index + 1}", font_size=20, color="#aaaaaa"))
        self._ui_layer.add_object(Text("re", cx-130, cy+70,  0,
            text="[SPACE]  Nochmal spielen", font_size=20, color="#ffff00"))
        self._ui_layer.add_object(Text("mn", cx-100, cy+105, 0,
            text="[M]  Hauptmenü", font_size=18, color="#888888"))

    def _build_win(self):
        self._clear_all()
        self._state = "win"
        self.scene.set_background("#001100")
        self.scene.default_camera.pos_x = SCREEN_WIDTH  // 2
        self.scene.default_camera.pos_y = SCREEN_HEIGHT // 2

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self._ui_layer.add_object(Text("win", cx-200, cy-80,  0,
            text="DU HAST GEWONNEN!", font_size=44, color="#00ff88"))
        self._ui_layer.add_object(Text("sc",  cx-120, cy-20,  0,
            text=f"Finaler Score:  {self._score}", font_size=22, color="#ffffff"))
        self._ui_layer.add_object(Text("re",  cx-130, cy+50,  0,
            text="[SPACE]  Nochmal spielen", font_size=20, color="#ffff00"))
        self._ui_layer.add_object(Text("mn",  cx-100, cy+85,  0,
            text="[M]  Hauptmenü", font_size=18, color="#888888"))

    # ──────────────────────────────────────────
    #  Wellen
    # ──────────────────────────────────────────
    def _spawn_wave(self, wave_index):
        cfg   = WAVES[min(wave_index, len(WAVES) - 1)]
        count = cfg["count"]
        speed = cfg["speed"]
        for i in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dist  = SPAWN_DISTANCE + random.randint(0, 200)
            ax = self._ship.pos_x + math.cos(angle) * dist
            ay = self._ship.pos_y + math.sin(angle) * dist
            a = Sprite(f"a_{self._uid()}_{i}", ax, ay, 0, collidable=True)
            a.add_animation("0", ["rsc/asteroid7"], False, 0)
            a.play_animation("0")
            a.object_var = {
                "speed_move": speed * random.uniform(0.7, 1.3),
                "speed_rot":  random.randint(1, 6),
            }
            a.object_group.append("astero")
            a.rotation = random.randint(0, 359)
            self._game_layer.add_object(a)
        self._wave_active = True

    # ──────────────────────────────────────────
    #  Update
    # ──────────────────────────────────────────
    def update(self):

        if self._state == "title":
            if self.scene.is_key_pressed("space"):
                self._build_game()
            return

        if self._state in ("gameover", "win"):
            if self.scene.is_key_pressed("space"):
                self._build_game()
            elif self.scene.is_key_pressed("m"):
                self._build_title()
            return

        if self._state != "playing":
            return

        # Wellen-Countdown
        if self._wave_countdown_active:
            if self._wave_timer.get_time() > self._countdown_end:
                self._wave_countdown_active = False
                self._txt_info.set_text("")
                self._wave_timer.reset()
                self._spawn_wave(self._wave_index)
            return

        layer = self._game_layer
        ship_alive = layer.get_object_by_name("ship") is not None

        # Asteroiden bewegen & Kollisionen
        asteroids_left = 0
        for obj in list(layer.objects):
            if "astero" not in obj.object_group:
                continue
            asteroids_left += 1
            obj.rotation += obj.object_var["speed_rot"]

            if ship_alive:
                obj.move_toward_position(
                    self._ship.pos_x, self._ship.pos_y,
                    obj.object_var["speed_move"]
                )
                if obj.check_collision(self._ship):
                    self._spawn_explosion(obj.pos_x, obj.pos_y)
                    layer.delete_objects("ship")
                    ship_alive = False

            for bullet in list(layer.objects):
                if "bullet" not in bullet.object_group:
                    continue
                if bullet.check_collision(obj):
                    self._spawn_explosion(bullet.pos_x, bullet.pos_y)
                    layer.delete_objects(bullet.name)
                    layer.delete_objects(obj.name)
                    self._score += POINTS_PER_ASTEROID
                    self._txt_score.set_text(f"Punkte: {self._score}")
                    asteroids_left -= 1
                    break

        # Welle abgeschlossen
        if self._wave_active and asteroids_left == 0:
            self._wave_active = False
            self._wave_index += 1
            if self._wave_index >= len(WAVES):
                self._build_win()
                return
            self._txt_wave.set_text(f"Welle: {self._wave_index + 1}")
            self._txt_info.set_text(f"Welle {self._wave_index + 1} beginnt ...")
            self._wave_countdown_active = True
            self._countdown_end = 2500
            self._wave_timer.reset()

        # Explosionen aufräumen
        for obj in list(layer.objects):
            if "explosion" in obj.object_group:
                if obj.current_frame == len(obj.current_animation["paths"]) - 1:
                    layer.delete_objects(obj.name)

        # Bullets bewegen
        for obj in list(layer.objects):
            if "bullet" in obj.object_group:
                obj.move_toward_angle(obj.object_var["rot"], BULLET_SPEED)

        # Schiff steuern
        if ship_alive:
            self._ship.move_toward_angle(self._ship.rotation, SHIP_SPEED)
            self._ship.rotate_toward_position(
                self.scene.mouse_x - layer.pos_x,
                self.scene.mouse_y - layer.pos_y,
                SHIP_ROTATION_SPEED
            )
            self.scene.default_camera.pos_x = self._ship.pos_x
            self.scene.default_camera.pos_y = self._ship.pos_y

            if (self.scene.is_key_pressed("space") and
                    self._shoot_timer.get_time() > SHOOT_COOLDOWN):
                b = Sprite(f"b_{self._uid()}", self._ship.pos_x, self._ship.pos_y,
                           0, collidable=True)
                b.add_animation("0", ["rsc/Bullet.png"], loop=False, time_between=0)
                b.object_var = {"rot": self._ship.rotation}
                b.object_group.append("bullet")
                b.play_animation("0")
                layer.add_object(b)
                self._shoot_timer.reset()
        else:
            self._build_game_over()


WaveSurvival()