"""Generates every image for the Lode Runner-style seasonal asset pack.

    python3 tools/gen_sprites.py            # builds all themes listed in THEMES
    python3 tools/gen_sprites.py fall       # builds one theme

Writes, per theme, into assets/themes/<theme>/:
    sheet.png + sheet.lua   sprite atlas and its name -> rect table
    background.png          320x240 scene behind the level
    frame.png               320x240 HUD panels and ground strip (drawn on top)
    title.png               192x32 title banner
and assets/font.png (3x5 pixel font) once.

How the art is made (the lesson in this file):
  * Every sprite is an ASCII map. Each letter is a colour ROLE ("c" = shirt,
    "o" = trousers...). A theme is just a palette that says what colour each role is.
  * Characters are built from two parts: a HEAD (5 rows, per character per theme)
    stamped onto a BODY pose (shared by every theme). So the scarecrow and the
    mummy run with exactly the same legs. Change a pose once, every theme follows.
  * Tiles are 8 wide x 12 tall. 28 columns x 8 px = 224 px, the same playfield
    width as the other games in the project, and 28 x 16 is the original grid.
"""
import os
import sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")
TW, TH = 8, 12                       # tile size
SCREEN_W, SCREEN_H = 320, 240
GRID_X, GRID_Y, COLS, ROWS = 48, 30, 28, 16
FLOOR_Y = GRID_Y + ROWS * TH         # 222: top of the ground strip in frame.png


def hexc(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# ---------------------------------------------------------------------------
# 3x5 font (same glyph order as the other packs: " A-Z 0-9 . : - !")
# ---------------------------------------------------------------------------
GLYPHS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:-!"
FONT = {
    " ": ["...", "...", "...", "...", "..."],
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#.#", "###", "###", "#.#", "#.#"], "N": ["##.", "#.#", "#.#", "#.#", "#.#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "Q": [".#.", "#.#", "#.#", "##.", ".##"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#.#", "#.#", "###", "###", "#.#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], "Z": ["###", "..#", ".#.", "#..", "###"],
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["##.", "..#", ".#.", "#..", "###"], "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "##."],
    ".": ["...", "...", "...", "...", ".#."], ":": ["...", ".#.", "...", ".#.", "..."],
    "-": ["...", "...", "###", "...", "..."], "!": [".#.", ".#.", ".#.", "...", ".#."],
}


def text(img, s, x, y, col, scale=1, shadow=None):
    """Draw text with the 3x5 font. Each glyph is 4 px wide (3 + 1 gap) at scale 1."""
    px = img.load()
    for ch in s.upper():
        g = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c != "#":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        X, Y = x + gx * scale + sx, y + gy * scale + sy
                        if shadow and 0 <= X + 1 < img.width and 0 <= Y + 1 < img.height:
                            if px[X + 1, Y + 1][3] == 0 or px[X + 1, Y + 1] != col:
                                px[X + 1, Y + 1] = shadow
                        if 0 <= X < img.width and 0 <= Y < img.height:
                            px[X, Y] = col
        x += 4 * scale
    return x


def text_width(s, scale=1):
    return len(s) * 4 * scale - scale


def build_font():
    """love.graphics.newImageFont format: a separator column (colour of pixel 0,0) before every glyph."""
    sep = (255, 0, 255, 255)
    w = 1 + len(GLYPHS) * 5
    img = Image.new("RGBA", (w, 5), (0, 0, 0, 0))
    px = img.load()
    x = 0
    for ch in GLYPHS:
        for y in range(5):
            px[x, y] = sep
        x += 1
        for gy, row in enumerate(FONT[ch]):
            for gx, c in enumerate(row):
                if c == "#":
                    px[x + gx, gy] = (255, 255, 255, 255)
        x += 4                      # 3 px glyph + 1 px gap
    for y in range(5):
        px[w - 1, y] = sep
    img.save(os.path.join(OUT, "font.png"))


# ---------------------------------------------------------------------------
# Character art
# ---------------------------------------------------------------------------
# BODY poses: 8x12 maps, facing RIGHT. "." = transparent.
#   c torso   a sleeve   g hand   o trousers   O trouser shade   b feet
# head = (column, row, view): where the 8x5 head sprite is stamped, and which view.
POSES = {
    "run_1": ((0, 0, "side"), [
        "........", "........", "........", "........", "........",
        "..cccca.", ".acccc.g", ".g.oo...", "..oooo..", ".oo..oo.", ".o....o.", "bb....bb"]),
    "run_2": ((0, 0, "side"), [
        "........", "........", "........", "........", "........",
        "...ccca.", "..acccg.", "..g.oo..", "...oo...", "...oOo..", "...o.o..", "...bbb.."]),
    "run_3": ((0, 0, "side"), [
        "........", "........", "........", "........", "........",
        ".acccc..", "g.cccca.", "...oo.g.", "..oooo..", ".oo..oo.", "oo....o.", "b.....bb"]),
    "run_4": ((0, 0, "side"), [
        "........", "........", "........", "........", "........",
        "..accc..", "..gccca.", "...oo.g.", "...oo...", "..oOo...", "..o.o...", "..bbb..."]),
    # climbing: seen from behind, hands reach up past the head
    "climb_1": ((0, 0, "back"), [
        "g.......", "a.......", "a.......", "a.......", "a.......",
        "acccccc.", "..cccca.", "..cccc.g", "..oooo..", "..o..o..", "..o..oo.", "..b....."]),
    "climb_2": ((0, 0, "back"), [
        ".......g", ".......a", ".......a", ".......a", ".......a",
        ".cccccca", ".acccc..", "g.cccc..", "..oooo..", "..o..o..", ".oo..o..", ".....b.."]),
    # hand-over-hand on a bar: hands at the top, head dropped two rows
    "bar_1": ((0, 3, "side"), [
        "........", ".g...g..", ".a...a..", "........", "........", "........",
        "........", "........", ".acccca.", "..cccc..", "..oooo..", "..o..o.."]),
    "bar_2": ((0, 3, "side"), [
        "........", "..g...g.", "..a...a.", "........", "........", "........",
        "........", "........", "..acccca", "..cccc..", "..oooo..", "...oo..."]),
    # falling: arms up, legs together
    "fall": ((0, 1, "side"), [
        "g......g", "a......a", "a......a", "........", "........",
        "........", "acccccca", "..cccc..", "..oooo..", "..o..o..", "..o..o..", "..b..b.."]),
    # digging: crouched, arm pointing down-forward to the brick beside you
    "dig": ((0, 1, "side"), [
        "........", "........", "........", "........", "........",
        "........", "..ccccaa", "..ccccag", ".oooo...", ".oo.oo..", ".o...o..", "bb...bb."]),
}

# Guard-only poses
GUARD_POSES = {
    # stuck in a hole: only the top half shows, arms flailing
    "trapped_1": ((0, 5, "side"), [
        "........", "........", "g.......", "a......g", "a......a",
        "........", "........", "........", "........", "acccccca", "..cccc..", "..cccc.."]),
    "trapped_2": ((0, 6, "side"), [
        "........", "........", "........", "g......g", "a......a",
        "a......a", "........", "........", "........", "........", "acccccca", "..cccc.."]),
}

# HEADS: 8x5, facing right ("side") and from behind ("back").
#   h hat   H hat shade   s skin   e eye   m mouth / stitching   w wrap   W wrap shade   r hair
HEADS = {
    "fall": {
        "player": {   # farmer kid in a straw hat
            "side": [".hhhh...", "hHHHHhh.", "..sse...", "..sss...", "...s...."],
            "back": ["..hhhh..", ".hHHHHh.", "..rrrr..", "..rrrr..", "...ss..."],
        },
        "guard": {    # scarecrow: burlap sack head, floppy hat
            "side": ["..hhh...", ".hhhhhhH", "..sse...", "..mms...", "...ss..."],
            "back": ["..hhh...", ".Hhhhhhh", "..ssss..", "..ssss..", "...ss..."],
        },
    },
    "halloween": {
        "player": {   # trick-or-treater in a witch hat
            "side": ["....hH..", "...hhh..", "hhhHhhhh", "..sse...", "...ss..."],
            "back": ["....hH..", "...hhh..", "hhhHhhhh", "..rrrr..", "...ss..."],
        },
        "guard": {    # mummy: bandages and one glowing eye
            "side": ["..wwww..", "..WwwW..", "..wwwe..", "..Wwww..", "...ww..."],
            "back": ["..wwww..", "..WwwW..", "..wwww..", "..wWWw..", "...ww..."],
        },
    },
    "christmas": {
        "player": {   # elf in a red hat with a white pom-pom
            "side": ["...hw...", "..hhhH..", ".wwwwww.", "..sse...", "...ss..."],
            "back": ["...hw...", "..hhhH..", ".wwwwww.", "..rrrr..", "...ss..."],
        },
        "guard": {    # nutcracker: tall black hat with a gold band, white beard
            "side": ["..hhhh..", "..HHHH..", "..sse...", "..wwws..", "...ww..."],
            "back": ["..hhhh..", "..HHHH..", "..ssss..", "..wwww..", "...ww..."],
        },
    },
    "winter": {
        "player": {   # kid in a striped beanie
            "side": ["..hhhh..", ".hwhwhH.", ".hhhhhh.", "..sse...", "...ss..."],
            "back": ["..hhhh..", ".hwhwhH.", ".hhhhhh.", "..hhhh..", "...ss..."],
        },
        "guard": {    # snowman: top hat, coal eye, carrot nose
            "side": ["..hhh...", ".hhhhh..", ".wwwwe..", ".wWwwmm.", "..wwww.."],
            "back": ["..hhh...", ".hhhhh..", ".wwwww..", ".wWwww..", "..wwww.."],
        },
    },
}

# ---------------------------------------------------------------------------
# Themes: one palette per theme. Every colour the art uses is named here.
# ---------------------------------------------------------------------------
THEMES = {
    "fall": {
        "title": "HARVEST HEIST",
        "player": {"h": "e8c15a", "H": "a8782e", "s": "f2c49b", "e": "2a1a10", "r": "8a4b20",
                   "c": "d9532b", "a": "d9532b", "g": "f2c49b", "o": "3a6ea5", "O": "274e7a", "b": "5a3418"},
        "guard":  {"h": "7a5232", "H": "4e3220", "s": "dcb878", "e": "1a1008", "m": "7a5232",
                   "c": "9cae44", "a": "f0c050", "g": "f6dc80", "o": "a07a46", "O": "765630", "b": "f0c050"},
        # tiles
        "brick": {"B": "9a4b2a", "L": "c26a3d", "D": "6e3018", "M": "3b1c0e"},
        "bedrock": {"S": "6f6658", "L": "9a9080", "D": "433c33", "K": "564e43"},
        "ladder": {"R": "c58b4a", "r": "7e5326"},
        "bar": {"R": "d8b878", "r": "8e6e36"},
        "exit": {"R": "ffd25a", "r": "ff9a1e"},
        "fresh": "c98a5a",                           # tint of a brick that is refilling
        "item": "acorn",
        "itemcol": {"a": "e9b13a", "A": "b8801c", "k": "6e4a1e", "K": "8e6430", "l": "fff0a0", "s": "4a7a2a"},
        # scenery
        "sky": ["140a1c", "2a1424", "5a2a22", "a8542a"],
        "moon": "f5a742", "moon_shade": "d9822a", "halo": "f5a742",
        "hill": "1e120c", "hill2": "2c1a10",
        "panel": "160c08", "edge": "ff8a1e", "edge_dark": "723c0c",
        "label": "ff3b2e", "text": "ffe0a8", "accent": "e0701c",
        "ground": {"top": "6a4a2a", "mid": "3e2a16", "dark": "24170c"},
        "spark": "fff0a0",
        "amb": "leaves",
    },
    "halloween": {
        "title": "CANDY HEIST",
        "player": {"h": "9258dc", "H": "6238a8", "s": "f0c8a0", "e": "1a0e1e", "r": "ff8a1e",
                   "c": "2ec27a", "a": "2ec27a", "g": "f0c8a0", "o": "ff7a12", "O": "c4560a", "b": "1e1428"},
        "guard":  {"w": "e8e0cc", "W": "a8a08a", "e": "7cff6a", "s": "e8e0cc",
                   "c": "d8d0bc", "a": "c8c0aa", "g": "e8e0cc", "o": "a8a08a", "O": "7e7866", "b": "8e8874"},
        "brick": {"B": "5e5470", "L": "857aa0", "D": "3e3650", "M": "1e1828"},
        "bedrock": {"S": "3e3850", "L": "6a6288", "D": "1e1a28", "K": "4e4864"},
        "ladder": {"R": "b8b2a0", "r": "6e6a5c"},            # bone-white wood
        "bar": {"R": "9a9aa8", "r": "5a5a66"},               # chain
        "exit": {"R": "9cff7a", "r": "3ec24a"},
        "fresh": "9a8ab8",
        "item": "candy",
        "itemcol": {"a": "ff8a1e", "A": "c8560a", "k": "ffe060", "K": "ffffff", "l": "fff2c0", "s": "ff8a1e"},
        "sky": ["0c0814", "1a1028", "2e1840", "4a2460"],
        "moon": "e8e0ff", "moon_shade": "b8b0e0", "halo": "c8b8ff",
        "hill": "120c1a", "hill2": "1c1428",
        "panel": "100818", "edge": "ff8010", "edge_dark": "723908",
        "label": "ff3b2e", "text": "ffa040", "accent": "ff8010",
        "ground": {"top": "3a3048", "mid": "221a2e", "dark": "140e1c"},
        "spark": "c8ff9a",
        "amb": "embers",
    },
    "christmas": {
        "title": "PRESENT HEIST",
        "player": {"h": "d42a34", "H": "8a1a22", "w": "ffffff", "s": "f2c49b", "e": "1a1018", "r": "c86a30",
                   "c": "2e9a4a", "a": "2e9a4a", "g": "f2c49b", "o": "c42a34", "O": "8a1a22", "b": "f0d048"},
        "guard":  {"h": "3a3a4a", "H": "e0b838", "s": "f2c49b", "e": "1a1018", "w": "f4f4f4",
                   "c": "c42a34", "a": "c42a34", "g": "f4f4f4", "o": "f4f4f4", "O": "c0c0cc", "b": "2a2a34"},
        "brick": {"B": "b07038", "L": "d89860", "D": "7a4420", "M": "f2ece0"},     # gingerbread, icing joints
        "bedrock": {"S": "2e5a3a", "L": "58a068", "D": "163422", "K": "3e7a4c"},   # holly-green stone
        "ladder": {"R": "f0f0f8", "r": "d02a34"},                                  # candy cane rails
        "bar": {"R": "3aa04a", "r": "c42a34"},                                     # garland
        "exit": {"R": "ffe27a", "r": "ffa81e"},
        "fresh": "f0c890",
        "item": "present",
        "itemcol": {"a": "d42a34", "A": "8a1a22", "l": "ff6a6a", "K": "ffe05a", "k": "ffe05a"},
        "sky": ["060c1e", "0c1a3a", "1a3a5a", "2e5a6e"],
        "moon": "fff4c8", "moon_shade": "e8d8a0", "halo": "fff0b0",
        "hill": "0c1a24", "hill2": "14283a", "cap": "e8f0f8",
        "panel": "0a1018", "edge": "d02030", "edge_dark": "6a1018",
        "label": "ff4a4a", "text": "ffffff", "accent": "d42030",
        "ground": {"top": "f0f6fc", "mid": "b8c8dc", "dark": "7a8aa8"},
        "spark": "fff4a0",
        "amb": "snow",
    },
    "winter": {
        "title": "FROZEN HEIST",
        "player": {"h": "3aa0e8", "H": "2070b0", "w": "ffffff", "s": "f2c49b", "e": "1a1018",
                   "c": "f08a2a", "a": "f08a2a", "g": "7a5230", "o": "2a3a6a", "O": "1a2448", "b": "5a3a28"},
        "guard":  {"h": "22262e", "w": "f4f8ff", "W": "b0c4e0", "e": "10141c", "m": "ff8a20",
                   "c": "f4f8ff", "a": "8a5a30", "g": "8a5a30", "o": "dce6f4", "O": "b0c4e0", "b": "dce6f4"},
        "brick": {"B": "5a9ed0", "L": "a8dcf4", "D": "3470a0", "M": "1e4468"},     # ice blocks
        "bedrock": {"S": "4a5668", "L": "7e8ea8", "D": "222a38", "K": "5c6a80"},   # dark slate
        "ladder": {"R": "d8e6f2", "r": "7090b0"},                                  # frosted wood
        "bar": {"R": "eef8ff", "r": "86aed0"},                                     # frosted rope
        "exit": {"R": "9affd8", "r": "30c8a0"},                                    # aurora
        "fresh": "c0e4f8",
        "item": "crystal",
        "itemcol": {"K": "e8faff", "l": "ffffff", "a": "6ad0f8", "A": "2a90d0"},
        "sky": ["04081a", "0a1a3a", "14405a", "2a6a78"],
        "moon": "f0f8ff", "moon_shade": "c0d8f0", "halo": "a8d0ff",
        "hill": "0a1424", "hill2": "162844", "cap": "dbe8f4",
        "panel": "081018", "edge": "50b0f0", "edge_dark": "1e4a70",
        "label": "78c8ff", "text": "d8f0ff", "accent": "50b0f0",
        "ground": {"top": "e0ecf8", "mid": "a8bcd4", "dark": "687c9c"},
        "spark": "d8f8ff",
        "amb": "blizzard",
    },
}


def pal(d):
    return {k: hexc(v) for k, v in d.items()}


# ---------------------------------------------------------------------------
# A tiny sprite type: a dict name -> RGBA Image, packed onto a sheet at the end
# ---------------------------------------------------------------------------
def from_map(rows, colours):
    h, w = len(rows), max(len(r) for r in rows)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != "." and c in colours:
                px[x, y] = colours[c]
    return img


def character(pose, head_set, colours):
    (hx, hy, view), body = pose
    img = from_map(body, colours)
    head = from_map(head_set[view], colours)
    img.alpha_composite(head, (hx, hy))
    return img


# ---------- tiles ----------
def brick_tile(c):
    """Two courses of bricks, joints staggered. Top row of each course is highlighted."""
    img = Image.new("RGBA", (TW, TH), c["M"])
    px = img.load()
    for course in range(2):
        y0 = course * 6
        joints = (3, 7) if course == 0 else (1, 5)  # 4 px bricks, staggered like a real wall
        for y in range(y0, y0 + 5):
            for x in range(TW):
                if x in joints:
                    continue
                col = c["B"]
                if y == y0:
                    col = c["L"]
                elif y == y0 + 4:
                    col = c["D"]
                px[x, y] = col
    return img


def bedrock_tile(c):
    """A single bevelled slab: reads as 'different' from brick at a glance (no mortar)."""
    img = Image.new("RGBA", (TW, TH), c["S"])
    px = img.load()
    for x in range(TW):
        px[x, 0] = c["L"]
        px[x, TH - 1] = c["D"]
    for y in range(TH):
        px[0, y] = c["L"]
        px[TW - 1, y] = c["D"]
    for (x, y) in [(2, 3), (5, 2), (3, 7), (6, 8), (2, 9), (4, 5)]:
        px[x, y] = c["K"]
    px[TW - 1, 0] = c["S"]
    px[0, TH - 1] = c["S"]
    return img


def ladder_tile(c):
    img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    px = img.load()
    for y in range(TH):
        px[1, y] = c["R"]
        px[6, y] = c["r"]
    for y in (1, 4, 7, 10):
        for x in range(2, 6):
            px[x, y] = c["R"]
        px[5, y] = c["r"]
    return img


def bar_tile(c, chain=False):
    img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    px = img.load()
    for x in range(TW):
        if chain:
            px[x, 1] = c["R"] if x % 4 in (0, 1) else c["r"]
            px[x, 2] = c["r"] if x % 4 in (0, 1) else c["R"]
        else:   # twisted rope
            px[x, 1] = c["R"] if x % 2 == 0 else c["r"]
            px[x, 2] = c["r"] if x % 2 == 0 else c["R"]
    return img


def dig_frames(brick):
    """Hole being dug: the brick crumbles away from the top in 4 steps."""
    frames = []
    for k in range(1, 5):
        img = brick.copy()
        px = img.load()
        cut = k * 3
        for y in range(cut):
            for x in range(TW):
                px[x, y] = (0, 0, 0, 0)
        if k < 4:   # ragged edge
            for x in range(0, TW, 2):
                px[x, cut] = (0, 0, 0, 0)
        else:       # leftover crumbs on the hole floor
            for x in (1, 4, 6):
                px[x, TH - 1] = brick.getpixel((2, 2))
        frames.append(img)
    return frames


def fill_frames(brick, fresh):
    """Hole refilling: brick grows back from the bottom, in a lighter 'fresh' tint
    so the player can see a hole is about to close."""
    f = hexc(fresh)
    frames = []
    for k in range(1, 5):
        img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
        top = TH - k * 3
        src = brick.load()
        px = img.load()
        for y in range(top, TH):
            for x in range(TW):
                r, g, b, a = src[x, y]
                if k < 4:
                    px[x, y] = ((r + f[0]) // 2, (g + f[1]) // 2, (b + f[2]) // 2, a)
                else:
                    px[x, y] = (r, g, b, a)
        frames.append(img)
    return frames


ITEMS = {
    # bottom-aligned on an 8x12 tile so the item sits on the floor below it
    "acorn": ["........", "........", "........", "........", "........",
              "...s....", ".KkkkK..", "KkkkkkK.", ".aalaa..", ".aaaaA..", "..aaA...", "...A...."],
    "candy": ["........", "........", "........", "........", "........",
              "........", "........", "s.aaa.s.", "ssalaAss", "s.aaA.s.", "........", "........"],
    "present": ["........", "........", "........", "........", "..kk.kk.",
                "...kkk..", "lllKKlll", "aaaKKaaa", "aaaKKaaa", "aaaKKaaa", "aaaKKaaa", "AAAKKAAA"],
    "crystal": ["........", "........", "........", "........", "...KK...",
                "..KllK..", ".KlllaK.", "KllaaaaK", ".KaaaAK.", "..KaAK..", "...KK...", "........"],
}


def item_sprite(theme, small=False):
    t = THEMES[theme]
    img = from_map(ITEMS[t["item"]], pal(t["itemcol"]))
    return img.crop((0, 4, 8, 12)) if small else img


# ---------- effects ----------
def circle_sprite(size, col, ring=False, holes=0):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    r = size / 2
    for y in range(size):
        for x in range(size):
            d = ((x + 0.5 - r) ** 2 + (y + 0.5 - r) ** 2) ** 0.5
            if d <= r - 0.2 and (not ring or d >= r - 1.6):
                if holes and (x * 7 + y * 3) % holes == 0:
                    continue
                px[x, y] = col
    return img


def dust_frames(col):
    out = []
    for i, (s, holes) in enumerate([(4, 0), (6, 5), (8, 3)]):
        img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        c = (col[0], col[1], col[2], 255 - i * 60)
        puff = circle_sprite(s, c, holes=holes)
        img.alpha_composite(puff, ((8 - s) // 2, (8 - s) // 2))
        out.append(img)
    return out


def number_sprite(n, col):
    s = str(n)
    img = Image.new("RGBA", (text_width(s) + 1, 6), (0, 0, 0, 0))
    text(img, s, 0, 0, col, shadow=(0, 0, 0, 255))
    return img


def spawn_frames(guard_img, col):
    """Guard re-appearing at the top: a column of light that solidifies."""
    frames = []
    w, h = guard_img.size
    for k, keep in enumerate((0.0, 0.35, 0.7)):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px, gp = img.load(), guard_img.load()
        for y in range(h):
            for x in range(w):
                if gp[x, y][3] and ((x * 5 + y * 3 + k) % 10) / 10 < keep:
                    px[x, y] = gp[x, y]
                elif gp[x, y][3] and (x + y + k) % 2 == 0:
                    px[x, y] = (col[0], col[1], col[2], 200)
        frames.append(img)
    return frames


def ambient(theme):
    t = THEMES[theme]
    if t["amb"] == "leaves":
        maps = [[".a...", "aab..", ".abb.", "..bb.", "....b"],
                ["..a..", ".aaa.", "aaaaa", ".bab.", "..b.."],
                ["b..a.", ".aaa.", ".aab.", "aab..", "....."]]
        cols = [{"a": hexc("d9532b"), "b": hexc("8a2e14")},
                {"a": hexc("e8a83a"), "b": hexc("a8641c")},
                {"a": hexc("b8481c"), "b": hexc("6e2a10")}]
        return [from_map(m, c) for m, c in zip(maps, cols)]
    if t["amb"] == "snow":         # christmas: soft flakes
        w, b = {"a": hexc("ffffff")}, {"a": hexc("c8e4ff")}
        return [from_map(["aa", "aa"], w), from_map([".a.", "aaa", ".a."], w), from_map([".a.", "aaa", ".a."], b)]
    if t["amb"] == "blizzard":     # winter: small hard flakes and one big crystal
        w, b = {"a": hexc("ffffff")}, {"a": hexc("a8dcf4"), "b": hexc("ffffff")}
        return [from_map(["aa"], w), from_map([".a.", "aaa", ".a."], b),
                from_map(["b.a.b", ".bab.", "aabaa", ".bab.", "b.a.b"], b)]
    # embers and a little bat
    e1 = from_map(["ab", "bb"], {"a": hexc("ffd060"), "b": hexc("ff8010")})
    e2 = from_map([".a.", "aba", ".a."], {"a": hexc("ff8010"), "b": hexc("ffe080")})
    bat = from_map(["a.....a", "aa.a.aa", ".aaaaa.", "..a.a.."], {"a": hexc("2a1838")})
    return [e1, e2, bat]


# ---------------------------------------------------------------------------
# Build one theme's sprite list
# ---------------------------------------------------------------------------
def build_sprites(theme):
    t = THEMES[theme]
    S = {}
    # tiles
    brick = brick_tile(pal(t["brick"]))
    S["brick"] = brick
    S["trap"] = brick.copy()                     # a trapdoor looks exactly like brick: that's the trick
    hint = brick.copy()                          # ...but the level editor needs to tell them apart
    hp = hint.load()
    for x in range(1, TW, 2):
        hp[x, TH // 2 - 1] = hexc(t["text"])
    S["trap_hint"] = hint
    S["bedrock"] = bedrock_tile(pal(t["bedrock"]))
    S["ladder"] = ladder_tile(pal(t["ladder"]))
    S["bar"] = bar_tile(pal(t["bar"]), chain=(theme == "halloween"))
    S["exit_1"] = ladder_tile(pal(t["exit"]))
    S["exit_2"] = ladder_tile({"R": hexc(t["exit"]["r"]), "r": hexc(t["exit"]["R"])})
    for i, f in enumerate(dig_frames(brick), 1):
        S["dig_%d" % i] = f
    for i, f in enumerate(fill_frames(brick, t["fresh"]), 1):
        S["fill_%d" % i] = f
    S["gold"] = item_sprite(theme)
    # characters
    for who in ("player", "guard"):
        colours = pal(t[who])
        heads = HEADS[theme][who]
        for name, pose in POSES.items():
            S["%s_%s" % (who, name)] = character(pose, heads, colours)
    gcol = pal(t["guard"])
    for name, pose in GUARD_POSES.items():
        S["guard_" + name] = character(pose, HEADS[theme]["guard"], gcol)
    for i, f in enumerate(spawn_frames(S["guard_run_2"], hexc(t["spark"])), 1):
        S["guard_spawn_%d" % i] = f
    # small icons
    life = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    life.alpha_composite(from_map(HEADS[theme]["player"]["side"], pal(t["player"])), (0, 1))
    S["life_icon"] = life
    S["gold_icon"] = item_sprite(theme, small=True)
    carry = item_sprite(theme, small=True).resize((4, 4), Image.NEAREST)
    S["carry"] = carry                           # drawn over a guard who is holding gold
    # effects
    for i, f in enumerate(dust_frames(hexc(t["brick"]["L"])), 1):
        S["dust_%d" % i] = f
    S["spark"] = from_map([".a.", "aba", ".a."], {"a": hexc(t["spark"]), "b": (255, 255, 255, 255)})
    S["debris_1"] = from_map(["aa", "aa"], {"a": hexc(t["brick"]["L"])})
    S["debris_2"] = from_map(["a.", "aa"], {"a": hexc(t["brick"]["B"])})
    for n in (75, 250, 1500):
        S["pts_%d" % n] = number_sprite(n, hexc(t["text"]))
    for i, a in enumerate(ambient(theme), 1):
        S["amb_%d" % i] = a
    return S


def pack(sprites, width=256):
    """Shelf packer: tallest first, 1 px gap. Returns sheet image and rects."""
    order = sorted(sprites.items(), key=lambda kv: (-kv[1].height, kv[0]))
    x = y = shelf = 0
    rects = {}
    for name, img in order:
        if x + img.width > width:
            x, y, shelf = 0, y + shelf + 1, 0
        rects[name] = (x, y, img.width, img.height)
        x += img.width + 1
        shelf = max(shelf, img.height)
    sheet = Image.new("RGBA", (width, y + shelf), (0, 0, 0, 0))
    for name, img in sprites.items():
        rx, ry, _, _ = rects[name]
        sheet.alpha_composite(img, (rx, ry))
    return sheet, rects


def write_sheet_lua(path, rects):
    lines = ["-- generated by tools/gen_sprites.py: sprite name -> rect on sheet.png", "return {"]
    for name in sorted(rects):
        x, y, w, h = rects[name]
        lines.append("  %s = {x=%d, y=%d, w=%d, h=%d}," % (name, x, y, w, h))
    lines.append("}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Background, frame, title
# ---------------------------------------------------------------------------
def lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def build_background(theme):
    import random
    rng = random.Random(theme)
    t = THEMES[theme]
    img = Image.new("RGBA", (SCREEN_W, SCREEN_H))
    px = img.load()
    stops = [hexc(c) for c in t["sky"]]
    for y in range(SCREEN_H):
        f = y / (SCREEN_H - 1) * (len(stops) - 1)
        i = min(int(f), len(stops) - 2)
        c = lerp_col(stops[i], stops[i + 1], f - i)
        for x in range(SCREEN_W):
            px[x, y] = c
    # stars, top half only
    for _ in range(90):
        x, y = rng.randrange(SCREEN_W), rng.randrange(150)
        b = rng.choice((90, 140, 200))
        px[x, y] = (b, b, b + 20 if b < 235 else 255, 255)
    # moon with halo, low on the horizon (kept dim: the level is drawn over it)
    mx, my, mr = 160, 196, 26
    halo, moon, shade = hexc(t["halo"]), hexc(t["moon"]), hexc(t["moon_shade"])
    for y in range(SCREEN_H):
        for x in range(SCREEN_W):
            d = ((x - mx) ** 2 + (y - my) ** 2) ** 0.5
            if d <= mr:
                c = moon
                if ((x - mx + 9) ** 2 + (y - my + 6) ** 2) < 36 or ((x - mx - 8) ** 2 + (y - my - 7) ** 2) < 20:
                    c = shade
                px[x, y] = c
            elif d <= mr + 22:
                a = (1 - (d - mr) / 22) ** 2 * 0.35
                o = px[x, y]
                px[x, y] = lerp_col(o, halo, a)
    # horizon silhouettes
    hill, hill2 = hexc(t["hill"]), hexc(t["hill2"])
    import math
    for x in range(SCREEN_W):
        h1 = 212 + 6 * math.sin(x / 23.0) + 3 * math.sin(x / 7.0)
        h2 = 204 + 8 * math.sin(x / 41.0 + 1.3)
        for y in range(SCREEN_H):
            if y >= h1:
                px[x, y] = hill
            elif y >= h2:
                px[x, y] = hill2
        if t.get("cap"):               # a line of snow along the top of each ridge
            for hy in (int(h1), int(h2)):
                px[x, hy] = hexc(t["cap"])
    if theme == "fall":           # corn stalks and bare trees
        for x in range(4, SCREEN_W - 2, 9):
            base = int(212 + 6 * math.sin(x / 23.0))
            for y in range(base - rng.randint(8, 14), base):
                px[x, y] = hill
            px[x - 1, base - 7] = hill
            px[x + 1, base - 10] = hill
        for tx in (30, 95, 230, 292):
            base = int(206 + 8 * math.sin(tx / 41.0 + 1.3))
            for y in range(base - 22, base):
                px[tx, y] = hill2
            for k in range(1, 8):
                px[tx - k, base - 14 - k] = hill2
                px[tx + k, base - 18 - k // 2] = hill2
    elif theme in ("christmas", "winter"):
        # pine trees: stacked triangles; christmas ones carry coloured lights, winter ones snow
        lights = [hexc(c) for c in ("ff4a4a", "ffe05a", "5ae08a", "6ab8ff")]
        for i, tx in enumerate(range(16, SCREEN_W - 10, 31)):
            base = int(212 + 6 * math.sin(tx / 23.0))
            top = base - rng.randint(30, 40)
            for y in range(top, base):
                half = (y - top) // 3 + 1
                for x in range(tx - half, tx + half + 1):
                    px[x, y] = hill2 if (y - top) % 9 < 7 else hill
                if theme == "winter" and (y - top) % 9 == 0:
                    for x in range(tx - half, tx + half + 1, 2):
                        px[x, y] = hexc(t["cap"])
                if theme == "christmas" and (y - top) % 6 == 4:
                    px[tx - half + 1 + (y * 7) % max(1, 2 * half - 1), y] = lights[(y + i) % 4]
            if theme == "christmas":
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):          # star on top
                    px[tx + dx, top + dy] = hexc("ffe05a")
        if theme == "winter":          # aurora: two soft green-blue bands across the sky
            for x in range(SCREEN_W):
                for k, (col, y0, amp) in enumerate((("30e8a8", 70, 18), ("5a8aff", 92, 14))):
                    yc = y0 + amp * math.sin(x / 38.0 + k * 1.7) + 6 * math.sin(x / 13.0)
                    for y in range(int(yc) - 9, int(yc) + 10):
                        a = max(0.0, 1 - abs(y - yc) / 9) * 0.32
                        px[x, y] = lerp_col(px[x, y], hexc(col), a)
    else:                          # tombstones and a crooked tree
        for tx in range(14, SCREEN_W, 27):
            base = int(212 + 6 * math.sin(tx / 23.0))
            h = rng.randint(6, 9)
            for y in range(base - h, base + 1):
                for x in range(tx, tx + 5):
                    if y == base - h and x in (tx, tx + 4):
                        continue
                    px[x, y] = hill2
        for tx in (60, 250):
            base = int(206 + 8 * math.sin(tx / 41.0 + 1.3))
            for y in range(base - 26, base):
                px[tx + (base - y) // 9, y] = hill
            for k in range(1, 10):
                px[tx + 2 - k, base - 18 - k // 2] = hill
                px[tx + 3 + k, base - 22 - k // 3] = hill
    return img


def build_frame(theme):
    t = THEMES[theme]
    img = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))
    px = img.load()
    panel, edge, dark = hexc(t["panel"]), hexc(t["edge"]), hexc(t["edge_dark"])
    for y in range(SCREEN_H):
        for x in list(range(0, 48)) + list(range(272, SCREEN_W)):
            px[x, y] = panel
        px[46, y], px[47, y] = dark, edge
        px[272, y], px[273, y] = edge, dark
    # ground strip under the last row of the grid (y 222-239)
    g = {k: hexc(v) for k, v in t["ground"].items()}
    for y in range(FLOOR_Y, SCREEN_H):
        for x in range(48, 272):
            if y == FLOOR_Y:
                c = g["top"]
            elif y < FLOOR_Y + 4:
                c = g["mid"] if (x + y) % 5 else g["top"]
            else:
                c = g["dark"] if (x * 3 + y * 7) % 11 else g["mid"]
            px[x, y] = c
    label, txt = hexc(t["label"]), hexc(t["text"])
    text(img, "1UP", 6, 6, label)
    text(img, "LIVES", 6, 200, txt)
    text(img, "HIGH", 278, 6, label)
    text(img, "SCORE", 278, 13, txt)
    text(img, "LEVEL", 278, 40, txt)
    text(img, "GOLD", 278, 70, txt)
    for x in range(278, 316):
        px[x, 100] = dark
    return img


def build_title(theme):
    t = THEMES[theme]
    w, h = 192, 32
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    panel, edge, dark, acc = hexc(t["panel"]), hexc(t["edge"]), hexc(t["edge_dark"]), hexc(t["accent"])
    for y in range(4, 28):
        for x in range(2, w - 2):
            px[x, y] = panel
    for x in range(2, w - 2):
        px[x, 4] = px[x, 27] = edge
        px[x, 5] = px[x, 26] = dark
    for y in range(4, 28):
        px[2, y] = px[w - 3, y] = edge
    title = t["title"]
    tw = text_width(title, 2)
    text(img, title, (w - tw) // 2, 11, hexc(t["text"]), scale=2, shadow=dark)
    # little portraits: hero on the left, guard on the right
    hero = from_map(HEADS[theme]["player"]["side"], pal(t["player"])).resize((16, 10), Image.NEAREST)
    guard = from_map(HEADS[theme]["guard"]["side"], pal(t["guard"])).transpose(Image.FLIP_LEFT_RIGHT).resize((16, 10), Image.NEAREST)
    img.alpha_composite(hero, (8, 11))
    img.alpha_composite(guard, (w - 24, 11))
    for x in (6, w - 7):
        for y in (8, 23):
            px[x, y] = acc
    return img


def build(theme):
    d = os.path.join(OUT, "themes", theme)
    os.makedirs(d, exist_ok=True)
    sheet, rects = pack(build_sprites(theme))
    sheet.save(os.path.join(d, "sheet.png"))
    write_sheet_lua(os.path.join(d, "sheet.lua"), rects)
    build_background(theme).save(os.path.join(d, "background.png"))
    build_frame(theme).save(os.path.join(d, "frame.png"))
    build_title(theme).save(os.path.join(d, "title.png"))
    print("%-10s sheet %dx%d, %d sprites" % (theme, sheet.width, sheet.height, len(rects)))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_font()
    for name in (sys.argv[1:] or list(THEMES)):
        build(name)
