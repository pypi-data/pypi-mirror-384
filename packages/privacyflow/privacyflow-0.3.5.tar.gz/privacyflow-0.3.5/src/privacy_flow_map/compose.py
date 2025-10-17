# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
# ============================================================

import yaml
from pathlib import Path
from privacy_flow_map.flowmap import FlowMap, Node, Flow
from privacy_flow_map.parser import load_privacy_file
from privacy_flow_map.logger import log
from privacy_flow_map.scan_web import scan_website
from privacy_flow_map.report_builder import save_html_report
from privacy_flow_map.render import save_mermaid


def compose_privacy_maps(
    input_files: list[Path],
    scan_url: str | None = None,
    output_dir: Path | None = None,
    insecure: bool = False,
) -> FlowMap:
    """
    Unisce più file privacy.yaml/.json in un'unica FlowMap
    e opzionalmente integra i tracker trovati da una scansione web.
    """
    log.info("[COMPOSE] Avvio composizione delle mappe privacy.")



    merged = FlowMap(nodes=[], flows=[])

    for file in input_files:
        log.info(f"[COMPOSE] Caricamento file privacy: {file}")
        try:
            fm = None

            # Prova prima con il parser standard PrivacyFlow
            try:
                fm = load_privacy_file(file)
                log.info(f"[DEBUG] Lettura file: {file}")
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read(300)

                except Exception as e:
                    log.warning(f"[DEBUG] Impossibile leggere {file}: {e}")
            except Exception:
                fm = None

            if fm:
                merged.nodes.extend(fm.nodes)
                merged.flows.extend(fm.flows)
                log.info(f"[OK] File {file} caricato ({len(fm.nodes)} nodi, {len(fm.flows)} flussi)")
                continue

            # Se non è un modello standard (es. flowmap.yaml), prova YAML raw
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            raw_nodes = data.get("nodes", [])
            raw_flows = data.get("flows", [])

            if raw_nodes or raw_flows:
                from privacy_flow_map.flowmap import Node, Flow
                nodes = [Node(**n) if isinstance(n, dict) else n for n in raw_nodes]
                flows = [Flow(**f) if isinstance(f, dict) else f for f in raw_flows]
                merged.nodes.extend(nodes)
                merged.flows.extend(flows)
                log.info(f"[OK] File YAML raw {file} caricato ({len(nodes)} nodi, {len(flows)} flussi)")
            else:
                log.warning(f"[WARN] Nessun nodo/flusso trovato in {file}")

        except Exception as e:
            log.error(f"[COMPOSE] Errore durante la lettura di {file}: {e}")

    # --- Aggiunta risultati da scan opzionale ---
    if scan_url:
        try:
            base_out = Path(output_dir or "out")
            scan_dir = base_out / "scan_tmp"
            scan_dir.mkdir(parents=True, exist_ok=True)
            scanned = scan_website(scan_url, scan_dir, insecure=insecure)
            if scanned:
                merged.nodes.extend(scanned.nodes)
                merged.flows.extend(scanned.flows)
        except Exception as e:
            log.error(f"[COMPOSE] Errore durante la scansione da {scan_url}: {e}")

    # --- Normalizzazione ID nodi (senza deduplicazione) ---
    norm_nodes = []
    for n in merged.nodes:
        nid = _norm_id(getattr(n, "id", ""))
        if not nid:
            continue
        n.id = nid
        norm_nodes.append(n)
    merged.nodes = norm_nodes

    for fl in merged.flows:
        fl.source = _norm_id(getattr(fl, "source", ""))
        fl.target = _norm_id(getattr(fl, "target", ""))

    # --- Salvataggio file YAML unificato ---
    base_out = Path(output_dir or "out")
    out_dir = base_out / "merged"   # ✅ percorso dinamico
    out_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = out_dir / "merged.yaml"


    try:
        data = {
            "nodes": [vars(n) for n in merged.nodes],
            "flows": [vars(f) for f in merged.flows],
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        log.info(f"[OK] File YAML unificato salvato in: {yaml_path}")
    except Exception as e:
        log.error(f"[ERR] Errore durante il salvataggio del merged.yaml: {e}")
        raise

    # --- Genera report base ---
    try:
        save_html_report(merged, out_dir / "report.html")
        save_mermaid(merged, out_dir / "flowmap.md")
    except Exception as e:
        log.error(f"[ERR] Errore durante la generazione del report: {e}")

    return merged

import re

def _norm_id(v: str) -> str:
    # stessa policy del report: solo [a-zA-Z0-9_], max 40 char
    return re.sub(r'[^a-zA-Z0-9_]', '_', str(v))[:40]