# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================
import logging
from string import Template
from .license_manager import get_active_license

import json
import re
import html
from datetime import datetime
from pathlib import Path
from .logger import log

# =============================================================================
# Template HTML per il report (aggiunto {summary_html})
# =============================================================================
from string import Template

# =============================================================================
# Template HTML per il report
# =============================================================================
from string import Template

# =============================================================================
# Template HTML per il report
# =============================================================================
# ====================== HTML (no format/Template) ============================
# Segnaposto testuali: %%SUMMARY_HTML%%, %%DIAGRAMS_HTML%%, %%NODES_TABLE%%,
# %%FLOWS_TABLE%%, %%TIMESTAMP%%
HTML_TEMPLATE_BASE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Privacy Flow Map Report</title>
<style>
body {
  position: relative;
  background-color: #fafafa;
  color: #222;
  font-family: Arial, sans-serif;
  overflow-x: visible;
}
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ccc; padding: 6px 8px; font-size: 14px; text-align: left; }
th { background: #f2f2f2; }
h1, h2 { color: #0078d4; font-weight: 600; }

 .legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #222;
}

.legend-box {
  width: 20px;
  height: 20px;
  margin-right: 6px;
  border: 1px solid #ccc;
  border-radius: 3px;
  box-shadow: inset 0 0 2px rgba(0, 0, 0, 0.1);
}

/* ✅ Colori esatti già in uso per i nodi dei diagrammi */
.legend-service { background-color: #E3F2FD; border-color: #1E88E5; }
.legend-datastore { background-color: #F3E5F5; border-color: #8E24AA; }
.legend-thirdparty { background-color: #FFF3E0; border-color: #FB8C00; }
.legend-controller { background-color: #A8E6FF; border-color: #2AA4AD; }
.legend-processor { background-color: #E0F7FA; border-color: #00ACC1; }
.legend-subprocessor { background-color: #CCF3FA; border-color: #00BBD6; } 
.legend-subject { background-color: #E0D7F9; border-color: #9B59B6; }



 .summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}

.summary-wrap {
  display: flex;
  justify-content: space-between;  /* 🔹 forza la separazione orizzontale */
  align-items: flex-start;
  width: 100%;
  gap: 40px;
}

.summary-card {
  flex: 1 1 auto;
  min-width: 300px;
}

.pie {
  flex: 0 0 auto;
  margin-left: auto;               /* 🔹 spinge il grafico tutto a destra */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 🔹 Watermark riga 1 */
body::before {
  content: "PrivacyFlow Community Edition";
  position: fixed;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  font-size: 80px;
  font-weight: bold;
  color: rgba(0, 0, 0, 0.15);
  font-family: Arial, sans-serif;
  text-align: center;
  white-space: nowrap;
  z-index: 0;
  pointer-events: none;
  user-select: none;
}

/* 🔹 Watermark riga 2 */
body::after {
  content: "for internal demo only";
  position: fixed;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  font-size: 50px;
  font-weight: bold;
  color: rgba(0, 0, 0, 0.15);
  font-family: Arial, sans-serif;
  text-align: center;
  white-space: nowrap;
  z-index: 0;
  pointer-events: none;
  user-select: none;
}

/* 🔹 Mantiene il watermark visibile in video e stampa */
body {
  position: relative;
  z-index: 1;
}

@media print {
  body::before,
  body::after {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
}

.pie svg {
  width: 160px;
  height: 160px;
  margin-bottom: 10px;
}
/* --- Footer: visibile solo in fondo all'ultima pagina --- */
.footer {
  display: block;
  text-align: center;
  font-size: 12px;
  color: #666;
  border-top: 1px solid #ddd;
  padding-top: 5px;
  margin-top: 40px;
  background: #fafafa;
}

/* ✅ Nascosto in tutte le .diagram-page (pagine intermedie) */
.diagram-page .footer {
  display: none !important;
}
@media print {
  /* forza la stampa dei background */
  html, body, .legend, .legend-item, .legend-box {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }

  /* 🔳 quadratini legenda con bg esplicito in print */
  .legend-box { border: 1px solid #ccc !important; }

  .legend-service      { background-color: #E3F2FD !important; border-color: #1E88E5 !important; }
  .legend-datastore    { background-color: #F3E5F5 !important; border-color: #8E24AA !important; }
  .legend-thirdparty   { background-color: #FFF3E0 !important; border-color: #FB8C00 !important; }
  .legend-controller   { background-color: #A8E6FF !important; border-color: #2AA4AD !important; }
  .legend-processor    { background-color: #E0F7FA !important; border-color: #00ACC1 !important; }
  .legend-subprocessor { background-color: #CCF3FA !important; border-color: #00BBD6 !important; }

  /* anche la torta */
  .pie svg path,
  .pie svg circle {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
/* ✅ In stampa: mostrato solo sull'ultima pagina e fissato in fondo */
@media print {
  .footer {
  display: block;
  text-align: center;
  font-size: 12px;
  color: #666;
  border-top: 1px solid #ddd;
  padding-top: 5px;
  margin-top: 40px;
  background: #fafafa;
}




  /* Nascosto in tutte le sezioni precedenti */
  .diagram-page .footer {
    display: none !important;
  }
  
}
 
body::before {
  content: "PrivacyFlow Community Edition";
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  font-size: 90px;
  font-weight: bold;
  color: rgba(0, 0, 0, 0.15); /* 🔸 leggermente più scuro */
  font-family: Arial, sans-serif;
  white-space: nowrap;
  z-index: -1;
  pointer-events: none;
  isolation: isolate;
}
 
 @media print {
  body::before {
    color: rgba(0, 0, 0, 0.10); /* 🔸 un po’ più tenue in PDF */
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}

  
   @media print {
  @page { size: A4 landscape; margin: 10mm; }

  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  /* Ogni sezione di diagramma è una pagina logica */
  .diagram-page {
    display: block !important;
    width: 100% !important;
    min-height: 180mm !important;
    overflow: visible !important;
  }

  /* Ogni nuova .diagram-page inizia una nuova pagina */
  .diagram-page + .diagram-page {
    page-break-before: always !important;
    break-before: page !important;
  }

  /* Evita spezzature interne */
  .diagram-page * {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
  .legend-box {
    -webkit-print-color-adjust: exact !important;
    color-adjust: exact !important;
    print-color-adjust: exact !important;
    box-shadow: none !important;
  }

  .legend-service { background-color: #E3F2FD !important; }
  .legend-datastore { background-color: #F3E5F5 !important; }
  .legend-thirdparty { background-color: #FFF3E0 !important; }
  .legend-controller { background-color: #A8E6FF !important; }
  .legend-processor { background-color: #E0F7FA !important; }
  .legend-subprocessor { background-color: #CCF3FA !important; }
  /* Assicura che la legenda sia parte del flusso normale */
  .legend {
    position: static !important;
    margin-top: 8mm !important;
    margin-bottom: 0 !important;
    justify-content: center !important;
    display: flex !important;
    flex-wrap: wrap !important;
  }

  .mermaid {
    width: 100% !important;
    height: 140mm !important;
    overflow: visible !important;
  }

  .mermaid svg {
    width: 100% !important;
    height: auto !important;
    max-height: 140mm !important;
  }

  .diagram-section h2 {
    margin: 0 0 4mm 0 !important;
  }
   
}


 

 

 
</style>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
 


</head>
<body>
<h1>Privacy Flow Map Report</h1>

%%SUMMARY_HTML%%

 

<div id="diagrams" class="diagrams-container">%%DIAGRAMS_HTML%%</div>


<section id="nodes-section">
  <h2>Nodi</h2>
  %%NODES_TABLE%%
</section>

<h2>Flussi</h2>
%%FLOWS_TABLE%%

 
<div class="footer">
Generato il %%TIMESTAMP%%
</div>
<p style="font-size:12px; text-align:center; color:#666;">
PrivacyFlow 2025 PrivacyFlow Labs – All rights reserved.<br>
</p>


 <script>
mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
window.addEventListener('DOMContentLoaded', () => {
  const blocks = document.querySelectorAll('script.mermaid-code[type="text/plain"]');
  blocks.forEach((block, idx) => {
    const code = (block.textContent || '').trim();
    const targetId = block.dataset.target;
    const target = document.getElementById(targetId);
    if (!code || !target) return;
    mermaid.render(`pf_${idx + 1}`, code, target)
      .then(({ svg, bindFunctions }) => {
        target.innerHTML = svg;
        if (bindFunctions) bindFunctions(target);
      })
      .catch(err => console.error('Mermaid render error:', err));
  });
});
</script>
</body>
</html>
"""


# =============================================================================
# Funzioni di supporto (MERMAID, TABELLE)
# =============================================================================

import re


def _norm_id(v: str) -> str:
    """Rimuove caratteri non validi e uniforma gli ID."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', str(v))[:40]


def sanitize_label(text: str) -> str:
    if not text:
        return ""
    text = html.escape(text)
    text = re.sub(r'["\'`|<>/\\:{}()\[\]]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:60]


def get_node_class(node):
    """Restituisce la classe di stile Mermaid per il nodo."""
    # Se il nodo ha un ruolo GDPR, questo prevale
    role = getattr(node, "role", None)
    if role and role.lower() in GDPR_ROLE_CLASSES:
        return GDPR_ROLE_CLASSES[role.lower()]

    # Altrimenti fallback sul type standard
    return getattr(node, "type", "service")


def build_mermaid_diagram(flowmap) -> str:
    """
    Costruisce il diagramma Mermaid normalizzando gli ID
    (es. 'www.register.it' → 'www_register_it') per evitare duplicati.
    """
    try:
        def _sid(v: str) -> str:
            """Normalizza ID per l'uso nel diagramma."""
            return re.sub(r'[^a-zA-Z0-9_]', '_', str(v))[:40]

        def _slabel(t: str) -> str:
            """Sanitizza l'etichetta visuale (nome nodo) SENZA HTML-escape."""
            if not t:
                return ""
            t = str(t)
            # togli solo spazi/controlli e caratteri che rompono Mermaid
            t = re.sub(r'[\r\n\t]+', ' ', t)
            t = re.sub(r'\s{2,}', ' ', t).strip()
            # evita doppi apici nel contenuto (useremo ["..."] come delimitatori)
            t = t.replace('"', "'")
            # opzionale: rimuovi solo parentesi quadre che hanno significato in mermaid
            t = t.replace('[', '(').replace(']', ')')
            return t[:60]

        def _edge_label(purpose: str, lawful: str | None) -> str:
            parts = []
            if purpose:
                parts.append(str(purpose))
            if lawful:
                parts.append(str(lawful))
            label = " - ".join(parts).strip() or " "
            label = label.replace('"', "'")
            label = re.sub(r'[\r\n\t|]+', ' ', label)
            return f'"{label}"'

        # ─────────────────────────────
        # Inizio costruzione grafo
        # ─────────────────────────────
        lines = ["flowchart LR"]
        known_ids = {}
        nodes_sorted = sorted(
            getattr(flowmap, "nodes", []),
            key=lambda n: 0 if getattr(n, "type", "") in ("subject", "data_subject") else 1
        )
        # Normalizza tutti i nodi iniziali
        for n in nodes_sorted:
            nid = _sid(getattr(n, "id", ""))
            node_class = (get_node_class(n) or "").strip().lower()
            ntype = (getattr(n, "type", "") or "").strip().lower()
            nrole = (getattr(n, "role", "") or "").strip().lower()

            # 🔹 Forza la classe "subject" se il nodo è un interessato / utente / data subject
            if ntype in ("subject", "data_subject") or nrole in ("subject", "data_subject") or "subject" in nid:
                node_class = "subject"

            # fallback default se vuoto
            if not node_class:
                node_class = "service"

            # aggiungi la riga nel diagramma
            lines.append(f"class {nid} {node_class};")

        # Genera i flussi
        for flow in getattr(flowmap, "flows", []):
            src = _sid(getattr(flow, "source", ""))
            dst = _sid(getattr(flow, "target", ""))
            flow.source = src
            flow.target = dst
            purpose = getattr(flow, "purpose", "") or ""
            lawful = getattr(flow, "lawful_basis", None)

            # Crea automaticamente nodi mancanti ma con ID già normalizzato
            if src not in known_ids:
                lines.append(f'    {src}["{src}"]')
                known_ids[src] = True
                log.info(f"[+] Nodo sorgente creato automaticamente: {src}")

            if dst not in known_ids:
                lines.append(f'    {dst}["{dst}"]')
                known_ids[dst] = True
                log.info(f"[+] Nodo destinazione creato automaticamente: {dst}")

            lines.append(f'    {src} -->|{_edge_label(purpose, lawful)}| {dst}')

        # ─────────────────────────────
        # Definizioni di stile per tipo nodo
        # ─────────────────────────────
        lines += [
            "classDef service fill:#E3F2FD,stroke:#1E88E5,color:#0D47A1;",
            "classDef datastore fill:#F3E5F5,stroke:#8E24AA,color:#4A148C;",
            "classDef thirdparty fill:#FFF3E0,stroke:#FB8C00,color:#E65100;",
            "classDef processor fill:#E0F7FA,stroke:#00ACC1,color:#006064;",
            "classDef controller fill:#A8E6FF,stroke:#2AA4AD,color:#006064;",
            "classDef subject fill:#EDE7F6,stroke:#B388FF,color:#4A148C;",
        ]

        for n in getattr(flowmap, "nodes", []):
            nid = _sid(getattr(n, "id", ""))
            node_class = get_node_class(n).lower()

            # 🔹 forza corrispondenza per soggetto anche se il ruolo è "data_subject"
            if node_class in ("data_subject", "subject"):
                node_class = "subject"


            lines.append(f"class {nid} {node_class};")

        diagram = "\n".join(lines).strip()
        diagram = re.sub(r'</?div[^>]*>', '', diagram, flags=re.I)
        return diagram

    except Exception as e:
        log.error(f"[!] Errore durante la costruzione del diagramma Mermaid: {e}")
        return "flowchart LR\nA[Errore] --> B[Diagramma non generato]"


def build_table(items, headers):
    """
    headers: può essere una lista di stringhe ["id", "name", "type"]
             oppure di tuple [(campo, etichetta_visuale)]
    """
    if not items:
        return "<p><em>Nessun dato disponibile.</em></p>"

    # 🔹 costruzione header con label personalizzate
    html_rows = ["<table><thead><tr>"]
    for h in headers:
        field, label = (h if isinstance(h, tuple) else (h, h))
        html_rows.append(f"<th>{html.escape(label)}</th>")
    html_rows.append("</tr></thead><tbody>")

    # 🔹 righe dati
    for item in items:
        html_rows.append("<tr>")
        for h in headers:
            field = h[0] if isinstance(h, tuple) else h
            value = item.get(field, "") if isinstance(item, dict) else getattr(item, field, "")
            html_rows.append(f"<td>{html.escape(str(value))}</td>")
        html_rows.append("</tr>")
    html_rows.append("</tbody></table>")
    return "".join(html_rows)

# =============================================================================
# Summary (metriche + pie chart SVG)
# =============================================================================

def _count_by_type(flowmap):
    types = {}
    for n in getattr(flowmap, "nodes", []):
        t = (getattr(n, "type", "") or "").lower()
        types[t] = types.get(t, 0) + 1
    return types


def _build_pie_svg(values, labels,colors):
    """
    Crea il grafico a torta SVG coerente con i colori usati nella legenda dei diagrammi.
    """
    total = sum(values) or 1
    angles = [v / total * 360 for v in values]

    # 🎨 Palette coerente con la legenda


    # --- Costruzione path SVG ---
    import math
    paths = []
    start_angle = 0
    for i, (angle, color) in enumerate(zip(angles, colors)):
        end_angle = start_angle + angle
        x1 = 70 + 60 * math.cos(math.radians(start_angle))
        y1 = 70 + 60 * math.sin(math.radians(start_angle))
        x2 = 70 + 60 * math.cos(math.radians(end_angle))
        y2 = 70 + 60 * math.sin(math.radians(end_angle))
        large_arc = 1 if angle > 180 else 0
        d = f"M 70 70 L {x1:.3f} {y1:.3f} A 60 60 0 {large_arc} 1 {x2:.3f} {y2:.3f} Z"
        paths.append(f'<path d="{d}" fill="{color}" stroke="#ccc" />')
        start_angle = end_angle

    pie_svg = f"""
    <svg class="pie" viewBox="0 0 140 140" width="160" height="160" aria-label="Role Breakdown">
      <circle cx="70" cy="70" r="60" fill="#f5f5f5" stroke="#ddd" />
      {''.join(paths)}
    </svg>
    """

    # --- Legenda coerente ---
    legend_html = """
    <div style="font-size:13px;">
      <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#A8E6FF;border:1px solid #bbb;"></span>Controllers</div>
      <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#E0F7FA;border:1px solid #bbb;"></span>Processors</div>
      <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#F3E5F5;border:1px solid #bbb;"></span>Datastores</div>
      <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#FFF3E0;border:1px solid #bbb;"></span>Third-parties</div>
      <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#E3F2FD;border:1px solid #bbb;"></span>Services</div>
 <div style="display:flex;align-items:center;gap:6px;">
  <span style="display:inline-block;width:12px;height:12px;background:#EDE7F6;border:1px solid #bbb;"></span>
  Data subjects
</div>
     </div>
    """

    return pie_svg, legend_html



def _cosd(deg):  # cos in gradi
    import math
    return math.cos(math.radians(deg))


def _sind(deg):  # sin in gradi
    import math
    return math.sin(math.radians(deg))


# =============================================================================
# Tabella Ruoli GDPR (estensione semantica)
# =============================================================================
GDPR_ROLE_CLASSES = {
    "controller": "controller",
    "processor": "processor",
    "sub_processor": "processor",
    "data_subject": "subject",
    "subject": "subject",
}


def build_gdpr_roles_section(flowmap):
    """Crea una tabella sintetica con i ruoli GDPR presenti nel modello.
       Se 'role' non è esplicito, deduce il ruolo dal 'type' usando GDPR_ROLE_CLASSES.
       Include anche la base giuridica (lawful basis) se presente.
    """
    rows = []
    valid_roles = set(GDPR_ROLE_CLASSES.keys())

    for n in getattr(flowmap, "nodes", []):
        # leggi ruolo esplicito o dedotto
        role = getattr(n, "role", None)
        node_type = getattr(n, "type", "").lower()
        if not role and node_type in valid_roles:
            role = node_type

        if not role:
            continue

        # 🔹 estrai lawful_bases (lista, singolo valore o da meta)
        lawful_bases = []
        if hasattr(n, "lawful_bases") and getattr(n, "lawful_bases"):
            lb = getattr(n, "lawful_bases")
            lawful_bases = lb if isinstance(lb, list) else [lb]
        elif hasattr(n, "meta") and isinstance(n.meta, dict):
            lb = n.meta.get("lawful_bases") or n.meta.get("lawful_basis")
            if lb:
                lawful_bases = lb if isinstance(lb, list) else [lb]

        # 🔹 normalizza e prepara la riga
        rows.append({
            "name": getattr(n, "name", getattr(n, "id", "")),
            "role": role,
            "region": getattr(n, "region", "EU"),
            "dpo": getattr(n, "dpo", ""),
            "lawful basis": ", ".join(lawful_bases) if lawful_bases else ""
        })

    if not rows:
        return ""

    headers = ["name", "role", "region", "dpo", "lawful basis"]
    table_html = build_table(rows, headers)

    return f"""
    <section class="gdpr-roles" style="margin:20px 0 30px;">
      <h2>Ruoli GDPR</h2>
      <p>Elenco dei soggetti identificati nel modello come data subject, titolari, responsabili o sub-responsabili del trattamento.</p>
      {table_html}
    </section>
    """


def build_summary_section(flowmap):
    total_nodes = len(getattr(flowmap, "nodes", []))
    total_flows = len(getattr(flowmap, "flows", []))
    by_type = _count_by_type(flowmap)

    controllers = by_type.get("controller", 0)
    processors = by_type.get("processor", 0) + by_type.get("sub_processor", 0)
    datastores = by_type.get("datastore", 0) + by_type.get("database", 0)
    thirdparties = by_type.get("thirdparty", 0)
    services = by_type.get("service", 0)
    subjects = by_type.get("subject", 0)
    values = [controllers, processors, datastores, thirdparties, services, subjects]
    labels = ["Controllers", "Processors", "Datastores", "Third-parties", "Services", "Data Subjects"]
    colors = ["#A8E6FF", "#E0F7FA", "#F3E5F5", "#FFF3E0", "#E3F2FD", "#EDE7F6"]

    pie_svg, legend_html = _build_pie_svg(values, labels,colors)

    return f"""
    <section class="summary">
      <div class="summary-wrap">
        <div class="summary-card">
          <h2>📊 Privacy Flow Summary</h2>
          <ul>
            <li><b>Total nodes:</b> {total_nodes}</li>
            <li><b>Total flows:</b> {total_flows}</li>
            <li><b>Controllers:</b> {controllers}</li>
            <li><b>Processors:</b> {processors}</li>
            <li><b>Third-party systems:</b> {thirdparties}</li>
            <li><b>Data stores:</b> {datastores}</li>
            <li><b>Services:</b> {services}</li>
            <li><b>Data Subjects:</b> {subjects}</li>
          </ul>
        </div>
        <div class="pie">
          {pie_svg}
          {legend_html}
        </div>
      </div>
    </section>
    """



# =============================================================================
# Salvataggio report
# =============================================================================

def save_html_report(flowmap, out_path: Path):


    global HTML_TEMPLATE_BASE

    """Genera e salva il report HTML (diagrammi + tabelle + summary)."""
    try:
        # Tabelle e summary
        headers = [("id", "id"), ("name", "name"), ("type", "type (Technical)")]
        nodes_table = build_table(getattr(flowmap, "nodes", []), headers)
        headers = [("source", "source"), ("target", "target"), ("purpose", "purpose"),("lawful_basis","lawful basis")]
        flows_table = build_table(getattr(flowmap, "flows", []),headers)

        summary_html = build_summary_section(flowmap)
        gdpr_roles_html = build_gdpr_roles_section(flowmap)
        summary_html = summary_html + gdpr_roles_html



        # --- Lettura licenza attiva ---
        from datetime import datetime

        try:
            lic = get_active_license() or {}
        except Exception:
            lic = {}

        edition = str(lic.get("plan", "community")).lower()
        customer = lic.get("customer", "N/A")

        expires_value = lic.get("expires", "2099-12-31T23:59:59")

        # Conversione sicura
        if isinstance(expires_value, datetime):
            expires = expires_value
        else:
            try:
                expires = datetime.fromisoformat(str(expires_value))
            except Exception:
                expires = datetime(2099, 12, 31, 23, 59, 59)

        # --- Gestione watermark dinamico ---
        if edition == "community":
            watermark_css = """
            body::before {
                content: "PrivacyFlow Community Edition – Solo per uso interno e demo";
                position: fixed;
                top: 45%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-30deg);
                font-size: 90px;
                font-weight: bold;
                color: rgba(0, 0, 0, 0.10);
                font-family: Arial, sans-serif;
                z-index: -1;
                pointer-events: none;
            }
            """
        else:
            #  Rimozione completa watermark per Pro o Enterprise
            try:
                global HTML_TEMPLATE_BASE
                HTML_TEMPLATE_BASE = re.sub(
                    r"body::before\s*\{[^}]+\}|body::after\s*\{[^}]+\}", "", HTML_TEMPLATE_BASE, flags=re.S
                )
            except Exception as e:
                log.warning(f"[WARN] Rimozione watermark non riuscita: {e}")
            watermark_css = ""




        # Dominio analizzato (facoltativo)
        root_node = None
        for n in getattr(flowmap, "nodes", []):
            if getattr(n, "type", "") == "service" and str(getattr(n, "name", "")).startswith("www."):
                root_node = n
                break
        if root_node is not None:
            summary_html += (
                "<div style='background:#e8f8ff;border-left:5px solid #01C6C7;"
                "padding:10px;margin:16px 0 24px;border-radius:8px;'>"
                "<b>Dominio analizzato:</b> "
                "<a href='https://" + html.escape(str(root_node.name)) + "' target='_blank'>" +
                html.escape(str(root_node.name)) + "</a>"
                "</div>"
            )

        # --- DIAGRAMMI MULTIPLI o SINGOLO ---
        diagrams_html = ""

        # 🔹 Rileva se flowmap è multiplo
        if isinstance(flowmap, (list, tuple)):
            flowmaps = flowmap
        else:
            flowmaps = [flowmap]

        parts = []
        for i, fm in enumerate(flowmaps, start=1):
            code = build_mermaid_diagram(fm).strip()

            block = f"""
            <div class="diagram-page">
              <section class="diagram-section">
                <h2>Diagramma dei flussi</h2>
                <div id="mermaid-target-{i}" class="mermaid" style="text-align:center;margin:10px auto;width:95%;max-width:1400px;"></div>
                <script class="mermaid-code" type="text/plain" data-target="mermaid-target-{i}">{code}</script>
                <div class="legend">
                  <div class="legend-item"><div class="legend-box legend-service"></div>Servizio interno</div>
                  <div class="legend-item"><div class="legend-box legend-datastore"></div>Archivio dati</div>
                  <div class="legend-item"><div class="legend-box legend-thirdparty"></div>Terza parte / Fornitore esterno</div>
                  <div class="legend-item"><div class="legend-box legend-controller"></div>Titolare del trattamento</div>
                  <div class="legend-item"><div class="legend-box legend-processor"></div>Responsabile del trattamento</div>
                  <div class="legend-item"><div class="legend-box legend-subprocessor"></div>Sub-responsabile del trattamento</div>
                    <div class="legend-item"><div class="legend-box legend-subject"></div>Interessato / Data Subject</div>

                </div>
              </section>
            </div>
            """

            parts.append(block)

        diagrams_html = "\n".join(parts)


        # Composizione HTML con replace testuale
        html_content = (HTML_TEMPLATE_BASE
                        .replace("%%SUMMARY_HTML%%", summary_html)
                        .replace("%%DIAGRAMS_HTML%%", diagrams_html)
                        .replace("%%NODES_TABLE%%", nodes_table)
                        .replace("%%FLOWS_TABLE%%", flows_table)
                        .replace("%%TIMESTAMP%%", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


        # Footer dinamico
        if edition in ("pro", "enterprise"):
            html_content = html_content.replace(
                "PrivacyFlow 2025 PrivacyFlow Labs – All rights reserved.",
                f"PrivacyFlow {edition.capitalize()} Edition – {customer} "
                + (f"(valida fino al {expires})" if expires else "")
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_content, encoding="utf-8")
        log.info(f"[OK] Report HTML scritto in: {out_path}")
    except Exception as e:
        log.error(f"[!] Errore durante il salvataggio del report HTML: {e}")
        raise

def save_md_report(flowmap, output_dir):
    """Salva anche la versione Markdown del flowmap."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "flowmap.md"

    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Privacy Flow Map\n\n")
            f.write("## Nodi\n\n")
            for n in getattr(flowmap, "nodes", []):
                f.write(f"- **{getattr(n, 'id', '')}** ({getattr(n, 'type', 'unknown')})\n")
            f.write("\n## Flussi\n\n")
            for fl in getattr(flowmap, "flows", []):
                f.write(
                    f"- {getattr(fl, 'source', '?')} → {getattr(fl, 'target', '?')} ({getattr(fl, 'purpose', 'n/a')})\n")
        log.info(f"[OK] Flowmap Markdown salvato in: {md_path}")
    except Exception as e:
        log.error(f"[ERR] Errore durante il salvataggio del Markdown: {e}")


def save_json_report(flowmap, out_path: Path):
    """Salva il flowmap in formato JSON leggibile (serializzazione sicura)."""
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [vars(n) for n in getattr(flowmap, "nodes", [])],
            "flows": [vars(f) for f in getattr(flowmap, "flows", [])],
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"[OK] Report JSON scritto in: {out_path}")
    except Exception as e:
        log.error(f"[!] Errore durante il salvataggio JSON: {e}")
        raise
