import random
import math
import time

import pygame


FRAME_SIZE = 32
WALK_ROWS = {
    "down": 4,
    "up": 5,
    "right": 6,
    "left": 7,
    "down_left": 8,
    "down_right": 9,
    "up_right": 10,
    "up_left": 11,
}
REST_ROWS = {
    "sit": 0,
    "stand": 1,
    "sit2": 2,
    "lie": 3,
}
SLEEP_ROWS = {
    "sleep_1_left": 12,
    "sleep_1_right": 13,
    "sleep_2_left": 14,
    "sleep_2_right": 15,
    "sleep_3_left": 16,
    "sleep_3_right": 17,
    "sleep_4_left": 18,
    "sleep_4_right": 19,
}
ACTION_ROWS = {
    "meow": 28,
    "meow_sit": 28,
    "meow_stand": 29,
    "meow_sit2": 30,
    "meow_lie": 31,
    "yawn": 32,
    "yawn_sit": 32,
    "yawn_stand": 33,
    "yawn_sit2": 34,
    "yawn_lie": 35,
    "wash": 36,
    "wash_sit": 36,
    "wash_stand": 37,
    "wash_lie": 38,
    "scratch_left": 39,
    "scratch_right": 40,
    "hiss_left": 41,
    "hiss_right": 42,
    "dragged": 43,
    "paw_attack_down": 44,
    "paw_attack_up": 45,
    "paw_attack_left": 46,
    "paw_attack_right": 47,
    "paw_attack_down_right": 48,
    "paw_attack_down_left": 49,
    "paw_attack_up_right": 50,
    "paw_attack_up_left": 51,
    "hind_legs": 52,
}
PERSONALITY_PRESETS = {
    "lazy": {
        "rest_chance": 0.70,
        "idle_action_chance": 0.0,
        "rest_duration_seconds": (7, 22),
        "pause_seconds": (1.5, 5),
        "move_weights": (0.75, 0.20, 0.05),
        "speed_range": (0.8, 1.6),
    },
    "active": {
        "rest_chance": 0.30,
        "idle_action_chance": 0.0,
        "rest_duration_seconds": (3, 10),
        "pause_seconds": (0.2, 1.2),
        "move_weights": (0.35, 0.35, 0.30),
        "speed_range": (1.2, 2.4),
    },
}


def load_cat_frames(sheet_path, scale=3):
    sheet = pygame.image.load(str(sheet_path)).convert_alpha()
    scaled_size = max(1, round(FRAME_SIZE * scale))

    if sheet.get_width() < FRAME_SIZE or sheet.get_height() < FRAME_SIZE:
        raise ValueError("Cat sprite sheet is too small.")

    frames = {}
    for direction, row in WALK_ROWS.items():
        frames[direction] = load_row_frames(sheet, row, scaled_size)

    for rest_direction, row in REST_ROWS.items():
        frames[rest_direction] = load_row_frames(sheet, row, scaled_size)

    for sleep_key, row in SLEEP_ROWS.items():
        frames[sleep_key] = load_row_frames(sheet, row, scaled_size)

    for action_name, row in ACTION_ROWS.items():
        frames[action_name] = load_row_frames(sheet, row, scaled_size)

    return frames


def load_row_frames(sheet, row, scaled_size):
    frames = []
    column_count = sheet.get_width() // FRAME_SIZE

    for frame_index in range(column_count):
        rect = pygame.Rect(
            frame_index * FRAME_SIZE,
            row * FRAME_SIZE,
            FRAME_SIZE,
            FRAME_SIZE,
        )
        frame = sheet.subsurface(rect).copy()
        if pygame.mask.from_surface(frame).count() == 0:
            continue
        frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
        frames.append(frame)

    if not frames:
        raise ValueError(f"No visible frames found in row {row}.")

    return frames


class Cat:
    def __init__(
        self,
        window,
        frames,
        position,
        fps=60,
        follow_radius=260,
        follow_seconds=3,
    ):
        self.window = window
        self.frames = frames
        self.fps = fps
        self.follow_radius = follow_radius
        self.follow_duration_frames = round(fps * follow_seconds)
        self.follow_frames = 0
        self.scatter_cooldown_frames = 0
        self.follow_offset = pygame.Vector2(0, 0)
        self.rest_frames = 0
        self.rest_key = None
        self.rest_frame_index = 0
        self.rest_wash_check_frames = 0
        self.personality = None
        self.rest_chance = 0
        self.rest_duration_range = (0, 0)
        self.idle_action_chance = 0
        self.pause_duration_range = (0, 0)
        self.move_weights = (1, 0, 0)
        self.frames_until_yawn = random.randint(round(fps * 20), round(fps * 45))
        self.wander_frames = 0
        self.home_target = None
        self.home_sleeping = False
        self.home_sleep_key = None
        self.action_key = None
        self.action_frame_index = 0.0
        self.action_speed = 0.12
        self.sleep_action_speed = 0.02
        self.action_loops_remaining = 0
        self.resume_rest_after_action = False
        self.click_times = []
        self.click_limit = 5
        self.click_window_seconds = 2.5
        self.drag_started_at = 0
        self.drag_hiss_seconds = 3
        self.drag_hissed = False
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)
        self.position = pygame.Vector2(position)
        self.direction = "down"
        self.frame_index = 0.0
        self.animation_speed = 0.14
        self.speed_range = (0.8, 1.6)
        self.follow_speed_range = (2.1, 3.2)
        self.apply_personality("lazy")
        self.speed = random.uniform(*self.speed_range)
        self.follow_speed = random.uniform(*self.follow_speed_range)
        self.pause_frames = 0
        self.image = self.frames[self.direction][0]
        self.target_position = self.get_wander_target()
        if random.random() < self.rest_chance:
            self.start_resting()

    def update(self, mouse_position=None):
        if self.dragging:
            self.update_dragging_image()
            return

        if mouse_position is not None:
            mouse_position = pygame.Vector2(mouse_position)

        if self.follow_frames > 0:
            self.follow_mouse(mouse_position)
            return

        if self.action_key:
            self.play_action()
            return

        if self.home_target is not None and not self.home_sleeping:
            if self.move_toward(self.home_target, self.speed):
                self.position = self.home_target
                self.home_sleeping = True
                self.start_action(self.home_sleep_key, loops=-1, clear_states=False)
            return

        if self.scatter_cooldown_frames > 0:
            self.scatter_cooldown_frames -= 1
        elif mouse_position is not None and self.is_mouse_near(mouse_position):
            self.start_following(mouse_position)
            self.follow_mouse(mouse_position)
            return

        if self.rest_frames > 0:
            self.rest_frames -= 1
            if self.rest_frames <= 0:
                self.finish_resting()
                return
            if self.rest_wash_check_frames > 0:
                self.rest_wash_check_frames -= 1
            elif random.random() < 0.72:
                self.start_rest_wash()
                return
            else:
                self.schedule_next_rest_wash()
            self.show_rest_frame()
            return

        if self.pause_frames > 0:
            self.pause_frames -= 1
            self.show_pause_frame()
            if self.pause_frames == 0:
                self.rest_key = None
            return

        if self.should_do_hind_legs():
            self.start_action("hind_legs", loops=random.randint(1, 2))
            return

        if self.move_toward(self.target_position, self.speed):
            self.position = self.target_position
            self.speed = random.uniform(*self.speed_range)
            if self.wander_frames >= self.frames_until_yawn:
                self.start_action("yawn", loops=1)
                self.reset_yawn_timer()
            else:
                self.start_next_idle_state()
        else:
            self.wander_frames += 1

    def start_next_idle_state(self):
        roll = random.random()
        if roll < self.rest_chance:
            self.start_resting()
        elif roll < self.rest_chance + self.idle_action_chance:
            self.start_random_idle_action()
        else:
            self.start_wandering()

    def start_wandering(self):
        self.target_position = self.get_wander_target()
        self.pause_frames = random.randint(*self.pause_duration_range)

    def resume_after_drop(self):
        if random.random() < self.rest_chance:
            self.start_resting()
            return
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.action_key = None
        self.pause_frames = 0
        self.speed = random.uniform(*self.speed_range)
        self.target_position = self.get_wander_target()

    def reset_yawn_timer(self):
        self.wander_frames = 0
        self.frames_until_yawn = random.randint(round(self.fps * 20), round(self.fps * 45))

    def apply_personality(self, personality):
        preset = PERSONALITY_PRESETS.get(personality, PERSONALITY_PRESETS["lazy"])
        self.personality = personality if personality in PERSONALITY_PRESETS else "lazy"
        self.rest_chance = preset["rest_chance"]
        self.idle_action_chance = preset["idle_action_chance"]
        self.rest_duration_range = tuple(
            max(1, round(self.fps * seconds))
            for seconds in preset["rest_duration_seconds"]
        )
        self.pause_duration_range = tuple(
            max(1, round(self.fps * seconds))
            for seconds in preset["pause_seconds"]
        )
        self.move_weights = preset["move_weights"]
        self.speed_range = preset["speed_range"]

    def set_personality(self, personality):
        self.apply_personality(personality)
        self.speed = random.uniform(*self.speed_range)
        if self.dragging or self.home_target is not None or self.action_key:
            return
        if self.rest_frames > 0 and random.random() >= self.rest_chance:
            self.rest_frames = 0
            self.rest_key = None
            self.rest_wash_check_frames = 0
            self.start_wandering()
        elif self.rest_frames == 0 and self.pause_frames == 0:
            self.start_next_idle_state()

    def register_click(self):
        now = time.monotonic()
        self.click_times = [
            clicked_at
            for clicked_at in self.click_times
            if now - clicked_at <= self.click_window_seconds
        ]
        self.click_times.append(now)

        if len(self.click_times) >= self.click_limit:
            self.click_times.clear()
            self.start_hiss()
        else:
            self.start_meow()

    def go_home(self, target_position):
        self.clear_temporary_states(clear_home=False)
        self.home_target = self.get_clamped_position(pygame.Vector2(target_position))
        self.home_sleeping = False
        self.home_sleep_key = self.get_random_sleep_key()
        self.speed = random.uniform(1.4, 2.2)
        self.target_position = self.home_target

    def get_random_sleep_key(self):
        sleep_number = random.randint(1, 4)
        side = "left" if self.is_facing_left() else "right"
        return f"sleep_{sleep_number}_{side}"

    def draw(self):
        self.window.blit(self.image, self.position)

    def contains_point(self, point):
        return self.image.get_rect(topleft=self.position).collidepoint(point)

    def start_drag(self, mouse_position):
        mouse_position = pygame.Vector2(mouse_position)
        self.dragging = True
        self.drag_started_at = time.monotonic()
        self.drag_hissed = False
        self.drag_offset = mouse_position - self.position
        self.clear_temporary_states()
        self.target_position = self.position.copy()
        self.show_dragged_frame()

    def drag_to(self, mouse_position):
        if not self.dragging:
            return
        mouse_position = pygame.Vector2(mouse_position)
        self.position = self.get_clamped_position(mouse_position - self.drag_offset)
        self.target_position = self.position.copy()

    def end_drag(self, clicked=False):
        dragged_for = time.monotonic() - self.drag_started_at
        self.dragging = False
        if self.drag_hissed or dragged_for >= self.drag_hiss_seconds:
            self.start_hiss()
        elif clicked:
            self.register_click()
        else:
            self.target_position = self.position.copy()
            self.resume_after_drop()

    def get_random_position(self):
        max_x = max(0, self.window.get_width() - self.image.get_width())
        max_y = max(0, self.window.get_height() - self.image.get_height())
        return pygame.Vector2(
            random.randint(0, max_x),
            random.randint(0, max_y),
        )

    def get_nearby_random_position(self):
        return self.get_offset_random_position(60, 220)

    def get_medium_random_position(self):
        return self.get_offset_random_position(220, 520)

    def get_offset_random_position(self, min_distance, max_distance):
        angle = random.uniform(0, math.tau)
        distance = random.uniform(min_distance, max_distance)
        target = self.position + pygame.Vector2(
            math.cos(angle) * distance,
            math.sin(angle) * distance,
        )
        return self.get_clamped_position(target)

    def get_wander_target(self):
        movement = random.choices(
            ("near", "medium", "far"),
            weights=self.move_weights,
            k=1,
        )[0]
        if movement == "near":
            return self.get_nearby_random_position()
        if movement == "medium":
            return self.get_medium_random_position()
        return self.get_random_position()

    def get_clamped_position(self, position):
        max_x = max(0, self.window.get_width() - self.image.get_width())
        max_y = max(0, self.window.get_height() - self.image.get_height())
        return pygame.Vector2(
            min(max(position.x, 0), max_x),
            min(max(position.y, 0), max_y),
        )

    def get_center(self):
        return self.position + pygame.Vector2(
            self.image.get_width() / 2,
            self.image.get_height() / 2,
        )

    def is_mouse_near(self, mouse_position):
        return self.get_center().distance_to(mouse_position) <= self.follow_radius

    def start_following(self, mouse_position):
        angle = random.uniform(0, math.tau)
        offset_distance = random.uniform(25, 75)
        self.follow_offset = pygame.Vector2(
            math.cos(angle) * offset_distance,
            math.sin(angle) * offset_distance,
        )
        self.follow_frames = self.follow_duration_frames
        self.follow_speed = random.uniform(*self.follow_speed_range)
        self.pause_frames = 0
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.action_key = None
        self.resume_rest_after_action = False
        self.target_position = self.get_follow_target(mouse_position)

    def follow_mouse(self, mouse_position):
        self.follow_frames -= 1

        if mouse_position is not None and self.follow_frames > 0:
            self.target_position = self.get_follow_target(mouse_position)
            self.move_toward(self.target_position, self.follow_speed)
            return

        self.scatter_from(mouse_position)

    def get_follow_target(self, mouse_position):
        image_center = pygame.Vector2(
            self.image.get_width() / 2,
            self.image.get_height() / 2,
        )
        return self.get_clamped_position(mouse_position - image_center + self.follow_offset)

    def scatter_from(self, mouse_position):
        if mouse_position is None:
            self.target_position = self.get_random_position()
        else:
            angle = random.uniform(0, math.tau)
            distance = random.uniform(180, 520)
            image_center = pygame.Vector2(
                self.image.get_width() / 2,
                self.image.get_height() / 2,
            )
            target_center = mouse_position + pygame.Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance,
            )
            self.target_position = self.get_clamped_position(target_center - image_center)

        self.speed = random.uniform(1.5, 2.5)
        self.pause_frames = 0
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.action_key = None
        self.resume_rest_after_action = False
        self.scatter_cooldown_frames = round(self.fps * 1.5)

    def move_toward(self, target_position, speed):
        direction_to_target = target_position - self.position
        distance_to_target = direction_to_target.length()

        if distance_to_target <= speed:
            self.position = target_position
            return True

        step = direction_to_target.normalize() * speed
        self.position += step
        self.direction = self.get_direction_from_step(step)
        self.play_walk_animation()
        return False

    def start_resting(self):
        self.action_key = None
        self.resume_rest_after_action = False
        self.rest_frames = random.randint(*self.rest_duration_range)
        self.rest_key = self.get_random_rest_key()
        self.rest_frame_index = random.randrange(len(self.frames[self.rest_key]))
        self.schedule_next_rest_wash()
        self.pause_frames = 0
        self.show_rest_frame()

    def finish_resting(self):
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.start_next_idle_state()

    def get_random_rest_key(self):
        return random.choices(
            ("sit", "sit2", "lie", "stand"),
            weights=(0.38, 0.27, 0.30, 0.05),
            k=1,
        )[0]

    def show_rest_frame(self):
        if self.rest_key is None:
            self.rest_key = self.get_random_rest_key()
            self.rest_frame_index = random.randrange(len(self.frames[self.rest_key]))
        rest_frames = self.frames[self.rest_key]
        self.image = rest_frames[int(self.rest_frame_index)]

    def show_pause_frame(self):
        if self.rest_key is None:
            self.rest_key = self.get_random_rest_key()
            self.rest_frame_index = random.randrange(len(self.frames[self.rest_key]))
        self.show_rest_frame()

    def schedule_next_rest_wash(self):
        self.rest_wash_check_frames = random.randint(round(self.fps * 3), round(self.fps * 7))

    def start_rest_wash(self):
        self.schedule_next_rest_wash()
        self.start_action(
            self.get_wash_key_for_pose(),
            loops=self.get_wash_loop_count(),
            clear_states=False,
        )
        self.resume_rest_after_action = True

    def start_meow(self):
        self.start_action(self.get_meow_key_for_pose(), loops=1)

    def get_meow_key_for_pose(self):
        if self.rest_key == "stand":
            return "meow_stand"
        if self.rest_key == "sit2":
            return "meow_sit2"
        if self.rest_key == "lie":
            return "meow_lie"
        if self.rest_key == "sit":
            return "meow_sit"
        return random.choice(("meow_sit", "meow_stand", "meow_sit2", "meow_lie"))

    def start_random_idle_action(self):
        action_key = random.choices(
            (
                self.get_wash_key_for_pose(),
                self.get_scratch_key(),
                self.get_paw_attack_key(),
                "hind_legs",
            ),
            weights=(0.58, 0.18, 0.12, 0.12),
            k=1,
        )[0]
        self.start_action(action_key, loops=self.get_idle_action_loop_count(action_key))

    def get_idle_action_loop_count(self, action_key):
        if action_key.startswith("wash"):
            return self.get_wash_loop_count()
        if action_key == "hind_legs":
            return random.randint(1, 2)
        return 1

    def get_wash_loop_count(self):
        return random.randint(1, 3)

    def get_wash_key_for_pose(self):
        if self.rest_key == "stand":
            return "wash_stand"
        if self.rest_key == "lie":
            return "wash_lie"
        if self.rest_key in ("sit", "sit2"):
            return "wash_sit"
        return random.choices(
            ("wash_sit", "wash_lie", "wash_stand"),
            weights=(0.46, 0.42, 0.12),
            k=1,
        )[0]

    def get_scratch_key(self):
        return "scratch_left" if self.is_facing_left() else "scratch_right"

    def start_hiss(self):
        self.start_action(self.get_hiss_key(), loops=random.randint(2, 3))

    def get_hiss_key(self):
        return "hiss_left" if self.is_facing_left() else "hiss_right"

    def get_paw_attack_key(self):
        return f"paw_attack_{self.direction}"

    def should_do_hind_legs(self):
        return (
            "hind_legs" in self.frames
            and self.frames["hind_legs"]
            and random.random() < 1 / max(1, self.fps * 55)
        )

    def start_action(self, action_key, loops=1, clear_states=True):
        if action_key not in self.frames or not self.frames[action_key]:
            return
        if clear_states:
            self.clear_temporary_states()
        self.action_key = action_key
        self.action_frame_index = 0.0
        self.action_loops_remaining = loops if loops < 0 else max(1, loops)
        self.image = self.frames[self.action_key][0]

    def get_action_speed(self, action_key):
        return self.sleep_action_speed if action_key.startswith("sleep_") else self.action_speed

    def play_action(self):
        action_frames = self.frames[self.action_key]
        self.action_frame_index += self.get_action_speed(self.action_key)

        if self.action_frame_index >= len(action_frames):
            if self.action_loops_remaining > 0:
                self.action_loops_remaining -= 1
            if self.action_loops_remaining == 0:
                self.action_key = None
                self.action_frame_index = 0.0
                if self.home_sleeping:
                    self.start_action(self.home_sleep_key, loops=-1, clear_states=False)
                elif self.resume_rest_after_action and self.rest_frames > 0:
                    self.resume_rest_after_action = False
                    self.show_rest_frame()
                else:
                    self.start_next_idle_state()
                return
            self.action_frame_index = 0.0

        self.image = action_frames[int(self.action_frame_index)]

    def update_dragging_image(self):
        if time.monotonic() - self.drag_started_at >= self.drag_hiss_seconds:
            self.drag_hissed = True
            self.show_looping_action(self.get_hiss_key())
        else:
            self.show_dragged_frame()

    def show_dragged_frame(self):
        self.image = self.frames["dragged"][0]

    def show_looping_action(self, action_key):
        action_frames = self.frames[action_key]
        self.action_frame_index += self.action_speed
        if self.action_frame_index >= len(action_frames):
            self.action_frame_index = 0.0
        self.image = action_frames[int(self.action_frame_index)]

    def clear_temporary_states(self, clear_home=True):
        self.follow_frames = 0
        self.scatter_cooldown_frames = 0
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.action_key = None
        self.resume_rest_after_action = False
        self.pause_frames = 0
        if clear_home:
            self.home_target = None
            self.home_sleeping = False
            self.home_sleep_key = None

    def play_walk_animation(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames[self.direction]):
            self.frame_index = 0
        self.image = self.frames[self.direction][int(self.frame_index)]

    def is_facing_left(self):
        return self.direction in ("left", "down_left", "up_left")

    @staticmethod
    def get_direction_from_step(step):
        abs_x = abs(step.x)
        abs_y = abs(step.y)

        if abs_x > abs_y * 1.8:
            return "right" if step.x > 0 else "left"
        if abs_y > abs_x * 1.8:
            return "down" if step.y > 0 else "up"
        if step.x > 0 and step.y > 0:
            return "down_right"
        if step.x < 0 and step.y > 0:
            return "down_left"
        if step.x > 0 and step.y < 0:
            return "up_right"
        if step.x < 0 and step.y < 0:
            return "up_left"
        return "down" if step.y > 0 else "up"
