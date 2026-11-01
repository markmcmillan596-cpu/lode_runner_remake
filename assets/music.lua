-- Optional background music: one seamless 16-bar loop per theme (assets/themes/<theme>/music.wav).
--   local music = Music.load("fall")
--   music:play()
--   music:pause() / music:resume() / music:stop()
--   music:toggleMute()
-- The 1983 original had no music at all, only effects, so the player could listen for
-- holes closing and plan in peace. Try your game both ways and decide.
local Music = {}
Music.__index = Music

Music.VOLUME = 0.30        -- kept under the effects, which carry the gameplay information

function Music.load(theme)
  local src = love.audio.newSource("assets/themes/" .. theme .. "/music.wav", "stream")
  src:setLooping(true)          -- tools/gen_audio.py wraps note tails, so the loop is seamless
  src:setVolume(Music.VOLUME)
  return setmetatable({src = src, muted = false}, Music)
end

function Music:play()   self.src:play() end
function Music:pause()  self.src:pause() end
function Music:resume() self.src:play() end
function Music:stop()   self.src:stop() end

function Music:toggleMute()
  self.muted = not self.muted
  self.src:setVolume(self.muted and 0 or Music.VOLUME)
  return self.muted
end

return Music
