-- Seasonal weather, particle effects and the between-level circle wipe.
--   fx = FX.new(theme)                 -- theme from Atlas.load
--   fx:update(dt)
--   fx:drawAmbient()                   -- drifting leaves / embers, right after the background
--   fx:draw()                          -- particles and score popups, after the sprites, before the frame
--   fx:drawWipe()                      -- last of all (covers everything, frame included)
--   fx:dig(x, y)                       dust puff where a brick is dug      (x, y = centre)
--   fx:gold(x, y)                      sparkle when gold is collected
--   fx:crush(x, y)                     debris when a guard is caught by a refilling hole
--   fx:points(x, y, n)                 rising score popup (n = 75, 250, 1500)
--   fx:wipe(cx, cy, onClosed)          circle closes on (cx, cy), calls onClosed, then opens again
--   fx:wiping()                        true while a wipe is running (freeze the game meanwhile)
--   fx:setTheme(theme)                 change season (keeps a running wipe going)
local FX = {}
FX.__index = FX

local PX0, PX1 = 48, 272     -- playfield left / right edge
local rnd = love.math.random

-- Per-theme weather. Kept light: in a puzzle game the level must stay easy to read.
local WEATHER = {
  fall      = {n = 10, vx = {-8, 8},  vy = {14, 26},  sway = 10, sprites = {"amb_1", "amb_2", "amb_3"}},
  halloween = {n = 12, vx = {-6, 6},  vy = {-16, -6}, sway = 6,  sprites = {"amb_1", "amb_2", "amb_3"}},
  christmas = {n = 30, vx = {-4, 4},  vy = {10, 20},  sway = 6,  sprites = {"amb_1", "amb_2", "amb_3"}},
  winter    = {n = 40, vx = {-40, -20}, vy = {30, 60}, sway = 3, sprites = {"amb_1", "amb_2", "amb_3"}},
}

local WIPE_TIME = 0.45       -- seconds to close (and again to open)
local WIPE_MAX = 200         -- radius that uncovers the whole 320x240 screen from anywhere

local function lerp(range) return range[1] + rnd() * (range[2] - range[1]) end

function FX.new(theme)
  local self = setmetatable({theme = theme, parts = {}, amb = {}, wipeT = nil}, FX)
  self.w = WEATHER[theme.name] or WEATHER.fall
  for i = 1, self.w.n do self.amb[i] = self:newAmb(true) end
  return self
end

-- Switch season without interrupting a wipe that is in progress.
function FX:setTheme(theme)
  self.theme, self.parts, self.amb = theme, {}, {}
  self.w = WEATHER[theme.name] or WEATHER.fall
  for i = 1, self.w.n do self.amb[i] = self:newAmb(true) end
end

function FX:newAmb(anywhere)
  local w = self.w
  local a = {sprite = w.sprites[rnd(#w.sprites)], phase = rnd() * 6.28, vx = lerp(w.vx), vy = lerp(w.vy)}
  a.x = PX0 + rnd() * (PX1 - PX0)
  a.y = anywhere and rnd() * 240 or (a.vy > 0 and -8 or 248)
  return a
end

-- sprite may be a name or a list of names (animated over the particle's life).
function FX:emit(sprite, x, y, vx, vy, life, g, fade)
  self.parts[#self.parts + 1] = {sprite = sprite, x = x, y = y, vx = vx, vy = vy, g = g or 0,
                                 life = life, max = life, fade = fade ~= false}
end

function FX:update(dt)
  for i, a in ipairs(self.amb) do
    a.phase = a.phase + dt * 2
    a.x = a.x + (a.vx + math.sin(a.phase) * self.w.sway) * dt
    a.y = a.y + a.vy * dt
    if a.y > 248 or a.y < -12 or a.x < PX0 - 12 or a.x > PX1 + 12 then self.amb[i] = self:newAmb(false) end
  end
  for i = #self.parts, 1, -1 do
    local p = self.parts[i]
    p.life = p.life - dt
    if p.life <= 0 then
      table.remove(self.parts, i)
    else
      p.vy = p.vy + p.g * dt
      p.x, p.y = p.x + p.vx * dt, p.y + p.vy * dt
    end
  end
  if self.wipeT then
    local before = self.wipeT
    self.wipeT = self.wipeT + dt
    if before < WIPE_TIME and self.wipeT >= WIPE_TIME and self.onClosed then self.onClosed() end
    if self.wipeT >= WIPE_TIME * 2 then self.wipeT = nil end
  end
end

function FX:drawAmbient()
  love.graphics.setColor(1, 1, 1, 0.8)
  for _, a in ipairs(self.amb) do self.theme:draw(a.sprite, math.floor(a.x), math.floor(a.y)) end
  love.graphics.setColor(1, 1, 1, 1)
end

function FX:draw()
  for _, p in ipairs(self.parts) do
    local name = p.sprite
    if type(name) == "table" then
      local age = 1 - p.life / p.max
      name = name[math.min(#name, math.floor(age * #name) + 1)]
    end
    love.graphics.setColor(1, 1, 1, p.fade and math.min(1, p.life / (p.max * 0.5)) or 1)
    local w, h = self.theme:size(name)
    self.theme:draw(name, math.floor(p.x - w / 2), math.floor(p.y - h / 2))
  end
  love.graphics.setColor(1, 1, 1, 1)
end

function FX:dig(x, y)
  self:emit({"dust_1", "dust_2", "dust_3"}, x, y - 2, 0, -12, 0.35, 0)
  for _ = 1, 3 do self:emit("debris_" .. rnd(2), x, y, rnd(-30, 30), rnd(-50, -20), 0.4, 180) end
end

function FX:gold(x, y)
  for _ = 1, 8 do self:emit("spark", x + rnd(-4, 4), y + rnd(-4, 4), rnd(-20, 20), rnd(-40, -10), 0.5, 0) end
end

function FX:crush(x, y)
  for _ = 1, 8 do self:emit("debris_" .. rnd(2), x, y, rnd(-60, 60), rnd(-90, -30), 0.6, 220) end
  self:emit({"dust_1", "dust_2", "dust_3"}, x, y, 0, -8, 0.4, 0)
end

function FX:points(x, y, n)
  local name = "pts_" .. n
  if self.theme.rects[name] then self:emit(name, x, y, 0, -14, 1.0, 0, false) end
end

-- The original closed and opened the screen with concentric circles between levels.
function FX:wipe(cx, cy, onClosed)
  self.wipeT, self.wipeX, self.wipeY, self.onClosed = 0, cx, cy, onClosed
end

function FX:wiping() return self.wipeT ~= nil end

-- Needs a stencil buffer: when drawing to a canvas use
--   love.graphics.setCanvas({canvas, stencil = true})        (LOVE 11.x API)
function FX:drawWipe()
  if not self.wipeT then return end
  local t = self.wipeT
  local k = t < WIPE_TIME and 1 - t / WIPE_TIME or (t - WIPE_TIME) / WIPE_TIME
  local r = math.floor(WIPE_MAX * k)
  love.graphics.stencil(function() love.graphics.circle("fill", self.wipeX, self.wipeY, r) end, "replace", 1)
  love.graphics.setStencilTest("equal", 0)
  love.graphics.setColor(0, 0, 0, 1)
  love.graphics.rectangle("fill", 0, 0, 320, 240)
  love.graphics.setStencilTest()
  love.graphics.setColor(1, 1, 1, 1)
end

return FX
