<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Workflow Workspace – Neon Crossroads</title>
  <style>
    :root {
      --bg: #f3f4f6;
      --panel: #ffffff;
      --ink: #0f172a;
      --muted: #6b7280;
      --accent: #f59e0b;
      --border: #e5e7eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      height: 64px;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: white;
      border-bottom: 1px solid var(--border);
    }
    header h1 {
      font-size: 18px;
      margin: 0;
      font-weight: 900;
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
      grid-template-columns: 280px 1fr 320px;
      height: calc(100vh - 64px);
    }
    .sidebar {
      background: white;
      border-right: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
    }
    .sidebar h2 {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 12px;
    }
    .chapter {
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      margin-bottom: 8px;
      cursor: pointer;
      background: #f9fafb;
    }
    .chapter.active {
      background: #fff7ed;
      border-color: var(--accent);
    }
    .chapter-title {
      font-weight: 700;
      font-size: 14px;
    }
    .chapter-meta {
      font-size: 11px;
      color: var(--muted);
      margin-top: 2px;
    }
    .canvas {
      padding: 24px;
      overflow-y: auto;
    }
    .canvas h2 {
      margin-top: 0;
      font-size: 20px;
    }
    .pages {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 16px;
    }
    .page {
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.08);
      overflow: hidden;
      cursor: pointer;
    }
    .page-thumb {
      height: 180px;
      background: linear-gradient(135deg, #c7d2fe, #818cf8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      font-weight: 900;
      color: #312e81;
    }
    .page-meta {
      padding: 10px;
      font-size: 12px;
    }
    .inspector {
      background: white;
      border-left: 1px solid var(--border);
      padding: 16px;
      overflow-y: auto;
    }
    .inspector h3 {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .section {
      margin-bottom: 20px;
    }
    button {
      width: 100%;
      padding: 10px;
      border-radius: 10px;
      border: none;
      background: linear-gradient(135deg, #f59e0b, #fbbf24);
      font-weight: 900;
      text-transform: uppercase;
      cursor: pointer;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <header>
    <div style="display:flex; align-items:center; gap:12px">
      <h1>Neon Crossroads</h1>
      <span class="pill">Draft</span>
    </div>
    <div style="font-size:12px; color:var(--muted)">4 Chapters · 32 Pages</div>
  </header>

  <div class="layout">
    <aside class="sidebar">
      <h2>Chapters</h2>
      <div class="chapter active">
        <div class="chapter-title">Chapter 1 · Neon Crossroads</div>
        <div class="chapter-meta">4 scenes · 12 pages</div>
      </div>
      <div class="chapter">
        <div class="chapter-title">Chapter 2 · First Lead</div>
        <div class="chapter-meta">3 scenes · 8 pages</div>
      </div>
      <div class="chapter">
        <div class="chapter-title">Chapter 3 · Broken Alibi</div>
        <div class="chapter-meta">2 scenes · 6 pages</div>
      </div>
    </aside>

    <main class="canvas">
      <h2>Chapter 1 · Neon Crossroads</h2>
      <div class="pages">
        <div class="page"><div class="page-thumb">1</div><div class="page-meta">Scene 1 · Page 1</div></div>
        <div class="page"><div class="page-thumb">2</div><div class="page-meta">Scene 1 · Page 2</div></div>
        <div class="page"><div class="page-thumb">3</div><div class="page-meta">Scene 2 · Page 3</div></div>
        <div class="page"><div class="page-thumb">4</div><div class="page-meta">Scene 2 · Page 4</div></div>
        <div class="page"><div class="page-thumb">+</div><div class="page-meta">Generate More</div></div>
      </div>
    </main>

    <aside class="inspector">
      <div class="section">
        <h3>Generation</h3>
        <button>Generate Pages</button>
        <button>Generate Chapters</button>
      </div>
      <div class="section">
        <h3>Chapter Info</h3>
        <div style="font-size:12px; color:var(--muted)">
          Scenes: 4<br />
          Pages Planned: 12<br />
          Pages Generated: 8
        </div>
      </div>
      <div class="section">
        <h3>Characters</h3>
        <div style="font-size:12px">Inspector Hale<br/>Witness Vega</div>
      </div>
    </aside>
  </div>
</body>
</html>
