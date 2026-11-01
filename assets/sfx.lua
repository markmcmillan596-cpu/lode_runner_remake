-- Sound effects. One WAV per name per theme (assets/themes/<theme>/sfx/).
--   local sfx = SFX.load("fall")
--   sfx:play("gold")
--   sfx:play("gold", 1.0 + streak * 0.05)    -- optional pitch
--   sfx:loop("fall") ... sfx:stop("fall")    -- the falling whistle repeats until you land
-- Every effect was normalised to the same loudness by tools/gen_audio.py,
-- so switching season does not change the volume.
local SFX = {}
SFX.__index = SFX

SFX.NAMES = {
  "dig",            -- player digs a hole
  "fill",           -- a hole closes (players learn to listen for this)
  "gold",           -- gold collected
  "all_gold",       -- last gold collected: the escape ladder appears
  "fall",           -- falling (loop it, stop it on landing)
  "trapped",        -- a guard drops into a hole
  "guard_die",      -- a guard is crushed by a refilling hole
  "guard_spawn",    -- a guard reappears at the top
  "player_die",     -- caught by a guard, or trapped in a refilled hole
  "level_start", "level_clear", "extra_life", "game_over", "pause", "select",
}

function SFX.load(theme)
  local self = setmetatable({src = {}, playing = {}, volume = 1}, SFX)
  for _, n in ipairs(SFX.NAMES) do
    self.src[n] = love.audio.newSource("assets/themes/" .. theme .. "/sfx/" .. n .. ".wav", "static")
  end
  return self
end

-- Clones the source so rapid repeats overlap instead of cutting each other off.
function SFX:play(name, pitch)
  local s = self.src[name]
  if not s then return end
  s = s:clone()
  s:setVolume(self.volume)
  s:setPitch(pitch or 1)
  s:play()
  self.playing[name] = s
  return s
end

-- Plays a sound on repeat until stop(name). Does nothing if it is already looping.
function SFX:loop(name)
  local s = self.playing[name]
  if s and s:isPlaying() and s:isLooping() then return end
  s = self:play(name)
  if s then s:setLooping(true) end
end

-- Stops the most recent copy of a sound.
function SFX:stop(name)
  local s = self.playing[name]
  if s then s:stop(); self.playing[name] = nil end
end

return SFX
