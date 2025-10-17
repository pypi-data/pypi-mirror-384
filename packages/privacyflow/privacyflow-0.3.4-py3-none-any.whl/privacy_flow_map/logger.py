# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================

import logging
from pathlib import Path

# Configura directory log
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "privacyflow.log"

log = logging.getLogger("privacyflow")

if not log.handlers:
    log.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(console_handler)

    # File handler (scrive su logs/privacyflow.log)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
    log.addHandler(file_handler)

# 👉 Nessuna stampa automatica all'import
# Usa log.info(...) da cli.py o altri moduli
