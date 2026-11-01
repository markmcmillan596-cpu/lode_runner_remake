"""Runs the Lua side of the pack without Love2D, using a stubbed `love` API.

    pip install lupa      (embedded LuaJIT, the same Lua dialect Love2D uses)
    python3 tests/headless_test.py

Checks: every theme loads, every sprite name the Lua code asks for exists on every
sheet, every sound file exists, the sample level parses, the viewer runs 20 seconds
of frames through every key (including the circle-wipe theme switch), and the level
parser rejects broken files with a clear message.
"""
import os
import sys
import wave
from PIL import Image
from lupa import luajit21 as lupa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
drawn, problems = [], []


def img_dims(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return Image.open(path).size


def wav_ok(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with wave.open(path) as w:
        assert w.getnframes() > 0, path
    return True


lua.globals().py_img_dims = img_dims
lua.globals().py_wav_ok = wav_ok
lua.globals().py_exists = os.path.exists
lua.globals().py_read = lambda p: open(p).read() if os.path.exists(p) else None
lua.globals().py_drawn = lambda name: drawn.append(name)

lua.execute(r"""
package.path = "./?.lua;" .. package.path
local function obj(t) return setmetatable(t or {}, {__index = function() return function() end end}) end
love = {}
love.graphics = obj{
  newImage = function(p)
    local w, h = py_img_dims(p)
    return obj{getDimensions = function() return w, h end, path = p}
  end,
  newQuad = function(x, y, w, h, sw, sh)
    assert(x + w <= sw and y + h <= sh, "quad outside sheet")
    return obj{}
  end,
  newCanvas = function() return obj{} end,
  newImageFont = function(p) py_img_dims(p); return obj{} end,
  draw = function(img, q) end,
  stencil = function(fn) fn() end,
}
love.filesystem = obj{
  load = function(p) local f = assert(loadfile(p)); return f end,
  read = function(p) return py_read(p) end,
  getInfo = function(p) if py_exists(p) then return {} end end,
}
local function source(p)
  py_wav_ok(p)
  local looping, playing = false, false
  local s
  s = obj{clone = function() return source(p) end,
          setLooping = function(_, v) looping = v end, isLooping = function() return looping end,
          play = function() playing = true end, stop = function() playing = false end,
          isPlaying = function() return playing end}
  return s
end
love.audio = obj{newSource = function(p) return source(p) end}
love.math = {random = function(a, b)
  if not a then return math.random() end
  if not b then return math.random(a) end
  return math.random(a, b) end}
love.event = obj{}
love.keyboard = obj{isDown = function() return false end}
""")

Atlas = lua.eval('require("assets.atlas")')
Level = lua.eval('require("assets.level")')
SFX = lua.eval('require("assets.sfx")')

available = [t for t in ["fall", "halloween", "christmas", "winter"]
             if os.path.exists("assets/themes/%s/sheet.png" % t)]
print("themes present:", available)

# Every sprite the Lua code can request, built from the same tables the code uses.
needed = set(lua.eval("""(function()
  local A = require("assets.atlas")
  local out = {}
  for _, s in pairs(A.TILE_SPRITE) do out[#out+1] = s end
  for _, who in ipairs({"player", "guard"}) do
    for _, anim in ipairs({"run", "climb", "bar", "fall", "dig"}) do
      for _, f in ipairs(A.ANIM[anim].frames) do out[#out+1] = who .. "_" .. f end
    end
  end
  for _, anim in ipairs({"trapped", "spawn"}) do
    for _, f in ipairs(A.ANIM[anim].frames) do out[#out+1] = "guard_" .. f end
  end
  for _, anim in ipairs({"exit", "dig_hole", "fill_hole"}) do
    for _, f in ipairs(A.ANIM[anim].frames) do out[#out+1] = f end
  end
  for _, n in pairs(A.POINTS) do out[#out+1] = "pts_" .. n end
  for _, s in ipairs({"life_icon", "gold_icon", "carry", "spark", "debris_1", "debris_2",
                      "dust_1", "dust_2", "dust_3", "amb_1", "amb_2", "amb_3", "trap_hint"}) do
    out[#out+1] = s
  end
  return out
end)()""").values())

for t in available:
    theme = Atlas.load(t)
    names = set(theme.rects.keys())
    missing = needed - names
    if missing:
        problems.append("%s sheet is missing: %s" % (t, sorted(missing)))
    extra = names - needed
    if extra:
        print("  %s: sprites not referenced by the Lua code: %s" % (t, sorted(extra)))
    SFX.load(t)                                  # raises if any wav is missing
    assert os.path.exists("assets/themes/%s/music.wav" % t)
    print("  %s: %d sprites, %d sounds OK" % (t, len(names), len(list(SFX.NAMES.values()))))

lv = Level.load("assets/levels/01.txt")
print("level 01: %d gold, %d guards, player at %d,%d" % (len(lv.gold), len(lv.guards), lv.player.col, lv.player.row))
exits = sum(1 for r in range(16) for c in range(28) if lv.cells[r][c] == "exit")
assert exits > 0, "level 01 has no escape ladder"

# Broken levels must fail with a readable message.
bad = {
    "too few rows": "#" * 28 + "\n",
    "unknown char": "\n".join(["&$" + " " * 26] + ["Z" + " " * 27] + [" " * 28] * 14),
    "no player": "\n".join(["$" + " " * 27] + [" " * 28] * 15),
    "two players": "\n".join(["&&$" + " " * 25] + [" " * 28] * 15),
}
for label, text in bad.items():
    ok, msg = lua.eval('function(t) return pcall(require("assets.level").parse, t, "test") end')(text)
    if ok:
        problems.append("level parser accepted a broken level (%s)" % label)
    else:
        print("  rejects %-12s -> %s" % (label, str(msg).split(": ", 1)[-1]))

# Run the viewer: load, then 20 s of frames with every key pressed along the way.
lua.execute('dofile("viewer.lua")')
lua.execute("love.load()")
keys = ["tab", "tab", "tab", "e", "m", "m"] + ["s"] * 15 + ["t"] + ["e"]
frames = 1200
for i in range(frames):
    lua.globals().love.update(1 / 60)
    lua.globals().love.draw()
    if i % 40 == 0 and keys:
        lua.globals().love.keypressed(keys.pop(0))
current = lua.eval("""(function()
  for i = 1, 60 do
    local n, v = debug.getupvalue(love.draw, i)
    if n == nil then break end
    if n == "theme" then return v.name end
  end
end)()""")
print("viewer: %d frames, all keys pressed, final theme %s" % (frames, current))
if len(available) > 1 and current == available[0]:
    problems.append("theme switch (T + circle wipe) did not change the theme")

# Run the game (main.lua) for a few seconds of frames, also with the viewer switch.
lua.execute('dofile("main.lua")')
lua.execute("love.load()")
for i in range(300):
    lua.globals().love.update(1 / 60)
    lua.globals().love.draw()
lua.globals().love.keypressed("r")
print("game: 300 frames ran, restart OK")

if problems:
    print("\nPROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("\nall checks passed")
