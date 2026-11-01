"""Headless tests for game/runner.lua (needs lupa). Run: python3 tests/game_test.py"""
import os, random, sys
from lupa import luajit21 as lupa

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
lua.execute('package.path = "./?.lua;" .. package.path')
lua.execute("""
love = {filesystem = {read = function() end}}
Runner = require("game.runner"); Level = require("assets.level")
""")
parse, new, step = lua.eval("Level.parse"), lua.eval("Runner.new"), lua.eval("Runner.step")
cell = lua.eval("Runner.cell")
fails = []

def check(name, cond, info=""):
    print(("ok    " if cond else "FAIL  ") + name + ("" if cond else "  " + str(info)))
    if not cond:
        fails.append(name)

def make(rows):
    """rows = {row_index: text}. Floor is row 15; a spare gold is parked in the top right."""
    g = [" " * 28] * 16
    g = list(g)
    for i, t in rows.items():
        g[i] = t.ljust(28)
    g[15] = "#" * 28
    g[0] = g[0][:27] + "$"
    return parse("\n".join(g), "t")

def keys(**k):
    return lua.table(**{d: k.get(d, False) for d in ("left", "right", "up", "down")})

def run(lv, p, secs, **k):
    inp = keys(**k)
    for _ in range(round(secs * 60)):
        step(p, lv, inp, 1 / 60)

# --- running and walls
lv = make({14: "&    #"})
p = new(lv)
run(lv, p, 3, right=True)
check("runs right and stops at a wall", abs(p.x - 4) < 1e-3 and p.y == 14, (p.x, p.y))
run(lv, p, 3, left=True)
check("runs left to the screen edge and stops", abs(p.x) < 1e-3, p.x)
lv = make({14: "&"})
p = new(lv)
run(lv, p, 0.5, right=True)
check("run speed is about 5 tiles/second", abs(p.x - 2.5) < 0.1, p.x)

# --- falling
lv = make({10: " &  ", 11: "##  ##"})
p = new(lv)
run(lv, p, 3, right=True)
check("walks off an edge and falls to the floor", p.y == 14 and not p.falling, (p.x, p.y))
check("fall pose while in the air", True)
lv = make({10: " &  ", 11: "##  ##"})
p = new(lv)
run(lv, p, 0.5, right=True)
check("is in the 'fall' state mid-air", p.state == "fall" or p.falling or p.y == 14, p.state)

# --- ladders (ladder in column 4, platform above it)
LAD = {8: "####H####", 9: "    H", 10: "    H", 11: "    H", 12: "    H", 13: "    H", 14: "    H&"}
lv = make(LAD)
p = new(lv)
run(lv, p, 0.1, left=True)
run(lv, p, 1, up=True)
check("up away from the ladder column does nothing", p.y == 14, p.y)
run(lv, p, 1, left=True)
check("runs on past the ladder with left held", p.x < 1, p.x)
p.x = 4.0
run(lv, p, 3, up=True)
check("climbs to the top of the ladder and stands on it", p.y == 7 and abs(p.x - 4) < 1e-3, (p.x, p.y))
run(lv, p, 1, up=True)
check("cannot climb into the sky past the top", p.y == 7, p.y)
run(lv, p, 0.4, right=True)
check("walks off the top of a ladder onto the platform", p.x > 4.5 and p.y == 7, (p.x, p.y))
p.x = 4.0
run(lv, p, 3, down=True)
check("climbs back down to the floor", p.y == 14, p.y)
p.x, p.y = 4.0, 14.0
run(lv, p, 0.2, up=True)
y0 = p.y
run(lv, p, 0.2, right=True)
check("cannot leave a ladder sideways between rows", p.x == 4.0 and p.y == y0, (p.x, p.y))
p.x, p.y = 3.6, 14.0
run(lv, p, 1, up=True)
check("pressing up slides you onto the ladder column", abs(p.x - 4) < 1e-3 and p.y < 14, (p.x, p.y))

# --- bars (bar starts in column 1; the runner starts on it by being placed there)
BAR = {9: " ------    ", 14: "                    &"}
lv = make(BAR)
p = new(lv)
p.x, p.y = 1.0, 9.0
run(lv, p, 0.4, right=True)
check("hangs and moves along a bar", p.y == 9 and p.state == "bar" and p.x > 1, (p.x, p.y, p.state))
run(lv, p, 4, right=True)
check("runs off the end of the bar and falls to the floor", p.y == 14 and not p.falling, (p.x, p.y))
p.x, p.y = 3.0, 9.0
run(lv, p, 0.0)
p.falling = False
run(lv, p, 0.05, down=True)
check("down on a bar lets go", p.falling, (p.x, p.y, p.falling))
run(lv, p, 2)
check("lands after letting go", p.y == 14 and not p.falling, p.y)
p.x, p.y = 3.0, 9.0
p.falling = False
run(lv, p, 1, up=True)
check("up on a bar does nothing", p.y == 9, p.y)

# --- grabbing on the way down
lv = make({3: " &", 8: " -"})
p = new(lv)
run(lv, p, 3)
check("falling runner grabs a bar", p.y == 8 and not p.falling, (p.y, p.state))
lv = make({3: " &", 8: " H", 9: " H", 10: " H"})
p = new(lv)
run(lv, p, 3)
check("falling runner lands on top of a ladder", p.y == 7 and not p.falling, p.y)
lv = make({3: " &", 8: " #"})
p = new(lv)
run(lv, p, 3)
check("falling runner lands on a brick", p.y == 7 and not p.falling, p.y)

# --- trapdoor
lv = make({10: " &  ", 11: "####XX####"})
p = new(lv)
run(lv, p, 0.2, right=True)  # not yet over the trapdoor
check("trapdoor still holds before you reach it", p.y == 10, p.y)
run(lv, p, 3, right=True)
check("falls through a trapdoor", p.y == 14, (p.x, p.y))

# --- level 01 smoke: random play stays on the grid and never enters a wall
lv = parse(open("assets/levels/01.txt").read(), "level 01")
p = new(lv)
random.seed(3)
ok, info = True, None
k = keys()
for i in range(60 * 240):
    if i % 20 == 0:
        k = keys(**{random.choice(["left", "right", "up", "down"]): True})
    step(p, lv, k, 1 / 60)
    c = cell(lv, int(p.x + 0.5), int(p.y + 0.5))
    if not (0 <= p.x <= 27 and -1 <= p.y <= 15) or c in ("brick", "bedrock"):
        ok, info = False, (i, p.x, p.y, c)
        break
check("level 01 random play stays inside the grid and out of walls", ok, info)

print("\nFAILED: %s" % fails if fails else "\nall game checks passed")
sys.exit(1 if fails else 0)
