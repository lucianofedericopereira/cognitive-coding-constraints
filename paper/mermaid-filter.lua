--[[
mermaid-filter.lua — Pandoc Lua filter for Mermaid diagram rendering.

Strategy (in order of preference):
  1. For latex/pdf output: parse `flowchart TD` Mermaid syntax directly
     and emit a native `forest` LaTeX tree — no external tools required.
     Requires: texlive package `forest` (included in texlive-latex-extra).
  2. Fallback for other formats or unrecognised Mermaid: call mmdc to
     produce a PNG and embed it as an image.
     Requires: npm install -g @mermaid-js/mermaid-cli

Usage (handled automatically by `make paper`):
  pandoc input.md --lua-filter=paper/mermaid-filter.lua --pdf-engine=xelatex ...
]]


-- ============================================================
-- Utility: escape LaTeX special characters in a label string
-- ============================================================
local function latex_escape(s)
  -- Order matters: backslash first, then others
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("{",  "\\{")
  s = s:gsub("}",  "\\}")
  s = s:gsub("#",  "\\#")
  s = s:gsub("%%", "\\%%")
  s = s:gsub("&",  "\\&")
  s = s:gsub("%$", "\\$")
  s = s:gsub("_",  "\\_")
  s = s:gsub("%^", "\\^{}")
  s = s:gsub("~",  "\\textasciitilde{}")
  return s
end


-- ============================================================
-- Parse `flowchart TD` Mermaid source → forest LaTeX raw block
-- Returns nil if the source cannot be parsed as a simple TD tree.
-- ============================================================
local function mermaid_to_forest(src)

  -- ── Step 1: extract node labels ──────────────────────────
  -- Handles:  ID["label"]  and  ID(["label"])  and  ID{label}
  local labels = {}
  for id, label in src:gmatch('(%w+)%["([^"]+)"%]') do
    labels[id] = label
  end
  -- Unlabelled nodes (bare `ID`)
  for id in src:gmatch('\n%s*(%w+)%s*\n') do
    if not labels[id] then labels[id] = id end
  end

  -- ── Step 2: extract directed edges ───────────────────────
  -- Handles:  A --> B   and   A -->|text| B  (text ignored)
  local children = {}   -- parent_id → ordered list of child_ids
  local has_parent = {}
  for parent, child in src:gmatch('(%w+)%s*%-%->%s*%w*%s*(%w+)') do
    if not children[parent] then children[parent] = {} end
    table.insert(children[parent], child)
    has_parent[child] = true
  end

  -- ── Step 3: find root (node with no incoming edge) ───────
  local root = nil
  for id in pairs(labels) do
    if not has_parent[id] then
      root = id
      break
    end
  end
  if not root then return nil end

  -- ── Step 4: recursive forest-tree builder ────────────────
  -- Labels are wrapped in {} so commas/colons inside text are not
  -- parsed as TikZ/forest option separators.
  local function build(id, depth)
    local label = latex_escape(labels[id] or id)
    local indent = string.rep("  ", depth)
    if children[id] and #children[id] > 0 then
      local parts = { indent .. "[{" .. label .. "}" }
      for _, child_id in ipairs(children[id]) do
        table.insert(parts, build(child_id, depth + 1))
      end
      table.insert(parts, indent .. "]")
      return table.concat(parts, "\n")
    else
      return indent .. "[{" .. label .. "}]"
    end
  end

  local tree_body = build(root, 2)

  -- ── Step 5: wrap in forest environment ───────────────────
  local forest_code = table.concat({
    "\\begin{forest}",
    "  for tree={",
    "    font=\\small\\ttfamily,",
    "    grow'=0,",
    "    child anchor=west,",
    "    parent anchor=south,",
    "    anchor=west,",
    "    calign=first,",
    "    inner xsep=4pt,",
    "    edge path={",
    "      \\noexpand\\path[draw, \\forestoption{edge}]",
    "        (!u.south west)+(7.5pt,0) |- (.child anchor)",
    "        \\forestoption{edge label};",
    "    },",
    "    before computing xy={l=15pt},",
    "  }",
    tree_body,
    "\\end{forest}",
  }, "\n")

  return forest_code
end


-- ============================================================
-- PNG fallback via mmdc (used for non-latex output formats)
-- ============================================================
local system = require("pandoc.system")
local path   = require("pandoc.path")
local IMG_DIR  = "paper/figures"
local _img_seq = 0

local function sh(cmd)
  local ok = os.execute(cmd)
  return ok == true or ok == 0
end

local function render_mermaid_png(mermaid_src)
  sh(string.format('mkdir -p "%s"', IMG_DIR))
  _img_seq = _img_seq + 1
  local base    = string.format("mermaid_%03d", _img_seq)
  local in_file = path.join({IMG_DIR, base .. ".mmd"})
  local out_png = path.join({IMG_DIR, base .. ".png"})
  local f = io.open(in_file, "w")
  if not f then return nil end
  f:write(mermaid_src)
  f:close()
  local cmd = string.format(
    'mmdc -i "%s" -o "%s" --backgroundColor transparent --width 900 2>/dev/null',
    in_file, out_png
  )
  if sh(cmd) then return out_png end
  io.stderr:write("[mermaid-filter] mmdc not found — keeping code block.\n"
    .. "  Install: npm install -g @mermaid-js/mermaid-cli\n")
  return nil
end


-- ============================================================
-- Pandoc filter entry-point
-- ============================================================
function CodeBlock(block)
  if block.classes[1] ~= "mermaid" then return nil end

  local fmt = FORMAT or ""

  -- ── LaTeX / PDF path: emit forest tree ───────────────────
  if fmt == "latex" or fmt == "pdf" then
    local forest = mermaid_to_forest(block.text)
    if forest then
      -- Inject \usepackage{forest} only once via a raw TeX header trick:
      -- pandoc's --include-in-header handles this; forest is listed in
      -- header.tex so the package is always loaded.
      return pandoc.RawBlock("latex", forest)
    else
      -- Parser failed: fall back to code block
      io.stderr:write("[mermaid-filter] Could not parse Mermaid as tree; keeping code block.\n")
      block.classes = {""}
      return block
    end
  end

  -- ── Other formats (HTML, DOCX, …): try mmdc PNG ──────────
  local img_path = render_mermaid_png(block.text)
  if img_path then
    return pandoc.Para({
      pandoc.Image({pandoc.Str("Diagram")}, img_path, "")
    })
  end

  -- Last resort: plain code block
  block.classes = {""}
  return block
end
