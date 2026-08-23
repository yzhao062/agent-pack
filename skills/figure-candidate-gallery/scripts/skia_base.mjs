// skia_base.mjs -- shared house style for figure-candidate-gallery (skia-canvas).
//
// Import from every skia schematic candidate so cards, chips, arrows, and graphs
// share one palette and one export path. The shipped visual-system and
// archetype contracts are the quality floor.
//
// Requires skia-canvas, which Node's ESM loader resolves by walking up from
// THIS file's own directory (NODE_PATH does not work for ESM bare imports).
// Copy this helper into figure-src/candidates/<run-id>/ beside the candidate
// scripts. Each candidate imports './skia_base.mjs'. The bare skia-canvas
// import resolves upward to figure-src/node_modules. Install once with:
//   npm i skia-canvas        (run under figure-src/)
//
// The canvas is built in POINTS (1/72 inch), so the PDF exports as a correct
// physical-size vector and the PNG upscales via export density. Lay out in
// points.

import { Canvas, FontLibrary } from 'skia-canvas'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

// ---- House palette: role -> {accent, fill}. Defaults; palette.json wins. ---
export const PALETTE = {
  data:        { accent: '#B26B00', fill: '#FBEFD8' }, // amber
  fm:          { accent: '#1F5FBF', fill: '#E0EAFB' }, // blue
  harness:     { accent: '#B23A48', fill: '#F9E0E4' }, // red
  measurement: { accent: '#2D6A4F', fill: '#DDF1E3' }, // green
  bad:         { accent: '#B23A48', fill: '#F9E0E4' }, // hazard / leak
}
export const INK = '#1A1A1A'
export const SUBTLE = '#666666'
export const HAIRLINE = '#D0D0D0'

// ---- Run configuration ----------------------------------------------------
// Tree prep writes palette.json into the run directory beside this file's
// copy. figure_base.py reads the same file, so a batch that mixes matplotlib
// and skia shares one map and one font. Without it the defaults above apply.
// A missing file is the documented default case. A file that exists is
// validated in full before either export is touched, and any problem throws:
// falling back to the shipped colors would render a batch off-palette while
// every check still agreed, since both helpers would agree on the same wrong
// defaults. The rules match figure_base.load_run_config exactly.
export let FONT = 'sans'
const RUN_CONFIG = join(dirname(fileURLToPath(import.meta.url)), 'palette.json')
let raw = null
try {
  raw = readFileSync(RUN_CONFIG, 'utf-8')
} catch (e) {
  // Only a missing file is the documented default case. A directory in
  // its place, or a permission problem, must surface: figure_base raises
  // on those, so swallowing them here would load shipped colors on one
  // half of a batch while the other half refused to start.
  if (e.code !== 'ENOENT') {
    throw new Error(`${RUN_CONFIG}: cannot read run config: ${e.message}`)
  }
}
if (raw !== null) {
  let cfg
  try {
    cfg = JSON.parse(raw)
  } catch (e) {
    throw new Error(`${RUN_CONFIG}: cannot parse run config: ${e.message}`)
  }
  const isObject = v => v !== null && typeof v === 'object' && !Array.isArray(v)
  if (!isObject(cfg)) throw new Error(`${RUN_CONFIG}: run config must be an object`)
  const font = 'font' in cfg ? cfg.font : FONT
  if (font !== 'sans' && font !== 'serif') {
    throw new Error(`${RUN_CONFIG}: font must be "sans" or "serif", got ${JSON.stringify(font)}`)
  }
  const palette = 'palette' in cfg ? cfg.palette : {}
  if (!isObject(palette)) throw new Error(`${RUN_CONFIG}: palette must be an object`)
  const merged = {}
  for (const [role, tones] of Object.entries(palette)) {
    // Assigning '__proto__' here would set this object's prototype rather
    // than store a role, so the role would vanish while figure_base kept
    // it. Reject it in both helpers rather than let one half go off-palette.
    if (role === '__proto__') throw new Error(`${RUN_CONFIG}: '__proto__' is not a usable role name`)
    if (!isObject(tones)) throw new Error(`${RUN_CONFIG}: role "${role}" must be an object`)
    const bad = Object.entries(tones).filter(([, v]) => typeof v !== 'string').map(([k]) => k)
    if (bad.length) throw new Error(`${RUN_CONFIG}: role "${role}" tones ${bad} must be strings`)
    const tone = { ...(PALETTE[role] || {}), ...tones }
    const missing = ['accent', 'fill'].filter(k => !(k in tone))
    if (missing.length) throw new Error(`${RUN_CONFIG}: new role "${role}" needs ${missing}`)
    merged[role] = tone
  }
  Object.assign(PALETTE, merged)
  FONT = font
}

const PT = 72

// When the run font is 'serif', register a Palatino-like family under the
// 'body' alias to match a mathpazo document.
let bodyRegistered = false
if (FONT === 'serif') {
  try {
    FontLibrary.use('body', [
      'C:/Windows/Fonts/pala.ttf',
      'C:/Windows/Fonts/palatinolinotype.ttf',
      '/usr/share/fonts/**/P052*.ttf',
      '/usr/share/fonts/**/*Palladio*.ttf',
    ])
    bodyRegistered = true
  } catch (e) { /* fall through to the generic serif stack below */ }
}

// FONT_STACK is what every text helper writes into ctx.font. It is derived
// from the run font, so a failed 'body' registration still renders serif
// rather than silently falling back to the sans stack while FONT still
// reads 'serif'. matplotlib resolves an equivalent family for the same run.
export const FONT_STACK = FONT === 'serif'
  ? `${bodyRegistered ? 'body, ' : ''}Palatino Linotype, P052, DejaVu Serif, serif`
  : 'Arial, Helvetica, DejaVu Sans, sans-serif'

export function makeCanvas(wIn, hIn) {
  const canvas = new Canvas(wIn * PT, hIn * PT)
  const ctx = canvas.getContext('2d')
  ctx.textBaseline = 'middle'
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  ctx.fillStyle = 'white'
  ctx.fillRect(0, 0, wIn * PT, hIn * PT)   // opaque ground for the PNG
  return { canvas, ctx, W: wIn * PT, H: hIn * PT }
}

export function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

// A filled, accent-bordered card in a role color. Returns the center point.
export function card(ctx, x, y, w, h, role, { r = 7, lw = 1.4 } = {}) {
  const p = PALETTE[role] || PALETTE.data
  roundRect(ctx, x, y, w, h, r)
  ctx.fillStyle = p.fill
  ctx.fill()
  ctx.lineWidth = lw
  ctx.strokeStyle = p.accent
  ctx.stroke()
  return { cx: x + w / 2, cy: y + h / 2 }
}

// A pill-shaped label chip centered on (cx, cy).
export function chip(ctx, cx, cy, label, role, { pad = 7, fs = 9 } = {}) {
  const p = PALETTE[role] || PALETTE.data
  ctx.font = `${fs}px ${FONT_STACK}`
  const w = ctx.measureText(label).width + pad * 2
  const h = fs + pad
  roundRect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
  ctx.fillStyle = p.fill
  ctx.fill()
  ctx.lineWidth = 1
  ctx.strokeStyle = p.accent
  ctx.stroke()
  ctx.fillStyle = INK
  ctx.textAlign = 'center'
  ctx.fillText(label, cx, cy + 0.5)
}

// A line with a filled arrowhead; dashed for failure or leakage edges.
export function arrow(ctx, x1, y1, x2, y2,
                      { color = INK, lw = 1.25, head = 5.5, dashed = false } = {}) {
  ctx.save()
  ctx.strokeStyle = color
  ctx.fillStyle = color
  ctx.lineWidth = lw
  ctx.setLineDash(dashed ? [4, 3] : [])
  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()
  const a = Math.atan2(y2 - y1, x2 - x1)
  const back = head
  const wing = head * 0.48
  ctx.setLineDash([])
  ctx.beginPath()
  ctx.moveTo(x2, y2)
  ctx.lineTo(x2 - back * Math.cos(a) + wing * Math.sin(a),
             y2 - back * Math.sin(a) - wing * Math.cos(a))
  ctx.lineTo(x2 - back * Math.cos(a) - wing * Math.sin(a),
             y2 - back * Math.sin(a) + wing * Math.cos(a))
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

// Shared warning glyph for leak, failure, defer, or below-chance cues. Always
// use this rather than drawing a local triangle, so every schematic in a batch
// carries the same hazard mark. size is the triangle height in points.
export function hazard(ctx, x, y,
                       { size = 9, color = PALETTE.bad.accent, fill = 'white',
                         lw = 1.05 } = {}) {
  const h = size
  const w = size * 1.08
  ctx.save()
  ctx.translate(x, y)
  ctx.beginPath()           // apex up; white fill so it reads on any background
  ctx.moveTo(0, -h / 2)
  ctx.lineTo(w / 2, h / 2)
  ctx.lineTo(-w / 2, h / 2)
  ctx.closePath()
  ctx.fillStyle = fill
  ctx.fill()
  ctx.lineWidth = lw
  ctx.strokeStyle = color
  ctx.lineJoin = 'round'
  ctx.stroke()
  ctx.strokeStyle = color   // bang: vertical stroke (upper) + dot (lower)
  ctx.lineWidth = Math.max(0.8, lw)
  ctx.beginPath()
  ctx.moveTo(0, -h * 0.16)
  ctx.lineTo(0, h * 0.18)
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(0, h * 0.32, Math.max(0.75, size * 0.075), 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.restore()
}

// Plain text label. Centered by default; pass align/baseline to change.
export function label(ctx, text, x, y,
                      { fs = 9, color = INK, align = 'center',
                        baseline = 'middle', weight = '' } = {}) {
  ctx.font = `${weight ? weight + ' ' : ''}${fs}px ${FONT_STACK}`
  ctx.fillStyle = color
  ctx.textAlign = align
  ctx.textBaseline = baseline
  ctx.fillText(text, x, y)
}

// Edge label on a small white plate so it stays legible where it crosses a line.
export function edgeLabel(ctx, text, x, y, { fs = 7.5, color = SUBTLE } = {}) {
  ctx.font = `${fs}px ${FONT_STACK}`
  const w = ctx.measureText(text).width + 6
  const hh = fs + 4
  roundRect(ctx, x - w / 2, y - hh / 2, w, hh, 3)
  ctx.save()
  ctx.globalAlpha = 0.92
  ctx.fillStyle = 'white'
  ctx.fill()
  ctx.restore()
  ctx.fillStyle = color
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, x, y)
}

// A labeled graph node: a circle (agents) or a small role card (stores, tools).
export function node(ctx, x, y, text, role,
                     { r = 16, shape = 'circle', fs = 9 } = {}) {
  ctx.font = `${fs}px ${FONT_STACK}`
  const p = PALETTE[role] || PALETTE.data
  if (shape === 'card') {
    const w = Math.max(r * 2.6, ctx.measureText(text).width + 16)
    const hh = r * 1.6
    card(ctx, x - w / 2, y - hh / 2, w, hh, role, { r: 6 })
  } else {
    ctx.beginPath()
    ctx.arc(x, y, r, 0, Math.PI * 2)
    ctx.fillStyle = p.fill
    ctx.fill()
    ctx.lineWidth = 1.4
    ctx.strokeStyle = p.accent
    ctx.stroke()
  }
  label(ctx, text, x, y, { fs })
}

// Convenience wrapper for a typed node-link graph. Draws edges first (trimmed
// to node boundaries, dashed + hazard for anomalous edges) then nodes on top.
//   nodes: [{ id, x, y, label, role, shape, r }]
//   edges: [{ from, to, label, dashed, hazard }]
export function nodeLinkGraph(ctx, { nodes, edges = [] }, { nodeR = 16 } = {}) {
  const byId = {}
  for (const n of nodes) byId[n.id] = n
  for (const e of edges) {
    const a = byId[e.from]
    const b = byId[e.to]
    if (!a || !b) continue
    const dx = b.x - a.x
    const dy = b.y - a.y
    const L = Math.hypot(dx, dy) || 1
    const ux = dx / L
    const uy = dy / L
    const ra = a.r || nodeR
    const rb = b.r || nodeR
    const x1 = a.x + ux * ra
    const y1 = a.y + uy * ra
    const x2 = b.x - ux * (rb + 2)
    const y2 = b.y - uy * (rb + 2)
    arrow(ctx, x1, y1, x2, y2, {
      dashed: !!e.dashed,
      color: e.hazard ? PALETTE.bad.accent : INK,
      lw: e.hazard ? 1.5 : 1.25,
    })
    if (e.label) edgeLabel(ctx, e.label, (x1 + x2) / 2, (y1 + y2) / 2)
    if (e.hazard) hazard(ctx, (x1 + x2) / 2, (y1 + y2) / 2 - 9, { size: 8 })
  }
  for (const n of nodes) {
    node(ctx, n.x, n.y, n.label, n.role || 'data',
         { r: n.r || nodeR, shape: n.shape || 'circle' })
  }
}

export async function saveCanvas({ canvas }, stem, outdir) {
  const pdf = join(outdir, stem + '.pdf')
  const png = join(outdir, stem + '.png')
  // toFile is the current API; saveAs is the deprecated older name. Bind to
  // whichever the installed skia-canvas exposes.
  const write = (canvas.toFile || canvas.saveAs).bind(canvas)
  await write(pdf)                       // vector, correct physical size
  await write(png, { density: 3 })       // about 216 dpi raster preview
  console.log('wrote', pdf)
  console.log('wrote', png)
}
