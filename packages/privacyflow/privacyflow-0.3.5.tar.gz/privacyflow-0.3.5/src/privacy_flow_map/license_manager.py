# ============================================================
#  PrivacyFlow - License Manager
#  Gestione licenze digitali firmate RSA
# ============================================================

import os
import json
import base64
import logging
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

log = logging.getLogger(__name__)

LICENSE_PATHS = [
    os.path.expanduser("~/.config/privacyflow/license.json"),
    os.path.expanduser("~/.privacyflow/license.json"),
    os.path.expanduser("~/privacyflow/license.json"),
]

# Chiave pubblica usata per la verifica firma
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqwnHcNnlG41uyOyVfTcf
u7B6Efqzdy7XuMKsAIiJPAmT92dzu3Qp3kS1Ls5ttDxfAAEV+3GmL3jbLHGWQGtA
wWlFez6J4lLWkdvRDmm641sqEN8OROWZebbTD2H7aEnTcSd9oi5N3qvj6nGI1VFt
j/FjPW/f2ItXvbBdw9kAgszxC/Iw1GyQypKrY5axaJDUYRVnZxMePXy/LmOXZAxH
3aiCvK0p9N4OKRv/7PV8G+SZlny8S7iaecrLduiBCbm2bdJJpHtR3C8BF6HZThlH
vwqpIZUshZpv590UFQE4kAUZohhH0+9OVIYanrQsIqgr4WT8uXheUyF7YSiJiJxi
cwIDAQAB
-----END PUBLIC KEY-----"""

# Licenza di fallback (Community Edition)
DEFAULT_LICENSE = {
    "edition": "Community",
    "customer": "Unlicensed User",
    "plan": "community",
    "features": ["init", "scan", "compose", "render"],
    "expires": None,
}


# ============================================================
# Funzioni principali
# ============================================================

def read_license() -> dict | None:
    """Carica il JSON della licenza dai percorsi noti."""
    for path in LICENSE_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.warning(f"Errore lettura {path}: {e}")
    return None


def verify_signature(license_data: dict) -> bool:
    """Verifica la firma digitale RSA-PSS della licenza PrivacyFlow."""
    sig_b64 = license_data.get("_signature")
    if not sig_b64:
        log.warning("Nessuna firma trovata nella licenza.")
        return False

    try:
        # Prepara payload e firma
        payload = {k: v for k, v in license_data.items() if k != "_signature"}
        message = json.dumps(payload, sort_keys=True)
        if isinstance(message, str):
            message = message.encode("utf-8")

        # Gestione robusta firma (stringa o bytes)
        if isinstance(sig_b64, str):
            signature = base64.b64decode(sig_b64)
        elif isinstance(sig_b64, bytes):
            try:
                signature = base64.b64decode(sig_b64)
            except Exception:
                signature = sig_b64
        else:
            log.error(f"Tipo non gestito per signature: {type(sig_b64)}")
            return False

        # Carica chiave pubblica
        public_key = serialization.load_pem_public_key(
            PUBLIC_KEY_PEM if isinstance(PUBLIC_KEY_PEM, bytes) else PUBLIC_KEY_PEM.encode("utf-8")
        )


        # Verifica la firma RSA-PSS
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True

    except InvalidSignature:
        log.warning("Firma della licenza non valida.")
        return False
    except Exception as e:
        log.error(f"Errore durante la verifica firma: {e}")
        return False


def get_active_license() -> dict:
    """
    Restituisce le informazioni sulla licenza corrente.
    Chiavi: plan, valid, customer, expires
    """
    path = find_license_file()
    if not path:
        return {"plan": "community", "valid": False, "customer": None, "expires": None}

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            lic = json.load(f)

        if not verify_signature(lic):
            return {"plan": "community", "valid": False, "customer": lic.get("customer"), "expires": lic.get("expires")}

        exp = datetime.fromisoformat(lic["expires"])
        if exp < datetime.utcnow():
            return {"plan": "community", "valid": False, "customer": lic.get("customer"), "expires": lic.get("expires")}

        return {
            "plan": lic.get("plan", "enterprise"),
            "valid": True,
            "customer": lic.get("customer"),
            "expires": lic.get("expires"),
        }

    except Exception as e:
        log.error(f"Errore nel caricamento licenza: {e}")
        return {"plan": "community", "valid": False, "customer": None, "expires": None}



def get_feature_flag(feature: str) -> bool:
    """Controlla se una funzionalità è abilitata nella licenza."""
    lic = get_active_license()
    feats = lic.get("features", [])
    return feature in feats


def print_license_info():
    """Mostra banner CLI della licenza attiva."""
    lic = get_active_license()
    edition = lic.get("edition", "Community")
    customer = lic.get("customer", "N/A")
    exp = lic.get("expires")

    print("─────────────────────────────────────────────")
    if edition.lower() == "community":
        print("PrivacyFlow Community Edition")
        print("Uso gratuito per audit e test interni.")
    else:
        print(f"PrivacyFlow {edition} Edition — {customer}")
        if exp:
            print(f"Valida fino al {exp}")
        else:
            print("Licenza senza scadenza (lifetime).")
    print("─────────────────────────────────────────────")

def sign_license(customer: str, domains: list[str], days_valid: int = 365, output_dir: str = "licenses"):
    """
    Genera una licenza firmata con la chiave privata locale (solo per uso interno).
    Richiede il file private_key.pem nel percorso tools/private_key.pem.
    """
    import json, base64, os
    from datetime import datetime, timedelta
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key_path = os.path.join("tools", "private_key.pem")
    if not os.path.exists(key_path):
        print(f"Chiave privata non trovata: {key_path}")
        return

    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    license_data = {
        "customer": customer,
        "domains": domains,
        "plan": "enterprise",
        "issued": datetime.utcnow().isoformat(),
        "expires": (datetime.utcnow() + timedelta(days=days_valid)).isoformat(),
    }

    message = json.dumps(license_data, sort_keys=True).encode("utf-8")

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    license_data["_signature"] = base64.b64encode(signature).decode("utf-8")

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"license_{customer.replace(' ', '_')}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(license_data, f, indent=2)

    print(f"Licenza generata: {out_file}")
    return out_file

def activate_license_file(src_path: str):
    """Installa manualmente una nuova licenza."""
    if not os.path.exists(src_path):
        raise FileNotFoundError(src_path)

    with open(src_path, "r", encoding="utf-8") as sf:
        data_obj = json.load(sf)

    os.makedirs(os.path.dirname(LICENSE_PATHS[1]), exist_ok=True)
    with open(LICENSE_PATHS[1], "w", encoding="utf-8") as df:
        json.dump(data_obj, df, indent=2)

    print(f"Licenza installata in {LICENSE_PATHS[1]}")


import os, json, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def find_license_file():
    """Trova la licenza valida nei percorsi standard dell’utente."""
    candidates = [
        os.path.expanduser("~/.config/privacyflow/license.json"),
        os.path.expanduser("~/.privacyflow/license.json"),
        os.path.expanduser("~/privacyflow/license.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def check_license():
    """Verifica la validità della licenza."""
    path = find_license_file()
    if not path:
        print("Nessuna licenza trovata. Usa `privacy-flow license` per installarne una.")
        return False

    try:
        with open(path, "r", encoding="utf-8-sig") as f:  # supporta UTF-8 e UTF-8 con BOM
            lic = json.load(f)

        sig = base64.b64decode(lic["_signature"])
        payload = {k: v for k, v in lic.items() if k != "_signature"}
        message = json.dumps(payload, sort_keys=True).encode("utf-8")

        pub = serialization.load_pem_public_key(PUBLIC_KEY_PEM.encode())
        pub.verify(sig, message, padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ), hashes.SHA256())

        print(f"Licenza valida per {lic['customer']}")
        print(f"   Piano: {lic.get('plan')}  Scadenza: {lic.get('expires')}")
        return True

    except Exception as e:
        print(f"Licenza non valida: {e}")
        return False

if __name__ == "__main__":
    check_license()