-- Runner physics: moving, climbing, hanging on bars and falling. No Love2D calls in here,
-- so tests/game_test.py can run it headless.
--
-- Positions are in TILE units (x = column, y = row, top-left of the character's cell),
-- fractional while moving between cells. Rows grow downward. A character is "aligned" when
-- a coordinate sits on a whole tile; walking needs y aligned, ladders need x aligned.
local Runner = {}

-- Tuning knobs, tiles per second. Playtest and adjust these.
Runner.RUN   = 5.0
Runner.CLIMB = 4.0
Runner.BAR   = 4.0
Runner.FALL  = 8.0

local EPS = 1e-4

local function round(v) return math.floor(v + 0.5) end
local function aligned(v) return math.abs(v - round(v)) < EPS end

-- Outside the grid: side walls and the floor are solid, the sky above is empty.
local function cell(lv, c, r)
  if c < 0 or c >= lv.cols or r >= lv.rows then return "bedrock" end
  if r < 0 then return "empty" end
  return lv.cells[r][c]
end
Runner.cell = cell

local function solid(k) return k == "brick" or k == "bedrock" end
local function holdsUp(k) return k == "brick" or k == "bedrock" or k == "ladder" end

function Runner.new(lv)
  return {x = lv.player.col, y = lv.player.row, dir = 1, falling = false, skip = false,
          state = "stand", moved = false, animT = 0}
end

-- Falls toward the floor; stops (grabs) on a ladder or bar, or lands when the cell below holds.
local function fall(p, lv, dt)
  p.falling, p.state = true, "fall"
  local cx = round(p.x)
  -- drift sideways onto the column being fallen through
  local dx = cx - p.x
  local sx = Runner.FALL * dt
  p.x = math.abs(dx) <= sx and cx or p.x + (dx > 0 and sx or -sx)
  local remaining = Runner.FALL * dt
  while remaining > 1e-9 do
    if aligned(p.y) then
      p.y = round(p.y)
      if p.skip then
        p.skip = false
      else
        local here, below = cell(lv, cx, p.y), cell(lv, cx, p.y + 1)
        if here == "ladder" or here == "bar" or holdsUp(below) then
          p.falling = false
          return
        end
      end
    end
    local step = math.min(remaining, math.floor(p.y + EPS) + 1 - p.y)
    p.y = p.y + step
    remaining = remaining - step
  end
end

-- input = {left=, right=, up=, down=} booleans. Advances the runner by dt seconds.
function Runner.step(p, lv, input, dt)
  p.moved = false
  if p.falling then fall(p, lv, dt) ; return end

  local cx = round(p.x)
  local yal = aligned(p.y)
  local r = yal and round(p.y) or nil

  if yal then
    p.y = r
    local here, below = cell(lv, cx, r), cell(lv, cx, r + 1)
    local supported = here == "ladder" or here == "bar" or holdsUp(below)
    if not supported then fall(p, lv, dt); return end
  end

  local wantV = (input.up and "up") or (input.down and "down") or nil
  local vertical = false
  if wantV then
    if yal then
      local here, below, above = cell(lv, cx, r), cell(lv, cx, r + 1), cell(lv, cx, r - 1)
      if wantV == "up" then
        vertical = here == "ladder" and not solid(above)
      elseif not solid(below) then
        if here == "bar" or (here == "ladder" and below ~= "ladder") then
          -- let go: drop (or step off the bottom of a ladder) and fall
          p.skip = true
          fall(p, lv, dt)
          return
        end
        vertical = below == "ladder" or here == "ladder"
      end
    else
      vertical = true          -- already between rows on a ladder: keep going
    end
  end

  if vertical then
    -- line up with the ladder column first
    if not aligned(p.x) then
      local dx = cx - p.x
      local s = Runner.RUN * dt
      p.x = math.abs(dx) <= s and cx or p.x + (dx > 0 and s or -s)
      p.state = "climb"
      return
    end
    p.x = cx
    local remaining = Runner.CLIMB * dt
    local sign = wantV == "up" and -1 or 1
    while remaining > 1e-9 do
      local boundary = sign < 0 and math.ceil(p.y - EPS) - 1 or math.floor(p.y + EPS) + 1
      local step = math.min(remaining, math.abs(boundary - p.y))
      p.y = p.y + sign * step
      remaining = remaining - step
      p.moved = true
      if aligned(p.y) then
        p.y = round(p.y)
        break           -- re-check what is here next frame (top of ladder, bottom, etc.)
      end
    end
    p.state = "climb"
    return
  end

  -- Horizontal movement: only when standing on a whole row.
  local dir = (input.right and 1) or (input.left and -1) or 0
  if dir ~= 0 and yal then
    p.dir = dir
    local hanging = cell(lv, cx, r) == "bar"
    local remaining = (hanging and Runner.BAR or Runner.RUN) * dt
    local travelled = 0
    while remaining > 1e-9 do
      if aligned(p.x) then
        p.x = round(p.x)
        if solid(cell(lv, p.x + dir, r)) then break end
      end
      local boundary = dir > 0 and math.floor(p.x + EPS) + 1 or math.ceil(p.x - EPS) - 1
      local step = math.min(remaining, math.abs(boundary - p.x))
      p.x = p.x + dir * step
      remaining = remaining - step
      travelled = travelled + step
    end
    p.moved = travelled > 0
  end

  -- Pose for drawing.
  local here = yal and cell(lv, round(p.x), r) or "ladder"
  if yal and here == "bar" then p.state = "bar"
  elseif not yal then p.state = "climb"
  elseif here == "ladder" and not p.moved then p.state = "climb"
  elseif p.moved then p.state = "run"
  else p.state = "stand" end
end

return Runner
