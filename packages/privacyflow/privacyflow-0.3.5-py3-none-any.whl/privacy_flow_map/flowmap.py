# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================


from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal

NodeType = Literal["service", "datastore", "thirdparty", "processor", "source"]


class Node:
    def __init__(self, id, name=None, label=None, type=None, region=None, meta=None, **kwargs):
        self.id = id
        self.name = name or label or id
        self.type = type or "unknown"
        self.region = region or "unknown"
        # meta ufficiale (sempre dict)
        self.meta = meta if isinstance(meta, dict) else {}
        # eventuali campi extra, ma evita di reimpostare 'meta'
        for k, v in kwargs.items():
            if k == "meta":
                # se per qualche motivo entra ancora, fondi con quello ufficiale
                if isinstance(v, dict):
                    self.meta.update(v)
                continue
            setattr(self, k, v)


@dataclass
class Flow:
    source: str
    target: str
    purpose: str = "unspecified"
    lawful_basis: Optional[str] = None
    transfer_mechanism: Optional[str] = None  # ✅ aggiunto campo mancante
    data_categories: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)

@dataclass
class FlowMap:
    nodes: List[Node] = field(default_factory=list)
    flows: List[Flow] = field(default_factory=list)

    def to_dict(self):
        """Restituisce una rappresentazione serializzabile del flowmap."""
        return {
            "nodes": [vars(n) for n in self.nodes],
            "flows": [vars(f) for f in self.flows],
        }
