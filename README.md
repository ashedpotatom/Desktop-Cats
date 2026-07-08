# Desktop Cats

Desktop Cats is a cat version of the original desktop ducky project. The pet uses
Python and PyGame, picks random nearby, medium, or faraway points on the
screen, and walks around with 8-directional cat animations from the included
Free pack sprites. Cats can be switched between lazy and active personalities,
wash more often while resting, can be dragged around, click without moving to
trigger a silent meow animation, and sometimes yawn, scratch, hiss, or
playfully paw attack before wandering again. They also occasionally stand on
their hind legs.

## How to Run

On macOS, double-click:

```text
Run Desktop Cats.command
```

The command creates a local `.venv`, installs the required Python packages, and
then starts Desktop Cats. If Python 3 is missing, it opens the Python download
page or tries `brew install python` when Homebrew is available. After setup, the
Terminal window minimizes itself while the cats keep running.

From Terminal, you can also run:

```bash
./Run\ Desktop\ Cats.command
```

Show a specific number of cats:

```bash
./Run\ Desktop\ Cats.command 5
```

To keep the Terminal window visible for troubleshooting:

```bash
DESKTOP_CATS_KEEP_TERMINAL=1 ./Run\ Desktop\ Cats.command
```

Press `Esc` or `Q` to close the pet.

## Notes

- Mac App Store preparation files are in `packaging/`. Start with
  `packaging/APP_STORE_RELEASE_PLAN_KO.md` and
  `packaging/APP_STORE_RELEASE_CHECKLIST.md` before building a signed app.
- On macOS, the app uses tiny transparent desktop-level windows that move
  around every connected display. Regular app windows can cover the cats, so
  they pass underneath active windows instead of walking over them.
- On Windows, the app uses a transparent, always-on-top borderless window so
  the cat can roam over the desktop.
- On other operating systems, PyGame opens a borderless preview window.
- Change `CAT_COUNT` in `main.py`, pass `--cats`, or set
  `DESKTOP_CAT_COUNT` to control how many cats appear.
- Change `CAT_VARIANTS` in `main.py` to choose which Free pack cat sheets are
  used.
- The base cat size is 40% smaller than the original version, and it scales up
  gently on larger screens.
- On macOS, the menu bar cat icon has `House`, `Mode`, and `Layer`. Use
  `Mode` to choose `Lazy Cat` or `Active Cat`. Lazy cats rest about 70% of the
  time and move about 30% of the time, mostly with short walks. Active cats move
  about 70% of the time, with a mix of short walks and longer dashes.
- Use `Layer` to choose `Front` or `Back`. `Front` pins cats above other
  windows, while `Back` sends them underneath normal app windows.
- Click a cat to play a silent meow animation. The click can use `meow sit`,
  `meow stand`, `meow sit 2`, or `meow lie`.
- Resting cats have a higher chance to wash themselves using the matching
  `wash sit`, `wash stand`, or `wash lie` animation, repeated 1 to 3 times.
- Drag a cat to move it. While dragging, it uses the unnamed frame below
  `hiss (r)` in the Free pack reference sheet.
- Clicking too many times quickly or holding a drag for 3 seconds makes the cat
  hiss 2 to 3 times.
- On macOS, click the menu bar cat icon and choose `House` to show the cat bed.
  The bed is scaled larger than the cats and targets the visible center of the
  bed art, so cats can tuck into it before sleeping with a random `sleep 1`,
  `sleep 2`, `sleep 3`, or `sleep 4` animation. Sleep animations breathe more
  slowly than other actions. If no cats are going to or sleeping in the bed, the
  bed hides until `House` is chosen again.
- If a sleeping cat is dragged awake and dropped back onto the visible bed, it
  sleeps again where it was dropped instead of snapping to the bed center.

On macOS, stop the cat by pressing `Control+C` in the Terminal window that
started it, or by closing that Terminal window.

## Credits

Based on `munucrafts/PY-DesktopPet-Ducky`.

Cat sprite sheets are from the local `Free pack` folder provided with this
project. See `ASSET_CREDITS.md` for details.
