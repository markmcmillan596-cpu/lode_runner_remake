-- Atlas: loads a theme's sprite sheet, background, frame and title banner.
--   local Atlas = require("assets.atlas")
--   local theme = Atlas.load("fall")
--   theme:draw("brick", x, y)                    -- x, y = top-left corner
--   theme:drawFacing("player_run_1", x, y, -1)   -- -1 = facing left (art faces right)
--   theme:tile(col, row, "brick")                -- draw at a grid cell (0-based)
local Atlas = {}

Atlas.THEMES = {"fall", "halloween", "christmas", "winter"}

-- Base resolution is 320x240 (render to a canvas, scale 3x with nearest filtering).
Atlas.SCREEN = {w = 320, h = 240}

-- The original Lode Runner grid: 28 columns x 16 rows, one screen per level.
-- Tiles are 8 wide x 12 tall, so the grid is 224 x 192 px and fits the same
-- 224 px playfield as the other games in the project.
Atlas.TILE_W, Atlas.TILE_H = 8, 12
Atlas.GRID = {x = 48, y = 30, cols = 28, rows = 16}
Atlas.PLAYFIELD = {x = 48, y = 0, w = 224, h = 240}
Atlas.FLOOR_Y = 222          -- top of the ground strip drawn in frame.png
-- The 30 px band above row 0 is open sky: climbing up into it finishes the level.

-- Characters in level files (the classic fan-editor convention).
Atlas.TILES = {
  [" "] = "empty",  ["#"] = "brick",  ["@"] = "bedrock", ["H"] = "ladder",
  ["-"] = "bar",    ["X"] = "trap",   ["S"] = "exit",    ["$"] = "gold",
  ["0"] = "guard",  ["&"] = "player",
}

-- Sprite to draw for each tile kind ("exit" is invisible until all gold is taken).
Atlas.TILE_SPRITE = {brick = "brick", bedrock = "bedrock", ladder = "ladder", bar = "bar",
                     trap = "trap", gold = "gold"}

-- Animations: frame lists and frames per second. Characters face RIGHT in the sheet.
Atlas.ANIM = {
  run      = {frames = {"run_1", "run_2", "run_3", "run_4"}, fps = 10},
  climb    = {frames = {"climb_1", "climb_2"}, fps = 8},
  bar      = {frames = {"bar_1", "bar_2"}, fps = 8},
  fall     = {frames = {"fall"}, fps = 1},
  dig      = {frames = {"dig"}, fps = 1},
  trapped  = {frames = {"trapped_1", "trapped_2"}, fps = 6},           -- guard only
  spawn    = {frames = {"spawn_1", "spawn_2", "spawn_3"}, fps = 6},    -- guard only
  exit     = {frames = {"exit_1", "exit_2"}, fps = 4},
  dig_hole = {frames = {"dig_1", "dig_2", "dig_3", "dig_4"}},           -- spread over DIG_TIME
  fill_hole = {frames = {"fill_1", "fill_2", "fill_3", "fill_4"}},      -- spread over FILL_TIME
}

-- Returns the sprite name for an animation at time t, e.g. Atlas.frame("guard", "run", t).
function Atlas.frame(who, anim, t)
  local a = Atlas.ANIM[anim]
  local i = math.floor(t * (a.fps or 1)) % #a.frames + 1
  return (who and (who .. "_") or "") .. a.frames[i]
end

-- For a hole that takes `duration` seconds to dig or fill: which frame at `elapsed`.
function Atlas.holeFrame(anim, elapsed, duration)
  local f = Atlas.ANIM[anim].frames
  local i = math.min(#f, math.floor(elapsed / duration * #f) + 1)
  return f[i]
end

-- Points (popups exist for these values: pts_75, pts_250, pts_1500).
Atlas.POINTS = {gold = 250, trap_guard = 75, kill_guard = 75, level = 1500}

-- Where to print HUD values (the labels are already in frame.png).
Atlas.LAYOUT = {
  score = {x = 6,   y = 14},
  hi    = {x = 278, y = 22},
  level = {x = 278, y = 48},
  gold  = {x = 278, y = 78},           -- gold left, e.g. draw gold_icon then "x 6"
  lives = {x = 6,   y = 208, step = 9, perRow = 4, rowStep = 9},   -- life_icon (8x8) per spare life
}

-- Text and accent colours that suit each theme's HUD.
Atlas.TEXT = {
  fall      = {1.0, 0.88, 0.66},
  halloween = {1.0, 0.63, 0.25},
  christmas = {1.0, 1.0, 1.0},
  winter    = {0.85, 0.94, 1.0},
}
Atlas.ACCENT = {
  fall      = {0.88, 0.44, 0.11},
  halloween = {1.0, 0.50, 0.06},
  christmas = {0.82, 0.13, 0.19},
  winter    = {0.50, 0.75, 0.94},
}

-- Top-left pixel of a grid cell (0-based col and row).
function Atlas.cellXY(col, row)
  return Atlas.GRID.x + col * Atlas.TILE_W, Atlas.GRID.y + row * Atlas.TILE_H
end

-- 3x5 pixel font (A-Z 0-9 . : - !). Uppercase only.
function Atlas.font()
  local f = love.graphics.newImageFont("assets/font.png", " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:-!")
  f:setFilter("nearest", "nearest")
  return f
end

-- Themes whose art is actually present in assets/themes (handy while some are still being built).
function Atlas.available()
  local list = {}
  for _, n in ipairs(Atlas.THEMES) do
    if love.filesystem.getInfo("assets/themes/" .. n .. "/sheet.png") then list[#list + 1] = n end
  end
  return list
end

local Theme = {}
Theme.__index = Theme

function Theme:draw(name, x, y, r, sx, sy, ox, oy)
  local q = self.quads[name]
  if not q then error("unknown sprite: " .. tostring(name)) end
  love.graphics.draw(self.sheet, q, x, y, r or 0, sx or 1, sy or 1, ox or 0, oy or 0)
end

-- dir = 1 draws the art as it is (facing right), dir = -1 mirrors it (facing left).
-- Either way, x, y stays the top-left corner of the cell the character is in.
function Theme:drawFacing(name, x, y, dir)
  if dir == -1 then
    local w = self.rects[name].w
    self:draw(name, x + w, y, 0, -1, 1)
  else
    self:draw(name, x, y)
  end
end

function Theme:tile(col, row, name)
  local x, y = Atlas.cellXY(col, row)
  self:draw(name, x, y)
end

function Theme:size(name)
  local r = self.rects[name]
  if not r then error("unknown sprite: " .. tostring(name)) end
  return r.w, r.h
end

function Atlas.load(name)
  local dir = "assets/themes/" .. name .. "/"
  local function img(file)
    local i = love.graphics.newImage(dir .. file)
    i:setFilter("nearest", "nearest")
    return i
  end
  local rects = love.filesystem.load(dir .. "sheet.lua")()
  local sheet = img("sheet.png")
  local quads = {}
  local sw, sh = sheet:getDimensions()
  for k, r in pairs(rects) do quads[k] = love.graphics.newQuad(r.x, r.y, r.w, r.h, sw, sh) end
  return setmetatable({
    name = name, sheet = sheet, rects = rects, quads = quads,
    background = img("background.png"), frame = img("frame.png"), title = img("title.png"),
    text = Atlas.TEXT[name] or {1, 1, 1}, accent = Atlas.ACCENT[name] or {1, 1, 1},
  }, Theme)
end

return Atlas
