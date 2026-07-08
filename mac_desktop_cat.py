from pathlib import Path
import math
import random
import tempfile
import time

import AppKit
import Foundation
import Quartz
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
CLICK_DRAG_THRESHOLD = 6
PET_BACK_WINDOW_LEVEL = Quartz.CGWindowLevelForKey(Quartz.kCGNormalWindowLevelKey) - 1
PET_FRONT_WINDOW_LEVEL = Quartz.CGWindowLevelForKey(Quartz.kCGScreenSaverWindowLevelKey)
PET_WINDOW_LEVEL = PET_BACK_WINDOW_LEVEL
BED_SCALE_MULTIPLIER = 1.5
BED_SLEEP_WIDTH_RATIO = 0.84


def window_level_for_layer(layer):
    return PET_FRONT_WINDOW_LEVEL if layer == "front" else PET_BACK_WINDOW_LEVEL


def get_visible_screen_frames():
    screens = list(AppKit.NSScreen.screens() or [])
    if not screens:
        screens = [AppKit.NSScreen.mainScreen()]
    return [screen.visibleFrame() for screen in screens if screen is not None]


def get_largest_screen_size(screen_frames):
    screen_frame = max(
        screen_frames,
        key=lambda frame: frame.size.width * frame.size.height,
    )
    return screen_frame.size.width, screen_frame.size.height


def get_screen_frames_signature(screen_frames):
    return tuple(
        sorted(
            (
                frame.origin.x,
                frame.origin.y,
                frame.size.width,
                frame.size.height,
            )
            for frame in screen_frames
        )
    )


def get_window_position_bounds(screen_frames, width, height):
    bounds = []
    for frame in screen_frames:
        min_x = frame.origin.x
        min_y = frame.origin.y
        max_x = frame.origin.x + max(0, frame.size.width - width)
        max_y = frame.origin.y + max(0, frame.size.height - height)
        bounds.append((min_x, min_y, max_x, max_y))
    return bounds


def get_union_bounds(position_bounds):
    return (
        min(bound[0] for bound in position_bounds),
        min(bound[1] for bound in position_bounds),
        max(bound[2] for bound in position_bounds),
        max(bound[3] for bound in position_bounds),
    )


def get_random_position_in_bounds(position_bounds):
    weights = [
        max(1, (bound[2] - bound[0] + 1) * (bound[3] - bound[1] + 1))
        for bound in position_bounds
    ]
    min_x, min_y, max_x, max_y = random.choices(
        position_bounds,
        weights=weights,
        k=1,
    )[0]
    return random.uniform(min_x, max_x), random.uniform(min_y, max_y)


def get_clamped_position_in_bounds(x, y, position_bounds):
    best_position = None
    best_distance = None

    for min_x, min_y, max_x, max_y in position_bounds:
        clamped_x = min(max(x, min_x), max_x)
        clamped_y = min(max(y, min_y), max_y)
        distance = (x - clamped_x) ** 2 + (y - clamped_y) ** 2
        if best_distance is None or distance < best_distance:
            best_position = (clamped_x, clamped_y)
            best_distance = distance

    return best_position


def get_screen_frame_containing_point(screen_frames, point_x, point_y):
    best_frame = None
    best_distance = None

    for frame in screen_frames:
        min_x = frame.origin.x
        min_y = frame.origin.y
        max_x = frame.origin.x + frame.size.width
        max_y = frame.origin.y + frame.size.height
        clamped_x = min(max(point_x, min_x), max_x)
        clamped_y = min(max(point_y, min_y), max_y)
        distance = (point_x - clamped_x) ** 2 + (point_y - clamped_y) ** 2
        if distance == 0:
            return frame
        if best_distance is None or distance < best_distance:
            best_frame = frame
            best_distance = distance

    return best_frame or screen_frames[0]


def run_mac_desktop_cat(
    sprite_sheets,
    bed_image,
    menu_icon,
    scale=3,
    max_scale=2.7,
    cat_count=1,
    reference_screen=(1440, 900),
    fps=60,
):
    sprite_sheets = [Path(sprite_sheet) for sprite_sheet in sprite_sheets]
    bed_image = Path(bed_image)
    menu_icon = Path(menu_icon)

    with tempfile.TemporaryDirectory(prefix="desktop-cat-") as frame_dir:
        frame_cache = {}
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        app.finishLaunching()
        screen_frames = get_visible_screen_frames()
        screen_width, screen_height = get_largest_screen_size(screen_frames)
        cat_scale = get_responsive_cat_scale(
            screen_width,
            screen_height,
            scale,
            max_scale,
            reference_screen,
        )

        desktop_cats = []
        for index in range(max(1, cat_count)):
            sprite_sheet = sprite_sheets[index % len(sprite_sheets)]
            if sprite_sheet not in frame_cache:
                frame_cache[sprite_sheet] = load_nsimage_frames(
                    sprite_sheet,
                    Path(frame_dir),
                    cat_scale,
                )
            desktop_cat = DesktopCat(
                frame_cache[sprite_sheet],
                fps,
                screen_frames,
            )
            desktop_cat.show()
            desktop_cats.append(desktop_cat)

        cat_bed = CatBedWindow(bed_image, cat_scale, screen_frames)
        menu_controller, status_item = create_status_menu(
            menu_icon,
            cat_bed,
            desktop_cats,
            fps,
        )

        try:
            run_desktop_cats(app, desktop_cats, cat_bed, fps)
        except KeyboardInterrupt:
            pass
        finally:
            for desktop_cat in desktop_cats:
                desktop_cat.close()
            cat_bed.close()


def load_nsimage_frames(sheet_path, frame_dir, scale):
    sheet = pygame.image.load(str(sheet_path))
    scaled_size = max(1, round(FRAME_SIZE * scale))
    sheet_name = Path(sheet_path).stem

    if sheet.get_width() < FRAME_SIZE or sheet.get_height() < FRAME_SIZE:
        raise ValueError("Cat sprite sheet is too small.")

    surfaces = {}
    for direction, row in WALK_ROWS.items():
        surfaces[direction] = load_row_surfaces(sheet, row, scaled_size)

    for rest_direction, row in REST_ROWS.items():
        surfaces[rest_direction] = load_row_surfaces(sheet, row, scaled_size)

    for sleep_key, row in SLEEP_ROWS.items():
        surfaces[sleep_key] = load_row_surfaces(sheet, row, scaled_size)

    for action_name, row in ACTION_ROWS.items():
        surfaces[action_name] = load_row_surfaces(sheet, row, scaled_size)

    images = {}
    for direction, direction_frames in surfaces.items():
        images[direction] = []
        for frame_index, frame in enumerate(direction_frames):
            path = frame_dir / f"{sheet_name}_{direction}_{frame_index}.png"
            pygame.image.save(frame, str(path))
            image = AppKit.NSImage.alloc().initWithContentsOfFile_(str(path))
            images[direction].append(image)

    return images


def load_row_surfaces(sheet, row, scaled_size):
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


class DesktopCat:
    def __init__(self, frames, fps, screen_frames=None):
        self.frames = frames
        self.fps = fps
        self.follow_duration_frames = round(fps * 3)
        self.follow_frames = 0
        self.scatter_cooldown_frames = 0
        self.follow_offset_x = 0
        self.follow_offset_y = 0
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
        self.dragging = False
        self.drag_started_at = 0
        self.drag_hiss_seconds = 3
        self.drag_hissed = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
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
        self.width = int(self.image.size().width)
        self.height = int(self.image.size().height)
        self.layer = "back"
        self.set_screen_frames(screen_frames or get_visible_screen_frames())
        self.x, self.y = self.get_random_position()
        self.target_x, self.target_y = self.get_wander_target()
        if random.random() < self.rest_chance:
            self.start_resting()

        rect = AppKit.NSMakeRect(self.x, self.y, self.width, self.height)
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setHasShadow_(False)
        self.window.setIgnoresMouseEvents_(False)
        self.window.setLevel_(window_level_for_layer(self.layer))
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorStationary
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        self.image_view = AppKit.NSImageView.alloc().initWithFrame_(
            AppKit.NSMakeRect(0, 0, self.width, self.height)
        )
        self.image_view.setImageScaling_(AppKit.NSImageScaleAxesIndependently)
        self.image_view.setImage_(self.image)
        self.window.setContentView_(self.image_view)

    def show(self):
        self.order_for_layer()

    def close(self):
        self.window.close()

    def set_layer(self, layer):
        self.layer = layer if layer == "front" else "back"
        self.window.setLevel_(window_level_for_layer(self.layer))
        self.order_for_layer()

    def order_for_layer(self):
        if self.layer == "front":
            self.window.orderFrontRegardless()
        else:
            self.window.orderFront_(None)

    def set_screen_frames(self, screen_frames):
        screen_signature = get_screen_frames_signature(screen_frames)
        if getattr(self, "screen_signature", None) == screen_signature:
            return

        self.screen_signature = screen_signature
        self.screen_frames = screen_frames
        self.position_bounds = get_window_position_bounds(
            self.screen_frames,
            self.width,
            self.height,
        )
        self.min_x, self.min_y, self.max_x, self.max_y = get_union_bounds(
            self.position_bounds
        )

        if hasattr(self, "x"):
            self.x, self.y = self.get_clamped_position(self.x, self.y)
        if hasattr(self, "target_x"):
            self.target_x, self.target_y = self.get_clamped_position(
                self.target_x,
                self.target_y,
            )
        if self.home_target is not None:
            self.home_target = self.get_clamped_position(*self.home_target)

    @staticmethod
    def process_events(app, desktop_cats, cat_bed):
        while True:
            event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                AppKit.NSEventMaskAny,
                Foundation.NSDate.dateWithTimeIntervalSinceNow_(0),
                AppKit.NSDefaultRunLoopMode,
                True,
            )
            if event is None:
                break
            if DesktopCat.handle_mouse_event(event, desktop_cats, cat_bed):
                continue
            app.sendEvent_(event)

    @staticmethod
    def handle_mouse_event(event, desktop_cats, cat_bed):
        event_type = event.type()
        if event_type not in (
            AppKit.NSLeftMouseDown,
            AppKit.NSLeftMouseDragged,
            AppKit.NSLeftMouseUp,
        ):
            return False

        mouse_position = AppKit.NSEvent.mouseLocation()
        event_window = event.window()
        active_cat = next((cat for cat in desktop_cats if cat.dragging), None)

        if event_type == AppKit.NSLeftMouseDown:
            for cat in reversed(desktop_cats):
                if cat.window == event_window:
                    desktop_cats.remove(cat)
                    desktop_cats.append(cat)
                    cat.order_for_layer()
                    cat.start_drag(mouse_position.x, mouse_position.y)
                    return True
            return False

        if active_cat is None:
            return False

        if event_type == AppKit.NSLeftMouseDragged:
            active_cat.drag_to(mouse_position.x, mouse_position.y)
            return True

        active_cat.end_drag(mouse_position.x, mouse_position.y, cat_bed)
        return True

    def update(self, mouse_position=None):
        if self.dragging:
            self.update_dragging_image()
            return

        if self.follow_frames > 0:
            self.follow_mouse(mouse_position)
            return

        if self.scatter_cooldown_frames > 0:
            self.scatter_cooldown_frames -= 1
        elif mouse_position is not None and self.is_mouse_near(mouse_position):
            self.start_following(mouse_position)
            self.follow_mouse(mouse_position)
            return

        if self.action_key:
            self.play_action()
            return

        if self.home_target is not None and not self.home_sleeping:
            target_x, target_y = self.home_target
            if self.move_toward(target_x, target_y, self.speed):
                self.x = target_x
                self.y = target_y
                self.home_sleeping = True
                self.start_action(self.home_sleep_key, loops=-1, clear_states=False)
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

        if self.move_toward(self.target_x, self.target_y, self.speed):
            self.x = self.target_x
            self.y = self.target_y
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

    def reset_yawn_timer(self):
        self.wander_frames = 0
        self.frames_until_yawn = random.randint(round(self.fps * 20), round(self.fps * 45))

    def start_wandering(self):
        self.target_x, self.target_y = self.get_wander_target()
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
        self.target_x, self.target_y = self.get_wander_target()

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

    def go_home(self, target_x, target_y):
        self.clear_temporary_states(clear_home=False)
        self.home_target = self.get_clamped_position(target_x, target_y)
        self.home_sleeping = False
        self.home_sleep_key = self.get_random_sleep_key()
        self.speed = random.uniform(1.4, 2.2)
        self.target_x, self.target_y = self.home_target

    def sleep_at(self, target_x, target_y):
        self.clear_temporary_states(clear_home=False)
        self.x, self.y = self.get_clamped_position(target_x, target_y)
        self.home_target = (self.x, self.y)
        self.home_sleeping = True
        self.home_sleep_key = self.get_random_sleep_key()
        self.target_x, self.target_y = self.home_target
        self.start_action(self.home_sleep_key, loops=-1, clear_states=False)

    def get_random_sleep_key(self):
        sleep_number = random.randint(1, 4)
        side = "left" if self.is_facing_left() else "right"
        return f"sleep_{sleep_number}_{side}"

    def is_using_home(self):
        return self.home_target is not None or self.home_sleeping

    def draw(self):
        self.image_view.setImage_(self.image)
        self.window.setFrameOrigin_(AppKit.NSMakePoint(self.x, self.y))

    def get_random_position(self):
        return get_random_position_in_bounds(self.position_bounds)

    def get_nearby_random_position(self):
        return self.get_offset_random_position(60, 220)

    def get_medium_random_position(self):
        return self.get_offset_random_position(220, 520)

    def get_offset_random_position(self, min_distance, max_distance):
        angle = random.uniform(0, math.tau)
        distance = random.uniform(min_distance, max_distance)
        return self.get_clamped_position(
            self.x + math.cos(angle) * distance,
            self.y + math.sin(angle) * distance,
        )

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

    def get_clamped_position(self, x, y):
        return get_clamped_position_in_bounds(x, y, self.position_bounds)

    def get_center(self):
        return (
            self.x + self.width / 2,
            self.y + self.height / 2,
        )

    def is_mouse_near(self, mouse_position):
        center_x, center_y = self.get_center()
        mouse_x, mouse_y = mouse_position
        return math.hypot(center_x - mouse_x, center_y - mouse_y) <= self.follow_radius

    def start_following(self, mouse_position):
        angle = random.uniform(0, math.tau)
        offset_distance = random.uniform(25, 75)
        self.follow_offset_x = math.cos(angle) * offset_distance
        self.follow_offset_y = math.sin(angle) * offset_distance
        self.follow_frames = self.follow_duration_frames
        self.follow_speed = random.uniform(*self.follow_speed_range)
        self.pause_frames = 0
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.resume_rest_after_action = False
        self.target_x, self.target_y = self.get_follow_target(mouse_position)

    def follow_mouse(self, mouse_position):
        self.follow_frames -= 1

        if mouse_position is not None and self.follow_frames > 0:
            self.target_x, self.target_y = self.get_follow_target(mouse_position)
            self.move_toward(self.target_x, self.target_y, self.follow_speed)
            return

        self.scatter_from(mouse_position)

    def get_follow_target(self, mouse_position):
        mouse_x, mouse_y = mouse_position
        return self.get_clamped_position(
            mouse_x - self.width / 2 + self.follow_offset_x,
            mouse_y - self.height / 2 + self.follow_offset_y,
        )

    def scatter_from(self, mouse_position):
        if mouse_position is None:
            self.target_x, self.target_y = self.get_random_position()
        else:
            mouse_x, mouse_y = mouse_position
            angle = random.uniform(0, math.tau)
            distance = random.uniform(180, 520)
            self.target_x, self.target_y = self.get_clamped_position(
                mouse_x + math.cos(angle) * distance - self.width / 2,
                mouse_y + math.sin(angle) * distance - self.height / 2,
            )

        self.speed = random.uniform(1.5, 2.5)
        self.pause_frames = 0
        self.rest_frames = 0
        self.rest_key = None
        self.rest_wash_check_frames = 0
        self.action_key = None
        self.resume_rest_after_action = False
        self.scatter_cooldown_frames = round(self.fps * 1.5)

    def move_toward(self, target_x, target_y, speed):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= speed:
            self.x = target_x
            self.y = target_y
            return True

        step_x = dx / distance * speed
        step_y = dy / distance * speed
        self.x += step_x
        self.y += step_y
        self.direction = self.get_direction_from_step(step_x, step_y)
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

    def start_drag(self, mouse_x, mouse_y):
        self.dragging = True
        self.drag_started_at = time.monotonic()
        self.drag_hissed = False
        self.drag_start_x = mouse_x
        self.drag_start_y = mouse_y
        self.drag_offset_x = mouse_x - self.x
        self.drag_offset_y = mouse_y - self.y
        self.clear_temporary_states()
        self.target_x = self.x
        self.target_y = self.y
        self.show_dragged_frame()

    def drag_to(self, mouse_x, mouse_y):
        if not self.dragging:
            return
        self.x, self.y = self.get_clamped_position(
            mouse_x - self.drag_offset_x,
            mouse_y - self.drag_offset_y,
        )
        self.target_x = self.x
        self.target_y = self.y

    def end_drag(self, mouse_x, mouse_y, cat_bed=None):
        if not self.dragging:
            return
        moved_distance = math.hypot(mouse_x - self.drag_start_x, mouse_y - self.drag_start_y)
        dragged_for = time.monotonic() - self.drag_started_at
        self.dragging = False
        if (
            cat_bed is not None
            and moved_distance > CLICK_DRAG_THRESHOLD
            and cat_bed.contains_drop(self, mouse_x, mouse_y)
        ):
            target_x, target_y = cat_bed.sleep_position_for_drop(self)
            self.sleep_at(target_x, target_y)
        elif self.drag_hissed or dragged_for >= self.drag_hiss_seconds:
            self.start_hiss()
        elif moved_distance <= CLICK_DRAG_THRESHOLD:
            self.register_click()
        else:
            self.target_x = self.x
            self.target_y = self.y
            self.resume_after_drop()

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
    def get_direction_from_step(step_x, step_y):
        abs_x = abs(step_x)
        abs_y = abs(step_y)

        if abs_x > abs_y * 1.8:
            return "right" if step_x > 0 else "left"
        if abs_y > abs_x * 1.8:
            return "up" if step_y > 0 else "down"
        if step_x > 0 and step_y > 0:
            return "up_right"
        if step_x < 0 and step_y > 0:
            return "up_left"
        if step_x > 0 and step_y < 0:
            return "down_right"
        if step_x < 0 and step_y < 0:
            return "down_left"
        return "up" if step_y > 0 else "down"


def self_test(sheet_path):
    with tempfile.TemporaryDirectory(prefix="desktop-cat-test-") as frame_dir:
        frames = load_nsimage_frames(sheet_path, Path(frame_dir), 3)
        assert sorted(frames) == [
            "down",
            "down_left",
            "down_right",
            "dragged",
            "hind_legs",
            "hiss_left",
            "hiss_right",
            "left",
            "lie",
            "meow",
            "meow_lie",
            "meow_sit",
            "meow_sit2",
            "meow_stand",
            "paw_attack_down",
            "paw_attack_down_left",
            "paw_attack_down_right",
            "paw_attack_left",
            "paw_attack_right",
            "paw_attack_up",
            "paw_attack_up_left",
            "paw_attack_up_right",
            "right",
            "scratch_left",
            "scratch_right",
            "sit",
            "sit2",
            "sleep_1_left",
            "sleep_1_right",
            "sleep_2_left",
            "sleep_2_right",
            "sleep_3_left",
            "sleep_3_right",
            "sleep_4_left",
            "sleep_4_right",
            "stand",
            "up",
            "up_left",
            "up_right",
            "wash",
            "wash_lie",
            "wash_sit",
            "wash_stand",
            "yawn",
            "yawn_lie",
            "yawn_sit",
            "yawn_sit2",
            "yawn_stand",
        ]
        assert len(frames["down"]) == 4
        assert len(frames["up"]) == 4
        assert len(frames["left"]) == 8
        assert len(frames["right"]) == 8
        assert len(frames["down_left"]) == 6
        assert len(frames["down_right"]) == 6
        assert len(frames["up_left"]) == 6
        assert len(frames["up_right"]) == 6
        assert len(frames["sit"]) >= 6
        assert len(frames["stand"]) >= 8
        assert len(frames["sit2"]) >= 6
        assert len(frames["lie"]) >= 8
        assert len(frames["meow"]) >= 3
        assert len(frames["meow_sit"]) >= 3
        assert len(frames["meow_stand"]) >= 3
        assert len(frames["meow_sit2"]) >= 3
        assert len(frames["meow_lie"]) >= 3
        assert len(frames["yawn"]) >= 8
        assert len(frames["yawn_sit"]) >= 8
        assert len(frames["yawn_stand"]) >= 8
        assert len(frames["yawn_sit2"]) >= 8
        assert len(frames["yawn_lie"]) >= 8
        assert len(frames["wash"]) >= 8
        assert len(frames["wash_sit"]) >= 8
        assert len(frames["wash_stand"]) >= 8
        assert len(frames["wash_lie"]) >= 7
        assert len(frames["scratch_left"]) >= 8
        assert len(frames["scratch_right"]) >= 8
        assert len(frames["hiss_left"]) >= 2
        assert len(frames["hiss_right"]) >= 2
        assert len(frames["dragged"]) >= 1
        assert len(frames["hind_legs"]) >= 4
        assert len(frames["paw_attack_down"]) >= 8
        for sleep_number in range(1, 5):
            assert len(frames[f"sleep_{sleep_number}_left"]) >= 2
            assert len(frames[f"sleep_{sleep_number}_right"]) >= 2
        first_frame = frames["down"][0]
        assert int(first_frame.size().width) == 96
        assert int(first_frame.size().height) == 96


def get_responsive_cat_scale(width, height, base_scale, max_scale, reference_screen):
    screen_factor = min(width / reference_screen[0], height / reference_screen[1])
    if screen_factor <= 1:
        return base_scale
    return min(max_scale, base_scale * (screen_factor ** 0.35))


class CatBedWindow:
    def __init__(self, image_path, cat_scale, screen_frames=None):
        self.image_path = Path(image_path)
        self.scale = max(1, cat_scale * BED_SCALE_MULTIPLIER)
        self.visible = False
        self.layer = "back"
        self.image = self.load_image()
        self.width = int(self.image.size().width)
        self.height = int(self.image.size().height)
        self.set_screen_frames(screen_frames or get_visible_screen_frames())

        rect = AppKit.NSMakeRect(self.x, self.y, self.width, self.height)
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setHasShadow_(False)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setLevel_(window_level_for_layer(self.layer))
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorStationary
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        self.image_view = AppKit.NSImageView.alloc().initWithFrame_(
            AppKit.NSMakeRect(0, 0, self.width, self.height)
        )
        self.image_view.setImageScaling_(AppKit.NSImageScaleAxesIndependently)
        self.image_view.setImage_(self.image)
        self.window.setContentView_(self.image_view)

    def load_image(self):
        source = pygame.image.load(str(self.image_path))
        scaled_size = (
            max(1, round(source.get_width() * self.scale)),
            max(1, round(source.get_height() * self.scale)),
        )
        scaled = pygame.transform.scale(source, scaled_size)
        self.set_visible_bounds(scaled)
        output_path = Path(tempfile.gettempdir()) / "desktop_cat_bed_scaled.png"
        pygame.image.save(scaled, str(output_path))
        return AppKit.NSImage.alloc().initWithContentsOfFile_(str(output_path))

    def set_visible_bounds(self, surface):
        rects = pygame.mask.from_surface(surface).get_bounding_rects()
        if not rects:
            self.visible_min_x = 0
            self.visible_max_x = surface.get_width()
            self.visible_min_y = 0
            self.visible_max_y = surface.get_height()
            self.visible_width = surface.get_width()
            self.visible_center_x = surface.get_width() / 2
            self.visible_center_y = surface.get_height() / 2
            return

        left = min(rect.left for rect in rects)
        top = min(rect.top for rect in rects)
        right = max(rect.right for rect in rects)
        bottom = max(rect.bottom for rect in rects)
        self.visible_min_x = left
        self.visible_max_x = right
        self.visible_min_y = surface.get_height() - bottom
        self.visible_max_y = surface.get_height() - top
        self.visible_width = right - left
        self.visible_center_x = left + self.visible_width / 2
        self.visible_center_y = surface.get_height() - (top + (bottom - top) / 2)

    def set_screen_frames(self, screen_frames):
        screen_signature = get_screen_frames_signature(screen_frames)
        if getattr(self, "screen_signature", None) == screen_signature:
            return

        self.screen_signature = screen_signature
        self.screen_frames = screen_frames
        self.position_bounds = get_window_position_bounds(
            self.screen_frames,
            self.width,
            self.height,
        )
        self.min_x, self.min_y, self.max_x, self.max_y = get_union_bounds(
            self.position_bounds
        )

        if not hasattr(self, "x"):
            self.position_on_screen_containing_point(*AppKit.NSEvent.mouseLocation())
            return

        self.x, self.y = self.get_clamped_position(self.x, self.y)
        if hasattr(self, "window") and self.visible:
            self.window.setFrameOrigin_(AppKit.NSMakePoint(self.x, self.y))

    def position_on_screen_containing_point(self, point_x, point_y):
        screen_frame = get_screen_frame_containing_point(
            self.screen_frames,
            point_x,
            point_y,
        )
        self.x = screen_frame.origin.x + (screen_frame.size.width - self.width) / 2
        self.y = screen_frame.origin.y + 36
        self.x, self.y = self.get_clamped_position(self.x, self.y)

    def get_clamped_position(self, x, y):
        return get_clamped_position_in_bounds(x, y, self.position_bounds)

    def show(self):
        self.set_screen_frames(get_visible_screen_frames())
        if not self.visible:
            self.position_on_screen_containing_point(*AppKit.NSEvent.mouseLocation())
        self.window.setFrameOrigin_(AppKit.NSMakePoint(self.x, self.y))
        self.order_for_layer()
        self.visible = True

    def hide(self):
        self.window.orderOut_(None)
        self.visible = False

    def set_layer(self, layer):
        self.layer = layer if layer == "front" else "back"
        self.window.setLevel_(window_level_for_layer(self.layer))
        if self.visible:
            self.order_for_layer()

    def order_for_layer(self):
        if self.layer == "front":
            self.window.orderFrontRegardless()
        else:
            self.window.orderFront_(None)

    def hide_if_empty(self, desktop_cats):
        if self.visible and not any(
            cat.dragging or cat.is_using_home()
            for cat in desktop_cats
        ):
            self.hide()

    def close(self):
        self.window.close()

    def contains_drop(self, cat, mouse_x, mouse_y):
        if not self.visible:
            return False
        center_x = cat.x + cat.width / 2
        center_y = cat.y + cat.height / 2
        return (
            self.contains_screen_point(center_x, center_y)
            or self.contains_screen_point(mouse_x, mouse_y)
        )

    def contains_screen_point(self, point_x, point_y):
        return (
            self.x + self.visible_min_x <= point_x <= self.x + self.visible_max_x
            and self.y + self.visible_min_y <= point_y <= self.y + self.visible_max_y
        )

    def sleep_position_for_drop(self, cat):
        min_center_x = self.x + self.visible_min_x
        max_center_x = self.x + self.visible_max_x
        min_center_y = self.y + self.visible_min_y
        max_center_y = self.y + self.visible_max_y
        center_x = min(max(cat.x + cat.width / 2, min_center_x), max_center_x)
        center_y = min(max(cat.y + cat.height / 2, min_center_y), max_center_y)
        return cat.get_clamped_position(
            center_x - cat.width / 2,
            center_y - cat.height / 2,
        )

    def cat_target_for(self, index, total, cat_width, cat_height):
        if total <= 1:
            offset_x = 0
        else:
            usable_width = max(cat_width, self.visible_width * BED_SLEEP_WIDTH_RATIO)
            fit_spacing = (usable_width - cat_width) / max(1, total - 1)
            spacing = min(cat_width * 0.46, fit_spacing)
            offset_x = (index - (total - 1) / 2) * spacing

        target_x = self.x + self.visible_center_x - cat_width / 2 + offset_x
        target_y = self.y + self.visible_center_y - cat_height / 2
        return self.get_clamped_position(target_x, target_y)


class StatusMenuController(AppKit.NSObject):
    def menuWillOpen_(self, menu):
        self.start_menu_animation_timer()

    def menuDidClose_(self, menu):
        self.stop_menu_animation_timer()

    def start_menu_animation_timer(self):
        self.stop_menu_animation_timer()
        frame_delay = 1 / self.fps
        self.menu_animation_timer = (
            Foundation.NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
                frame_delay,
                self,
                "tickWhileMenuOpen:",
                None,
                True,
            )
        )
        Foundation.NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.menu_animation_timer,
            AppKit.NSEventTrackingRunLoopMode,
        )

    def stop_menu_animation_timer(self):
        if self.menu_animation_timer is not None:
            self.menu_animation_timer.invalidate()
            self.menu_animation_timer = None

    def tickWhileMenuOpen_(self, timer):
        tick_desktop_cats(self.desktop_cats, self.cat_bed)

    def house_(self, sender):
        self.cat_bed.show()
        total = len(self.desktop_cats)
        for index, desktop_cat in enumerate(self.desktop_cats):
            target_x, target_y = self.cat_bed.cat_target_for(
                index,
                total,
                desktop_cat.width,
                desktop_cat.height,
            )
            desktop_cat.go_home(target_x, target_y)
            desktop_cat.order_for_layer()

    def lazyCat_(self, sender):
        self.set_cat_personality("lazy")

    def activeCat_(self, sender):
        self.set_cat_personality("active")

    def set_cat_personality(self, personality):
        for desktop_cat in self.desktop_cats:
            desktop_cat.set_personality(personality)

    def frontLayer_(self, sender):
        self.set_cat_layer("front")

    def backLayer_(self, sender):
        self.set_cat_layer("back")

    def set_cat_layer(self, layer):
        self.cat_bed.set_layer(layer)
        for desktop_cat in self.desktop_cats:
            desktop_cat.set_layer(layer)

    def quit_(self, sender):
        AppKit.NSApplication.sharedApplication().terminate_(sender)


def create_status_menu(icon_path, cat_bed, desktop_cats, fps):
    status_item = AppKit.NSStatusBar.systemStatusBar().statusItemWithLength_(
        AppKit.NSVariableStatusItemLength
    )
    icon = AppKit.NSImage.alloc().initWithContentsOfFile_(str(icon_path))
    icon.setTemplate_(True)
    icon.setSize_(AppKit.NSMakeSize(18, 18))
    status_item.button().setImage_(icon)

    menu = AppKit.NSMenu.alloc().init()
    controller = StatusMenuController.alloc().init()
    controller.cat_bed = cat_bed
    controller.desktop_cats = desktop_cats
    controller.fps = fps
    controller.menu_animation_timer = None

    house_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "House",
        "house:",
        "",
    )
    house_item.setTarget_(controller)
    menu.addItem_(house_item)

    mode_menu = AppKit.NSMenu.alloc().initWithTitle_("Mode")
    mode_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Mode",
        None,
        "",
    )
    mode_item.setSubmenu_(mode_menu)
    menu.addItem_(mode_item)

    lazy_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Lazy Cat",
        "lazyCat:",
        "",
    )
    lazy_item.setTarget_(controller)
    mode_menu.addItem_(lazy_item)

    active_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Active Cat",
        "activeCat:",
        "",
    )
    active_item.setTarget_(controller)
    mode_menu.addItem_(active_item)

    layer_menu = AppKit.NSMenu.alloc().initWithTitle_("Layer")
    layer_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Layer",
        None,
        "",
    )
    layer_item.setSubmenu_(layer_menu)
    menu.addItem_(layer_item)

    front_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Front",
        "frontLayer:",
        "",
    )
    front_item.setTarget_(controller)
    layer_menu.addItem_(front_item)

    back_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Back",
        "backLayer:",
        "",
    )
    back_item.setTarget_(controller)
    layer_menu.addItem_(back_item)

    menu.addItem_(AppKit.NSMenuItem.separatorItem())

    quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit",
        "quit:",
        "q",
    )
    quit_item.setTarget_(controller)
    menu.addItem_(quit_item)

    menu.setDelegate_(controller)
    status_item.setMenu_(menu)
    return controller, status_item


def tick_desktop_cats(desktop_cats, cat_bed):
    screen_frames = get_visible_screen_frames()
    cat_bed.set_screen_frames(screen_frames)

    for desktop_cat in desktop_cats:
        desktop_cat.set_screen_frames(screen_frames)
        desktop_cat.update()
        desktop_cat.draw()

    cat_bed.hide_if_empty(desktop_cats)
    AppKit.NSApplication.sharedApplication().updateWindows()


def run_desktop_cats(app, desktop_cats, cat_bed, fps):
    frame_delay = 1 / fps

    while True:
        started_at = time.monotonic()
        DesktopCat.process_events(app, desktop_cats, cat_bed)

        tick_desktop_cats(desktop_cats, cat_bed)

        elapsed = time.monotonic() - started_at
        time.sleep(max(0, frame_delay - elapsed))
