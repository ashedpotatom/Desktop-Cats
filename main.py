from pathlib import Path
from argparse import ArgumentParser
import os
import platform
import random
import sys

import pygame

from cat import Cat, load_cat_frames


def get_base_dir():
    resource_path = os.environ.get("RESOURCEPATH")
    if resource_path:
        return Path(resource_path)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parents[1] / "Resources"
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
CAT_ASSET_DIR = BASE_DIR / "Assets" / "Sprites" / "free_pack"
CAT_BED_IMAGE = BASE_DIR / "Assets" / "House" / "cat_bed_blue.png"
MENU_BAR_ICON = BASE_DIR / "Assets" / "MenuBar" / "cat_icon.png"
CAT_VARIANTS = (
    "cat_1.png",
    "cat_1_6.png",
    "cat_1_9.png",
)
FPS = 60
ORIGINAL_CAT_SCALE = 3
CAT_SCALE = ORIGINAL_CAT_SCALE * 0.6
MAX_CAT_SCALE = ORIGINAL_CAT_SCALE * 0.9
CAT_COUNT = 3
REFERENCE_SCREEN = (1440, 900)
TRANSPARENCY_COLOR = (255, 0, 255)
PREVIEW_BACKGROUND = (28, 28, 32)
CLICK_DRAG_THRESHOLD = 6


def create_window():
    screen = pygame.display.Info()
    screen_size = (screen.current_w, screen.current_h)

    if platform.system() == "Windows":
        return pygame.display.set_mode(screen_size, pygame.NOFRAME)

    preview_size = (
        min(900, screen.current_w),
        min(600, screen.current_h),
    )
    return pygame.display.set_mode(preview_size, pygame.NOFRAME)


def configure_desktop_window():
    if platform.system() != "Windows":
        return lambda: None

    try:
        import ctypes
        import win32con
        import win32gui
    except ImportError:
        print("Install pywin32 for the transparent desktop window on Windows.")
        return lambda: None

    hwnd = pygame.display.get_wm_info().get("window")
    if not hwnd:
        return lambda: None

    user32 = ctypes.windll.user32
    layered_window = 0x80000
    current_style = user32.GetWindowLongW(hwnd, -20)
    user32.SetWindowLongW(hwnd, -20, current_style | layered_window)

    color_key = (
        TRANSPARENCY_COLOR[0]
        | (TRANSPARENCY_COLOR[1] << 8)
        | (TRANSPARENCY_COLOR[2] << 16)
    )
    user32.SetLayeredWindowAttributes(hwnd, color_key, 0, 0x00000001)

    def keep_on_top():
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )

    return keep_on_top


def get_cat_count():
    try:
        default_count = int(os.environ.get("DESKTOP_CAT_COUNT", CAT_COUNT))
    except ValueError:
        default_count = CAT_COUNT

    parser = ArgumentParser(description="Run desktop cats.")
    parser.add_argument(
        "--cats",
        type=int,
        default=default_count,
        help="number of cats to show",
    )
    args = parser.parse_args()
    return max(1, min(args.cats, 20))


def get_random_start_position(window, image):
    max_x = max(0, window.get_width() - image.get_width())
    max_y = max(0, window.get_height() - image.get_height())
    return (
        random.randint(0, max_x),
        random.randint(0, max_y),
    )


def get_responsive_cat_scale(width, height):
    screen_factor = min(width / REFERENCE_SCREEN[0], height / REFERENCE_SCREEN[1])
    if screen_factor <= 1:
        return CAT_SCALE
    return min(MAX_CAT_SCALE, CAT_SCALE * (screen_factor ** 0.35))


def create_cats(window, count, cat_scale):
    frame_cache = {}
    cats = []

    for index in range(count):
        variant = CAT_VARIANTS[index % len(CAT_VARIANTS)]
        sprite_path = CAT_ASSET_DIR / variant
        if sprite_path not in frame_cache:
            frame_cache[sprite_path] = load_cat_frames(
                sprite_path,
                scale=cat_scale,
            )

        frames = frame_cache[sprite_path]
        start_position = get_random_start_position(window, frames["down"][0])
        cats.append(
            Cat(
                window,
                frames,
                start_position,
                fps=FPS,
            )
        )

    return cats


def main():
    cat_count = get_cat_count()

    if platform.system() == "Darwin":
        from mac_desktop_cat import run_mac_desktop_cat

        run_mac_desktop_cat(
            [CAT_ASSET_DIR / variant for variant in CAT_VARIANTS],
            bed_image=CAT_BED_IMAGE,
            menu_icon=MENU_BAR_ICON,
            scale=CAT_SCALE,
            max_scale=MAX_CAT_SCALE,
            cat_count=cat_count,
            reference_screen=REFERENCE_SCREEN,
            fps=FPS,
        )
        return

    pygame.init()
    pygame.display.set_caption("Desktop Cat")

    window = create_window()
    keep_on_top = configure_desktop_window()
    clock = pygame.time.Clock()
    cat_scale = get_responsive_cat_scale(window.get_width(), window.get_height())
    cats = create_cats(window, cat_count, cat_scale)

    background = (
        TRANSPARENCY_COLOR
        if platform.system() == "Windows"
        else PREVIEW_BACKGROUND
    )

    running = True
    dragged_cat = None
    drag_start_position = None
    while running:
        clock.tick(FPS)
        keep_on_top()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_ESCAPE, pygame.K_q)
            ):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cat in reversed(cats):
                    if cat.contains_point(event.pos):
                        dragged_cat = cat
                        drag_start_position = pygame.Vector2(event.pos)
                        cats.remove(cat)
                        cats.append(cat)
                        cat.start_drag(event.pos)
                        break
            elif event.type == pygame.MOUSEMOTION and dragged_cat:
                dragged_cat.drag_to(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragged_cat:
                clicked = (
                    drag_start_position is not None
                    and pygame.Vector2(event.pos).distance_to(drag_start_position)
                    <= CLICK_DRAG_THRESHOLD
                )
                dragged_cat.end_drag(clicked=clicked)
                dragged_cat = None
                drag_start_position = None

        window.fill(background)
        for cat in cats:
            cat.update()
            cat.draw()
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
