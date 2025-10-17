# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================


import yaml
import json
from pathlib import Path
from .flowmap import FlowMap, Node, Flow
from .logger import log

# --- Mini ontologia GDPR per PrivacyFlow v2 ---
GDPR_ROLES = {
    "controller": {
        "label": "Titolare del trattamento",
        "default_color": "#A8E6FF",
        "description": "Determina finalità e mezzi del trattamento."
    },
    "processor": {
        "label": "Responsabile del trattamento",
        "default_color": "#E0F7FA",
        "description": "Tratta dati personali per conto del titolare."
    },
    "sub_processor": {
        "label": "Sub-responsabile",
        "default_color": "#B2EBF2",
        "description": "Soggetto ingaggiato dal responsabile."
    },
    "datastore": {
        "label": "Archivio dati",
        "default_color": "#F3E5F5",
        "description": "Sistema di conservazione dei dati personali."
    },
    "thirdparty": {
        "label": "Terza parte",
        "default_color": "#FFF3E0",
        "description": "Servizio esterno coinvolto nel trattamento."
    },
}
def _flatten_meta_dict(*dicts):
    """
    Fonde più dict "meta-like" e appiattisce qualsiasi livello 'meta' annidato.
    Esempi:
      {'meta': {'a': 1}, 'b': 2}       -> {'a': 1, 'b': 2}
      {'meta': {'a': 1, 'meta': {'c': 3}}} -> {'a': 1, 'c': 3}
    """
    out = {}
    for d in dicts:
        if not isinstance(d, dict):
            continue
        tmp = dict(d)
        inner = tmp.pop("meta", None)
        if isinstance(inner, dict):
            out.update(_flatten_meta_dict(inner))  # ricorsivo
        out.update(tmp)
    return out
def load_privacy_file(path: Path) -> FlowMap:
    """
    Carica un file privacy.yaml o privacy.json e restituisce un FlowMap.
    Gestisce eccezioni e log informativi.
    """
    path = Path(path)
    log.info(f"[*] Caricamento file privacy: {path}")

    if not path.exists():
        log.error(f"[!] File non trovato: {path}")
        raise FileNotFoundError(f"File not found: {path}")

    # --- Lettura file
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"[!] Errore nella lettura del file {path}: {e}")
        raise

    # --- Parsing YAML o JSON
    try:
        if path.suffix.lower() in [".yaml", ".yml"]:
            raw = yaml.safe_load(content)
        elif path.suffix.lower() == ".json":
            raw = json.loads(content)
        else:
            log.error(f"[!] Formato file non supportato: {path.suffix}")
            raise ValueError(f"Unsupported file format: {path.suffix}")
    except Exception as e:
        log.error(f"[!] Errore nel parsing del file {path}: {e}")
        raise

    if not isinstance(raw, dict):
        log.error(f"[!] File {path} non valido: struttura principale non è un dizionario.")
        raise ValueError(f"Invalid structure in {path}")

    # --- Parsing nodi con supporto GDPR ---
    try:
        nodes = []
        for n in raw.get("nodes", []):
            # chiavi che promuoviamo a campi di primo livello
            promoted = {"id", "name", "type", "data_categories", "owner", "region", "role", "lawful_bases", "dpo",
                        "meta"}
            extras = {k: v for k, v in n.items() if k not in promoted}
            meta_src = n.get("meta", {})

            node = Node(
                id=n["id"],
                name=n.get("name", n["id"]),
                type=n.get("type", "service"),
                data_categories=n.get("data_categories", []),
                owner=n.get("owner"),
                region=n.get("region"),
                meta=_flatten_meta_dict(meta_src, extras),
            )
            if "role" in n:           setattr(node, "role", n["role"])
            if "lawful_bases" in n:   setattr(node, "lawful_bases", n["lawful_bases"])
            if "dpo" in n:            setattr(node, "dpo", n["dpo"])
            nodes.append(node)
    except Exception as e:
        log.error(f"[!] Errore nel parsing dei nodi nel file {path}: {e}")
        raise

        # --- Parsing flussi ---
    try:
        flows = []
        for f in raw.get("flows", []):
            promoted = {"source", "target", "purpose", "lawful_basis", "transfer_mechanism", "data_categories", "meta"}
            extras = {k: v for k, v in f.items() if k not in promoted}
            meta_src = f.get("meta", {})

            flows.append(Flow(
                source=f["source"],
                target=f["target"],
                purpose=f.get("purpose", "unspecified"),
                lawful_basis=f.get("lawful_basis"),
                transfer_mechanism=f.get("transfer_mechanism"),
                data_categories=f.get("data_categories", []),
                meta=_flatten_meta_dict(meta_src, extras),
            ))
    except Exception as e:
        log.error(f"[!] Errore nel parsing dei flussi nel file {path}: {e}")
        raise

    fm = FlowMap(nodes=nodes, flows=flows)
    log.info(f"[OK] File {path.name} caricato: {len(nodes)} nodi, {len(flows)} flussi.")
    return fm
