# Lode Runner asset pack (game 6)

Seasonal art and sound for a Lode Runner-style remake in Love2D. This folder is an
asset pack plus a small viewer, not the game: the game is what you build next with
Claude Code, stage by stage, from the project guide.

All four seasons are built, with identical sprite and sound names so the game code never changes per theme:

| Theme | Title | Hero | Guards | Gold | Bricks | Sound |
| --- | --- | --- | --- | --- | --- | --- |
| fall | Harvest Heist | farmer kid | scarecrows | acorns | clay brick | soft square waves |
| halloween | Candy Heist | trick-or-treater | mummies | wrapped candy | tombstone brick | thin pulse waves, minor scale |
| christmas | Present Heist | elf | nutcrackers | presents | gingerbread with icing joints | glass bells, major scale |
| winter | Frozen Heist | kid in a beanie | snowmen | ice crystals | ice blocks | soft sines, lydian scale |

## Run the viewer

```
love .
```

TAB switches title / level / sprite sheet. T changes season (with the between-level
circle wipe). S plays each effect in turn. M toggles music. E shows the escape ladder.

## What's in the box

```
lode-runner/
  conf.lua, main.lua         asset viewer
  assets/
    atlas.lua                sprites, grid, animations, HUD layout
    level.lua                level loader and terrain drawing
    fx.lua                   weather, dust, sparkles, popups, circle wipe
    sfx.lua, music.lua       sound effects and the optional music loop
    font.png                 3x5 pixel font
    levels/01.txt            sample level
    themes/<season>/         sheet.png + sheet.lua, background, frame, title,
                             music.wav, sfx/*.wav
  tools/
    gen_sprites.py           makes every image (edit art here, then re-run)
    gen_audio.py             makes every sound
    preview_level.py         renders a level to PNG without Love2D
  tests/headless_test.py     runs the Lua code with a stubbed love API
```

## Design decisions (and where they came from)

| Decision | Why |
| --- | --- |
| 28 x 16 grid, one screen per level | The original grid. The whole puzzle is visible at once. |
| 8 x 12 px tiles | 28 x 8 = 224 px, the same playfield as the other games; 12 px tall leaves room for a readable figure. |
| Brick and bedrock look clearly different | Which floors you can dig is the core rule, so it must read at a glance. |
| Trapdoor looks exactly like brick | That is the trick in the original. `trap_hint` exists for a level editor. |
| Holes refill in a lighter "fresh" colour | The original let you watch a hole closing; timing puzzles depend on it. |
| Characters face right, flipped in code | Half the art, and `drawFacing` keeps the top-left corner fixed. |
| Heads stamped onto shared body poses | The farmer and the scarecrow run with the same legs. Fix a pose once, every season follows. |
| Effects first, music optional and off in the viewer | The 1983 game had effects only, each one telling you about a rule. |
| Every effect normalised to the same loudness | Switching season never sounds like a volume change. |
| Music loop wraps its note tails | Seamless by construction, so no seam repair at load time. |

## Level files

28 characters x 16 lines, the convention used by fan-made Lode Runner editors:

| Char | Meaning | Char | Meaning |
| --- | --- | --- | --- |
| space | empty | `-` | hand-over-hand bar |
| `#` | brick (diggable) | `X` | trapdoor (looks like brick, you fall through) |
| `@` | bedrock (not diggable) | `S` | escape ladder (hidden until all gold is taken) |
| `H` | ladder | `$` | gold |
| `0` | guard | `&` | player (exactly one) |

`Level.load` returns the terrain plus separate lists of gold, guards and the player,
and gives a clear error (row and column) for a broken file.

## Using it in the game

```lua
local Atlas, Level = require("assets.atlas"), require("assets.level")
local theme = Atlas.load("fall")
local lv = Level.load("assets/levels/01.txt")
-- in love.draw:
Level.draw(lv, theme, allGoldTaken, t, holes)
theme:drawFacing(Atlas.frame("guard", "run", t), x, y, -1)
```

Draw order: background, `fx:drawAmbient()`, level, gold, characters, `fx:draw()`,
frame, HUD text, `fx:drawWipe()`. Render to a 320 x 240 canvas created with a stencil
(`love.graphics.setCanvas({canvas, stencil = true})`, LOVE 11.x) and scale it 3x.

Timers belong to the game, not the art, so they are not set here. The viewer uses
dig 0.4 s, open 2 s, refill 0.8 s as placeholders; the original's exact timing was not
found in the research, so tune them by playing.

## Changing the art or sound

Edit the maps and palettes in `tools/gen_sprites.py` (or the cues in `tools/gen_audio.py`),
then:

```
python3 tools/gen_sprites.py      # needs Pillow
python3 tools/gen_audio.py        # needs numpy
python3 tests/headless_test.py    # needs lupa
```
