# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================




import requests
import warnings
import logging
import json
import yaml
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from privacy_flow_map.flowmap import FlowMap, Node, Flow
from privacy_flow_map.logger import log


def scan_website(url, out_dir=None, depth=1, insecure=False, verify_ssl=None):
    if verify_ssl is not None:
        insecure = not verify_ssl
    """
    Scansiona un sito o un file HTML e genera la flowmap dei tracker rilevati.
    """
    from pathlib import Path
    log.info(f"[*] Scansione del sito: {url}")
    flowmap = FlowMap()

    # --- Gestione SSL e warning ---
    if insecure:
        warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("requests").setLevel(logging.CRITICAL)
        session = requests.Session()
        verify_ssl = False
        log.warning("[!] SSL verification disabilitata (--insecure attivo).")
    else:
        session = requests.Session()
        verify_ssl = True

    # --- Nodo principale (servizio) ---
    main_host = urlparse(url).hostname or "localhost"
    # Crea automaticamente il nodo radice in base al dominio scansionato
    import re
    root_id = re.sub(r'[^a-zA-Z0-9_]', '_', main_host)[:40]
    root_name = main_host

    flowmap.nodes.append(Node(
        id=root_id,
        name=root_name,
        type="service",
        region="EU"
    ))
    log.info(f"[OK] Nodo radice creato automaticamente: {root_id} ({root_name})")

    # --- Download HTML principale ---
    try:
        if url.startswith("http"):
            response = session.get(url, verify=verify_ssl, timeout=10)
            html = response.text
        else:
            with open(url, "r", encoding="utf-8") as f:
                html = f.read()
    except Exception as e:
        log.error(f"[ERR] Impossibile accedere a {url}: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")

    # --- Estrazione risorse esterne ---
    resources = set()
    for tag in soup.find_all(["script", "img", "iframe", "link"]):
        src = tag.get("src") or tag.get("href")
        if not src:
            continue
        abs_url = urljoin(url, src)
        host = urlparse(abs_url).hostname
        if host and host != main_host:
            resources.add(host)

    # --- Creazione nodi terze parti e flussi ---
    for host in sorted(resources):
        flowmap.nodes.append(Node(id=host, name=host, type="thirdparty"))
        flowmap.flows.append(Flow(
            source=root_id,
            target=host,
            purpose="resource_request",
            lawful_basis="legitimate_interest"
        ))


# --- Salvataggio output ---
    from pathlib import Path
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = flowmap.to_dict()

    # Salva JSON
    json_path = out_dir / "flowmap.json"
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2, ensure_ascii=False)
        log.info(f"[OK] Flowmap JSON salvato in: {json_path}")
    except Exception as e:
        log.error(f"[ERR] Impossibile salvare {json_path}: {e}")

    # Salva YAML
    yaml_path = out_dir / "flowmap.yaml"
    try:
        with open(yaml_path, "w", encoding="utf-8") as yf:
            yaml.safe_dump(data, yf, sort_keys=False, allow_unicode=True)
        log.info(f"[OK] Flowmap YAML salvato in: {yaml_path}")
    except Exception as e:
        log.error(f"[ERR] Impossibile salvare {yaml_path}: {e}")

    log.info(f"[SCAN] Completato: {len(flowmap.nodes)} nodi trovati, {len(flowmap.flows)} flussi.")
    return flowmap

def cmd_scan(args):
    """Handler CLI per il comando 'scan'."""
    from pathlib import Path
    out_dir = Path(args.output)
    try:
        scan_website(
            url=args.url,
            out_dir=out_dir,
            depth=args.depth,         # ✅ usa depth invece di max_depth
            insecure=getattr(args, "insecure", False)
        )
    except Exception as e:
        log.error(f"[ERR] Errore durante la scansione: {e}")
