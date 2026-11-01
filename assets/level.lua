-- Level loader: turns a 28x16 text file into data the game can use.
--   local Level = require("assets.level")
--   local lv = Level.load("assets/levels/01.txt")
--   lv.cells[row][col]   -> "empty", "brick", "bedrock", "ladder", "bar", "trap" or "exit"
--   lv.gold              -> list of {col=, row=}
--   lv.guards            -> list of {col=, row=}
--   lv.player            -> {col=, row=}
-- Rows and columns are 0-based to match Atlas.cellXY. Gold, guards and the player
-- are taken OUT of the terrain (their cells become "empty"), because they move.
--
-- This is the idea Lode Runner was built on: one set of rules, any layout.
-- A level is only data, so a level editor is just a program that writes this file.
local Atlas = require("assets.atlas")
local Level = {}

function Level.parse(text, name)
  name = name or "level"
  local G = Atlas.GRID
  local lines = {}
  for line in (text .. "\n"):gmatch("(.-)\r?\n") do lines[#lines + 1] = line end
  if lines[#lines] == "" then lines[#lines] = nil end         -- the file's final newline
  while #lines > G.rows and lines[#lines] == "" do lines[#lines] = nil end
  if #lines ~= G.rows then
    error(("%s: expected %d rows, found %d"):format(name, G.rows, #lines))
  end
  local lv = {cols = G.cols, rows = G.rows, cells = {}, gold = {}, guards = {}, player = nil}
  for r = 0, G.rows - 1 do
    local line = lines[r + 1]
    if #line > G.cols then error(("%s: row %d is %d wide (max %d)"):format(name, r, #line, G.cols)) end
    line = line .. string.rep(" ", G.cols - #line)       -- editors often trim trailing spaces
    lv.cells[r] = {}
    for c = 0, G.cols - 1 do
      local ch = line:sub(c + 1, c + 1)
      local kind = Atlas.TILES[ch]
      if not kind then error(("%s: unknown character %q at row %d, col %d"):format(name, ch, r, c)) end
      if kind == "gold" then
        lv.gold[#lv.gold + 1] = {col = c, row = r}; kind = "empty"
      elseif kind == "guard" then
        lv.guards[#lv.guards + 1] = {col = c, row = r}; kind = "empty"
      elseif kind == "player" then
        if lv.player then error(name .. ": more than one player (&)") end
        lv.player = {col = c, row = r}; kind = "empty"
      end
      lv.cells[r][c] = kind
    end
  end
  if not lv.player then error(name .. ": no player (&)") end
  if #lv.gold == 0 then error(name .. ": no gold ($)") end
  return lv
end

function Level.load(path)
  local text = love.filesystem.read(path)
  if not text then error("cannot read " .. path) end
  return Level.parse(text, path)
end

-- Draws the terrain. showExit = true once all gold is collected.
-- holes (optional): holes[row][col] = sprite name to draw instead of the brick
-- (a dig_ or fill_ frame), or false for a fully open hole (draw nothing).
function Level.draw(lv, theme, showExit, t, holes)
  for r = 0, lv.rows - 1 do
    for c = 0, lv.cols - 1 do
      local kind = lv.cells[r][c]
      local hole = holes and holes[r] and holes[r][c]
      if hole ~= nil then
        if hole then theme:tile(c, r, hole) end
      elseif kind == "exit" then
        if showExit then theme:tile(c, r, Atlas.frame(nil, "exit", t or 0)) end
      elseif Atlas.TILE_SPRITE[kind] then
        theme:tile(c, r, Atlas.TILE_SPRITE[kind])
      end
    end
  end
end

return Level
