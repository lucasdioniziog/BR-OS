// ============================================================
//  Dashboard de Atendimento — servidor único (Express + HTML)
//  1. npm install express node-fetch cors
//  2. node dashboard.js
//  3. Abra http://localhost:3000
// ============================================================

const express = require("express");
const cors    = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

// ─── CONFIG ────────────────────────────────────────────────
// Troque para a URL e token reais quando tiver acesso à API
const USE_MOCK  = true;          // false → chama API_URL
const API_URL   = "https://api.empresa.com/atendimentos";
const API_TOKEN = "SEU_TOKEN_AQUI";
// ───────────────────────────────────────────────────────────

// ─── DADOS MOCK ────────────────────────────────────────────
const MOCK = (() => {
  const assuntos  = ["Cancelamento","Cobrança","Suporte Técnico","Dúvida","Reclamação","Elogio"];
  const nomes     = ["João","Maria","Pedro","Ana","Carlos","Beatriz","Lucas","Fernanda","Rafael","Juliana"];
  const registros = [];
  for (let i = 0; i < 120; i++) {
    registros.push({
      id:        i + 1,
      cliente:   nomes[Math.floor(Math.random() * nomes.length)] + " " + (Math.floor(Math.random() * 900) + 100),
      assunto:   assuntos[Math.floor(Math.random() * assuntos.length)],
      tempo:     +(Math.random() * 12 + 1).toFixed(2),   // minutos
      resolvido: Math.random() > 0.25,
      data:      new Date(Date.now() - Math.random() * 7 * 864e5).toISOString()
    });
  }
  return registros;
})();

// ─── PROXY / MOCK ──────────────────────────────────────────
app.get("/atendimentos", async (req, res) => {
  if (USE_MOCK) return res.json(MOCK);

  try {
    // node-fetch v2 (CommonJS)
    const fetch    = (...a) => import("node-fetch").then(m => m.default(...a));
    const response = await fetch(API_URL, {
      headers: { Authorization: `Bearer ${API_TOKEN}` }
    });
    if (!response.ok) return res.status(response.status).json({ error: "Erro na API externa" });
    res.json(await response.json());
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Erro ao buscar dados" });
  }
});

app.post("/atendimentos", async (req, res) => {
  if (USE_MOCK) return res.json({ success: true, mock: true });

  try {
    const fetch    = (...a) => import("node-fetch").then(m => m.default(...a));
    const response = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${API_TOKEN}` },
      body:    JSON.stringify(req.body)
    });
    res.json(await response.json());
  } catch (err) {
    res.status(500).json({ error: "Erro ao enviar dados" });
  }
});

// ─── FRONTEND ──────────────────────────────────────────────
app.get("/", (_, res) => res.send(/* html */`<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard · Atendimento</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
/* ── Reset & Base ───────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:      #070d1a;
  --surface: #0e1a2e;
  --border:  #1c2f4a;
  --accent:  #00e5ff;
  --accent2: #7c3aed;
  --green:   #22d3a5;
  --yellow:  #fbbf24;
  --red:     #f87171;
  --text:    #e2eaf4;
  --muted:   #60748a;
  --font-display: 'Syne', sans-serif;
  --font-mono:    'Space Mono', monospace;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-display);
  min-height: 100vh;
  padding: 32px 28px 60px;
  background-image:
    radial-gradient(ellipse 60% 40% at 80% 0%, rgba(0,229,255,.06) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 20% 100%, rgba(124,58,237,.07) 0%, transparent 70%);
}

/* ── Header ─────────────────────────────────────────────── */
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 20px;
}
header h1 {
  font-size: clamp(1.3rem, 3vw, 1.9rem);
  font-weight: 800;
  letter-spacing: -.5px;
}
header h1 span { color: var(--accent); }
#statusBadge {
  font-family: var(--font-mono);
  font-size: .72rem;
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(34,211,165,.12);
  color: var(--green);
  border: 1px solid rgba(34,211,165,.3);
  display: flex;
  align-items: center;
  gap: 6px;
}
#statusBadge::before {
  content: '';
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%,100% { opacity:1; }
  50%      { opacity:.3; }
}

/* ── KPI Grid ───────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px 18px;
  position: relative;
  overflow: hidden;
  transition: transform .2s, border-color .2s;
}
.kpi:hover { transform: translateY(-3px); border-color: var(--accent); }
.kpi::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--kpi-color, var(--accent));
  opacity: .8;
}
.kpi-label {
  font-size: .72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--muted);
  margin-bottom: 10px;
}
.kpi-value {
  font-family: var(--font-mono);
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--kpi-color, var(--accent));
  line-height: 1;
}
.kpi-sub {
  font-size: .7rem;
  color: var(--muted);
  margin-top: 6px;
}

/* Ranking especial */
#kpiRanking .kpi-value { font-size: 1.1rem; }

/* ── Charts ─────────────────────────────────────────────── */
.charts {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}
@media(max-width:720px) { .charts { grid-template-columns: 1fr; } }

.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 20px;
}
.chart-title {
  font-size: .78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  margin-bottom: 16px;
}

/* ── Table ──────────────────────────────────────────────── */
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 20px;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: .82rem;
}
thead th {
  text-align: left;
  font-size: .68rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
tbody tr {
  border-bottom: 1px solid rgba(255,255,255,.04);
  transition: background .15s;
}
tbody tr:hover { background: rgba(255,255,255,.03); }
tbody td { padding: 10px 6px; }
.badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 20px;
  font-size: .67rem;
  font-weight: 600;
}
.badge-ok  { background:rgba(34,211,165,.15); color:var(--green); }
.badge-err { background:rgba(248,113,113,.15); color:var(--red); }

/* ── Loader ─────────────────────────────────────────────── */
#loader {
  position: fixed; inset: 0;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 999;
  gap: 16px;
  transition: opacity .4s;
}
#loader.hide { opacity: 0; pointer-events: none; }
.spinner {
  width: 42px; height: 42px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
#loader p { color: var(--muted); font-size: .85rem; }

/* ── Fade-in ────────────────────────────────────────────── */
.fade-in { animation: fadeIn .5s ease both; }
@keyframes fadeIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
</style>
</head>
<body>

<div id="loader">
  <div class="spinner"></div>
  <p>Carregando atendimentos...</p>
</div>

<header class="fade-in">
  <h1>📊 Dashboard de <span>Atendimento</span></h1>
  <div id="statusBadge">AO VIVO</div>
</header>

<!-- KPIs -->
<div class="kpi-grid fade-in" style="animation-delay:.1s">
  <div class="kpi" style="--kpi-color:var(--accent)">
    <div class="kpi-label">TMA</div>
    <div class="kpi-value" id="vTma">—</div>
    <div class="kpi-sub">Tempo médio (min)</div>
  </div>
  <div class="kpi" style="--kpi-color:var(--accent2)">
    <div class="kpi-label">Atendimentos</div>
    <div class="kpi-value" id="vTotal">—</div>
    <div class="kpi-sub">Total no período</div>
  </div>
  <div class="kpi" style="--kpi-color:var(--green)">
    <div class="kpi-label">Resolvidos</div>
    <div class="kpi-value" id="vResolvidos">—</div>
    <div class="kpi-sub">Taxa de resolução</div>
  </div>
  <div class="kpi" style="--kpi-color:var(--yellow)">
    <div class="kpi-label">Retornos</div>
    <div class="kpi-value" id="vRetorno">—</div>
    <div class="kpi-sub">Clientes que voltaram</div>
  </div>
  <div class="kpi" style="--kpi-color:var(--accent)">
    <div class="kpi-label">Clientes Retidos</div>
    <div class="kpi-value" id="vRetidos">—</div>
    <div class="kpi-sub">Único contato</div>
  </div>
  <div class="kpi" id="kpiRanking">
    <div class="kpi-label">Ranking</div>
    <div class="kpi-value" id="vRanking">—</div>
    <div class="kpi-sub" id="vScore">Score: —</div>
  </div>
</div>

<!-- Charts -->
<div class="charts fade-in" style="animation-delay:.2s">
  <div class="chart-card">
    <div class="chart-title">Atendimentos por Assunto</div>
    <canvas id="chartAssuntos" height="200"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Resolução (Pizza)</div>
    <canvas id="chartPizza" height="200"></canvas>
  </div>
</div>

<!-- Tabela recentes -->
<div class="table-card fade-in" style="animation-delay:.3s">
  <div class="chart-title" style="margin-bottom:14px">Últimos 10 Atendimentos</div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Cliente</th>
        <th>Assunto</th>
        <th>Tempo (min)</th>
        <th>Status</th>
        <th>Data</th>
      </tr>
    </thead>
    <tbody id="tabelaBody"></tbody>
  </table>
</div>

<script>
const fmt = n => n.toLocaleString("pt-br");
const fmtDate = s => new Date(s).toLocaleDateString("pt-br", { day:"2-digit", month:"2-digit", hour:"2-digit", minute:"2-digit" });

async function init() {
  try {
    const res  = await fetch("/atendimentos");
    const data = await res.json();

    if (!Array.isArray(data)) throw new Error("Resposta inválida da API");

    // ── KPIs ──
    const total      = data.length;
    const totalTempo = data.reduce((a, d) => a + (d.tempo || 0), 0);
    const tma        = total ? (totalTempo / total).toFixed(2) : 0;

    const resolvidos = data.filter(d => d.resolvido).length;
    const taxaRes    = total ? Math.round(resolvidos / total * 100) : 0;

    const clientesMap = {};
    data.forEach(d => { clientesMap[d.cliente] = (clientesMap[d.cliente] || 0) + 1; });
    const retornos = Object.values(clientesMap).filter(v => v > 1).length;
    const retidos  = Object.values(clientesMap).filter(v => v === 1).length;

    const score  = Math.max(0, Math.min(100, Math.round(taxaRes - (tma * 1.5) - retornos * 0.3)));
    const rankin = score >= 85 ? "🥇 Ouro" : score >= 65 ? "🥈 Prata" : "🥉 Bronze";
    const rankColor = score >= 85 ? "var(--yellow)" : score >= 65 ? "var(--muted)" : "var(--accent2)";

    document.getElementById("vTma").textContent       = tma;
    document.getElementById("vTotal").textContent     = fmt(total);
    document.getElementById("vResolvidos").textContent = taxaRes + "%";
    document.getElementById("vRetorno").textContent   = fmt(retornos);
    document.getElementById("vRetidos").textContent   = fmt(retidos);
    document.getElementById("vRanking").textContent   = rankin;
    document.getElementById("vScore").textContent     = "Score: " + score;
    document.getElementById("kpiRanking").style.setProperty("--kpi-color", rankColor);

    // ── Chart Assuntos ──
    const assuntos = {};
    data.forEach(d => { const k = d.assunto || "Outros"; assuntos[k] = (assuntos[k] || 0) + 1; });
    const aLabels = Object.keys(assuntos);
    const aVals   = Object.values(assuntos);

    new Chart(document.getElementById("chartAssuntos"), {
      type: "bar",
      data: {
        labels: aLabels,
        datasets: [{
          label: "Qtd",
          data: aVals,
          backgroundColor: aLabels.map((_, i) =>
            ["#00e5ff","#7c3aed","#22d3a5","#fbbf24","#f87171","#818cf8"][i % 6] + "bb"
          ),
          borderColor: "transparent",
          borderRadius: 6
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color:"#1c2f4a" }, ticks: { color:"#60748a", font:{ family:"Space Mono", size:11 } } },
          y: { grid: { color:"#1c2f4a" }, ticks: { color:"#60748a", font:{ family:"Space Mono", size:11 } } }
        }
      }
    });

    // ── Chart Pizza ──
    new Chart(document.getElementById("chartPizza"), {
      type: "doughnut",
      data: {
        labels: ["Resolvidos","Pendentes"],
        datasets: [{
          data: [resolvidos, total - resolvidos],
          backgroundColor: ["#22d3a5bb","#f87171bb"],
          borderColor: "transparent",
          hoverOffset: 8
        }]
      },
      options: {
        cutout: "68%",
        plugins: {
          legend: { labels: { color:"#60748a", font:{ family:"Space Mono", size:11 }, padding:16 } }
        }
      }
    });

    // ── Tabela ──
    const recentes = [...data].sort((a,b) => new Date(b.data) - new Date(a.data)).slice(0, 10);
    const tbody = document.getElementById("tabelaBody");
    tbody.innerHTML = recentes.map(d => \`
      <tr>
        <td style="color:var(--muted);font-family:var(--font-mono)">#\${d.id}</td>
        <td>\${d.cliente}</td>
        <td>\${d.assunto || "—"}</td>
        <td style="font-family:var(--font-mono)">\${(d.tempo||0).toFixed(2)}</td>
        <td><span class="badge \${d.resolvido ? 'badge-ok' : 'badge-err'}">\${d.resolvido ? "Resolvido" : "Pendente"}</span></td>
        <td style="color:var(--muted);font-size:.75rem">\${d.data ? fmtDate(d.data) : "—"}</td>
      </tr>
    \`).join("");

    // ── Esconde loader ──
    document.getElementById("loader").classList.add("hide");

  } catch (err) {
    console.error(err);
    document.getElementById("loader").innerHTML =
      \`<p style="color:var(--red);font-family:var(--font-mono)">Erro: \${err.message}</p>\`;
  }
}

init();
// Atualiza a cada 60s
setInterval(init, 60000);
</script>
</body>
</html>`));

// ─── START ──────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n✅  Dashboard rodando → http://localhost:${PORT}\n`);
  console.log(`   USE_MOCK = ${USE_MOCK ? "true  (dados simulados)" : "false (API real)"}`);
  console.log(`   Para usar API real: defina USE_MOCK = false e configure API_URL e API_TOKEN\n`);
});
