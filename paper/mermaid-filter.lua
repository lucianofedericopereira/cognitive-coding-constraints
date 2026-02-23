--[[
mermaid-filter.lua — Pandoc Lua filter for Mermaid diagram rendering.

Converts fenced ```mermaid code blocks to PNG images embedded in the output.
Falls back to a styled code block if mmdc is not available.

Requirements (one-time):
  npm install -g @mermaid-js/mermaid-cli

Usage (handled automatically by `make paper`):
  pandoc input.md --lua-filter=paper/mermaid-filter.lua --pdf-engine=xelatex -o out.pdf
]]

local system = require("pandoc.system")
local path   = require("pandoc.path")

-- Directory where generated images are written (relative to repo root).
local IMG_DIR  = "paper/figures"
local _img_seq = 0  -- counter for unique filenames


--- Run a shell command; return true on success, false otherwise.
local function sh(cmd)
  local ok = os.execute(cmd)
  -- os.execute returns true/0 on success in Lua 5.1/5.2; use both forms
  return ok == true or ok == 0
end


--- Ensure a directory exists.
local function mkdir(dir)
  sh(string.format('mkdir -p "%s"', dir))
end


--- Try to render *mermaid_src* to a PNG file.
-- Returns the output path on success, nil on failure.
local function render_mermaid(mermaid_src)
  mkdir(IMG_DIR)

  _img_seq = _img_seq + 1
  local base    = string.format("mermaid_%03d", _img_seq)
  local in_file = path.join({IMG_DIR, base .. ".mmd"})
  local out_png = path.join({IMG_DIR, base .. ".png"})

  -- Write Mermaid source to temp file
  local f = io.open(in_file, "w")
  if not f then
    io.stderr:write("[mermaid-filter] Cannot write to " .. in_file .. "\n")
    return nil
  end
  f:write(mermaid_src)
  f:close()

  -- Try mmdc (Mermaid CLI)
  local cmd = string.format(
    'mmdc -i "%s" -o "%s" --backgroundColor transparent --width 900 2>/dev/null',
    in_file, out_png
  )

  if sh(cmd) then
    return out_png
  else
    io.stderr:write(
      "[mermaid-filter] mmdc not found or failed — keeping code block.\n"
      .. "  Install: npm install -g @mermaid-js/mermaid-cli\n"
    )
    return nil
  end
end


--- Pandoc filter entry-point: intercept CodeBlock elements.
function CodeBlock(block)
  -- Match both `mermaid` and ` ```mermaid ` annotations
  if not (block.classes[1] == "mermaid") then
    return nil  -- leave unchanged
  end

  local img_path = render_mermaid(block.text)

  if img_path then
    -- Replace the code block with a centred figure
    local img = pandoc.Image(
      {pandoc.Str("Diagram")},  -- alt text
      img_path,                  -- src
      ""                         -- title
    )
    -- Wrap in a Para so it appears as a block
    return pandoc.Para({img})
  else
    -- Graceful fallback: keep the code block but change class so it
    -- renders as plain text (no syntax highlighting confusion)
    block.classes = {""}
    return block
  end
end
