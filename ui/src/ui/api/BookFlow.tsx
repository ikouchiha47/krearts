<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Story Engine – Workflow Workspace</title>
  <style>
    :root {
      --bg: #020617;
      --panel: #0f172a;
      --surface: #020617;
      --ink: #f8fafc;
      --muted: #94a3b8;
      --accent: #f59e0b;
      --border: #1e293b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: linear-gradient(180deg, #0b1020, #020617);
      color: var(--ink);
    }
    header {
      height: 64px;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #020617;
      border-bottom: 1px solid var(--border);
    }
    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      background: #fff7ed;
      color: #92400e;
      font-size: 12px;
      font-weight: 700;
    }
    .layout {
      display: grid;
      grid-template-columns: 260px 1fr 320px;
      height: calc(100vh - 64px);
    }
    /* LEFT */
    .sidebar {
      background: #020617;
      border-right: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
    }
    .chapter {
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      margin-bottom: 8px;
      cursor: pointer;
    }
    .chapter.active { border-color: var(--accent); background: rgba(245,158,11,0.12); }

    /* CENTER */
    .canvas {
      padding: 20px 24px;
      overflow-y: auto;
    }
    .view-tabs { display: flex; gap: 8px; margin-bottom: 16px; }
    .tab {
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid var(--border);
      cursor: pointer;
      color: var(--muted);
    }
    .tab.active { background: var(--accent); color: black; border-color: var(--accent); }

    .story, .pages, .timeline, .graph {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
    }
    .story-section {
      background: #020617;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
    }

    .pages { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px,1fr)); gap: 16px; }
    .page { background: #020617; border-radius: 14px; border: 1px solid var(--border); cursor: pointer; }
    .page-thumb { height: 160px; display:flex; align-items:center; justify-content:center; font-size:32px; background:#818cf8; }
    .page.pending .page-thumb { background:#334155; }
    .page-meta { padding: 10px; font-size: 12px; }

    .timeline-row { display:flex; gap:8px; margin-bottom:12px; }
    .timeline-block { background:#fde68a; padding:6px 10px; border-radius:6px; font-size:11px; }

    .graph { position: relative; height: 520px; }
    .graph-node {
      position: absolute;
      background: #020617;
      border: 2px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      min-width: 160px;
      text-align: center;
    }
    .graph-node.main { border-color: var(--accent); }
    .graph-node.chapter { border-color: #38bdf8; }
    .graph-node.spinoff { border-color: #f472b6; }

    /* RIGHT – CHARACTERS */
    .character-panel {
      background: #020617;
      border-left: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
    }
    .character-grid { display:grid; gap:16px; }
    .character-card img { width:100%; height:160px; object-fit:cover; border-radius:12px; }
    .character-card strong { display:block; margin-top:8px; }
  </style>
</head>
<body>
<header>
  <div style="display:flex; gap:12px; align-items:center">
    <strong>Neon Crossroads</strong>
    <span class="pill">Draft</span>
  </div>
  <div style="font-size:12px; color:var(--muted)">4 Chapters · 32 Pages</div>
</header>

<div class="layout">
  <aside class="sidebar">
    <div class="chapter active">Chapter 1 · Neon Crossroads</div>
    <div class="chapter">Chapter 2 · First Lead</div>
    <div class="chapter">Chapter 3 · Broken Alibi</div>
  </aside>

  <main class="canvas">
    <div class="view-tabs">
      <div class="tab active">Story</div>
      <div class="tab">Pages</div>
      <div class="tab">Timeline</div>
      <div class="tab">Story Graph</div>
    </div>

    <div class="story">
      <div class="story-section">
        <h3>Overview</h3>
        <p>Neon Crossroads is a neon‑soaked crime noir following Inspector Hale.</p>
      </div>
      <div class="story-section"><h4>Chapter 1</h4><p>A body, a broken streetlight.</p></div>
      <div class="story-section"><h4>Chapter 2</h4><p>The first real suspect surfaces.</p></div>
    </div>

    <div class="pages" style="display:none">
      <div class="page"><div class="page-thumb">1</div><div class="page-meta">Scene 1 · Page 1</div></div>
      <div class="page"><div class="page-thumb">2</div><div class="page-meta">Scene 1 · Page 2</div></div>
      <div class="page pending"><div class="page-thumb">+</div><div class="page-meta">Generate pages</div></div>
    </div>

    <div class="timeline" style="display:none">
      <div class="timeline-row"><strong>Chapter 1</strong><div class="timeline-block">1</div><div class="timeline-block">2</div></div>
    </div>

    <div class="graph" style="display:none">
      <div class="graph-node main" style="top:40px; left:40%">Main Story</div>
      <div class="graph-node chapter" style="top:180px; left:20%">Chapter 1</div>
      <div class="graph-node chapter" style="top:180px; left:45%">Chapter 2</div>
      <div class="graph-node spinoff" style="top:340px; left:45%">Spinoff</div>
    </div>
  </main>

  <aside class="character-panel">
    <h3>Characters</h3>
    <div class="character-grid">
      <div class="character-card"><img src="https://images.unsplash.com/photo-1603415526960-f7e0328c63b1?w=400" /><strong>Inspector Hale</strong><span>Protagonist</span></div>
      <div class="character-card"><img src="https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=400" /><strong>Witness Vega</strong><span>Witness</span></div>
    </div>
  </aside>
</div>

<script>
  const tabs = document.querySelectorAll('.tab');
  const views = {
    'Story': document.querySelector('.story'),
    'Pages': document.querySelector('.pages'),
    'Timeline': document.querySelector('.timeline'),
    'Story Graph': document.querySelector('.graph'),
  };

  tabs.forEach(tab => {
    tab.onclick = () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      Object.values(views).forEach(v => v.style.display = 'none');
      views[tab.textContent].style.display = tab.textContent === 'Pages' ? 'grid' : 'block';
    };
  });
</script>
</body>
</html>
