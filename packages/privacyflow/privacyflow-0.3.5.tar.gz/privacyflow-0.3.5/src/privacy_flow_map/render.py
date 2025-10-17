# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================




"""
Modulo: render
Genera file di output (Mermaid, JSON, HTML) a partire da una FlowMap.
"""

import json
from pathlib import Path
from .flowmap import FlowMap, Node, Flow
from .parser import load_privacy_file
from .report_builder import save_html_report
from .logger import log


def to_mermaid(flowmap: FlowMap) -> str:
    """
    Converte una FlowMap in codice Mermaid per la visualizzazione dei flussi.
    """
    lines = ["flowchart LR"]

    for n in flowmap.nodes:
        node_id =  n.id
        label = n.name or n.id
        lines.append(f'    {node_id}["{label}"]')

    for f in flowmap.flows:
        src = f.source
        dst = f.target
        label = f"{f.purpose or ''}"
        if f.lawful_basis:
            label += f" ({f.lawful_basis})"
        label = label.strip()
        lines.append(f"    {src} -->|{label}| {dst}")

    # --- definizioni colori
    lines.extend([
        "classDef service fill:#E3F2FD,stroke:#1E88E5,color:#0D47A1;",
        "classDef datastore fill:#F3E5F5,stroke:#8E24AA,color:#4A148C;",
        "classDef thirdparty fill:#FFF3E0,stroke:#FB8C00,color:#E65100;",
        "classDef processor fill:#E0F7FA,stroke:#00ACC1,color:#006064;",
    ])

    # --- applica classi
    for n in flowmap.nodes:
        lines.append(f"class {n.id} {n.type};")

    return "\n".join(lines)


def save_mermaid(flowmap: FlowMap, out_path: Path):
    """Salva il diagramma Mermaid su file .md"""
    content = f"```mermaid\n{to_mermaid(flowmap)}\n```"
    Path(out_path).write_text(content, encoding="utf-8")
    log.info(f"[RENDER] Mermaid scritto in {out_path}")

def save_json(flowmap: FlowMap, out_path: Path):
    """Salva il diagramma in formato JSON"""
    data = {
        "nodes": [n.__dict__ for n in flowmap.nodes],
        "flows": [f.__dict__ for f in flowmap.flows],
    }
    Path(out_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"[RENDER] JSON scritto in {out_path}")




def render_files(input_path: str, output_dir: str):
    """
    Funzione principale per generare i file di output da un privacy.yaml/.json.
    """
    in_path = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"[RENDER] Carico file: {in_path}")
    flowmap = load_privacy_file(in_path)

    import re

    def _sid(v: str) -> str:
        """Normalizza gli ID per evitare duplicati (es. www.register.it → www_register_it)."""
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(v))[:40]

    unique_nodes = {}
    new_nodes = []
    id_map = {}

    # Normalizza e deduplica nodi
    for node in getattr(flowmap, "nodes", []):
        nid = _sid(getattr(node, "id", ""))
        old_id = node.id
        node.id = nid
        id_map[old_id] = nid

        if nid not in unique_nodes:
            unique_nodes[nid] = node
            new_nodes.append(node)
        else:
            log.info(f"[!] Nodo duplicato unificato: {old_id} → {nid}")

    flowmap.nodes = new_nodes

    # Aggiorna i flussi con ID normalizzati
    for flow in getattr(flowmap, "flows", []):
        if hasattr(flow, "source") and flow.source in id_map:
            flow.source = id_map[flow.source]
        else:
            flow.source = _sid(getattr(flow, "source", ""))

        if hasattr(flow, "target") and flow.target in id_map:
            flow.target = id_map[flow.target]
        else:
            flow.target = _sid(getattr(flow, "target", ""))




    save_mermaid(flowmap, out_dir / "flowmap.md")
    save_json(flowmap, out_dir / "flowmap.json")
    save_html_report(flowmap, out_dir / "report.html")

    log.info(f"[RENDER] File generati in: {out_dir}")
    return out_dir

