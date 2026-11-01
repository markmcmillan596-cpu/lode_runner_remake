"""Renders a level file to a PNG with a theme's art, without needing Love2D.

    python3 tools/preview_level.py fall assets/levels/01.txt out.png [scale]

Handy for checking a level layout (or a new theme) at a glance. It draws the
screen the same way the game will: background, tiles, characters, frame.
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sprites import GRID_X, GRID_Y, TW, TH, OUT, text  # noqa: E402

TILE_SPRITE = {"#": "brick", "@": "bedrock", "H": "ladder", "-": "bar", "X": "trap", "$": "gold"}


def load_theme(theme):
    d = os.path.join(OUT, "themes", theme)
    sheet = Image.open(os.path.join(d, "sheet.png"))
    rects = {}
    for line in open(os.path.join(d, "sheet.lua")):
        line = line.strip()
        if "= {x=" in line:
            name, rest = line.split(" = ")
            vals = dict(kv.split("=") for kv in rest.strip("{},").split(", "))
            x, y, w, h = (int(vals[k]) for k in "xywh")
            rects[name] = sheet.crop((x, y, x + w, y + h))
    return d, rects


def render(theme, level_path, show_exit=False):
    d, spr = load_theme(theme)
    screen = Image.open(os.path.join(d, "background.png")).convert("RGBA")
    rows = open(level_path).read().split("\n")[:16]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            x, y = GRID_X + c * TW, GRID_Y + r * TH
            name = TILE_SPRITE.get(ch)
            if ch == "S" and show_exit:
                name = "exit_1"
            if name:
                screen.alpha_composite(spr[name], (x, y))
            if ch == "0":
                screen.alpha_composite(spr["guard_run_1"], (x, y))
            if ch == "&":
                screen.alpha_composite(spr["player_run_1"], (x, y))
    screen.alpha_composite(Image.open(os.path.join(d, "frame.png")), (0, 0))
    return screen


if __name__ == "__main__":
    theme, lvl, out = sys.argv[1:4]
    scale = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    img = render(theme, lvl)
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(out)
