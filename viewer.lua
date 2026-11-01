-- Asset viewer for the Lode Runner pack. Not the game: a way to see and hear every asset.
--   TAB    title / level / sprite sheet view
--   T      next theme (with the between-level circle wipe)
--   S      play the next sound effect          M   music on / off (off by default, like 1983)
--   E      show / hide the escape ladder       ESC quit
local Atlas = require("assets.atlas")
local Level = require("assets.level")
local FX    = require("assets.fx")
local SFX   = require("assets.sfx")
local Music = require("assets.music")

local SCALE = 3
local DIG_TIME, OPEN_TIME, FILL_TIME = 0.4, 2.0, 0.8   -- name the timers (see the research doc)

local canvas, font, themes, ti, theme, fx, sfx, music, lv
local view, views = 1, {"title", "level", "sheet"}
local t, sfxIndex, lastSfx, showExit, musicOn = 0, 0, "", false, false

local function loadTheme(name)
  if music then music:stop() end
  theme, sfx, music = Atlas.load(name), SFX.load(name), Music.load(name)
  if fx then fx:setTheme(theme) else fx = FX.new(theme) end
  if musicOn then music:play() end
end

function love.load()
  love.graphics.setDefaultFilter("nearest", "nearest")
  canvas = love.graphics.newCanvas(Atlas.SCREEN.w, Atlas.SCREEN.h)
  font = Atlas.font()
  love.graphics.setFont(font)
  themes = Atlas.available()
  ti = 1
  lv = Level.load("assets/levels/01.txt")
  loadTheme(themes[ti])
end

-- A demo hole beside the player that is dug, stays open, then refills, forever.
-- Returns the holes table Level.draw understands: a sprite name, or false for open.
local function demoHole()
  local c, r = lv.player.col + 1, lv.player.row + 1
  local k = t % (DIG_TIME + OPEN_TIME + FILL_TIME + 1)
  local name
  if k < DIG_TIME then name = Atlas.holeFrame("dig_hole", k, DIG_TIME)
  elseif k < DIG_TIME + OPEN_TIME then name = false
  elseif k < DIG_TIME + OPEN_TIME + FILL_TIME then name = Atlas.holeFrame("fill_hole", k - DIG_TIME - OPEN_TIME, FILL_TIME)
  else return nil end
  return {[r] = {[c] = name}}
end

function love.update(dt)
  t = t + dt
  fx:update(dt)
end

local function drawHUD()
  local L = Atlas.LAYOUT
  love.graphics.setColor(theme.text)
  love.graphics.print("12500", L.score.x, L.score.y)
  love.graphics.print("50000", L.hi.x, L.hi.y)
  love.graphics.print("001", L.level.x, L.level.y)
  love.graphics.setColor(1, 1, 1)
  theme:draw("gold_icon", L.gold.x, L.gold.y)
  love.graphics.setColor(theme.text)
  love.graphics.print("X " .. #lv.gold, L.gold.x + 10, L.gold.y + 2)
  love.graphics.setColor(1, 1, 1)
  for i = 0, 4 do
    theme:draw("life_icon", L.lives.x + (i % L.lives.perRow) * L.lives.step,
               L.lives.y + math.floor(i / L.lives.perRow) * L.lives.rowStep)
  end
end

local function drawLevel()
  Level.draw(lv, theme, showExit, t, demoHole())
  for _, g in ipairs(lv.gold) do theme:tile(g.col, g.row, "gold") end
  for i, g in ipairs(lv.guards) do
    local x, y = Atlas.cellXY(g.col, g.row)
    local anims = {"run", "trapped", "bar"}
    theme:drawFacing(Atlas.frame("guard", anims[(i - 1) % 3 + 1], t), x, y, -1)
    if i == 1 then theme:draw("carry", x + 2, y - 4) end
  end
  local x, y = Atlas.cellXY(lv.player.col, lv.player.row)
  theme:drawFacing(Atlas.frame("player", "run", t), x, y, 1)
end

function love.draw()
  love.graphics.setCanvas({canvas, stencil = true})
  love.graphics.clear(0, 0, 0, 1)
  love.graphics.draw(theme.background, 0, 0)
  fx:drawAmbient()
  if views[view] == "level" then
    drawLevel()
  elseif views[view] == "title" then
    love.graphics.draw(theme.title, 64, 60)
    love.graphics.setColor(theme.text)
    love.graphics.print("TAB VIEW  T THEME  S SOUND  M MUSIC", 92, 110)
    love.graphics.setColor(1, 1, 1)
  else
    love.graphics.draw(theme.sheet, 32, 40)
  end
  fx:draw()
  love.graphics.draw(theme.frame, 0, 0)
  drawHUD()
  love.graphics.setColor(theme.text)
  love.graphics.print(theme.name:upper() .. "  " .. lastSfx:upper(), 52, 232)
  love.graphics.setColor(1, 1, 1)
  fx:drawWipe()
  love.graphics.setCanvas()
  love.graphics.draw(canvas, 0, 0, 0, SCALE, SCALE)
end

function love.keypressed(key)
  if key == "escape" then love.event.quit()
  elseif key == "tab" then view = view % #views + 1; sfx:play("select")
  elseif key == "e" then showExit = not showExit; if showExit then sfx:play("all_gold") end
  elseif key == "m" then
    musicOn = not musicOn
    if musicOn then music:play() else music:stop() end
  elseif key == "s" then
    sfxIndex = sfxIndex % #SFX.NAMES + 1
    lastSfx = SFX.NAMES[sfxIndex]
    sfx:play(lastSfx)
    local x, y = Atlas.cellXY(lv.player.col, lv.player.row)
    if lastSfx == "dig" then fx:dig(x + 12, y + 18)
    elseif lastSfx == "gold" then fx:gold(x + 4, y + 6); fx:points(x + 4, y - 4, 250)
    elseif lastSfx == "guard_die" then fx:crush(x + 4, y + 6) end
  elseif key == "t" and #themes > 1 then
    local x, y = Atlas.cellXY(lv.player.col, lv.player.row)
    fx:wipe(x + 4, y + 6, function() ti = ti % #themes + 1; loadTheme(themes[ti]) end)
  end
end
