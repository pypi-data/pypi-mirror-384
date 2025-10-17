# ============================================================
#  PrivacyFlow - Privacy Data Flow Mapper & Compliance Tool
#  Copyright (c) 2025 PrivacyFlow Labs. All rights reserved.
#  Developed in Italy by the PrivacyFlow Project
#  Website: https://www.privacyflow.it
#  License: Proprietary / Commercial - Redistribution prohibited
# ============================================================


"""
Modulo CLI principale per PrivacyFlow Map
Comando principale: `privacy-flow`
"""

import argparse
import sys
import os
from pathlib import Path



# ✅ Import robusti per supportare PyInstaller e installazioni via pip
try:
    from privacy_flow_map.scan_web import scan_website
    from privacy_flow_map.compose import compose_privacy_maps
    from privacy_flow_map.render import render_files
    from privacy_flow_map.report_builder import save_html_report
    from privacy_flow_map.logger import log
    from privacy_flow_map.flowmap import FlowMap
except ImportError:
    # fallback per esecuzione da sorgente
    from .scan_web import scan_website
    from .compose import compose_privacy_maps
    from .render import render_files
    from .report_builder import save_html_report
    from .logger import log
    from .flowmap import FlowMap


def cmd_init(args):
    """Crea un file privacy.yaml di esempio (base o extended)"""
    from pathlib import Path
    from privacy_flow_map.logger import log

    if args.template == "extended":
        sample_yaml = """\
    nodes:
      - id: data_subject
        name: Utente / Cliente
        type: subject
        data_categories: [personal_data, contact_data]
        region: EU
        meta:
          description: "Persona fisica i cui dati vengono trattati (cliente, utente, dipendente)"
        lawful_bases: [consent]

      - id: webapp
        name: Customer Portal
        type: service
        data_categories: [PII, Analytics, Contact]
        owner: "ACME"
        region: "EU"
        role: controller
        lawful_bases: [contract, legitimate_interest]
        dpo: "dpo@acme.com"
        meta:
          business_unit: "Digital"
          risk_level: "Medium"
          reviewed_by: "Privacy Office"
          last_review: "2025-10-14"

      - id: api_gateway
        name: API Gateway
        type: service
        data_categories: [PII, Analytics]
        region: "EU"
        role: processor
        lawful_bases: [contract]
        meta:
          managed_by: "IT Dept"
          version: "1.2"
          comment: "Handles user traffic to microservices"

      - id: db_main
        name: Primary Database
        type: datastore
        data_categories: [PII]
        region: "EU"
        role: controller
        lawful_bases: [contract, legal_obligation]
        meta:
          storage_type: "PostgreSQL"
          backup: "daily"
          encryption: "AES256"

      - id: analytics
        name: Analytics Platform
        type: thirdparty
        data_categories: [Analytics]
        region: "US"
        role: processor
        lawful_bases: [legitimate_interest]
        transfer_mechanism: "SCCs"
        meta:
          vendor: "Google Analytics"
          retention: "12 months"
          purpose_detail: "usage metrics"

      - id: notif
        name: Email Notification Service
        type: thirdparty
        data_categories: [Contact]
        region: "US"
        role: processor
        lawful_bases: [consent]
        transfer_mechanism: "SCCs"
        meta:
          vendor: "Mailgun"
          purpose_detail: "transactional notifications"

      - id: retention
        name: Archival Storage
        type: datastore
        data_categories: [PII, Contact]
        region: "EU"
        role: processor
        lawful_bases: [legal_obligation]
        meta:
          storage_type: "AWS Glacier"
          retention_period: "10 years"
          managed_by: "IT Compliance"

    flows:
      - source: data_subject
        target: webapp
        purpose: "registration_and_use"
        lawful_basis: "consent"
        data_categories: [personal_data, contact_data]
        meta:
          description: "Utente fornisce i propri dati per accedere al portale"

      - source: webapp
        target: api_gateway
        purpose: "frontend_to_backend"
        lawful_basis: "contract"
        data_categories: [PII, Analytics]
        meta:
          protocol: "HTTPS"
          encryption: "TLS1.3"

      - source: api_gateway
        target: db_main
        purpose: "account_storage"
        lawful_basis: "contract"
        data_categories: [PII]
        meta:
          interface: "JDBC"
          comment: "Writes user account data"

      - source: api_gateway
        target: analytics
        purpose: "usage_analytics"
        lawful_basis: "legitimate_interest"
        transfer_mechanism: "SCCs"
        data_categories: [Analytics]
        meta:
          tracking_id: "GA-XXXXXX"
          anonymization: true

      - source: db_main
        target: retention
        purpose: "data_retention"
        lawful_basis: "legal_obligation"
        data_categories: [PII]
        meta:
          retention_policy: "10y"
          frequency: "monthly"

      - source: api_gateway
        target: notif
        purpose: "notifications"
        lawful_basis: "consent"
        transfer_mechanism: "SCCs"
        data_categories: [Contact]
        meta:
          message_type: "transactional"
          provider: "Mailgun"
    """
    else:
        sample_yaml = """\
    nodes:
      - id: data_subject
        name: Utente / Cliente
        type: subject
        data_categories: [personal_data, contact_data]
        region: EU
        lawful_bases: [consent]
        meta:
          description: "Interessato ai sensi del GDPR"

      - id: webapp
        name: Customer Portal
        type: service
        data_categories: [PII, Analytics]
        owner: "ACME"
        region: "EU"
        role: controller
        lawful_bases: [contract]
        meta:
          business_unit: "Digital"
          reviewed_by: "Privacy Office"

      - id: db_main
        name: Primary Database
        type: datastore
        data_categories: [PII]
        region: "EU"
        role: controller
        lawful_bases: [contract]
        meta:
          encryption: "AES256"
          backup: "daily"

      - id: notif
        name: Email Service
        type: thirdparty
        data_categories: [Contact]
        region: "US"
        role: processor
        lawful_bases: [consent]
        transfer_mechanism: "SCCs"
        meta:
          vendor: "Mailgun"
          retention: "6 months"

    flows:
      - source: data_subject
        target: webapp
        purpose: "registration"
        lawful_basis: "consent"
        data_categories: [personal_data, contact_data]
        meta:
          description: "L’utente invia i propri dati per creare un account"

      - source: webapp
        target: db_main
        purpose: "account_management"
        lawful_basis: "contract"
        data_categories: [PII]
        meta:
          encryption: "TLS1.3"

      - source: webapp
        target: notif
        purpose: "notifications"
        lawful_basis: "consent"
        transfer_mechanism: "SCCs"
        data_categories: [Contact]
        meta:
          channel: "email"
          provider: "Mailgun"
    """

    out_file = Path("privacy.yaml")
    out_file.write_text(sample_yaml, encoding="utf-8")
    print(f"[OK] Template '{args.template}' creato in: {out_file.resolve()}")
    log.info(f"[INIT] privacy.yaml creato con template '{args.template}'.")


def cmd_scan(args):
    """Esegue la scansione di un sito o file HTML."""
    from pathlib import Path
    out_dir = Path(args.output)

    try:
        scan_website(
            url=args.url,
            out_dir=out_dir,
            depth=getattr(args, "depth", 1),
            insecure=getattr(args, "insecure", False)
        )
    except Exception as e:
        log.error(f"[ERR] Errore durante la scansione: {e}")


import click



@click.group()
def cli():
    pass


@cli.command()
@click.argument("key")
def license(key):
    """Attiva una licenza locale"""
    save_license(key)


def cmd_compose(args):
    """Unisce più file privacy.yaml/.json e genera i report in output"""
    from privacy_flow_map.logger import log

    out_dir = Path(args.output or "out")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Cartella di output: {out_dir}")

    try:
        compose_privacy_maps(
            input_files=[Path(f) for f in args.files],
            scan_url=args.track_from,  # ✅ usa l’argomento passato da CLI
            output_dir=out_dir,
            insecure=getattr(args, "insecure", False),
        )
        print(f"[OK] Composizione completata in: {out_dir}")
    except Exception as e:
        log.exception("[ERR] Errore durante la composizione:")
        print(f"[ERR] {e}")





def cmd_render(args):
    """Renderizza un file privacy.yaml/.json in output HTML + Mermaid"""
    try:
        render_files(args.input, args.output or "out")
        print(f"[OK] Render completato in: {args.output or 'out'}")
    except Exception as e:
        log.exception("[ERR] Errore nel render:")
        print(f"[ERR] {e}")


def cmd_license_activate(args):
    from privacy_flow_map.license_manager import activate_license_file
    activate_license_file(args.file)

def cmd_license_info(args):
    """Mostra informazioni sulla licenza attiva."""
    from privacy_flow_map.license_manager import get_active_license

    lic = get_active_license()
    if not lic.get("valid"):
        print(" Nessuna licenza valida trovata.")
        print(" Usa: privacy-flow license activate <file.json>")
        return

    plan = lic.get("plan", "community").capitalize()
    customer = lic.get("customer", "N/A")
    expires = lic.get("expires", "N/A")
    print(f"✅ Licenza {plan} per {customer} — scade il {expires}")

# --- Comando: license ---
def cmd_license_info(args):
    """Mostra informazioni sulla licenza attiva."""
    from privacy_flow_map.license_manager import get_active_license

    try:
        lic = get_active_license()
        if not lic:
            print("Nessuna licenza trovata. Usa `privacy-flow license activate <file>` per attivarla.")
            return
        print(f"Licenza valida per {lic.get('customer')} fino al {lic.get('expires')}")
    except Exception as e:
        print(f"Errore nel leggere la licenza: {e}")


def main():
    """Entry point CLI"""
    parser = argparse.ArgumentParser(
        prog="privacy-flow",
        description="Privacy Flow Map CLI",
        add_help=True  # lascia che argparse gestisca -h/--help
    )

    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # --- INIT ---
    p_init = subparsers.add_parser("init", help="Crea un template privacy.yaml")
    p_init.add_argument(
        "--template",
        choices=["base", "extended"],
        default="base",
        help="Specifica il tipo di template da generare (default: base)"
    )

    p_init.add_argument("-o", "--output", help="Percorso del file di output")
    p_init.set_defaults(fn=cmd_init)

    # --- SCAN ---
    p_scan = subparsers.add_parser("scan", help="Scansiona un sito o file HTML per identificare tracker e cookie")
    p_scan.add_argument("url", help="URL del sito o percorso file HTML da analizzare")
    p_scan.add_argument("-o", "--output", help="Cartella di output per il report HTML", default="out")
    p_scan.add_argument("--depth", type=int, default=1, help="Profondità massima di scansione (default: 1)")
    p_scan.add_argument("--insecure", action="store_true",
                        help="Disabilita la verifica SSL (solo per test o ambienti isolati)")
    p_scan.set_defaults(fn=cmd_scan)

    # --- COMPOSE ---
    p_compose = subparsers.add_parser("compose", help="Unisce più file privacy e risultati di scansione")
    p_compose.add_argument("files", nargs="+", help="Elenco file privacy.yaml/.json da unire")
    p_compose.add_argument("--default-basis", help="Base giuridica predefinita (es. consent, contract)")
    p_compose.add_argument("-o", "--output", help="Cartella di output (default: out/)")
    p_compose.add_argument("--track-from", help="URL del sito da cui importare tracker")

    p_compose.set_defaults(fn=cmd_compose)

    # --- RENDER ---
    p_render = subparsers.add_parser("render", help="Renderizza un file privacy.yaml/.json in Mermaid + HTML + JSON")
    p_render.add_argument("input", help="Percorso del file privacy.yaml o privacy.json")
    p_render.add_argument("-o", "--output", help="Cartella di output (default: out/)")
    p_render.set_defaults(fn=cmd_render)

    from privacy_flow_map import __version__ as pkg_version

    parser.add_argument(
        "--version",
        action="version",
        version=f"PrivacyFlow {pkg_version}",
        help="Mostra la versione corrente ed esce."
    )

    p_license = subparsers.add_parser("license", help="Gestione licenza")
    p_license_sub = p_license.add_subparsers(dest="license_cmd")





    #  Default: se non viene passato activate/generate, mostra info
    p_license.set_defaults(fn=cmd_license_info)
    p_license_sub.required = False
    # -------------------------

    # --- PARSING ---
    args = parser.parse_args()

    from privacy_flow_map.license_manager import get_active_license

    # --- Verifica licenza una sola volta ---
    license_info = get_active_license()

    if not license_info["valid"]:
        print("─────────────────────────────────────────────")
        print("  PrivacyFlow Community Edition")
        print("  Uso gratuito per audit e test interni.")
        print("─────────────────────────────────────────────")
    else:
        print(f"{license_info['plan'].capitalize()} License attiva per {license_info['customer']}")

    # --- FIX: Gestione speciale per "privacy-flow license" senza subcomando ---
    if getattr(args, "cmd", None) == "license" and not getattr(args, "fn", None):
        from privacy_flow_map.license_manager import load_active_license
        try:
            lic = load_active_license()
            if not lic:
                print("Nessuna licenza trovata. Usa `privacy-flow license activate <file>` per attivarla.")
            else:
                print(f"Licenza valida per {lic.get('customer')} fino al {lic.get('expires')}")
        except Exception as e:
            print(f"Errore nel leggere la licenza: {e}")
        sys.exit(0)
    # --------------------------------------------------------------------------

    # --- Esecuzione comando standard ---
    args.fn(args)



if __name__ == "__main__":
    main()
