import random
from gdpython import Game, Scene, Layer, Sprite, Text, Sound, Music, Timer


class TheGame(Game):

    scene: Scene

    def start(self):

        self.music = Music("rsc/egame/Dungeon-Crawler.wav", 0.2)
        self.music.play()

        self.background_layer = Layer("background", 0, 0, -1)
        self.scene.add_layer(self.background_layer)
        self.ui = Layer("ui", 0, 0, 2)
        self.scene.add_layer(self.ui)

        self.health_display = []
        self.player_max_health = 3
        self.player_health = 3
        self.health_is_decimal = False
        self.update_hearts()
        self.alive = True

        self.swing_sound = Sound("swing", "rsc/egame/swing.wav", volume=0.2)
        self.oof = Sound("oof", "rsc/egame/oof.wav", volume=0.2)
        self.urgh = Sound("urgh", "rsc/egame/urgh.wav", volume=0.2)

        self.char = Sprite("char", 0, 0, 0, collidable=True,
                           hitbox_offset_x=30, hitbox_offset_y=30,
                           hitbox_width=4, hitbox_height=8)
        self.scene.default_layer.add_object(self.char)

        char_animations = {
            "idle": (["idle_0", "idle_1", "idle_2", "idle_3"], True, 150),
            "move_up": (["walk_up_0", "walk_up_1", "walk_up_2", "walk_up_3", "walk_up_4", "walk_up_5"], True, 150),
            "move_down": (["walk_down_0", "walk_down_1", "walk_down_2", "walk_down_3", "walk_down_4", "walk_down_5"], True, 150),
            "move_left": (["walk_left_0", "walk_left_1", "walk_left_2", "walk_left_3", "walk_left_4", "walk_left_5"], True, 150),
            "move_right": (["walk_right_0", "walk_right_1", "walk_right_2", "walk_right_3", "walk_right_4", "walk_right_5"], True, 150),
            "attack_up": (["pierce_up_0", "pierce_up_1", "pierce_up_2", "pierce_up_3", "pierce_up_4", "pierce_up_5", "pierce_up_6", "pierce_up_7"], False, 50),
            "attack_down": (["pierce_down_0", "pierce_down_1", "pierce_down_2", "pierce_down_3", "pierce_down_4", "pierce_down_5", "pierce_down_6", "pierce_down_7"], False, 50),
            "attack_left": (["pierce_left_0", "pierce_left_1", "pierce_left_2", "pierce_left_3", "pierce_left_4", "pierce_left_5", "pierce_left_6", "pierce_left_7"], False, 50),
            "attack_right": (["pierce_right_0", "pierce_right_1", "pierce_right_2", "pierce_right_3", "pierce_right_4", "pierce_right_5", "pierce_right_6", "pierce_right_7"], False, 50),
            "death": (["death_0", "death_1", "death_2", "death_3", "death_4", "death_5", "death_6", "death_7"], False, 150),
        }

        for anim_name, (frames, loop, time_b) in char_animations.items():
            self.char.add_animation(anim_name, [f"rsc/egame/{f}.png" for f in frames], loop=loop, time_between=time_b)

        self.char.play_animation("idle")

        for i in range(5):
            mob = Sprite(f"mob_{i}", 0, 0, 0, collidable=True)
            mob.add_animation("mob", ["rsc/egame/ghost.png"], False)
            while mob.get_distance_to_position(self.char.pos_x, self.char.pos_y) < 300:
                mob.pos_x = random.randint(-400, 400)
                mob.pos_y = random.randint(-400, 400)
            mob.object_group.append("mob")
            mob.play_animation("mob")
            self.scene.default_layer.add_object(mob)

        self.attack_box = Sprite("atk_box", 0, 0, 0, collidable=True, hitbox_offset_y=5,
                                 hitbox_width=5, hitbox_height=5)
        self.attack_box_in_scene = False

        self.atk_offset_x = 0
        self.atk_offset_y = 0

        self.scene_timer = Timer()
        self.scene_timer.start()
        self.dmg_time = 0
        self.atk_time = 0

        self.attacking = False

        self.directions = {
            "move_up": False,
            "move_down": False,
            "move_left": False,
            "move_right": False
        }

        self.game_over_text = Text("game_over", 0, 300, 1, "YOU DIED", "Georgia", 100, "#a80707")

    def update_hearts(self):
        for heart in self.health_display:
            self.ui.delete_objects(heart.name)
        self.health_display.clear()

        start_x = 30
        full_hearts = int(self.player_health)
        self.health_is_decimal = self.player_health % 1 != 0
        empty_hearts = self.player_max_health - full_hearts - (1 if self.health_is_decimal else 0)

        for i in range(full_hearts):
            h = Sprite(f"fullHeart{i}", start_x, 50, 0)
            h.add_animation("fH", ["rsc/egame/full_heart.png"], loop=False, time_between=0)
            h.play_animation("fH")
            self.health_display.append(h)
            start_x += 20

        if self.health_is_decimal:
            h = Sprite("halfHeart", start_x, 50, 0)
            h.add_animation("hH", ["rsc/egame/half_heart.png"], False, 0)
            h.play_animation("hH")
            self.health_display.append(h)
            start_x += 20

        for i in range(empty_hearts):
            h = Sprite(f"emptyHeart{i}", start_x, 50, 0)
            h.add_animation("eH", ["rsc/egame/empty_heart.png"], False, 0)
            h.play_animation("eH")
            self.health_display.append(h)
            start_x += 20

        for heart in self.health_display:
            self.ui.add_object(heart)

    def all_false(self):
        for key in self.directions:
            self.directions[key] = False

    def _current_move_animation(self):
        for direction in self.directions:
            if self.directions[direction]:
                return direction
        return None

    def _char_hitbox_center_x(self):
        return self.char.pos_x + self.char.hitbox_offset_x + self.char.hitbox_width / 2

    def _char_hitbox_center_y(self):
        return self.char.pos_y + self.char.hitbox_offset_y + self.char.hitbox_height / 2

    def update(self):
        if not self.alive:
            return

        current_time = self.scene_timer.get_time()

        if self.attacking:
            self.attack_box.pos_x = self._char_hitbox_center_x() + self.atk_offset_x - self.attack_box.hitbox_width / 2
            self.attack_box.pos_y = self._char_hitbox_center_y() + self.atk_offset_y - self.attack_box.hitbox_height / 2

            for mob in list(self.scene.default_layer.objects):
                if "mob" in mob.object_group and mob.check_collision(self.attack_box):
                    self.scene.default_layer.delete_objects(mob.name)

            if self.char.animation_finished:
                self.attacking = False
                self.attack_box_in_scene = False
                self.scene.default_layer.delete_objects("atk_box")

        for mob in list(self.scene.default_layer.objects):
            if "mob" not in mob.object_group:
                continue
            if not self.alive:
                break

            mob.move_toward_position(
                self._char_hitbox_center_x(),
                self._char_hitbox_center_y(),
                0.4
            )

            if mob.check_collision(self.char) and current_time - self.dmg_time >= 1000:
                self.player_health -= 0.5
                self.dmg_time = current_time
                if self.player_health <= 0:
                    self.player_health = 0
                    self.update_hearts()
                    self.urgh.play()
                    self.music.stop()
                    self.music = Music("rsc/egame/down.wav", 0.2)
                    self.music.play()
                    self.alive = False
                    self.char.play_animation("death")
                    self.ui.add_object(self.game_over_text)
                    break
                else:
                    self.update_hearts()
                    self.oof.play()

        self._handle_movement()
        self._handle_attack(current_time)

    def _handle_movement(self):
        moving = False

        if self.scene.is_key_pressed("w"):
            moving = True
            if self.scene.is_key_pressed("a"):
                if not self.directions["move_left"]:
                    self.all_false()
                    self.directions["move_left"] = True
                    if not self.attacking:
                        self.char.play_animation("move_left")
                self.char.move_toward_angle(225, 2)
            elif self.scene.is_key_pressed("d"):
                if not self.directions["move_right"]:
                    self.all_false()
                    self.directions["move_right"] = True
                    if not self.attacking:
                        self.char.play_animation("move_right")
                self.char.move_toward_angle(315, 2)
            else:
                if not self.directions["move_up"]:
                    self.all_false()
                    self.directions["move_up"] = True
                    if not self.attacking:
                        self.char.play_animation("move_up")
                self.char.move_toward_angle(270, 2)
        elif self.scene.is_key_pressed("s"):
            moving = True
            if self.scene.is_key_pressed("a"):
                if not self.directions["move_left"]:
                    self.all_false()
                    self.directions["move_left"] = True
                    if not self.attacking:
                        self.char.play_animation("move_left")
                self.char.move_toward_angle(135, 2)
            elif self.scene.is_key_pressed("d"):
                if not self.directions["move_right"]:
                    self.all_false()
                    self.directions["move_right"] = True
                    if not self.attacking:
                        self.char.play_animation("move_right")
                self.char.move_toward_angle(45, 2)
            else:
                if not self.directions["move_down"]:
                    self.all_false()
                    self.directions["move_down"] = True
                    if not self.attacking:
                        self.char.play_animation("move_down")
                self.char.move_toward_angle(90, 2)
        elif self.scene.is_key_pressed("a"):
            moving = True
            if not self.directions["move_left"]:
                self.all_false()
                self.directions["move_left"] = True
                if not self.attacking:
                    self.char.play_animation("move_left")
            self.char.move_toward_angle(180, 2)
        elif self.scene.is_key_pressed("d"):
            moving = True
            if not self.directions["move_right"]:
                self.all_false()
                self.directions["move_right"] = True
                if not self.attacking:
                    self.char.play_animation("move_right")
            self.char.move_toward_angle(0, 2)

        if not self.attacking and not moving and any(self.directions.values()):
            self.all_false()
            self.char.play_animation("idle")

        if not self.attacking and moving:
            active = self._current_move_animation()
            if active and not self.char.current_animation == self.char.animations.get(active):
                self.char.play_animation(active)

    def _handle_attack(self, current_time):
        if not self.scene.is_key_pressed("left"):
            return
        if current_time - self.atk_time < 500:
            return
        if self.attacking:
            return

        self.atk_time = current_time
        self.atk_offset_x = 0
        self.atk_offset_y = 0

        if self.scene.is_key_pressed("w"):
            self.char.play_animation("attack_up")
            self.atk_offset_y = -24
        elif self.scene.is_key_pressed("s"):
            self.char.play_animation("attack_down")
            self.atk_offset_y = 24
        elif self.scene.is_key_pressed("a"):
            self.char.play_animation("attack_left")
            self.atk_offset_x = -24
        elif self.scene.is_key_pressed("d"):
            self.char.play_animation("attack_right")
            self.atk_offset_x = 24
        else:
            self.char.play_animation("idle")
            return

        self.attacking = True
        self.swing_sound.play()

        self.attack_box.pos_x = self._char_hitbox_center_x() + self.atk_offset_x - self.attack_box.hitbox_width / 2
        self.attack_box.pos_y = self._char_hitbox_center_y() + self.atk_offset_y - self.attack_box.hitbox_height / 2

        if not self.attack_box_in_scene:
            self.scene.default_layer.add_object(self.attack_box)
            self.attack_box_in_scene = True


TheGame()