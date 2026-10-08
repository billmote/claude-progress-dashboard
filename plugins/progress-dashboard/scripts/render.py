#!/usr/bin/env python3
"""Progress dashboard renderer. No model, no dependencies.

Reads every <root>/<project>/.dashboard/sessions/*.json and writes one page,
<root>/.dashboard/index.html, with a tab per project. Each project's own
.dashboard/index.html becomes a small page that forwards to it.

Usage: python3 render.py [ROOT]
ROOT defaults to the "root" in ~/.claude/progress-dashboard/style.json, else
the parent of the current folder. Style comes from <root>/.dashboard/style.json,
then ~/.claude/progress-dashboard/style.json, else defaults.
"""
import datetime, glob, html, json, os, sys, tempfile

DEFAULTS = {"theme": "dark", "density": "airy", "accent": "#4f8cff",
            "title": "Work Board", "owner": "you", "timezone": ""}
FORWARD_MARK = "progress-dashboard-forward"
FORWARD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta http-equiv="refresh" content="0; url=../../.dashboard/index.html">'
           '<!-- ' + FORWARD_MARK + ' --><title>Moved</title></head>'
           '<body style="font:15px sans-serif;padding:40px">The progress page is one level up: '
           '<a href="../../.dashboard/index.html">open it</a>.</body></html>\n')

def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def write_atomic(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)

def main():
    home_style = load(os.path.expanduser("~/.claude/progress-dashboard/style.json")) or {}
    root = sys.argv[1] if len(sys.argv) > 1 else home_style.get("root") or os.path.dirname(os.getcwd())
    root = os.path.abspath(os.path.expanduser(root))
    style = dict(DEFAULTS)
    style.update({k: v for k, v in home_style.items() if v})
    style.update({k: v for k, v in (load(os.path.join(root, ".dashboard", "style.json")) or {}).items() if v})
    if not style["timezone"]:
        style["timezone"] = os.environ.get("TZ") or "America/New_York"

    projects, bad = [], []
    for d in sorted(os.listdir(root), key=str.lower):
        pdir = os.path.join(root, d)
        if d.startswith(".") or not os.path.isdir(os.path.join(pdir, ".dashboard")):
            continue
        sessions = []
        for f in sorted(glob.glob(os.path.join(pdir, ".dashboard", "sessions", "*.json"))):
            s = load(f)
            if isinstance(s, dict):
                s.setdefault("id", os.path.basename(f)[:-5])
                sessions.append(s)
            else:
                bad.append(f)
        projects.append({"name": d, "sessions": sessions})
        fwd = os.path.join(pdir, ".dashboard", "index.html")
        try:
            cur = open(fwd).read()
        except Exception:
            cur = ""
        if FORWARD_MARK not in cur:
            write_atomic(fwd, FORWARD)

    data = json.dumps(projects, ensure_ascii=False, indent=0).replace("</", "<\\/")
    title = style["title"]
    first, _, rest = title.partition(" ")
    title_html = (html.escape(first) + " <span>" + html.escape(rest) + "</span>") if rest else html.escape(title)
    page = (TEMPLATE
            .replace("/*__DATA__*/[]", data)
            .replace("__BUILT__", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
            .replace("__TITLE_HTML__", title_html)
            .replace("__TITLE__", html.escape(title))
            .replace("__OWNER__", html.escape(style["owner"]))
            .replace("__TZ__", style["timezone"].replace("'", ""))
            .replace("__ACCENT__", style["accent"].replace(";", ""))
            .replace("__THEME__", "light" if style["theme"] == "light" else "dark")
            .replace("__DENSITY__", "dense" if style["density"] == "dense" else "airy"))
    out = os.path.join(root, ".dashboard", "index.html")
    write_atomic(out, page)
    n = sum(len(p["sessions"]) for p in projects)
    running = sum(1 for p in projects for s in p["sessions"] if not (s.get("finished") or s.get("status") == "finished"))
    print(f"{len(projects)} projects, {n} sessions, {running} running -> {out}")
    for f in bad:
        print(f"skipped (not valid JSON): {f}")

TEMPLATE = r'''<!doctype html>
<html lang="en" data-theme="__THEME__" data-density="__DENSITY__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
/* Layout: waiting-on-you on top, project tabs, a one-line session strip, then one session's detail. */
:root{
  --bg:#0e1319; --surface:#151c24; --surface-2:#1b242e; --line:#25303b; --line-2:#2f3c49;
  --fg:#e7edf3; --muted:#9aabbb; --faint:#6c7d8d;
  --accent:__ACCENT__; --accent-soft:color-mix(in srgb,var(--accent) 14%,transparent);
  --good:#72c79a; --warn:#e3b45e; --bad:#e8655d; --bad-soft:rgba(232,101,93,.13);
  --sans:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg)}
body{font:15px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding-inline:clamp(16px,4vw,40px);padding-block:28px 64px;display:flex;flex-direction:column;gap:34px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer;text-align:left}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
.tnum{font-variant-numeric:tabular-nums}

header.top{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
h1{margin:0;font-size:26px;font-weight:650;letter-spacing:-.01em}
h1 span{color:var(--accent)}
.clock{color:var(--muted);font-size:14px}
.clock b{color:var(--fg);font-weight:600}
.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint);font-weight:600;margin:0 0 12px}

/* Waiting on you */
.waiting{display:flex;flex-direction:column;gap:10px}
.wq{display:grid;grid-template-columns:1fr auto;gap:4px 18px;padding:16px 18px;background:var(--surface);border:1px solid var(--line);border-radius:12px;width:100%}
.wq:hover{border-color:var(--line-2);background:var(--surface-2)}
.wq .src{font-size:12.5px;color:var(--accent);grid-column:1}
.wq .when{font-size:12.5px;color:var(--faint);grid-column:2;grid-row:1;text-align:right;white-space:nowrap}
.wq .q{grid-column:1/-1;font-size:16px;font-weight:550;text-wrap:pretty}
.wq .def{grid-column:1/-1;font-size:13.5px;color:var(--muted)}
.wq .def em{font-style:normal;color:var(--faint)}
.none{color:var(--muted);padding:14px 18px;border:1px dashed var(--line);border-radius:12px}

/* Tabs */
.tabs{display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line)}
.tab{display:flex;align-items:center;gap:9px;padding:11px 16px 12px;border-bottom:2px solid transparent;margin-bottom:-1px;color:var(--muted);font-weight:550}
.tab:hover{color:var(--fg)}
.tab[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--accent)}
.tab .count{font-size:12px;padding:1px 8px;border-radius:999px;background:var(--surface-2);color:var(--muted);font-weight:600}
.tab[aria-selected="true"] .count{background:var(--accent-soft);color:var(--accent)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--bad);display:inline-block;flex:none}

/* Strip */
.strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.card{display:grid;grid-template-columns:1fr auto;align-items:center;gap:8px 14px;padding:14px 16px;background:var(--surface);border:1px solid var(--line);border-radius:12px;min-height:76px;width:100%}
.card:hover{background:var(--surface-2)}
.card[aria-current="true"]{border-color:var(--accent);background:var(--surface-2)}
.card .name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.card .meta{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted);white-space:nowrap}
.bar{grid-column:1/-1;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--faint)}
.track{flex:1;height:6px;border-radius:4px;background:var(--line);overflow:hidden}
.fill{height:100%;background:var(--accent);border-radius:4px}
.qbadge{color:var(--warn)}

/* Detail */
.detail{display:flex;flex-direction:column;gap:22px;min-height:420px}
.dhead{display:flex;flex-direction:column;gap:8px}
.dhead h2{margin:0;font-size:23px;font-weight:650;letter-spacing:-.005em;text-wrap:balance}
.sub{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--muted);font-size:13.5px}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:2px 10px;border-radius:999px;border:1px solid var(--line-2);color:var(--muted)}
.pill.working{color:var(--accent);border-color:color-mix(in srgb,var(--accent) 45%,transparent)}
.pill.done{color:var(--good);border-color:rgba(114,199,154,.4)}
.pill.stuck{color:var(--bad);border-color:rgba(232,101,93,.5)}
.now{font-size:16px}
.now b{color:var(--accent);font-weight:600}
.lede{font-size:15.5px;color:var(--fg);max-width:70ch}
.next{padding:12px 16px;border-radius:10px;background:var(--accent-soft);color:var(--fg);max-width:80ch}
.next b{color:var(--accent)}
.stuckbox{padding:14px 18px;border-radius:12px;background:var(--bad-soft);border:1px solid rgba(232,101,93,.35);display:flex;flex-direction:column;gap:6px}
.stuckbox h3{margin:0;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--bad)}
.stuckbox p{margin:0}

.cols{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:22px;align-items:start}
@media (max-width:820px){.cols{grid-template-columns:1fr}}
.col{display:flex;flex-direction:column;gap:22px;min-width:0}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px;min-width:0}
.panel h3{margin:0 0 12px;font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint);font-weight:600}

.steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.step{display:grid;grid-template-columns:22px 1fr auto;gap:2px 12px;padding:11px 0;border-top:1px solid var(--line)}
.step:first-child{border-top:0;padding-top:2px}
.step .ic{width:14px;height:14px;border-radius:50%;margin-top:4px;border:2px solid var(--faint)}
.step.done .ic{background:var(--good);border-color:var(--good)}
.step.working .ic{border-color:var(--accent);background:radial-gradient(circle,var(--accent) 0 3px,transparent 4px)}
.step.stuck .ic{background:var(--bad);border-color:var(--bad)}
.step .nm{font-weight:520}
.step.notstarted .nm{color:var(--muted)}
.step .st{font-size:12px;color:var(--faint);white-space:nowrap;padding-top:2px}
.step.done .st{color:var(--good)} .step.working .st{color:var(--accent)} .step.stuck .st{color:var(--bad)}
.step .nt{grid-column:2/-1;font-size:13.5px;color:var(--muted)}
.subs{grid-column:2/-1;list-style:none;margin:6px 0 0;padding:0 0 0 12px;border-left:1px solid var(--line);display:flex;flex-direction:column;gap:4px;font-size:13.5px;color:var(--muted)}
.subs .ok{color:var(--good)}

.files{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
.files li{display:flex;justify-content:space-between;gap:14px;align-items:baseline}
.files .fn{min-width:0;overflow-wrap:anywhere}
.files .ft{font-size:12.5px;color:var(--faint);white-space:nowrap;text-align:right}
.empty{color:var(--faint);font-size:14px}

.kv{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:8px 16px;margin:0}
.kv dt{color:var(--muted);font-size:13.5px}
.kv dd{margin:0;overflow-wrap:anywhere}
.kv dd.mono{font-family:var(--mono);font-size:13.5px}
.big{display:flex;flex-wrap:wrap;gap:18px 28px}
.big div{display:flex;flex-direction:column}
.big b{font-size:24px;font-weight:650;font-variant-numeric:tabular-nums}
.big span{font-size:12.5px;color:var(--muted)}
.big small{font-size:12px;color:var(--faint);max-width:22ch}
.hbars{display:flex;flex-direction:column;gap:10px}
.hb{display:grid;grid-template-columns:minmax(0,9rem) 1fr auto;gap:12px;align-items:center;font-size:13.5px}
.hb .track{height:8px}
.hb .v{font-variant-numeric:tabular-nums;color:var(--muted);white-space:nowrap}
.plist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.plist li{display:flex;justify-content:space-between;gap:12px}
.plist .s{font-size:12.5px;color:var(--muted)}
.plist .s.done{color:var(--good)} .plist .s.stuck{color:var(--bad)}
.ev{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:6px}
.log{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
.log li{display:grid;grid-template-columns:6.8rem 1fr;gap:12px;font-size:14px}
.log .lt{color:var(--faint);font-size:12.5px;padding-top:2px}
@media (max-width:520px){.log li{grid-template-columns:1fr;gap:0}.hb{grid-template-columns:1fr auto}.hb .track{grid-column:1/-1;grid-row:2}}

.finished{display:flex;flex-direction:column;gap:6px}
.frow{display:flex;justify-content:space-between;gap:14px;padding:9px 14px;border-radius:10px;width:100%;color:var(--muted)}
.frow:hover,.frow[aria-current="true"]{background:var(--surface);color:var(--fg)}
.frow .ft{font-size:12.5px;color:var(--faint);white-space:nowrap}
details.earlier summary{cursor:pointer;color:var(--faint);font-size:13px;padding:6px 0;list-style:none}
details.earlier summary::-webkit-details-marker{display:none}
details.earlier summary::before{content:"\25B8  "}
details.earlier[open] summary::before{content:"\25BE  "}
@media (prefers-reduced-motion:no-preference){.step.working .ic{animation:pulse 1.6s ease-in-out infinite}}
@keyframes pulse{50%{opacity:.45}}

/* Light theme */
html[data-theme="light"]{--bg:#f6f7f9;--surface:#ffffff;--surface-2:#f0f2f5;--line:#e1e5ea;--line-2:#cfd6de;--fg:#16202a;--muted:#55636f;--faint:#7c8893;--good:#2f8a57;--warn:#a86d0a;--bad:#c0392b;--bad-soft:rgba(192,57,43,.08);color-scheme:light}
/* Dense */
html[data-density="dense"] body{font-size:14px}
html[data-density="dense"] .wrap{gap:20px;padding-block:18px 40px}
html[data-density="dense"] .panel{padding:12px 14px}
html[data-density="dense"] .card{padding:10px 12px;min-height:60px}
html[data-density="dense"] .wq{padding:10px 14px}
html[data-density="dense"] .step{padding:7px 0}
html[data-density="dense"] .detail,html[data-density="dense"] .col{gap:14px}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <h1>__TITLE_HTML__</h1>
    <div class="clock">Now <b id="clock" class="tnum">--</b> <span id="tzabbr"></span></div>
  </header>

  <section aria-labelledby="wob">
    <p class="eyebrow" id="wob">Waiting on __OWNER__</p>
    <div class="waiting" id="waiting"></div>
  </section>

  <section>
    <nav class="tabs" id="tabs" role="tablist"></nav>
  </section>

  <section aria-label="Sessions">
    <p class="eyebrow" id="stripLabel">Running now</p>
    <div class="strip" id="strip"></div>
  </section>

  <section class="detail" id="detail" aria-live="polite"></section>

  <section aria-label="Finished">
    <p class="eyebrow">Finished today</p>
    <div class="finished" id="finished"></div>
  </section>
</div>

<script>
/* Built by render.py at __BUILT__. Do not edit: rerun render.py. */
const PROJECTS = /*__DATA__*/[];

const TZ = '__TZ__';
const TZ_ABBR = new Intl.DateTimeFormat('en-US',{timeZone:TZ,timeZoneName:'short'}).formatToParts(new Date()).find(p=>p.type==='timeZoneName').value;
const STUCK_MS = 15 * 60 * 1000;
const fDay = new Intl.DateTimeFormat('en-US', {timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit'});
const fTime = new Intl.DateTimeFormat('en-US', {timeZone: TZ, hour: 'numeric', minute: '2-digit'});
const fDate = new Intl.DateTimeFormat('en-US', {timeZone: TZ, weekday: 'short', month: 'short', day: 'numeric'});
const fClock = new Intl.DateTimeFormat('en-US', {timeZone: TZ, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', second: '2-digit'});

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ms = iso => { const t = Date.parse(iso); return isNaN(t) ? null : t; };
const dayKey = t => fDay.format(new Date(t));
function when(iso){ const t = ms(iso); if (t == null) return ''; const tm = fTime.format(t); return dayKey(t) === dayKey(Date.now()) ? tm : fDate.format(t) + ', ' + tm; }
function agoText(t){ const m = Math.floor((Date.now() - t) / 60000); if (m < 1) return 'just now'; if (m < 60) return m + ' min ago'; const h = Math.floor(m / 60); if (h < 24) return h + ' hr ago'; const d = Math.floor(h / 24); return d + (d === 1 ? ' day ago' : ' days ago'); }
function ago(iso){ const t = ms(iso); return t == null ? '' : `<span class="ago" data-t="${t}">${agoText(t)}</span>`; }

function normStatus(s){ s = String(s || '').toLowerCase(); if (s === 'done' || s === 'sent' || s === 'finished') return 'done'; if (s === 'working' || s === 'in progress' || s === 'running') return 'working'; if (s === 'stuck' || s === 'failed' || s === 'blocked') return 'stuck'; return 'notstarted'; }
const STATUS_WORD = {done: 'Done', working: 'Working', stuck: 'Stuck', notstarted: 'Not started'};

function linkFor(project, d){
  const raw = d.href || d.path || d.value || '';
  if (/^(https?|file):/i.test(raw)) return raw;
  if (raw.startsWith('/')) return 'file://' + encodeURI(raw);
  if (/\//.test(raw) || /\.[a-z0-9]{2,5}$/i.test(raw)) {
    const rel = raw.replace(/^(\.\.\/)+/, '').replace(/^\.\//, '');
    return '../' + encodeURIComponent(project) + '/' + encodeURI(rel);
  }
  return null;
}

function norm(s, project){
  const started = s.started || s.started_at;
  const last = s.last_update || s.lastUpdate || s.finished_at || s.finishedAt || started;
  const finished = !!s.finished || s.status === 'finished';
  const n = {
    raw: s, project, id: s.id, title: s.title || s.task || s.id, started, last,
    lastMs: ms(last) || 0, finished,
    finishedAt: s.finished_at || s.finishedAt || (finished ? last : null),
    doing: s.doing_now || s.doingNow || '',
    steps: (s.steps || []).map(st => ({name: st.name, status: normStatus(st.status), note: st.note || '', sub: (st.sub || []).map(x => ({name: x.name, status: normStatus(x.status)}))})),
    questions: (s.questions || []).map(q => ({text: q.text || q.q, def: q.default || '', at: q.at || last})),
    stuckList: (s.stuck || []).map(x => typeof x === 'string' ? x : (x.reason || x.text || '')).filter(Boolean),
    deliverables: (s.deliverables || []).map(d => ({name: d.name || d.label, shown: d.path || d.value || '', link: linkFor(project, d), at: d.at || d.time || ''}))
  };
  n.done = n.steps.filter(x => x.status === 'done').length;
  n.total = n.steps.length;
  return n;
}

const projects = PROJECTS.map(p => ({name: p.name, sessions: p.sessions.map(s => norm(s, p.name)).sort((a, b) => b.lastMs - a.lastMs)}));
const replaced = new Set(); projects.forEach(p => p.sessions.forEach(s => { if (s.raw.replaces_next_for) replaced.add(s.raw.replaces_next_for); }));

function isQuiet(s){ return !s.finished && Date.now() - s.lastMs > STUCK_MS; }
function isStuck(s){ return !s.finished && (isQuiet(s) || s.stuckList.length > 0 || s.steps.some(x => x.status === 'stuck')); }
function stuckReasons(s){
  const r = [];
  if (isQuiet(s)) r.push(`No word from this session since ${when(s.last)} ${TZ_ABBR} (${agoText(s.lastMs)}).`);
  return r.concat(s.stuckList);
}
function openAsks(s){
  const out = s.questions.map(q => ({q: q.text, def: q.def, at: q.at}));
  if (s.raw.next_for_bill && !replaced.has(s.id)) out.push({q: s.raw.next_for_bill, def: 'Nothing happens until you do it.', at: s.last});
  return out;
}

let sel = {project: null, session: null};
function readHash(){
  const h = decodeURIComponent(location.hash.slice(1) || '');
  const i = h.indexOf('/');
  const pn = i < 0 ? h : h.slice(0, i), sid = i < 0 ? '' : h.slice(i + 1);
  let p = projects.find(x => x.name === pn);
  if (!p) p = projects.slice().sort((a, b) => (b.sessions[0]?.lastMs || 0) - (a.sessions[0]?.lastMs || 0))[0];
  let s = p.sessions.find(x => x.id === sid) || p.sessions[0] || null;
  sel = {project: p.name, session: s ? s.id : null};
}
function writeHash(){
  const h = '#' + encodeURIComponent(sel.project) + (sel.session ? '/' + encodeURIComponent(sel.session) : '');
  try { history.replaceState(null, '', h); } catch (e) { location.hash = h; }
}
function choose(project, session){
  const p = projects.find(x => x.name === project);
  sel = {project, session: session || (p.sessions[0] ? p.sessions[0].id : null)};
  writeHash(); render();
}

function renderWaiting(){
  const items = [];
  projects.forEach(p => p.sessions.forEach(s => openAsks(s).forEach(a => items.push({p, s, a}))));
  items.sort((x, y) => (ms(y.a.at) || 0) - (ms(x.a.at) || 0));
  const el = document.getElementById('waiting');
  if (!items.length) { el.innerHTML = '<div class="none">Nothing is waiting on you.</div>'; return; }
  el.innerHTML = items.map(({p, s, a}) => `
    <button class="wq" data-p="${esc(p.name)}" data-s="${esc(s.id)}">
      <span class="src">${esc(p.name)} · ${esc(s.title)}</span>
      <span class="when tnum">${a.at ? 'Asked ' + esc(when(a.at)) + ' · ' + ago(a.at) : ''}</span>
      <span class="q">${esc(a.q)}</span>
      ${a.def ? `<span class="def"><em>Meanwhile:</em> ${esc(a.def)}</span>` : ''}
    </button>`).join('');
}

function renderTabs(){
  document.getElementById('tabs').innerHTML = projects.map(p => {
    const running = p.sessions.filter(s => !s.finished).length;
    const alert = p.sessions.some(s => isStuck(s) || openAsks(s).length);
    return `<button class="tab" role="tab" aria-selected="${p.name === sel.project}" data-p="${esc(p.name)}">
      ${alert ? '<span class="dot" title="Something stuck or a question open"></span>' : ''}
      <span>${esc(p.name)}</span><span class="count tnum" title="Sessions running">${running} running</span></button>`;
  }).join('');
}

function renderStrip(p){
  const el = document.getElementById('strip');
  const running = p.sessions.filter(s => !s.finished);
  document.getElementById('stripLabel').textContent = 'Running now';
  if (!p.sessions.length) { el.innerHTML = '<div class="none">No sessions yet</div>'; return; }
  if (!running.length) { el.innerHTML = '<div class="none">Nothing running right now.</div>'; return; }
  el.innerHTML = running.map(s => {
    const pct = s.total ? Math.round(100 * s.done / s.total) : 0;
    const q = openAsks(s).length;
    return `<button class="card" aria-current="${s.id === sel.session}" data-p="${esc(p.name)}" data-s="${esc(s.id)}">
      <span class="name" title="${esc(s.title)}">${esc(s.title)}</span>
      <span class="meta">${isStuck(s) ? '<span class="dot" title="Stuck"></span>' : ''}<span class="${q ? 'qbadge' : ''}">${q} ${q === 1 ? 'question' : 'questions'}</span></span>
      <span class="bar"><span class="track"><span class="fill" style="width:${pct}%"></span></span><span class="tnum">${s.done} of ${s.total}</span></span>
    </button>`;
  }).join('');
}

function kvRows(rows, title){
  return `<div class="panel"><h3>${esc(title)}</h3><dl class="kv">${rows.map(r => `<dt>${esc(r.label)}</dt><dd class="${r.mono ? 'mono tnum' : ''}">${esc(r.value)}</dd>`).join('')}</dl></div>`;
}
const LABELS = {total: 'Total', window: 'Dates'};

function extras(s){
  const r = s.raw, out = [];
  if (r.facts && r.facts.length) {
    const rows = r.facts.map(f => Array.isArray(f) ? (/^[\d$,.%]+$/.test(String(f[0])) ? {label: f[1], value: f[0]} : {label: f[0], value: f[1]}) : f);
    out.push(kvRows(rows, r.facts_title || 'Key facts'));
  }
  if (r.results) out.push(`<div class="panel"><h3>${esc(r.results.title || 'Results')}</h3><div class="big">${r.results.items.map(i => `<div><b>${esc(i.value)}</b><span>${esc(i.label)}</span>${i.note ? `<small>${esc(i.note)}</small>` : ''}</div>`).join('')}</div></div>`);
  if (r.load) { const pct = Math.round(100 * r.load.done / r.load.total); out.push(`<div class="panel"><h3>${esc(r.load.title || 'Progress')}</h3><div class="hbars"><div class="hb"><span>${r.load.done} of ${r.load.total}</span><span class="track"><span class="fill" style="width:${pct}%"></span></span><span class="v">${r.load.failed || 0} failed</span></div></div>${r.load.note ? `<p class="empty" style="margin:12px 0 0">${esc(r.load.note)}</p>` : ''}</div>`); }
  if (r.audience) {
    const a = r.audience, max = Math.max(...a.parts.map(x => x.count));
    out.push(`<div class="panel"><h3>${esc(a.title || 'Who it went to')}</h3><div class="hbars">${a.parts.map(x => `<div class="hb"><span>${esc(x.name)}</span><span class="track"><span class="fill" style="width:${Math.round(100 * (x.sent != null ? x.sent : x.count) / max)}%"></span></span><span class="v">${x.sent != null ? `${x.sent} of ${x.count} ${esc(a.sent_label || 'sent')}` : `${x.count} ${esc(a.unit || '')}`}</span></div>`).join('')}</div>${a.note ? `<p class="empty" style="margin:12px 0 0">${esc(a.note)}</p>` : ''}</div>`);
  }
  if (r.people) out.push(`<div class="panel"><h3>${esc(r.people.title || 'People')}</h3><ul class="plist">${r.people.names.map(n => `<li><span>${esc(n.name)}</span><span class="s ${normStatus(n.status)}">${esc(n.note)}</span></li>`).join('')}</ul></div>`);
  if (r.pieces) out.push(`<div class="panel"><h3>Pieces</h3><ul class="plist">${r.pieces.map(n => `<li><span>${esc(n.name)}</span><span class="s ${normStatus(n.status)}">${n.status === 'sent' ? 'Sent' : esc(STATUS_WORD[normStatus(n.status)])}</span></li>`).join('')}</ul></div>`);
  if (r.evidence) out.push(`<div class="panel"><h3>The evidence</h3><ul class="ev">${r.evidence.map(e => `<li>${esc(e)}</li>`).join('')}</ul></div>`);
  (r.panels || []).forEach(p => out.push(kvRows(p.rows, p.title)));
  if (r.schedule) out.push(kvRows(Object.entries(r.schedule).map(([k, v]) => ({label: LABELS[k] || k, value: v})), 'Schedule'));
  if (r.plan) out.push(kvRows(Object.entries(r.plan).map(([k, v]) => ({label: LABELS[k] || k, value: v})), 'What was planned'));
  return out.join('');
}

function renderDetail(p){
  const el = document.getElementById('detail');
  const s = p.sessions.find(x => x.id === sel.session);
  if (!s) { el.innerHTML = ''; return; }
  const stuck = isStuck(s);
  const state = s.finished ? 'done' : stuck ? 'stuck' : 'working';
  const stateWord = s.finished ? 'Finished' : stuck ? 'Stuck' : 'Working';
  const reasons = stuckReasons(s);
  const r = s.raw;
  const steps = s.steps.map(st => `<li class="step ${st.status}"><span class="ic" aria-hidden="true"></span><span class="nm">${esc(st.name)}</span><span class="st">${STATUS_WORD[st.status]}</span>${st.note ? `<span class="nt">${esc(st.note)}</span>` : ''}${st.sub.length ? `<ul class="subs">${st.sub.map(x => `<li><span class="${x.status === 'done' ? 'ok' : ''}">${x.status === 'done' ? 'Done' : STATUS_WORD[x.status]}</span> · ${esc(x.name)}</li>`).join('')}</ul>` : ''}</li>`).join('');
  const files = s.deliverables.length ? `<ul class="files">${s.deliverables.map(d => `<li><span class="fn">${d.link ? `<a href="${esc(d.link)}" target="_blank" rel="noopener">${esc(d.name)}</a>` : `${esc(d.name)}: <span class="empty">${esc(d.shown)}</span>`}</span><span class="ft tnum">${d.at ? esc(when(d.at)) + '<br>' + ago(d.at) : ''}</span></li>`).join('')}</ul>` : '<p class="empty">Nothing to open yet.</p>';
  const log = r.log && r.log.length ? `<div class="panel"><h3>What happened</h3><ul class="log">${r.log.slice().reverse().map(l => `<li><span class="lt tnum">${esc(when(l.at))}</span><span>${esc(l.text)}</span></li>`).join('')}</ul></div>` : '';
  el.innerHTML = `
    <div class="dhead">
      <h2>${esc(s.title)}</h2>
      <div class="sub tnum"><span class="pill ${state}">${stateWord}</span>
        <span>Started ${esc(when(s.started))}</span>
        <span>${s.finished ? 'Finished ' + esc(when(s.finishedAt)) + ' · ' + ago(s.finishedAt) : 'Last update ' + esc(when(s.last)) + ' · ' + ago(s.last)}</span>
        <span>${s.done} of ${s.total} steps done</span></div>
    </div>
    ${!s.finished && s.doing ? `<div class="now">Doing now: <b>${esc(s.doing)}</b></div>` : ''}
    ${r.summary || r.outcome ? `<div class="lede">${esc(r.outcome || r.summary)}</div>` : ''}
    ${r.next_for_bill && !replaced.has(s.id) ? `<div class="next"><b>Your next step:</b> ${esc(r.next_for_bill)}</div>` : ''}
    ${r.deadline_label ? `<div class="sub">${esc(r.deadline_label)}</div>` : ''}
    ${reasons.length ? `<div class="stuckbox"><h3>${s.finished ? 'Left unresolved' : 'Stuck'}</h3>${reasons.map(x => `<p>${esc(x)}</p>`).join('')}</div>` : ''}
    <div class="cols">
      <div class="col"><div class="panel"><h3>Steps</h3><ol class="steps">${steps}</ol></div>${log}</div>
      <div class="col"><div class="panel"><h3>Latest files</h3>${files}</div>${extras(s)}</div>
    </div>`;
}

function renderFinished(p){
  const el = document.getElementById('finished');
  const today = dayKey(Date.now());
  const fin = p.sessions.filter(s => s.finished);
  const todays = fin.filter(s => s.finishedAt && dayKey(ms(s.finishedAt)) === today);
  const older = fin.filter(s => !todays.includes(s));
  const row = s => `<button class="frow" aria-current="${s.id === sel.session}" data-p="${esc(p.name)}" data-s="${esc(s.id)}"><span>${esc(s.title)}</span><span class="ft tnum">${esc(when(s.finishedAt))}</span></button>`;
  let open = false; try { open = sessionStorage.getItem('wb-earlier') === '1'; } catch (e) {}
  el.innerHTML = (todays.length ? todays.map(row).join('') : '<div class="empty" style="padding:4px 0">Nothing finished yet today.</div>') +
    (older.length ? `<details class="earlier" ${open ? 'open' : ''}><summary>Earlier (${older.length})</summary>${older.map(row).join('')}</details>` : '');
  const d = el.querySelector('details');
  if (d) d.addEventListener('toggle', () => { try { sessionStorage.setItem('wb-earlier', d.open ? '1' : '0'); } catch (e) {} });
}

function render(){
  const p = projects.find(x => x.name === sel.project);
  renderWaiting(); renderTabs(); renderStrip(p); renderDetail(p); renderFinished(p);
}

document.addEventListener('click', e => {
  const b = e.target.closest('[data-p]');
  if (!b) return;
  choose(b.dataset.p, b.dataset.s || null);
  if (b.classList.contains('wq') || b.classList.contains('frow')) document.getElementById('detail').scrollIntoView({behavior: 'smooth', block: 'start'});
});
window.addEventListener('hashchange', () => { readHash(); render(); });

function tick(){
  document.getElementById('clock').textContent = fClock.format(new Date());
  document.getElementById('tzabbr').textContent = TZ_ABBR;
  document.querySelectorAll('.ago').forEach(a => { a.textContent = agoText(+a.dataset.t); });
}

readHash(); writeHash(); render(); tick();
setInterval(tick, 1000);
try { const y = sessionStorage.getItem('wb-scroll'); if (y) window.scrollTo(0, +y); } catch (e) {}
window.addEventListener('beforeunload', () => { try { sessionStorage.setItem('wb-scroll', String(window.scrollY)); } catch (e) {} });
setTimeout(() => location.reload(), 10000);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
