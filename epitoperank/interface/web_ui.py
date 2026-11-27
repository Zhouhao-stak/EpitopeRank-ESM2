"""EpitopeRank web UI - Modern AI Scientific Workspace.

Redesigned as an interactive multi-agent analysis platform with:
- 仪表盘 with real-time project status
- AI 流水线 visualization with agent workflow
- Results 探索r with filtering and search
- Independent chart management
- 基因-level exploration

Backend API remains unchanged (FastAPI endpoints in epitoperank/api/app.py).
Frontend uses vanilla JS SPA architecture for zero-build deployment.
"""

from __future__ import annotations

from fastapi.responses import HTMLResponse

_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="icon" type="image/png" href="/assets/logo.png">
<script>
(function(){
  try {
    var pref = localStorage.getItem('epitoperank.theme') || 'light';
    var dark = pref === 'dark' || (pref === 'system' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    if (localStorage.getItem('epitoperank.sidebar') === 'compact') {
      document.documentElement.classList.add('sidebar-compact');
    }
  } catch (e) {}
})();
</script>
<style>
/* ==========================================================================
   EpitopeRank · Immuno-Lab design system
   One consolidated stylesheet (replaces the stacked legacy theme layers).
   Palette: teal (splicing / ESM-2) -> sky -> indigo (AI), rose for
   immunogenic signal, on calm slate surfaces. Light + dark themes.
   字体策略：只引用系统自带字体，不打包任何字体文件。
   ========================================================================== */
:root, html[data-theme="light"] {
  color-scheme: light;
  --bg: #f2f5f9;
  --bg-glow-a: rgba(20,184,166,.10);
  --bg-glow-b: rgba(99,102,241,.08);
  --surface: #ffffff;
  --surface-2: #f6f8fb;
  --surface-3: #edf1f7;
  --surface-hover: #f2f6fb;
  --border: #e3e8ef;
  --border-strong: #cdd5e0;
  --text: #0f172a;
  --text-secondary: #475569;
  --text-muted: #6b7a90;
  --accent: #0d9488;
  --accent-hover: #0f766e;
  --accent-strong: #115e59;
  --accent-soft: rgba(13,148,136,.09);
  --accent-ring: rgba(13,148,136,.22);
  --ai: #6366f1;
  --ai-soft: rgba(99,102,241,.10);
  --sky: #0284c7;
  --sky-soft: rgba(2,132,199,.10);
  --secondary: #059669;
  --success-soft: rgba(5,150,105,.10);
  --warning: #c2710c;
  --warning-soft: rgba(217,119,6,.11);
  --danger: #e11d48;
  --danger-soft: rgba(225,29,72,.09);
  --brand-grad: linear-gradient(135deg,#14b8a6 0%,#0ea5e9 52%,#6366f1 100%);
  --btn-primary-bg: linear-gradient(180deg,#14a394 0%,#0d9488 100%);
  --btn-primary-hover: linear-gradient(180deg,#0f978a 0%,#0b8076 100%);
  --btn-primary-fg: #ffffff;
  --btn-primary-shadow: 0 1px 2px rgba(13,148,136,.25), 0 6px 16px -6px rgba(13,148,136,.55);
  --input-bg: #ffffff;
  --table-head: #f7f9fc;
  --row-hover: #f3f8fc;
  --topbar-bg: rgba(242,245,249,.80);
  --overlay: rgba(15,23,42,.42);
  --sidebar-bg: linear-gradient(185deg,#0b1628 0%,#0c1a30 55%,#101a36 100%);
  --sidebar-text: #a9b6cb;
  --sidebar-strong: #f8fafc;
  --sidebar-muted: #5f6f88;
  --sidebar-line: rgba(255,255,255,.06);
  --sidebar-hover: rgba(255,255,255,.05);
  --sidebar-active: rgba(45,212,191,.13);
  --sidebar-active-line: rgba(94,234,212,.32);
  --hero-bg: radial-gradient(120% 140% at 0% 0%, #0f2b46 0%, #0b1f36 45%, #121a3d 100%);
  --scroll-thumb: #c5cfdc;
  --scroll-thumb-hover: #9fb0c5;
  /* legacy tokens still referenced by inline styles across the markup/JS */
  --black: var(--text);
  --white: var(--surface);
  --gray-900: var(--text);
  --gray-700: var(--text-secondary);
  --gray-500: var(--text-muted);
  --gray-300: var(--border);
  --gray-100: var(--surface-2);
  --font-sans: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, Roboto, Arial, sans-serif;
  --font-display: "Segoe UI Variable Display", "Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
  --font-mono: "Cascadia Code", "Cascadia Mono", "JetBrains Mono", ui-monospace, "SF Mono", Consolas, monospace;
  --fs-xs: 12px; --fs-sm: 13px; --fs-base: 14px; --fs-xl: 28px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-5: 24px; --space-6: 32px;
  --radius-sm: 9px;
  --radius: 14px;
  --radius-lg: 20px;
  --shadow-xs: 0 1px 2px rgba(15,23,42,.05);
  --shadow-sm: 0 1px 3px rgba(15,23,42,.06), 0 1px 2px rgba(15,23,42,.04);
  --shadow: 0 10px 28px -10px rgba(15,23,42,.16), 0 2px 6px rgba(15,23,42,.05);
  --shadow-lg: 0 30px 70px -18px rgba(15,23,42,.35);
  --ease: cubic-bezier(.16,1,.3,1);
  --motion-ease: cubic-bezier(.16,1,.3,1);
  --sidebar-w: 248px;
}
html[data-theme="dark"] {
  color-scheme: dark;
  --bg: #070b15;
  --bg-glow-a: rgba(45,212,191,.07);
  --bg-glow-b: rgba(129,140,248,.08);
  --surface: #0e1525;
  --surface-2: #121b2e;
  --surface-3: #18223a;
  --surface-hover: #152036;
  --border: #1e2a42;
  --border-strong: #2b3a58;
  --text: #e7edf7;
  --text-secondary: #a5b2c7;
  --text-muted: #7586a0;
  --accent: #2dd4bf;
  --accent-hover: #5eead4;
  --accent-strong: #99f6e4;
  --accent-soft: rgba(45,212,191,.10);
  --accent-ring: rgba(45,212,191,.28);
  --ai: #818cf8;
  --ai-soft: rgba(129,140,248,.13);
  --sky: #38bdf8;
  --sky-soft: rgba(56,189,248,.12);
  --secondary: #34d399;
  --success-soft: rgba(52,211,153,.12);
  --warning: #fbbf24;
  --warning-soft: rgba(251,191,36,.12);
  --danger: #fb7185;
  --danger-soft: rgba(251,113,133,.12);
  --btn-primary-bg: linear-gradient(180deg,#3ee0cb 0%,#22c3ae 100%);
  --btn-primary-hover: linear-gradient(180deg,#6aeedb 0%,#2dd4bf 100%);
  --btn-primary-fg: #04201c;
  --btn-primary-shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 20px -8px rgba(45,212,191,.55);
  --input-bg: #0b1220;
  --table-head: #111a2c;
  --row-hover: #131d31;
  --topbar-bg: rgba(7,11,21,.78);
  --overlay: rgba(2,6,15,.66);
  --sidebar-bg: linear-gradient(185deg,#060a14 0%,#070d1b 60%,#0a1024 100%);
  --sidebar-line: rgba(255,255,255,.05);
  --hero-bg: radial-gradient(120% 140% at 0% 0%, #0d2a3f 0%, #0a1a2e 45%, #141a40 100%);
  --scroll-thumb: #26334d;
  --scroll-thumb-hover: #34466a;
  --shadow-xs: 0 1px 2px rgba(0,0,0,.35);
  --shadow-sm: 0 1px 3px rgba(0,0,0,.4);
  --shadow: 0 14px 34px -12px rgba(0,0,0,.6);
  --shadow-lg: 0 34px 80px -16px rgba(0,0,0,.75);
}

/* ---------- Base ---------- */
* { box-sizing: border-box; margin: 0; padding: 0; }
html { background: var(--bg); }
body {
  font-family: var(--font-sans); font-size: var(--fs-base); line-height: 1.6; color: var(--text);
  background: var(--bg);
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}
h1, h2, h3 { font-family: var(--font-display); color: var(--text); font-weight: 650; letter-spacing: -.02em; }
strong, b { font-weight: 650; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
code { font-family: var(--font-mono); font-size: .92em; padding: 1px 6px; border-radius: 6px; background: var(--surface-3); color: var(--text); }
::selection { background: var(--accent-ring); color: var(--text); }
* { scrollbar-width: thin; scrollbar-color: var(--scroll-thumb) transparent; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scroll-thumb); border-radius: 999px; border: 3px solid transparent; background-clip: padding-box; }
::-webkit-scrollbar-thumb:hover { background: var(--scroll-thumb-hover); border: 3px solid transparent; background-clip: padding-box; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 6px; }
.app { display: flex; min-height: 100vh; }

/* ---------- Sidebar ---------- */
.sidebar {
  width: var(--sidebar-w); position: fixed; inset: 0 auto 0 0; z-index: 100;
  background: var(--sidebar-bg); border-right: 1px solid var(--sidebar-line);
  overflow-y: auto; overflow-x: hidden; padding-bottom: 20px; isolation: isolate;
  display: flex; flex-direction: column;
  transition: transform .22s var(--ease), visibility .22s;
}
.sidebar::after { content: ""; position: absolute; inset: auto -40% -10% -40%; height: 260px; z-index: -1; pointer-events: none;
  background: radial-gradient(closest-side, rgba(45,212,191,.12), transparent); }
.sidebar :focus-visible { outline-color: #5eead4; }
.brand { display: flex; align-items: center; gap: 12px; padding: 22px 20px 20px; border-bottom: 1px solid var(--sidebar-line); min-height: 78px; }
.brand-mark { flex: none; width: 40px; height: 40px; border-radius: 11px; display: grid; place-items: center; overflow: hidden;
  background: transparent;
  box-shadow: 0 6px 18px -4px rgba(14,165,233,.45); }
.brand-mark img { width: 40px; height: 40px; display: block; object-fit: contain; }
.brand-text { min-width: 0; }
.brand-name { font-family: var(--font-display); font-size: 18px; font-weight: 700; letter-spacing: -.02em; color: var(--sidebar-strong); line-height: 1.2; white-space: nowrap; }
.brand-tagline { margin-top: 3px; font-size: 11px; line-height: 1.4; color: var(--sidebar-text); opacity: .8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-section { padding: 18px 0 4px; }
.nav-label { padding: 0 22px; margin-bottom: 6px; font-size: 11px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--sidebar-muted); white-space: nowrap; }
.nav-item {
  position: relative; z-index: 1; display: flex; align-items: center; gap: 12px;
  width: calc(100% - 24px); margin: 2px 12px; padding: 10px 12px; min-height: 42px;
  border: 0; border-radius: 10px; background: transparent; color: var(--sidebar-text);
  font: 500 14px/1.3 var(--font-sans); text-align: left; cursor: pointer; white-space: nowrap; overflow: hidden;
  transition: color .18s ease, background .18s ease;
}
.nav-item svg { width: 19px; height: 19px; flex: none; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; transition: transform .25s var(--ease), color .18s; }
.nav-item:hover { color: var(--sidebar-strong); background: var(--sidebar-hover); }
.nav-item:hover svg { transform: translateX(2px); }
.nav-item.active { color: var(--sidebar-strong); background: transparent; }
.nav-item.active svg { color: #5eead4; }
.nav-fluid-marker {
  position: absolute; left: 12px; top: 0; width: calc(100% - 24px); height: 42px; z-index: 0; pointer-events: none;
  border-radius: 10px; background: linear-gradient(100deg, rgba(45,212,191,.18), rgba(99,102,241,.10));
  border: 1px solid var(--sidebar-active-line); box-shadow: 0 6px 20px -8px rgba(45,212,191,.45);
  transition: transform .42s var(--ease), height .25s var(--ease), width .32s var(--ease);
}
.nav-fluid-marker::before { content: ""; position: absolute; left: -1px; top: 10px; bottom: 10px; width: 3px; border-radius: 0 3px 3px 0; background: #5eead4; box-shadow: 0 0 12px #5eead4; }
.sidebar-foot { margin-top: auto; padding: 14px 20px 0; font-size: 11px; color: var(--sidebar-muted); white-space: nowrap; display: flex; align-items: center; gap: 8px; }
.sidebar-foot .pulse { width: 7px; height: 7px; border-radius: 50%; background: #34d399; box-shadow: 0 0 0 3px rgba(52,211,153,.15); flex: none; }

/* compact (icon-only) sidebar on desktop widths */
@media (min-width: 769px) {
  html.sidebar-compact { --sidebar-w: 76px; }
  html.sidebar-compact .brand { padding: 20px 19px; justify-content: center; }
  html.sidebar-compact .brand-text,
  html.sidebar-compact .nav-label,
  html.sidebar-compact .sidebar-foot span:not(.pulse) { display: none; }
  html.sidebar-compact .nav-section { padding-top: 14px; border-top: 1px solid var(--sidebar-line); margin-top: 6px; }
  html.sidebar-compact .nav-section:first-of-type { border-top: 0; margin-top: 0; }
  html.sidebar-compact .nav-item { font-size: 0; justify-content: center; padding: 10px 0; gap: 0; }
  html.sidebar-compact .nav-item:hover svg { transform: scale(1.08); }
  html.sidebar-compact .sidebar-foot { justify-content: center; padding-inline: 0; }
}

/* ---------- Main + topbar ---------- */
.main { margin-left: var(--sidebar-w); flex: 1; min-width: 0; min-height: 100vh;  }
.topbar {
  position: sticky; top: 0; z-index: 50; height: 64px; display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 0 32px; background: var(--topbar-bg); border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.topbar-left { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
#current-project {
  display: inline-flex; align-items: center; gap: 8px; min-width: 0; max-width: 46vw;
  padding: 6px 12px 6px 10px; border-radius: 999px; border: 1px solid var(--border); background: var(--surface);
  font-size: 13px !important; font-weight: 550; color: var(--text) !important; box-shadow: var(--shadow-xs);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
#current-project::before { content: ""; flex: none; width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.icon-btn {
  flex: none; width: 36px; height: 36px; display: inline-grid; place-items: center; padding: 0;
  border-radius: 10px; border: 1px solid var(--border); background: var(--surface); color: var(--text-secondary);
  cursor: pointer; box-shadow: var(--shadow-xs); transition: color .18s, border-color .18s, background .18s, transform .18s var(--ease);
}
.icon-btn:hover { color: var(--accent); border-color: var(--accent-ring); background: var(--accent-soft); }
.icon-btn:active { transform: scale(.94); }
.icon-btn svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.theme-toggle .ico-moon { display: none; }
html[data-theme="dark"] .theme-toggle .ico-sun { display: none; }
html[data-theme="dark"] .theme-toggle .ico-moon { display: block; }
.topbar-actions { display: flex; gap: 10px; align-items: center; }
.content { max-width: 1480px; margin: 0 auto; padding: 30px 32px 64px; }
.content:focus { outline: none; }

/* ---------- Page header ---------- */
.page { display: none; }
.page.active { display: block; }
.workspace-heading { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; margin-bottom: 26px; }
.workspace-heading h1 { font-size: 28px; line-height: 1.25; font-weight: 700; letter-spacing: -.03em; }
.workspace-heading p { margin-top: 6px; max-width: 76ch; font-size: 14px; color: var(--text-secondary); }
.workspace-tag {
  display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; padding: 6px 12px; border-radius: 999px;
  font-size: 12px; font-weight: 600; color: var(--accent); background: var(--accent-soft); border: 1px solid var(--accent-ring);
}
.workspace-tag::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* ---------- Cards & grid ---------- */
.grid { display: grid; gap: 20px; }
.grid > * { min-width: 0; }
.grid-2 { grid-template-columns: repeat(2, minmax(0,1fr)); }
.grid-3 { grid-template-columns: repeat(3, minmax(0,1fr)); }
.grid-4 { grid-template-columns: repeat(4, minmax(0,1fr)); }
.card, .chart-container {
  position: relative; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-sm);
  transition: border-color .15s ease;
}
.card:hover { border-color: var(--border-strong); }
.card-title { font-size: 14px; font-weight: 650; color: var(--text); }
.chart-container { margin-bottom: 24px; }
.filters { display: flex; gap: 22px; flex-wrap: wrap; margin-bottom: 24px; }
.filter-group { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }
.filter-label { font-size: 11px; font-weight: 650; letter-spacing: .08em; text-transform: uppercase; color: var(--text-muted); }

/* dashboard stat tiles */
.stat-card { padding: 20px 22px; overflow: hidden; }
.stat-card .stat-icon {
  position: absolute; top: 18px; right: 18px; width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center;
  color: var(--accent); background: var(--accent-soft);
}
.stat-card .stat-icon svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.stat-card.tone-sky .stat-icon { color: var(--sky); background: var(--sky-soft); }
.stat-card.tone-rose .stat-icon { color: var(--danger); background: var(--danger-soft); }
.stat-card.tone-ai .stat-icon { color: var(--ai); background: var(--ai-soft); }
.stat-card::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: var(--accent); opacity: .85; }
.stat-card.tone-sky::after { background: var(--sky); }
.stat-card.tone-rose::after { background: var(--danger); }
.stat-card.tone-ai::after { background: var(--ai); }
#stat-samples, #stat-events, #stat-significant {
  font-family: var(--font-display); font-size: 34px !important; font-weight: 700 !important; letter-spacing: -.03em;
  color: var(--text) !important; font-variant-numeric: tabular-nums; line-height: 1.15;
}

/* ---------- Hero / start guide ---------- */
.start-guide {
  position: relative; isolation: isolate; overflow: hidden; display: grid; grid-template-columns: minmax(0,1.25fr) minmax(0,1fr);
  align-items: center; gap: 36px; margin: 0 0 28px; padding: 38px 40px; min-height: 300px;
  border-radius: var(--radius-lg); background: var(--hero-bg); color: #e6f4f1;
  border: 1px solid rgba(255,255,255,.06); box-shadow: 0 24px 50px -24px rgba(11,31,54,.7);
}

.start-guide::after {
  content: ""; position: absolute; inset: 0; z-index: -2; pointer-events: none; opacity: .5;
  background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 32px 32px; -webkit-mask-image: radial-gradient(ellipse at 70% 40%, #000 20%, transparent 75%); mask-image: radial-gradient(ellipse at 70% 40%, #000 20%, transparent 75%);
}
.start-guide > div, .start-guide ol { position: relative; z-index: 1; }
.hero-eyebrow { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 14px; padding: 5px 12px; border-radius: 999px;
  font-size: 12px; font-weight: 600; letter-spacing: .04em; color: #99f6e4; background: rgba(45,212,191,.10); border: 1px solid rgba(94,234,212,.25); }
.hero-eyebrow::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #5eead4; box-shadow: 0 0 10px #5eead4; }
.start-guide h2 { font-size: clamp(26px, 2.6vw, 36px); line-height: 1.2; font-weight: 700; letter-spacing: -.03em; color: #ffffff; max-width: 15em; text-wrap: balance; }
.start-guide h2 em { font-style: normal; background: linear-gradient(90deg,#5eead4,#7dd3fc 50%,#a5b4fc); -webkit-background-clip: text; background-clip: text; color: transparent; }
.start-guide p { margin: 14px 0 24px; max-width: 34em; font-size: 14px; line-height: 1.75; color: #b6c8d6; }
.start-guide .btn { margin: 0 10px 8px 0; }
.start-guide .btn-primary { background: linear-gradient(180deg,#5eead4,#2dd4bf); color: #042f2b; box-shadow: 0 10px 26px -10px rgba(45,212,191,.8); }
.start-guide .btn-primary:hover { background: linear-gradient(180deg,#99f6e4,#5eead4); color: #042f2b; }
.start-guide .btn-secondary { background: rgba(255,255,255,.06); color: #e2f3f0; border-color: rgba(255,255,255,.18); }
.start-guide .btn-secondary:hover { background: rgba(255,255,255,.12); color: #fff; border-color: rgba(255,255,255,.32); }
.start-guide ol {
  list-style: none; display: grid; gap: 14px; align-self: end; padding: 20px 22px; border-radius: var(--radius);
  background: rgba(10,25,44,.82); border: 1px solid rgba(255,255,255,.12);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
}
.start-guide li { display: flex; gap: 14px; align-items: flex-start; font-size: 12px; line-height: 1.5; color: #9fb4c4; }
.start-guide li b { flex: none; width: 28px; height: 28px; border-radius: 9px; display: grid; place-items: center; font-size: 12px; font-weight: 700;
  color: #5eead4; background: rgba(45,212,191,.12); border: 1px solid rgba(94,234,212,.22); font-variant-numeric: tabular-nums; }
.start-guide strong { display: block; margin-bottom: 2px; font-size: 14px; font-weight: 600; color: #f1f5f9; }
.hero-art { position: absolute; right: 0; top: 0; width: 58%; height: 100%; z-index: 0; pointer-events: none; opacity: .9; }
.hero-art .exon { fill: rgba(45,212,191,.16); stroke: #5eead4; stroke-width: 1.4; }
.hero-art .exon.alt { fill: rgba(129,140,248,.14); stroke: #a5b4fc; stroke-dasharray: 4 4; }
.hero-art .intron { stroke: rgba(148,163,184,.45); stroke-width: 1.4; fill: none; }
.hero-art .arc { fill: none; stroke: rgba(125,211,252,.55); stroke-width: 1.4; }
.hero-art .arc.skip { stroke: #5eead4; stroke-width: 1.8; }
.hero-art .signal { fill: none; stroke: #99f6e4; stroke-width: 2; stroke-linecap: round; stroke-dasharray: 22 520; stroke-dashoffset: -120; }
.hero-art .bead { fill: #0b1f36; stroke: #7dd3fc; stroke-width: 1.5; }
.hero-art .bead.hot { fill: #fb7185; stroke: #fecdd3; }
.hero-art .bond { stroke: rgba(125,211,252,.55); stroke-width: 1.4; fill: none; }
.hero-art .groove { fill: none; stroke: rgba(165,180,252,.55); stroke-width: 1.6; stroke-dasharray: 3 5; }
.hero-art text { font: 600 10px var(--font-mono); fill: rgba(203,213,225,.55); letter-spacing: .08em; }
@keyframes spliceFlow { to { stroke-dashoffset: -538; } }
@keyframes beadPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.25); } }

/* ---------- Buttons ---------- */
.btn {
  position: relative; isolation: isolate; overflow: hidden; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  min-height: 38px; padding: 8px 16px; border-radius: 10px; border: 1px solid transparent; cursor: pointer;
  font: 600 13px/1.2 var(--font-sans); letter-spacing: .01em; white-space: nowrap;
  transition: background .18s, border-color .18s, color .18s, box-shadow .2s, transform .18s var(--ease);
}
.btn:active:not(:disabled) { transform: scale(.97); }
.btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }
.btn-sm { min-height: 32px; padding: 6px 12px; font-size: 12.5px; border-radius: 9px; }
.btn-primary { background: var(--btn-primary-bg); color: var(--btn-primary-fg); box-shadow: var(--btn-primary-shadow); }
.btn-primary:hover:not(:disabled) { background: var(--btn-primary-hover); color: var(--btn-primary-fg); transform: translateY(-1px); }
.btn-secondary { background: var(--surface); color: var(--text); border-color: var(--border-strong); box-shadow: var(--shadow-xs); }
.btn-secondary:hover:not(:disabled) { color: var(--accent); border-color: var(--accent-ring); background: var(--accent-soft); }
.btn-danger { background: var(--danger-soft); color: var(--danger); border-color: transparent; }
.btn-danger:hover:not(:disabled) { background: var(--danger); color: #fff; }
.btn[aria-busy="true"] { cursor: progress; padding-right: 36px; }
.btn[aria-busy="true"]::after { content: ""; position: absolute; right: 12px; top: calc(50% - 6px); width: 12px; height: 12px; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: requestSpin .7s linear infinite; }
.press-wave { position: absolute; z-index: -1; pointer-events: none; width: 160px; height: 160px; border-radius: 50%; background: currentColor; opacity: .14; transform: translate(-50%,-50%) scale(0); animation: pressWave .5s var(--ease) forwards; }
@keyframes pressWave { to { transform: translate(-50%,-50%) scale(2); opacity: 0; } }
@keyframes requestSpin { to { transform: rotate(360deg); } }

/* ---------- Status pills ---------- */
.status { display: inline-flex; align-items: center; gap: 7px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; border: 1px solid transparent; white-space: nowrap; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); flex: none; }
.status-running { color: var(--accent); background: var(--accent-soft); border-color: var(--accent-ring); }
.status-running .status-dot { background: var(--accent); animation: dotPulse 1.6s ease-in-out infinite; }
.status-completed { color: var(--secondary); background: var(--success-soft); border-color: transparent; }
.status-completed .status-dot { background: var(--secondary); }
.status-waiting { color: var(--text-secondary); background: var(--surface-3); border-color: var(--border); }
@keyframes dotPulse { 0%,100% { box-shadow: 0 0 0 0 var(--accent-ring); } 50% { box-shadow: 0 0 0 5px transparent; } }
.hero-chip { padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; color: var(--text-secondary); background: var(--accent-soft); border: 1px solid var(--accent-ring); }

/* ---------- Forms ---------- */
input, select, textarea, .search-input {
  flex: 1; min-width: 0; padding: 9px 12px; font: 400 14px/1.45 var(--font-sans); color: var(--text);
  background: var(--input-bg); border: 1px solid var(--border-strong); border-radius: var(--radius-sm); caret-color: var(--accent);
  transition: border-color .18s, box-shadow .18s, background-color .3s;
}
input:hover, select:hover, textarea:hover { border-color: var(--text-muted); }
input:focus, select:focus, textarea:focus, .search-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-ring); }
input::placeholder, textarea::placeholder { color: var(--text-muted); opacity: 1; }
input[type="checkbox"], input[type="radio"] { flex: 0 0 16px; width: 16px; height: 16px; min-height: auto; padding: 0; accent-color: var(--accent); cursor: pointer; box-shadow: none; }
input[type="file"] { display: none; }
select { cursor: pointer; }
select option { color: var(--text); background: var(--surface); }
textarea { resize: vertical; }
input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus { -webkit-text-fill-color: var(--text); -webkit-box-shadow: 0 0 0 1000px var(--input-bg) inset; transition: background-color 9999s ease-out; }
#upload-modal input, #project-name, #analysis-query { color: var(--text) !important; background: var(--input-bg) !important; border-color: var(--border-strong) !important; }
.search-bar { display: flex; gap: 12px; margin-bottom: 22px; }
.search-input { padding: 11px 14px 11px 40px;
  background: var(--input-bg) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round'><circle cx='11' cy='11' r='7'/><path d='M20 20l-3.5-3.5'/></svg>") no-repeat 13px center; }
.checkbox-group { display: flex; gap: 8px; flex-wrap: wrap; }
.checkbox-label { display: inline-flex; align-items: center; gap: 8px; padding: 6px 11px; border-radius: 999px; font-size: 13px; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); cursor: pointer; transition: all .18s; }
.checkbox-label:hover { color: var(--text); border-color: var(--accent-ring); background: var(--accent-soft); }
.checkbox-label:has(input:checked) { color: var(--accent); border-color: var(--accent-ring); background: var(--accent-soft); }
.checkbox-label select { margin-left: 6px; }
details > summary { cursor: pointer; }
details[open] > :not(summary) { animation: detailReveal .24s var(--ease); }
@keyframes detailReveal { from { opacity: .3; transform: translateY(-4px); } to { opacity: 1; transform: none; } }

/* ---------- Segmented controls ---------- */
.lang-toggle, .seg { display: inline-flex; align-items: center; gap: 2px; padding: 3px; border-radius: 10px; background: var(--surface-3); border: 1px solid var(--border); }
.lang-toggle button, .seg button { border: 0; background: transparent; color: var(--text-secondary); font: 600 12px/1 var(--font-sans); padding: 7px 11px; border-radius: 7px; cursor: pointer; white-space: nowrap; transition: background .18s, color .18s, box-shadow .18s; }
.lang-toggle button:hover, .seg button:hover { color: var(--text); }
.lang-toggle button.active, .seg button.active { background: var(--surface); color: var(--accent); box-shadow: var(--shadow-sm); }
.quick-switch { gap: 10px; color: var(--text-secondary); }
.quick-switch kbd { padding: 1px 6px; border-radius: 6px; border: 1px solid var(--border-strong); background: var(--surface-2); font: 600 10.5px var(--font-mono); color: var(--text-muted); }

/* ---------- Tables ---------- */
.table-container { overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow-sm); }
table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; font-variant-numeric: tabular-nums; }
thead { background: var(--table-head); }
th { position: sticky; top: 0; z-index: 1; text-align: left; padding: 11px 14px; font-size: 11.5px; font-weight: 650; letter-spacing: .04em; text-transform: uppercase; color: var(--text-muted); background: var(--table-head); border-bottom: 1px solid var(--border); white-space: nowrap; }
td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-secondary); }
tr:last-child td { border-bottom: 0; }
tbody tr { transition: background-color .15s; }
tbody tr:hover { background: var(--row-hover); }
th.num, td.num { text-align: right; }
td.mono { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }
#page-explorer .table-container table { min-width: 680px; }
#events-table .event-row { cursor: pointer; }
#events-table .event-row:hover td:nth-child(3) { color: var(--accent); }
#events-table .event-row:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.row-go { display: inline-flex; color: var(--accent); opacity: 0; transform: translateX(-4px); transition: opacity .15s, transform .2s var(--ease); }
.event-row:hover .row-go, .event-row:focus-visible .row-go { opacity: 1; transform: none; }
.dpsi-cell { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.dpsi-value.up { color: var(--danger); font-weight: 600; }
.dpsi-value.down { color: var(--secondary); font-weight: 600; }
.dpsi-bar { position: relative; flex: none; width: 48px; height: 5px; border-radius: 999px; background: var(--surface-3); }
.dpsi-bar::after { content: ""; position: absolute; left: 50%; top: -2px; bottom: -2px; width: 1px; background: var(--border-strong); }
.dpsi-bar > span { position: absolute; top: 0; bottom: 0; }
.dpsi-bar > .up { left: 50%; background: var(--danger); border-radius: 0 999px 999px 0; }
.dpsi-bar > .down { right: 50%; background: var(--secondary); border-radius: 999px 0 0 999px; }
.sk { display: block; height: 9px; border-radius: 999px; background: linear-gradient(105deg, var(--surface-3) 30%, var(--surface-2) 48%, var(--surface-3) 66%); background-size: 220% 100%; animation: skSweep 1.1s linear infinite; }
.skeleton-row td { padding: 12px 14px; }
@keyframes skSweep { from { background-position: 120% 0; } to { background-position: -120% 0; } }
.explorer-select-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; padding: 10px 14px; border-radius: var(--radius); font-size: 13px; color: var(--text-secondary); background: var(--accent-soft); border: 1px dashed var(--accent-ring); }

/* ---------- Pipeline timeline ---------- */
.pipeline { display: flex; flex-direction: column; gap: 0; position: relative; }
.pipeline-step { position: relative; display: flex; align-items: center; gap: 16px; padding: 16px 14px; border-radius: 12px; border: 1px solid transparent; background: transparent; transition: background .2s, border-color .2s; }
.pipeline-step:not(:last-child)::after { content: ""; position: absolute; left: 32px; top: 54px; bottom: -14px; width: 2px; border-radius: 2px; background: var(--border); }
.pipeline-step:hover { background: var(--surface-2); }
.pipeline-step.active { background: var(--accent-soft); border-color: var(--accent-ring); }
.pipeline-step.completed:not(:last-child)::after { background: linear-gradient(var(--secondary), var(--border)); }
.step-number { position: relative; z-index: 1; flex: none; width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 14px; font-variant-numeric: tabular-nums; color: var(--text-muted); background: var(--surface); border: 2px solid var(--border-strong); }
.pipeline-step.active .step-number { color: var(--btn-primary-fg); background: var(--accent); border-color: var(--accent); box-shadow: 0 0 0 5px var(--accent-ring); animation: stepPulse 1.8s ease-in-out infinite; }
.pipeline-step.completed .step-number { color: #fff; background: var(--secondary); border-color: var(--secondary); }
@keyframes stepPulse { 0%,100% { box-shadow: 0 0 0 4px var(--accent-ring); } 50% { box-shadow: 0 0 0 9px transparent; } }
.step-info { flex: 1; min-width: 0; }
.step-name { font-weight: 650; font-size: 14px; color: var(--text); margin-bottom: 2px; }
.step-desc { font-size: 13px; line-height: 1.5; color: var(--text-muted); }
#progress-bar { background: var(--brand-grad) !important; box-shadow: 0 0 14px var(--accent-ring) !important; border-radius: 999px; position: relative; overflow: hidden; }

@keyframes barShine { to { transform: translateX(100%); } }
#pipeline-progress { font-family: var(--font-display); font-variant-numeric: tabular-nums; }

/* ---------- Visualization ---------- */
#page-visualization > .grid { grid-template-columns: 330px minmax(0,1fr); align-items: start; }
#page-visualization > .grid > div:first-child { position: sticky; top: 84px; max-height: calc(100vh - 110px); overflow-y: auto; padding-right: 6px; }
#page-visualization > .grid > div:first-child > .card { margin-bottom: 14px !important; padding: 18px; }
#page-visualization .card .btn { width: 100%; justify-content: flex-start !important; padding: 11px 14px !important; white-space: normal; line-height: 1.4; border-radius: 11px;
  background: var(--surface-2); color: var(--text); border: 1px solid transparent; box-shadow: none; }
#page-visualization .card .btn:hover { background: var(--accent-soft); border-color: var(--accent-ring); color: var(--text); transform: translateX(2px); }
#page-visualization .card .btn[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }
#chart-display { min-height: 560px !important; display: flex; flex-direction: column; justify-content: flex-start; top: 84px !important; }
#chart-display img { display: block; max-width: 100%; height: auto; max-height: min(74vh, 720px); object-fit: contain; margin: 0 auto; border-radius: 10px; background: #fff; }
.mobile-chart-select { display: none; }

/* ---------- Gene / report / settings ---------- */
#page-gene .search-bar { max-width: 820px; }
#page-gene #gene-details .card { min-height: 280px; display: grid; align-content: center; }
#report-output { margin-top: 4px; min-height: 220px; display: grid; align-content: center; border-radius: var(--radius); border: 1.5px dashed var(--border-strong); background: var(--surface-2); }
#page-settings > .grid { grid-template-columns: minmax(320px,1fr) minmax(0,1fr); align-items: start; }
.model-config-body { display: flex; flex-direction: column; gap: 12px; }
.model-config-body .cfg-row, .cfg-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.model-config-body .cfg-row label { flex: none; width: 92px; font-size: 12.5px; font-weight: 600; color: var(--text-secondary); }
.model-config-body .cfg-row input { flex: 1; }
.cfg-hint, .cfg-msg { font-size: 12.5px; line-height: 1.7; color: var(--text-muted); }
.cfg-msg.ok { color: var(--secondary); }
.cfg-msg.err { color: var(--danger); }
.pref-list { display: flex; flex-direction: column; }
.pref-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 0; border-top: 1px solid var(--border); }
.pref-row:first-child { border-top: 0; padding-top: 4px; }
.pref-row .pref-name { font-size: 14px; font-weight: 600; color: var(--text); }
.pref-row .pref-desc { font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }
.kbd-list { display: grid; grid-template-columns: auto 1fr; gap: 8px 14px; font-size: 12.5px; color: var(--text-secondary); }
.kbd-list kbd { justify-self: start; padding: 2px 7px; border-radius: 6px; border: 1px solid var(--border-strong); border-bottom-width: 2px; background: var(--surface-2); font: 600 11px var(--font-mono); color: var(--text); white-space: nowrap; }

/* ---------- MCP console (kept for compatibility) ---------- */
.mcp-panel { display: flex; flex-direction: column; gap: 12px; }
.mcp-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.mcp-title { font-size: 16px; font-weight: 650; color: var(--text); }
.mcp-sub { font-size: 12px; color: var(--text-muted); margin-top: 3px; }
.mcp-badge { padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); color: var(--text-secondary); background: var(--surface-2); white-space: nowrap; }
.mcp-badge.ok { color: var(--secondary); background: var(--success-soft); border-color: transparent; }
.mcp-badge.err { color: var(--danger); background: var(--danger-soft); border-color: transparent; }
.mcp-result { margin: 0; padding: 12px; max-height: 300px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface-2); color: var(--text-secondary); font: 12px/1.55 var(--font-mono); white-space: pre-wrap; word-break: break-word; }
.mcp-result.err { color: var(--danger); }

/* ---------- Neoantigen & peptide workbench ---------- */
.pep-workspace { max-width: 1320px; margin: 0 auto; }
.pep-layout { display: grid; grid-template-columns: minmax(0,1fr) 340px; gap: 24px; align-items: start; }
.pep-inputs { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 4px 26px; box-shadow: var(--shadow-sm); }
.pep-section { padding: 22px 0; }
.pep-inputs .pep-section + .pep-section { border-top: 1px solid var(--border); }
.pep-workspace h3 { font-size: 15px; font-weight: 650; margin-bottom: 8px; color: var(--text); }
.pep-help, .pep-header p { font-size: 13px; color: var(--text-secondary); }
.pep-options { position: sticky; top: 84px; padding: 4px 22px; border-radius: var(--radius); background: var(--surface); border: 1px solid var(--border); box-shadow: var(--shadow-sm); overflow: hidden; }
.pep-options::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--brand-grad); }
.pep-options .btn-primary { width: 100%; min-height: 46px; font-size: 14px; }
.pep-guide { border-top: 1px solid var(--border); padding: 18px 0 20px; }
.pep-guide h3 { font-size: 13px; }
.pep-guide p { font-size: 12.5px; color: var(--text-secondary); margin-top: 8px; line-height: 1.65; }
.pep-output { margin-top: 24px; padding: 22px 24px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-sm); min-width: 0; }
#pep-results { overflow-x: auto; }
#pep-results:empty::before { content: "完成序列与 HLA 设置后，点击「预测并排序」。结果将在这里显示。"; display: block; padding: 28px 0; text-align: center; color: var(--text-muted); font-size: 13px; }
#pep-sequences { min-height: 200px; font-family: var(--font-mono) !important; background: var(--input-bg) !important; }
#page-neoantigen input:not([type=checkbox]), #page-neoantigen select { min-height: 40px; }
#page-neoantigen details { background: var(--surface-2); }
.neo-mode-tabs { display: inline-flex; gap: 4px; padding: 4px; border-radius: 12px; background: var(--surface-3); border: 1px solid var(--border); flex-wrap: wrap; max-width: 100%; }
.neo-mode-tab { border: 0; background: transparent; color: var(--text-secondary); padding: 8px 16px; border-radius: 9px; font: 600 13px var(--font-sans); cursor: pointer; transition: all .18s; }
.neo-mode-tab:hover { color: var(--text); }
.neo-mode-tab.active { background: var(--surface); color: var(--accent); box-shadow: var(--shadow-sm); }
.neo-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; padding: 12px 16px; border-radius: var(--radius); font-size: 13px; background: var(--surface); border: 1px solid var(--border); box-shadow: var(--shadow-xs); }
.neo-filter-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 12px 0; margin-bottom: 12px; border-bottom: 1px solid var(--border); }
.neo-filter-bar select, .neo-filter-bar input[type=text] { flex: none; min-height: 34px !important; padding: 5px 10px; font-size: 12.5px; }
.neo-chip { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; font-size: 12px; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); cursor: pointer; transition: all .15s; }
.neo-chip:hover { color: var(--accent); border-color: var(--accent-ring); background: var(--accent-soft); }
.neo-badge { display: inline-block; margin-right: 4px; padding: 1px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; border: 1px solid transparent; white-space: nowrap; }
.neo-badge-ok { color: var(--secondary); background: var(--success-soft); }
.neo-badge-warn { color: var(--warning); background: var(--warning-soft); }
.neo-badge-danger { color: var(--danger); background: var(--danger-soft); }
.neo-badge-muted { color: var(--text-muted); border-color: var(--border); }
.neo-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 12px; }
.neo-result-body { max-height: 60vh; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.neo-result-body table { font-size: 12px; }
.neo-result-body th { background: var(--table-head); }
.neo-result-body td { white-space: nowrap; font-family: var(--font-mono); font-size: 12px; padding: 8px 12px; color: var(--text); }
.neo-result-body pre { margin: 0; padding: 16px; font: 12px/1.6 var(--font-mono); white-space: pre; color: var(--text-secondary); }
.neo-path { margin-top: 10px; font: 12px var(--font-mono); color: var(--text-muted); word-break: break-all; }
.pep-tier { display: inline-block; margin-left: 6px; padding: 1px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; border: 1px solid transparent; }
.pep-tier-strong { color: var(--secondary); background: var(--success-soft); }
.pep-tier-weak { color: var(--warning); background: var(--warning-soft); }
.pep-tier-none { color: var(--text-muted); border-color: var(--border); }
.pep-tier-unknown { color: var(--text-muted); border-color: var(--border); opacity: .75; }
.neo-hint-box { margin-bottom: 12px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--ai-soft); background: var(--ai-soft); }
.neo-hint-box > div:first-child { color: var(--ai) !important; }

/* ---------- Trace & mission ---------- */
.trace-control { padding: 8px 11px; border-radius: var(--radius-sm); font-size: 13px; color: var(--text); background: var(--input-bg); border: 1px solid var(--border-strong); }
.trace-badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; border: 1px solid transparent; }
.trace-llm { color: var(--ai); background: var(--ai-soft); }
.trace-rule { color: var(--text-secondary); background: var(--surface-3); }
.trace-reflection { color: var(--warning); background: var(--warning-soft); }
.trace-episodic { color: #a855f7; background: rgba(168,85,247,.12); }
.trace-replay { color: var(--accent); background: var(--accent-soft); }
.trace-step { position: relative; margin-left: 6px; padding: 6px 0 14px 16px; border-left: 2px solid var(--border); }
.trace-step::before { content: ""; position: absolute; left: -6px; top: 12px; width: 10px; height: 10px; border-radius: 50%; background: var(--surface); border: 2px solid var(--accent); }
.trace-step-title { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--text); }
.trace-meta { margin-top: 4px; font-size: 12.5px; line-height: 1.6; color: var(--text-secondary); word-break: break-word; }
.trace-call { margin-bottom: 8px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface-2); font-size: 12px; }
.trace-bar { height: 6px; margin-top: 8px; border-radius: 4px; background: var(--surface-3); overflow: hidden; }
.trace-bar > span { display: block; height: 100%; background: var(--brand-grad); }
.trace-metric { margin-top: 4px; font-family: var(--font-display); font-size: 24px; font-weight: 700; color: var(--text); }
.mission-banner { margin-bottom: 12px; padding: 14px 16px; border-radius: 12px; border: 1px solid; font-size: 13px; line-height: 1.6; }
.mission-banner-failed { color: var(--danger); background: var(--danger-soft); border-color: transparent; }
.mission-banner-partial { color: var(--warning); background: var(--warning-soft); border-color: transparent; }
.mission-banner-succeeded { color: var(--secondary); background: var(--success-soft); border-color: transparent; }
.mission-banner-running { color: var(--text-secondary); background: var(--surface-2); border-color: var(--border); }
.mission-hint { margin-top: 6px; font-size: 12px; line-height: 1.6; color: var(--text-muted); }
.mission-path, .mission-code { font: 12px var(--font-mono); color: var(--text-secondary); }
.mission-path { word-break: break-all; }
.mission-code { white-space: nowrap; overflow-x: auto; }
.mission-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }

/* ---------- Modals: upload, event detail, ingest ---------- */
#upload-modal { background: var(--overlay) !important; }
#upload-modal > div { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; box-shadow: var(--shadow-lg); color: var(--text); animation: modalIn .3s var(--ease); }
#drop-zone { border-color: var(--border-strong) !important; border-radius: var(--radius) !important; transition: border-color .2s, background-color .2s, transform .2s var(--ease) !important; }
#drop-zone:hover { border-color: var(--accent) !important; background: var(--accent-soft) !important; }
#event-detail-modal { background: var(--overlay) !important; }
#event-detail-modal > div { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; box-shadow: var(--shadow-lg); color: var(--text); overflow-x: hidden; animation: modalIn .3s var(--ease); }
#event-detail-modal > div > div:first-child { background: var(--hero-bg) !important; color: #fff !important; }
#ingest-modal { display: none; position: fixed; inset: 0; z-index: 1200; padding: 24px; align-items: center; justify-content: center; background: var(--overlay); }
#ingest-modal.open { display: flex; }
.ingest-panel { width: min(980px, 96vw); max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); animation: modalIn .3s var(--ease); }
.ingest-head { display: flex; align-items: flex-start; gap: 12px; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); background: var(--surface-2); }
.ingest-head .ingest-title { font-size: 19px; font-weight: 700; color: var(--text); letter-spacing: -.02em; }
.ingest-head .ingest-sub { margin-top: 4px; font-size: 12.5px; color: var(--text-muted); }
.ingest-close { margin-left: auto; flex: none; width: 32px; height: 32px; border-radius: 9px; border: 1px solid var(--border); background: var(--surface); color: var(--text-secondary); font-size: 16px; line-height: 1; cursor: pointer; }
.ingest-close:hover { color: var(--accent); border-color: var(--accent-ring); }
.ingest-body { padding: 18px 24px 22px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.ingest-trace { display: flex; gap: 8px; flex-wrap: wrap; }
.ingest-step { display: inline-flex; align-items: center; gap: 7px; padding: 5px 11px; border-radius: 999px; font-size: 12px; font-weight: 600; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); }
.ingest-step .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); }
.ingest-step.ok .dot { background: var(--secondary); }
.ingest-step.warn .dot { background: var(--warning); }
.ingest-step.error .dot { background: var(--danger); }
.ingest-step.running .dot { background: var(--accent); animation: dotPulse 1.4s infinite; }
.ingest-step.skip { opacity: .6; }
.ingest-source, .ingest-files, .ingest-privacy { font-size: 12.5px; color: var(--text-muted); line-height: 1.7; }
.ingest-files code { font-family: var(--font-mono); }
.ingest-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; }
.ingest-stat { padding: 12px 14px; border-radius: 12px; border: 1px solid var(--border); background: var(--surface-2); }
.ingest-stat .v { font-family: var(--font-display); font-size: 20px; font-weight: 700; line-height: 1.2; color: var(--text); }
.ingest-stat .k { margin-top: 3px; font-size: 11.5px; letter-spacing: .05em; text-transform: uppercase; color: var(--text-muted); }
.ingest-section-title { margin-bottom: 8px; font-size: 11.5px; font-weight: 650; letter-spacing: .08em; text-transform: uppercase; color: var(--text-muted); }
.ingest-map-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; }
.ingest-map-row { display: flex; align-items: center; gap: 10px; }
.ingest-map-row label { flex: none; width: 132px; font-size: 12.5px; font-weight: 600; color: var(--text-secondary); }
.ingest-map-row select { flex: 1; min-width: 0; padding: 7px 9px; font-size: 12.5px; }
.ingest-map-row select.missing { border-color: var(--warning); box-shadow: 0 0 0 3px var(--warning-soft); }
.ingest-issues { display: flex; flex-direction: column; gap: 6px; }
.ingest-issue { display: flex; gap: 8px; padding: 9px 11px; border-radius: 10px; font-size: 12.5px; line-height: 1.55; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); }
.ingest-issue .tag { flex: none; height: fit-content; padding: 2px 7px; border-radius: 6px; font-size: 11px; font-weight: 700; letter-spacing: .04em; }
.ingest-issue.error { border-color: var(--danger-soft); }
.ingest-issue.error .tag { color: var(--danger); background: var(--danger-soft); }
.ingest-issue.warning .tag { color: var(--warning); background: var(--warning-soft); }
.ingest-issue.info .tag { color: var(--accent); background: var(--accent-soft); }
.ingest-preview-table { max-height: 260px; overflow: auto; border: 1px solid var(--border); border-radius: 10px; }
.ingest-preview-table table { min-width: 620px; }
.ingest-footer { display: flex; align-items: center; gap: 12px; padding: 14px 24px; border-top: 1px solid var(--border); background: var(--surface-2); }
.ingest-footer .ingest-error { margin-right: auto; font-size: 12.5px; color: var(--danger); }
@keyframes modalIn { from { opacity: 0; transform: translateY(14px) scale(.98); } to { opacity: 1; transform: none; } }

/* ---------- Project detail drawer ---------- */
.detail-drawer-backdrop { position: fixed; inset: 0; z-index: 1500; background: var(--overlay); opacity: 0; visibility: hidden; transition: opacity .25s, visibility .25s; }
body.detail-open .detail-drawer-backdrop { opacity: 1; visibility: visible; }
#project-detail.detail-drawer {
  position: fixed; z-index: 1501; top: 0; right: 0; bottom: 0; width: min(940px, 92vw); margin: 0; padding: 28px;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg); border: 0; border-left: 1px solid var(--border);
  background: var(--surface); box-shadow: var(--shadow-lg); overflow-y: auto;
  transform: translateX(104%); visibility: hidden; transition: transform .34s var(--ease), visibility .34s;
}
#project-detail.detail-drawer::before { display: none; }
#project-detail.detail-drawer:hover { box-shadow: var(--shadow-lg); }
body.detail-open #project-detail.detail-drawer { transform: translateX(0); visibility: visible; }

/* ---------- Quick switch (Ctrl+K) ---------- */
.quick-dialog { width: min(560px, calc(100vw - 32px)); max-height: 80vh; margin: 12vh auto auto; padding: 0; color: var(--text); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); overflow: hidden; }
.quick-dialog::backdrop { background: var(--overlay); }
.quick-dialog[open] { animation: modalIn .26s var(--ease); }
.quick-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 20px 6px; }
.quick-head h2 { font-size: 15px; }
.quick-search { padding: 10px 20px 12px; }
.quick-search input { width: 100%; background: var(--surface-2); }
.quick-results { display: grid; gap: 2px; padding: 0 10px 14px; overflow: auto; max-height: 50vh; }
.quick-result { display: flex; align-items: center; gap: 10px; padding: 11px 14px; border: 0; border-radius: 10px; background: transparent; color: var(--text); font: 500 14px var(--font-sans); text-align: left; cursor: pointer; }
.quick-result::after { content: "↵"; margin-left: auto; font-size: 12px; color: var(--text-muted); opacity: 0; }
.quick-result:hover, .quick-result:focus-visible { background: var(--accent-soft); color: var(--accent); outline: none; }
.quick-result:hover::after, .quick-result:focus-visible::after { opacity: 1; }
.quick-result[aria-current=page] { color: var(--accent); font-weight: 650; }
.quick-result[hidden] { display: none; }
.quick-empty { padding: 20px 14px; font-size: 13px; color: var(--text-muted); }

/* ---------- Toasts & dialogs ---------- */
#toast-stack { position: fixed; top: 78px; right: 24px; z-index: 3000; display: flex; flex-direction: column; gap: 10px; width: min(384px, calc(100vw - 32px)); pointer-events: none; }
.app-toast { pointer-events: auto; position: relative; overflow: hidden; display: flex; gap: 12px; align-items: flex-start; padding: 14px 12px 14px 16px; color: var(--accent); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-lg); animation: toastIn .3s var(--ease); }
.app-toast.leaving { animation: toastOut .22s ease forwards; }
.app-toast-icon { flex: none; width: 26px; height: 26px; margin-top: 1px; border-radius: 50%; display: grid; place-items: center; color: #fff; background: var(--accent); }
.app-toast-icon svg { width: 14px; height: 14px; }
.app-toast-body { flex: 1; min-width: 0; }
.app-toast-title { font-size: 13.5px; font-weight: 650; line-height: 1.45; color: var(--text); }
.app-toast-msg { margin-top: 3px; font-size: 13px; line-height: 1.6; color: var(--text-secondary); white-space: pre-line; word-break: break-word; }
.app-toast-close { flex: none; width: 24px; height: 24px; display: grid; place-items: center; border: 0; border-radius: 7px; background: transparent; color: var(--text-muted); font-size: 13px; cursor: pointer; }
.app-toast-close:hover { color: var(--text); background: var(--surface-3); }
.app-toast::after { content: ""; position: absolute; left: 0; bottom: 0; width: 100%; height: 3px; background: currentColor; opacity: .55; transform-origin: left; animation: toastLife var(--toast-life, 5.2s) linear forwards; }
.app-toast.paused::after { animation-play-state: paused; }
.app-toast.success { color: var(--secondary); }
.app-toast.success .app-toast-icon { background: var(--secondary); }
.app-toast.error { color: var(--danger); }
.app-toast.error .app-toast-icon { background: var(--danger); }
.app-toast.warning { color: var(--warning); }
.app-toast.warning .app-toast-icon { background: var(--warning); }
@keyframes toastIn { from { opacity: 0; transform: translateX(18px) scale(.98); } to { opacity: 1; transform: none; } }
@keyframes toastOut { to { opacity: 0; transform: translateX(18px); } }
@keyframes toastLife { from { transform: scaleX(1); } to { transform: scaleX(0); } }
.app-dialog { width: min(528px, calc(100vw - 32px)); margin: auto; padding: 0; overflow: hidden; color: var(--text); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); }
.app-dialog::backdrop { background: var(--overlay); }
.app-dialog[open] { animation: modalIn .28s var(--ease); }
.app-dialog-head { display: flex; gap: 14px; align-items: flex-start; padding: 24px 24px 0; }
.app-dialog-mark { flex: none; width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center; color: var(--accent); background: var(--accent-soft); }
.app-dialog-mark svg { width: 20px; height: 20px; }
.app-dialog.success .app-dialog-mark { color: var(--secondary); background: var(--success-soft); }
.app-dialog.error .app-dialog-mark { color: var(--danger); background: var(--danger-soft); }
.app-dialog.warning .app-dialog-mark { color: var(--warning); background: var(--warning-soft); }
.app-dialog-titles { flex: 1; min-width: 0; padding-top: 2px; }
.app-dialog-title { font-size: 16px; font-weight: 700; letter-spacing: -.01em; color: var(--text); }
.app-dialog-sub { margin-top: 4px; font-size: 12px; color: var(--text-muted); }
.app-dialog-close { flex: none; width: 30px; height: 30px; display: grid; place-items: center; border-radius: 9px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-muted); font-size: 14px; cursor: pointer; }
.app-dialog-close:hover { color: var(--text); border-color: var(--border-strong); }
.app-dialog-body { padding: 16px 24px 4px; font-size: 14px; line-height: 1.72; color: var(--text-secondary); white-space: pre-line; word-break: break-word; }
.app-dialog-body strong { color: var(--text); }
.app-dialog-detail { margin-top: 14px; padding: 12px 14px; max-height: 150px; overflow: auto; border-radius: 10px; border: 1px solid var(--border); background: var(--surface-2); font: 12px/1.6 var(--font-mono); color: var(--text-secondary); white-space: pre-wrap; }
.app-dialog-list { margin: 14px 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 7px; }
.app-dialog-list li { position: relative; padding-left: 18px; font-size: 13px; color: var(--text-secondary); }
.app-dialog-list li::before { content: ""; position: absolute; left: 4px; top: 9px; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }
.app-dialog-foot { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 10px; padding: 18px 24px 22px; }
.app-dialog-foot .btn-danger { background: var(--danger); color: #fff; }
.app-dialog-foot .btn-danger:hover { filter: brightness(1.08); }

/* ---------- Global request indicator ---------- */
#request-indicator { position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 4000; overflow: hidden; pointer-events: none; background: var(--accent-soft); }
#request-indicator[hidden] { display: none; }
#request-indicator::after { content: ""; display: block; width: 35%; height: 100%; background: var(--brand-grad); animation: requestSweep 1.1s ease-in-out infinite alternate; }
@keyframes requestSweep { from { transform: translateX(-30%); } to { transform: translateX(220%); } }

/* ---------- Misc / a11y / responsive ---------- */
.skip-link { position: fixed; left: calc(var(--sidebar-w) + 16px); top: -70px; z-index: 2000; padding: 10px 14px; border-radius: 10px; background: var(--surface); color: var(--accent); box-shadow: var(--shadow); }
.skip-link:focus { top: 12px; }
.mobile-menu, .drawer-close, .nav-scrim { display: none; }
@keyframes pageIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
body.motion-paused *, body.motion-paused *::before, body.motion-paused *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
body.motion-paused .start-guide::before { left: 72% !important; top: 40% !important; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; } }
@media (min-width: 1680px) { .content { padding-top: 36px; } }
@media (max-width: 1200px) {
  .grid-4 { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .start-guide { grid-template-columns: 1fr; }
  .hero-art { width: 100%; opacity: .35; }
  .pep-layout { grid-template-columns: 1fr; }
  .pep-options { position: relative; top: 0; }
  #page-visualization > .grid { grid-template-columns: 280px minmax(0,1fr); }
  #page-settings > .grid { grid-template-columns: 1fr; }
  .quick-switch kbd { display: none; }
}
@media (max-width: 768px) {
  .mobile-menu { display: inline-flex; }
  .sidebar { width: min(284px, 86vw); z-index: 120; transform: translateX(-105%); visibility: hidden; box-shadow: var(--shadow-lg); }
  .navigation-open .sidebar { transform: translateX(0); visibility: visible; }
  .nav-scrim { display: block; position: fixed; inset: 0; z-index: 110; border: 0; background: var(--overlay); opacity: 0; visibility: hidden; transition: opacity .25s, visibility .25s; }
  .navigation-open .nav-scrim { opacity: 1; visibility: visible; }
  .drawer-close { display: flex; margin: 14px 12px 0 auto; }
  body.navigation-open { overflow: hidden; }
  .sidebar-toggle { display: none; }
  .main { margin-left: 0; }
  .topbar { height: auto; min-height: 60px; padding: 10px 16px; flex-wrap: wrap; }
  .topbar-actions { flex-wrap: wrap; gap: 8px; }
  #current-project { max-width: 60vw; }
  .content { padding: 22px 16px 48px; }
  .workspace-heading { align-items: flex-start; flex-direction: column; }
  .workspace-heading h1 { font-size: 24px; }
  .workspace-tag { display: none; }
  .grid-2, .grid-3, .grid-4, #page-visualization > .grid { grid-template-columns: 1fr; }
  #page-dashboard > .grid-4 { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .start-guide { padding: 26px 22px; }
  .mobile-chart-select { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
  #page-visualization > .grid > div:first-child { display: none; }
  #chart-display { position: static !important; min-height: 320px !important; }
  .search-bar { flex-wrap: wrap; }
  .search-bar input { flex-basis: 100%; }
  .pipeline-step { flex-wrap: wrap; }
  .model-config-body .cfg-row { flex-direction: column; align-items: stretch; }
  .model-config-body .cfg-row label { width: auto; }
  #neo-mapping-fields { grid-template-columns: 1fr !important; }
  .ingest-stats { grid-template-columns: repeat(2,1fr); }
  .ingest-map-grid { grid-template-columns: 1fr; }
  .ingest-footer { flex-wrap: wrap; }
  #toast-stack { top: 14px; right: 14px; left: 14px; width: auto; }
  .app-dialog-foot { flex-direction: column-reverse; align-items: stretch; }
  #project-detail.detail-drawer { width: 100vw; padding: 20px; border-radius: 0; }
  .skip-link { left: 16px; }
  #events-table td[colspan] { text-align: left !important; padding: 32px 16px !important; }
}
</style>
</head>
<body>
<div class="app">
  <button class="nav-scrim" tabindex="-1" aria-label="关闭导航" onclick="toggleNavigation(false)"></button><aside class="sidebar" id="app-navigation" aria-label="主导航"><div class="nav-fluid-marker" aria-hidden="true"></div><button class="drawer-close btn btn-secondary" type="button" onclick="toggleNavigation(false)">关闭菜单</button>
    <div class="brand"><div class="brand-mark" aria-hidden="true"><img src="/assets/logo.png" alt="EpitopeRank" width="40" height="40"/></div><div class="brand-text"><div class="brand-name">EpitopeRank</div><div class="brand-tagline">rMATS 剪接新抗原 · ESM-2</div></div></div>
    <div class="nav-section"><div class="nav-label">核心流程</div>
      <button type="button" class="nav-item active" data-page="dashboard" aria-current="page" title="项目工作台 (Alt+1)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z"/></svg>项目工作台</button>
      <button type="button" class="nav-item" data-page="pipeline" title="rMATS 分析 (Alt+2)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16 M4 12h16 M4 19h16 M8 3v4 M16 10v4 M10 17v4"/></svg>rMATS 分析</button>
      <button type="button" class="nav-item" data-page="explorer" title="剪接事件 (Alt+3)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16v16H4z M4 10h16 M10 4v16"/></svg>剪接事件</button>
      <button type="button" class="nav-item" data-page="neoantigen" title="新抗原 &amp; ESM-2 (Alt+4)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h5l3-8 4 16 3-8h3"/></svg>新抗原 &amp; ESM-2</button>
    </div>
    <div class="nav-section"><div class="nav-label">结果与配置</div>
      <button type="button" class="nav-item" data-page="visualization" title="可视化图表 (Alt+5)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 3v17h17 M8 16v-5 M13 16V7 M18 16V4"/></svg>可视化图表</button>
      <button type="button" class="nav-item" data-page="report" title="分析报告 (Alt+6)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z M14 3v5h5 M9 12h7 M9 16h7"/></svg>分析报告</button>
      <button type="button" class="nav-item" data-detail="1" onclick="openProjectDetail()" title="项目详情"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16v16H4z M4 9h16 M9 9v11 M14 4v5"/></svg>项目详情</button>
      <button type="button" class="nav-item" data-page="settings" title="设置"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v3 M12 18v3 M3 12h3 M18 12h3 M6 6l2 2 M16 16l2 2 M6 18l2-2 M16 8l2-2 M8 12a4 4 0 1 0 8 0a4 4 0 1 0-8 0"/></svg>设置</button>
    </div>
    <div class="sidebar-foot" title="ESM-2-650M LoRA + rMATS 本地引擎"><span class="pulse" aria-hidden="true"></span><span>rMATS · ESM-2 引擎就绪</span></div>
  </aside>
  <a class="skip-link" href="#workspace-content">跳到工作区</a><main class="main">
    <div class="topbar">
      <div class="topbar-left">
        <button class="btn btn-secondary btn-sm mobile-menu" type="button" aria-controls="app-navigation" aria-expanded="false" onclick="toggleNavigation()">菜单</button>
        <button class="icon-btn sidebar-toggle" type="button" onclick="toggleSidebarCompact()" title="折叠/展开侧边栏 (Ctrl+B)" aria-label="折叠或展开侧边栏">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>
        </button>
        <div id="current-project" title="当前项目">未加载项目</div>
      </div>
      <div class="topbar-actions">
        <button type="button" class="btn btn-secondary btn-sm quick-switch" onclick="openQuickSwitch()">快捷跳转 <kbd>Ctrl K</kbd></button>
        <button type="button" class="icon-btn theme-toggle" id="theme-toggle-btn" onclick="cycleTheme()" title="切换浅色/深色主题" aria-label="切换浅色或深色主题">
          <svg class="ico-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
          <svg class="ico-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
        <div class="lang-toggle" role="group" aria-label="Language" data-no-i18n>
          <button type="button" data-lang="zh" class="active" aria-pressed="true">简体</button>
          <button type="button" data-lang="zh-Hant" aria-pressed="false">繁體</button>
          <button type="button" data-lang="en" aria-pressed="false">EN</button>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="refreshData()">刷新</button>
        <button class="btn btn-primary btn-sm" onclick="showUploadModal()">+ 新建 rMATS 分析</button>
      </div>
    </div>
    <div class="content" id="workspace-content" tabindex="-1">
      <div class="page active" id="page-dashboard">
        <header class="workspace-heading"><div><h1>项目工作台</h1><p>管理剪接分析项目，追踪进度，回到每一次研究的结果。</p></div><span class="workspace-tag">研究工作区</span></header>
        
        <div class="grid grid-4" style="margin-bottom: 24px;">
          <div class="card stat-card">
            <div class="stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 18l-5-9V3"/><path d="M8 15h8"/></svg></div>
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;">总样本数</div>
            <div id="stat-samples">-</div>
            <div style="font-size: 12px; margin-top: 8px; color: var(--text-muted);">RNA-seq 样本</div>
          </div>
          <div class="card stat-card tone-sky">
            <div class="stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="10" width="4" height="4" rx="1"/><rect x="17" y="10" width="4" height="4" rx="1"/><path d="M7 12h10M5 10c2-5 12-5 14 0"/></svg></div>
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;">剪接事件</div>
            <div id="stat-events">-</div>
            <div style="font-size: 12px; margin-top: 8px; color: var(--text-muted);">检测到的事件总数</div>
          </div>
          <div class="card stat-card tone-rose">
            <div class="stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3l2.6 5.3L20.5 9l-4.2 4.1 1 5.9L12 16.2 6.7 19l1-5.9L3.5 9l5.9-.7L12 3z"/></svg></div>
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;">显著事件</div>
            <div id="stat-significant">-</div>
            <div style="font-size: 12px; margin-top: 8px; color: var(--text-muted);">FDR &lt; 0.05 &amp; |ΔPSI| &gt; 0.1</div>
          </div>
          <div class="card stat-card tone-ai">
            <div class="stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/><circle cx="12" cy="12" r="3"/></svg></div>
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;">系统状态</div>
            <div style="margin-top: 12px;" id="stat-status"><span class="status status-waiting"><span class="status-dot"></span>空闲</span></div>
            <div style="font-size: 12px; margin-top: 12px; color: var(--text-muted);">本地分析引擎在线</div>
          </div>
        </div>
<section class="start-guide" aria-label="开始使用"><svg class="hero-art" viewBox="0 0 640 320" preserveAspectRatio="xMaxYMid slice" aria-hidden="true"><line class="intron" x1="48" y1="68" x2="592" y2="68"/><rect class="exon" x="62" y="52" width="94" height="32" rx="7"/><rect class="exon alt" x="256" y="52" width="96" height="32" rx="7"/><rect class="exon" x="454" y="52" width="110" height="32" rx="7"/><path class="arc" d="M156 52 C190 22, 222 22, 256 52"/><path class="arc" d="M352 52 C386 22, 420 22, 454 52"/><path class="arc skip" d="M109 52 C180 -6, 426 -6, 509 52"/><path class="signal" d="M109 52 C180 -6, 426 -6, 509 52"/><path class="groove" d="M110 264 Q320 310 530 264"/><path class="bond" d="M148 238 L204 224 L260 240 L316 220 L372 238 L428 224 L484 238"/><circle class="bead" cx="148" cy="238" r="7"/><circle class="bead" cx="204" cy="224" r="7"/><circle class="bead" cx="260" cy="240" r="7"/><circle class="bead hot" cx="316" cy="220" r="9"/><circle class="bead" cx="372" cy="238" r="7"/><circle class="bead" cx="428" cy="224" r="7"/><circle class="bead" cx="484" cy="238" r="7"/></svg><div><span class="hero-eyebrow">rMATS · ORF 重建 · ESM-2-650M LoRA</span><h2>从剪接事件，走向<em>高免疫原性</em>新抗原。</h2><p>上传 rMATS 差异剪接数据，一键完成统计筛选、跨连接点 ORF 重建与 IEDB + ESM-2 融合排序。</p><button class="btn btn-primary" onclick="showUploadModal()">新建分析项目</button><button class="btn btn-secondary" onclick="navigateTo('peptide')">已有肽序列？直接预测</button></div><ol><li><b>01</b><span><strong>准备数据</strong>支持 rMATS 五类事件表与报告目录导入</span></li><li><b>02</b><span><strong>剪接与 ORF</strong>确认字段映射，筛选显著事件并重建 ORF</span></li><li><b>03</b><span><strong>新抗原排序</strong>IEDB MHC 结合 + ESM-2 免疫原性融合排序</span></li></ol></section>
        <div class="grid grid-2">
          <div class="card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary);">当前运行 Agent</div>
              <div id="current-agent-indicator" style="display: none;"><span class="status status-running"><span class="status-dot"></span>分析中</span></div>
            </div>
            <div id="current-agent">
              <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                <div style="font-size: 36px; margin-bottom: 12px; opacity: 0.3;"></div>
                <div style="font-size: 14px;">暂无运行中的分析</div>
                <button class="btn btn-primary" style="margin-top: 16px;" onclick="showUploadModal()">启动新分析</button>
              </div>
            </div>
          </div>
          <div class="card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary);">历史项目</div>
              <button class="btn btn-sm btn-secondary" onclick="loadDashboard()">刷新</button>
            </div>
            <input aria-label="搜索历史项目" id="project-search" type="search" placeholder="搜索历史项目" oninput="renderProjectHistory()" style="width:100%;margin-bottom:12px;padding:9px;border:1px solid var(--border);border-radius:var(--radius-sm);">
            <div id="recent-projects" style="max-height:440px;overflow:auto;">
              <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                <div style="font-size: 36px; margin-bottom: 12px; opacity: 0.3;"></div>
                <div style="font-size: 14px;">暂无项目</div>
              </div>
            </div>
            <div id="storage-hint" style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);font-size:12px;line-height:1.6;color:var(--text-muted);">
              数据目录：读取中…
            </div>
          </div>
        </div>
      </div>
      <div class="page" id="page-pipeline"><header class="workspace-heading"><div><h1>分析流程</h1><p>查看数据处理、统计分析与解读进度，定位当前执行阶段。</p></div></header>
        <div class="card" style="margin-bottom: 24px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
            <div>
              <div style="font-size: 16px; font-weight: 600;">分析进度</div>
              <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;" id="pipeline-status-text">等待启动...</div>
            </div>
            <div id="pipeline-progress" style="font-size: 20px; font-weight: 600; color: var(--accent);">0%</div>
          </div>
          <div style="height: 8px; background: var(--gray-100); border-radius: var(--radius-sm); overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">
            <div id="progress-bar" style="height: 100%; width: 0%; background: var(--black); transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 4px rgba(8, 145, 178, 0.3);"></div>
          </div>
        </div>
        
        <div class="card" style="margin-bottom: 24px;">
          <div style="font-size: 14px; font-weight: 600; margin-bottom: 16px; color: var(--text);">Agent 工作流</div>
          <div class="pipeline" id="pipeline-steps">
            <div class="pipeline-step waiting">
              <div class="step-number">1</div>
              <div class="step-info">
                <div class="step-name"> 数据 Agent</div>
                <div class="step-desc">加载并验证输入数据，检查文件格式和完整性</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
            <div class="pipeline-step waiting">
              <div class="step-number">2</div>
              <div class="step-info">
                <div class="step-name"> 质控 Agent</div>
                <div class="step-desc">执行质量控制检查，过滤低质量样本</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
            <div class="pipeline-step waiting">
              <div class="step-number">3</div>
              <div class="step-info">
                <div class="step-name"> 剪接检测 Agent</div>
                <div class="step-desc">使用统计模型检测可变剪接事件</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
            <div class="pipeline-step waiting">
              <div class="step-number">4</div>
              <div class="step-info">
                <div class="step-name"> 统计 Agent</div>
                <div class="step-desc">计算显著性（FDR）和效应量（Delta PSI）</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
            <div class="pipeline-step waiting">
              <div class="step-number">5</div>
              <div class="step-info">
                <div class="step-name"> 注释 Agent</div>
                <div class="step-desc">功能注释、通路富集和文献证据收集</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
            <div class="pipeline-step waiting">
              <div class="step-number">6</div>
              <div class="step-info">
                <div class="step-name"> 解读 Agent</div>
                <div class="step-desc">生成生物学解读和专业分析报告</div>
              </div>
              <span class="status status-waiting"><span class="status-dot"></span>等待中</span>
            </div>
          </div>
        </div>
      </div>
      <div class="page" id="page-explorer"><header class="workspace-heading"><div><h1>事件浏览器</h1><p>按基因、事件类型与显著性筛选，追溯候选事件的统计依据。</p></div></header>
        <div class="card" style="margin-bottom: 24px;">
          <div style="font-size: 16px; font-weight: 600; margin-bottom: 20px;">筛选条件</div>
          <div class="search-bar" style="margin-bottom: 20px;">
            <input type="text" class="search-input" placeholder="搜索基因名称、事件ID或染色体位置..." aria-label="搜索事件" id="search-input" onkeypress="if(event.key==='Enter') applyFilters()">
            <button class="btn btn-primary" onclick="applyFilters()"> 应用筛选</button>
          </div>
          <div class="filters" style="margin-bottom: 0;">
            <div class="filter-group">
              <div class="filter-label">事件类型</div>
              <div class="checkbox-group">
                <label class="checkbox-label"><input type="checkbox" value="SE" checked> SE (外显子跳跃)</label>
                <label class="checkbox-label"><input type="checkbox" value="MXE" checked> MXE (互斥外显子)</label>
                <label class="checkbox-label"><input type="checkbox" value="A3SS" checked> A3SS (可变3'剪接)</label>
                <label class="checkbox-label"><input type="checkbox" value="A5SS" checked> A5SS (可变5'剪接)</label>
                <label class="checkbox-label"><input type="checkbox" value="RI" checked> RI (内含子保留)</label>
              </div>
            </div>
            <div class="filter-group">
              <div class="filter-label">统计阈值</div>
              <div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
                <label class="checkbox-label"><input type="checkbox" id="filter-significant"> 仅显著事件</label>
                <label class="checkbox-label">排序
                  <select id="filter-order" style="margin-left:6px;padding:6px 8px;border:1px solid var(--border);border-radius:var(--radius-sm);background:transparent;color:var(--text);font-family:inherit;font-size:12px;">
                    <option value="fdr">按 FDR</option>
                    <option value="delta_psi">按 |ΔPSI|</option>
                    <option value="gene">按基因名</option>
                  </select>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="explorer-select-bar" id="explorer-select-bar">
          <span id="explorer-select-count">勾选感兴趣的剪接事件，可直接带入「新抗原筛选」自动重建 ORF 并预测</span>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button type="button" class="btn btn-primary btn-sm" id="explorer-send-neo" onclick="sendSelectedEventsToNeo()" disabled>送去筛选新抗原 →</button>
            <button type="button" class="btn btn-secondary btn-sm" id="explorer-clear-neo" onclick="clearSelectedEvents()" disabled>清空勾选</button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th style="width:36px;" aria-label="选择"><input type="checkbox" id="events-select-all" aria-label="全选当前页" onchange="toggleSelectAllEvents(this.checked)"></th>
                <th>事件 ID</th>
                <th>基因</th>
                <th>类型</th>
                <th class="num">ΔPSI</th>
                <th class="num">FDR</th>
                <th aria-label="查看详情"></th>
              </tr>
            </thead>
            <tbody id="events-table">
              <tr>
                <td colspan="7" style="text-align: center; padding: 60px; color: var(--text-muted);">
                  <div style="font-size: 36px; margin-bottom: 16px; opacity: 0.3;"></div>
                  <div style="font-size: 16px; font-weight: 600;">未加载事件数据</div>
                  <div style="font-size: 14px; margin-top: 8px;">请完成分析后查看结果</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div id="events-pager" style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:16px;flex-wrap:wrap;font-size:13px;color:var(--text-secondary);">
          <div id="events-pager-info">-</div>
          <div style="display:flex;gap:8px;align-items:center;">
            <button class="btn btn-sm btn-secondary" onclick="gotoEventPage(1)">首页</button>
            <button class="btn btn-sm btn-secondary" onclick="gotoEventPage(state.eventPage - 1)">上一页</button>
            <span id="events-pager-page">1 / 1</span>
            <button class="btn btn-sm btn-secondary" onclick="gotoEventPage(state.eventPage + 1)">下一页</button>
            <button class="btn btn-sm btn-secondary" onclick="gotoEventPage(state.eventPages)">末页</button>
          </div>
        </div>
      </div>
      <div class="page" id="page-visualization"><header class="workspace-heading"><div><h1>可视化工作室</h1><p>选择研究问题对应的图表，查看当前项目的可视化结果。</p></div></header>
        <div class="mobile-chart-select"><label for="chart-select-mobile">图表类型</label><select id="chart-select-mobile" onchange="if(this.value) loadChart(this.value)"><option value="">选择要查看的图表</option><option value="volcano">火山图 Volcano</option><option value="dpsi_waterfall">ΔPSI 瀑布图 Waterfall</option><option value="dpsi_ecdf">ΔPSI 累积分布 ECDF</option><option value="fdr_scree">显著性碎石图 Scree</option><option value="event_type_counts">事件类型分布</option><option value="event_significance">类型×显著性堆叠图</option><option value="event_schematic">剪接机制示意图 Schematic</option><option value="psi_heatmap">PSI 热图 Heatmap</option><option value="psi_distribution">分组 PSI 箱线图</option><option value="sample_composition">队列构成图</option><option value="candidate_ranking">候选基因排名</option><option value="score_components">评分分解堆叠图</option><option value="enrichment">功能富集点图</option></select></div><div class="grid grid-2">
          <div>
            <div class="card" style="margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: var(--text);"> 核心统计图</div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 14px;">差异剪接的显著性与效应量</div>
              <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="btn btn-secondary" onclick="loadChart('volcano')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 火山图 Volcano</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">ΔPSI vs -log10(FDR)，标注显著性阈值</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('dpsi_waterfall')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> ΔPSI 瀑布图 Waterfall</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">Top 25 效应量排序，区分包含上调/下调</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('dpsi_ecdf')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> ΔPSI 累积分布 ECDF</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">效应量经验累积分布与阈值占比</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('fdr_scree')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 显著性碎石图 Scree</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">候选排名 vs -log10(FDR)，定位显著性拐点</div></div>
                </button>
              </div>
            </div>
            <div class="card" style="margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: var(--text);"> 事件组成与机制</div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 14px;">剪接事件类型构成与分子机制</div>
              <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="btn btn-secondary" onclick="loadChart('event_type_counts')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 事件类型分布</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">SE/MXE/A5SS/A3SS/RI 五类事件计数</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('event_significance')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 类型×显著性堆叠图</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">各类型中显著与非显著事件构成</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('event_schematic')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 剪接机制示意图 Schematic</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">五类可变剪接的外显子-内含子结构模式图</div></div>
                </button>
              </div>
            </div>
            <div class="card" style="margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: var(--text);"> 样本与质控</div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 14px;">队列构成与样本水平 PSI 模式</div>
              <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="btn btn-secondary" onclick="loadChart('psi_heatmap')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> PSI 热图 Heatmap</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">Top 事件逐样本 PSI 聚类热图</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('psi_distribution')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 分组 PSI 箱线图</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">各组 PSI 分布与离群样本检测</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('sample_composition')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 队列构成图</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">分组占比与批次分布（QC 必备）</div></div>
                </button>
              </div>
            </div>
            <div class="card">
              <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: var(--text);"> AI 排序与功能富集</div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 14px;">智能体候选评分与通路注释</div>
              <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="btn btn-secondary" onclick="loadChart('candidate_ranking')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 候选基因排名</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">综合评分 Top 15 候选事件条形图</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('score_components')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 评分分解堆叠图</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">显著性/效应/生物学/文献四维贡献</div></div>
                </button>
                <button class="btn btn-secondary" onclick="loadChart('enrichment')" style="justify-content: flex-start; padding: 12px 16px; text-align: left;">
                  <div><div style="font-weight: 600; margin-bottom: 2px;"> 功能富集点图</div><div style="font-size: 12px; color: var(--text-secondary); font-weight: 400;">GO/KEGG 富集倍数 vs FDR 气泡图</div></div>
                </button>
              </div>
            </div>
          </div>
          <div>
            <div class="chart-container" id="chart-display" style="min-height: 600px; position: sticky; top: 88px;">
              <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-muted);">
                <div style="font-size: 36px; margin-bottom: 20px; opacity: 0.3;"></div>
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">选择图表类型</div>
                <div style="font-size: 14px;">选择图表后，预览将在这里显示</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="page" id="page-gene"><header class="workspace-heading"><div><h1>基因探索</h1><p>以基因为线索，连接剪接事件、统计结果与生物学证据。</p></div></header>
        <div class="search-bar">
          <input type="text" class="search-input" placeholder="输入基因符号（如 TP53、BRCA1、MYC）..." aria-label="基因符号" id="gene-search" onkeypress="if(event.key==='Enter') exploreGene()">
          <button class="btn btn-primary" onclick="exploreGene()"> 探索</button>
        </div>
        <div style="margin-bottom: 24px; padding: 20px; background: var(--gray-100); border-radius: var(--radius); border-left: 1px solid var(--gray-700);">
          <div style="font-size: 13px; font-weight: 600; color: var(--secondary); margin-bottom: 8px;"> 提示</div>
          <div style="font-size: 13px; line-height: 1.8; color: var(--text);">
            输入基因符号查看该基因的所有剪接事件、统计信息和文献证据。支持热门基因如 TP53、BRCA1、MYC、EGFR 等。
          </div>
        </div>
        <div id="gene-details">
          <div class="card">
            <div style="padding: 60px; text-align: center; color: var(--text-muted);">
              <div style="font-size: 36px; margin-bottom: 16px; opacity: 0.3;"></div>
              <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">探索基因剪接模式</div>
              <div style="font-size: 14px;">在上方输入基因符号以探索其剪接事件和生物学功能</div>
            </div>
          </div>
        </div>
      </div>
      <div class="page" id="page-report"><header class="workspace-heading"><div><h1>报告与交付</h1><p>导出当前项目的剪接分析、图表及候选新抗原证据。</p></div></header>
        <div class="card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
            <div>
              <div style="font-size: 16px; font-weight: 600; margin-bottom: 4px;">生成分析报告</div>
              <div style="font-size: 13px; color: var(--text-secondary);">基于当前分析结果生成专业报告</div>
            </div>
            <div style="display: flex; gap: 12px;">
              <button class="btn btn-primary" onclick="generateReport('html')">
                <span> HTML 报告</span>
              </button>
              <button class="btn btn-secondary" onclick="generateReport('pdf')">
                <span> PDF 报告</span>
              </button>
            </div>
          </div>
          
          <div id="report-output" role="status" aria-live="polite">
            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
              <div style="font-size: 36px; margin-bottom: 20px; opacity: 0.3;"></div>
              <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">准备生成报告</div>
              <div style="font-size: 14px;">有已保存的项目肽结果时，报告会附上候选序列、来源和 HLA 预测。</div>
            </div>
          </div>
          
          <div style="margin-top: 24px; padding: 20px; background: var(--gray-100); border-radius: var(--radius); border-left: 1px solid var(--black);">
            <div style="font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 8px;"> 报告内容</div>
            <div style="font-size: 13px; line-height: 1.8; color: var(--text);">
              <div>• 项目概览与样本统计</div>
              <div>• 按项目阈值筛选的剪接事件</div>
              <div>• 关键基因的功能注释与通路富集</div>
              <div>• 可视化图表（火山图、热图、分布图）</div>
              <div>• 候选肽与新抗原证据（含未评估项）</div>
              <div>• 生物学解读与分析局限</div>
            </div>
          </div>
        </div>
      </div>
      
      
      <div class="page" id="page-trace"><header class="workspace-heading"><div><h1>决策轨迹</h1><p>一次分析里，每一步由谁决定、依据是什么，以及模型与工具各自做了什么。数值计算仍由确定性工具完成。</p></div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <select id="trace-project" class="trace-control" style="min-width:230px" onchange="loadDecisionTrace()"></select>
          <button class="btn btn-sm btn-secondary" onclick="loadDecisionTrace()">刷新轨迹</button>
        </div></header>
        <div id="trace-summary" class="grid grid-4" style="margin-bottom:16px;"></div>
        <div class="card" style="margin-bottom:16px;">
          <div style="font-size:16px;font-weight:600;margin-bottom:6px;">完整性与重放校验</div>
          <div id="trace-integrity" class="trace-meta">选择项目后加载轨迹…</div>
          <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
            <input id="trace-compare-right" class="trace-control" placeholder="另一个 agent_state.json 路径（可选）" style="flex:1;min-width:260px;">
            <button class="btn btn-sm btn-secondary" onclick="compareDecisionTrace()">对比两次运行</button>
          </div>
          <div id="trace-compare-result" class="trace-meta" style="margin-top:10px;"></div>
        </div>
        <div class="grid grid-2">
          <div class="card"><div style="font-size:16px;font-weight:600;margin-bottom:12px;">决策时间线</div><div id="trace-steps"></div></div>
          <div class="card"><div style="font-size:16px;font-weight:600;margin-bottom:12px;">模型与工具调用</div><div id="trace-calls"></div></div>
        </div>
      </div>

      <div class="page" id="page-mission"><header class="workspace-heading"><div><h1>自主任务</h1><p>用一句科研目标生成可审阅的分析计划；确认后自主执行，并给出可离线复现的证明。</p></div></header>
        <div class="card" style="margin-bottom:16px;">
          <div style="font-size:16px;font-weight:600;margin-bottom:10px;">1 · 描述目标</div>
          <textarea id="mission-query" class="trace-control" rows="2" style="width:100%;resize:vertical;" placeholder="例如：为 UPF1 敲低样本找 3 个可验证的 MHC-I 新抗原候选">为 UPF1 敲低样本找 3 个可验证的 MHC-I 新抗原候选</textarea>
          <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center;">
            <input id="mission-input" class="trace-control" style="flex:1;min-width:280px;" placeholder="输入数据目录，例如 E:/rMATS_data/UPF1_KD_vs_scr2">
            <button class="btn btn-sm btn-primary" onclick="missionGenerate()">生成计划</button>
          </div>
          <div id="mission-plan-status" class="trace-meta" style="margin-top:8px;"></div>
          <div class="trace-meta" style="margin-top:4px;color:var(--text-muted);">输入目录请指向含 sample_metadata.tsv 的单个数据集文件夹；不要填多个数据集共用的上级目录，否则样本分组读不到，会筛不出显著事件。</div>
        </div>
        <div class="card" id="mission-plan-card" style="margin-bottom:16px;display:none;">
          <div style="font-size:16px;font-weight:600;margin-bottom:10px;">2 · 审阅并修改计划（这份契约会随运行一起存档）</div>
          <div class="grid grid-2">
            <div><div class="trace-meta">目标</div><input id="mission-goal" class="trace-control" style="width:100%;"></div>
            <div><div class="trace-meta">意图</div><select id="mission-intent" class="trace-control" style="width:100%;"><option value="differential_AS">差异可变剪接</option><option value="neoantigen">新抗原 / 肽预测</option><option value="exploration">数据探索</option></select></div>
          </div>
          <div class="grid grid-4" style="margin-top:10px;">
            <div><div class="trace-meta">FDR 阈值</div><input id="mission-fdr" class="trace-control" style="width:100%;" type="number" step="0.01" min="0.001" max="0.99"></div>
            <div><div class="trace-meta">|dPSI| 阈值</div><input id="mission-dpsi" class="trace-control" style="width:100%;" type="number" step="0.01" min="0.001" max="0.99"></div>
            <div><div class="trace-meta">候选数上限</div><input id="mission-topn" class="trace-control" style="width:100%;" type="number" min="1" max="200"></div>
            <div><div class="trace-meta">最大步数</div><input id="mission-steps" class="trace-control" style="width:100%;" type="number" min="1" max="60"></div>
          </div>
          <div style="margin-top:10px;"><div class="trace-meta">允许调用的工具（每行一个；删掉即不允许该动作）</div>
            <textarea id="mission-tools" class="trace-control" rows="7" style="width:100%;resize:vertical;font-family:var(--font-mono,monospace);font-size:12px;"></textarea></div>
          <div id="mission-plan-meta" class="trace-meta" style="margin-top:8px;"></div>
          <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
            <button class="btn btn-sm btn-primary" onclick="missionRun()">确认并执行</button>
            <span class="trace-meta">阈值与预算来自本机配置，模型不能改写。</span>
          </div>
        </div>
        <div class="card" id="mission-result" style="display:none;">
          <div style="font-size:16px;font-weight:600;margin-bottom:10px;">3 · 执行结果与可复现证明</div>
          <div id="mission-status-banner"></div>
          <div id="mission-artifacts"></div>
          <div id="mission-run-summary" class="trace-meta" style="margin-top:8px;"></div>
          <div id="mission-deviations" style="margin-top:12px;"></div>
          <div id="mission-proof" style="margin-top:12px;"></div>
          <div class="mission-actions">
            <button class="btn btn-sm btn-primary" onclick="missionOpenReport('html')">打开本次报告</button>
            <button class="btn btn-sm btn-secondary" onclick="missionOpenReport('pdf')">打开 PDF</button>
            <button class="btn btn-sm btn-secondary" onclick="missionVerify()">一键离线重放验证</button>
            <button class="btn btn-sm btn-secondary" onclick="missionCopyProof()">复制重放命令</button>
            <button class="btn btn-sm btn-secondary" onclick="missionOpenTrace()">查看决策轨迹</button>
          </div>
          <div id="mission-verify-result" class="trace-meta" style="margin-top:10px;"></div>
        </div>
      </div>
<div class="page" id="page-settings"><header class="workspace-heading"><div><h1>工作区设置</h1><p>配置可选大模型解读服务，查看 ESM-2 免疫原性与 rMATS 核心管线状态。</p></div></header>
        <div class="grid grid-2">
          <div class="card">
            <div style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">可选大模型配置</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 18px;">
              仅用于报告里的 AI 叙述解读（不配置也可完整运行 rMATS 分析与 ESM-2 排序）。密钥仅保存在本机。
            </div>
            <div class="model-config-body" style="display: block;">
              <div class="cfg-row"><label for="cfg-base">Base URL</label><input id="cfg-base" type="text" autocomplete="off" placeholder="https://api.deepseek.com"></div>
              <div class="cfg-row"><label for="cfg-model">模型名</label><input id="cfg-model" type="text" autocomplete="off" placeholder="deepseek-flash"></div>
              <div class="cfg-row"><label for="cfg-key">API Key</label><input id="cfg-key" type="password" autocomplete="off" placeholder="留空则保持当前密钥"></div>
              <div class="cfg-row">
                <button class="btn btn-primary btn-sm" id="cfg-save" type="button" onclick="saveModelConfig()">保存并启用</button>
                <span class="cfg-msg" id="cfg-msg"></span>
              </div>
              <div class="cfg-row" style="margin-top: 12px;">
                <span class="status status-waiting" id="cfg-status"><span class="status-dot"></span><span id="cfg-status-text">检查中…</span></span>
              </div>
              <div class="cfg-hint">密钥仅保存在本机 .env，保存后即时生效。</div>
            </div>
          </div>

          <div class="card">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px;flex-wrap:wrap;">
              <div style="font-size: 16px; font-weight: 600;">ESM-2-650M LoRA 免疫原性服务</div>
              <span class="status status-waiting" id="esm2-cfg-status"><span class="status-dot"></span><span id="esm2-cfg-status-text">检测中…</span></span>
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">
              对接 128 核服务器或 Hugging Face Space 的 ESM-2-650M LoRA 5 折集成服务，激活第 6 维 T 细胞免疫原性与 TCR 热点标注；保存后即时生效，无需重启。
            </div>
            <div class="model-config-body" style="display: block;">
              <div class="cfg-row"><label for="esm2-cfg-url">服务地址</label><input id="esm2-cfg-url" type="text" autocomplete="off" placeholder="https://xxx.trycloudflare.com 或 http://127.0.0.1:8090"></div>
              <div class="cfg-row"><label for="esm2-cfg-key">API Key</label><input id="esm2-cfg-key" type="password" autocomplete="off" placeholder="留空则保持当前密钥"></div>
              <div class="cfg-row">
                <button class="btn btn-primary btn-sm" id="esm2-cfg-save" type="button" onclick="saveEsm2Config()">保存并测试连通</button>
                <button class="btn btn-secondary btn-sm" type="button" onclick="loadEsm2Config(true)">重新检测</button>
                <span class="cfg-msg" id="esm2-cfg-msg"></span>
              </div>
              <div class="cfg-hint" id="esm2-cfg-detail" style="margin-top:8px;">支持 rMATS 五类剪接表 → ORF 自动重建 → IEDB NetMHCpan-4.1 + ESM-2-650M LoRA 6 维融合排序。</div>
            </div>
          </div>
        </div>

        <div class="grid grid-2" style="margin-top: 20px;">
          <div class="card">
            <div style="font-size: 16px; font-weight: 650; margin-bottom: 12px;">外观与交互偏好</div>
            <div class="pref-list">
              <div class="pref-row">
                <div>
                  <div class="pref-name">界面主题</div>
                  <div class="pref-desc">在明亮的实验室浅色模式与低眩光深色模式之间切换</div>
                </div>
                <div class="seg" role="group" aria-label="界面主题" id="theme-seg">
                  <button type="button" data-theme-pref="light" onclick="setTheme('light')">浅色</button>
                  <button type="button" data-theme-pref="dark" onclick="setTheme('dark')">深色</button>
                  <button type="button" data-theme-pref="system" onclick="setTheme('system')">跟随系统</button>
                </div>
              </div>
              <div class="pref-row">
                <div>
                  <div class="pref-name">侧边导航栏</div>
                  <div class="pref-desc">收起为紧凑图标栏，留出更宽敞的表格与图表画布</div>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" id="sidebar-density-btn" onclick="toggleSidebarCompact()">切换紧凑模式</button>
              </div>
              <div class="pref-row">
                <div>
                  <div class="pref-name">界面过渡动效</div>
                  <div class="pref-desc">关闭后立即禁用页面切换与按钮涟漪动效</div>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" id="motion-toggle" onclick="toggleMotion()" aria-pressed="true">动态：开</button>
              </div>
            </div>
          </div>

          <div class="card">
            <div style="font-size: 16px; font-weight: 650; margin-bottom: 12px;">快捷键速查</div>
            <div class="kbd-list">
              <kbd>Ctrl + K</kbd><span>打开快捷跳转命令面板</span>
              <kbd>Ctrl + B</kbd><span>折叠 / 展开左侧导航栏</span>
              <kbd>Alt + 1 ~ 6</kbd><span>快速切换核心工作区页面</span>
              <kbd>Esc</kbd><span>关闭当前弹窗或项目详情抽屉</span>
            </div>
          </div>
        </div>
      </div>
    <div class="page" id="page-neoantigen">
      <div class="pep-workspace">
        <header class="workspace-heading" style="margin-bottom:18px;">
          <div>
            <h1>新抗原筛选</h1>
            <p>从当前项目的剪接事件一键筛选候选新抗原，或直接粘贴肽段快速预测 HLA 结合。</p>
          </div>
          <div class="neo-mode-tabs" role="tablist" aria-label="筛选模式">
            <button type="button" class="neo-mode-tab active" id="neo-tab-project" role="tab" aria-selected="true" onclick="neoSwitchMode('project')">从当前项目筛选</button>
            <button type="button" class="neo-mode-tab" id="neo-tab-direct" role="tab" aria-selected="false" onclick="neoSwitchMode('direct')">直接输入肽段</button>
          </div>
        </header>

        <!-- Mode 1: Streamlined One-Click Project Screening -->
        <div id="neo-mode-project">
          <div class="neo-bar">
            <div id="neo-readiness" aria-live="polite" style="color:var(--text-secondary);">正在读取当前项目状态…</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
              <button type="button" class="status status-waiting" id="neo-esm2-pill" onclick="navigateTo('settings')" title="点击前往设置配置或检测 ESM-2 服务" style="cursor:pointer;"><span class="status-dot"></span><span id="neo-esm2-pill-text">ESM-2 检测中…</span></button>
              <button class="btn btn-secondary btn-sm" type="button" id="neo-check" onclick="checkNeoReadiness()">刷新状态</button>
              <button class="btn btn-secondary btn-sm" type="button" onclick="document.getElementById('neo-cds-file').click()">上传 CDS 表…</button>
              <input id="neo-cds-file" type="file" accept=".tsv,.csv,.txt" style="display:none;" onchange="uploadCdsTable(this)">
            </div>
          </div>

          <div id="neo-mapping-panel" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:14px;margin:0 0 18px;background:rgba(255,255,255,.02);">
            <div style="font-weight:600;margin-bottom:4px;">确认 CDS 表的列含义</div>
            <p id="neo-mapping-note" style="margin:0 0 10px;font-size:13px;color:var(--text-muted);">这张表的列名不是标准写法，系统已按内容猜测。核对四项后点击确认即可。</p>
            <div id="neo-mapping-fields" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;"></div>
            <div id="neo-mapping-preview" style="margin-top:10px;overflow-x:auto;"></div>
            <div style="display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap;">
              <button class="btn btn-secondary btn-sm" type="button" onclick="saveColumnMapping()">确认这套对应关系</button>
              <span id="neo-mapping-status" style="font-size:12px;color:var(--text-muted);"></span>
            </div>
          </div>

          <div class="pep-layout">
            <div class="pep-inputs">
              <section class="pep-section">
                <h3>1. 选择 HLA 型别</h3>
                <p style="margin:4px 0 10px;color:var(--text-secondary);font-size:13px;">
                  点击常用面板一键填入，或输入逗号分隔的 HLA（留空则仅生成跨连接点候选肽，不联网预测）。
                </p>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 10px;">
                  <button class="btn btn-secondary btn-sm" type="button" onclick="neoUsePanel('class1_common')">常用 MHC-I 面板</button>
                  <button class="btn btn-secondary btn-sm" type="button" onclick="neoUsePanel('class2_common')">常用 MHC-II 面板</button>
                  <button class="btn btn-secondary btn-sm" type="button" onclick="neoClearAlleles()">清空</button>
                </div>
                <input id="neo-hla" type="text" list="pep-allele-list" autocomplete="off" spellcheck="false"
                  placeholder="例如 HLA-A*02:01, HLA-B*07:02"
                  style="display:block;width:100%;padding:10px;font-size:13px;">
                <div id="neo-allele-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;"></div>
              </section>

              <section class="pep-section">
                <h3>2. 数据来源与正常蛋白组过滤（可选）</h3>
                <div id="neo-selected-events-box" class="neo-hint-box" style="display:none;">
                  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;">
                    <span id="neo-selected-events-title">已从事件浏览器带入指定事件</span>
                    <button type="button" class="btn btn-secondary btn-sm" style="min-height:26px;padding:2px 10px;font-size:12px;" onclick="clearSelectedEvents()">恢复自动选取</button>
                  </div>
                  <div id="neo-selected-events-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;"></div>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div>
                    <label for="neo-cds-select" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:6px;">编码序列表（CDS）</label>
                    <select id="neo-cds-select" style="width:100%;padding:8px;font-size:13px;"></select>
                    <div id="neo-cds-hint" style="font-size:12px;color:var(--text-muted);margin-top:4px;"></div>
                  </div>
                  <div>
                    <label for="neo-fasta-select" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:6px;">正常蛋白组去重 FASTA（可选）</label>
                    <div style="display:flex;gap:6px;align-items:center;">
                      <select id="neo-fasta-select" style="flex:1;padding:8px;font-size:13px;"><option value="">不进行正常蛋白组过滤</option></select>
                      <button class="btn btn-secondary btn-sm" type="button" onclick="document.getElementById('neo-fasta-file').click()" style="white-space:nowrap;">上传…</button>
                      <input id="neo-fasta-file" type="file" accept=".fa,.fasta,.faa" style="display:none;" onchange="uploadSelfFasta(this)">
                    </div>
                    <div id="neo-fasta-hint" style="font-size:12px;color:var(--text-muted);margin-top:4px;">上传正常参考蛋白组后，自动标记是否命中自身蛋白。</div>
                  </div>
                </div>

                <details style="margin-top:16px;padding:12px 14px;border:1px solid var(--border);border-radius:10px;">
                  <summary style="cursor:pointer;font-size:13px;font-weight:500;color:var(--text-secondary);">更多参数（MHC 类别 / 预测器 / ORF 重建选项）</summary>
                  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:12px;">
                    <div>
                      <label for="neo-mhc-class" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">MHC 类别</label>
                      <select id="neo-mhc-class" style="width:100%;padding:8px;font-size:13px;">
                        <option value="class1">class1（MHC-I，8–11 aa）</option>
                        <option value="class2">class2（MHC-II，11–30 aa）</option>
                        <option value="both" selected>both（按 HLA 类别自动拆分）</option>
                      </select>
                    </div>
                    <div>
                      <label for="neo-predictor" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">预测器</label>
                      <select id="neo-predictor" style="width:100%;padding:8px;font-size:13px;">
                        <option value="iedb">IEDB（在线，默认）</option>
                        <option value="local" id="neo-predictor-local">MHCflurry（本地，需安装）</option>
                        <option value="auto">auto（本地优先，失败转 IEDB）</option>
                      </select>
                    </div>
                    <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-secondary);">
                      <input type="checkbox" id="neo-processing" checked> 加工预测（proteasome / TAP）
                    </label>
                    <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-secondary);">
                      <input type="checkbox" id="neo-lookup"> 查询 IEDB 已知表位
                    </label>
                    <div>
                      <label for="orf-source" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">自动重建 ORF 参考源</label>
                      <select id="orf-source" onchange="toggleOrfSource()" style="width:100%;padding:8px;font-size:13px;">
                        <option value="ensembl">Ensembl REST（在线 GRCh38）</option>
                        <option value="local">本地 GTF + FASTA（离线）</option>
                      </select>
                    </div>
                    <div>
                      <label for="orf-max-events" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">自动重建最多事件数</label>
                      <input id="orf-max-events" type="number" value="20" min="1" max="200" style="width:100%;padding:8px;font-size:13px;">
                    </div>
                    <div>
                      <label for="orf-fdr" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">ORF 筛选 FDR 上限</label>
                      <input id="orf-fdr" type="number" value="0.05" step="0.01" min="0" style="width:100%;padding:8px;font-size:13px;">
                    </div>
                    <div>
                      <label for="orf-dpsi" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">ORF 筛选 |ΔPSI| 下限</label>
                      <input id="orf-dpsi" type="number" value="0.1" step="0.05" min="0" style="width:100%;padding:8px;font-size:13px;">
                    </div>
                  </div>
                  <div id="orf-local-fields" style="display:none;margin-top:10px;">
                    <label for="orf-gtf" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">GTF 文件路径</label>
                    <input id="orf-gtf" type="text" placeholder="例如 annotation.gtf" style="display:block;width:100%;padding:8px;margin-bottom:8px;font-size:13px;">
                    <label for="orf-fasta" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:4px;">基因组 FASTA 路径</label>
                    <input id="orf-fasta" type="text" placeholder="例如 genome.fa" style="display:block;width:100%;padding:8px;font-size:13px;">
                  </div>
                  <label style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-muted);margin-top:10px;">
                    <input type="checkbox" id="neo-force-rebuild"> 忽略已有 CDS 表，本次重新从 rMATS 坐标重建 ORF
                  </label>
                </details>
              </section>
            </div>

            <aside class="pep-options">
              <section class="pep-section">
                <h3>一键筛选</h3>
                <p class="pep-help">缺少 CDS 表时自动从 rMATS 坐标重建 ORF，再完成候选肽生成、去重过滤与综合排序。</p>
                <div style="margin-top:14px;">
                  <button class="btn btn-primary" type="button" id="neo-guided-run" onclick="runUnifiedNeoantigen()">一键筛选新抗原</button>
                </div>
                <div id="neo-progress-box" style="display:none;margin-top:14px;padding:12px;border-radius:10px;background:var(--surface-2);border:1px solid var(--border);">
                  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px;margin-bottom:7px;">
                    <span id="neo-progress-pct" style="font-weight:700;color:var(--accent);">0%</span>
                    <span id="neo-progress-elapsed" style="font-family:var(--font-mono);color:var(--text-muted);">0.0s</span>
                  </div>
                  <div style="height:7px;border-radius:999px;background:var(--surface-3);overflow:hidden;">
                    <div id="neo-progress-bar" style="height:100%;width:0%;background:var(--brand-grad);transition:width .3s ease;"></div>
                  </div>
                  <div id="neo-progress-stage" style="margin-top:8px;font-size:12px;color:var(--text-secondary);line-height:1.5;">准备中…</div>
                </div>
                <div id="neo-status" role="status" aria-live="polite" style="margin-top:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;color:var(--text-secondary);"></div>
                <div id="neo-errors" style="margin-top:8px;"></div>
              </section>
              <div class="pep-guide">
                <h3>快速判读</h3>
                <p><b>% Rank 越低越好</b>：&lt;0.5% 为强结合，0.5–2% 为弱结合。</p>
                <p>免疫原性分为 Calis (2013) 本地倾向分（正值更优）；NMD 风险提示可能发生无义介导降解。</p>
                <p style="color:var(--text-muted);">计算预测不等于真实呈递或免疫原性，最终靶点需实验验证。</p>
              </div>
            </aside>
          </div>

          <section class="pep-output" id="neo-result-panel" style="display:none;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:8px;">
              <div>
                <h3 style="margin:0 0 4px;">筛选结果</h3>
                <div id="neo-result-summary" style="font-size:13px;color:var(--text-secondary);"></div>
              </div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <button class="btn btn-primary btn-sm" type="button" onclick="exportNeoFilteredFasta()">导出 FASTA</button>
                <button class="btn btn-secondary btn-sm" type="button" onclick="exportNeoFilteredCsv()">导出合成清单 CSV</button>
                <button class="btn btn-secondary btn-sm" type="button" onclick="revealNeoResult()">打开结果目录</button>
              </div>
            </div>

            <div class="neo-filter-bar" id="neo-filter-bar">
              <select id="neo-filter-tier" onchange="renderNeoRankedTable()" aria-label="按结合分级筛选">
                <option value="all">全部结合分级</option>
                <option value="strong">仅强结合 (&lt;0.5%)</option>
                <option value="usable">强 + 弱结合 (&lt;2%)</option>
              </select>
              <input id="neo-filter-search" type="text" placeholder="搜索基因 / 肽段 / 事件ID…" oninput="renderNeoRankedTable()" style="width:200px;">
              <label style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-secondary);cursor:pointer;">
                <input type="checkbox" id="neo-filter-novel" onchange="renderNeoRankedTable()"> 排除正常蛋白命中
              </label>
              <label style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-secondary);cursor:pointer;">
                <input type="checkbox" id="neo-filter-lc" onchange="renderNeoRankedTable()"> 排除低复杂度
              </label>
              <label style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-secondary);cursor:pointer;">
                <input type="checkbox" id="neo-filter-nmd" onchange="renderNeoRankedTable()"> 排除 NMD 风险
              </label>
              <span id="neo-filter-count" style="font-size:12px;color:var(--text-muted);margin-left:auto;"></span>
            </div>

            <div id="neo-result-body"></div>
            <div id="neo-epitope-matches"></div>
            <div id="neo-result-files" style="margin-top:12px;display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--text-muted);"></div>
          </section>
        </div>

        <!-- Mode 2: Direct Peptide Sequence Prediction -->
        <div id="neo-mode-direct" style="display:none;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
            <p style="margin:0;color:var(--text-secondary);font-size:14px;">手里已有候选肽序列？直接粘贴即可比较 HLA 结合能力与加工打分。</p>
            <button type="button" class="btn btn-secondary btn-sm" onclick="pepFillExample()">填入示例</button>
          </div>
          <div class="pep-layout"><div class="pep-inputs">
            <section class="pep-section">
              <h3><label for="pep-sequences">候选肽序列</label></h3>
              <p style="margin:6px 0 10px;color:var(--text-secondary);font-size:13px;">
                每行一个肽段（支持 FASTA 格式）；<b>MHC-I 用 8–11 aa，MHC-II 用 11–30 aa</b>，页面单次最多 200 条肽、8 个 HLA。
              </p>
              <textarea id="pep-sequences" rows="7" spellcheck="false"
                style="display:block;width:100%;padding:10px;margin:8px 0 6px;border:1px solid var(--border);border-radius:var(--radius);background:transparent;color:var(--text);font-family:var(--font-mono,monospace);font-size:13px;line-height:1.6;resize:vertical;"
                placeholder="SLYNTVATL&#10;GILGFVFTL&#10;NLVPMVATV"></textarea>
              <div id="pep-seq-count" role="status" aria-live="polite" style="font-size:12px;color:var(--text-muted);">已识别 0 条肽段</div>
            </section>
            <section class="pep-section">
              <h3><label for="pep-alleles">HLA 型别</label></h3>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 10px;">
                <button class="btn btn-secondary btn-sm" type="button" onclick="pepUsePanel('class1_common')">常用 MHC-I 面板</button>
                <button class="btn btn-secondary btn-sm" type="button" onclick="pepUsePanel('class2_common')">常用 MHC-II 面板</button>
                <button class="btn btn-secondary btn-sm" type="button" onclick="pepClearAlleles()">清空型别</button>
              </div>
              <input id="pep-alleles" type="text" list="pep-allele-list" autocomplete="off" spellcheck="false"
                placeholder="例如 HLA-A*02:01, HLA-B*07:02"
                style="display:block;width:100%;padding:10px;border:1px solid var(--border);border-radius:var(--radius);background:transparent;color:var(--text);font-family:inherit;font-size:13px;">
              <datalist id="pep-allele-list"></datalist>
              <div id="pep-allele-hint" style="font-size:12px;color:var(--text-muted);margin-top:6px;">参考表尚未加载。</div>
              <div id="pep-allele-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;"></div>
            </section>
          </div>
          <aside class="pep-options"><section class="pep-section">
            <h3>预测设置</h3><p class="pep-help">先选类别，再点击预测。在线预测需要联网。</p>
            <div style="display:grid;grid-template-columns:1fr;gap:14px;margin-top:12px;">
              <div>
                <label for="pep-mhc-class" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:6px;">MHC 类别</label>
                <select id="pep-mhc-class" style="width:100%;padding:8px;border:1px solid var(--border);border-radius:var(--radius-sm);background:transparent;color:var(--text);font-family:inherit;font-size:13px;">
                  <option value="class1">class1（MHC-I，8–11 aa）</option>
                  <option value="class2">class2（MHC-II，11–30 aa）</option>
                  <option value="both">both（按类别拆分）</option>
                </select>
              </div>
              <div>
                <label for="pep-predictor" style="display:block;font-size:12px;color:var(--text-secondary);margin-bottom:6px;">预测器</label>
                <select id="pep-predictor" style="width:100%;padding:8px;border:1px solid var(--border);border-radius:var(--radius-sm);background:transparent;color:var(--text);font-family:inherit;font-size:13px;">
                  <option value="iedb">IEDB（在线）</option>
                  <option value="local" id="pep-predictor-local">MHCflurry（本地，需安装）</option>
                  <option value="auto">auto（本地优先，失败转 IEDB）</option>
                </select>
              </div>
              <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-secondary);">
                <input type="checkbox" id="pep-processing" checked> 加工预测（proteasome / TAP）
              </label>
              <label style="display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-secondary);">
                <input type="checkbox" id="pep-lookup"> 查询 IEDB 已知表位
              </label>
            </div>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px;">
              <button class="btn btn-primary" type="button" id="pep-predict-btn" onclick="pepPredict()">预测并排序</button>
              <span id="pep-capabilities" style="font-size:12px;color:var(--text-muted);"></span>
            </div>
          </section><div class="pep-guide"><h3>如何看结果？</h3><p><b>Percentile rank 越低越好。</b>&lt;0.5% 为强结合，&lt;2% 为弱结合。</p><p>结合预测不等于抗原呈递或免疫原性。</p></div></aside></div>
          <section class="pep-output">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
              <h3 style="margin:0;">预测结果</h3>
              <button type="button" class="btn btn-secondary btn-sm" id="pep-export-csv" onclick="pepExportCsv()" style="display:none;">导出 CSV</button>
            </div>
            <div id="pep-status" role="status" aria-live="polite" style="white-space:pre-wrap;margin-top:8px;"></div>
            <div id="pep-errors"></div><div id="pep-results" style="margin-top:14px;"></div>
          </section>
        </div>
      </div>
    </div>
  </main>
</div>

<div class="detail-drawer-backdrop" id="detail-backdrop" onclick="closeProjectDetail()" aria-hidden="true"></div>
<section class="card detail-drawer" id="project-detail" aria-label="历史项目详情">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px;flex-wrap:wrap;">
    <div>
      <div style="font-size:12px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);">历史项目详情</div>
      <div style="font-size:20px;font-weight:600;margin-top:4px;" id="detail-title">-</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:6px;" id="detail-meta">-</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <button class="btn btn-sm btn-secondary" type="button" onclick="closeProjectDetail()">关闭详情</button>
      <button class="btn btn-sm btn-secondary" type="button" onclick="openReport('html')">打开 HTML 报告</button>
      <button class="btn btn-sm btn-secondary" type="button" onclick="openReport('pdf')">下载 PDF</button>
      <button class="btn btn-sm btn-secondary" type="button" onclick="revealProjectBundle()">成果文件夹</button>
      <button class="btn btn-sm btn-secondary" type="button" onclick="packageProject()">打包 ZIP</button>
      <button class="btn btn-sm btn-secondary" type="button" onclick="jumpToExplorer()">浏览全部事件</button>
      <button class="btn btn-sm btn-danger" type="button" onclick="deleteCurrentProject()" style="color:var(--danger);">删除项目</button>
    </div>
  </div>
  <div id="detail-bundle-hint" style="font-size:12px;color:var(--text-muted);margin:-6px 0 10px;"></div>
  <div class="grid grid-2" style="gap:20px;">
    <div>
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin-bottom:10px;">样本分组</div>
      <div id="detail-groups" style="display:flex;flex-wrap:wrap;gap:8px;"></div>
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin:20px 0 10px;">事件类型分布</div>
      <div id="detail-types" style="display:flex;flex-wrap:wrap;gap:8px;"></div>
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin:20px 0 10px;">流程日志（最近 12 条）</div>
      <div id="detail-logs" style="max-height:220px;overflow:auto;font-size:12px;line-height:1.7;"></div>
    </div>
    <div>
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin-bottom:10px;">图表（点击放大）</div>
      <div id="detail-figures" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;"></div>
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin:20px 0 10px;">候选事件 Top 10</div>
      <div id="detail-candidates" style="max-height:260px;overflow:auto;font-size:12px;"></div>
    </div>
  </div>
</section>

<dialog id="quick-dialog" class="quick-dialog" aria-labelledby="quick-title">
  <div class="quick-head"><h2 id="quick-title">快速前往工作区</h2><button type="button" class="btn btn-secondary btn-sm" onclick="closeQuickSwitch()" aria-label="关闭快捷跳转">关闭</button></div>
  <div class="quick-search"><input id="quick-search" type="search" placeholder="搜索页面，如 肽预测、报告…" aria-label="搜索工作区" autocomplete="off" oninput="filterQuickSwitch()"></div>
  <div class="quick-results" id="quick-results"></div>
</dialog>
<!-- Upload Modal -->
<div role="dialog" aria-modal="true" aria-label="新建分析项目" id="upload-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--white); z-index: 1000; align-items: center; justify-content: center;">
  <div style="background: var(--white); border: 1px solid var(--gray-300); border-radius: var(--radius); padding: 32px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <h2 style="font-size: 20px; font-weight: 600; color: var(--black);">新建分析项目</h2>
      <button onclick="closeUploadModal()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: var(--gray-700);">×</button>
    </div>
    <div style="margin-bottom: 20px;">
      <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--gray-700);">项目名称</label>
      <input type="text" id="project-name" placeholder="输入项目名称（如 My_RNA_Study）" style="width: 100%; padding: 10px; border: 1px solid var(--gray-300); border-radius: var(--radius); font-size: 14px; font-family: var(--font-sans); color: var(--gray-900); background: var(--white);">
    </div>
    <div style="margin-bottom: 20px;">
      <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--gray-700);">分析查询</label>
      <input type="text" id="analysis-query" placeholder="输入分析查询（如 compare treatment vs control）" style="width: 100%; padding: 10px; border: 1px solid var(--gray-300); border-radius: var(--radius); font-size: 14px; font-family: var(--font-sans); color: var(--gray-900); background: var(--white);">
    </div>
    <div style="margin-bottom: 24px;">
      <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--gray-700);">上传文件</label>
      <div id="drop-zone" role="button" tabindex="0" aria-label="选择数据文件" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();document.getElementById('file-input').click();}" style="border: 2px dashed var(--gray-300); border-radius: var(--radius); padding: 40px; text-align: center; cursor: pointer; transition: all 0.2s; background: var(--gray-100);" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)" ondrop="handleDrop(event)" onclick="document.getElementById('file-input').click()">
        <div style="font-size: 36px; margin-bottom: 12px;"></div>
        <div style="font-size: 14px; color: var(--gray-700);">拖拽文件到此处，或点击选择文件</div>
        <div style="font-size: 12px; color: var(--gray-500); margin-top: 8px;">支持 CSV、TSV、TXT、文本 .xls、Excel .xls/.xlsx/.xlsm 及压缩文本 .gz；表达量表会被识别并提示所需事件数据</div>
      </div>
      <input type="file" id="file-input" multiple style="display: none;" onchange="handleFileSelect(event)">
      <input type="file" id="report-directory-input" webkitdirectory directory multiple style="display: none;" onchange="handleReportDirectory(event)">
      <button type="button" class="btn btn-secondary" style="margin-top: 10px;" onclick="document.getElementById('report-directory-input').click()">选择华大报告目录</button>
      <div id="file-list" style="margin-top: 12px;"></div>
    </div>
    <div style="display: flex; gap: 12px; justify-content: flex-end;">
      <button class="btn btn-secondary" onclick="closeUploadModal()">取消</button>
      <button class="btn btn-primary" id="start-analysis-btn" onclick="startAnalysis()" disabled>开始分析</button>
    </div>
  </div>
</div>

<!-- Smart Ingestion Review Modal -->
<div id="ingest-modal" role="dialog" aria-modal="true" aria-labelledby="ingest-title">
  <div class="ingest-panel">
    <div class="ingest-head">
      <div>
        <div class="ingest-title" id="ingest-title">智能接入检查</div>
        <div class="ingest-sub" id="ingest-sub">Agent 已读取数据结构，请确认字段映射后开始分析。</div>
      </div>
      <button class="ingest-close" type="button" onclick="closeIngestModal()" aria-label="关闭">×</button>
    </div>
    <div class="ingest-body" id="ingest-body"></div>
    <div class="ingest-footer">
      <div class="ingest-error" id="ingest-error"></div>
      <button class="btn btn-secondary" type="button" id="ingest-cancel" onclick="closeIngestModal()">取消</button>
      <button class="btn btn-primary" type="button" id="ingest-confirm" onclick="confirmIngest()">确认映射并分析</button>
    </div>
  </div>
</div>

<script>
const state = { currentProject: localStorage.getItem('epitoperank.currentProject'), projects: [], analysisStatus: null, detail: null, storage: null, events: [], eventPage: 1, eventPages: 1, eventTotal: 0, currentPage: 'dashboard' };
let neoResultDir = '', neoRankedRows = [], neoSortKey = 'rank', neoSortDir = 1, neoMode = 'project';
const neoSelectedEvents = new Set();
const NEO_CR = String.fromCharCode(13), NEO_LF = String.fromCharCode(10), NEO_TAB = String.fromCharCode(9);
// 中文备注：切换新抗原工作台的两个模式（项目一键筛选 / 直接输入肽段）。
function neoSwitchMode(mode) {
  neoMode = mode === 'direct' ? 'direct' : 'project';
  const proj = document.getElementById('neo-mode-project');
  const direct = document.getElementById('neo-mode-direct');
  const tabProj = document.getElementById('neo-tab-project');
  const tabDirect = document.getElementById('neo-tab-direct');
  if (proj) proj.style.display = neoMode === 'project' ? 'block' : 'none';
  if (direct) direct.style.display = neoMode === 'direct' ? 'block' : 'none';
  if (tabProj) { tabProj.classList.toggle('active', neoMode === 'project'); tabProj.setAttribute('aria-selected', String(neoMode === 'project')); }
  if (tabDirect) { tabDirect.classList.toggle('active', neoMode === 'direct'); tabDirect.setAttribute('aria-selected', String(neoMode === 'direct')); }
  if (neoMode === 'direct') {
    pepInitPage();
  }
}
function neoInitPage() {
  pepBindOnce();
  if (!pepState.loaded) { pepLoadMeta(); pepRefreshReference(); }
  neoBindOnce();
  neoRenderChips();
  renderSelectedEventsBox();
  checkNeoReadiness();
  restoreNeoStateForProject();
  loadEsm2Config(false);
}
let neoBound = false;
function neoBindOnce() {
  if (neoBound) return;
  neoBound = true;
  const hlaInput = document.getElementById('neo-hla');
  if (hlaInput) {
    hlaInput.addEventListener('input', () => { neoRenderChips(); });
    hlaInput.addEventListener('change', () => { neoRenderChips(); });
  }
}
function neoTokens() {
  const input = document.getElementById('neo-hla');
  if (!input) return [];
  return Array.from(new Set(input.value.split(/[,;\\s]+/).map(v => v.trim()).filter(Boolean)));
}
function neoRenderChips() {
  const wrap = document.getElementById('neo-allele-chips');
  if (!wrap) return;
  wrap.replaceChildren();
  neoTokens().forEach(token => {
    const chip = document.createElement('span');
    chip.className = 'neo-chip';
    chip.textContent = token + ' ×';
    chip.title = '点击移除 ' + token;
    chip.onclick = () => {
      document.getElementById('neo-hla').value = neoTokens().filter(v => v !== token).join(', ');
      neoRenderChips();
    };
    wrap.appendChild(chip);
  });
}
function neoUsePanel(name) {
  const panel = name === 'class2_common' ? PEP_CLASS2_PANEL : PEP_CLASS1_PANEL;
  document.getElementById('neo-hla').value = panel.slice(0, 6).join(', ');
  const mhcSelect = document.getElementById('neo-mhc-class');
  if (mhcSelect) mhcSelect.value = name === 'class2_common' ? 'class2' : 'class1';
  neoRenderChips();
}
function neoClearAlleles() {
  const input = document.getElementById('neo-hla');
  if (input) input.value = '';
  neoRenderChips();
}
// 中文备注：检查当前项目的新抗原分析就绪状态（数据目录、CDS 表与可选参考 FASTA）。
async function checkNeoReadiness() {
  const resultBox = document.getElementById('neo-readiness');
  const runButton = document.getElementById('neo-guided-run');
  const button = document.getElementById('neo-check');
  if (!resultBox || !runButton) return;
  if (!state.currentProject) {
    resultBox.textContent = '尚未选择项目。请先在仪表盘选择或新建项目，或切换到「直接输入肽段」。';
    runButton.disabled = true;
    renderCdsChoices({ cds_files: [] });
    renderFastaChoices([]);
    return;
  }
  const projectId = state.currentProject;
  if (button) button.disabled = true;
  resultBox.textContent = '正在读取项目状态…';
  try {
    const response = await fetch('/api/neoantigen/readiness/' + encodeURIComponent(projectId));
    const data = await response.json(); if (!response.ok) throw new Error(data.detail || '检查失败');
    if (projectId !== state.currentProject) return;
    const files = data.cds_files || [];
    const cdsNote = files.length
      ? '已识别 ' + files.length + ' 份 CDS 表'
      : ((data.rmats_files || []).length ? '未建 CDS 表（点击筛选时将自动从 rMATS 重建 ORF）' : '未找到 CDS 表（请先上传）');
    resultBox.innerHTML = '<strong>' + neoEscape(data.project_name) + '</strong> · '
      + Number(data.event_count || 0) + ' 个剪接事件 · ' + neoEscape(cdsNote);
    renderCdsChoices(data);
    renderFastaChoices(data.fasta_files || []);
    neoReadiness = data;
    renderColumnMapping(data);
    const canRun = files.length > 0 || (data.rmats_files || []).length > 0;
    runButton.disabled = !canRun;
  } catch (error) {
    const message = String(error.message || error);
    resultBox.textContent = message.includes('input_dir must be inside')
      ? '无法访问此项目的原始数据目录。' : '状态检查失败：' + message;
    runButton.disabled = true;
  } finally {
    if (button) button.disabled = false;
  }
}
function renderCdsChoices(data) {
  const select = document.getElementById('neo-cds-select');
  const hint = document.getElementById('neo-cds-hint');
  if (!select) return;
  const files = (data && data.cds_files) || [];
  const hasRmats = ((data && data.rmats_files) || []).length > 0;
  select.replaceChildren();
  if (!files.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = hasRmats ? '自动从 rMATS 坐标重建 ORF' : '（暂无 CDS 表，请先上传）';
    select.appendChild(option);
    select.disabled = true;
    if (hint) hint.textContent = hasRmats ? '点击「一键筛选新抗原」会自动在线重建编码序列并继续。' : '点顶部「上传 CDS 表…」补充。';
    const mp = document.getElementById('neo-mapping-panel');
    if (mp) mp.style.display = 'none';
    return;
  }
  files.forEach(name => {
    const option = document.createElement('option');
    option.value = name; option.textContent = name;
    select.appendChild(option);
  });
  const preferred = (data.cds_selected && files.indexOf(data.cds_selected) >= 0) ? data.cds_selected : files[0];
  select.value = preferred; select.disabled = false;
  select.onchange = () => renderColumnMapping(neoReadiness);
  if (hint) hint.textContent = files.length > 1 ? '已选 ' + preferred + '（共 ' + files.length + ' 份可切换）' : '已自动选中，无需手动配置。';
}
function renderFastaChoices(files) {
  const select = document.getElementById('neo-fasta-select');
  if (!select) return;
  const current = select.value;
  select.replaceChildren();
  const noneOpt = document.createElement('option');
  noneOpt.value = ''; noneOpt.textContent = '不进行正常蛋白组过滤';
  select.appendChild(noneOpt);
  (files || []).forEach(name => {
    const opt = document.createElement('option');
    opt.value = name; opt.textContent = name;
    select.appendChild(opt);
  });
  if (current && (files || []).indexOf(current) >= 0) select.value = current;
}
const NEO_FIELD_ORDER = ['event_id', 'reference_cds', 'altered_cds', 'junction_nt'];
const NEO_FIELD_FALLBACK = {event_id:'事件 ID', reference_cds:'参考（正常）编码序列',
  altered_cds:'改变后（变异）编码序列', junction_nt:'新剪接连接点位置（整数）'};
let neoReadiness = null;
function neoClip(value, limit) { const text = String(value == null ? '' : value); return text.length > limit ? text.slice(0, limit) + '…' : text; }
function renderColumnMapping(data) {
  const panel = document.getElementById('neo-mapping-panel');
  const fields = document.getElementById('neo-mapping-fields');
  const preview = document.getElementById('neo-mapping-preview');
  const status = document.getElementById('neo-mapping-status');
  if (!panel || !data) return;
  const name = (document.getElementById('neo-cds-select').value || data.cds_selected || '');
  const detail = (data.cds_details || {})[name];
  if (!detail || !detail.needs_confirmation) { panel.style.display = 'none'; fields.replaceChildren(); preview.innerHTML = ''; return; }
  const labels = data.field_labels || NEO_FIELD_FALLBACK;
  const header = detail.header || [];
  fields.replaceChildren();
  NEO_FIELD_ORDER.forEach(field => {
    const wrap = document.createElement('label');
    wrap.style.cssText = 'display:block;font-size:13px;';
    wrap.appendChild(document.createTextNode(labels[field] || field));
    const select = document.createElement('select');
    select.id = 'neo-map-' + field;
    select.style.cssText = 'display:block;width:100%;padding:8px;margin-top:4px;';
    const blank = document.createElement('option'); blank.value = ''; blank.textContent = '（请选择）';
    select.appendChild(blank);
    header.forEach(column => {
      const option = document.createElement('option');
      option.value = column; option.textContent = column || '（空列名）';
      select.appendChild(option);
    });
    select.value = (detail.map || {})[field] || '';
    wrap.appendChild(select);
    fields.appendChild(wrap);
  });
  const columns = detail.preview || [];
  if (columns.length) {
    const head = columns.map(item => '<th>' + neoEscape(item.column || '（空列名）') + '</th>').join('');
    const body = [0, 1].map(index => '<tr>' + columns.map(item => {
      const value = (item.samples || [])[index] || '';
      return '<td style="max-width:280px;"><span title="' + neoEscape(value) + '">' + neoEscape(neoClip(value, 46)) + '</span></td>';
    }).join('') + '</tr>').join('');
    preview.innerHTML = '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">样本内容（前两行）——用它确认哪列是参考、哪列是改变后</div>'
      + '<table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
  } else {
    preview.innerHTML = '';
  }
  status.textContent = detail.source === 'saved' ? '已保存过映射。' : '自动猜测结果，确认后以后不再询问。';
  panel.style.display = 'block';
}
async function saveColumnMapping() {
  const status = document.getElementById('neo-mapping-status');
  const name = document.getElementById('neo-cds-select').value || '';
  if (!state.currentProject || !name) { status.textContent = '请先选择项目和编码序列表。'; return; }
  const map = {};
  NEO_FIELD_ORDER.forEach(field => {
    const select = document.getElementById('neo-map-' + field);
    map[field] = select ? select.value : '';
  });
  const missing = NEO_FIELD_ORDER.filter(field => !map[field]);
  if (missing.length) { status.textContent = '还有 ' + missing.length + ' 项没有选择。'; return; }
  if (new Set(Object.keys(map).map(key => map[key])).size < NEO_FIELD_ORDER.length) {
    status.textContent = '同一列不能承担两个角色，请分别选择。'; return;
  }
  status.textContent = '正在保存…';
  try {
    const response = await fetch('/api/neoantigen/column-map', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({project_id: state.currentProject, file: name, map: map})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '保存失败');
    const message = data.warning || ('已保存，按这套映射可为 ' + data.verified_rows + ' 行样本生成肽。');
    await checkNeoReadiness();
    document.getElementById('neo-mapping-status').textContent = message;
  } catch (error) { status.textContent = String(error.message || error); }
}
// 中文备注：上传用户选择的参考/剪接 CDS 序列表并更新列映射状态。
async function uploadCdsTable(input) {
  const status = document.getElementById('neo-status');
  const file = input.files && input.files[0];
  if (!file) return;
  if (!state.currentProject) { status.textContent = '请先选择一个项目。'; input.value = ''; return; }
  status.textContent = '正在上传 ' + file.name + '…';
  try {
    const form = new FormData();
    form.append('project_id', state.currentProject);
    form.append('file', file, file.name);
    const response = await fetch('/api/neoantigen/cds-upload', {method:'POST', body:form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '上传失败');
    status.textContent = '已添加 ' + data.saved + '，列：' + (data.columns || []).join('、');
    await checkNeoReadiness();
    document.getElementById('neo-cds-select').value = data.saved;
  } catch (error) { status.textContent = String(error.message || error); }
  finally { input.value = ''; }
}
async function uploadSelfFasta(input) {
  const hint = document.getElementById('neo-fasta-hint');
  const file = input.files && input.files[0];
  if (!file) return;
  if (!state.currentProject) { if (hint) hint.textContent = '请先选择一个项目。'; input.value = ''; return; }
  if (hint) hint.textContent = '正在上传 ' + file.name + '…';
  try {
    const form = new FormData();
    form.append('project_id', state.currentProject);
    form.append('file', file, file.name);
    const response = await fetch('/api/peptide/self-fasta-upload', { method: 'POST', body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '上传失败');
    renderFastaChoices(data.fasta_files || [data.saved]);
    document.getElementById('neo-fasta-select').value = data.saved;
    if (hint) hint.textContent = '已启用正常蛋白组去重：' + data.saved;
  } catch (error) {
    if (hint) hint.textContent = '上传失败：' + String(error.message || error);
  } finally { input.value = ''; }
}
// 中文备注：在已有 CDS 表与在线自动构建 ORF 两种输入来源之间切换界面显示。
function toggleOrfSource() {
  const local = document.getElementById('orf-source').value === 'local';
  const box = document.getElementById('orf-local-fields');
  if (box) box.style.display = local ? 'block' : 'none';
}
// 中文备注：维护事件浏览器勾选的剪接事件集合并联动新抗原工作台。
function updateExplorerSelectBar() {
  const count = neoSelectedEvents.size;
  const label = document.getElementById('explorer-select-count');
  const sendBtn = document.getElementById('explorer-send-neo');
  const clearBtn = document.getElementById('explorer-clear-neo');
  if (label) {
    label.textContent = count
      ? '已勾选 ' + count + ' 个剪接事件，可直接带入「新抗原筛选」重建 ORF 并预测'
      : '勾选感兴趣的剪接事件，可直接带入「新抗原筛选」自动重建 ORF 并预测';
  }
  if (sendBtn) sendBtn.disabled = count === 0;
  if (clearBtn) clearBtn.disabled = count === 0;
  renderSelectedEventsBox();
}
function toggleEventSelection(eventId, checked) {
  if (!eventId) return;
  if (checked) neoSelectedEvents.add(eventId);
  else neoSelectedEvents.delete(eventId);
  updateExplorerSelectBar();
}
function toggleSelectAllEvents(checked) {
  document.querySelectorAll('#events-table input.event-select-cb').forEach(cb => {
    cb.checked = checked;
    if (checked) neoSelectedEvents.add(cb.value);
    else neoSelectedEvents.delete(cb.value);
  });
  updateExplorerSelectBar();
}
function clearSelectedEvents() {
  neoSelectedEvents.clear();
  const allCb = document.getElementById('events-select-all');
  if (allCb) allCb.checked = false;
  document.querySelectorAll('#events-table input.event-select-cb').forEach(cb => { cb.checked = false; });
  updateExplorerSelectBar();
}
function renderSelectedEventsBox() {
  const box = document.getElementById('neo-selected-events-box');
  const chips = document.getElementById('neo-selected-events-chips');
  const title = document.getElementById('neo-selected-events-title');
  if (!box || !chips) return;
  const ids = Array.from(neoSelectedEvents);
  if (!ids.length) { box.style.display = 'none'; chips.replaceChildren(); return; }
  box.style.display = 'block';
  if (title) title.textContent = '已从事件浏览器指定 ' + ids.length + ' 个事件（运行时自动针对这些事件重建 ORF）';
  chips.replaceChildren();
  ids.slice(0, 30).forEach(id => {
    const chip = document.createElement('span');
    chip.className = 'neo-chip';
    chip.textContent = id + ' ×';
    chip.onclick = () => { neoSelectedEvents.delete(id); updateExplorerSelectBar(); };
    chips.appendChild(chip);
  });
  if (ids.length > 30) {
    const more = document.createElement('span');
    more.style.cssText = 'font-size:12px;color:var(--text-muted);';
    more.textContent = '…共 ' + ids.length + ' 个';
    chips.appendChild(more);
  }
}
function sendSelectedEventsToNeo() {
  if (!neoSelectedEvents.size) return;
  neoSwitchMode('project');
  navigateTo('neoantigen');
}

const NEO_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
// 中文备注：对新抗原面板输出文本进行 HTML 实体转义，防止 XSS 注入。
function neoEscape(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, ch => NEO_ESCAPES[ch]); }

let neoPollTimer = 0;
let neoLoadedProject = null;

function setNeoProgressUI(visible, pct, stage, elapsedSec) {
  const box = document.getElementById('neo-progress-box');
  if (!box) return;
  box.style.display = visible ? 'block' : 'none';
  if (!visible) return;
  const pctEl = document.getElementById('neo-progress-pct');
  const barEl = document.getElementById('neo-progress-bar');
  const stageEl = document.getElementById('neo-progress-stage');
  const elEl = document.getElementById('neo-progress-elapsed');
  const p = Math.max(0, Math.min(100, Number(pct || 0)));
  if (pctEl) pctEl.textContent = p + '%';
  if (barEl) barEl.style.width = p + '%';
  if (stageEl && stage) stageEl.textContent = stage;
  if (elEl && elapsedSec !== undefined) elEl.textContent = Number(elapsedSec).toFixed(1) + 's';
}

function applyNeoResultData(data, opts) {
  const options = opts || {};
  const status = document.getElementById('neo-status');
  const errBox = document.getElementById('neo-errors');
  if (errBox) errBox.replaceChildren();
  neoRankedRows = data.ranked_rows || [];
  neoResultDir = data.results_input_dir || '';
  neoLoadedProject = state.currentProject;
  const tiers = data.binding_tiers || {};
  const manifestAlleles = (((data.manifest || {}).options || {}).alleles) || neoTokens();
  const hasAlleles = Array.isArray(manifestAlleles) && manifestAlleles.length > 0;
  const orfNote = data.orf_summary
    ? '已自动重建 ' + Number(data.orf_summary.written) + ' 条 ORF（' + data.orf_summary.reference + ' / ' + data.orf_summary.genome_build + '）；'
    : '';
  const tierNote = hasAlleles
    ? '强结合 ' + Number(tiers.strong_count || 0) + ' 条 · 弱结合 ' + Number(tiers.weak_count || 0) + ' 条 · 非结合 ' + Number(tiers.not_binding_count || 0) + ' 条'
    : '未填 HLA，仅生成候选肽与本地理化/免疫原性特征';
  const prefix = options.restored ? '已加载上次筛选结果：共 ' : (orfNote + '筛选完成：共 ');
  if (status) {
    status.style.color = 'var(--secondary)';
    status.textContent = prefix + Number(data.candidate_count || 0) + ' 条候选肽（' + tierNote + '）。';
  }
  if (errBox && (data.errors || []).length) {
    errBox.innerHTML = '<div style="font-size:12px;color:var(--danger);">注意：' + data.errors.length + ' 条预测警告（'
      + neoEscape(String((data.errors[0] && data.errors[0].error) || data.errors[0])) + '）</div>';
  }
  const summaryEl = document.getElementById('neo-result-summary');
  if (summaryEl) {
    const evTiers = data.tiers || {};
    const evText = Object.keys(evTiers).sort().map(k => k + '层:' + evTiers[k]).join(' · ');
    summaryEl.textContent = '候选 ' + Number(data.candidate_count || 0) + ' 条 · ' + tierNote + (evText ? ' · 证据分层 ' + evText : '');
  }
  const panel = document.getElementById('neo-result-panel');
  if (panel) {
    panel.style.display = 'block';
    if (options.scrollIntoView) {
      setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
    }
  }
  renderNeoRankedTable();
  renderNeoEpitopeMatches(data.epitope_matches || []);
  renderNeoResultFiles(data);
  if (data.orf_summary) checkNeoReadiness();
}

function attachNeoJobPolling(jobId, projectId) {
  if (neoPollTimer) { clearInterval(neoPollTimer); neoPollTimer = 0; }
  const button = document.getElementById('neo-guided-run');
  const status = document.getElementById('neo-status');
  if (button) button.disabled = true;
  if (status) status.textContent = '';

  const tick = async () => {
    try {
      const resp = await fetch('/api/peptide/job/' + encodeURIComponent(jobId));
      if (!resp.ok) throw new Error('筛选任务状态读取失败');
      const info = await resp.json();
      if (projectId !== state.currentProject) {
        clearInterval(neoPollTimer); neoPollTimer = 0;
        if (button) button.disabled = false;
        setNeoProgressUI(false);
        return;
      }
      if (info.state === 'running') {
        setNeoProgressUI(true, info.percent, info.stage, info.elapsed_sec);
        return;
      }
      clearInterval(neoPollTimer); neoPollTimer = 0;
      setNeoProgressUI(false);
      if (button) button.disabled = false;
      if (info.state === 'completed' && info.result) {
        applyNeoResultData(info.result, { scrollIntoView: true, restored: false });
        if (window.AppNotify) {
          AppNotify.toast('新抗原筛选已完成，共生成 ' + Number(info.result.candidate_count || 0) + ' 条候选肽。', 'success');
        }
      } else {
        if (status) {
          status.style.color = 'var(--danger)';
          status.textContent = String(info.error || '新抗原筛选失败');
        }
      }
    } catch (err) {
      clearInterval(neoPollTimer); neoPollTimer = 0;
      setNeoProgressUI(false);
      if (button) button.disabled = false;
      if (status) {
        status.style.color = 'var(--danger)';
        status.textContent = String(err.message || err);
      }
    }
  };
  tick();
  neoPollTimer = setInterval(tick, 500);
}

async function restoreNeoStateForProject() {
  const pid = state.currentProject;
  const panel = document.getElementById('neo-result-panel');
  const status = document.getElementById('neo-status');
  if (!pid) {
    if (panel) panel.style.display = 'none';
    setNeoProgressUI(false);
    return;
  }
  if (neoLoadedProject && neoLoadedProject !== pid) {
    neoRankedRows = [];
    if (panel) panel.style.display = 'none';
    if (status) status.textContent = '';
  }
  try {
    const actResp = await fetch('/api/peptide/job/active/' + encodeURIComponent(pid));
    const act = await actResp.json().catch(() => ({}));
    if (pid !== state.currentProject) return;
    if (act && act.active && act.job_id) {
      setNeoProgressUI(true, act.percent, act.stage, act.elapsed_sec);
      attachNeoJobPolling(act.job_id, pid);
      return;
    }
    const savedResp = await fetch('/api/peptide/results/' + encodeURIComponent(pid));
    const saved = await savedResp.json().catch(() => ({}));
    if (pid !== state.currentProject) return;
    if (saved && saved.available) {
      applyNeoResultData(saved, { scrollIntoView: false, restored: true });
    }
  } catch (e) {}
}

// 中文备注：统一的一键项目新抗原筛选入口（异步进度任务 + 自动滚动展示结果）。
async function runUnifiedNeoantigen() {
  const status = document.getElementById('neo-status');
  const errBox = document.getElementById('neo-errors');
  const button = document.getElementById('neo-guided-run');
  if (errBox) errBox.replaceChildren();
  if (!state.currentProject) { status.textContent = '请先在仪表盘选择一个项目。'; return; }
  const projectId = state.currentProject;
  const alleles = neoTokens();
  const cdsChoice = document.getElementById('neo-cds-select').value || '';
  const fastaChoice = document.getElementById('neo-fasta-select').value || '';
  const selectedIds = Array.from(neoSelectedEvents);
  const forceRebuild = document.getElementById('neo-force-rebuild').checked;
  const predictor = alleles.length ? document.getElementById('neo-predictor').value : 'none';
  const payload = {
    project_id: projectId,
    cds_table: (selectedIds.length || forceRebuild) ? '' : cdsChoice,
    alleles: alleles,
    mhc_class: document.getElementById('neo-mhc-class').value,
    predictor: predictor,
    processing: document.getElementById('neo-processing').checked,
    lookup_epitopes: document.getElementById('neo-lookup').checked,
    self_fastas: fastaChoice ? [fastaChoice] : [],
    auto_build_orf: true,
    force_rebuild_orf: forceRebuild,
    orf_source: document.getElementById('orf-source').value,
    orf_max_events: Number(document.getElementById('orf-max-events').value || 20),
    orf_fdr_max: Number(document.getElementById('orf-fdr').value || 0.05),
    orf_min_abs_dpsi: Number(document.getElementById('orf-dpsi').value || 0.1),
    orf_event_ids: selectedIds
  };
  if (payload.orf_source === 'local') {
    payload.orf_gtf = document.getElementById('orf-gtf').value.trim();
    payload.orf_fasta = document.getElementById('orf-fasta').value.trim();
  }
  button.disabled = true;
  status.style.color = 'var(--text-secondary)';
  status.textContent = '';
  setNeoProgressUI(true, 2, '正在启动新抗原筛选任务…', 0);
  try {
    const response = await fetch('/api/peptide/job/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.job_id) throw new Error(pepErrorDetail(response, data, '启动新抗原筛选失败'));
    attachNeoJobPolling(data.job_id, projectId);
  } catch (error) {
    setNeoProgressUI(false);
    button.disabled = false;
    status.style.color = 'var(--danger)';
    status.textContent = String(error.message || error);
  }
}

function neoFilteredRows() {
  const tier = (document.getElementById('neo-filter-tier') || {}).value || 'all';
  const query = ((document.getElementById('neo-filter-search') || {}).value || '').trim().toLowerCase();
  const onlyNovel = !!(document.getElementById('neo-filter-novel') || {}).checked;
  const noLc = !!(document.getElementById('neo-filter-lc') || {}).checked;
  const noNmd = !!(document.getElementById('neo-filter-nmd') || {}).checked;
  return neoRankedRows.filter(row => {
    if (tier === 'strong' && row.binding_tier !== 'strong') return false;
    if (tier === 'usable' && row.binding_tier !== 'strong' && row.binding_tier !== 'weak') return false;
    if (onlyNovel && row.self_hit === true) return false;
    if (noLc && row.low_complexity === true) return false;
    if (noNmd && (row.nmd_risk === 'candidate' || row.nmd_risk === 'possible')) return false;
    if (query) {
      const blob = [row.peptide, row.gene_symbol, row.event_id, row.best_allele, row.event_type].join(' ').toLowerCase();
      if (!blob.includes(query)) return false;
    }
    return true;
  });
}

function neoSortRanked(key) {
  if (neoSortKey === key) neoSortDir = -neoSortDir;
  else { neoSortKey = key; neoSortDir = (key === 'rank' || key === 'percentile_rank') ? 1 : -1; }
  renderNeoRankedTable();
}

function renderNeoRankedTable() {
  const body = document.getElementById('neo-result-body');
  const countEl = document.getElementById('neo-filter-count');
  if (!body) return;
  const rows = neoFilteredRows().slice();
  if (countEl) countEl.textContent = '显示 ' + rows.length + ' / ' + neoRankedRows.length + ' 条';
  if (!rows.length) {
    body.innerHTML = '<div style="padding:20px 0;color:var(--text-muted);font-size:13px;">当前筛选条件下无匹配候选肽，可放宽上方过滤条件。</div>';
    return;
  }
  const numCols = { rank: 1, percentile_rank: 1, processing_total_score: 1, immunogenicity_score: 1, esm2_immunogenicity: 1, composite_score: 1 };
  rows.sort((a, b) => {
    if (numCols[neoSortKey]) {
      const av = (a[neoSortKey] === null || a[neoSortKey] === undefined || a[neoSortKey] === '') ? Number.POSITIVE_INFINITY : Number(a[neoSortKey]);
      const bv = (b[neoSortKey] === null || b[neoSortKey] === undefined || b[neoSortKey] === '') ? Number.POSITIVE_INFINITY : Number(b[neoSortKey]);
      if (av !== bv) return (av < bv ? -1 : 1) * neoSortDir;
    } else {
      const as = String(a[neoSortKey] || '').toLowerCase();
      const bs = String(b[neoSortKey] || '').toLowerCase();
      if (as !== bs) return (as < bs ? -1 : 1) * neoSortDir;
    }
    return Number(a.rank || 0) - Number(b.rank || 0);
  });
  const hasEsm2 = rows.some(r => r.esm2_immunogenicity !== null && r.esm2_immunogenicity !== undefined && r.esm2_immunogenicity !== '');
  const cols = [
    ['rank', '#'], ['peptide', '候选肽'], ['gene_symbol', '基因 / 事件'],
    ['best_allele', '最优 HLA'], ['percentile_rank', '% Rank'],
    ['processing_total_score', '加工分'],
    [hasEsm2 ? 'esm2_immunogenicity' : 'immunogenicity_score', hasEsm2 ? 'ESM-2 免疫原性' : '免疫原性'],
    ['composite_score', '综合分 / 分层'], ['nmd_risk', '风险与来源标记']
  ];
  const head = cols.map(([k, label]) => {
    const arrow = neoSortKey === k ? (neoSortDir === 1 ? ' ▲' : ' ▼') : '';
    return '<th data-neo-sort="' + k + '" style="cursor:pointer;white-space:nowrap;">' + neoEscape(label) + arrow + '</th>';
  }).join('');
  const renderHotspot = (pep, weights) => {
    if (!Array.isArray(weights) || !weights.length || !pep) return neoEscape(pep);
    const maxW = Math.max.apply(null, weights.map(w => Number(w) || 0)) || 1;
    return String(pep).split('').map((aa, i) => {
      const w = Number(weights[i] || 0);
      const alpha = Math.min(0.85, Math.max(0.06, (w / maxW) * 0.78));
      return '<span title="P' + (i + 1) + ' ' + neoEscape(aa) + ': ' + w.toFixed(3)
        + '" style="display:inline-block;padding:0 2px;margin-right:1px;border-radius:3px;background:rgba(13,148,136,'
        + alpha.toFixed(2) + ');">' + neoEscape(aa) + '</span>';
    }).join('');
  };
  const htmlRows = rows.slice(0, 300).map(row => {
    const tier = row.binding_tier || 'unknown';
    const tierLabel = tier === 'strong' ? '强结合' : (tier === 'weak' ? '弱结合' : (tier === 'none' ? '非结合' : '未预测'));
    const tierCls = 'pep-tier-' + (tier === 'strong' || tier === 'weak' || tier === 'none' ? tier : 'unknown');
    const pct = (row.percentile_rank !== null && row.percentile_rank !== undefined && row.percentile_rank !== '')
      ? neoEscape(row.percentile_rank) : '—';
    const proc = (row.processing_total_score !== null && row.processing_total_score !== undefined && row.processing_total_score !== '')
      ? Number(row.processing_total_score).toFixed(2) : '—';
    const hasRowEsm2 = (row.esm2_immunogenicity !== null && row.esm2_immunogenicity !== undefined && row.esm2_immunogenicity !== '');
    const immVal = hasRowEsm2
      ? Number(row.esm2_immunogenicity).toFixed(4)
      : ((row.immunogenicity_score !== null && row.immunogenicity_score !== undefined && row.immunogenicity_score !== '')
        ? Number(row.immunogenicity_score).toFixed(3) : '—');
    let immCell = immVal;
    if (row.esm2_fusion_tier) {
      const ft = String(row.esm2_fusion_tier);
      const ftCls = ft.indexOf('1') >= 0 ? 'neo-badge-ok' : (ft.indexOf('2') >= 0 ? 'neo-badge-warn' : 'neo-badge-muted');
      immCell += ' <span class="neo-badge ' + ftCls + '">' + neoEscape(ft) + '</span>';
    }
    const score = (row.composite_score !== null && row.composite_score !== undefined) ? Number(row.composite_score).toFixed(3) : '—';
    const badges = [];
    if (row.self_hit === false) badges.push('<span class="neo-badge neo-badge-ok">未命中正常蛋白</span>');
    else if (row.self_hit === true) badges.push('<span class="neo-badge neo-badge-danger">命中正常蛋白</span>');
    if (row.esm2_mut_wt_detail) badges.push('<span class="neo-badge neo-badge-ok">v5-beta Mut-WT</span>');
    if (row.nmd_risk === 'candidate' || row.nmd_risk === 'possible') badges.push('<span class="neo-badge neo-badge-warn">⚠ NMD 风险</span>');
    if (row.low_complexity === true) badges.push('<span class="neo-badge neo-badge-muted">低复杂度</span>');
    if (!badges.length) badges.push('<span class="neo-badge neo-badge-muted">常规</span>');
    const source = [row.gene_symbol || '', row.event_id || '', row.event_type || ''].filter(Boolean).join(' · ');
    const pepHtml = Array.isArray(row.esm2_residue_weights)
      ? renderHotspot(row.peptide, row.esm2_residue_weights)
      : neoEscape(row.peptide);
    return '<tr>'
      + '<td>' + neoEscape(row.rank) + '</td>'
      + '<td style="font-family:var(--font-mono,monospace);font-weight:500;">' + pepHtml + '</td>'
      + '<td>' + neoEscape(source || '—') + '</td>'
      + '<td>' + neoEscape(row.best_allele || '—') + '</td>'
      + '<td style="white-space:nowrap;">' + pct + '<span class="pep-tier ' + tierCls + '">' + tierLabel + '</span></td>'
      + '<td>' + proc + '</td>'
      + '<td style="white-space:nowrap;">' + immCell + '</td>'
      + '<td style="white-space:nowrap;">' + score + ' <span class="neo-badge neo-badge-muted">' + neoEscape(row.evidence_tier || 'D') + '</span></td>'
      + '<td>' + badges.join('') + '</td>'
      + '</tr>';
  }).join('');
  body.innerHTML = '<div class="table-container" style="max-height:520px;overflow:auto;"><table><thead><tr>' + head + '</tr></thead><tbody>' + htmlRows + '</tbody></table></div>';
  body.querySelectorAll('th[data-neo-sort]').forEach(th => {
    th.addEventListener('click', () => neoSortRanked(th.getAttribute('data-neo-sort')));
  });
}

function renderNeoEpitopeMatches(matches) {
  const box = document.getElementById('neo-epitope-matches');
  if (!box) return;
  if (!matches || !matches.length) { box.replaceChildren(); return; }
  const rows = matches.slice(0, 40).map(r => '<tr>'
    + '<td style="font-family:var(--font-mono,monospace);">' + neoEscape(r.candidate_peptide || r.peptide) + '</td>'
    + '<td>' + neoEscape(r.mhc_restriction || '') + '</td>'
    + '<td>' + neoEscape(r.qualitative_measure || '') + '</td>'
    + '<td>' + neoEscape(r.source_organism || '') + '</td>'
    + '<td>' + neoEscape(r.pubmed_id || '') + '</td></tr>').join('');
  box.innerHTML = '<div style="margin-top:14px;font-size:12px;color:var(--text-secondary);">IEDB 已知表位命中（' + matches.length + ' 条）</div>'
    + '<div class="table-container" style="max-height:200px;overflow:auto;margin-top:6px;"><table><thead><tr><th>肽段</th><th>HLA</th><th>结局</th><th>来源</th><th>PMID</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

function renderNeoResultFiles(data) {
  const box = document.getElementById('neo-result-files');
  if (!box) return;
  box.replaceChildren();
  const baseDir = data.results_input_dir || '';
  if (!baseDir) return;
  const base = '/api/peptide/file?input_dir=' + encodeURIComponent(baseDir) + '&name=';
  const label = document.createElement('span');
  label.textContent = '原始结果文件：';
  box.appendChild(label);
  ['ranked_candidates.tsv', 'splice_peptides.tsv', 'mhc_predictions.tsv', 'manifest.json', 'summary.md'].forEach(name => {
    if ((data.files || []).length && (data.files || []).indexOf(name) < 0) return;
    const link = document.createElement('a');
    link.href = base + encodeURIComponent(name);
    link.textContent = name;
    link.style.color = 'var(--accent)';
    box.appendChild(link);
  });
}

function neoTriggerDownload(filename, content, mime) {
  const blob = new Blob([content], { type: mime || 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

function exportNeoFilteredFasta() {
  const rows = neoFilteredRows();
  if (!rows.length) return;
  const lines = rows.map(r => '>' + [r.rank, r.gene_symbol || 'NA', r.event_id || 'NA', r.best_allele || 'noHLA', r.binding_tier || 'unknown'].join('|') + NEO_LF + r.peptide);
  neoTriggerDownload('neoantigen_candidates.fasta', lines.join(NEO_LF) + NEO_LF, 'text/plain;charset=utf-8');
}

function exportNeoFilteredCsv() {
  const rows = neoFilteredRows();
  if (!rows.length) return;
  const cols = ['rank', 'peptide', 'length', 'gene_symbol', 'event_id', 'event_type', 'best_allele', 'percentile_rank', 'binding_tier', 'processing_total_score', 'immunogenicity_score', 'esm2_v4_score', 'esm2_immunogenicity', 'esm2_fusion_score', 'esm2_fusion_tier', 'composite_score', 'evidence_tier', 'self_hit', 'low_complexity', 'nmd_risk'];
  const esc = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const lines = [cols.join(',')].concat(rows.map(r => cols.map(c => esc(r[c])).join(',')));
  neoTriggerDownload('neoantigen_synthesis_list.csv', '\\uFEFF' + lines.join(NEO_LF) + NEO_LF, 'text/csv;charset=utf-8');
}

async function revealNeoResult() {
  if (!neoResultDir) return;
  try {
    const response = await fetch('/api/neoantigen/reveal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_dir: neoResultDir, folder: 'peptide_results' })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || ('HTTP ' + response.status));
  } catch (error) {
    const status = document.getElementById('neo-status');
    if (status) status.textContent = '无法打开目录：' + String(error.message || error);
  }
}

/* ------------------------------------------------------------------ */
/* Peptide prediction page (additive; all globals prefixed with pep)   */
/* ------------------------------------------------------------------ */
const PEP_CLASS1_PANEL = [
  'HLA-A*01:01', 'HLA-A*02:01', 'HLA-A*03:01', 'HLA-A*11:01',
  'HLA-A*23:01', 'HLA-A*24:02', 'HLA-A*26:01', 'HLA-A*31:01',
  'HLA-B*07:02', 'HLA-B*08:01', 'HLA-B*15:01', 'HLA-B*27:05',
  'HLA-B*35:01', 'HLA-B*40:01', 'HLA-B*44:02', 'HLA-B*44:03',
  'HLA-B*57:01', 'HLA-B*58:01', 'HLA-C*07:02', 'HLA-C*04:01'
];
const PEP_CLASS2_PANEL = [
  'HLA-DRB1*01:01', 'HLA-DRB1*03:01', 'HLA-DRB1*04:01', 'HLA-DRB1*07:01',
  'HLA-DRB1*09:01', 'HLA-DRB1*11:01', 'HLA-DRB1*13:02', 'HLA-DRB1*15:01',
  'HLA-DPA1*01:03/DPB1*04:01', 'HLA-DQA1*05:01/DQB1*02:01'
];
const pepState = {
  loaded: false,
  loading: false,
  capabilities: null,
  referenceTotal: 0,
  searchTimer: null,
  predictions: [],
  sortKey: 'percentile_rank',
  sortDir: 1,
  bound: false,
  projectOutput: ''
};
const PEP_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
// 中文备注：对多肽工作台展示的文本进行 HTML 转义。
function pepEscape(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, ch => PEP_ESCAPES[ch]);
}
// 中文备注：设置多肽工作台指定状态栏的文案与提示色调。
function pepSetStatus(id, text, tone) {
  const box = document.getElementById(id);
  if (!box) return;
  box.textContent = text || '';
  box.style.color = tone === 'error' ? 'var(--danger)' : (tone === 'muted' ? 'var(--text-muted)' : 'var(--text-secondary)');
}
// 中文备注：从接口响应中提取可读的错误详情，缺失时回退到默认提示。
function pepErrorDetail(response, payload, fallback) {
  if (payload && payload.detail) {
    return typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail);
  }
  return fallback + '（HTTP ' + response.status + '）';
}
// 中文备注：将多肽工作台输入的 HLA 等位基因文本拆分为去重后的标签数组。
function pepTokens() {
  const input = document.getElementById('pep-alleles');
  if (!input) return [];
  return input.value.split(/[,;\\s]+/).map(v => v.trim()).filter(Boolean);
}
// 中文备注：根据当前选中的 HLA 等位基因列表渲染可移除的标签芯片。
function pepRenderChips() {
  const wrap = document.getElementById('pep-allele-chips');
  if (!wrap) return;
  wrap.replaceChildren();
  const tokens = pepTokens();
  tokens.forEach(token => {
    const chip = document.createElement('span');
    chip.textContent = token + '  ×';
    chip.title = '点击移除 ' + token;
    chip.style.cssText = 'padding:4px 9px;border:1px solid var(--border);border-radius:999px;font-size:12px;color:var(--text-secondary);cursor:pointer;';
    chip.onclick = () => {
      const remaining = pepTokens().filter(value => value !== token);
      document.getElementById('pep-alleles').value = remaining.join(', ');
      pepRenderChips();
    };
    wrap.appendChild(chip);
  });
}
// 中文备注：向多肽工作台填入示例多肽序列与常用 HLA 等位基因，便于快速体验。
async function pepFillExample() {
  const field = document.getElementById('pep-sequences');
  if (field.value.trim()) {
    const confirmed = await AppNotify.confirm(
      '填入示例会覆盖当前填写好的肽序列和 HLA 型别。',
      { kind: 'warning', title: '替换当前输入？', confirmLabel: '填入示例', cancelLabel: '保留输入' }
    );
    if (!confirmed) return;
  }
  field.value = ['SLYNTVATL', 'GILGFVFTL', 'NLVPMVATV'].join(String.fromCharCode(10));
  document.getElementById('pep-alleles').value = 'HLA-A*02:01';
  document.getElementById('pep-mhc-class').value = 'class1';
  pepCountSequences(); pepRenderChips(); pepRefreshReference();
  field.focus();
}
// 中文备注：实时统计并显示当前输入框中的有效多肽序列条数。
function pepCountSequences() {
  const label = document.getElementById('pep-seq-count');
  if (!label) return { peptides: [], invalid: 0 };
  const raw = document.getElementById('pep-sequences').value.split(/\\r?\\n/);
  const peptides = [];
  let invalid = 0;
  raw.forEach(line => {
    let value = line.trim();
    if (!value || value.startsWith('>') || value.startsWith(';')) return;
    value = value.replace(/\\s+/g, '').toUpperCase();
    if (!/^[ACDEFGHIKLMNPQRSTVWY]+$/.test(value) || value.length < 8 || value.length > 30) {
      invalid += 1;
      return;
    }
    peptides.push(value);
  });
  const unique = Array.from(new Set(peptides));
  label.textContent = '已识别 ' + unique.length + ' 条肽段（8–30 aa）' + (invalid ? '，忽略 ' + invalid + ' 行无效输入' : '');
  label.style.color = invalid ? 'var(--danger)' : 'var(--text-muted)';
  return { peptides: unique, invalid: invalid };
}
// 中文备注：将预置 HLA 群体面板（如高频等位基因组合）一键填入输入框。
function pepUsePanel(name) {
  const panel = name === 'class2_common' ? PEP_CLASS2_PANEL : PEP_CLASS1_PANEL;
  document.getElementById('pep-alleles').value = panel.join(', ');
  document.getElementById('pep-mhc-class').value = name === 'class2_common' ? 'class2' : 'class1';
  pepRenderChips();
  pepRefreshReference();
}
// 中文备注：清空当前已选的 HLA 等位基因输入与标签芯片。
function pepClearAlleles() {
  document.getElementById('pep-alleles').value = '';
  pepRenderChips();
  pepRefreshReference();
}
// 中文备注：按当前筛选词与 MHC 类别向后端拉取 HLA 等位基因与参考表位提示。
async function pepRefreshReference() {
  const hint = document.getElementById('pep-allele-hint');
  if (!hint) return;
  const mhcClass = document.getElementById('pep-mhc-class').value === 'class2' ? 2 : 1;
  const search = document.getElementById('pep-alleles').value.trim();
  hint.textContent = '正在加载等位基因参考表…';
  hint.style.color = 'var(--text-muted)';
  try {
    const url = '/api/peptide/reference?mhc_class=' + mhcClass
      + '&search=' + encodeURIComponent(search) + '&limit=500';
    const response = await fetch(url);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(pepErrorDetail(response, payload, '参考表加载失败'));
    const items = payload.items || [];
    const list = document.getElementById('pep-allele-list');
    list.replaceChildren();
    items.forEach(item => {
      const option = document.createElement('option');
      option.value = item.allele;
      option.label = [item.locus, item.supertype].filter(Boolean).join(' · ');
      list.appendChild(option);
    });
    pepState.referenceTotal = Number(payload.total || items.length);
    hint.textContent = 'MHC-' + (mhcClass === 1 ? 'I' : 'II') + ' 参考表：共 '
      + pepState.referenceTotal + ' 个等位基因' + (search ? '（当前匹配 ' + items.length + '）' : '（显示前 ' + items.length + '）');
    hint.style.color = 'var(--text-muted)';
  } catch (error) {
    hint.textContent = '参考表加载失败：' + String(error.message || error);
    hint.style.color = 'var(--danger)';
  }
}
// 中文备注：对参考库检索输入进行防抖处理，避免频繁请求后端。
function pepDebounceReference() {
  if (pepState.searchTimer) clearTimeout(pepState.searchTimer);
  pepState.searchTimer = setTimeout(() => { pepRefreshReference(); }, 300);
}
// 中文备注：同步当前选中项目与多肽工作台“按项目运行”按钮的可用状态。
function pepUpdateProjectState() {
  const hint = document.getElementById('pep-project-hint');
  const button = document.getElementById('pep-project-btn');
  if (!hint || !button) return;
  if (state.currentProject) {
    hint.textContent = '当前项目：' + state.currentProject + '。将读取项目目录中的事件表和编码序列对照表。';
    hint.style.color = 'var(--text-muted)';
    button.disabled = false;
    button.style.opacity = '1';
  } else {
    hint.textContent = '尚未选择项目。请先在“仪表盘”新建或选择一个项目，再回来生成候选肽。';
    hint.style.color = 'var(--text-muted)';
    button.disabled = true;
    button.style.opacity = '.55';
  }
}
// 中文备注：加载多肽预测后端的能力信息（可用预测器、默认等位基因面板等）。
async function pepLoadMeta() {
  if (pepState.loading) return;
  pepState.loading = true;
  try {
    const response = await fetch('/api/peptide/capabilities');
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(pepErrorDetail(response, payload, '能力信息加载失败'));
    pepState.capabilities = payload;
    const local = (payload.predictors || {}).mhcflurry || {};
    const reference = payload.reference || {};
    const ready = !!local.available;
    [
      [document.getElementById('pep-predictor-local'), document.getElementById('pep-predictor')],
      [document.getElementById('neo-predictor-local'), document.getElementById('neo-predictor')]
    ].forEach(([opt, sel]) => {
      if (opt && sel) {
        opt.disabled = !ready;
        opt.textContent = 'MHCflurry（本地，' + (ready ? '可用' : '未安装') + '）';
        if (!ready && sel.value === 'local') sel.value = 'iedb';
      }
    });
    const label = document.getElementById('pep-capabilities');
    const esm2 = (payload.predictors || {}).esm2_lora || {};
    const esm2Tag = esm2.available
      ? 'ESM-2 LoRA 已连接（' + (esm2.folds || 5) + '折）'
      : 'ESM-2 LoRA 离线降级中';
    if (label) {
      label.textContent = 'IEDB 在线 · MHCflurry ' + (local.available ? '可用 ' + (local.version || '') : '未安装')
        + ' · ' + esm2Tag
        + ' · 参考表 class1 ' + (reference.alleles_class1 || 0) + ' / class2 ' + (reference.alleles_class2 || 0)
        + ' · 已知表位 ' + (reference.known_epitopes || 0);
    }
  } catch (error) {
    const label = document.getElementById('pep-capabilities');
    if (label) label.textContent = '能力信息加载失败：' + String(error.message || error);
  } finally {
    pepState.loading = false;
    pepState.loaded = true;
  }
}
// 中文备注：为多肽工作台各输入框与按钮绑定一次性交互事件监听。
function pepBindOnce() {
  if (pepState.bound) return;
  pepState.bound = true;
  const textarea = document.getElementById('pep-sequences');
  if (textarea) textarea.addEventListener('input', pepCountSequences);
  const alleles = document.getElementById('pep-alleles');
  if (alleles) {
    alleles.addEventListener('input', () => { pepRenderChips(); pepDebounceReference(); });
    alleles.addEventListener('change', () => { pepRenderChips(); pepRefreshReference(); });
  }
  const mhcSelect = document.getElementById('pep-mhc-class');
  if (mhcSelect) mhcSelect.addEventListener('change', () => { pepRefreshReference(); });
}
// 中文备注：初始化多肽预测工作台页面状态并加载元数据与参考列表。
function pepInitPage() {
  pepBindOnce();
  pepUpdateProjectState();
  pepRenderChips();
  const textarea = document.getElementById('pep-sequences');
  if (textarea) textarea.focus();
  if (!pepState.loaded) {
    pepLoadMeta();
    pepRefreshReference();
  } else {
    pepUpdateProjectState();
  }
}
// 中文备注：提取多肽结果行的综合排序分值，用于数值比较与排序。
function pepScoreValue(row) {
  const candidates = [row.score, row.total_score, row.mhcnp_probability];
  for (let index = 0; index < candidates.length; index += 1) {
    const value = Number(candidates[index]);
    if (candidates[index] !== null && candidates[index] !== undefined && Number.isFinite(value)) {
      return value;
    }
  }
  return Number.POSITIVE_INFINITY;
}
// 中文备注：按指定列名读取多肽结果行的可比较排序键。
function pepSortValue(row, key) {
  if (key === 'percentile_rank') {
    const value = Number(row[key]);
    return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
  }
  if (key === 'score') return pepScoreValue(row);
  return String(row[key] == null ? '' : row[key]).toLowerCase();
}
// 中文备注：切换多肽预测结果表的排序字段与升降序并重新渲染。
function pepSortBy(key) {
  if (pepState.sortKey === key) {
    pepState.sortDir = -pepState.sortDir;
  } else {
    pepState.sortKey = key;
    pepState.sortDir = key === 'percentile_rank' ? 1 : -1;
  }
  pepRenderPredictionTable();
}
// 中文备注：渲染多肽结合亲和力与分级预测结果表格。
function pepRenderPredictionTable() {
  const box = document.getElementById('pep-results');
  if (!box) return;
  const rows = pepState.predictions.slice();
  if (!rows.length) {
    box.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">暂无预测结果。</p>';
    return;
  }
  const key = pepState.sortKey;
  const dir = pepState.sortDir;
  rows.sort((a, b) => {
    const left = pepSortValue(a, key);
    const right = pepSortValue(b, key);
    if (left < right) return -1 * dir;
    if (left > right) return 1 * dir;
    return String(a.peptide || '').localeCompare(String(b.peptide || ''));
  });
  const header = '<th style="white-space:nowrap;">#</th>' + [
    ['peptide', '肽段'], ['allele', 'HLA'],
    ['method', '方法'], ['percentile_rank', 'percentile rank（<0.5 强 / <2 弱）'], ['score', '分数（EL / 加工总分，不可比）']
  ].map(([column, text]) => {
    const marker = pepState.sortKey === column ? (pepState.sortDir === 1 ? ' ▲' : ' ▼') : '';
    return '<th data-sort="' + column + '" style="cursor:pointer;white-space:nowrap;">'
      + pepEscape(text) + marker + '</th>';
  }).join('');
  const body = rows.map((row, index) => {
    const method = row.method_label || row.method || '';
    const rankValue = Number(row.percentile_rank);
    const hasRank = row.percentile_rank !== null && row.percentile_rank !== undefined
      && Number.isFinite(rankValue);
    let tierClass = 'pep-tier-unknown';
    let tierText = '无 rank';
    if (hasRank && rankValue < 0.5) { tierClass = 'pep-tier-strong'; tierText = '强结合'; }
    else if (hasRank && rankValue < 2) { tierClass = 'pep-tier-weak'; tierText = '弱结合'; }
    else if (hasRank) { tierClass = 'pep-tier-none'; tierText = '非结合'; }
    const percentile = (hasRank ? pepEscape(row.percentile_rank) : '—')
      + '<span class="pep-tier ' + tierClass + '">' + tierText + '</span>';
    const scoreValue = pepScoreValue(row);
    const score = scoreValue === Number.POSITIVE_INFINITY ? '—' : pepEscape(scoreValue);
    return '<tr>'
      + '<td>' + (index + 1) + '</td>'
      + '<td style="font-family:var(--font-mono,monospace);">' + pepEscape(row.peptide) + '</td>'
      + '<td>' + pepEscape(row.allele) + '</td>'
      + '<td>' + pepEscape(method) + '</td>'
      + '<td>' + percentile + '</td>'
      + '<td>' + score + '</td>'
      + '</tr>';
  }).join('');
  box.innerHTML = '<div class="table-container" style="max-height:460px;overflow:auto;">'
    + '<table><thead><tr>' + header + '</tr></thead><tbody>' + body + '</tbody></table></div>'
    + '<div style="font-size:12px;color:var(--text-muted);margin-top:6px;">共 '
    + rows.length + ' 行（肽段 × HLA × 方法）。点击表头可排序。'
    + '强结合 &lt;0.5、弱结合 0.5~2、其余不列为候选；EL 分数与加工总分量纲不同，不可横向比较。</div>'
    + '<div id="pep-tier-summary" class="trace-meta" style="margin-top:6px;"></div>';
  const tierCounts = { strong: 0, weak: 0, none: 0, unknown: 0 };
  rows.forEach(function (row) {
    const value = Number(row.percentile_rank);
    if (row.percentile_rank === null || row.percentile_rank === undefined || !Number.isFinite(value)) {
      tierCounts.unknown += 1;
    } else if (value < 0.5) { tierCounts.strong += 1; }
    else if (value < 2) { tierCounts.weak += 1; }
    else { tierCounts.none += 1; }
  });
  const tierSummary = document.getElementById('pep-tier-summary');
  if (tierSummary) {
    const usable = tierCounts.strong + tierCounts.weak;
    tierSummary.textContent = '自动分级：强结合 ' + tierCounts.strong + ' 条 · 弱结合 '
      + tierCounts.weak + ' 条 · 非结合 ' + tierCounts.none + ' 条 · 无 rank '
      + tierCounts.unknown + ' 条。'
      + (usable ? '' : '本批未发现可用结合候选，不能据此宣称找到新抗原。');
    tierSummary.style.color = usable ? 'var(--text-secondary)' : 'var(--danger)';
  }
  box.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => pepSortBy(th.getAttribute('data-sort')));
  });
  const expBtn = document.getElementById('pep-export-csv');
  if (expBtn) expBtn.style.display = rows.length ? 'inline-flex' : 'none';
}
function pepExportCsv() {
  if (!pepState.predictions.length) return;
  const cols = ['peptide', 'allele', 'method_label', 'percentile_rank', 'score', 'total_score'];
  const esc = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const lines = [cols.join(',')].concat(pepState.predictions.map(r => cols.map(c => esc(r[c])).join(',')));
  neoTriggerDownload('peptide_predictions.csv', '\\uFEFF' + lines.join(NEO_LF) + NEO_LF, 'text/csv;charset=utf-8');
}
// 中文备注：展示多肽预测过程中返回的警告或单条失败信息。
function pepRenderErrors(errors) {
  const box = document.getElementById('pep-errors');
  if (!box) return;
  if (!errors || !errors.length) { box.replaceChildren(); return; }
  const items = errors.map(error => {
    const stage = error && error.stage ? String(error.stage) : '未知阶段';
    const message = error && error.error ? String(error.error) : JSON.stringify(error);
    return '<li><strong>' + pepEscape(stage) + '</strong>：' + pepEscape(message) + '</li>';
  }).join('');
  box.innerHTML = '<div style="font-size:12px;color:var(--danger);">预测服务返回 ' + errors.length
    + ' 条错误：</div><ul style="margin:6px 0 0 18px;font-size:12px;color:var(--text-secondary);">'
    + items + '</ul>';
}
function pepRenderEpitopes(matches) {
  const box = document.getElementById('pep-results');
  if (!box || !matches || !matches.length) return;
  const rows = matches.slice(0, 50).map(row => '<tr>'
    + '<td style="font-family:var(--font-mono,monospace);">' + pepEscape(row.candidate_peptide || row.peptide) + '</td>'
    + '<td>' + pepEscape(row.mhc_restriction || '') + '</td>'
    + '<td>' + pepEscape(row.qualitative_measure || '') + '</td>'
    + '<td>' + pepEscape(row.source_organism || '') + '</td>'
    + '<td>' + pepEscape(row.pubmed_id || '') + '</td>'
    + '</tr>').join('');
  const section = document.createElement('div');
  section.style.marginTop = '12px';
  section.innerHTML = '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:6px;">IEDB 已知表位匹配（'
    + matches.length + ' 条；命中只说明该序列曾被检测过，不代表本次候选已验证）</div>'
    + '<div class="table-container" style="max-height:220px;overflow:auto;"><table><thead><tr>'
    + '<th>肽段</th><th>HLA</th><th>结局</th><th>来源</th><th>PMID</th></tr></thead><tbody>'
    + rows + '</tbody></table></div>';
  box.appendChild(section);
}
// 中文备注：提交手工输入的多肽序列到后端 /api/peptide/predict 并展示结果。
async function pepPredict() {
  const button = document.getElementById('pep-predict-btn');
  const status = 'pep-status';
  const parsed = pepCountSequences();
  const peptides = parsed.peptides;
  if (!peptides.length) {
    pepSetStatus(status, '请先输入至少一条 8–30 aa 的候选肽序列。', 'error');
    return;
  }
  const alleles = pepTokens();
  if (!alleles.length) {
    pepSetStatus(status, '请至少填写一个 HLA 型别，或点击常用面板快速填充。', 'error');
    return;
  }
  if (peptides.length > 200) {
    pepSetStatus(status, '单次最多 200 条肽，当前输入 ' + peptides.length + ' 条；请分批预测。', 'error');
    return;
  }
  if (alleles.length > 8) {
    pepSetStatus(status, '单次最多 8 个 HLA 型别，当前输入 ' + alleles.length + ' 个；请分批预测。', 'error');
    return;
  }
  const payload = {
    peptides: peptides,
    alleles: alleles,
    mhc_class: document.getElementById('pep-mhc-class').value,
    predictor: document.getElementById('pep-predictor').value,
    processing: document.getElementById('pep-processing').checked,
    lookup_epitopes: document.getElementById('pep-lookup').checked
  };
  button.disabled = true;
  button.style.opacity = '.55';
  pepSetStatus(status, '正在调用预测服务（' + peptides.length + ' 条肽 × ' + alleles.length + ' 个 HLA）…', 'muted');
  try {
    const response = await fetch('/api/peptide/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(pepErrorDetail(response, data, '预测失败'));
    pepState.predictions = data.predictions || [];
    pepRenderErrors(data.errors || []);
    pepRenderPredictionTable();
    pepRenderEpitopes(data.epitope_matches || []);
    const errorCount = (data.errors || []).length;
    const count = Number(data.prediction_count || pepState.predictions.length);
    const zeroHint = (!count && !errorCount && payload.predictor !== 'none')
      ? ' 未产生预测记录：请核对肽长度与 MHC 类别、HLA 型别是否匹配（MHC-I 8–11 aa / MHC-II 11–30 aa）。'
      : '';
    const suffix = errorCount ? '；有 ' + errorCount + ' 条服务错误，见下方说明' : '；无服务错误';
    pepSetStatus(status, '预测完成：候选 ' + Number(data.candidate_count || 0) + ' 条，预测记录 '
      + count + ' 条' + suffix + '。' + zeroHint
      + ' percentile rank 越低越好（<0.5 强 / <2 弱）；预测不等于呈递或免疫原性。', errorCount ? 'error' : 'muted');
  } catch (error) {
    pepState.predictions = [];
    pepRenderPredictionTable();
    pepSetStatus(status, String(error.message || error), 'error');
  } finally {
    button.disabled = false;
    button.style.opacity = '1';
  }
}

document.querySelectorAll('.nav-item[data-page]').forEach(item => { item.addEventListener('click', () => { navigateTo(item.dataset.page); }); });
// 中文备注：切换移动端/窄屏模式下的侧边栏导航抽屉开闭状态与主区 inert 锁定。
function toggleNavigation(force) {
  const open = typeof force === 'boolean' ? force : !document.body.classList.contains('navigation-open');
  const mobile = window.matchMedia('(max-width:768px)').matches;
  const closingFocusedDrawer = !open && document.getElementById('app-navigation').contains(document.activeElement);
  document.querySelector('main').inert = open && mobile;
  document.body.classList.toggle('navigation-open', open);
  if (closingFocusedDrawer) document.querySelector('.mobile-menu').focus();
  document.querySelector('.mobile-menu').setAttribute('aria-expanded', String(open));
  const navigation = document.getElementById('app-navigation');
  navigation.inert = !open && window.matchMedia('(max-width:768px)').matches;
  if (open) { syncFluidMarker(); navigation.querySelector('.nav-item.active').focus(); }

}

const traceState = { projectsLoaded: false, data: null };
// 中文备注：对决策追踪面板中的文本进行 HTML 转义。
function traceEsc(value) {
  return String(value === undefined || value === null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
// 中文备注：将过长的文本按字符上限截断并追加省略号。
function traceShort(value, limit) {
  let text;
  try { text = typeof value === 'string' ? value : JSON.stringify(value); }
  catch (error) { text = String(value); }
  text = String(text || '');
  return text.length > limit ? text.slice(0, limit) + '…' : text;
}
function traceBadge(source) {
  const key = String(source || 'rule');
  const labels = { llm: '模型决策', rule: '规则链', reflection: '反思纠错', episodic: '经验记忆', replay: '重放' };
  const cls = ['llm', 'reflection', 'episodic', 'replay'].includes(key) ? key : 'rule';
  return '<span class="trace-badge trace-' + cls + '">' + traceEsc(labels[key] || key) + '</span>';
}
// 中文备注：生成决策追踪摘要指标卡片的 HTML 片段。
function traceMetric(label, value, detail, bar) {
  let barHtml = '';
  if (typeof bar === 'number') {
    const pct = Math.max(0, Math.min(100, Math.round(bar * 100)));
    barHtml = '<div class="trace-bar"><span style="width:' + pct + '%"></span></div>';
  }
  return '<div class="card"><div class="trace-meta">' + traceEsc(label) + '</div>'
    + '<div class="trace-metric">' + traceEsc(value) + '</div>'
    + '<div class="trace-meta">' + traceEsc(detail) + '</div>' + barHtml + '</div>';
}
// 中文备注：加载并渲染指定项目的智能体决策轨迹、步骤来源与工具调用记录。
async function loadDecisionTrace() {
  const select = document.getElementById('trace-project');
  if (!select) return;
  const summary = document.getElementById('trace-summary');
  const stepsBox = document.getElementById('trace-steps');
  const callsBox = document.getElementById('trace-calls');
  const integrity = document.getElementById('trace-integrity');
  if (!traceState.projectsLoaded) {
    const projects = await apiCall('/projects');
    const list = (projects && projects.projects) || [];
    select.innerHTML = list.map(function (p) {
      const id = p.project_id || p.id || '';
      return '<option value="' + traceEsc(id) + '">' + traceEsc(p.name || id) + '</option>';
    }).join('');
    if (state.currentProject) select.value = state.currentProject;
    traceState.projectsLoaded = true;
  }
  const id = select.value;
  if (!id) {
    summary.innerHTML = '';
    integrity.textContent = '还没有已分析的项目。请先运行一次分析。';
    stepsBox.innerHTML = '<div class="trace-meta">暂无轨迹。</div>';
    callsBox.innerHTML = '<div class="trace-meta">暂无调用。</div>';
    return;
  }
  stepsBox.innerHTML = '<div class="trace-meta">正在读取轨迹…</div>';
  const data = await apiCall('/projects/' + encodeURIComponent(id) + '/trace');
  if (!data || !data.available) {
    summary.innerHTML = '';
    integrity.textContent = '该项目没有决策轨迹：' + traceEsc((data && data.detail) || '接口不可用')
      + '。只有 agentic 模式运行会写入 agent_state.json。';
    stepsBox.innerHTML = '<div class="trace-meta">暂无轨迹。</div>';
    callsBox.innerHTML = '<div class="trace-meta">暂无调用。</div>';
    return;
  }
  traceState.data = data;
  const pct = Math.round((data.llm_ratio || 0) * 100);
  summary.innerHTML = traceMetric('总决策步数', data.total_steps, '含规则链与模型选步')
    + traceMetric('模型参与决策', data.llm_steps, '占比 ' + pct + '%', data.llm_ratio)
    + traceMetric('自我纠错 / 经验', (data.reflection_steps || 0) + ' / ' + (data.episodic_steps || 0), 'reflection / episodic')
    + traceMetric('模型 / 工具调用', data.model_call_count + ' / ' + data.tool_call_count, '全部写入轨迹文件');
  const fingerprints = Object.keys(data.input_fingerprints || {}).length;
  const reports = Object.keys(data.reports || {}).length;
  let integrityText = '轨迹完整性：' + (data.integrity_ok ? '校验通过' : '未通过或无签名')
    + '；输入指纹 ' + fingerprints + ' 个文件；报告哈希 ' + reports + ' 份；模型 '
    + traceEsc(data.model_name || '未配置') + '；llm_enabled=' + traceEsc(String(data.llm_enabled));
  if (data.errors && data.errors.length) {
    integrityText += '；错误 ' + data.errors.length + ' 条：' + traceShort(data.errors[0], 140);
  }
  integrity.textContent = integrityText;
  stepsBox.innerHTML = (data.steps || []).map(function (s) {
    const args = s.args && Object.keys(s.args).length ? traceShort(s.args, 180) : '';
    const issues = (s.issues || []).length ? '问题：' + traceEsc(traceShort(s.issues.join('、'), 160)) : '';
    return '<div class="trace-step"><div class="trace-step-title">'
      + '<span>' + traceEsc(s.index) + '.</span><span>' + traceEsc(s.action) + '</span>'
      + traceBadge(s.source) + '<span class="trace-meta">' + traceEsc(s.status) + '</span></div>'
      + '<div class="trace-meta">' + traceEsc(s.rationale || '') + '</div>'
      + (args ? '<div class="trace-meta">参数 ' + traceEsc(args) + '</div>' : '')
      + (issues ? '<div class="trace-meta">' + issues + '</div>' : '')
      + '<div class="trace-meta">耗时 ' + traceEsc(s.seconds) + ' s</div></div>';
  }).join('') || '<div class="trace-meta">没有步骤记录。</div>';
  const modelCards = (data.model_calls || []).map(function (c) {
    return '<div class="trace-call"><div style="font-weight:500">#' + traceEsc(c.seq) + ' '
      + traceEsc(c.stage) + ' · ' + traceEsc(c.model || '') + '</div>'
      + '<div class="trace-meta">prompt ' + traceEsc(c.prompt_hash) + ' · temp '
      + traceEsc(c.temperature) + ' · ' + traceEsc(c.elapsed_ms) + ' ms</div>'
      + '<div class="trace-meta">解析结果 ' + traceEsc(traceShort(c.parsed, 220)) + '</div>'
      + '<details><summary class="trace-meta">查看原始响应</summary><div class="trace-meta">'
      + traceEsc(traceShort(c.raw_response, 1200)) + '</div></details></div>';
  }).join('');
  const toolCards = (data.tool_calls || []).map(function (c) {
    return '<div class="trace-call"><div style="font-weight:500">#' + traceEsc(c.seq) + ' MCP '
      + traceEsc(c.tool) + ' · ' + traceEsc(c.server) + '</div>'
      + '<div class="trace-meta">参数 ' + traceEsc(traceShort(c.args, 200)) + '</div>'
      + '<div class="trace-meta">结果 ' + traceEsc(traceShort(c.result, 260)) + '</div></div>';
  }).join('');
  callsBox.innerHTML = modelCards + toolCards || '<div class="trace-meta">这次运行没有模型或工具调用（纯确定性运行）。</div>';
}
async function compareDecisionTrace() {
  const out = document.getElementById('trace-compare-result');
  const left = document.getElementById('trace-project').value;
  const right = document.getElementById('trace-compare-right').value.trim();
  if (!left) { out.textContent = '请先选择项目。'; return; }
  const payload = { left: left, right: right || left };
  out.textContent = '正在对比…';
  const result = await apiCall('/trace/compare', { method: 'POST', body: JSON.stringify(payload) });
  if (!result) { out.textContent = '对比请求失败。'; return; }
  if (result.detail) { out.textContent = '对比失败：' + traceEsc(result.detail); return; }
  out.textContent = result.identical
    ? '两次运行的步骤、参数、排序结果与报告哈希完全一致。'
    : '存在差异：' + traceEsc((result.differences || []).join('；'));
}


const missionState = { plan: null, projectId: '', proof: null, job: '' };
// 中文备注：对任务编排（Mission）面板文本进行 HTML 转义。
function missionEsc(value) { return traceEsc(value === undefined || value === null ? '' : String(value)); }
// 中文备注：根据后台任务轮询结果与复现证明渲染任务执行状态概览。
function missionRenderStatus(job, proof) {
  const box = document.getElementById('mission-status-banner');
  if (!box) return;
  const info = job || {};
  let status = (proof && proof.run_status) || info.outcome_status
    || (info.status === 'failed' ? 'failed' : (info.status === 'done' ? 'succeeded' : 'running'));
  let cls = 'mission-banner mission-banner-running';
  let title = '正在执行分析';
  let body = '任务已提交；完成后这里会直接给出结论、失败原因和产物位置。';
  if (status === 'failed') {
    cls = 'mission-banner mission-banner-failed';
    title = '本次分析未产出数据';
    body = (proof && proof.run_summary) || ('执行失败：' + (info.error || info.stopped_reason || '未知原因'));
  } else if (status === 'partial') {
    cls = 'mission-banner mission-banner-partial';
    title = '结果不完整';
    body = (proof && proof.run_summary) || ('分析提前结束：' + (info.stopped_reason || '预算耗尽'));
  } else if (status === 'succeeded') {
    cls = 'mission-banner mission-banner-succeeded';
    title = '分析完成';
    body = (proof && proof.run_summary) || '报告、图表与决策轨迹已写入下方目录。';
  }
  let html = '<div class="' + cls + '"><div style="font-size:14px;font-weight:600;margin-bottom:4px;">'
    + missionEsc(title) + '</div><div>' + missionEsc(body) + '</div>';
  const failure = proof && proof.failure;
  if (failure) {
    html += '<div class="mission-hint">终止原因：' + missionEsc(failure.reason) + '</div>';
    html += '<div class="mission-hint">排查建议：' + missionEsc(failure.hint) + '</div>';
  }
  (info.diagnostics || []).forEach(function (item) {
    html += '<div class="mission-hint">数据加载提示：' + missionEsc(item) + '</div>';
  });
  box.innerHTML = html + '</div>';
}
// 中文备注：渲染任务生成的报告、图表与数据产物下载/预览列表。
function missionRenderArtifacts(proof) {
  const box = document.getElementById('mission-artifacts');
  if (!box) return;
  const artifacts = (proof && proof.artifacts) || [];
  const dir = (proof && proof.output_dir) || '';
  let html = '<div class="trace-meta" style="font-weight:500;margin-bottom:6px;">本次产物在哪</div>';
  html += '<div class="mission-path">' + missionEsc(dir) + '</div>';
  if (!artifacts.length) {
    html += '<div class="mission-hint">本次没有生成结果文件；失败时通常只有一份占位报告。</div>';
  } else {
    html += '<div class="mission-hint">已生成 ' + artifacts.length + ' 个文件：'
      + artifacts.slice(0, 8).map(function (item) { return missionEsc(item.name); }).join('、') + '</div>';
    const figures = artifacts.filter(function (item) { return item.kind === 'figure'; }).length;
    html += figures
      ? '<div class="mission-hint">图表 ' + figures + ' 张；报告、轨迹都在上面的目录里。</div>'
      : '<div class="mission-hint">没有图表：本次没有进入出图与候选排序环节。</div>';
  }
  html += '<div class="mission-hint">这一区只放可复现凭证；候选表、剪接事件与图表请到左侧「报告」「事件浏览器」「候选新抗原」「可视化」页查看。</div>';
  box.innerHTML = html;
}
function missionOpenReport(format) {
  const id = missionState.projectId;
  if (!id) { document.getElementById('mission-verify-result').textContent = '请先执行一次分析。'; return; }
  const urls = (missionState.proof && missionState.proof.report_urls) || {};
  const url = urls[format] || ('/api/report/' + encodeURIComponent(id) + '?format=' + format);
  window.open(url, '_blank', 'noopener');
}
// 中文备注：更新任务编排面板的状态提示栏文本。
function missionSetStatus(text) {
  document.getElementById('mission-plan-status').textContent = text;
}
// 中文备注：按固定间隔轮询后台异步任务状态，直到完成或失败并触发回调。
function missionPoll(jobId, onDone, onTick) {
  let attempts = 0;
  const tick = async function () {
    attempts += 1;
    const job = await apiCall('/jobs/' + encodeURIComponent(jobId));
    if (!job) { onDone({ status: 'failed', error: '无法查询任务状态' }); return; }
    if (onTick) onTick(job, attempts);
    if (job.status === 'running' && attempts < 160) {
      setTimeout(tick, 1500);
      return;
    }
    onDone(job);
  };
  tick();
}
async function missionGenerate() {
  missionSetStatus('正在生成计划…');
  const payload = { query: document.getElementById('mission-query').value.trim() };
  const result = await apiCall('/plan/preview', { method: 'POST', body: JSON.stringify(payload) });
  if (!result || !result.plan) { missionSetStatus('计划生成失败：' + traceEsc((result && result.detail) || '接口不可用')); return; }
  missionState.plan = result.plan;
  const plan = result.plan;
  document.getElementById('mission-goal').value = plan.goal || '';
  document.getElementById('mission-intent').value = plan.intent || 'differential_AS';
  document.getElementById('mission-fdr').value = (plan.thresholds || {}).fdr || 0.05;
  document.getElementById('mission-dpsi').value = (plan.thresholds || {}).delta_psi || 0.1;
  document.getElementById('mission-topn').value = (plan.thresholds || {}).top_candidates || 20;
  document.getElementById('mission-steps').value = (plan.budgets || {}).max_steps || 20;
  document.getElementById('mission-tools').value = (plan.expected_tools || []).join(String.fromCharCode(10));
  document.getElementById('mission-plan-meta').textContent = '计划来源 ' + traceEsc(plan.source)
    + '；可用动作注册表 ' + traceEsc(result.registry_size) + ' 个；预期输出：'
    + traceEsc((plan.expected_outputs || []).join('、'));
  document.getElementById('mission-plan-card').style.display = 'block';
  missionSetStatus('计划已生成，请审阅或修改后执行。');
}
function missionCollectPlan() {
  const base = missionState.plan || {};
  const thresholds = Object.assign({}, base.thresholds || {}, {
    fdr: parseFloat(document.getElementById('mission-fdr').value),
    delta_psi: parseFloat(document.getElementById('mission-dpsi').value),
    top_candidates: parseInt(document.getElementById('mission-topn').value, 10)
  });
  const budgets = Object.assign({}, base.budgets || {}, {
    max_steps: parseInt(document.getElementById('mission-steps').value, 10)
  });
  return {
    goal: document.getElementById('mission-goal').value.trim() || base.goal,
    intent: document.getElementById('mission-intent').value,
    thresholds: thresholds, budgets: budgets,
    expected_tools: document.getElementById('mission-tools').value.split(String.fromCharCode(10))
      .map(function (s) { return s.trim(); }).filter(Boolean),
    expected_outputs: base.expected_outputs || [],
    source: 'user', created_at: base.created_at || '', notes: base.notes || []
  };
}
async function missionRun() {
  const inputDir = document.getElementById('mission-input').value.trim();
  if (!inputDir) { missionSetStatus('请先填写输入数据目录。'); return; }
  const resultBox = document.getElementById('mission-result');
  resultBox.style.display = 'block';
  missionRenderStatus({ status: 'running' }, null);
  missionSetStatus('正在执行分析，可能需要几十秒…');
  const payload = {
    query: document.getElementById('mission-query').value.trim(),
    input_dir: inputDir, plan: missionCollectPlan()
  };
  const started = await apiCall('/plan/run', { method: 'POST', body: JSON.stringify(payload) });
  if (!started || !started.job_id) {
    missionRenderStatus({ status: 'failed', error: (started && started.detail) || '接口不可用' }, null);
    missionSetStatus('启动失败：' + traceEsc((started && started.detail) || '接口不可用')); return;
  }
  missionState.job = started.job_id;
  missionPoll(started.job_id, function (job) {
    resultBox.style.display = 'block';
    if (job.status === 'done') {
      missionState.projectId = job.project_id || '';
      missionRenderStatus(job, null);
      document.getElementById('mission-run-summary').textContent = '项目 '
        + missionEsc(job.project_id) + '；模式 ' + missionEsc(job.mode) + '；执行 '
        + missionEsc(job.steps) + ' 步；终止状态 ' + missionEsc(job.stopped_reason || '正常结束')
        + '；输入事件 ' + missionEsc(job.event_count || 0) + ' 条；图表 ' + missionEsc(job.figures || 0) + ' 张。';
      missionSetStatus('正在生成可复现证明…');
      missionLoadProof(job.project_id, job);
    } else {
      missionRenderStatus(job, null);
      missionSetStatus('执行失败：' + missionEsc(job.error || '未知错误'));
    }
  }, function (job, n) {
    if (n % 4 === 0) missionSetStatus('正在执行分析…（已等待 ' + Math.round(n * 1.5) + ' 秒）');
  });
}
async function missionLoadProof(projectId, job) {
  const proof = await apiCall('/projects/' + encodeURIComponent(projectId) + '/proof');
  if (!proof || proof.detail) {
    missionRenderStatus(job || {}, null);
    missionSetStatus('证明生成失败：' + missionEsc((proof && proof.detail) || '接口不可用')); return;
  }
  missionState.proof = proof;
  missionRenderStatus(job || {}, proof);
  missionRenderArtifacts(proof);
  const dev = proof.deviations || {};
  let devHtml = '<div class="trace-meta" style="font-weight:500;margin-bottom:6px;">计划与实际</div>';
  devHtml += '<div class="trace-meta">计划工具 ' + missionEsc(dev.planned_count)
    + ' 个，实际执行 ' + missionEsc(dev.executed_count) + ' 步，计划命中率 '
    + missionEsc(dev.adherence_ratio === null ? '无计划' : Math.round((dev.adherence_ratio || 0) * 100) + '%') + '</div>';
  devHtml += '<div class="mission-hint">' + missionEsc(dev.note || '') + '</div>';
  if ((dev.planned_not_run || []).length) {
    devHtml += '<div class="trace-call"><div style="font-weight:500">未执行的计划动作（'
      + dev.planned_not_run.length + ' 个）</div><div class="trace-meta">'
      + missionEsc(dev.planned_not_run.join('、')) + '</div><div class="mission-hint">'
      + missionEsc(dev.planned_not_run_reason || '') + '</div></div>';
  }
  (dev.autonomous_additions || []).slice(0, 6).forEach(function (item) {
    devHtml += '<div class="trace-call"><div style="font-weight:500">自主补充 ' + missionEsc(item.action)
      + ' · ' + traceBadge(item.source) + '</div><div class="trace-meta">'
      + missionEsc(item.reason_zh || item.reason) + '</div>'
      + '<details style="margin-top:4px;"><summary class="trace-meta" style="cursor:pointer;">查看模型原始依据</summary>'
      + '<div class="trace-meta">' + missionEsc(item.reason) + '</div></details></div>';
  });
  document.getElementById('mission-deviations').innerHTML = devHtml;
  const traj = proof.trajectory || {};
  const reports = Object.keys(proof.reports || {}).length;
  document.getElementById('mission-proof').innerHTML =
    '<div class="trace-meta" style="font-weight:500;margin-bottom:6px;">可复现证明</div>'
    + '<div class="trace-meta">完整性 ' + (proof.integrity_ok ? '校验通过' : '未通过')
    + '；输入指纹 ' + missionEsc(Object.keys(proof.input_fingerprints || {}).length)
    + ' 个文件；报告哈希 ' + missionEsc(reports) + ' 份；模型调用 '
    + missionEsc(traj.model_calls) + ' 次；工具调用 ' + missionEsc(traj.tool_calls) + ' 次</div>'
    + '<div class="trace-call mission-code" style="margin-top:8px;">'
    + missionEsc(proof.replay_command) + '</div>'
    + '<div class="mission-hint">' + missionEsc((proof.limitations || []).join(' ')) + '</div>';
  missionSetStatus(proof.run_status === 'failed'
    ? '分析未产出数据；失败原因与产物位置已显示在上方。'
    : '分析完成，证明已生成。可点「一键离线重放验证」。');
}
async function missionVerify() {
  const id = missionState.projectId;
  if (!id) return;
  document.getElementById('mission-verify-result').textContent = '正在离线重放并逐项比对…';
  const started = await apiCall('/projects/' + encodeURIComponent(id) + '/verify',
    { method: 'POST', body: JSON.stringify({}) });
  if (!started || !started.job_id) {
    document.getElementById('mission-verify-result').textContent =
      '验证启动失败：' + traceEsc((started && started.detail) || '接口不可用');
    return;
  }
  missionPoll(started.job_id, function (job) {
    const box = document.getElementById('mission-verify-result');
    if (job.status === 'done') {
      box.textContent = job.identical
        ? '重放通过：步骤、参数、排序结果与报告哈希逐项一致，且全程未调用模型或外部工具。'
        : '重放存在差异：' + traceEsc((job.differences || []).join('；'));
    } else {
      box.textContent = '验证失败：' + traceEsc(job.error || '未知错误');
    }
  }, function (job, n) {
    if (n % 4 === 0) document.getElementById('mission-verify-result').textContent =
      '正在离线重放…（已等待 ' + Math.round(n * 1.5) + ' 秒）';
  });
}
function missionCopyProof() {
  const command = missionState.proof && missionState.proof.replay_command;
  const box = document.getElementById('mission-verify-result');
  if (!command) { box.textContent = '暂无可复制的重放命令。'; return; }
  if (navigator.clipboard) navigator.clipboard.writeText(command);
  box.textContent = '重放命令已复制到剪贴板（单行，可直接粘贴到终端）。';
}
function missionOpenTrace() {
  const id = missionState.projectId;
  if (!id) return;
  const select = document.getElementById('trace-project');
  if (select) {
    const option = Array.from(select.options).find(function (o) { return o.value === id; });
    if (!option) { const opt = document.createElement('option'); opt.value = id; opt.textContent = id; select.appendChild(opt); }
    select.value = id;
  }
  navigateTo('trace');
}

// 中文备注：切换主界面当前激活的工作区页面，并触发对应页面的数据加载与动效。
function navigateTo(page) {
  let targetMode = null;
  if (page === 'peptide') { page = 'neoantigen'; targetMode = 'direct'; }
  if (!document.getElementById('page-' + page)) return;
  closeProjectDetail();
  const previousPage = state.currentPage;
  toggleNavigation(false);
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.dataset.page === page) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });

  document.querySelectorAll('.nav-item').forEach(item => { item.classList.toggle('active', item.dataset.page === page); });
  document.querySelectorAll('.page').forEach(p => { p.classList.toggle('active', p.id === `page-${page}`); });
  state.currentPage = page;
  syncFluidMarker();
  animateWorkspace(previousPage, page);
  document.getElementById('workspace-content').focus({preventScroll:true});
  window.scrollTo({top:0, behavior:'instant'});
  if (page === 'dashboard') loadDashboard();
  if (page === 'pipeline') loadPipeline();
  if (page === 'neoantigen') {
    if (targetMode) neoSwitchMode(targetMode);
    neoInitPage();
  }
  if (page === 'explorer') loadExplorer();
  if (page === 'settings') { loadModelConfig(); loadEsm2Config(false); loadMcpServers(); }
  if (page === 'trace') loadDecisionTrace();
  if (page === 'mission') missionGenerate();
}
// 中文备注：封装带全局加载进度条与统一错误处理的 fetch API 请求助手。
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`/api${endpoint}`, { headers: { 'Content-Type': 'application/json' }, ...options });
    if (!response.ok) {
      console.warn('API HTTP Error:', response.status, endpoint);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return null;
  }
}
// 中文备注：加载仪表盘统计概览与历史项目列表。
async function loadDashboard() {
  const response = await apiCall('/projects');
  if (!response) {
    document.getElementById('recent-projects').innerHTML = '<div role="alert" style="padding:24px;color:var(--danger)">暂时无法连接项目服务。请检查服务是否启动，然后点击上方刷新。</div>';
    return;
  }
  const projectsData = (response && response.projects) || response || [];
  state.projects = Array.isArray(projectsData) ? projectsData : [];

  // Keep the selected historical project across refreshes.
  if (state.projects.length > 0) {
    const selectedProject = state.projects.find(p => p.project_id === state.currentProject) || state.projects[0];
    state.currentProject = selectedProject.project_id;
    localStorage.setItem('epitoperank.currentProject', state.currentProject);
    document.getElementById('current-project').textContent = selectedProject.name || selectedProject.project_id;

    // Counters come from the list endpoint (SQL counts), so the dashboard stays
    // fast even for projects with a million events.
    document.getElementById('stat-samples').textContent = selectedProject.sample_count ?? '-';
    document.getElementById('stat-events').textContent = fmtCount(selectedProject.event_count);
    document.getElementById('stat-significant').textContent = fmtCount(selectedProject.significant_count);
    document.getElementById('stat-status').innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>已归档</span>';

    if (document.body.classList.contains('detail-open')) {
      await loadProjectDetail(state.currentProject);
    }
  } else {
    document.getElementById('stat-samples').textContent = '-';
    document.getElementById('stat-events').textContent = '-';
    document.getElementById('stat-significant').textContent = '-';
    closeProjectDetail();
  }

  renderProjectHistory();
  loadStorageHint();
}
// 中文备注：将整数计数格式化为带千分位分隔符的可读字符串。
function fmtCount(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return n.toLocaleString('en-US');
}
// 中文备注：将时间戳或 ISO 日期字符串格式化为本地可读日期时间。
function fmtDate(value) {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
// 中文备注：刷新界面中的当前项目存储目录提示信息。
async function loadStorageHint() {
  if (state.storage) { renderStorageHint(); return; }
  const info = await apiCall('/storage');
  if (info) { state.storage = info; renderStorageHint(); }
}
// 中文备注：将当前项目的数据存储路径渲染到页面提示区。
function renderStorageHint() {
  const box = document.getElementById('storage-hint');
  if (!box || !state.storage) return;
  const root = state.storage.runtime_root || '-';
  const db = (state.storage.databases || {})['epitoperank.sqlite3'] || {};
  box.innerHTML = `数据目录：<span style="font-family:var(--font-mono);word-break:break-all;color:var(--text-secondary);">${ingestEsc(root)}</span>`
    + `　·　数据库 ${db.size_mb || 0} MB`;
}
// 中文备注：打开侧边历史项目详情抽屉，并在未加载或切换项目时自动拉取最新详情。
async function openProjectDetail() {
  if (!state.currentProject && Array.isArray(state.projects) && state.projects.length > 0) {
    state.currentProject = state.projects[0].project_id;
    localStorage.setItem('epitoperank.currentProject', state.currentProject);
  }
  if (!state.currentProject) {
    AppNotify.toast('请先在仪表盘选择或运行一个项目，再打开项目详情。', 'warning');
    return;
  }
  toggleNavigation(false);
  const hint = document.getElementById('detail-bundle-hint');
  if (hint) hint.textContent = '';
  document.body.classList.add('detail-open');
  const loadedId = state.detail && state.detail.project ? state.detail.project.project_id : null;
  if (!state.detail || loadedId !== state.currentProject) {
    const titleEl = document.getElementById('detail-title');
    if (titleEl) titleEl.textContent = '加载中…';
    await loadProjectDetail(state.currentProject);
  }
}
// 中文备注：收起并清空当前展开的历史项目详情面板。
function closeProjectDetail() { document.body.classList.remove('detail-open'); }
// 中文备注：按项目 ID 加载历史项目的摘要、事件数、报告与导出操作区。
async function loadProjectDetail(projectId) {
  const status = await apiCall(`/status/${encodeURIComponent(projectId)}`);
  state.detail = status || null;
  if (!status || !status.project) {
    closeProjectDetail();
    AppNotify.toast('无法加载该项目详情，可能项目已被删除或服务未响应。', 'error');
    return;
  }

  const project = status.project || {};
  document.getElementById('detail-title').textContent = project.name || project.project_id || projectId;
  document.getElementById('detail-meta').textContent =
    `${project.project_id || projectId} · ${fmtDate(project.created_at)} · 输入格式 ${project.source_format || '-'} · ${fmtCount(status.events)} 个事件 / ${fmtCount(status.significant)} 个显著`;

  const groups = {};
  (status.samples || []).forEach(s => { const g = s.group_name || '未分组'; (groups[g] = groups[g] || []).push(s.sample_id); });
  const groupChips = Object.entries(groups).map(([g, ids]) =>
    `<span class="hero-chip" title="${ingestEsc(ids.join(', '))}">${ingestEsc(g)} · ${ids.length}</span>`).join('');
  document.getElementById('detail-groups').innerHTML = groupChips || '<span style="font-size:12px;color:var(--text-muted);">未记录样本分组</span>';

  const types = status.event_types || {};
  document.getElementById('detail-types').innerHTML = Object.entries(types).map(([k, v]) =>
    `<span class="hero-chip">${ingestEsc(k)} · ${fmtCount(v)}</span>`).join('') || '<span style="font-size:12px;color:var(--text-muted);">-</span>';

  const logs = (status.logs || []).slice(-12).reverse();
  document.getElementById('detail-logs').innerHTML = logs.length ? logs.map(l =>
    `<div style="display:flex;gap:8px;border-bottom:1px dashed var(--border);padding:4px 0;">
       <span style="color:var(--text-muted);white-space:nowrap;">${ingestEsc((l.created_at || '').replace('T', ' ').slice(5, 16))}</span>
       <span style="color:var(--text-secondary);">[${ingestEsc(l.agent || '')}] ${ingestEsc(l.action || '')}</span>
       <span style="margin-left:auto;color:${l.status === 'ok' ? 'var(--secondary)' : 'var(--danger)'};">${ingestEsc(l.status || '')}</span>
     </div>`).join('') : '<span style="font-size:12px;color:var(--text-muted);">无日志</span>';

  const figures = (status.artifacts || []).filter(a => (a.kind || '').startsWith('figure:'));
  document.getElementById('detail-figures').innerHTML = figures.length ? figures.map(a => {
    const name = a.kind.split(':')[1];
    const url = `/api/figure/${encodeURIComponent(projectId)}/${encodeURIComponent(name)}`;
    return `<a href="${url}" target="_blank" rel="noopener" style="display:block;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;background:var(--surface-2);">
      <img src="${url}" alt="${ingestEsc(name)}" loading="lazy" style="width:100%;height:96px;object-fit:cover;display:block;">
      <div style="font-size:12px;padding:4px 6px;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${ingestEsc(name)}</div>
    </a>`;
  }).join('') : '<span style="font-size:12px;color:var(--text-muted);">该项目没有保存图表</span>';

  const candidates = status.candidates || [];
  document.getElementById('detail-candidates').innerHTML = candidates.length ? `<table style="width:100%;border-collapse:collapse;">
      <thead><tr style="text-align:left;color:var(--text-muted);font-size:12px;">
        <th style="padding:4px 6px;">#</th><th style="padding:4px 6px;">基因</th><th style="padding:4px 6px;">类型</th>
        <th style="padding:4px 6px;">ΔPSI</th><th style="padding:4px 6px;">FDR</th></tr></thead>
      <tbody>${candidates.map(c => `<tr style="border-top:1px solid var(--border);">
        <td style="padding:4px 6px;">${ingestEsc(c.rank)}</td>
        <td style="padding:4px 6px;font-weight:600;">${ingestEsc(c.gene_symbol || c.gene_id || '-')}</td>
        <td style="padding:4px 6px;">${ingestEsc(c.event_type || '-')}</td>
        <td style="padding:4px 6px;color:${(c.delta_psi || 0) > 0 ? 'var(--danger)' : 'var(--secondary)'};">${c.delta_psi === null || c.delta_psi === undefined ? '-' : Number(c.delta_psi).toFixed(3)}</td>
        <td style="padding:4px 6px;">${c.fdr === null || c.fdr === undefined ? '-' : fmtFdr(c.fdr)}</td>
      </tr>`).join('')}</tbody></table>`
    : '<span style="font-size:12px;color:var(--text-muted);">该项目没有候选事件记录</span>';
}
// 中文备注：按格式打开 HTML 报告或触发 PDF 报告下载（兼容桌面端 WebView2 窗口）。
function openReport(format) {
  if (!state.currentProject) return;
  const url = `/api/report/${encodeURIComponent(state.currentProject)}?format=${encodeURIComponent(format)}`;
  if (format === 'pdf') {
    const link = document.createElement('a');
    link.href = url;
    link.download = `${state.currentProject}_report.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    return;
  }
  const win = window.open(url, '_blank');
  if (!win) {
    closeProjectDetail();
    navigateTo('report');
    if (typeof generateReport === 'function') generateReport('html');
  }
}
// 中文备注：调用后端接口在系统文件管理器中打开当前项目的成果目录。
async function revealProjectBundle() {
  if (!state.currentProject) return;
  const hint = document.getElementById('detail-bundle-hint');
  const say = (text, ok) => {
    if (!hint) return;
    hint.textContent = text;
    hint.style.color = ok ? 'var(--secondary)' : 'var(--danger)';
  };
  if (hint) say('正在整理成果文件夹…', true);
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(state.currentProject)}/reveal-bundle`, { method: 'POST' });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { say(data.detail || '打开成果文件夹失败', false); return; }
    say('已打开：' + (data.path || ''), true);
  } catch (error) {
    say('打开成果文件夹失败：' + error.message, false);
  }
}
// 中文备注：将当前项目的成果目录打包为 ZIP 压缩包并提示保存路径。
async function packageProject() {
  if (!state.currentProject) return;
  const hint = document.getElementById('detail-bundle-hint');
  const say = (text, ok) => {
    if (!hint) return;
    hint.textContent = text;
    hint.style.color = ok ? 'var(--secondary)' : 'var(--danger)';
  };
  if (hint) say('正在打包…', true);
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(state.currentProject)}/package`, { method: 'POST' });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { say(data.detail || '打包失败', false); return; }
    say(`已打包（${data.size_mb} MB）：${data.path}`, true);
  } catch (error) {
    say('打包失败：' + error.message, false);
  }
}
// 中文备注：关闭项目详情抽屉并跳转到事件浏览器页面查看全部剪接事件。
function jumpToExplorer() {
  if (!state.currentProject) return;
  closeProjectDetail();
  navigateTo('explorer');
}
// 中文备注：二次确认后删除当前选中项目及其历史记录并刷新列表。
async function deleteCurrentProject() {
  if (!state.currentProject) return;
  const project = (state.projects || []).find(p => p.project_id === state.currentProject) || {};
  const label = project.name || state.currentProject;
  const confirmed = await AppNotify.confirm(
    `项目「${label}」的数据库记录、图表与报告目录都会被移除，且无法撤销。原始输入数据不会被删除。`,
    { kind: 'warning', title: '删除这个项目？', confirmLabel: '删除项目', cancelLabel: '保留项目', danger: true }
  );
  if (!confirmed) return;
  const response = await fetch(`/api/projects/${encodeURIComponent(state.currentProject)}`, { method: 'DELETE' });
  if (!response.ok) { AppNotify.toast('删除失败：HTTP ' + response.status, 'error'); return; }
  localStorage.removeItem('epitoperank.currentProject');
  state.currentProject = null;
  state.detail = null;
  closeProjectDetail();
  await loadDashboard();
}
// 中文备注：按搜索词过滤并渲染历史项目卡片列表。
function renderProjectHistory() {
  const projectsList = document.getElementById('recent-projects');
  const term = (document.getElementById('project-search')?.value || '').toLowerCase();
  const projects = state.projects.filter(p => ((p.name || '') + ' ' + (p.project_id || '') + ' ' + (p.query || '')).toLowerCase().includes(term));
  if (state.projects.length === 0) {
    projectsList.innerHTML = '<div style="padding: 40px; text-align: center; color: var(--text-muted);">暂无项目</div>';
  } else {
    projectsList.innerHTML = projects.map(p => {
      const active = p.project_id === state.currentProject;
      return `<div style="padding: 11px 12px; border-bottom: 1px solid var(--border); cursor: pointer; ${active ? 'background:var(--gray-100);border-left:1px solid var(--black);' : 'border-left:3px solid transparent;'}" onclick="selectProject('${ingestEsc(p.project_id)}')">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline;">
          <div style="font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${ingestEsc(p.name || p.project_id)}</div>
          <div style="font-size:12px;color:var(--text-muted);white-space:nowrap;">${ingestEsc(fmtDate(p.created_at).slice(0, 10))}</div>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);margin-top:5px;display:flex;gap:10px;flex-wrap:wrap;">
          <span>${ingestEsc(p.source_format || '-')}</span>
          <span>事件 ${fmtCount(p.event_count)}</span>
          <span style="color:var(--danger);">显著 ${fmtCount(p.significant_count)}</span>
        </div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${ingestEsc(p.query || '分析查询')}</div>
      </div>`;
    }).join('') || '<div style="padding:20px;text-align:center;color:var(--text-muted);">没有匹配的项目</div>';
  }
}
async function loadPipeline() {
  if (!state.currentProject) return;
  const status = await apiCall(`/status/${state.currentProject}`);
  state.analysisStatus = status;
  if (status) updatePipelineUI(status);
}
// 中文备注：根据后端返回的分析状态同步更新流水线各阶段的进度展示。
function updatePipelineUI(status) {
  const steps = document.querySelectorAll('.pipeline-step');
  
  // Try to get current_step from status, or infer from logs
  let currentStep = status.current_step;
  let statusText = '等待启动...';
  
  if (currentStep === undefined || currentStep === null) {
    // Infer step from logs
    const logs = status.logs || [];
    const actions = logs.map(l => l.action);
    
    if (actions.includes('run_finished')) {
      currentStep = steps.length; // All steps completed
      statusText = '分析已完成';
    } else if (actions.includes('interpret_candidates') || actions.includes('generate_report')) {
      currentStep = 5; // Interpretation done
      statusText = '解读 Agent 正在生成生物学解读...';
    } else if (actions.includes('collect_literature_evidence')) {
      currentStep = 4;
      statusText = '注释 Agent 正在收集文献证据...';
    } else if (actions.includes('run_enrichment')) {
      currentStep = 4;
      statusText = '注释 Agent 正在进行通路富集分析...';
    } else if (actions.includes('rank_candidates')) {
      currentStep = 3;
      statusText = '统计 Agent 正在排序候选事件...';
    } else if (actions.includes('filter_significant_events')) {
      currentStep = 3;
      statusText = '剪接检测 Agent 正在筛选显著事件...';
    } else if (actions.includes('summarize_dataset')) {
      currentStep = 2;
      statusText = '质控 Agent 正在进行质量检查...';
    } else if (actions.includes('understand_query')) {
      currentStep = 1;
      statusText = '数据 Agent 正在理解查询...';
    } else if (actions.includes('run_started')) {
      currentStep = 0;
      statusText = '分析已启动，准备中...';
    } else {
      currentStep = 0;
      statusText = '等待启动...';
    }
  } else {
    const stepNames = ['数据加载', '质量控制', '剪接检测', '统计分析', '功能注释', '生物学解读'];
    statusText = currentStep < stepNames.length ? `正在执行: ${stepNames[currentStep]}` : '处理中...';
  }
  
  document.getElementById('pipeline-status-text').textContent = statusText;
  
  const totalSteps = steps.length;
  const progress = Math.round((currentStep / totalSteps) * 100);
  document.getElementById('pipeline-progress').textContent = `${progress}%`;
  document.getElementById('progress-bar').style.width = `${progress}%`;
  
  steps.forEach((step, index) => {
    step.classList.remove('waiting', 'active', 'completed');
    if (index < currentStep) { 
      step.classList.add('completed'); 
      step.querySelector('.status').className = 'status status-completed'; 
      step.querySelector('.status').innerHTML = '<span class="status-dot"></span>已完成'; 
    } else if (index === currentStep && currentStep < totalSteps) { 
      step.classList.add('active'); 
      step.querySelector('.status').className = 'status status-running'; 
      step.querySelector('.status').innerHTML = '<span class="status-dot"></span>运行中'; 
    } else { 
      step.classList.add('waiting'); 
      step.querySelector('.status').className = 'status status-waiting'; 
      step.querySelector('.status').innerHTML = '<span class="status-dot"></span>等待中'; 
    }
  });
}
// 中文备注：初始化事件浏览器并加载当前项目的第一页剪接事件。
async function loadExplorer() {
  if (!state.currentProject) return;
  // Real rMATS projects hold 10^5-10^6 events: filtering and paging happen in
  // SQLite, the browser only ever receives one page.
  await loadEventPage(1);
}
// 中文备注：收集事件浏览器中的搜索关键词、事件类型、显著性与排序筛选条件。
function explorerFilters() {
  const term = (document.getElementById('search-input')?.value || '').trim();
  const types = Array.from(document.querySelectorAll('.checkbox-group input[type="checkbox"]'))
    .filter(cb => cb.checked).map(cb => cb.value);
  return {
    q: term,
    // The backend accepts a single event type; when several are ticked we omit
    // the filter and let the user narrow further, rather than silently
    // showing only the first one.
    event_type: types.length === 1 ? types[0] : '',
    significant_only: !!document.getElementById('filter-significant')?.checked,
    order_by: document.getElementById('filter-order')?.value || 'fdr',
  };
}
// 中文备注：按页码与筛选条件分页请求后端项目剪接事件列表。
async function loadEventPage(page) {
  if (!state.currentProject) return;
  const filters = explorerFilters();
  const params = new URLSearchParams({
    page: String(page),
    size: '50',
    q: filters.q,
    event_type: filters.event_type,
    significant_only: filters.significant_only ? 'true' : 'false',
    order_by: filters.order_by,
  });
  const skeletonTimer = setTimeout(eventsSkeleton, 120);
  let data;
  try { data = await apiCall(`/projects/${encodeURIComponent(state.currentProject)}/events?${params.toString()}`); }
  finally { clearTimeout(skeletonTimer); }
  if (!data || data.events === undefined) {
    document.getElementById('events-table').innerHTML =
      '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--danger);">读取事件失败（项目可能已被删除）</td></tr>';
    return;
  }
  state.events = data.events;
  state.eventPage = data.page;
  state.eventPages = data.pages;
  state.eventTotal = data.total;
  renderEventsTable(data.events);
  const info = document.getElementById('events-pager-info');
  if (info) info.textContent = `共 ${fmtCount(data.total)} 个事件 · 每页 ${data.size} 条 · 已按${({fdr: 'FDR', delta_psi: '|ΔPSI|', gene: '基因名'})[filters.order_by] || 'FDR'}排序`;
  const pager = document.getElementById('events-pager-page');
  if (pager) pager.textContent = `${data.page} / ${data.pages}`;
}
// 中文备注：跳转到事件浏览器的指定页码并刷新表格。
function gotoEventPage(page) {
  const target = Math.min(Math.max(1, Number(page) || 1), state.eventPages || 1);
  loadEventPage(target);
}
// 中文备注：将极小数值（如 p 值）格式化为科学计数法字符串。
function fmtSci(value, digits) {
  if (value === null || value === undefined || value === '') return '-';
  const n = Number(value);
  if (!isFinite(n)) return '-';
  if (n === 0) return '0';
  if (Math.abs(n) < 1e-300) return n > 0 ? '<1e-300' : '>-1e-300';
  const parts = n.toExponential(digits === undefined ? 2 : digits).split('e');
  let mantissa = parts[0];
  if (mantissa.indexOf('.') >= 0) mantissa = mantissa.replace(/0+$/, '').replace(/[.]$/, '');
  return mantissa + 'e' + String(Number(parts[1]));
}
// 中文备注：格式化 FDR 显著性数值，便于在表格中对齐展示。
function fmtFdr(value) {
  if (value === null || value === undefined || value === '') return '-';
  const n = Number(value);
  if (!isFinite(n)) return '-';
  if (n === 0) return '0';
  return n >= 0.001 ? n.toFixed(3) : fmtSci(n, 2);
}
// 中文备注：渲染带方向色标与进度条的 ΔPSI 表格单元格 HTML。
function dpsiCell(value) {
  if (value === null || value === undefined || value === '' || !isFinite(Number(value))) return '<td class="num">-</td>';
  const n = Number(value), direction = n > 0 ? 'up' : n < 0 ? 'down' : 'neutral';
  return `<td class="num"><span class="dpsi-cell"><span class="dpsi-value ${direction}">${n > 0 ? '+' : ''}${n.toFixed(3)}</span><span class="dpsi-bar" aria-hidden="true"><span class="${direction}" style="width:${(Math.min(Math.abs(n),1)*50).toFixed(1)}%"></span></span></span></td>`;
}
// 中文备注：生成事件列表加载期间的骨架屏占位行 HTML。
function eventsSkeleton() {
  const tbody = document.getElementById('events-table');
  if (!tbody) return;
  tbody.innerHTML = Array.from({length:9}, () => '<tr class="skeleton-row">' + [70,52,38,34,44].map((width,i) => `<td><span class="sk" style="width:${width}%;${i > 2 ? 'margin-left:auto;' : ''}"></span></td>`).join('') + '<td></td></tr>').join('');
}
const eventTable = document.getElementById('events-table');
// 中文备注：点击事件表格行后打开该剪接事件的详细信息弹窗。
function openEventRow(event) {
  if (event.target.closest('input.event-select-cb') || event.target.closest('td.event-select-cell')) return;
  const row = event.target.closest('tr[data-event]');
  if (!row || !eventTable.contains(row)) return;
  if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;
  if (event.type === 'keydown') event.preventDefault();
  viewEventDetails(row.dataset.event);
}
eventTable.addEventListener('click', openEventRow);
eventTable.addEventListener('keydown', openEventRow);
// 中文备注：将当前页的剪接事件数据渲染到表格主体并绑定行点击事件。
function renderEventsTable(events) {
  const tbody = document.getElementById('events-table');
  const allCb = document.getElementById('events-select-all');
  if (allCb) allCb.checked = false;
  if (!events || events.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">未找到匹配的事件</td></tr>';
    return;
  }
  tbody.innerHTML = events.map(event => {
    const eventId = event.event_id || event.id || '-';
    const gene = event.gene_symbol || event.gene || event.gene_id || '-';
    const eventType = event.event_type || event.type || '-';
    const dpsi = (event.delta_psi !== null && event.delta_psi !== undefined) ? Number(event.delta_psi).toFixed(3) : '-';
    const fdr = (event.fdr !== null && event.fdr !== undefined) ? fmtFdr(event.fdr) : '-';
    const color = (Number(event.delta_psi) || 0) > 0 ? 'var(--danger)' : 'var(--secondary)';
    const flag = event.significant ? '' : ' <span style="font-size:12px;color:var(--text-muted);">(不显著)</span>';
    const checked = neoSelectedEvents.has(eventId) ? ' checked' : '';
    return `<tr class="event-row" tabindex="0" data-event="${ingestEsc(eventId)}">
      <td class="event-select-cell"><input type="checkbox" class="event-select-cb" value="${ingestEsc(eventId)}" aria-label="选择 ${ingestEsc(eventId)}" onchange="toggleEventSelection(this.value, this.checked)"${checked}></td>
      <td class="mono">${ingestEsc(eventId)}</td>
      <td><strong>${ingestEsc(gene)}</strong>${flag}</td>
      <td>${ingestEsc(eventType)}</td>
      ${dpsiCell(event.delta_psi)}
      <td class="num">${ingestEsc(fdr)}</td>
      <td><span class="row-go" aria-hidden="true">›</span></td>
    </tr>`;
  }).join('');
}
// 中文备注：应用当前筛选条件并重置到第 1 页重新加载事件列表。
function applyFilters() {
  loadEventPage(1);
}
let activeChartRequest = 0;
// 中文备注：请求并展示指定类型的项目分析图表（火山图、热图、富集图等）。
function loadChart(chartType) {
  const request = ++activeChartRequest;
  const projectId = state.currentProject;
  document.querySelectorAll('#page-visualization button[onclick^="loadChart"]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.getAttribute('onclick').includes("'" + chartType + "'")));
  });
  document.getElementById('chart-select-mobile').value = chartType;

  const container = document.getElementById('chart-display');
  if (!projectId) {
    container.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 600px; color: var(--text-muted);">
        <div style="font-size: 36px; margin-bottom: 16px; opacity: 0.3;"></div>
        <div style="font-size: 16px; font-weight: 600;">未选择项目</div>
        <div style="font-size: 14px; margin-top: 8px;">请先在仪表盘选择一个分析项目</div>
      </div>`; 
    return; 
  }
  
  const meta = {
    volcano: ['火山图 Volcano Plot', '展示同时具有 ΔPSI 与 FDR 的事件。虚线标记图中采用的阈值。'],
    dpsi_waterfall: ['ΔPSI 瀑布图 Waterfall', '按 |ΔPSI| 排序的 Top 25 候选事件；橙色为包含水平上调，蓝色为下调，直观展示效应量谱。'],
    dpsi_ecdf: ['ΔPSI 累积分布 ECDF', 'ΔPSI 的经验累积分布曲线，并标注 |ΔPSI|>0.1 的事件占比，用于评估整体效应量分布。'],
    fdr_scree: ['显著性碎石图 Scree Plot', '候选排名对 -log10(FDR) 曲线，配合 FDR=0.05 参考线定位显著性拐点（elbow）。'],
    event_type_counts: ['事件类型分布 Composition', 'SE / MXE / A5SS / A3SS / RI 五类可变剪接事件的检出计数。'],
    event_significance: ['类型 × 显著性堆叠图', '各事件类型中通过阈值（FDR<0.05 且 |ΔPSI|>0.1）的显著事件与非显著事件构成。'],
    event_schematic: ['剪接机制示意图 Schematic', '五类可变剪接事件的外显子-内含子结构模式图（methods 级示意图）。'],
    psi_heatmap: ['PSI 热图 Heatmap', 'Top |ΔPSI| 事件的逐样本 PSI 热图，列上方标注样本分组，用于观察聚类模式。'],
    psi_distribution: ['分组 PSI 箱线图 Box Plot', '按实验组拆分的 Top 事件 PSI 分布（箱线 + 散点），用于识别离群样本。'],
    sample_composition: ['队列构成图 Cohort QC', '样本分组占比（环图）与批次分布（条形），为质控必备图表。'],
    candidate_ranking: ['候选基因排名 Ranking', 'AI 智能体综合评分（显著性+效应+生物学+文献）Top 15 候选事件。'],
    score_components: ['评分分解堆叠图 Decomposition', 'Top 候选的四维评分贡献分解：显著性 / 效应量 / 生物学 / 文献证据。'],
    enrichment: ['功能富集点图 Dot Plot', 'GO/KEGG 富集结果：横轴为富集倍数，颜色为 -log10(FDR)，点大小为重叠基因数。']
  };
  const info = meta[chartType] || ['图表', ''];
  
  container.innerHTML = `
    <div style="padding: 24px;">
      <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px; color: var(--text);">${info[0]}</div>
      <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6;">${info[1]}</div>
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 500px; background: var(--gray-100); border-radius: var(--radius);">
        <div style="width: 48px; height: 48px; border: 4px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <div style="margin-top: 20px; font-size: 14px; color: var(--text-secondary);">正在渲染图表（首次生成约需数秒）...</div>
      </div>
    </div>
  `;
  
  const img = document.createElement('img');
  img.alt = info[0];
  img.style.width = '100%';
  img.style.borderRadius = 'var(--radius)';
  img.style.marginTop = '20px';
  img.style.boxShadow = 'var(--shadow)';
  
  img.onload = function() {
    if (request !== activeChartRequest || projectId !== state.currentProject) return;
    container.innerHTML = `
      <div style="padding: 24px;">
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px; color: var(--text);">${info[0]}</div>
        <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6;">${info[1]}</div>
      </div>
    `;
    container.appendChild(img);
  };
  
  img.onerror = function() { 
    if (request !== activeChartRequest || projectId !== state.currentProject) return;
    container.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 600px; color: var(--text-muted);">
        <div style="font-size: 36px; margin-bottom: 16px; opacity: 0.3;"></div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">图表不可用</div>
        <div style="font-size: 14px;">请确认项目输入仍可访问，然后重试。</div>
      </div>
    `; 
  };
  img.src = '/api/figure/' + encodeURIComponent(projectId) + '/' + encodeURIComponent(chartType);
}
// 中文备注：按基因名检索当前项目相关剪接事件、功能注释与文献证据。
async function exploreGene() {
  const geneSymbol = document.getElementById('gene-search').value.trim();
  if (!geneSymbol) {
    AppNotify.toast('请输入基因符号', 'warning');
    return;
  }
  
  const container = document.getElementById('gene-details');
  if (!state.currentProject) {
    container.innerHTML = `
      <div class="card">
        <div style="padding: 40px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 36px; margin-bottom: 12px; opacity: 0.3;"></div>
          <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">请先选择项目</div>
          <div style="font-size: 14px;">在仪表盘选择一个分析项目后再探索基因</div>
        </div>
      </div>`;
    return;
  }
  
  // Show loading state
  container.innerHTML = `
    <div class="card">
      <div style="padding: 60px; text-align: center;">
        <div style="width: 48px; height: 48px; border: 4px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
        <div style="font-size: 16px; font-weight: 600;">正在加载 ${geneSymbol} 的信息...</div>
      </div>
    </div>`;
  
  const status = await apiCall(`/status/${state.currentProject}`);
  const candidates = (status && status.candidates) || [];
  const geneEvents = candidates.filter(e => (e.gene_symbol || '').toLowerCase() === geneSymbol.toLowerCase());
  
  if (geneEvents.length === 0) {
    container.innerHTML = `
      <div class="card">
        <div style="padding: 60px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 36px; margin-bottom: 16px; opacity: 0.3;"></div>
          <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">未找到 ${geneSymbol} 的剪接事件</div>
          <div style="font-size: 14px;">该基因可能不在当前分析的候选列表中，或未达到显著性阈值</div>
          <button class="btn btn-secondary" style="margin-top: 20px;" onclick="navigateTo('explorer')">浏览所有事件</button>
        </div>
      </div>`;
    return;
  }
  
  // Sort events by significance
  geneEvents.sort((a, b) => (a.fdr || 1) - (b.fdr || 1));
  
  // Calculate summary statistics
  const significantEvents = geneEvents.filter(e => e.fdr < 0.05);
  const avgDeltaPSI = geneEvents.reduce((sum, e) => sum + Math.abs(parseFloat(e.delta_psi || 0)), 0) / geneEvents.length;
  const eventTypeCounts = {};
  geneEvents.forEach(e => {
    const type = e.event_type || 'Unknown';
    eventTypeCounts[type] = (eventTypeCounts[type] || 0) + 1;
  });
  
  // Build event types summary
  const eventTypeSummary = Object.entries(eventTypeCounts).map(([type, count]) => `${type}: ${count}`).join(', ');
  
  let eventsHtml = `
    <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
      <thead>
        <tr style="border-bottom: 2px solid var(--border);">
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">事件 ID</th>
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">类型</th>
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">Delta PSI</th>
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">FDR</th>
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">评分</th>
          <th style="text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary);">操作</th>
        </tr>
      </thead>
      <tbody>
        ${geneEvents.map(e => {
          const dpsi = Number(e.delta_psi).toFixed(3);
          const fdr = fmtFdr(e.fdr);
          const score = e.score !== undefined ? Number(e.score).toFixed(3) : '-';
          const sigLevel = e.fdr < 0.001 ? '***' : e.fdr < 0.01 ? '**' : e.fdr < 0.05 ? '*' : '';
          const sigColor = e.fdr < 0.001 ? '#dc2626' : e.fdr < 0.01 ? '#f59e0b' : e.fdr < 0.05 ? '#059669' : '#94a3b8';
          
          return `<tr style="border-bottom: 1px solid var(--border);">
            <td style="padding: 12px 16px; font-family: monospace;">${e.event_id || '-'}</td>
            <td style="padding: 12px 16px;"><span style="background: var(--bg); padding: 4px 10px; border-radius: var(--radius); font-size: 12px; font-weight: 600;">${e.event_type || '-'}</span></td>
            <td style="padding: 12px 16px; font-family: monospace; font-weight: 600;">${dpsi}</td>
            <td style="padding: 12px 16px; font-family: monospace; font-weight: 600; color: ${sigColor};">${ingestEsc(fdr)} ${sigLevel}</td>
            <td style="padding: 12px 16px; font-family: monospace;">${score}</td>
            <td style="padding: 12px 16px;"><button class="btn btn-sm btn-secondary" onclick="viewEventDetails('${e.event_id || e.id}')">详情</button></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  `;
  
  // Process evidence
  let evidence = geneEvents.length > 0 ? (geneEvents[0].evidence_json || '') : '';
  if (evidence) {
    try {
      const parsed = typeof evidence === 'string' ? JSON.parse(evidence) : evidence;
      if (Array.isArray(parsed)) { 
        evidence = parsed.map(item => `<div style="margin-bottom: 10px; padding-left: 16px; border-left: 1px solid var(--accent);">• ${typeof item === 'string' ? item : JSON.stringify(item)}</div>`).join(''); 
      } else if (typeof parsed === 'object') { 
        evidence = Object.entries(parsed).map(([k, v]) => `<div style="margin-bottom: 10px;"><strong>${k}:</strong> ${v}</div>`).join(''); 
      }
    } catch (e) { 
      evidence = `<div>${evidence}</div>`; 
    }
  }
  
  container.innerHTML = `
    <div class="card" style="margin-bottom: 24px;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
        <div>
          <div style="font-size: 28px; font-weight: 600; background: var(--black); ">${geneSymbol}</div>
          <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">基因剪接分析报告</div>
        </div>
        <button class="btn btn-secondary" onclick="navigateTo('explorer')">返回事件列表</button>
      </div>
      
      <div class="grid grid-3" style="margin-bottom: 28px;">
        <div style="background: var(--gray-100); padding: 20px; border-radius: var(--radius); text-align: center;">
          <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #0e7490; font-weight: 600; margin-bottom: 8px;">总事件数</div>
          <div style="font-size: 28px; font-weight: 600; color: #0e7490;">${geneEvents.length}</div>
        </div>
        <div style="background: var(--gray-100); padding: 20px; border-radius: var(--radius); text-align: center;">
          <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #065f46; font-weight: 600; margin-bottom: 8px;">显著事件</div>
          <div style="font-size: 28px; font-weight: 600; color: #065f46;">${significantEvents.length}</div>
        </div>
        <div style="background: var(--gray-100); padding: 20px; border-radius: var(--radius); text-align: center;">
          <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #7c3aed; font-weight: 600; margin-bottom: 8px;">平均 |ΔPSI|</div>
          <div style="font-size: 28px; font-weight: 600; color: #7c3aed;">${avgDeltaPSI.toFixed(3)}</div>
        </div>
      </div>
      
      <div style="margin-bottom: 24px; padding: 16px; background: var(--bg); border-radius: var(--radius);">
        <div style="font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px;">事件类型分布</div>
        <div style="font-size: 14px; line-height: 1.6;">${eventTypeSummary}</div>
      </div>
      
      <div style="margin-bottom: 24px;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 16px; color: var(--text);">剪接事件详情</div>
        ${eventsHtml}
      </div>
      
      ${evidence ? `
      <div>
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 16px; color: var(--text);">文献证据</div>
        <div style="padding: 20px; background: var(--bg); border-radius: var(--radius); font-size: 14px; line-height: 1.8;">
          ${evidence}
        </div>
      </div>
      ` : ''}
    </div>
  `;
}
async function generateReport(format) {
  if (!state.currentProject) { 
    AppNotify.toast('请先选择一个项目', 'warning'); 
    return; 
  }
  
  const output = document.getElementById('report-output');
  output.innerHTML = `
    <div style="padding: 40px; text-align: center;">
      <div style="width: 48px; height: 48px; border: 4px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
      <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">正在生成报告...</div>
      <div style="font-size: 13px; color: var(--text-secondary);">这可能需要几分钟时间，请耐心等待</div>
    </div>
  `;
  
  try {
    const reportUrl = `/api/report/${encodeURIComponent(state.currentProject)}?format=${format}`;
    const response = await fetch(reportUrl, { method: 'GET' });
    
    if (!response.ok) {
      throw new Error(`报告生成失败 (${response.status})`);
    }
    
    // Get blob and create download link
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.currentProject}_report.${format === 'html' ? 'html' : 'pdf'}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    output.innerHTML = `
      <div style="padding: 24px; background: var(--gray-100); border-radius: var(--radius); border-left: 1px solid var(--gray-900);">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
          <div style="font-size: 20px;"></div>
          <div>
            <div style="font-size: 16px; font-weight: 600; color: var(--secondary);">报告生成成功！</div>
            <div style="font-size: 13px; color: var(--text-secondary);">文件已自动下载</div>
          </div>
        </div>
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(5, 150, 105, 0.2);">
          <button class="btn btn-sm btn-primary" onclick="window.open('${reportUrl}', '_blank')">在新窗口中查看</button>
        </div>
      </div>
    `;
  } catch (error) { 
    console.error('Report generation error:', error);
    output.innerHTML = `
      <div style="padding: 24px; background: var(--gray-100); border-radius: var(--radius); border-left: 1px solid var(--gray-900);">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
          <div style="font-size: 20px;"></div>
          <div>
            <div style="font-size: 16px; font-weight: 600; color: var(--danger);">报告生成失败</div>
            <div style="font-size: 13px; color: var(--text-secondary);">${error.message}</div>
          </div>
        </div>
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(220, 38, 38, 0.2);">
          <button class="btn btn-sm btn-secondary" onclick="generateReport('${format}')">重试</button>
        </div>
      </div>
    `; 
  }
}
// 中文备注：切换全局当前选中项目并联动刷新各工作区视图。
function selectProject(projectId) {
  state.currentProject = projectId;
  state.detail = null;
  const hint = document.getElementById('detail-bundle-hint');
  if (hint) hint.textContent = '';
  localStorage.setItem('epitoperank.currentProject', projectId);
  loadDashboard();
  clearSelectedEvents();
  if (state.currentPage === 'neoantigen') { checkNeoReadiness(); }
}
// 中文备注：重新拉取当前项目的最新状态、图表与事件数据。
function refreshData() { if (state.currentPage === 'dashboard') loadDashboard(); if (state.currentPage === 'pipeline') loadPipeline(); if (state.currentPage === 'explorer') loadExplorer(); }

document.addEventListener('keydown', event => {
  const modal = document.getElementById('upload-modal');
  if (event.key === 'Escape') { toggleNavigation(false); if (modal.style.display === 'flex') closeUploadModal(); }
  if (event.key !== 'Tab' || modal.style.display !== 'flex') return;
  const controls = Array.from(modal.querySelectorAll('button,input,select,textarea,[tabindex="0"]')).filter(el => !el.disabled && el.getClientRects().length);
  const first = controls[0], last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) { last.focus(); event.preventDefault(); }
  if (!event.shiftKey && document.activeElement === last) { first.focus(); event.preventDefault(); }
});
// Upload Modal Functions
let selectedFiles = [];
let uploadReturnFocus = null;

// 中文备注：打开“新建分析 / 上传数据”模态弹窗并重置上传区状态。
function showUploadModal() {
  uploadReturnFocus = document.activeElement;
  document.body.style.overflow = 'hidden';
  document.getElementById('upload-modal').style.display = 'flex';
  selectedFiles = [];
  updateFileList();
  document.getElementById('project-name').focus();
}

// 中文备注：关闭上传数据模态弹窗。
function closeUploadModal() {
  document.body.style.overflow = '';
  if (uploadReturnFocus) uploadReturnFocus.focus();
  document.getElementById('upload-modal').style.display = 'none';
  document.getElementById('project-name').value = '';
  document.getElementById('analysis-query').value = '';
  selectedFiles = [];
  updateFileList();
}

// 中文备注：处理文件拖入上传区时的悬停事件与高亮样式。
function handleDragOver(event) {
  event.preventDefault();
  event.stopPropagation();
  const dropZone = document.getElementById('drop-zone');
  dropZone.style.borderColor = 'var(--accent)';
  dropZone.style.background = 'var(--accent-soft)';
}

// 中文备注：处理文件拖离上传区时恢复默认边框样式。
function handleDragLeave(event) {
  event.preventDefault();
  event.stopPropagation();
  const dropZone = document.getElementById('drop-zone');
  dropZone.style.borderColor = 'var(--border)';
  dropZone.style.background = '';
}

// 中文备注：接收拖拽放入的文件列表并交由 handleFiles 处理。
function handleDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  const dropZone = document.getElementById('drop-zone');
  dropZone.style.borderColor = 'var(--border)';
  dropZone.style.background = '';
  
  const files = Array.from(event.dataTransfer.files);
  handleFiles(files);
}

// 中文备注：响应普通文件选择框变更并收集选中的文件。
function handleFileSelect(event) {
  console.log('handleFileSelect called');
  console.log('event.target:', event.target);
  console.log('event.target.files:', event.target.files);
  
  const files = Array.from(event.target.files);
  console.log('Converted files array:', files.length, files);
  
  handleFiles(files);
}

// 中文备注：响应整个报告目录选择框变更并收集目录内文件。
function handleReportDirectory(event) {
  const files = Array.from(event.target.files).filter(file => /.+[.](SE|MXE|A3SS|A5SS|RI)[.]xls$/i.test(file.name));
  if (!files.length) {
    AppNotify.toast('目录中没有找到华大逐样本剪接表（如 OC_001.SE.xls）', 'error');
    return;
  }
  handleFiles(files);
}

// 中文备注：校验并合并用户新选入的待上传文件列表，更新界面展示。
function handleFiles(files) {
  console.log('handleFiles called with', files.length, 'files');
  selectedFiles = [...selectedFiles, ...files];
  console.log('selectedFiles now:', selectedFiles.length, selectedFiles.map(f => f.name));
  updateFileList();
}

// 中文备注：重新渲染上传弹窗中的已选文件清单与移除按钮。
function updateFileList() {
  const fileListDiv = document.getElementById('file-list');
  const startBtn = document.getElementById('start-analysis-btn');
  
  if (selectedFiles.length === 0) {
    fileListDiv.innerHTML = '';
    startBtn.disabled = true;
  } else {
    fileListDiv.innerHTML = (selectedFiles.length > 30 ? '<div style="margin-bottom:8px">已选择 ' + selectedFiles.length + ' 个文件（仅显示前 30 个）</div>' : '') + selectedFiles.slice(0, 30).map((file, index) => 
      `<div style="padding: 8px; background: var(--bg); border-radius: var(--radius); margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 13px;">${file.name}</span>
        <button onclick="removeFile(${index})" style="background: none; border: none; cursor: pointer; color: var(--danger); font-size: 16px;">×</button>
      </div>`
    ).join('');
    startBtn.disabled = false;
  }
}

// 中文备注：从待上传文件队列中移除指定索引的文件。
function removeFile(index) {
  selectedFiles.splice(index, 1);
  updateFileList();
}

// 中文备注：上传文件并触发数据接入预览或启动完整剪接分析流水线。
async function startAnalysis() {
  const projectName = document.getElementById('project-name').value.trim();
  const analysisQuery = document.getElementById('analysis-query').value.trim() ||
    (selectedFiles.some(file => /.+[.](SE|MXE|A3SS|A5SS|RI)[.]xls$/i.test(file.name)) ? 'Explore per-sample PSI' : '');
  
  if (!projectName) {
    AppNotify.toast('请输入项目名称', 'warning');
    return;
  }
  
  if (!analysisQuery) {
    AppNotify.toast('请输入分析查询', 'warning');
    return;
  }
  
  if (selectedFiles.length === 0) {
    AppNotify.toast('请至少选择一个文件', 'warning');
    return;
  }
  
  // Save files reference BEFORE closing modal (closeUploadModal clears selectedFiles)
  const filesToUpload = [...selectedFiles];
  
  // Close modal and show loading
  closeUploadModal();
  const statusDiv = document.getElementById('stat-status');
  statusDiv.innerHTML = '<span class="status status-running"><span class="status-dot"></span>上传中...</span>';
  
  try {
    // Step 1: Upload files
    const formData = new FormData();
    
    console.log('Uploading files count:', filesToUpload.length);
    console.log('Files to upload:', filesToUpload.map(f => f.name));
    
    filesToUpload.forEach((file, index) => {
      console.log(`Adding file ${index}:`, file.name, file.type, file.size);
      formData.append('files', file, file.name);
    });
    
    // Verify FormData contents
    for (let [key, value] of formData.entries()) {
      console.log('FormData entry:', key, value.name, value.size);
    }
    
    const uploadResponse = await fetch('/api/upload', {
      method: 'POST',
      body: formData
      // Don't set Content-Type header - browser will set it with boundary
    });
    
    console.log('Upload response status:', uploadResponse.status);
    
    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      console.error('Upload error response:', errorText);
      throw new Error(`上传失败 (${uploadResponse.status}): ${errorText}`);
    }
    
    const uploadResult = await uploadResponse.json();
    const uploadDir = uploadResult.upload_dir;
    
    console.log('Files uploaded to:', uploadDir);
    
    // Step 2: let the ingestion agent read the table structure before analysis.
    statusDiv.innerHTML = '<span class="status status-running"><span class="status-dot"></span>智能体正在理解数据结构...</span>';
    let preview = null;
    try {
      const previewResponse = await fetch('/api/ingest/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_dir: uploadDir, use_llm: true })
      });
      if (previewResponse.ok) {
        preview = await previewResponse.json();
      } else {
        console.warn('ingest preview rejected:', previewResponse.status, await previewResponse.text());
      }
    } catch (previewError) {
      console.warn('ingest preview unavailable:', previewError);
    }

    if (preview && preview.native && (!preview.validation || preview.validation.ok) && !(preview.sample_ids || []).length) {
      statusDiv.innerHTML = '<span class="status status-running"><span class="status-dot"></span>已识别标准格式，开始分析...</span>';
      runAnalysisOnDir(analysisQuery, uploadDir, projectName, statusDiv);
      return;
    }
    if (preview) {
      statusDiv.dataset.ingestPending = '1';
      statusDiv.innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>等待确认数据映射...</span>';
      showIngestModal(preview, { uploadDir: uploadDir, projectName: projectName, analysisQuery: analysisQuery, statusDiv: statusDiv });
      return;
    }
    runAnalysisOnDir(analysisQuery, uploadDir, projectName, statusDiv);

  } catch (error) {
    console.error('Analysis error:', error);
    statusDiv.innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>空闲</span>';
    AppNotify.dialog({
      kind: 'error',
      title: '上传没有完成',
      message: '文件或数据目录在上传阶段中断，分析尚未启动。',
      detail: String(error && error.message ? error.message : error),
      bullets: ['确认文件格式为 CSV、TSV、TXT 或表格型 XLS', '单个文件不要过大，必要时先拆分', '检查网络与本地服务是否可用']
    });
  }
}

function runAnalysisOnDir(analysisQuery, inputDir, projectName, statusDiv) {
  const prevLatest = (state.projects && state.projects[0] && state.projects[0].project_id) || null;
  statusDiv.innerHTML = '<span class="status status-running"><span class="status-dot"></span>分析中（预计 3-6 分钟）...</span>';
  navigateTo('pipeline');

  const pollTimer = setInterval(async () => {
    try {
      const resp = await apiCall('/projects');
      const list = (resp && resp.projects) || [];
      if (list.length > 0 && list[0].project_id !== prevLatest && state.currentProject !== list[0].project_id) {
        state.currentProject = list[0].project_id;
        localStorage.setItem('epitoperank.currentProject', state.currentProject);
        document.getElementById('current-project').textContent = state.currentProject;
      }
      if (state.currentProject) loadPipeline();
    } catch (pollError) { console.warn('poll error:', pollError); }
  }, 4000);

  fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: analysisQuery, input_dir: inputDir, project_name: projectName })
  }).then(async analyzeResponse => {
    clearInterval(pollTimer);
    if (!analyzeResponse.ok) {
      const errorText = await analyzeResponse.text();
      statusDiv.innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>空闲</span>';
      AppNotify.dialog({
        kind: 'error',
        title: '分析未能完成',
        message: '服务返回了错误，本次分析已中止。修正输入后可以重新发起。',
        detail: 'HTTP ' + analyzeResponse.status + '\\n' + String(errorText || '').slice(0, 800)
      });
      return;
    }
    const analyzeResult = await analyzeResponse.json();
    if (analyzeResult && analyzeResult.project_id) {
      state.currentProject = analyzeResult.project_id;
      localStorage.setItem('epitoperank.currentProject', state.currentProject);
      document.getElementById('current-project').textContent = state.currentProject;
    }
    statusDiv.innerHTML = '<span class="status status-completed"><span class="status-dot"></span>已完成</span>';
    loadPipeline();
    loadDashboard();
    AppNotify.dialog({
      kind: 'success',
      title: '分析完成',
      subtitle: '结果已写入当前项目',
      message: '事件表已解析，显著性筛选与候选排序都已完成。接下来可以逐条查看事件，或直接生成研究报告。',
      actions: [
        { label: '生成研究报告', value: 'report', onClick: function () { navigateTo('report'); } },
        { label: '查看可视化', value: 'visualization', onClick: function () { navigateTo('visualization'); } },
        { label: '浏览事件', variant: 'primary', value: 'explorer', onClick: function () { navigateTo('explorer'); } }
      ]
    });
  }).catch(fetchError => {
    clearInterval(pollTimer);
    console.error('Analysis request error:', fetchError);
    statusDiv.innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>空闲</span>';
    AppNotify.dialog({
      kind: 'warning',
      title: '连接已中断',
      message: '前端没能拿到分析响应，但后台任务可能仍在运行。稍后点击右上角「刷新」即可看到最新进度。',
      detail: String(fetchError && fetchError.message ? fetchError.message : fetchError)
    });
  });
}

// ---------------------------------------------------------------------------
// Smart ingestion review
// ---------------------------------------------------------------------------
let ingestState = null;

const INGEST_STEP_LABELS = {
  profile: ['文件画像', 'Profiling'],
  heuristic: ['规则映射', 'Rule mapping'],
  llm: ['模型映射', 'LLM mapping'],
  validate: ['标准化', 'Standardization'],
  preview: ['置信度', 'Confidence']
};

function ingestT(zh, en) { return cfgText(zh, en); }

// 中文备注：对数据接入预览弹窗中的文本进行 HTML 转义。
function ingestEsc(value) {
  return String(value === null || value === undefined ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function ingestLevel(level) {
  if (level === 'high') return ingestT('高', 'high');
  if (level === 'medium') return ingestT('中', 'medium');
  return ingestT('低', 'low');
}

function ingestDelimiter(value) {
  if (value === String.fromCharCode(9)) return 'TAB';
  if (value === ',') return 'CSV';
  return value || '—';
}

// 中文备注：将数值安全格式化为固定小数位字符串，空值返回占位符。
function ingestFixed(value, digits) {
  const num = Number(value);
  if (value === null || value === undefined || value === '' || !isFinite(num)) return '—';
  return num.toFixed(digits);
}

// 中文备注：将数值安全格式化为科学计数法字符串，供数据接入预览使用。
function ingestSci(value) {
  const num = Number(value);
  if (value === null || value === undefined || value === '' || !isFinite(num)) return '—';
  if (num === 0) return '0';
  return fmtSci(num, 2);
}

// 中文备注：将数据格式识别与转换步骤轨迹渲染为列表项。
function ingestTraceSteps(trace) {
  const order = [];
  const byName = {};
  (trace || []).forEach(function (step) {
    if (!step || !step.step) return;
    if (!byName[step.step]) order.push(step.step);
    byName[step.step] = step;
  });
  return order.map(function (name) { return byName[name]; });
}

// 中文备注：打开数据接入与样本分组确认弹窗并载入后端预览结果。
function showIngestModal(data, context) {
  ingestState = {
    data: data,
    context: context,
    mapping: JSON.parse(JSON.stringify(data.mapping || {})),
    applying: false,
    groupLabels: []
  };
  if (!ingestState.mapping.columns) ingestState.mapping.columns = {};
  if (!ingestState.mapping.sample_groups) ingestState.mapping.sample_groups = {};
  const suggested = [...new Set(Object.values(ingestState.mapping.sample_groups).filter(Boolean))];
  ingestState.groupLabels = [suggested[0] || 'Control', suggested[1] || 'Treatment'];
  const modal = document.getElementById('ingest-modal');
  if (modal) modal.classList.add('open');
  document.body.style.overflow = 'hidden';
  renderIngestModal();
  const confirmBtn = document.getElementById('ingest-confirm');
  if (confirmBtn && !confirmBtn.disabled) confirmBtn.focus();
}

// 中文备注：关闭数据接入与样本分组确认弹窗。
function closeIngestModal() {
  if (ingestState && ingestState.applying) return;
  const statusDiv = ingestState && ingestState.context ? ingestState.context.statusDiv : null;
  const modal = document.getElementById('ingest-modal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = '';
  if (statusDiv && statusDiv.dataset.ingestPending === '1') {
    delete statusDiv.dataset.ingestPending;
    statusDiv.innerHTML = '<span class="status status-waiting"><span class="status-dot"></span>空闲</span>';
  }
  ingestState = null;
}

// 中文备注：渲染数据接入预览中的识别格式、样本分组映射表与校验警告。
function renderIngestModal() {
  if (!ingestState) return;
  const data = ingestState.data || {};
  const preview = data.preview || {};
  const issues = data.issues || [];
  const native = !!data.native;
  const bgi = data.status === 'bgi_single_sample';
  const unmappable = data.status === 'unmappable';
  const expressionOnly = data.detected_format === 'expression_quantification' || data.detected_format === 'transcript_quantification';

  const title = document.getElementById('ingest-title');
  const sub = document.getElementById('ingest-sub');
  const body = document.getElementById('ingest-body');
  const confirmBtn = document.getElementById('ingest-confirm');
  const cancelBtn = document.getElementById('ingest-cancel');
  const errorDiv = document.getElementById('ingest-error');
  if (!body || !confirmBtn) return;

  let subText = ingestT('Agent 已读取数据结构。确认字段映射后，将标准化并进入原有分析流程。', 'The agent has read the data structure. Confirm the field mapping to standardize and continue to analysis.');
  if (native) subText = ingestT('请核对每个样本的分组，确认后开始分析。', 'Review each sample group before analysis.');
  if (bgi) subText = ingestT('已识别华大逐样本剪接表。确认真实分组后可生成探索性 PSI 表；原报告没有组间显著性检验。', 'BGI per-sample PSI tables found. Confirm biological groups to create an exploratory table; the report has no differential significance test.');
  if (unmappable) subText = ingestT('未能从这些文件中识别出可分析的剪接事件表。', 'No analyzable splicing event table could be recognized in these files.');
  if (expressionOnly) subText = ingestT('文件已读取并识别为表达量矩阵。请另选剪接事件结果表进行剪接分析。', 'File read as an expression matrix. Select splicing event results for splicing analysis.');
  if (title) title.textContent = ingestT('智能接入检查', 'Smart ingestion review');
  if (sub) sub.textContent = subText;
  if (errorDiv) errorDiv.textContent = '';

  const html = [];
  const steps = ingestTraceSteps(data.agent_trace);
  if (steps.length) {
    html.push('<div class="ingest-trace">' + steps.map(function (step) {
      const labels = INGEST_STEP_LABELS[step.step] || [step.step, step.step];
      const detail = ingestT(step.detail || '', step.detail_en || step.detail || '');
      return '<span class="ingest-step ' + ingestEsc(step.status || 'ok') + '" title="' + ingestEsc(detail) + '"><span class="dot"></span>' + ingestEsc(ingestT(labels[0], labels[1])) + '</span>';
    }).join('') + '</div>');
  }

  const sourceBits = [];
  if (native) {
    sourceBits.push(ingestT('原生格式：', 'Native format: ') + ingestEsc(data.native_format || 'standard'));
  } else {
    sourceBits.push(ingestT('映射来源：', 'Mapping source: ') + (data.mapping_source === 'llm+heuristic' ? ingestT('大模型 + 规则', 'LLM + rules') : ingestT('确定性规则', 'Deterministic rules')));
    const confidence = data.confidence || {};
    sourceBits.push(ingestT('置信度：', 'Confidence: ') + ingestLevel(confidence.level) + ' · ' + Math.round(Number(confidence.score || 0) * 100) + '%');
  }
  if (data.elapsed_ms !== undefined && data.elapsed_ms !== null) sourceBits.push(ingestT('用时 ', 'took ') + Number(data.elapsed_ms) + ' ms');
  html.push('<div class="ingest-source">' + sourceBits.join(' · ') + '</div>');

  const validEvents = preview.valid_events !== undefined ? preview.valid_events : ((data.summary && data.summary.event_count) || 0);
  const sampleCount = preview.sample_count !== undefined ? preview.sample_count : ((data.summary && data.summary.sample_count) || 0);
  const fdrCoverage = preview.fdr_coverage !== undefined ? preview.fdr_coverage : 0;
  const deltaCoverage = preview.delta_coverage !== undefined ? preview.delta_coverage : 0;
  html.push('<div class="ingest-stats">' +
    '<div class="ingest-stat"><div class="v">' + ingestEsc(validEvents) + '</div><div class="k">' + ingestEsc(ingestT('有效事件', 'Valid events')) + '</div></div>' +
    '<div class="ingest-stat"><div class="v">' + ingestEsc(sampleCount) + '</div><div class="k">' + ingestEsc(ingestT('样本', 'Samples')) + '</div></div>' +
    '<div class="ingest-stat"><div class="v">' + Math.round(Number(fdrCoverage) * 100) + '%</div><div class="k">' + ingestEsc(ingestT('FDR 覆盖', 'FDR coverage')) + '</div></div>' +
    '<div class="ingest-stat"><div class="v">' + Math.round(Number(deltaCoverage) * 100) + '%</div><div class="k">' + ingestEsc(ingestT('ΔPSI 覆盖', 'ΔPSI coverage')) + '</div></div>' +
    '</div>');

  if (!native && data.event_file) {
    const eventFile = data.event_file;
    const metaFile = data.metadata_file;
    const rows = Number(eventFile.row_count || 0);
    const line = ingestT('事件表', 'Event table') + ' <code>' + ingestEsc(eventFile.name) + '</code> · ' + ingestDelimiter(eventFile.delimiter) + ' · ' + ingestT('表头第 ', 'header row ') + (Number(eventFile.header_row || 0) + 1) + ' · ' + rows + ingestT(' 行', ' rows');
    const metaLine = ingestT('样本表', 'Sample table') + ' <code>' + ingestEsc(metaFile ? metaFile.name : '—') + '</code>' + (metaFile ? '' : ' ' + ingestT('（未提供，已根据样本名推断分组）', '(not provided; groups inferred from sample names)'));
    const typeCounts = preview.event_types || {};
    const typeText = Object.keys(typeCounts).map(function (key) { return key + ' ' + typeCounts[key]; }).join(' · ');
    html.push('<div class="ingest-files"><div>' + line + '</div><div>' + metaLine + '</div>' + (typeText ? '<div>' + ingestEsc(ingestT('事件类型：', 'Event types: ') + typeText) + '</div>' : '') + '</div>');
  }

  if (unmappable && Array.isArray(data.files) && data.files.length) {
    const fileLines = data.files.map(function (file) {
      const suffix = file.supported ? ingestT('可解析', 'parseable') : ingestT('不可解析', 'not parseable');
      return '<div><code>' + ingestEsc(file.name) + '</code> · ' + suffix + (file.error ? ' · ' + ingestEsc(file.error) : '') + '</div>';
    });
    html.push('<div class="ingest-files">' + fileLines.join('') + '</div>');
  }

  if (!native && Array.isArray(data.mapping_fields) && data.mapping_fields.length && data.event_file) {
    const headers = data.event_file.headers || [];
    const columns = (data.mapping && data.mapping.columns) || {};
    const rows = data.mapping_fields.map(function (field) {
      const current = columns[field.field] || '';
      const label = ingestT(field.label_zh || field.field, field.label_en || field.field) + (field.required ? ' *' : '');
      let options = '<option value="">' + ingestEsc(ingestT('— 未映射 —', '— unmapped —')) + '</option>';
      let found = false;
      headers.forEach(function (header) {
        if (header === current) found = true;
        options += '<option value="' + ingestEsc(header) + '"' + (header === current ? ' selected' : '') + '>' + ingestEsc(header) + '</option>';
      });
      if (current && !found) options += '<option value="' + ingestEsc(current) + '" selected>' + ingestEsc(current) + '</option>';
      const missing = field.required && !current ? ' missing' : '';
      return '<div class="ingest-map-row"><label>' + ingestEsc(label) + '</label><select data-field="' + ingestEsc(field.field) + '"' + (field.required ? ' data-required="1"' : '') + ' onchange="ingestSelectChanged(this)"' + (missing ? ' class="missing"' : '') + '>' + options + '</select></div>';
    });
    html.push('<div><div class="ingest-section-title">' + ingestEsc(ingestT('字段映射', 'Field mapping')) + '</div><div class="ingest-map-grid">' + rows.join('') + '</div></div>');
  }

  const sampleIds = data.sample_ids || [];
  if (sampleIds.length) {
    const labels = ingestState.groupLabels;
    const assignments = ingestState.mapping.sample_groups;
    const assignedCount = sampleIds.filter(id => !!assignments[id]).length;
    const source = data.group_suggestion_source;
    const sourceText = source === 'previous_metadata'
      ? ingestT('已从相同事件文件的历史样本表恢复分组建议。', 'Group suggestions were restored from a previous sample sheet for the identical event file.')
      : source === 'metadata'
        ? ingestT('已读取上传的样本表。', 'Groups were read from the uploaded sample sheet.')
        : source === 'llm' || data.mapping_source === 'llm+heuristic'
          ? ingestT('大模型已提出分组建议，请核对。', 'The model suggested sample groups; please review them.')
          : ingestT('尚无可靠的完整分组建议，可修改分组名称并批量分配。', 'No complete reliable grouping was found; you can edit group names and assign samples in batches.');
    html.push('<div><div class="ingest-section-title">' + ingestEsc(ingestT('样本分组确认', 'Confirm sample groups')) + '</div>' +
      '<div style="margin:8px 0;color:var(--text-secondary)">' + ingestEsc(sourceText) + ' ' + assignedCount + '/' + sampleIds.length + '</div>' +
      '<div style="display:flex;gap:8px;margin:8px 0"><input data-group-label="0" value="' + ingestEsc(labels[0]) + '" oninput="ingestGroupLabelChanged(this)" aria-label="Group 1" placeholder="Group 1" style="width:48%;padding:8px"><input data-group-label="1" value="' + ingestEsc(labels[1]) + '" oninput="ingestGroupLabelChanged(this)" aria-label="Group 2" placeholder="Group 2" style="width:48%;padding:8px"></div>' +
      '<div style="display:flex;gap:8px;margin:8px 0"><button type="button" class="btn btn-sm btn-secondary" onclick="ingestAssignUnassigned(0)">' + ingestEsc(ingestT('未分配项 → 第一组', 'Unassigned → group 1')) + '</button><button type="button" class="btn btn-sm btn-secondary" onclick="ingestAssignUnassigned(1)">' + ingestEsc(ingestT('未分配项 → 第二组', 'Unassigned → group 2')) + '</button></div>' +
      '<details' + (assignedCount < sampleIds.length ? ' open' : '') + '><summary style="cursor:pointer;margin:8px 0">' + ingestEsc(ingestT('查看或调整逐样本分组', 'Review or edit individual samples')) + '</summary><div class="ingest-map-grid">' + sampleIds.map(function (sampleId) {
        const current = assignments[sampleId] || '';
        return '<div class="ingest-map-row"><label>' + ingestEsc(sampleId) + '</label><select data-sample-id="' + ingestEsc(sampleId) + '" onchange="ingestGroupChanged(this)"><option value="">' + ingestEsc(ingestT('— 请选择 —', '— Select —')) + '</option><option value="0"' + (current === labels[0] ? ' selected' : '') + '>' + ingestEsc(labels[0]) + '</option><option value="1"' + (current === labels[1] ? ' selected' : '') + '>' + ingestEsc(labels[1]) + '</option></select></div>';
      }).join('') + '</div></details></div>');
  } else {
    html.push('<div class="ingest-issue warning">' + ingestEsc(expressionOnly
      ? ingestT('FPKM、TPM 和 read_count 是表达量，不是剪接事件 PSI；请上传 SE/MXE/A3SS/A5SS/RI 事件表。', 'FPKM, TPM and read counts are expression values, not event PSI. Upload SE/MXE/A3SS/A5SS/RI event tables.')
      : ingestT('没有每样本 PSI 数据，无法生成真实的样本箱线图或热图。', 'No per-sample PSI data: sample box plots and heatmaps cannot be generated.')) + '</div>');
  }

  if (issues.length) {
    const items = issues.map(function (issue) {
      const severity = issue.severity === 'error' ? 'error' : (issue.severity === 'warning' ? 'warning' : 'info');
      const tag = severity === 'error' ? ingestT('错误', 'ERROR') : (severity === 'warning' ? ingestT('提示', 'WARN') : ingestT('信息', 'INFO'));
      const message = ingestT(issue.message || '', issue.message_en || issue.message || '');
      return '<div class="ingest-issue ' + severity + '"><span class="tag">' + ingestEsc(tag) + '</span><span>' + ingestEsc(message) + '</span></div>';
    });
    html.push('<div><div class="ingest-section-title">' + ingestEsc(ingestT('检查结果', 'Checks')) + '</div><div class="ingest-issues">' + items.join('') + '</div></div>');
  }

  const sampleEvents = preview.events || [];
  if (sampleEvents.length) {
    const head = ingestT('事件 ID', 'Event ID') + '</th><th>' + ingestT('基因', 'Gene') + '</th><th>' + ingestT('类型', 'Type') + '</th><th>ΔPSI</th><th class="num">FDR</th><th>' + ingestT('坐标', 'Coordinates');
    const rows = sampleEvents.map(function (event) {
      return '<tr><td>' + ingestEsc(event.event_id) + '</td><td>' + ingestEsc(event.gene) + '</td><td>' + ingestEsc(event.event_type) + '</td><td>' + ingestFixed(event.delta_psi, 3) + '</td><td>' + ingestSci(event.fdr) + '</td><td>' + ingestEsc(event.coordinates) + '</td></tr>';
    }).join('');
    html.push('<div><div class="ingest-section-title">' + ingestEsc(ingestT('标准化预览（前 5 行）', 'Standardized preview (first 5 rows)')) + '</div><div class="ingest-preview-table"><table><thead><tr><th>' + head + '</th></tr></thead><tbody>' + rows + '</tbody></table></div></div>');
  }

  const privacy = ingestT(data.privacy || '', data.privacy_en || data.privacy || '');
  if (privacy && !native) html.push('<div class="ingest-privacy">' + ingestEsc(privacy) + '</div>');

  body.innerHTML = html.join('');

  if (cancelBtn) cancelBtn.textContent = ingestT('取消', 'Cancel');
  if (!ingestState.applying) {
    if (unmappable || (native && data.validation && !data.validation.ok)) {
      confirmBtn.disabled = true;
      confirmBtn.textContent = unmappable
        ? ingestT('无法自动标准化', 'Cannot standardize')
        : ingestT('数据校验未通过', 'Validation failed');
    } else {
      updateIngestConfirmState();
    }
  }
}

// 中文备注：处理接入预览中主事件文件或分组列下拉选择变更。
function ingestSelectChanged(select) {
  if (!ingestState) return;
  if (!ingestState.mapping.columns) ingestState.mapping.columns = {};
  const field = select.getAttribute('data-field');
  if (!field) return;
  if (select.value) ingestState.mapping.columns[field] = select.value;
  else delete ingestState.mapping.columns[field];
  if (select.getAttribute('data-required') === '1') select.classList.toggle('missing', !select.value);
  updateIngestConfirmState();
}

// 中文备注：处理单个样本所属实验分组下拉框变更并刷新确认按钮状态。
function ingestGroupChanged(select) {
  if (!ingestState) return;
  const sampleId = select.getAttribute('data-sample-id');
  ingestState.mapping.sample_groups[sampleId] = select.value === '' ? '' : ingestState.groupLabels[Number(select.value)];
  updateIngestConfirmState();
}

// 中文备注：将所有未分配分组的样本一键归入指定的分组槽位。
function ingestAssignUnassigned(index) {
  if (!ingestState) return;
  const label = ingestState.groupLabels[index];
  (ingestState.data.sample_ids || []).forEach(function (id) {
    if (!ingestState.mapping.sample_groups[id]) ingestState.mapping.sample_groups[id] = label;
  });
  renderIngestModal();
}

// 中文备注：同步用户自定义的实验组/对照组显示名称。
function ingestGroupLabelChanged(input) {
  if (!ingestState) return;
  const index = Number(input.getAttribute('data-group-label'));
  const oldLabel = ingestState.groupLabels[index];
  const newLabel = input.value.trim();
  ingestState.groupLabels[index] = newLabel;
  Object.keys(ingestState.mapping.sample_groups).forEach(function (id) {
    if (ingestState.mapping.sample_groups[id] === oldLabel) ingestState.mapping.sample_groups[id] = newLabel;
  });
  document.querySelectorAll('#ingest-body select[data-sample-id]').forEach(function (select) {
    select.options[index + 1].textContent = newLabel;
  });
  updateIngestConfirmState();
}

// 中文备注：检查样本分组是否满足最低要求并更新“确认并开始分析”按钮状态。
function updateIngestConfirmState() {
  if (!ingestState) return;
  const data = ingestState.data || {};
  if (data.status === 'unmappable') return;
  const confirmBtn = document.getElementById('ingest-confirm');
  if (!confirmBtn || ingestState.applying) return;
  const columns = {};
  document.querySelectorAll('#ingest-body select[data-field]').forEach(function (select) {
    if (select.value) columns[select.getAttribute('data-field')] = select.value;
  });
  const preview = data.preview || {};
  const validation = preview.validation || data.validation || {};
  const sampleIds = data.sample_ids || [];
  const groupLabels = ingestState.groupLabels || [];
  const groupsReady = !sampleIds.length || (groupLabels[0] && groupLabels[1] && groupLabels[0] !== groupLabels[1] && sampleIds.every(id => groupLabels.includes(ingestState.mapping.sample_groups[id])) && new Set(sampleIds.map(id => ingestState.mapping.sample_groups[id])).size === 2);
  const missingGene = !columns.gene_symbol && !columns.gene_id;
  const hasDelta = !!columns.delta_PSI || (!!columns.mean_PSI_group1 && !!columns.mean_PSI_group2) || Number(preview.sample_psi_columns || 0) > 0;
  const hasSignificance = !!columns.FDR || !!columns.p_value;
  const ready = groupsReady && (data.native ? Number(validation.error_count || 0) === 0 : (data.status === 'bgi_single_sample' ? true : (!missingGene && hasDelta && hasSignificance)));
  confirmBtn.disabled = !ready;
  confirmBtn.textContent = ready ? (data.status === 'bgi_single_sample' ? ingestT('确认分组并生成探索性表', 'Create exploratory table') : ingestT('确认映射并分析', 'Confirm & analyze')) : ingestT('请先补全映射', 'Complete the mapping');
}

async function confirmIngest() {
  if (!ingestState || ingestState.applying) return;
  const data = ingestState.data || {};
  const ctx = ingestState.context || {};
  const errorDiv = document.getElementById('ingest-error');
  const confirmBtn = document.getElementById('ingest-confirm');
  if (errorDiv) errorDiv.textContent = '';

  if (data.status === 'bgi_single_sample') {
    ingestState.applying = true;
    if (confirmBtn) confirmBtn.disabled = true;
    try {
      const response = await fetch('/api/ingest/apply', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({input_dir:ctx.uploadDir, mapping:{adapter:'bgi_single_sample',sample_groups:ingestState.mapping.sample_groups}})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'HTTP ' + response.status);
      closeIngestModal();
      const statusDiv = ctx.statusDiv || document.getElementById('stat-status');
      if (statusDiv) statusDiv.textContent = ingestT('探索性事件表已生成：', 'Exploratory event table created: ') + result.path + ingestT('。原报告没有组间 p 值或 FDR，不会报告显著差异。', '. No differential p-values or FDR were available.');
    } catch (error) {
      if (errorDiv) errorDiv.textContent = error.message;
    } finally {
      ingestState.applying = false;
      updateIngestConfirmState();
    }
    return;
  }

  if (data.native) {
    const sampleIds = data.sample_ids || [];
    const groups = ingestState.mapping.sample_groups || {};
    if (sampleIds.length && (sampleIds.some(id => !groups[id]) || new Set(sampleIds.map(id => groups[id])).size !== 2)) {
      if (errorDiv) errorDiv.textContent = ingestT('请为每个样本选择分组，并确保两组都有样本。', 'Assign every sample and include both groups.');
      return;
    }
    if (!sampleIds.length) { closeIngestModal(); runAnalysisOnDir(ctx.analysisQuery, ctx.uploadDir, ctx.projectName, ctx.statusDiv); return; }
    ingestState.applying = true;
    if (confirmBtn) confirmBtn.disabled = true;
    try {
      const response = await fetch('/api/ingest/groups', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({input_dir:ctx.uploadDir,sample_groups:groups})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'HTTP ' + response.status);
      ingestState.applying = false;
      closeIngestModal();
      runAnalysisOnDir(ctx.analysisQuery, result.path, ctx.projectName, ctx.statusDiv);
    } catch (error) {
      ingestState.applying = false;
      if (errorDiv) errorDiv.textContent = error.message;
      updateIngestConfirmState();
    }
    return;
  }

  const columns = {};
  const selects = document.querySelectorAll('#ingest-body select[data-field]');
  for (let i = 0; i < selects.length; i++) {
    const field = selects[i].getAttribute('data-field');
    if (field && selects[i].value) columns[field] = selects[i].value;
  }
  const mappedFields = {};
  (data.mapping_fields || []).forEach(function (field) { mappedFields[field.field] = true; });
  const originalColumns = (data.mapping && data.mapping.columns) || {};
  Object.keys(originalColumns).forEach(function (key) {
    if (!mappedFields[key]) columns[key] = originalColumns[key];
  });

  if (!columns.gene_symbol && !columns.gene_id) {
    if (errorDiv) errorDiv.textContent = ingestT('请至少映射基因符号或基因 ID。', 'Map at least a gene symbol or gene ID column.');
    return;
  }
  const preview = data.preview || {};
  const hasDelta = !!columns.delta_PSI || (!!columns.mean_PSI_group1 && !!columns.mean_PSI_group2) || Number(preview.sample_psi_columns || 0) > 0;
  if (!hasDelta) {
    if (errorDiv) errorDiv.textContent = ingestT('请映射 ΔPSI，或同时映射两组平均 PSI。', 'Map delta PSI, or both group mean PSI columns.');
    return;
  }
  if (!columns.FDR && !columns.p_value) {
    if (errorDiv) errorDiv.textContent = ingestT('请映射 FDR 或 p 值，否则无法筛选显著事件。', 'Map an FDR or p-value column so significant events can be selected.');
    return;
  }

  const mapping = JSON.parse(JSON.stringify(data.mapping || {}));
  mapping.columns = columns;
  mapping.sample_groups = ingestState.mapping.sample_groups;
  mapping.sample_groups_confirmed = (data.sample_ids || []).length > 0;
  if (data.event_file && data.event_file.name) mapping.event_file = data.event_file.name;

  ingestState.applying = true;
  if (confirmBtn) { confirmBtn.disabled = true; confirmBtn.textContent = ingestT('标准化中…', 'Standardizing…'); }
  try {
    const response = await fetch('/api/ingest/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_dir: ctx.uploadDir, mapping: mapping })
    });
    let result = {};
    try { result = await response.json(); } catch (parseError) { result = {}; }
    if (!response.ok) {
      const detail = result && result.detail;
      const message = typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : 'HTTP ' + response.status);
      throw new Error(message);
    }
    const statusDiv = ctx.statusDiv || document.getElementById('stat-status');
    ingestState.applying = false;
    closeIngestModal();
    statusDiv.innerHTML = '<span class="status status-running"><span class="status-dot"></span>标准化完成，开始分析...</span>';
    runAnalysisOnDir(ctx.analysisQuery, result.path, ctx.projectName, statusDiv);
  } catch (error) {
    ingestState.applying = false;
    if (errorDiv) errorDiv.textContent = ingestT('标准化失败：', 'Standardization failed: ') + error.message;
    if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.textContent = ingestT('确认映射并分析', 'Confirm & analyze'); }
  }
}

document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape' && ingestState) closeIngestModal();
});

document.addEventListener('epitoperank:language', function () {
  if (ingestState) renderIngestModal();
});

function viewEventDetails(eventId) { 
  const event = state.events.find(e => (e.event_id || e.id) === eventId);
  if (!event) { AppNotify.toast('事件未找到', 'warning'); return; }
  
  const gene = event.gene_symbol || event.gene || 'Unknown';
  const eventType = event.event_type || event.type || 'Unknown';
  const dpsi = event.delta_psi !== null && event.delta_psi !== undefined ? Number(event.delta_psi).toFixed(4) : 'N/A';
  const fdr = event.fdr !== null && event.fdr !== undefined ? fmtFdr(event.fdr) : 'N/A';
  const pValue = event.p_value !== null && event.p_value !== undefined ? fmtSci(event.p_value, 3) : 'N/A';
  const score = event.score !== null && event.score !== undefined ? Number(event.score).toFixed(3) : 'N/A';
  
  // Determine significance level
  let sigLevel = 'ns';
  let sigColor = '#94a3b8';
  if (fdr !== 'N/A') {
    const fdrNum = parseFloat(String(fdr).replace('<', ''));
    if (fdrNum < 0.001) { sigLevel = '***'; sigColor = '#dc2626'; }
    else if (fdrNum < 0.01) { sigLevel = '**'; sigColor = '#f59e0b'; }
    else if (fdrNum < 0.05) { sigLevel = '*'; sigColor = '#059669'; }
  }
  
  // Biological interpretation based on delta PSI
  let biologicalImpact = '';
  let impactColor = '';
  const dpsiAbs = Math.abs(parseFloat(dpsi));
  if (dpsi !== 'N/A') {
    if (dpsiAbs > 0.3) { biologicalImpact = '强效应 - 可能导致蛋白质功能重大改变'; impactColor = '#dc2626'; }
    else if (dpsiAbs > 0.15) { biologicalImpact = '中等效应 - 可能影响蛋白质结构域'; impactColor = '#f59e0b'; }
    else if (dpsiAbs > 0.05) { biologicalImpact = '弱效应 - 可能对功能有轻微影响'; impactColor = '#059669'; }
    else { biologicalImpact = '微小效应 - 可能无显著生物学影响'; impactColor = '#94a3b8'; }
  }
  
  // Event type descriptions
  const eventDescriptions = {
    'SE': '外显子跳跃 (Skipped Exon): 最常见的外显子类型，可能导致蛋白质结构域缺失',
    'MXE': '互斥外显子 (Mutually Exclusive Exons): 两个相邻外显子中只保留一个',
    'A3SS': "可变3'剪接位点 (Alternative 3' Splice Site): 影响外显子3'端边界",
    'A5SS': "可变5'剪接位点 (Alternative 5' Splice Site): 影响外显子5'端边界",
    'RI': '内含子保留 (Retained Intron): 内含子未被正确移除'
  };
  
  const eventDesc = eventDescriptions[eventType] || '未知剪接事件类型';
  
  // Create modal HTML
  const modalHTML = `
    <div id="event-detail-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--white); z-index: 2000; display: flex; align-items: center; justify-content: center;">
      <div style="background: var(--white); border: 1px solid var(--gray-300); border-radius: var(--radius); padding: 0; max-width: 900px; width: 95%; max-height: 90vh; overflow-y: auto;">
        <!-- Header -->
        <div style="background: var(--black); padding: 32px; color: white; position: relative;">
          <button onclick="closeEventModal()" style="position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2); border: none; width: 36px; height: 36px; border-radius: 50%; color: white; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">×</button>
          <div style="font-size: 28px; font-weight: 600; margin-bottom: 8px;">${gene}</div>
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: var(--radius); font-size: 13px; font-weight: 400;">${eventType}</span>
            <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: var(--radius); font-size: 13px; font-weight: 400;">FDR ${ingestEsc(fdr)} ${sigLevel}</span>
          </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px;">
          <!-- Key Metrics -->
          <div class="grid grid-3" style="margin-bottom: 28px;">
            <div style="background: var(--gray-100); border: 1px solid var(--gray-300); padding: 20px; border-radius: var(--radius); text-align: center;">
              <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); font-weight: 600; margin-bottom: 8px;">Delta PSI</div>
              <div style="font-size: 28px; font-weight: 600; color: var(--black);">${dpsi}</div>
            </div>
            <div style="background: var(--gray-100); border: 1px solid var(--gray-300); padding: 20px; border-radius: var(--radius); text-align: center;">
              <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); font-weight: 600; margin-bottom: 8px;">FDR</div>
              <div style="font-size: 28px; font-weight: 600; color: var(--black);">${ingestEsc(fdr)}</div>
            </div>
            <div style="background: var(--gray-100); border: 1px solid var(--gray-300); padding: 20px; border-radius: var(--radius); text-align: center;">
              <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); font-weight: 600; margin-bottom: 8px;">评分</div>
              <div style="font-size: 28px; font-weight: 600; color: var(--black);">${score}</div>
            </div>
          </div>
          
          <!-- Biological Impact -->
          <div style="background: var(--gray-100); border-left: 1px solid var(--gray-700); padding: 20px; border-radius: var(--radius); margin-bottom: 24px;">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-900); margin-bottom: 8px;">生物学影响评估</div>
            <div style="font-size: 14px; line-height: 1.7; color: var(--gray-900);">${biologicalImpact}</div>
          </div>
          
          <!-- Event Description -->
          <div style="margin-bottom: 24px;">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); margin-bottom: 12px;">事件类型说明</div>
            <div style="font-size: 14px; line-height: 1.7; color: var(--gray-900); padding: 16px; background: var(--gray-100); border: 1px solid var(--gray-300); border-radius: var(--radius);">${eventDesc}</div>
          </div>
          
          <!-- Statistical Details -->
          <div style="margin-bottom: 24px;">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); margin-bottom: 12px;">统计详情</div>
            <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
              <tr style="border-bottom: 1px solid var(--gray-300);">
                <td style="padding: 12px 16px; font-weight: 600; color: var(--gray-700); width: 40%;">P值</td>
                <td style="padding: 12px 16px; font-family: var(--font-mono); font-size: 14px; color: var(--gray-900);">${ingestEsc(pValue)}</td>
              </tr>
              <tr style="border-bottom: 1px solid var(--gray-300);">
                <td style="padding: 12px 16px; font-weight: 600; color: var(--gray-700);">Delta PSI</td>
                <td style="padding: 12px 16px; font-family: var(--font-mono); font-size: 14px; color: var(--gray-900);">${dpsi}</td>
              </tr>
              <tr style="border-bottom: 1px solid var(--gray-300);">
                <td style="padding: 12px 16px; font-weight: 600; color: var(--gray-700);">FDR校正值</td>
                <td style="padding: 12px 16px; font-family: var(--font-mono); font-size: 14px; color: var(--gray-900);">${ingestEsc(fdr)}</td>
              </tr>
              <tr>
                <td style="padding: 12px 16px; font-weight: 600; color: var(--gray-700);">综合评分</td>
                <td style="padding: 12px 16px; font-family: var(--font-mono); font-size: 14px; color: var(--gray-900);">${score}</td>
              </tr>
            </table>
          </div>
          
          <!-- Literature Evidence -->
          ${event.evidence_json ? `
          <div style="margin-bottom: 24px;">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--gray-700); margin-bottom: 12px;">文献证据</div>
            <div style="padding: 20px; background: var(--gray-100); border: 1px solid var(--gray-300); border-radius: var(--radius); font-size: 14px; line-height: 1.7; color: var(--gray-900);" id="evidence-content">加载中...</div>
          </div>
          ` : '<div style="padding: 20px; background: var(--gray-100); border: 1px solid var(--gray-300); border-radius: var(--radius); font-size: 14px; color: var(--gray-500); text-align: center; margin-bottom: 24px;">暂无文献证据</div>'}
          
          <!-- Action Buttons -->
          <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 28px; padding-top: 24px; border-top: 1px solid var(--border);">
            <button class="btn btn-secondary" onclick="closeEventModal()">关闭</button>
            <button class="btn btn-primary" onclick="viewGeneInBrowser('${gene}')">查看基因详情</button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Load evidence if available
  if (event.evidence_json) {
    setTimeout(() => {
      try {
        const evidence = typeof event.evidence_json === 'string' ? JSON.parse(event.evidence_json) : event.evidence_json;
        const evidenceDiv = document.getElementById('evidence-content');
        if (Array.isArray(evidence)) {
          evidenceDiv.innerHTML = evidence.map(item => `<div style="margin-bottom: 8px;">• ${item}</div>`).join('');
        } else if (typeof evidence === 'object') {
          evidenceDiv.innerHTML = Object.entries(evidence).map(([k, v]) => `<div style="margin-bottom: 8px;"><strong>${k}:</strong> ${v}</div>`).join('');
        } else {
          evidenceDiv.textContent = evidence;
        }
      } catch (e) {
        document.getElementById('evidence-content').textContent = event.evidence_json;
      }
    }, 100);
  }
}

// 中文备注：关闭剪接事件详情模态弹窗。
function closeEventModal() {
  const modal = document.getElementById('event-detail-modal');
  if (modal) {
    modal.style.animation = 'fadeOut 0.3s';
    setTimeout(() => modal.remove(), 300);
  }
}

// 中文备注：从事件详情跳转到基因探索页面并自动查询该基因。
function viewGeneInBrowser(geneSymbol) {
  closeEventModal();
  navigateTo('gene');
  document.getElementById('gene-search').value = geneSymbol;
  exploreGene();
}

// ==================== MCP Tool Console ====================
const mcpState = { servers: {}, configPath: '', selectedServer: '', tools: [], loading: false };

// 中文备注：生成 MCP 服务器连接状态徽章 HTML。
function mcpStatusBadge(text, kind) {
  const badge = document.getElementById('mcp-status');
  if (!badge) return;
  badge.textContent = text;
  badge.className = 'mcp-badge' + (kind ? ' ' + kind : '');
}

// 中文备注：拉取已配置的内置及外部 MCP 服务器清单与可用工具列表。
async function loadMcpServers(force) {
  if (mcpState.loading) return;
  mcpState.loading = true;
  mcpStatusBadge('连接中…', '');
  document.getElementById('mcp-server-hint').textContent = '正在连接 MCP 服务器…';
  try {
    const response = await fetch('/api/mcp/servers' + (force ? '?refresh=1' : ''));
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    mcpState.servers = data.servers || {};
    mcpState.configPath = data.config_path || '';
    renderMcpServers();
  } catch (error) {
    mcpStatusBadge('连接失败', 'err');
    document.getElementById('mcp-server-hint').textContent = String(error);
    document.getElementById('mcp-server-select').innerHTML = '<option value="">无法读取 MCP 配置</option>';
    document.getElementById('mcp-tool-select').innerHTML = '<option value="">—</option>';
  } finally {
    mcpState.loading = false;
  }
}

// 中文备注：渲染 MCP 面板中的服务器列表、连接状态与工具下拉选项。
function renderMcpServers() {
  const select = document.getElementById('mcp-server-select');
  const names = Object.keys(mcpState.servers);
  const connected = names.filter(function (name) { return mcpState.servers[name].status === 'connected'; });
  if (!names.length) {
    mcpStatusBadge('未配置', 'err');
    select.innerHTML = '<option value="">未配置 MCP 服务器</option>';
    document.getElementById('mcp-server-hint').textContent = '在 ' + (mcpState.configPath || '~/.epitoperank/mcp/servers.json') + ' 中添加服务器';
    return;
  }
  const previous = mcpState.selectedServer;
  select.innerHTML = '';
  names.forEach(function (name) {
    const server = mcpState.servers[name];
    const option = document.createElement('option');
    const toolCount = (server.tools || []).length;
    const tag = server.builtin ? '内置' : (server.via || server.transport || 'MCP');
    option.value = name;
    option.textContent = name + ' · ' + tag + ' · ' + toolCount + ' 工具' + (server.status === 'connected' ? '' : '（未连接）');
    option.disabled = server.status !== 'connected';
    select.appendChild(option);
  });
  const preferred = (connected.indexOf(previous) >= 0 ? previous : connected[0]) || '';
  select.value = preferred;
  mcpState.selectedServer = preferred;
  if (connected.length) {
    mcpStatusBadge(connected.length + ' / ' + names.length + ' 已连接', 'ok');
  } else {
    mcpStatusBadge('未连接', 'err');
  }
  onMcpServerChange();
}

// 中文备注：切换选中的 MCP 服务器时更新其对应的工具列表。
function onMcpServerChange() {
  const name = document.getElementById('mcp-server-select').value;
  mcpState.selectedServer = name;
  const server = mcpState.servers[name];
  const toolSelect = document.getElementById('mcp-tool-select');
  const hint = document.getElementById('mcp-server-hint');
  if (!server || server.status !== 'connected') {
    toolSelect.innerHTML = '<option value="">无可用工具</option>';
    hint.textContent = server ? ('状态：' + server.status + (server.error ? ' · ' + server.error : '')) : '';
    onMcpToolChange();
    return;
  }
  mcpState.tools = server.tools || [];
  toolSelect.innerHTML = '';
  mcpState.tools.forEach(function (tool) {
    const option = document.createElement('option');
    option.value = tool.name;
    option.textContent = tool.name;
    toolSelect.appendChild(option);
  });
  const parts = ['连接方式：' + (server.via || server.transport || 'MCP')];
  if (server.url) parts.push(server.url);
  hint.textContent = parts.join(' · ');
  onMcpToolChange();
}

// 中文备注：切换选中的 MCP 工具时自动填充参数 JSON 示例模板。
function onMcpToolChange() {
  const toolName = document.getElementById('mcp-tool-select').value;
  const tool = mcpState.tools.find(function (item) { return item.name === toolName; });
  const desc = document.getElementById('mcp-tool-desc');
  const args = document.getElementById('mcp-args');
  if (!tool) {
    desc.textContent = '选择服务器与工具后调用';
    args.value = '{}';
    return;
  }
  desc.textContent = tool.description || '（无描述）';
  args.value = JSON.stringify(buildMcpExample(tool), null, 2);
}

// 中文备注：根据 MCP 工具的输入 Schema 生成可编辑的 JSON 示例参数。
function buildMcpExample(tool) {
  const schema = tool.input_schema || {};
  const properties = schema.properties || {};
  const example = {};
  Object.keys(properties).forEach(function (key) {
    const spec = properties[key] || {};
    if (spec.default !== undefined) {
      example[key] = spec.default;
    } else if (key === 'project_id' && state.currentProject) {
      example[key] = state.currentProject;
    } else if (spec.type === 'integer' || spec.type === 'number') {
      example[key] = spec.minimum !== undefined ? spec.minimum : 0;
    } else if (spec.type === 'boolean') {
      example[key] = false;
    } else if (spec.enum && spec.enum.length) {
      example[key] = spec.enum[0];
    } else {
      example[key] = '';
    }
  });
  return example;
}

// 中文备注：从 MCP 工具返回结构中提取可读的文本或 JSON 载荷。
function extractMcpPayload(result) {
  if (result === null || result === undefined) return result;
  if (typeof result !== 'object') return result;
  const structured = result.structuredContent !== undefined ? result.structuredContent : result.structured_content;
  if (structured !== undefined) {
    if (structured && typeof structured === 'object' && !Array.isArray(structured) && Object.keys(structured).length === 1 && typeof structured.result === 'string') {
      try { return JSON.parse(structured.result); } catch (error) { return structured.result; }
    }
    return structured;
  }
  if (Array.isArray(result.content)) {
    const texts = result.content.filter(function (item) {
      return item && item.type === 'text';
    }).map(function (item) { return item.text; });
    const text = texts.join(String.fromCharCode(10));
    if (text) {
      try { return JSON.parse(text); } catch (error) { return text; }
    }
  }
  return result;
}

// 中文备注：向后端 /api/mcp/call 发送选定工具与参数并展示执行结果。
async function callMcpTool() {
  const serverName = document.getElementById('mcp-server-select').value;
  const toolName = document.getElementById('mcp-tool-select').value;
  const resultEl = document.getElementById('mcp-result');
  const statusEl = document.getElementById('mcp-call-status');
  const button = document.getElementById('mcp-call-btn');
  if (!serverName || !toolName) {
    statusEl.textContent = '请选择可用的服务器与工具';
    return;
  }
  let args = {};
  const raw = document.getElementById('mcp-args').value.trim();
  if (raw) {
    try {
      args = JSON.parse(raw);
    } catch (error) {
      resultEl.className = 'mcp-result err';
      resultEl.textContent = '参数不是合法 JSON：' + error.message;
      return;
    }
  }
  if (!args || typeof args !== 'object' || Array.isArray(args)) {
    resultEl.className = 'mcp-result err';
    resultEl.textContent = '参数必须是 JSON 对象，例如 {"project_id": "SPN-XXXX"}';
    return;
  }
  button.disabled = true;
  statusEl.textContent = '调用中…';
  resultEl.className = 'mcp-result';
  resultEl.textContent = '正在通过 MCP 调用 ' + serverName + ' / ' + toolName + ' …';
  const started = performance.now();
  try {
    const response = await fetch('/api/mcp/call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ server_name: serverName, tool_name: toolName, arguments: args })
    });
    const data = await response.json();
    const elapsed = Math.round(performance.now() - started);
    if (!response.ok || !data.success) {
      const message = data.error || (data.detail ? JSON.stringify(data.detail) : ('HTTP ' + response.status));
      resultEl.className = 'mcp-result err';
      resultEl.textContent = '调用失败：' + message;
      statusEl.textContent = elapsed + ' ms · 失败';
      return;
    }
    const payload = extractMcpPayload(data.result);
    resultEl.className = 'mcp-result';
    resultEl.textContent = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
    statusEl.textContent = elapsed + ' ms · ' + serverName + ' / ' + toolName;
  } catch (error) {
    resultEl.className = 'mcp-result err';
    resultEl.textContent = '调用异常：' + error.message;
    statusEl.textContent = '失败';
  } finally {
    button.disabled = false;
  }
}

// 中文备注：提交外部 MCP 服务器配置到后端并刷新服务器连接列表。
async function addExternalMcpServer() {
  const status = document.getElementById('mcp-ext-status');
  const name = document.getElementById('mcp-ext-name').value.trim();
  const url = document.getElementById('mcp-ext-url').value.trim();
  if (!name || !url) { status.textContent = '请填写服务器名称与 URL。'; return; }
  status.textContent = '正在注册并连接…';
  try {
    const response = await fetch('/api/mcp/servers', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name: name, url: url, transport: 'http', protocol: 'auto'})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '连接失败');
    status.textContent = '状态：' + data.status + ' · 可用工具 ' + (data.tools || []).length + ' 个 · 配置：' + data.config_path;
    await loadMcpServers(true);
    document.getElementById('mcp-server-select').value = data.name;
    onMcpServerChange();
  } catch (error) { status.textContent = String(error.message || error); }
}
// 中文备注：调用后端 /api/mcp/agent 执行自然语言驱动的 MCP 智能体对话。
async function runMcpAgent() {
  const question = document.getElementById('mcp-agent-question').value.trim();
  const statusEl = document.getElementById('mcp-agent-status');
  const resultEl = document.getElementById('mcp-result');
  const button = document.getElementById('mcp-agent-btn');
  if (!question) {
    statusEl.textContent = '请输入自然语言指令';
    return;
  }
  button.disabled = true;
  statusEl.textContent = '模型正在选择工具…';
  resultEl.className = 'mcp-result';
  resultEl.textContent = 'Agent 正在规划 MCP 工具调用…';
  const started = performance.now();
  try {
    const response = await fetch('/api/mcp/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question, project_id: state.currentProject || '' })
    });
    const data = await response.json();
    const elapsed = Math.round(performance.now() - started);
    if (!response.ok) {
      resultEl.className = 'mcp-result err';
      resultEl.textContent = 'Agent 调用失败：' + (data.detail || ('HTTP ' + response.status));
      statusEl.textContent = elapsed + ' ms · 失败';
      return;
    }
    const plan = data.plan || {};
    const axis = data.source === 'llm' ? 'LLM 规划' : '规则回退';
    const header = [
      'Agent 规划（' + axis + '）：' + (plan.server || '?') + ' / ' + (plan.tool || '?'),
      plan.reason ? '理由：' + plan.reason : '',
      '─'.repeat(34)
    ].filter(Boolean).join(String.fromCharCode(10));
    const payload = extractMcpPayload(data.result);
    const body = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
    resultEl.className = data.success ? 'mcp-result' : 'mcp-result err';
    resultEl.textContent = header + String.fromCharCode(10) + (data.success ? body : ('调用失败：' + (data.error || body)));
    statusEl.textContent = elapsed + ' ms · ' + axis + ' · ' + (data.success ? '成功' : '失败');
    if (plan.server && mcpState.servers[plan.server]) {
      document.getElementById('mcp-server-select').value = plan.server;
      onMcpServerChange();
      if (plan.tool) {
        document.getElementById('mcp-tool-select').value = plan.tool;
        onMcpToolChange();
        document.getElementById('mcp-args').value = JSON.stringify(plan.arguments || {}, null, 2);
      }
    }
    if (data.llm_errors && data.llm_errors.length) {
      statusEl.textContent += ' · 模型回退';
    }
  } catch (error) {
    resultEl.className = 'mcp-result err';
    resultEl.textContent = 'Agent 调用异常：' + error.message;
    statusEl.textContent = '失败';
  } finally {
    button.disabled = false;
  }
}

// 中文备注：根据当前界面语言返回对应的中文或英文配置提示文案。
function cfgText(zh, en) {
  var i18n = window.__epitoperankI18n;
  return i18n && i18n.getLang && i18n.getLang() === 'en' ? en : zh;
}

// 中文备注：从后端加载当前大模型（LLM）配置状态并回填设置表单。
async function loadModelConfig(force) {
  const base = document.getElementById('cfg-base');
  if (!base) return;
  try {
    const response = await fetch('/api/llm/status');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    const values = (data.config && data.config.values) || {};
    if (force || !base.dataset.loaded) {
      base.value = values.MODEL_API_BASE_URL || '';
      document.getElementById('cfg-model').value = values.MODEL_NAME || '';
      const key = document.getElementById('cfg-key');
      key.value = '';
      key.placeholder = values.MODEL_API_KEY
        ? cfgText('当前密钥 ' + values.MODEL_API_KEY + '，留空保持不变', 'Current key ' + values.MODEL_API_KEY + ' — leave blank to keep it')
        : cfgText('粘贴你的 API Key', 'Paste your API key');
      base.dataset.loaded = '1';
    }
    const badge = document.getElementById('cfg-status');
    const statusText = document.getElementById('cfg-status-text');
    if (data.configured && data.enabled) {
      badge.className = 'status status-completed';
      statusText.textContent = cfgText('已配置 · ' + (data.model || 'LLM'), 'Configured · ' + (data.model || 'LLM'));
    } else {
      badge.className = 'status status-waiting';
      statusText.textContent = data.enabled ? cfgText('未配置 Key', 'No API key') : cfgText('模型已关闭', 'Model disabled');
    }
    const button = document.getElementById('cfg-save');
    if (button && !button.disabled) button.textContent = cfgText('保存并启用', 'Save & enable');
  } catch (error) {
    const badge = document.getElementById('cfg-status');
    if (badge) {
      badge.className = 'status status-waiting';
      document.getElementById('cfg-status-text').textContent = cfgText('状态不可用', 'Status unavailable');
    }
    console.error('loadModelConfig', error);
  }
}

function renderEsm2Status(info) {
  const ok = !!(info && info.available);
  const pill = document.getElementById('neo-esm2-pill');
  const pillText = document.getElementById('neo-esm2-pill-text');
  if (pill && pillText) {
    pill.className = 'status ' + (ok ? 'status-completed' : 'status-waiting');
    pillText.textContent = ok
      ? ('ESM-2 在线 · ' + (info.folds || 5) + '折 6维融合')
      : (info && info.configured ? 'ESM-2 离线（点此重配）' : 'ESM-2 未配置（点此设置）');
  }
  const st = document.getElementById('esm2-cfg-status');
  const stText = document.getElementById('esm2-cfg-status-text');
  const detail = document.getElementById('esm2-cfg-detail');
  if (st && stText) {
    st.className = 'status ' + (ok ? 'status-completed' : 'status-waiting');
    stText.textContent = ok ? '在线 · 6 维融合已激活' : (info && info.configured ? '连接失败（已自动降级 5 维）' : '未配置');
  }
  if (detail && info && info.detail) {
    detail.textContent = (ok ? '当前引擎：' : '诊断信息：') + info.detail;
  }
  const urlInput = document.getElementById('esm2-cfg-url');
  if (urlInput && !urlInput.value && info && info.url) {
    urlInput.value = info.url;
  }
}

async function loadEsm2Config(force) {
  const msg = document.getElementById('esm2-cfg-msg');
  if (force && msg) { msg.className = 'cfg-msg'; msg.textContent = '正在探测连通性…'; }
  try {
    const resp = await fetch('/api/esm2/status' + (force ? '?force=1' : ''));
    const data = await resp.json();
    renderEsm2Status(data);
    if (force && msg) {
      msg.className = 'cfg-msg ' + (data.available ? 'ok' : 'err');
      msg.textContent = data.available ? '连通正常！' : '暂时无法连上该地址，请检查隧道或网络。';
    }
  } catch (err) {
    if (force && msg) { msg.className = 'cfg-msg err'; msg.textContent = '检测失败：' + err.message; }
  }
}

async function saveEsm2Config() {
  const url = (document.getElementById('esm2-cfg-url')?.value || '').trim();
  const key = (document.getElementById('esm2-cfg-key')?.value || '').trim();
  const msg = document.getElementById('esm2-cfg-msg');
  const btn = document.getElementById('esm2-cfg-save');
  if (btn) btn.disabled = true;
  if (msg) { msg.className = 'cfg-msg'; msg.textContent = '正在保存并测试连通性…'; }
  try {
    const resp = await fetch('/api/esm2/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url, api_key: key })
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || ('HTTP ' + resp.status));
    renderEsm2Status(data.status || {});
    const keyInput = document.getElementById('esm2-cfg-key');
    if (keyInput) keyInput.value = '';
    const ok = !!(data.status && data.status.available);
    if (msg) {
      msg.className = 'cfg-msg ' + (ok ? 'ok' : 'err');
      msg.textContent = ok ? '已保存到本地 .env，ESM-2 服务连通正常！' : '已保存，但暂未连上：' + ((data.status && data.status.detail) || '请检查地址');
    }
  } catch (err) {
    if (msg) { msg.className = 'cfg-msg err'; msg.textContent = '保存失败：' + err.message; }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// 中文备注：保存用户在设置页填写的大模型 API 地址、密钥与模型名配置。
async function saveModelConfig() {
  const button = document.getElementById('cfg-save');
  const message = document.getElementById('cfg-msg');
  if (!button || button.disabled) return;
  const base = document.getElementById('cfg-base').value.trim();
  const model = document.getElementById('cfg-model').value.trim();
  const key = document.getElementById('cfg-key').value.trim();
  if (!base || !model) {
    message.className = 'cfg-msg err';
    message.textContent = cfgText('请填写 Base URL 和模型名', 'Base URL and model name are required');
    return;
  }
  const values = { MODEL_API_BASE_URL: base, MODEL_NAME: model };
  if (key) values.MODEL_API_KEY = key;
  button.disabled = true;
  button.textContent = cfgText('保存中…', 'Saving…');
  message.className = 'cfg-msg';
  message.textContent = '';
  try {
    const response = await fetch('/api/llm/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || ('HTTP ' + response.status));
    message.className = 'cfg-msg ok';
    message.textContent = key
      ? cfgText('配置已保存并即时生效', 'Saved — active immediately')
      : cfgText('配置已保存（保留原 Key）', 'Saved (existing key kept)');
    document.getElementById('cfg-key').value = '';
    document.getElementById('cfg-base').dataset.loaded = '';
    await loadModelConfig(true);
  } catch (error) {
    message.className = 'cfg-msg err';
    message.textContent = cfgText('保存失败: ', 'Save failed: ') + error.message;
  } finally {
    button.disabled = false;
    button.textContent = cfgText('保存并启用', 'Save & enable');
  }
}

document.addEventListener('epitoperank:language', function () {
  if (!document.getElementById('cfg-status-text')) return;
  const message = document.getElementById('cfg-msg');
  if (message) {
    message.className = 'cfg-msg';
    message.textContent = '';
  }
  loadModelConfig(true);
});

document.addEventListener('DOMContentLoaded', () => { loadDashboard(); loadModelConfig(); setInterval(() => { if (state.currentPage === 'pipeline' && state.currentProject) { loadPipeline(); } }, 5000); });
</script>
<script>
// 统一的应用内提示层：toast（轻量、自动消失）与 dialog（需要用户确认）。
// 不再使用浏览器原生 alert/confirm —— 原生弹窗在 Chrome / WebView2 / Electron
// 里样式各不相同，无法跟随本应用的主题、语言与圆角体系。
(function () {
  "use strict";

  var ICONS = {
    success: '<path d="M4.5 12.4l4.8 4.8L19.6 6.9"/>',
    error: '<path d="M6.6 6.6l10.8 10.8M17.4 6.6L6.6 17.4"/>',
    warning: '<path d="M12 4.8v9.4"/><circle cx="12" cy="18.9" r="1.45" fill="currentColor" stroke="none"/>',
    info: '<path d="M12 10.6v8.6"/><circle cx="12" cy="6.1" r="1.45" fill="currentColor" stroke="none"/>'
  };
  var TITLES = {
    success: ["完成", "Done"],
    error: ["未完成", "Not completed"],
    warning: ["请注意", "Please check"],
    info: ["提示", "Notice"]
  };
  var CLOSE_LABEL = ["关闭", "Close"];
  var DISMISS_LABEL = ["知道了", "Got it"];
  var TOAST_LIMIT = 4;

  function currentLang() {
    var i18n = window.__epitoperankI18n;
    var value = i18n && i18n.getLang ? i18n.getLang() : "zh";
    return value === "en" || value === "zh-Hant" ? value : "zh";
  }
  // 中文备注：规范化中英双语对照词条，供前端即时翻译与提示组件使用。
  function pair(item) { return currentLang() === "en" ? item[1] : item[0]; }
  // 中文备注：按当前语言设置将界面提示文案转换为对应语言版本。
  function translate(text) {
    var i18n = window.__epitoperankI18n;
    var raw = String(text === null || text === undefined ? "" : text);
    if (currentLang() === "zh") return raw;
    if (!i18n || !i18n.translate) return raw;
    // translateOne 按整串匹配字典，多段文案需要逐段翻译。
    var parts = raw.split("\\n\\n");
    for (var i = 0; i < parts.length; i++) parts[i] = i18n.translate(parts[i]);
    return parts.join("\\n\\n");
  }
  // 中文备注：根据通知类型（成功、警告、错误、信息）返回对应的内联 SVG 图标。
  function iconSvg(kind) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      (ICONS[kind] || ICONS.info) + "</svg>";
  }
  // 中文备注：获取或懒创建页面右上角的全局 Toast 通知容器节点。
  function resolveStack() {
    var node = document.getElementById("toast-stack");
    if (!node) {
      node = document.createElement("div");
      node.id = "toast-stack";
      node.setAttribute("role", "region");
      node.setAttribute("aria-live", "polite");
      document.body.appendChild(node);
    }
    return node;
  }

  // 中文备注：以淡出动画或立即方式关闭并移除单条 Toast 通知。
  function dismissToast(node, immediate) {
    if (!node || node.getAttribute("data-leaving") === "1") return;
    node.setAttribute("data-leaving", "1");
    if (immediate) { node.remove(); return; }
    node.classList.add("leaving");
    setTimeout(function () { node.remove(); }, 220);
  }

  // 中文备注：弹出一条带自动倒计时与关闭按钮的全局 Toast 提示消息。
  function toast(message, kind, options) {
    options = options || {};
    kind = ICONS[kind] ? kind : "info";
    var stack = resolveStack();
    while (stack.children.length >= TOAST_LIMIT) dismissToast(stack.firstElementChild, true);

    var life = typeof options.duration === "number" ? options.duration : 5200;
    var node = document.createElement("div");
    node.className = "app-toast " + kind;
    node.setAttribute("role", kind === "error" ? "alert" : "status");
    node.style.setProperty("--toast-life", life + "ms");

    var head = options.title ? translate(options.title) : pair(TITLES[kind]);
    var body = translate(message);
    node.innerHTML =
      '<span class="app-toast-icon">' + iconSvg(kind) + "</span>" +
      '<div class="app-toast-body"><div class="app-toast-title"></div>' +
      (body ? '<div class="app-toast-msg"></div>' : "") + "</div>" +
      '<button type="button" class="app-toast-close" aria-label="' + pair(CLOSE_LABEL) + '">&#10005;</button>';
    node.querySelector(".app-toast-title").textContent = head;
    if (body) node.querySelector(".app-toast-msg").textContent = body;

    var timer = null;
    // 中文备注：为 Toast 通知启动或重置自动关闭定时器（支持鼠标悬停暂停）。
    function arm(ms) {
      clearTimeout(timer);
      timer = setTimeout(function () { dismissToast(node); }, ms);
    }
    node.addEventListener("mouseenter", function () {
      clearTimeout(timer);
      node.classList.add("paused");
      node.style.removeProperty("--toast-life");
    });
    node.addEventListener("mouseleave", function () {
      node.classList.remove("paused");
      arm(1600);
    });
    node.addEventListener("click", function (event) {
      if (event.target.closest(".app-toast-close")) dismissToast(node);
    });
    stack.appendChild(node);
    if (life > 0) arm(life);
    return node;
  }

  var activeActions = [];
  var activeResolve = null;
  var dismissValue = null;

  // 中文备注：获取或懒创建统一的自定义模态确认/提示对话框 DOM 节点。
  function dialogNode() {
    var node = document.getElementById("app-dialog");
    if (!node) {
      node = document.createElement("dialog");
      node.id = "app-dialog";
      node.className = "app-dialog";
      document.body.appendChild(node);
    }
    return node;
  }

  // 中文备注：关闭自定义对话框并以用户选择结果兑现对应的 Promise。
  function settle(value) {
    var node = dialogNode();
    if (node.open) {
      try { node.close(); } catch (e) {}
    }
    var resolve = activeResolve;
    activeResolve = null;
    activeActions = [];
    if (resolve) resolve(value);
  }

  // 中文备注：以 Promise 形式弹出统一的模态提示或确认对话框。
  function dialog(options) {
    options = options || {};
    var kind = ICONS[options.kind] ? options.kind : "info";
    var node = dialogNode();
    if (node.open) settle(null);

    activeActions = options.actions && options.actions.length ? options.actions.slice() : [{
      label: pair(DISMISS_LABEL), variant: "primary", value: true
    }];
    dismissValue = "dismissValue" in options ? options.dismissValue : (activeActions.length === 1 ? activeActions[0].value : null);

    node.className = "app-dialog " + kind;
    var html =
      '<div class="app-dialog-head">' +
        '<div class="app-dialog-mark">' + iconSvg(kind) + "</div>" +
        '<div class="app-dialog-titles">' +
          '<div class="app-dialog-title" id="app-dialog-title"></div>' +
          (options.subtitle ? '<div class="app-dialog-sub"></div>' : "") +
        "</div>" +
        '<button type="button" class="app-dialog-close" aria-label="' + pair(CLOSE_LABEL) + '">&#10005;</button>' +
      "</div>" +
      '<div class="app-dialog-body"></div>' +
      '<div class="app-dialog-foot"></div>';
    node.innerHTML = html;
    node.querySelector(".app-dialog-title").textContent = translate(options.title || pair(TITLES[kind]));
    if (options.subtitle) node.querySelector(".app-dialog-sub").textContent = translate(options.subtitle);

    var body = node.querySelector(".app-dialog-body");
    body.textContent = translate(options.message || "");
    if (options.detail) {
      var detail = document.createElement("div");
      detail.className = "app-dialog-detail";
      detail.textContent = translate(options.detail);
      body.appendChild(detail);
    }
    if (options.bullets && options.bullets.length) {
      var list = document.createElement("ul");
      list.className = "app-dialog-list";
      options.bullets.forEach(function (item) {
        var li = document.createElement("li");
        li.textContent = translate(item);
        list.appendChild(li);
      });
      body.appendChild(list);
    }

    var foot = node.querySelector(".app-dialog-foot");
    activeActions.forEach(function (action, index) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "btn " + (action.variant === "primary" ? "btn-primary"
        : action.variant === "danger" ? "btn-danger" : "btn-secondary");
      button.setAttribute("data-app-action", String(index));
      button.textContent = translate(action.label || "");
      foot.appendChild(button);
    });
    foot.lastElementChild && foot.lastElementChild.focus({ preventScroll: true });

    node.onclick = function (event) {
      var button = event.target.closest("[data-app-action]");
      if (button) {
        var action = activeActions[Number(button.getAttribute("data-app-action"))];
        var value = action && "value" in action ? action.value : true;
        settle(value);
        if (action && typeof action.onClick === "function") setTimeout(action.onClick, 0);
        return;
      }
      if (event.target.closest(".app-dialog-close")) settle(dismissValue);
    };
    node.oncancel = function (event) {
      event.preventDefault();
      settle(dismissValue);
    };

    return new Promise(function (resolve) {
      var opener = document.activeElement;
      activeResolve = function (value) {
        // 关闭后把焦点还给触发元素，避免键盘用户丢失位置。
        if (opener && opener.isConnected && typeof opener.focus === "function") {
          try { opener.focus({ preventScroll: true }); } catch (e) {}
        }
        resolve(value);
      };
      node.showModal();
    });
  }

  // 中文备注：弹出异步确认弹窗并在用户点击确认或取消后返回布尔结果。
  function confirmAsync(message, options) {
    options = options || {};
    return dialog({
      kind: options.kind || "warning",
      title: options.title,
      message: message,
      actions: [
        { label: options.cancelLabel || pair(["取消", "Cancel"]), value: false },
        { label: options.confirmLabel || pair(["继续", "Continue"]),
          variant: options.danger ? "danger" : "primary", value: true }
      ],
      dismissValue: false
    }).then(function (value) { return value === true; });
  }

  window.AppNotify = {
    toast: toast,
    dialog: dialog,
    confirm: confirmAsync,
    translate: translate,
    clear: function () {
      var stack = document.getElementById("toast-stack");
      if (stack) Array.prototype.slice.call(stack.children).forEach(function (node) { dismissToast(node, true); });
    }
  };
})();
</script>

<script>
(function () {
  "use strict";
  // 繁简转换依赖 opencc-cn2t.js（约 1.1MB，占整个前端静态资源的大头）。
  // 绝大多数用户从不切到繁體，所以这里不再在首屏同步加载，而是等真正需要
  // 转换时才注入 <script>；加载完成后若当前语言仍是 zh-Hant，会自动重放一次
  // applyLanguage，把已经渲染出来的文字补上转换结果。
  var traditionalConverter = null;
  var converterLoad = null;
  var converterFailed = false;

  function ensureTraditionalConverter() {
    if (converterLoad || converterFailed) return converterLoad;
    // 资源拿不到时不能静默：用户点了繁體却看到简体，必须说明原因。
    function reportFailure() {
      if (lang === "zh-Hant") {
        AppNotify.toast("繁體中文轉換資源載入失敗，已保持簡體顯示。請檢查網路後重新整理。", "error");
      }
    }
    converterLoad = new Promise(function (resolve) {
      var script = document.createElement("script");
      script.src = "/assets/opencc-cn2t.js";
      script.async = true;
      script.onload = function () {
        try {
          traditionalConverter = window.OpenCC.Converter({ from: "cn", to: "t" });
        } catch (e) {
          converterFailed = true;
          reportFailure();
        }
        resolve(traditionalConverter);
        // 加载期间页面可能已经切成繁體：重新套用一次即可补齐。
        if (traditionalConverter && lang === "zh-Hant") applyLanguage("zh-Hant");
      };
      script.onerror = function () {
        converterFailed = true;
        reportFailure();
        resolve(null);
      };
      document.head.appendChild(script);
    });
    return converterLoad;
  }

  // 转换器未就绪时原样返回，避免为了一个未完成的下载阻塞整页渲染；命中缓存直接返回。
  var tradCache = Object.create(null);
  function toTraditional(text) {
    if (!text) return text;
    if (traditionalConverter) {
      var cached = tradCache[text];
      if (cached !== undefined) return cached;
      var converted = traditionalConverter(text);
      tradCache[text] = converted;
      return converted;
    }
    ensureTraditionalConverter();
    return text;
  }
  var DICT = {
    "仪表盘": "Dashboard",
    "AI 流水线": "AI Pipeline",
    "事件浏览器": "Event Explorer",
    "可视化": "Visualization",
    "基因浏览器": "Gene Browser",
    "报告": "Report",
    "设置": "Settings",
    "主菜单": "Main Menu",
    "分析工具": "Analysis Tools",
    "智能助手": "Assistant",
    "刷新": "Refresh",
    "+ 新建分析": "+ New Analysis",
    "未加载项目": "No project loaded",
    "AI 智能分析平台": "AI Analysis Platform",
    "EpitopeRank - AI 智能分析平台": "EpitopeRank - AI Analysis Platform",
    "从剪接事件，到可复现的生物学证据。": "From splicing events to reproducible biological evidence.",
    "让 Agent 整理数据、追踪分析状态，并把每一个结论连接到可验证的结果。": "Let agents organize data, track analysis status, and connect every conclusion to verifiable results.",
    "总样本数": "Total Samples",
    "RNA-seq 样本": "RNA-seq samples",
    "剪接事件": "Splicing Events",
    "检测到的事件总数": "Total detected events",
    "显著事件": "Significant Events",
    "系统状态": "System Status",
    "空闲": "Idle",
    "分析中": "Running",
    "当前运行 Agent": "Current Running Agent",
    "暂无运行中的分析": "No analysis running",
    "启动新分析": "Start New Analysis",
    "最近项目": "Recent Projects",
    "暂无项目": "No projects",
    "分析进度": "Analysis Progress",
    "等待启动...": "Waiting to start...",
    "Agent 工作流": "Agent Workflow",
    "加载并验证输入数据，检查文件格式和完整性": "Load and validate input data, checking file format and integrity",
    "执行质量控制检查，过滤低质量样本": "Run quality-control checks and filter low-quality samples",
    "使用统计模型检测可变剪接事件": "Detect alternative splicing events with statistical models",
    "计算显著性（FDR）和效应量（Delta PSI）": "Compute significance (FDR) and effect size (Delta PSI)",
    "功能注释、通路富集和文献证据收集": "Functional annotation, pathway enrichment, and literature evidence collection",
    "生成生物学解读和专业分析报告": "Generate biological interpretation and a professional analysis report",
    "等待中": "Waiting",
    "运行中": "Running",
    "已完成": "Completed",
    "数据加载": "Data Loading",
    "质量控制": "Quality Control",
    "剪接检测": "Splicing Detection",
    "统计分析": "Statistical Analysis",
    "功能注释": "Functional Annotation",
    "生物学解读": "Biological Interpretation",
    "未加载事件数据": "No event data loaded",
    "等待分析结果": "Waiting for analysis results",
    "请完成分析后查看结果": "Complete an analysis to view results",
    "准备生成报告": "Ready to generate report",
    "事件 ID": "Event ID",
    "类型": "Type",
    "基因": "Gene",
    "评分": "Score",
    "操作": "Actions",
    "详情": "Details",
    "事件类型": "Event Type",
    "查看": "View",
    "筛选条件": "Filters",
    "统计阈值": "Statistical Thresholds",
    "搜索基因名称、事件ID或染色体位置...": "Search gene name, event ID, or chromosome position...",
    "选择图表类型": "Select chart type",
    "左侧共 13 张专业科研图，点击即可渲染": "13 publication-ready figures on the left; click to render",
    "差异剪接的显著性与效应量": "Significance and effect size of differential splicing",
    "ΔPSI vs -log10(FDR)，标注显著性阈值": "ΔPSI vs -log10(FDR) with significance thresholds",
    "Top 25 效应量排序，区分包含上调/下调": "Top 25 by effect size, separating inclusion up/down",
    "SE/MXE/A5SS/A3SS/RI 五类事件计数": "Counts of the five event classes: SE/MXE/A5SS/A3SS/RI",
    "五类可变剪接的外显子-内含子结构模式图": "Exon-intron schematic of the five alternative splicing classes",
    "分组占比与批次分布（QC 必备）": "Group proportions and batch distribution (essential for QC)",
    "效应量经验累积分布与阈值占比": "Empirical effect-size CDF and threshold proportions",
    "候选排名 vs -log10(FDR)，定位显著性拐点": "Candidate rank vs -log10(FDR) to locate the significance elbow",
    "各类型中显著与非显著事件构成": "Significant vs non-significant events within each class",
    "剪接事件类型构成与分子机制": "Splicing event composition and molecular mechanisms",
    "Top 事件逐样本 PSI 聚类热图": "Per-sample PSI clustering heatmap for top events",
    "各组 PSI 分布与离群样本检测": "PSI distribution by group and outlier detection",
    "队列构成与样本水平 PSI 模式": "Cohort composition and sample-level PSI patterns",
    "综合评分 Top 15 候选事件条形图": "Bar chart of the top 15 candidates by composite score",
    "显著性/效应/生物学/文献四维贡献": "Four-dimensional contribution: significance / effect / biology / literature",
    "GO/KEGG 富集倍数 vs FDR 气泡图": "GO/KEGG enrichment fold vs FDR bubble plot",
    "智能体候选评分与通路注释": "Agent-based candidate scoring and pathway annotation",
    "SE (外显子跳跃)": "SE (skipped exon)",
    "MXE (互斥外显子)": "MXE (mutually exclusive exons)",
    "A5SS (可变5'剪接)": "A5SS (alternative 5' splice site)",
    "A3SS (可变3'剪接)": "A3SS (alternative 3' splice site)",
    "RI (内含子保留)": "RI (intron retention)",
    "基因注释": "Gene Annotation",
    "文献搜索": "Literature Search",
    "通路富集": "Pathway Enrichment",
    "剪接解读": "Splice Interpretation",
    "支持基因注释、文献搜索、通路富集和剪接事件解读等专业技能": "Professional skills including gene annotation, literature search, pathway enrichment, and splice event interpretation",
    "模型配置": "Model configuration",
    "检查中…": "Checking…",
    "模型名": "Model",
    "留空则保持当前密钥": "Leave blank to keep the current key",
    "保存并启用": "Save & enable",
    "保存中…": "Saving…",
    "密钥仅保存在本机 .env / 配置大模型.env，不会写入报告或日志；保存后即时生效。": "The key is stored only in the local .env / 配置大模型.env file; it is never written to reports or logs and applies immediately.",
    "未配置 Key": "No API key",
    "模型已关闭": "Model disabled",
    "状态不可用": "Status unavailable",
    "请填写 Base URL 和模型名": "Base URL and model name are required",
    "配置已保存并即时生效": "Saved — active immediately",
    "配置已保存（保留原 Key）": "Saved (existing key kept)",
    "选择左侧的技能按钮执行专业分析": "Choose a skill on the left to run a professional analysis",
    "请选择上方的技能按钮开始，或直接输入你的问题。": "Choose a skill above to start, or type your question.",
    "• 项目概览与样本统计": "• Project overview and sample statistics",
    "• 显著剪接事件列表（FDR": "• Significant splicing event list (FDR",
    "• 显著剪接事件列表（FDR < 0.05）": "• Significant splicing event list (FDR < 0.05)",
    "• 关键基因的功能注释与通路富集": "• Functional annotation and pathway enrichment for key genes",
    "• 可视化图表（火山图、热图、分布图）": "• Visualizations (volcano, heatmap, distribution)",
    "• AI 生成的生物学解读与建议": "• AI-generated biological interpretation and recommendations",
    "• 搜索相关科学文献": "• Search relevant scientific literature",
    "• 执行通路富集分析": "• Run pathway enrichment analysis",
    "• 解读剪接事件的临床意义": "• Interpret the clinical significance of splicing events",
    "• 查询基因注释和剪接位点信息": "• Query gene annotation and splice-site information",
    "Model Context Protocol · 运行时外部工具调用": "Model Context Protocol · runtime external tool calls",
    "未加载": "Not loaded",
    "自然语言指令": "Natural-language instruction",
    "AI 调用": "AI Call",
    "模型选择 MCP 工具 → 本地校验 → 执行并返回结果": "Model selects an MCP tool → local validation → execute and return results",
    "例如：查一下 CD44 有哪些显著剪接事件": "e.g. Show significant splicing events for CD44",
    "MCP 服务器": "MCP Server",
    "正在读取服务器配置…": "Reading server configuration…",
    "工具": "Tool",
    "选择服务器与工具后调用": "Select a server and tool to call",
    "参数（JSON）": "Arguments (JSON)",
    "调用工具": "Call Tool",
    "尚未调用": "Not called yet",
    "请输入自然语言指令": "Enter a natural-language instruction",
    "请选择可用的服务器与工具": "Select an available server and tool",
    "请输入问题或选择上方技能...": "Type a question or choose a skill above...",
    "输入问题或选择上方技能...": "Type a question or choose a skill above...",
    "发送": "Send",
    "我理解你的问题。请选择上方的技能按钮开始专业分析，或者告诉我你想分析哪个基因/事件。": "I understand your question. Choose a skill above to start a professional analysis, or tell me which gene or event you want to analyze.",
    "查询基因的详细信息，包括外显子结构、剪接位点、保守性评分和临床变异。": "Detailed gene information including exon structure, splice sites, conservation scores, and clinical variants.",
    "搜索 PubMed、Europe PMC 等数据库中的科学文献，查找与基因或疾病相关的剪接研究。": "Search PubMed, Europe PMC, and other databases for splicing studies related to a gene or disease.",
    "对候选基因列表进行 GO、KEGG、Reactome 通路富集分析，识别显著的功能类别。": "Run GO, KEGG, and Reactome pathway enrichment on candidate genes to identify significant functional categories.",
    "解读特定剪接事件的生物学和临床意义，包括致病性预测和治疗靶点分析。": "Interpret the biological and clinical significance of a specific splicing event, including pathogenicity prediction and therapeutic targets.",
    "请提供必要的参数（如基因名称、事件类型等），我将为你执行分析。": "Please provide the required parameters (e.g., gene name, event type) and I will run the analysis.",
    "探索基因剪接模式": "Explore Gene Splicing Patterns",
    "输入基因符号（如 TP53、BRCA1、MYC）...": "Enter a gene symbol (e.g., TP53, BRCA1, MYC)...",
    "输入基因符号查看该基因的所有剪接事件、统计信息和文献证据。支持热门基因如 TP53、BRCA1、MYC、EGFR 等。": "Enter a gene symbol to view all splicing events, statistics, and literature evidence. Popular genes: TP53, BRCA1, MYC, EGFR.",
    "在上方输入基因符号以探索其剪接事件和生物学功能": "Enter a gene symbol above to explore its splicing events and biological function",
    "基因剪接分析报告": "Gene Splicing Analysis Report",
    "返回事件列表": "Back to Event List",
    "总事件数": "Total Events",
    "平均 |ΔPSI|": "Mean |ΔPSI|",
    "事件类型分布": "Event Type Distribution",
    "剪接事件详情": "Splicing Event Details",
    "该基因可能不在当前分析的候选列表中，或未达到显著性阈值": "This gene may not be in the current candidate list or did not pass the significance threshold",
    "浏览所有事件": "Browse All Events",
    "未选择项目": "No project selected",
    "请先在仪表盘选择一个分析项目": "Select an analysis project on the dashboard first",
    "请先选择项目": "Select a project first",
    "在仪表盘选择一个分析项目后再探索基因": "Select an analysis project on the dashboard before exploring genes",
    "图表不可用": "Figure unavailable",
    "该项目可能尚未生成此图表，请完成分析后重试": "This figure may not exist yet. Complete the analysis and try again.",
    "正在渲染图表（首次生成约需数秒）...": "Rendering figure (the first render may take a few seconds)...",
    "报告生成成功！": "Report generated successfully!",
    "文件已自动下载": "The file has been downloaded automatically",
    "在新窗口中查看": "Open in New Window",
    "报告生成失败": "Report generation failed",
    "重试": "Retry",
    "正在生成报告...": "Generating report...",
    "这可能需要几分钟时间，请耐心等待": "This may take a few minutes. Please wait.",
    "未知错误": "Unknown error",
    "无标题": "Untitled",
    "查看原文 →": "View source →",
    "被引次数:": "Citations:",
    "机制:": "Mechanism:",
    "示例:": "Example:",
    "相关临床试验:": "Related clinical trials:",
    "进行中": "Ongoing",
    "位置:": "Location:",
    "染色体:": "Chromosome:",
    "链方向:": "Strand:",
    "生物类型:": "Biotype:",
    "基因符号:": "Gene symbol:",
    "基因名称:": "Gene name:",
    "基因类型:": "Gene type:",
    "未找到匹配的事件": "No matching events found",
    "暂无文献证据": "No literature evidence",
    "关闭": "Close",
    "查看基因详情": "View Gene Details",
    "生物学影响评估": "Biological Impact Assessment",
    "强效应 - 可能导致蛋白质功能重大改变": "Strong effect - may substantially alter protein function",
    "中等效应 - 可能影响蛋白质结构域": "Moderate effect - may affect a protein domain",
    "弱效应 - 可能对功能有轻微影响": "Weak effect - may have a minor functional impact",
    "微小效应 - 可能无显著生物学影响": "Minimal effect - likely no significant biological impact",
    "事件未找到": "Event not found",
    "事件类型说明": "Event Type Description",
    "统计详情": "Statistical Details",
    "P值": "P-value",
    "FDR校正值": "FDR-adjusted",
    "综合评分": "Composite Score",
    "文献证据": "Literature Evidence",
    "加载中...": "Loading...",
    "外显子跳跃 (Skipped Exon): 最常见的外显子类型，可能导致蛋白质结构域缺失": "Skipped exon (SE): the most common event type; may cause loss of a protein domain",
    "互斥外显子 (Mutually Exclusive Exons): 两个相邻外显子中只保留一个": "Mutually exclusive exons (MXE): only one of two adjacent exons is retained",
    "可变3'剪接位点 (Alternative 3' Splice Site): 影响外显子3'端边界": "Alternative 3' splice site (A3SS): affects the exon 3' boundary",
    "可变5'剪接位点 (Alternative 5' Splice Site): 影响外显子5'端边界": "Alternative 5' splice site (A5SS): affects the exon 5' boundary",
    "内含子保留 (Retained Intron): 内含子未被正确移除": "Retained intron (RI): the intron is not removed correctly",
    "未知剪接事件类型": "Unknown splicing event type",
    "以 ΔPSI 为横轴、-log10(FDR) 为纵轴展示全部剪接事件；虚线为 FDR=0.05 与 |ΔPSI|=0.1 阈值，橙色点为显著事件。": "ΔPSI on the x-axis and -log10(FDR) on the y-axis for all splicing events; dashed lines mark FDR=0.05 and |ΔPSI|=0.1; orange points are significant events.",
    "按 |ΔPSI| 排序的 Top 25 候选事件；橙色为包含水平上调，蓝色为下调，直观展示效应量谱。": "Top 25 candidates ranked by |ΔPSI|; orange indicates inclusion up, blue indicates inclusion down.",
    "ΔPSI 的经验累积分布曲线，并标注 |ΔPSI|>0.1 的事件占比，用于评估整体效应量分布。": "Empirical CDF of ΔPSI with the proportion of events above |ΔPSI|>0.1.",
    "候选排名对 -log10(FDR) 曲线，配合 FDR=0.05 参考线定位显著性拐点（elbow）。": "Candidate rank vs -log10(FDR) with an FDR=0.05 reference line to locate the significance elbow.",
    "SE / MXE / A5SS / A3SS / RI 五类可变剪接事件的检出计数。": "Detected counts for the five alternative splicing classes: SE / MXE / A5SS / A3SS / RI.",
    "各事件类型中通过阈值（FDR<0.05 且 |ΔPSI|>0.1）的显著事件与非显著事件构成。": "Significant vs non-significant events within each class using FDR<0.05 and |ΔPSI|>0.1.",
    "五类可变剪接事件的外显子-内含子结构模式图（methods 级示意图）。": "Exon-intron schematic of the five alternative splicing classes (methods-level figure).",
    "Top |ΔPSI| 事件的逐样本 PSI 热图，列上方标注样本分组，用于观察聚类模式。": "Per-sample PSI heatmap for top |ΔPSI| events with sample groups annotated above the columns.",
    "按实验组拆分的 Top 事件 PSI 分布（箱线 + 散点），用于识别离群样本。": "PSI distribution of top events by experimental group (box + scatter) to identify outliers.",
    "样本分组占比（环图）与批次分布（条形），为质控必备图表。": "Sample group proportions (donut) and batch distribution (bars) for QC.",
    "AI 智能体综合评分（显著性+效应+生物学+文献）Top 15 候选事件。": "Top 15 candidates by the agent composite score (significance + effect + biology + literature).",
    "Top 候选的四维评分贡献分解：显著性 / 效应量 / 生物学 / 文献证据。": "Four-dimensional score decomposition for top candidates: significance / effect size / biology / literature evidence.",
    "GO/KEGG 富集结果：横轴为富集倍数，颜色为 -log10(FDR)，点大小为重叠基因数。": "GO/KEGG enrichment: fold enrichment on the x-axis, color is -log10(FDR), dot size is overlapping gene count.",
    "新建分析项目": "New Analysis Project",
    "项目名称": "Project Name",
    "分析查询": "Analysis Query",
    "输入项目名称（如 My_RNA_Study）": "Enter a project name (e.g., My_RNA_Study)",
    "输入分析查询（如 compare treatment vs control）": "Enter an analysis query (e.g., compare treatment vs control)",
    "上传文件": "Upload Files",
    "拖拽文件到此处，或点击选择文件": "Drag files here, or click to choose files",
    "支持 CSV、TSV、TXT 表格（Excel 请另存为 CSV），可同时上传样本分组表": "CSV, TSV or TXT tables (save Excel as CSV); a sample-group table can be uploaded too",
    "取消": "Cancel",
    "开始分析": "Start Analysis",
    "请至少选择一个文件": "Please select at least one file",
    "请先选择一个项目": "Please select a project first",
    "请输入基因符号": "Please enter a gene symbol",
    "请输入分析查询": "Please enter an analysis query",
    "请输入项目名称": "Please enter a project name",
    "处理中...": "Processing...",
    "分析已完成": "Analysis complete",
    "分析已启动，准备中...": "Analysis started, preparing...",
    "上传中...": "Uploading...",
    "分析中（预计 3-6 分钟）...": "Running (estimated 3-6 minutes)...",
    "数据 Agent 正在理解查询...": "Data Agent is interpreting the query...",
    "质控 Agent 正在进行质量检查...": "QC Agent is running quality checks...",
    "剪接检测 Agent 正在筛选显著事件...": "Splicing Detection Agent is filtering significant events...",
    "统计 Agent 正在排序候选事件...": "Statistics Agent is ranking candidate events...",
    "注释 Agent 正在收集文献证据...": "Annotation Agent is collecting literature evidence...",
    "注释 Agent 正在进行通路富集分析...": "Annotation Agent is running pathway enrichment...",
    "解读 Agent 正在生成生物学解读...": "Interpretation Agent is generating biological interpretation...",
    "生成分析报告": "Generate Analysis Report",
    "基于当前分析结果生成专业报告": "Generate a professional report from the current analysis",
    "完成分析后可生成包含统计结果、可视化和生物学解读的专业报告": "Generate a professional report with statistics, visualizations, and biological interpretation after analysis",
    "你": "You",
    "数据 Agent": "Data Agent",
    "质控 Agent": "QC Agent",
    "剪接检测 Agent": "Splicing Detection Agent",
    "统计 Agent": "Statistics Agent",
    "注释 Agent": "Annotation Agent",
    "解读 Agent": "Interpretation Agent",
    "应用筛选": "Apply filters",
    "探索": "Explore",
    "核心统计图": "Core statistics",
    "样本与质控": "Samples and QC",
    "事件组成与机制": "Event composition and mechanisms",
    "AI 排序与功能富集": "AI ranking and enrichment",
    "火山图 Volcano": "Volcano plot",
    "ΔPSI 累积分布 ECDF": "ΔPSI ECDF",
    "显著性碎石图 Scree": "Significance scree plot",
    "类型×显著性堆叠图": "Type × significance stacked plot",
    "剪接机制示意图 Schematic": "Splicing mechanism schematic",
    "PSI 热图 Heatmap": "PSI heatmap",
    "分组 PSI 箱线图": "Grouped PSI box plot",
    "队列构成图": "Cohort composition",
    "候选基因排名": "Candidate gene ranking",
    "评分分解堆叠图": "Score decomposition stacked plot",
    "功能富集点图": "Functional enrichment dot plot",
    "ΔPSI 瀑布图 Waterfall": "ΔPSI waterfall",
    "分析结果": "Analysis results",
    "EpitopeRank 智能助手": "EpitopeRank Assistant",
    "MCP 工具": "MCP tools",
    "分析完成": "Analysis complete",
    "分析失败": "Analysis failed",
    "通路富集分析结果": "Pathway Enrichment Results",
    "文献搜索结果": "Literature Search Results",
    "剪接事件解读": "Splice Event Interpretation",
    "总结": "Summary",
    "报告内容": "Report contents",
    "导出当前项目的剪接分析、图表及候选新抗原证据。": "Export this project's splicing analysis, figures and candidate neoantigen evidence.",
    "有已保存的项目肽结果时，报告会附上候选序列、来源和 HLA 预测。": "Saved project peptide results add candidate sequences, sources and HLA predictions to the report.",
    "• 按项目阈值筛选的剪接事件": "• Splicing events filtered at the project thresholds",
    "• 候选肽与新抗原证据（含未评估项）": "• Candidate peptides and neoantigen evidence, including unevaluated fields",
    "• 生物学解读与分析局限": "• Biological interpretation and limitations",
    "展示同时具有 ΔPSI 与 FDR 的事件。虚线标记图中采用的阈值。": "Shows events with both ΔPSI and FDR. Dashed lines mark the thresholds used.",
    "请确认项目输入仍可访问，然后重试。": "Check that the project inputs are still available, then try again.",
    "HTML 报告": "HTML report",
    "PDF 报告": "PDF report",
    "提示": "Tip",
    "Agent 已读取数据结构，请确认字段映射后开始分析。": "The agent has read the data structure. Confirm the field mapping to start.",
    "HLA 型别": "HLA type",
    "HLA-I 型别（可选，多个用逗号分隔）": "HLA-I alleles (optional, comma-separated)",
    "IEDB（在线）": "IEDB (online)",
    "MHC 类别": "MHC class",
    "MHCflurry（本地，需安装）": "MHCflurry (local, requires install)",
    "Percentile rank 越低越好。": "Lower percentile rank is better.",
    "auto（本地优先，失败转 IEDB）": "auto (local first, fall back to IEDB)",
    "both（按类别拆分）": "both (split by class)",
    "moPepGen · Docker 变异肽生成": "moPepGen · Docker variant peptide generation",
    "上一页": "Previous",
    "上传事件数据，确认字段与分组，再查看统计结果和研究报告。": "Upload event data, confirm fields and groups, then review statistics and the research report.",
    "下一页": "Next",
    "下载 PDF": "Download PDF",
    "下载当前文件": "Download this file",
    "主导航": "Primary navigation",
    "仅显著事件": "Significant only",
    "从候选序列出发，比较 HLA 结合能力，找到值得进一步研究的肽段。": "Start from candidate sequences, compare HLA binding, and find peptides worth following up.",
    "从当前项目生成候选肽": "Generate candidate peptides from the current project",
    "从当前项目生成并排序": "Generate and rank from the current project",
    "从本机添加编码序列表…": "Add a coding-sequence table from this computer…",
    "以基因为线索，连接剪接事件、统计结果与生物学证据。": "Follow a gene to connect splicing events, statistics, and biological evidence.",
    "使用当前项目查找候选肽。先检查数据，再决定是否进行 HLA 结合预测。": "Find candidate peptides from the current project. Check the data first, then decide whether to run HLA binding prediction.",
    "使用当前项目的剪接事件与已重建的编码序列对照表生成跨连接点候选肽（对照表按表头自动识别，文件名不限）， 再按上面的 HLA 与预测选项排序。读码框与 ORF 必须由上游提供，平台不会从坐标猜测序列。": "Build junction-spanning candidate peptides from the current project's splicing events and reconstructed coding-sequence table (the table is detected by its header, file name unrestricted), then rank them with the HLA and prediction options above. The reading frame and ORF must come from upstream; the platform never guesses sequences from coordinates.",
    "使用当前项目逐阶段运行。每次确认只执行下一阶段；输入文件应位于项目数据目录。流程进度会保存。": "Run the current project stage by stage. Each confirmation executes only the next stage; input files should live in the project data directory. Progress is saved.",
    "使用所选文件生成候选肽": "Generate candidate peptides from the selected files",
    "例如 HLA-A*02:01, HLA-B*07:02": "e.g. HLA-A*02:01, HLA-B*07:02",
    "例如 HLA-A*02:01,HLA-B*07:02": "e.g. HLA-A*02:01,HLA-B*07:02",
    "候选事件 Top 10": "Top 10 candidate events",
    "候选肽序列": "Candidate peptide sequences",
    "先选类别，再选择运行方式。在线预测需要网络连接。": "Choose the class first, then the run mode. Online prediction requires a network connection.",
    "关闭导航": "Close navigation",
    "关闭快捷跳转": "Close quick switch",
    "关闭菜单": "Close menu",
    "准备候选肽": "Prepare candidate peptides",
    "准备数据": "Prepare data",
    "分析流程": "Analysis pipeline",
    "分阶段证据审计": "Staged evidence audit",
    "删除项目": "Delete project",
    "剪接事件与候选肽分析": "Splicing events and candidate peptide analysis",
    "新抗原筛选": "Neoantigen screening",
    "从当前项目筛选": "Screen from project",
    "直接输入肽段": "Direct peptides",
    "一键筛选新抗原": "Screen neoantigens",
    "送去筛选新抗原 →": "Screen selected →",
    "导出 FASTA": "Export FASTA",
    "导出合成清单 CSV": "Export synthesis CSV",
    "刷新状态": "Refresh",
    "上传 CDS 表…": "Upload CDS…",
    "剪接候选新抗原": "Splice-derived neoantigens",
    "剪接来源候选新抗原": "Splice-derived candidate neoantigens",
    "加工预测（proteasome / TAP）": "Processing prediction (proteasome / TAP)",
    "动态：开": "Motion: on",
    "历史项目": "Project history",
    "历史项目详情": "Project details",
    "项目详情": "Project details",
    "关闭详情": "Close details",
    "参考表尚未加载。": "The reference table is not loaded yet.",
    "可视化工作室": "Visualization studio",
    "可选：选择其他文件进行独立分析": "Optional: choose other files for a standalone analysis",
    "图表类型": "Chart type",
    "图表（点击放大）": "Figures (click to enlarge)",
    "基因探索": "Gene explorer",
    "基因符号": "Gene symbol",
    "填入示例": "Fill example",
    "填写后，候选肽和 HLA 型别会分批发送至 IEDB 做 NetMHCpan 结合预测（需要联网，几百条肽通常 30–90 秒）。预测不等于免疫原性验证。": "After you fill them in, candidate peptides and HLA alleles are sent in batches to IEDB for NetMHCpan binding prediction (network required; a few hundred peptides usually take 30–90 s). Prediction is not proof of immunogenicity.",
    "复制全部": "Copy all",
    "如何看结果？": "How to read the results",
    "它代表相对排名，不是亲和力 Kd。": "It is a relative ranking, not an affinity Kd.",
    "密钥仅保存在本机 .env / 配置大模型.env，保存后即时生效。": "The key is stored only in a local .env file and applies immediately after saving.",
    "将当前项目的统计结果、图表和解读整理为可分享的研究报告。": "Assemble the current project's statistics, figures, and interpretation into a shareable research report.",
    "工作区": "Workspace",
    "工作区设置": "Workspace settings",
    "已有肽序列？直接预测": "Already have peptides? Predict directly",
    "已识别 0 条肽段": "0 peptides recognized",
    "常用 MHC-I 面板": "Common MHC-I panels",
    "常用 MHC-II 面板": "Common MHC-II panels",
    "开头的标题行会被忽略。 单次最多 200 条肽、8 个 HLA（接口限制），避免触发 IEDB 频率限制。": "Leading header lines are ignored. Up to 200 peptides and 8 HLA alleles per run (API limits) to stay under IEDB rate limits.",
    "开始一次新的分析": "Start a new analysis",
    "开始使用": "Getting started",
    "开始阶段 0 审计": "Start stage 0 audit",
    "快捷跳转": "Quick switch",
    "快速前往工作区": "Jump to a workspace",
    "成果文件夹": "Results folder",
    "打包 ZIP": "Package ZIP",
    "打开 HTML 报告": "Open HTML report",
    "打开结果目录": "Open results directory",
    "报告与交付": "Reports and delivery",
    "按 FDR": "By FDR",
    "按 |ΔPSI|": "By |ΔPSI|",
    "按基因、事件类型与显著性筛选，追溯候选事件的统计依据。": "Filter by gene, event type, and significance to trace the statistical basis of each candidate.",
    "按基因名": "By gene name",
    "排序": "Sort",
    "探索与导出": "Explore and export",
    "探索性候选肽生成": "Exploratory candidate peptide generation",
    "搜索事件": "Search events",
    "搜索历史项目": "Search project history",
    "搜索工作区": "Search workspace",
    "搜索页面，如 肽预测、报告…": "Search pages, e.g. peptide, report…",
    "支持 CSV、TSV、TXT、文本 .xls、Excel .xls/.xlsx/.xlsm 及压缩文本 .gz；表达量表会被识别并提示所需事件数据": "Supports CSV, TSV, TXT, text .xls, Excel .xls/.xlsx/.xlsm, and gzipped text .gz; expression matrices are detected and the required event data is reported",
    "支持事件表与报告目录导入": "Import event tables and report directories",
    "数据目录：读取中…": "Data directory: reading…",
    "文件名不限": "Any file name",
    "智能接入检查": "Smart ingestion check",
    "末页": "Last",
    "查看数据处理、统计分析与解读进度，定位当前执行阶段。": "Track data processing, statistical analysis, and interpretation, and see which stage is running.",
    "查询 IEDB 已知表位": "Query known IEDB epitopes",
    "样本分组": "Sample groups",
    "检查与分析": "Check and analyze",
    "检查当前项目": "Check the current project",
    "检查编码序列，生成跨连接点候选肽，再进入结合预测与证据审计。": "Validate coding sequences, build junction-spanning candidate peptides, then move on to binding prediction and evidence audit.",
    "正在读取当前项目…": "Reading the current project…",
    "每行一个肽段（8–30 aa）；可直接粘贴 FASTA 序列，": "One peptide per line (8–30 aa); FASTA can be pasted directly,",
    "流程日志（最近 12 条）": "Pipeline log (last 12 entries)",
    "浏览候选事件，生成图表与报告": "Browse candidate events, generate figures and reports",
    "浏览全部事件": "Browse all events",
    "清空型别": "Clear alleles",
    "生成候选肽": "Generate candidate peptides",
    "用于报告里的 AI 解读与 MCP 工具的自然语言调用。密钥只保存在本机，不会写入报告或日志。": "Used for AI interpretation in reports and natural-language MCP tool calls. The key stays on this machine and is never written to reports or logs.",
    "研究工作区": "Research workspace",
    "确认列的含义": "Confirm what each column means",
    "确认并执行下一阶段": "Confirm and run the next stage",
    "确认数据映射，跟踪每一步进度": "Confirm the data mapping and follow every step",
    "确认映射并分析": "Confirm mapping and analyze",
    "确认这套对应关系": "Confirm this mapping",
    "第一步：检查项目数据": "Step 1: check project data",
    "第二步：选择编码序列表，生成候选肽": "Step 2: choose a coding-sequence table and generate candidate peptides",
    "管理剪接分析项目，追踪进度，回到每一次研究的结果。": "Manage splicing projects, track progress, and return to each study's results.",
    "系统会检查剪接事件和生成肽所需的编码序列表。": "The system checks the splicing events and the coding-sequence table needed to build peptides.",
    "结合预测不等于抗原呈递，也不等于免疫原性。排序仅用于探索性候选筛选。": "Binding prediction is not antigen presentation and not immunogenicity. Ranking is for exploratory candidate triage only.",
    "编码序列对照表需包含": "The coding-sequence table must contain",
    "编码序列表": "Coding-sequence table",
    "编码序列表就是「每个剪接事件对应的参考 CDS 与改变后 CDS」。系统按表头自动识别，": "A coding-sequence table maps each splicing event to its reference CDS and altered CDS. It is detected by header,",
    "肽预测": "Peptide prediction",
    "肽预测工作台": "Peptide prediction workbench",
    "自动识别当前项目中的 rMATS 事件表（JC 或 JCEC，文件名不限）。请提供版本匹配的参考文件并启动 Docker；生成的是蛋白质组学变异肽，不是 HLA 预测或 CDS 对照表。": "Auto-detect rMATS event tables in the current project (JC or JCEC, any file name). Provide a version-matched reference and start Docker; the output is proteomic variant peptides, not HLA predictions or a CDS table.",
    "菜单": "Menu",
    "请先选择一个项目。": "Select a project first.",
    "请先选择项目并填写已知证据。": "Select a project and fill in the known evidence first.",
    "跳到工作区": "Skip to workspace",
    "运行 moPepGen": "Run moPepGen",
    "这张表的列名不是标准写法，系统已按内容猜测。请核对下面四项，确认后只需设置一次。": "This table does not use standard column names, so the system guessed from the content. Check the four fields below; you only need to confirm once.",
    "选择 HLA": "Select HLA",
    "选择华大报告目录": "Choose a BGI report directory",
    "选择图表后，预览将在这里显示": "Pick a chart and the preview appears here",
    "选择数据文件": "Choose data files",
    "选择研究问题对应的图表，查看当前项目的可视化结果。": "Choose the chart that matches your research question to view this project's visualizations.",
    "选择要查看的图表": "Choose a chart",
    "逗号分隔；输入时会在 IEDB 等位基因表中搜索（最多显示 500 条）。class-I 与 class-II 需分别预测， 选择“both”时平台会按类别拆分。": "Comma-separated; typing searches the IEDB allele table (up to 500 matches). class-I and class-II are predicted separately; choosing \\"both\\" splits by class.",
    "配置 AI 解读服务与外部工具，查看连接状态。": "Configure the AI interpretation service and external tools, and check their connection status.",
    "项目工作台": "Project workspace",
    "预测与解读": "Prediction and interpretation",
    "预测器": "Predictor",
    "预测并排序": "Predict and rank",
    "预测流程": "Prediction pipeline",
    "预测结果": "Prediction results",
    "预测设置": "Prediction settings",
    "首页": "First",
    "高级选项：其他文件和专业分析工具": "Advanced: other files and specialist tools",
    "默认使用当前项目已上传的数据。编码序列对照表按表头自动识别，文件名不限；也可在下方选择文件进行独立分析。MHC 结合预测不等于免疫原性验证。": "Uses the data already uploaded to the current project by default. The coding-sequence table is detected by header with no file-name restriction; you can also pick files below for a standalone analysis. MHC binding prediction is not immunogenicity validation.",
    "，其中 junction_nt 是异常 CDS 内新连接点前的核苷酸数。": ", where junction_nt is the number of nucleotides before the novel junction in the altered CDS.",
    "；下面若已列出文件，直接选即可。": "; if files are already listed below, just pick one.",
    "完成": "Done",
    "未完成": "Not completed",
    "请注意": "Please check",
    "通知": "Notice",
    "上传没有完成": "Upload did not finish",
    "文件或数据目录在上传阶段中断，分析尚未启动。": "The upload was interrupted before analysis started.",
    "确认文件格式为 CSV、TSV、TXT 或表格型 XLS": "Check the file is CSV, TSV, TXT, or a table-style XLS",
    "单个文件不要过大，必要时先拆分": "Keep individual files small; split them if needed",
    "检查网络与本地服务是否可用": "Check that the network and the local service are up",
    "分析未能完成": "Analysis did not finish",
    "服务返回了错误，本次分析已中止。修正输入后可以重新发起。": "The service returned an error and this run was stopped. Fix the input and start again.",
    "结果已写入当前项目": "Results written to the current project",
    "事件表已解析，显著性筛选与候选排序都已完成。接下来可以逐条查看事件，或直接生成研究报告。": "The event table is parsed; significance filtering and candidate ranking are done. You can now review events one by one, or generate the research report.",
    "生成研究报告": "Generate report",
    "查看可视化": "View figures",
    "浏览事件": "Browse events",
    "连接已中断": "Connection lost",
    "前端没能拿到分析响应，但后台任务可能仍在运行。稍后点击右上角「刷新」即可看到最新进度。": "The UI did not receive the response, but the job may still be running. Use Refresh at the top right shortly to see the latest progress.",
    "删除这个项目？": "Delete this project?",
    "保留项目": "Keep project",
    "替换当前输入？": "Replace the current input?",
    "填入示例会覆盖当前填写好的肽序列和 HLA 型别。": "Filling in the example will overwrite the peptide sequences and HLA alleles you already entered.",
    "保留输入": "Keep input",
    "删除失败：": "Delete failed:",
    "删除失败：HTTP": "Delete failed: HTTP",
    "Agent 已读取数据结构。确认字段映射后，将标准化并进入原有分析流程。": "The agent has read the data structure. After you confirm the field mapping it will normalize the data and enter the standard analysis pipeline.",
    "Agent 正在规划 MCP 工具调用…": "The agent is planning an MCP tool call…",
    "Agent 规划（": "Agent plan (",
    "Agent 调用失败：": "Agent call failed:",
    "Agent 调用异常：": "Agent call error:",
    "FDR 覆盖": "FDR coverage",
    "FPKM、TPM 和 read_count 是表达量，不是剪接事件 PSI；请上传 SE/MXE/A3SS/A5SS/RI 事件表。": "FPKM, TPM, and read_count are expression levels, not splicing PSI; please upload SE/MXE/A3SS/A5SS/RI event tables.",
    "GENCODE 或 ENSEMBL": "GENCODE or ENSEMBL",
    "GTEx 基因组版本": "GTEx genome build",
    "GTEx 蛋白 FASTA 文件名": "GTEx protein FASTA file name",
    "GTEx 连接点表文件名": "GTEx junction table file name",
    "HLA 分型来源": "HLA typing source",
    "HLA 置信度": "HLA confidence",
    "HLA-I 型别，逗号分隔": "HLA-I alleles, comma-separated",
    "IEDB 在线 · MHCflurry": "IEDB online · MHCflurry",
    "LLM 规划": "LLM plan",
    "percentile rank 越低越好；预测不等于呈递或免疫原性。": "Lower percentile rank is better; prediction is not presentation or immunogenicity.",
    "— 未映射 —": "— not mapped —",
    "— 请选择 —": "— select —",
    "。原报告没有组间 p 值或 FDR，不会报告显著差异。": ". The original report has no between-group p-values or FDR, so no significant differences are reported.",
    "。将读取项目目录中的事件表和编码序列对照表。": ". Event tables and the coding-sequence table will be read from the project directory.",
    "上传失败": "Upload failed",
    "上游 ORF 表文件名（留空自动识别）": "Upstream ORF table file name (leave blank to auto-detect)",
    "不可解析": "Unparseable",
    "个等位基因": "alleles",
    "事件基因组版本": "Event genome build",
    "事件表": "Event table",
    "事件表完整性：complete / subset / unknown": "Event table completeness: complete / subset / unknown",
    "事件连接点表文件名": "Event junction table file name",
    "事件类型分布 Composition": "Event type composition",
    "事件类型：": "Event types:",
    "例如 GRCh38 / GENCODE vXX（须与上游一致）": "e.g. GRCh38 / GENCODE vXX (must match upstream)",
    "保存失败": "Save failed",
    "保存失败:": "Save failed:",
    "信息": "Info",
    "候选基因排名 Ranking": "Candidate gene ranking",
    "全蛋白组 FASTA 文件名": "Whole-proteome FASTA file name",
    "内置": "Built-in",
    "分组 PSI 箱线图 Box Plot": "Grouped PSI box plot",
    "剪接事件：": "Splicing events:",
    "功能富集点图 Dot Plot": "Functional enrichment dot plot",
    "加载中…": "Loading…",
    "动态：关": "Motion: off",
    "动态：系统关闭": "Motion: off by system",
    "单次最多 200 条肽，当前输入": "At most 200 peptides per run; currently",
    "单次最多 8 个 HLA 型别，当前输入": "At most 8 HLA alleles per run; currently",
    "原生格式：": "Native format:",
    "参数不是合法 JSON：": "Arguments are not valid JSON:",
    "参数必须是 JSON 对象，例如 {\\"project_id\\": \\"SPN-XXXX\\"}": "Arguments must be a JSON object, e.g. {\\"project_id\\": \\"SPN-XXXX\\"}",
    "参考基因组 FASTA 文件": "Reference genome FASTA file",
    "参考来源（GENCODE 或 ENSEMBL）": "Reference source (GENCODE or ENSEMBL)",
    "参考蛋白组 FASTA 文件": "Reference proteome FASTA file",
    "参考表加载失败": "Failed to load the reference table",
    "参考表加载失败：": "Failed to load the reference table:",
    "参考表：共": "Reference table:",
    "参考（正常）编码序列": "Reference (normal) coding sequence",
    "另有": "Additionally",
    "可以继续生成候选肽。检查只确认了表头，序列的读码框仍需由专业人员核实。": "You can continue generating candidate peptides. The check only confirmed headers; a specialist must still verify the reading frames.",
    "可用": "Available",
    "可解析": "Parseable",
    "同一列不能承担两个角色，请分别选择。": "One column cannot serve two roles; choose them separately.",
    "图表": "Chart",
    "在": "in",
    "坐标": "Coordinates",
    "坐标基准": "Coordinate basis",
    "基因组及注释版本": "Genome and annotation build",
    "基因组版本": "Genome build",
    "复制失败，请手动选择表格内容": "Copy failed; select the table content manually",
    "大模型 + 规则": "LLM + rules",
    "大模型已提出分组建议，请核对。": "The LLM suggested groups; please verify.",
    "失败": "Failed",
    "字段映射": "Field mapping",
    "字符": "characters",
    "完成：候选": "Done: candidates",
    "审计失败": "Audit failed",
    "尚无可靠的完整分组建议，可修改分组名称并批量分配。": "No reliable complete grouping yet; rename groups and assign samples in bulk.",
    "尚未选择项目。请先在“仪表盘”新建或选择一个项目，再回来生成候选肽。": "No project selected. Create or select one on the Dashboard, then come back to generate candidate peptides.",
    "尚未选择项目，请先在仪表盘选择或新建项目。": "No project selected. Select or create one on the Dashboard first.",
    "已从相同事件文件的历史样本表恢复分组建议。": "Group suggestions restored from a previous sample table for the same event file.",
    "已保存过映射。": "A mapping has already been saved.",
    "已保存，按这套映射可为": "Saved; this mapping can be used for",
    "已停止：": "Stopped:",
    "已在文件管理器中打开结果目录": "Opened the results directory in the file manager",
    "已复制到剪贴板": "Copied to clipboard",
    "已打开：": "Opened:",
    "已有读码框正确的 CDS": "CDS with a verified reading frame already available",
    "已添加": "Added",
    "已触发下载；桌面窗口若未保存文件，请直接查看表格或复制全部": "Download triggered; if the desktop window did not save the file, view the table or copy everything",
    "已识别": "Recognized",
    "已识别 rMATS 文件：": "rMATS files recognized:",
    "已识别华大逐样本剪接表。确认真实分组后可生成探索性 PSI 表；原报告没有组间显著性检验。": "Per-sample BGI splicing tables recognized. After you confirm the real groups an exploratory PSI table can be generated; the original report has no between-group significance test.",
    "已读取上传的样本表。": "The uploaded sample table has been read.",
    "已连接": "Connected",
    "已配置 ·": "Configured ·",
    "当前密钥": "Current key",
    "当前项目已切换，请重新检查。": "The current project changed; please check again.",
    "当前项目：": "Current project:",
    "成功": "OK",
    "打包失败": "Packaging failed",
    "打包失败：": "Packaging failed:",
    "打开成果文件夹失败": "Failed to open the results folder",
    "打开成果文件夹失败：": "Failed to open the results folder:",
    "执行失败": "Run failed",
    "执行失败，请查看日志。": "Run failed; check the log.",
    "执行完成。": "Run finished.",
    "探索性事件表已生成：": "Exploratory event table generated:",
    "接受跳过缺失的连接点或组织表达检查": "Allow skipping missing junction or tissue-expression checks",
    "改变后（变异）编码序列": "Altered (variant) coding sequence",
    "数据校验未通过": "Data validation failed",
    "文件已自动选中。": "The file has been selected automatically.",
    "文件已读取并识别为表达量矩阵。请另选剪接事件结果表进行剪接分析。": "The file was read and identified as an expression matrix. Choose a splicing event result table for splicing analysis.",
    "文件画像": "File profile",
    "新剪接连接点位置（整数）": "Novel junction position (integer)",
    "方法": "Method",
    "无": "None",
    "无法开始：": "Cannot start:",
    "无法恢复流程，请重新开始审计。": "The pipeline cannot be resumed; restart the audit.",
    "无法打开目录：": "Cannot open the directory:",
    "无法继续：": "Cannot continue:",
    "无法自动标准化": "Cannot normalize automatically",
    "无法访问此项目的原始数据目录。请重新选择该项目的数据文件，或联系管理员检查存储位置。": "The project's raw data directory is not accessible. Re-select the project's data files, or ask an administrator to check the storage location.",
    "无法运行：": "Cannot run:",
    "映射来源：": "Mapping source:",
    "显著性碎石图 Scree Plot": "Significance scree plot",
    "最低 junction 支持读数": "Minimum junction-support reads",
    "最低有效样本数": "Minimum informative samples",
    "有效事件": "Valid events",
    "未分配项 → 第一组": "Unassigned → group 1",
    "未分配项 → 第二组": "Unassigned → group 2",
    "未分组": "Ungrouped",
    "未安装": "Not installed",
    "未知阶段": "Unknown stage",
    "未能从这些文件中识别出可分析的剪接事件表。": "No analyzable splicing event table could be identified in these files.",
    "未连接": "Not connected",
    "未配置": "Not configured",
    "条服务错误，见下方说明": "service errors, see below",
    "条肽段（8–30 aa）": "peptides (8–30 aa)",
    "查看或调整逐样本分组": "Review or adjust per-sample groups",
    "标准化": "Standardization",
    "标准化中…": "Standardizing…",
    "标准化失败：": "Standardization failed:",
    "标准化预览（前 5 行）": "Normalized preview (first 5 rows)",
    "样本": "Samples",
    "样本分组确认": "Confirm sample groups",
    "样本表": "Sample table",
    "检查失败": "Check failed",
    "检查失败：": "Check failed:",
    "检查结果": "Check results",
    "检测到": "Detected",
    "模型映射": "LLM mapping",
    "模型正在选择工具…": "The model is choosing a tool…",
    "正在上传": "Uploading",
    "正在上传和分析…": "Uploading and analyzing…",
    "正在使用当前项目数据分析…": "Analyzing with the current project's data…",
    "正在保存…": "Saving…",
    "正在加载等位基因参考表…": "Loading the allele reference table…",
    "正在审计…": "Auditing…",
    "正在打包…": "Packaging…",
    "正在执行阶段": "Running stage",
    "正在整理成果文件夹…": "Assembling the results folder…",
    "正在检查项目数据…": "Checking project data…",
    "正在生成候选肽并查询 IEDB（": "Generating candidate peptides and querying IEDB (",
    "正在读取项目数据并生成候选肽，预测可能需要数十秒…": "Reading project data and generating candidate peptides; prediction may take tens of seconds…",
    "正在调用预测服务（": "Calling the prediction service (",
    "正在运行 Docker，耗时取决于输入大小，请勿关闭程序…": "Docker is running; duration depends on input size, please keep the app open…",
    "正在连接 MCP 服务器…": "Connecting to MCP servers…",
    "正在通过 MCP 调用": "Calling via MCP",
    "正常对照设计": "Normal control design",
    "正常组织表达表文件名": "Normal tissue expression table file name",
    "没有匹配的页面，试试「报告」或「设置」。": "No matching page. Try \\"Report\\" or \\"Settings\\".",
    "没有每样本 PSI 数据，无法生成真实的样本箱线图或热图。": "No per-sample PSI data, so a real sample box plot or heatmap cannot be produced.",
    "注释版本": "Annotation release",
    "流程已停止或完成": "The pipeline has stopped or finished",
    "火山图 Volcano Plot": "Volcano plot",
    "点下方「从本机添加编码序列表」就能直接补上，不用重新跑整个分析。": "Use \\"Add a coding-sequence table from this computer\\" below to fill the gap without re-running the whole analysis.",
    "点击移除": "Click to remove",
    "点左侧按钮从本机添加，或重新上传项目时把它一起放进去。": "Use the button on the left to add it from this computer, or include it the next time you upload the project.",
    "状态：": "Status:",
    "理由：": "Reason:",
    "生成候选肽失败": "Failed to generate candidate peptides",
    "用时": "Elapsed",
    "目录中没有找到华大逐样本剪接表（如 OC_001.SE.xls）": "No per-sample BGI splicing table (e.g. OC_001.SE.xls) found in this directory",
    "相对于项目上传目录的文件路径": "Path relative to the project upload directory",
    "确定性规则": "Deterministic rules",
    "确认分组并生成探索性表": "Confirm groups and generate the exploratory table",
    "确认并执行阶段": "Confirm and run stage",
    "确认支持读数为 junction 读数": "Confirm support reads are junction reads",
    "确认输入为已量化事件": "Confirm the input is quantified events",
    "类型 × 显著性堆叠图": "Type × significance stacked plot",
    "粘贴你的 API Key": "Paste your API key",
    "结果目录：": "Results directory:",
    "结果：": "Result:",
    "编码序列表：已自动识别": "Coding-sequence table: detected",
    "编码序列表：暂未找到": "Coding-sequence table: not found yet",
    "置信度": "Confidence",
    "肽段": "Peptide",
    "肿瘤表达及复现率表文件名": "Tumor expression and recurrence table file name",
    "能力信息加载失败": "Failed to load capability information",
    "能力信息加载失败：": "Failed to load capability information:",
    "自动猜测结果，确认后以后不再询问。": "Automatically guessed; confirm once and it will not ask again.",
    "自动识别": "Auto-detect",
    "行": "rows",
    "行 ·": "rows ·",
    "行无效输入": "invalid input lines",
    "规则回退": "Rule fallback",
    "规则映射": "Rule mapping",
    "评分分解堆叠图 Decomposition": "Score decomposition stacked plot",
    "请为每个样本选择分组，并确保两组都有样本。": "Assign a group to every sample and make sure both groups are non-empty.",
    "请先在上方填写 HLA 型别。": "Enter the HLA alleles above first.",
    "请先补全映射": "Complete the mapping first",
    "请先输入至少一条 8–30 aa 的候选肽序列。": "Enter at least one candidate peptide of 8–30 aa.",
    "请先选择已上传数据的项目，或选择文件进行独立分析。": "Select a project with uploaded data, or choose files for a standalone analysis.",
    "请先选择项目。": "Select a project first.",
    "请先选择项目和编码序列表。": "Select a project and a coding-sequence table first.",
    "请填写已知证据并开始审计。": "Fill in the known evidence and start the audit.",
    "请填写新审计的证据，再点击开始阶段 0。": "Fill in the new audit evidence, then start stage 0.",
    "请映射 FDR 或 p 值，否则无法筛选显著事件。": "Map FDR or a p-value, otherwise significant events cannot be filtered.",
    "请映射 ΔPSI，或同时映射两组平均 PSI。": "Map ΔPSI, or map both group mean PSI values.",
    "请核对每个样本的分组，确认后开始分析。": "Verify each sample's group, then start the analysis.",
    "请至少填写一个 HLA 型别，或点击常用面板快速填充。": "Enter at least one HLA allele, or use a common panel.",
    "请至少映射基因符号或基因 ID。": "Map at least the gene symbol or gene ID.",
    "调用中…": "Calling…",
    "调用失败：": "Call failed:",
    "调用异常：": "Call error:",
    "转录本注释 GTF 文件": "Transcript annotation GTF file",
    "输入数据类型": "Input data type",
    "输出目录：": "Output directory:",
    "还没有可用的编码序列表。点第一步下方的「从本机添加编码序列表」补上，再回来生成。": "No coding-sequence table available yet. Add one with \\"Add a coding-sequence table from this computer\\" under step 1, then come back to generate.",
    "还没有选择项目。请先创建或选择一个项目，再回来检查。": "No project selected. Create or select one, then come back to check.",
    "连接中…": "Connecting…",
    "连接失败": "Connection failed",
    "连接方式：": "Connection:",
    "配对正常蛋白 FASTA 文件名": "Matched normal protein FASTA file name",
    "错误": "Error",
    "队列构成图 Cohort QC": "Cohort composition",
    "阶段": "Stage",
    "需要一份含 event_id、reference_cds、altered_cds、junction_nt 四列的表，文件名随意。": "Needs a table with event_id, reference_cds, altered_cds, and junction_nt columns; the file name does not matter.",
    "项目：": "Project:",
    "预测失败": "Prediction failed",
    "预测完成：候选": "Prediction complete: candidates",
    "高": "high",
    "中": "medium",
    "低": "low",
    "（无描述）": "(no description)",
    "（当前匹配": "(currently matching",
    "（显示前": "(showing first",
    "（未提供，已根据样本名推断分组）": "(not provided; groups inferred from sample names)",
    "（未连接）": "(not connected)",
    "（空列名）": "(empty column name)",
    "（请选择）": "(select)",
    "（还没有可用的编码序列表）": "(no coding-sequence table available yet)",
    "，列：": ", columns:",
    "，可在下拉里切换。": "; switch in the dropdown.",
    "，失败": ", failed",
    "，忽略": ", ignored",
    "，留空保持不变": ", leave blank to keep",
    "；HLA 结合预测成功": "; HLA binding prediction succeeded",
    "；无服务错误": "; no service errors",
    "；有": "; there are",
    "；服务错误": "; service errors",
    "；未填写 HLA，只生成候选肽，未做任何外部预测。": "; no HLA alleles given, so only candidate peptides were generated and no external prediction was run.",
    "；超出单次上限的部分（": "; the part beyond the per-run limit (",
    "项没有选择。": "options not selected.",
    "个 HLA 型别，通常 30–90 秒，请勿关闭页面）…": "HLA alleles, usually 30–90 s, please keep the page open)…",
    "个 HLA）…": "HLA)…",
    "个文件看着像编码序列表，但没被采用（不影响下面的生成）：": "files look like coding-sequence tables but were not used (this does not affect generation):",
    "个；请分批预测。": "; please predict in batches.",
    "份（": "files (",
    "份，默认用": "files, defaulting to",
    "条": "items",
    "条，排序": "items, ranked",
    "条，预测": "peptides, predicted",
    "条，预测记录": "entries, prediction records",
    "条；证据分层": "entries; evidence tiers",
    "条；请分批预测。": "; please predict in batches.",
    "条）未预测，可缩小 CDS 表后重跑": ") were not predicted; shrink the CDS table and rerun",
    "条（详见 manifest 的 prediction_errors）": "(see prediction_errors in the manifest)",
    "条肽 ×": "peptides ×",
    "列": "column",
    "分数": "Score",
    "· 参考表 class1": "· reference table class1",
    "· 已知表位": "· known epitopes",
    "· 模型回退": "· model fallback",
    "ms · 失败": "ms · failed",
    "ΔPSI 覆盖": "ΔPSI coverage",
    "系统通知": "System notifications",
    "已归档": "Archived",
    "数据目录：": "Data directory: ",
    "列出本机已分析的 EpitopeRank 项目及 project_id。": "Lists analyzed EpitopeRank projects on this machine with their project_id.",
    "MHC-I 参考表：共 0 个等位基因": "MHC-I reference: 0 alleles",
  };

  var RULES = [
    function (s) {
      var p = "执行中: ";
      if (s.indexOf(p) === 0) return "Running: " + translateOne(s.slice(p.length));
      return null;
    },
    function (s) {
      var p = "请输入 ", q = " 的参数...";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return "Enter parameters for " + translateOne(s.slice(p.length, s.length - q.length)) + "...";
      }
      return null;
    },
    function (s) {
      var p = "我想使用 ", q = " 技能";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return "I want to use the " + translateOne(s.slice(p.length, s.length - q.length)) + " skill";
      }
      return null;
    },
    function (s) {
      var p = "共找到 ", q = " 篇相关文献";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return s.slice(p.length, s.length - q.length) + " papers found";
      }
      return null;
    },
    function (s) {
      var p = "输入基因数: ", q = " | 显著条目数: ";
      var i = s.indexOf(p), j = s.indexOf(q);
      if (i === 0 && j > 0) {
        return "Input genes: " + s.slice(p.length, j) + " | Significant terms: " + s.slice(j + q.length);
      }
      return null;
    },
    function (s) {
      var p = "正在加载 ", q = " 的信息...";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return "Loading information for " + s.slice(p.length, s.length - q.length) + "...";
      }
      return null;
    },
    function (s) {
      var p = "未找到 ", q = " 的剪接事件";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return "No splicing events found for " + s.slice(p.length, s.length - q.length);
      }
      return null;
    },
    function (s) {
      var p = "报告生成失败 (", q = ")";
      if (s.indexOf(p) === 0 && s.slice(-q.length) === q) {
        return "Report generation failed (" + s.slice(p.length, s.length - q.length) + ")";
      }
      return null;
    },
    function (s) {
      var p = "API 错误: ";
      if (s.indexOf(p) === 0) return "API error: " + s.slice(p.length);
      return null;
    },
    function (s) {
      var p = "上传失败 (";
      if (s.indexOf(p) === 0) return "Upload failed (" + s.slice(p.length);
      return null;
    },
    function (s) {
      var p = "分析失败 (";
      if (s.indexOf(p) === 0) return "Analysis failed (" + s.slice(p.length);
      return null;
    },
    function (s) {
      var p = " 分析失败: ";
      if (s.indexOf(p) === 0) return " Analysis failed: " + s.slice(p.length);
      return null;
    },
    function (s) {
      var p = " 执行出错: ";
      if (s.indexOf(p) === 0) return " Execution error: " + s.slice(p.length);
      return null;
    },
    function (s) {
      var p = "操作失败：";
      if (s.indexOf(p) !== 0) return null;
      var out = "Operation failed: " + s.slice(p.length);
      return out
        .split("请检查：").join("Please check: ")
        .split("文件格式是否正确").join("whether the file format is correct")
        .split("文件大小是否过大").join("whether the file is too large")
        .split("网络连接是否正常").join("whether the network connection is working");
    },
    function (s) {
      var p = "分析请求失败：";
      if (s.indexOf(p) !== 0) return null;
      var out = "Analysis request failed: " + s.slice(p.length);
      var q = "（分析可能仍在后台运行，请稍后刷新查看）";
      if (out.slice(-q.length) === q) {
        out = out.slice(0, out.length - q.length) + " (the analysis may still be running in the background; refresh later)";
      }
      return out;
    }
  ];

  // 动态拼接文案（含数字/用户名等），用正则匹配后套模板。
  var PATTERN_RULES = [
    [/^共 ([\\d,]+) 个事件 · 每页 ([\\d,]+) 条 · 已按(.+?)排序$/, "About $1 events · $2 per page · sorted by $3"],
    [/^事件 ([\\d,]+)$/, "Events $1"],
    [/^显著 ([\\d,]+)$/, "Significant $1"],
    [/^·\\s*数据库 ([\\d.,]+ MB)$/, "· Database $1"],
    [/^(\\S+) · (.+?) · 输入格式 (\\S+) · ([\\d,]+) 个事件 \\/ ([\\d,]+) 个显著$/, "$1 · $2 · input $3 · $4 events / $5 significant"],
    [/^MHC-I 参考表：共 ([\\d,]+) 个等位基因（显示前 ([\\d,]+)）$/, "MHC-I reference table: $1 alleles (showing first $2)"],
    [/^IEDB 在线 · MHCflurry 未安装 · 参考表 class1 ([\\d,]+) \\/ class2 ([\\d,]+) · 已知表位 ([\\d,]+)$/, "IEDB online · MHCflurry not installed · reference class1 $1 / class2 $2 · known epitopes $3"],
    [/^IEDB 在线 · MHCflurry 已安装 · 参考表 class1 ([\\d,]+) \\/ class2 ([\\d,]+) · 已知表位 ([\\d,]+)$/, "IEDB online · MHCflurry installed · reference class1 $1 / class2 $2 · known epitopes $3"],
    [/^当前项目：(.+?)。将读取项目目录中的事件表和编码序列对照表。$/, "Current project: $1. Event tables and the coding-sequence table will be read from the project directory."],
    [/^(\\d+) \\/ (\\d+) 已连接$/, "$1 / $2 connected"],
    [/^连接方式：(.+)$/, "Connection: $1"],
    [/^数据目录：(.+)$/, "Data directory: $1"],
    [/^已打包（(.+?) MB）：(.+)$/, "Packaged ($1 MB): $2"],
    [/^正在执行阶段 (.+)$/, "Running stage $1"],
    [/^项目「(.+?)」的数据库记录、图表与报告目录都会被移除，且无法撤销。原始输入数据不会被删除。$/, "The database record, figures, and report folder for “$1” will be removed. This cannot be undone. Raw input data is not deleted."],
    [/^删除失败：HTTP (\\d+)$/, "Delete failed: HTTP $1"],
    [/^([\\d,]+) 行无效输入$/, "$1 invalid input lines"],
    [/^已保存，按这套映射可为 ([\\d,]+) 行样本生成肽。$/, "Saved; this mapping can be used for $1 sample rows."],
    [/^(.+?) · (.+?) · ([\\d,]+) 工具(（未连接）)?$/, "$1 · $2 · $3 tools$4"],
  ];

  function applyPatternRules(value) {
    for (var i = 0; i < PATTERN_RULES.length; i++) {
      var pattern = PATTERN_RULES[i][0];
      if (!pattern.test(value)) continue;
      return value.replace(pattern, PATTERN_RULES[i][1])
        .replace(/基因名/g, "gene name")
        .replace(/内置/g, "built-in")
        .replace(/（未连接）/g, " (not connected)");
    }
    return null;
  }

  var ATTRS = ["placeholder", "title", "aria-label"];
  var NL2 = String.fromCharCode(10, 10);
  var originalText = new WeakMap();
  var originalAttrs = new WeakMap();
  var lang = "zh";
  try {
    var saved = localStorage.getItem("epitoperank_lang");
    if (saved === "en" || saved === "zh" || saved === "zh-Hant") lang = saved;
  } catch (e) {}

  // 中文备注：保留原字符串首尾空白，仅替换中间修剪后的核心文本。
  function replaceTrimmed(text, out) {
    var trimmed = text.trim();
    var i = text.indexOf(trimmed);
    if (i < 0) return text;
    return text.slice(0, i) + out + text.slice(i + trimmed.length);
  }

  // 中文备注：将单段中文/英文界面文本按当前语言字典或繁简转换器翻译。
  function translateOne(text) {
    if (lang === "zh-Hant") return toTraditional(text);
    var trimmed = text.trim();
    if (!trimmed) return text;
    // 字典键统一按「空白归一化后的单行文本」查：HTML 里跨行书写的长句、
    // 以及带缩进/换行的模板文本都能命中同一个键。
    var key = trimmed.replace(/\\s+/g, " ");
    if (Object.prototype.hasOwnProperty.call(DICT, key)) {
      return replaceTrimmed(text, DICT[key]);
    }
    if (key !== trimmed && Object.prototype.hasOwnProperty.call(DICT, trimmed)) {
      return replaceTrimmed(text, DICT[trimmed]);
    }
    for (var i = 0; i < RULES.length; i++) {
      var out = RULES[i](key);
      if (!out && key !== trimmed) out = RULES[i](trimmed);
      if (out) return replaceTrimmed(text, out);
    }
    var patterned = applyPatternRules(key);
    if (!patterned && key !== trimmed) patterned = applyPatternRules(trimmed);
    if (patterned) return replaceTrimmed(text, patterned);
    return text;
  }

  // 中文备注：对整段文本执行当前目标语言的翻译或繁简转换。
  function translateText(text) {
    if (lang === "zh-Hant") return toTraditional(text);
    if (text.indexOf(NL2) === -1) return translateOne(text);
    return text.split(NL2).map(translateOne).join(NL2);
  }

  // 中文备注：缓存原始文本并翻译单个 DOM 文本节点的内容。
  function translateTextNode(node) {
    var parent = node.parentElement;
    if (!parent || parent.closest("script,style,[data-no-i18n]")) return;
    var original = originalText.get(node);
    if (original === undefined) {
      original = node.nodeValue;
      originalText.set(node, original);
    }
    var target = lang === "zh" ? original : translateText(original);
    if (node.nodeValue !== target) node.nodeValue = target;
  }

  // 中文备注：翻译元素上的 placeholder、title、aria-label 等可本地化属性。
  function translateAttrs(el) {
    if (el.closest("script,style,[data-no-i18n]")) return;
    var store = originalAttrs.get(el);
    if (!store) {
      store = {};
      originalAttrs.set(el, store);
    }
    for (var i = 0; i < ATTRS.length; i++) {
      var name = ATTRS[i];
      if (!el.hasAttribute(name)) continue;
      if (!Object.prototype.hasOwnProperty.call(store, name)) {
        store[name] = el.getAttribute(name);
      }
      var target = lang === "zh" ? store[name] : translateOne(store[name]);
      if (el.getAttribute(name) !== target) {
        el.setAttribute(name, target);
      }
    }
  }

  // 中文备注：递归遍历指定 DOM 子树并对所有可见文本节点与属性应用语言转换。
  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) {
      translateTextNode(root);
      return;
    }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1) translateAttrs(root);
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null);
    var node = walker.nextNode();
    while (node) {
      if (node.nodeType === 3) translateTextNode(node);
      else translateAttrs(node);
      node = walker.nextNode();
    }
  }

  var observer = new MutationObserver(function (mutations) {
    if (lang === "zh") return;
    for (var i = 0; i < mutations.length; i++) {
      var m = mutations[i];
      if (m.type === "characterData") {
        var node = m.target;
        var stored = originalText.get(node);
        var expected = stored === undefined ? undefined : (lang === "zh" ? stored : translateText(stored));
        if (node.nodeValue === expected) continue;
        originalText.set(node, node.nodeValue);
        translateTextNode(node);
      } else if (m.type === "attributes") {
        var el = m.target;
        if (!el || el.nodeType !== 1) continue;
        var store = originalAttrs.get(el);
        if (!store) {
          store = {};
          originalAttrs.set(el, store);
        }
        var name = m.attributeName;
        var current = el.getAttribute(name);
        var wanted = store[name] === undefined ? undefined : (lang === "zh" ? store[name] : translateOne(store[name]));
        if (current === wanted) continue;
        store[name] = current;
        translateAttrs(el);
      } else {
        for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
      }
    }
  });

  // 中文备注：同步翻译浏览器标签页标题（document.title）。
  function translateTitle() {
    var el = document.querySelector("title");
    if (!el) return;
    if (!el.dataset.zh) el.dataset.zh = el.textContent;
    el.textContent = lang === "zh" ? el.dataset.zh : translateOne(el.dataset.zh);
  }

  // 中文备注：切换全局界面语言（简体/繁体/英文），按需加载 opencc 并重绘全页文案。
  function applyLanguage(next) {
    lang = next === "en" || next === "zh-Hant" ? next : "zh";
    document.documentElement.lang = lang === "en" ? "en" : (lang === "zh-Hant" ? "zh-Hant" : "zh-CN");
    try {
      localStorage.setItem("epitoperank_lang", lang);
      document.cookie = "epitoperank_lang=" + lang + "; path=/; max-age=31536000; SameSite=Lax";
    } catch (e) {}
    var buttons = document.querySelectorAll(".lang-toggle button");
    for (var i = 0; i < buttons.length; i++) {
      var active = buttons[i].getAttribute("data-lang") === lang;
      buttons[i].classList.toggle("active", active);
      buttons[i].setAttribute("aria-pressed", active ? "true" : "false");
    }
    observer.disconnect();
    try {
      walk(document.body);
      translateTitle();
    } finally {
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ATTRS
      });
    }
    try {
      document.dispatchEvent(new CustomEvent("epitoperank:language", { detail: { lang: lang } }));
    } catch (e) {}
  }

  window.__epitoperankI18n = {
    apply: applyLanguage,
    translate: translateOne,
    translateText: translateText,
    getLang: function () { return lang; }
  };

  // 兜底：任何遗漏的 alert() 都转成应用内 toast，不再弹原生对话框。
  // 业务代码已显式调用 AppNotify；这里只覆盖第三方库或历史遗留调用。
  window.alert = function (message) {
    if (window.AppNotify) {
      window.AppNotify.toast(String(message), "info");
      return;
    }
    var notice = document.createElement("div");
    notice.setAttribute("role", "status");
    notice.textContent = lang === "zh" ? String(message) : translateText(String(message));
    notice.style.cssText = "position:fixed;right:24px;bottom:24px;z-index:99999;max-width:520px;padding:16px 20px;border-radius:var(--radius);background:var(--surface);color:var(--text);border:1px solid var(--border);box-shadow:var(--shadow-lg);white-space:pre-line;font-size:14px;cursor:pointer";
    notice.onclick = function () { notice.remove(); };
    document.body.appendChild(notice);
    setTimeout(function () { notice.remove(); }, 8000);
  };
  var nativeConfirm = window.confirm.bind(window);
  window.confirm = function (message) {
    return nativeConfirm(lang === "zh" ? String(message) : translateText(String(message)));
  };

  // 中文备注：页面加载完成后的统一初始化入口：恢复语言、动效偏好并加载首页数据。
  function init() {
    var buttons = document.querySelectorAll(".lang-toggle button");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        applyLanguage(this.getAttribute("data-lang"));
      });
      // 悬停/聚焦到「繁體中文」就先偷偷下载，点击时基本已经就绪。
      if (buttons[i].getAttribute("data-lang") === "zh-Hant") {
        buttons[i].addEventListener("pointerenter", ensureTraditionalConverter, { once: true });
        buttons[i].addEventListener("focus", ensureTraditionalConverter, { once: true });
      }
    }
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRS
    });
    applyLanguage(lang);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>

<script>
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
let workspaceAnimation = null;
// 中文备注：判断当前是否启用界面过渡动效（综合用户开关与系统减少动效偏好）。
function motionIsEnabled() { return !reducedMotionQuery.matches && localStorage.getItem('epitoperank.motion') !== 'off'; }
// 中文备注：将当前动效开关状态同步到根节点属性与切换按钮样式。
function syncMotionPreference() {
  const enabled = motionIsEnabled();
  document.body.classList.toggle('motion-paused', !enabled);
  const button = document.getElementById('motion-toggle');
  if (button) {
    button.textContent = reducedMotionQuery.matches ? '动态：系统关闭' : enabled ? '动态：开' : '动态：关';
    button.setAttribute('aria-pressed', String(enabled));
    button.disabled = reducedMotionQuery.matches;
  }
  if (!enabled) {
    document.getAnimations().forEach(animation => animation.cancel());
    document.querySelectorAll('.press-wave').forEach(wave => wave.remove());
  }
}
// 中文备注：切换界面过渡动效开关并持久化到 localStorage。
function toggleMotion() { localStorage.setItem('epitoperank.motion', motionIsEnabled() ? 'off' : 'on'); syncMotionPreference(); }

// 中文备注：主题管理（浅色/深色/跟随系统），并同步原生桌面窗口标题栏颜色。
const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
function getThemePref() { return localStorage.getItem('epitoperank.theme') || 'light'; }
function resolveTheme(pref) { return pref === 'dark' || (pref === 'system' && colorSchemeQuery.matches) ? 'dark' : 'light'; }
function syncDesktopTheme(effective) {
  try {
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_theme === 'function') {
      window.pywebview.api.set_theme(effective);
    }
  } catch (e) {}
}
function applyTheme(pref) {
  const effective = resolveTheme(pref);
  document.documentElement.dataset.theme = effective;
  document.querySelectorAll('#theme-seg button[data-theme-pref]').forEach(btn => {
    const active = btn.dataset.themePref === pref;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-pressed', String(active));
  });
  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.title = effective === 'dark' ? '切换为浅色实验室主题' : '切换为深色科研主题';
  }
  syncDesktopTheme(effective);
}
function setTheme(pref) {
  localStorage.setItem('epitoperank.theme', pref);
  applyTheme(pref);
}
function cycleTheme() {
  const current = resolveTheme(getThemePref());
  setTheme(current === 'dark' ? 'light' : 'dark');
}
colorSchemeQuery.addEventListener('change', () => { if (getThemePref() === 'system') applyTheme('system'); });
window.addEventListener('pywebviewready', () => syncDesktopTheme(resolveTheme(getThemePref())));

// 中文备注：侧边栏展开/紧凑图标模式切换并持久化。
function syncSidebarCompactUI() {
  const compact = document.documentElement.classList.contains('sidebar-compact');
  const btn = document.getElementById('sidebar-density-btn');
  if (btn) btn.textContent = compact ? '展开侧边栏' : '切换紧凑模式';
  setTimeout(syncFluidMarker, 60);
  setTimeout(syncFluidMarker, 340);
}
function toggleSidebarCompact(force) {
  const next = typeof force === 'boolean' ? force : !document.documentElement.classList.contains('sidebar-compact');
  document.documentElement.classList.toggle('sidebar-compact', next);
  localStorage.setItem('epitoperank.sidebar', next ? 'compact' : 'expanded');
  syncSidebarCompactUI();
}

// 中文备注：将侧边栏流体指示滑块定位到当前激活导航项的位置。
function syncFluidMarker() {
  const sidebar = document.getElementById('app-navigation');
  if (!sidebar) return;
  const active = sidebar.querySelector('.nav-item.active');
  const marker = sidebar.querySelector('.nav-fluid-marker');
  if (!active || !marker) return;
  const y = Math.round(active.getBoundingClientRect().top - sidebar.getBoundingClientRect().top + sidebar.scrollTop);
  marker.style.transform = 'translate3d(0,' + y + 'px,0)';
  marker.style.height = active.offsetHeight + 'px';
}
// 中文备注：工作区页面瞬时切换（避免大表格重排动画掉帧）。
function animateWorkspace(_previous, _current) {}
let quickReturnFocus = null;
// 中文备注：打开 Ctrl+K 快捷命令/页面切换面板并聚焦搜索框。
function openQuickSwitch() {
  const dialog = document.getElementById('quick-dialog');
  if (dialog.open) return;
  quickReturnFocus = document.activeElement;
  const results = document.getElementById('quick-results');
  results.replaceChildren();
  document.querySelectorAll('.nav-item').forEach(item => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'quick-result'; button.textContent = item.textContent.trim();
    if (item.dataset.page === state.currentPage) button.setAttribute('aria-current','page');
    button.onclick = () => { dialog.close(); if (item.dataset.detail) openProjectDetail(); else navigateTo(item.dataset.page); };
    results.appendChild(button);
  });
  const empty = document.createElement('p'); empty.className = 'quick-empty'; empty.id = 'quick-empty'; empty.textContent = '没有匹配的页面，试试「报告」或「设置」。'; empty.hidden = true; results.appendChild(empty);
  document.getElementById('quick-search').value = '';
  dialog.showModal(); document.getElementById('quick-search').focus();
}
// 中文备注：关闭快捷切换面板并恢复焦点。
function closeQuickSwitch() { document.getElementById('quick-dialog').close(); if (quickReturnFocus) quickReturnFocus.focus(); }
// 中文备注：根据输入关键词实时过滤快捷切换面板中的候选工作区列表。
function filterQuickSwitch() {
  const query = document.getElementById('quick-search').value.trim().toLocaleLowerCase();
  let matches = 0;
  document.querySelectorAll('.quick-result').forEach(button => { button.hidden = !button.textContent.toLocaleLowerCase().includes(query); if (!button.hidden) matches++; });
  document.getElementById('quick-empty').hidden = matches > 0;
}
const SHORTCUT_PAGES = ['dashboard', 'pipeline', 'explorer', 'neoantigen', 'visualization', 'report'];
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    if (document.body.classList.contains('detail-open')) closeProjectDetail();
    const uploadModal = document.getElementById('upload-modal');
    if (uploadModal && uploadModal.style.display === 'flex') closeUploadModal();
    const ingestModal = document.getElementById('ingest-modal');
    if (ingestModal && ingestModal.classList.contains('open')) closeIngestModal();
    if (document.getElementById('event-detail-modal') && typeof closeEventModal === 'function') closeEventModal();
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && document.getElementById('upload-modal').style.display !== 'flex' && !document.getElementById('ingest-modal').classList.contains('open')) {
    event.preventDefault(); openQuickSwitch();
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b' && !event.altKey) {
    const tag = (document.activeElement && document.activeElement.tagName || '').toLowerCase();
    if (tag !== 'input' && tag !== 'textarea') { event.preventDefault(); toggleSidebarCompact(); }
  }
  if (event.altKey && !event.ctrlKey && !event.metaKey && event.key >= '1' && event.key <= '6') {
    const target = SHORTCUT_PAGES[Number(event.key) - 1];
    if (target) { event.preventDefault(); navigateTo(target); }
  }
  if (event.key === 'ArrowDown' && document.getElementById('quick-dialog').open && event.target.id === 'quick-search') {
    const first = document.querySelector('.quick-result:not([hidden])');
    if (first) { event.preventDefault(); first.focus(); }
  }
});

reducedMotionQuery.addEventListener('change', syncMotionPreference);
window.addEventListener('resize', () => { document.querySelector('main').inert = window.innerWidth <= 768 && document.body.classList.contains('navigation-open'); syncFluidMarker(); document.getElementById('app-navigation').inert = window.innerWidth <= 768 && !document.body.classList.contains('navigation-open'); });
new ResizeObserver(syncFluidMarker).observe(document.getElementById('app-navigation'));
applyTheme(getThemePref());
syncSidebarCompactUI();
syncMotionPreference(); syncFluidMarker();
document.getElementById('app-navigation').inert = window.innerWidth <= 768;
</script>

<div id="toast-stack" role="region" aria-label="系统通知" aria-live="polite" aria-relevant="additions"></div>
<dialog id="app-dialog" class="app-dialog" aria-labelledby="app-dialog-title"></dialog>
<script>
// Track actual requests initiated by a click without changing request outcomes.
(() => {
  const indicator = document.createElement('div');
  indicator.id = 'request-indicator'; indicator.hidden = true;
  indicator.setAttribute('role', 'status'); indicator.setAttribute('aria-label', '正在加载');
  document.body.append(indicator);
  let activeButton = null, pending = 0, showTimer = 0;
  const counts = new WeakMap();
  document.addEventListener('click', event => {
    activeButton = event.target.closest('button');
    queueMicrotask(() => { activeButton = null; });
  }, true);
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const button = activeButton;
    if (button) { counts.set(button, (counts.get(button) || 0) + 1); button.setAttribute('aria-busy','true'); }
    if (++pending === 1) {
      clearTimeout(showTimer);
      showTimer = setTimeout(() => { if (pending > 0) indicator.hidden = false; }, 220);
    }
    try { return await originalFetch.apply(this,args); }
    finally {
      if (--pending === 0) { clearTimeout(showTimer); indicator.hidden = true; }
      if (button) { const remaining = counts.get(button) - 1; counts.set(button,remaining); if (!remaining) button.removeAttribute('aria-busy'); }
    }
  };
})();
</script>
</body>
</html>"""


# 中文备注：渲染单页 Web 界面 HTML（参数：title）
def render(title: str = "EpitopeRank") -> HTMLResponse:
    """Render the modern EpitopeRank web UI."""
    return HTMLResponse(content=_HTML.replace("__TITLE__", title))
