"""
╔══════════════════════════════════════════════════════╗
║  Dashboard de Atendimento — Python + Flask           ║
║  Integração: IXC Soft (webservice/v1)                ║
╠══════════════════════════════════════════════════════╣
║  INSTALAÇÃO (apenas uma vez):                        ║
║    pip install flask requests                        ║
║                                                      ║
║  RODAR:                                              ║
║    python dashboard.py                               ║
║                                                      ║
║  Abra: http://localhost:3000                         ║
╚══════════════════════════════════════════════════════╝
"""

from flask import Flask, jsonify, render_template_string
import requests
import base64
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# ─── CONFIG IXC SOFT ────────────────────────────────────────────
# Troque para False quando tiver as credenciais do IXC Soft
USE_MOCK = True

# Preencha com os dados do seu servidor IXC Soft:
IXC_HOST  = "SEU_HOST_AQUI"          # ex: "suaempresa.ixcsoft.com.br"
IXC_TOKEN = "SEU_TOKEN_AQUI"         # token gerado no IXC Soft

# Endpoints usados (formulários do IXC Soft)
# su_oss_chamado = Chamados/Tickets de atendimento
IXC_ENDPOINT = f"https://{IXC_HOST}/webservice/v1/su_oss_chamado"
# ────────────────────────────────────────────────────────────────


def get_auth_header():
    """Monta o header de autenticação Basic do IXC Soft."""
    token_bytes = IXC_TOKEN.encode("utf-8")
    token_b64   = base64.b64encode(token_bytes).decode("utf-8")
    return {
        "Authorization": f"Basic {token_b64}",
        "Content-Type":  "application/json",
    }


def buscar_atendimentos_ixc():
    """
    Busca chamados do IXC Soft.
    O IXC retorna: { "type": "array", "total": N, "registros": [...] }
    """
    payload = {
        "qtype":  "su_oss_chamado.id",
        "query":  "",
        "oper":   ">=",
        "page":   "1",
        "rp":     "200",          # quantidade de registros por página
        "sortname":  "su_oss_chamado.id",
        "sortorder": "desc",
    }

    resp = requests.post(IXC_ENDPOINT, json=payload, headers=get_auth_header(), timeout=15)
    resp.raise_for_status()
    dados = resp.json()

    registros = dados.get("registros", [])

    # Normaliza campos do IXC para o formato interno do dashboard
    atendimentos = []
    for r in registros:
        # Calcula tempo em minutos entre abertura e fechamento
        try:
            abertura   = datetime.fromisoformat(r.get("data_abertura", ""))
            fechamento = datetime.fromisoformat(r.get("data_fechamento") or datetime.now().isoformat())
            tempo      = round((fechamento - abertura).total_seconds() / 60, 2)
        except Exception:
            tempo = 0

        atendimentos.append({
            "id":       r.get("id"),
            "cliente":  r.get("nome_cliente") or r.get("id_cliente", "Desconhecido"),
            "assunto":  r.get("assunto") or r.get("tipo_chamado", "Outros"),
            "tempo":    tempo,
            "resolvido": r.get("su_status") in ("F", "S"),   # F=Fechado, S=Solucionado
            "data":     r.get("data_abertura", ""),
        })

    return atendimentos


def gerar_mock():
    """Dados simulados para testar sem a API real."""
    assuntos = ["Cancelamento", "Cobrança", "Suporte Técnico", "Dúvida", "Reclamação", "Sem Sinal"]
    nomes    = ["João Silva", "Maria Santos", "Pedro Costa", "Ana Oliveira",
                "Carlos Lima", "Beatriz Souza", "Lucas Fernandes", "Juliana Rocha"]
    registros = []
    for i in range(1, 121):
        abertura = datetime.now() - timedelta(minutes=random.randint(10, 10080))
        registros.append({
            "id":       i,
            "cliente":  random.choice(nomes) + f" #{random.randint(100,999)}",
            "assunto":  random.choice(assuntos),
            "tempo":    round(random.uniform(1, 15), 2),
            "resolvido": random.random() > 0.25,
            "data":     abertura.isoformat(),
        })
    return registros


# ─── ROTAS API ──────────────────────────────────────────────────

@app.route("/atendimentos")
def atendimentos():
    try:
        dados = gerar_mock() if USE_MOCK else buscar_atendimentos_ixc()
        return jsonify(dados)
    except requests.exceptions.ConnectionError:
        return jsonify({"erro": "Não foi possível conectar ao IXC Soft. Verifique o HOST."}), 502
    except requests.exceptions.HTTPError as e:
        return jsonify({"erro": f"Erro HTTP {e.response.status_code} — verifique o TOKEN."}), 502
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ─── FRONTEND ───────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard · Atendimento</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
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

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 20px;
}
header h1 { font-size: clamp(1.3rem, 3vw, 1.9rem); font-weight: 800; letter-spacing: -.5px; }
header h1 span { color: var(--accent); }

#modoBadge {
  font-family: var(--font-mono);
  font-size: .72rem;
  padding: 5px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge-mock { background: rgba(251,191,36,.12); color: var(--yellow); border: 1px solid rgba(251,191,36,.3); }
.badge-live  { background: rgba(34,211,165,.12); color: var(--green);  border: 1px solid rgba(34,211,165,.3); }
.badge-live::before, .badge-mock::before {
  content: '';
  width: 7px; height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

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
.kpi-label { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; color: var(--muted); margin-bottom: 10px; }
.kpi-value { font-family: var(--font-mono); font-size: 1.7rem; font-weight: 700; color: var(--kpi-color, var(--accent)); line-height: 1; }
.kpi-sub   { font-size: .7rem; color: var(--muted); margin-top: 6px; }
#kpiRanking .kpi-value { font-size: 1.1rem; }

.charts {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}
@media(max-width:720px){ .charts { grid-template-columns: 1fr; } }

.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 20px;
}
.chart-title { font-size: .78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 16px; }

.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 20px;
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; font-size: .82rem; }
thead th { text-align: left; font-size: .68rem; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); padding-bottom: 10px; border-bottom: 1px solid var(--border); }
tbody tr { border-bottom: 1px solid rgba(255,255,255,.04); transition: background .15s; }
tbody tr:hover { background: rgba(255,255,255,.03); }
tbody td { padding: 10px 6px; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 20px; font-size: .67rem; font-weight: 600; }
.badge-ok  { background: rgba(34,211,165,.15); color: var(--green); }
.badge-err { background: rgba(248,113,113,.15); color: var(--red); }

#erro {
  background: rgba(248,113,113,.1);
  border: 1px solid rgba(248,113,113,.3);
  color: var(--red);
  padding: 16px 20px;
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: .82rem;
  margin-bottom: 24px;
  display: none;
}

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
.spinner { width: 42px; height: 42px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
#loader p { color: var(--muted); font-size: .85rem; }

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
  <div id="modoBadge" class="badge-mock">MODO MOCK</div>
</header>

<div id="erro"></div>

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

<div class="charts fade-in" style="animation-delay:.2s">
  <div class="chart-card">
    <div class="chart-title">Atendimentos por Assunto</div>
    <canvas id="chartAssuntos" height="200"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Resolução</div>
    <canvas id="chartPizza" height="200"></canvas>
  </div>
</div>

<div class="table-card fade-in" style="animation-delay:.3s">
  <div class="chart-title" style="margin-bottom:14px">Últimos 10 Atendimentos</div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Cliente</th><th>Assunto</th><th>Tempo (min)</th><th>Status</th><th>Data</th>
      </tr>
    </thead>
    <tbody id="tabelaBody"></tbody>
  </table>
</div>

<script>
let chartBar = null, chartPie = null;

const fmtDate = s => {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("pt-br", { day:"2-digit", month:"2-digit", hour:"2-digit", minute:"2-digit" });
};

async function init() {
  try {
    const res  = await fetch("/atendimentos");
    const data = await res.json();

    if (data.erro) throw new Error(data.erro);
    if (!Array.isArray(data)) throw new Error("Resposta inesperada da API");

    // KPIs
    const total      = data.length;
    const totalTempo = data.reduce((a, d) => a + (d.tempo || 0), 0);
    const tma        = total ? (totalTempo / total).toFixed(2) : 0;
    const resolvidos = data.filter(d => d.resolvido).length;
    const taxaRes    = total ? Math.round(resolvidos / total * 100) : 0;

    const clientesMap = {};
    data.forEach(d => { clientesMap[d.cliente] = (clientesMap[d.cliente] || 0) + 1; });
    const retornos = Object.values(clientesMap).filter(v => v > 1).length;
    const retidos  = Object.values(clientesMap).filter(v => v === 1).length;

    const score    = Math.max(0, Math.min(100, Math.round(taxaRes - (tma * 1.5) - retornos * 0.3)));
    const ranking  = score >= 85 ? "🥇 Ouro" : score >= 65 ? "🥈 Prata" : "🥉 Bronze";
    const rankColor = score >= 85 ? "var(--yellow)" : score >= 65 ? "var(--muted)" : "var(--accent2)";

    document.getElementById("vTma").textContent       = tma;
    document.getElementById("vTotal").textContent     = total.toLocaleString("pt-br");
    document.getElementById("vResolvidos").textContent = taxaRes + "%";
    document.getElementById("vRetorno").textContent   = retornos.toLocaleString("pt-br");
    document.getElementById("vRetidos").textContent   = retidos.toLocaleString("pt-br");
    document.getElementById("vRanking").textContent   = ranking;
    document.getElementById("vScore").textContent     = "Score: " + score;
    document.getElementById("kpiRanking").style.setProperty("--kpi-color", rankColor);

    // Badge modo
    const badge = document.getElementById("modoBadge");
    badge.className = "badge-live";
    badge.textContent = "AO VIVO";

    // Gráfico barras
    const assuntos = {};
    data.forEach(d => { const k = d.assunto || "Outros"; assuntos[k] = (assuntos[k]||0)+1; });
    const aLabels = Object.keys(assuntos);
    const aVals   = Object.values(assuntos);
    const cores   = ["#00e5ff","#7c3aed","#22d3a5","#fbbf24","#f87171","#818cf8"];

    if (chartBar) chartBar.destroy();
    chartBar = new Chart(document.getElementById("chartAssuntos"), {
      type: "bar",
      data: {
        labels: aLabels,
        datasets: [{ label: "Qtd", data: aVals,
          backgroundColor: aLabels.map((_,i) => cores[i%6]+"bb"),
          borderColor: "transparent", borderRadius: 6 }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color:"#1c2f4a" }, ticks: { color:"#60748a", font:{ family:"Space Mono", size:11 } } },
          y: { grid: { color:"#1c2f4a" }, ticks: { color:"#60748a", font:{ family:"Space Mono", size:11 } } }
        }
      }
    });

    // Gráfico pizza
    if (chartPie) chartPie.destroy();
    chartPie = new Chart(document.getElementById("chartPizza"), {
      type: "doughnut",
      data: {
        labels: ["Resolvidos","Pendentes"],
        datasets: [{ data: [resolvidos, total - resolvidos],
          backgroundColor: ["#22d3a5bb","#f87171bb"], borderColor: "transparent", hoverOffset: 8 }]
      },
      options: {
        cutout: "68%",
        plugins: { legend: { labels: { color:"#60748a", font:{ family:"Space Mono", size:11 }, padding:16 } } }
      }
    });

    // Tabela
    const recentes = [...data].sort((a,b) => new Date(b.data) - new Date(a.data)).slice(0,10);
    document.getElementById("tabelaBody").innerHTML = recentes.map(d => `
      <tr>
        <td style="color:var(--muted);font-family:var(--font-mono)">#${d.id}</td>
        <td>${d.cliente}</td>
        <td>${d.assunto || "—"}</td>
        <td style="font-family:var(--font-mono)">${(d.tempo||0).toFixed(2)}</td>
        <td><span class="badge ${d.resolvido ? 'badge-ok':'badge-err'}">${d.resolvido ? "Resolvido":"Pendente"}</span></td>
        <td style="color:var(--muted);font-size:.75rem">${fmtDate(d.data)}</td>
      </tr>
    `).join("");

    document.getElementById("loader").classList.add("hide");
    document.getElementById("erro").style.display = "none";

  } catch (err) {
    document.getElementById("loader").classList.add("hide");
    const el = document.getElementById("erro");
    el.style.display = "block";
    el.textContent = "⚠ Erro: " + err.message;
  }
}

init();
setInterval(init, 60000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    modo = "MOCK (dados simulados)" if USE_MOCK else f"IXC Soft → {IXC_HOST}"
    print(f"""
✅  Dashboard rodando → http://localhost:3000
    Modo: {modo}

    Para conectar ao IXC Soft:
      1. Defina USE_MOCK = False
      2. Preencha IXC_HOST com o endereço do seu servidor
      3. Preencha IXC_TOKEN com o token gerado no IXC Soft
    """)
    app.run(port=3000, debug=False)
