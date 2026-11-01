-- Lode Runner remake. `love .` plays the game; `love . viewer` opens the asset viewer.
local viewerRequested = false
for _, a in pairs(arg or {}) do if a == "viewer" then viewerRequested = true end end
if viewerRequested then require("viewer"); return end

local Atlas  = require("assets.atlas")
local Level  = require("assets.level")
local Runner = require("game.runner")

local SCALE, STEP = 3, 1 / 60
local THEME_NAME  = "fall"

local canvas, theme, lv, player
local t, acc = 0, 0

local function restart()
  lv = Level.load("assets/levels/01.txt")
  player = Runner.new(lv)
end

function love.load()
  love.graphics.setDefaultFilter("nearest", "nearest")
  canvas = love.graphics.newCanvas(Atlas.SCREEN.w, Atlas.SCREEN.h)
  love.graphics.setFont(Atlas.font())
  theme = Atlas.load(THEME_NAME)
  restart()
end

local function readInput()
  local k = love.keyboard.isDown
  return {left = k("left", "a"), right = k("right", "d"), up = k("up", "w"), down = k("down", "s")}
end

function love.update(dt)
  acc = acc + math.min(dt, 0.1)
  while acc >= STEP do                         -- fixed timestep: same feel at any frame rate
    acc = acc - STEP
    t = t + STEP
    Runner.step(player, lv, readInput(), STEP)
    if player.moved or player.falling then player.animT = player.animT + STEP end
  end
end

local function playerSprite()
  local p = player
  if p.state == "fall"  then return "player_fall" end
  if p.state == "stand" then return "player_run_1" end
  local anim = (p.state == "climb" and "climb") or (p.state == "bar" and "bar") or "run"
  -- hold the pose still when not actually moving (standing on a ladder or hanging)
  return Atlas.frame("player", anim, p.moved and p.animT or 0)
end

function love.draw()
  love.graphics.setCanvas({canvas, stencil = true})
  love.graphics.clear(0, 0, 0, 1)
  love.graphics.draw(theme.background, 0, 0)
  Level.draw(lv, theme, false, t)
  for _, g in ipairs(lv.gold) do theme:tile(g.col, g.row, "gold") end
  for _, g in ipairs(lv.guards) do
    local x, y = Atlas.cellXY(g.col, g.row)
    theme:drawFacing("guard_run_1", x, y, -1)
  end
  local x, y = Atlas.cellXY(player.x, player.y)
  theme:drawFacing(playerSprite(), math.floor(x + 0.5), math.floor(y + 0.5), player.dir)
  love.graphics.draw(theme.frame, 0, 0)
  love.graphics.setColor(theme.text)
  love.graphics.print(player.state:upper() .. "  R RESTART", 52, 232)
  love.graphics.setColor(1, 1, 1)
  love.graphics.setCanvas()
  love.graphics.draw(canvas, 0, 0, 0, SCALE, SCALE)
end

function love.keypressed(key)
  if key == "escape" then love.event.quit()
  elseif key == "r" then restart() end
end
