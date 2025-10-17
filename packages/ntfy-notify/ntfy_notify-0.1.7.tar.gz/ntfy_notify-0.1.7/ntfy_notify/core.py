import logging
import sys
import tomllib
from typing import Optional

import click  # macht das CLI schöner
import requests

# ----------------------------------------------------------------------
# Hilfsfunktion: Konfiguration laden (einmalig, cached)
# ----------------------------------------------------------------------
_config_cache: Optional[dict] = None

# /home/m/.config/ntfy_notify/config.toml
import os
from pathlib import Path

def get_cfg_path() -> Path:
    """
    Liefert den Pfad zur ntfy‑Notify‑Konfigurationsdatei.

    Reihenfolge der Suche:
    1. Umgebungsvariable NTFY-CONFIG (vollständiger Pfad)
    2. $XDG_CONFIG_HOME/ntfy_notify/config.toml  (falls gesetzt)
    3. ~/.config/ntfy_notify/config.toml
    4. Fallback‑Pfad für den Benutzer „m“
    """
    # 1️⃣ NTFY-CONFIG (kann ein absoluter Pfad sein)
    env_path = os.getenv("NTFY-CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # 2️⃣ XDG_CONFIG_HOME, falls definiert
    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg:
        candidate = Path(xdg) / "ntfy_notify" / "config.toml"
        if candidate.is_file():
            return candidate.resolve()

    # 3️⃣ Standard‑User‑Config (HOME/.config/…)
    home_cfg = Path.home() / ".config" / "ntfy_notify" / "config.toml"
    if home_cfg.is_file():
        return home_cfg.resolve()

    # 4️⃣ Harte Kodierung für den speziellen Nutzer „m”
    fallback = Path("/home/m/.config/ntfy-notify/config.toml")
    return fallback.resolve()

def load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    cfg_path = get_cfg_path()
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Konfigurationsdatei fehlt: {cfg_path}")

    with cfg_path.open("rb") as f:
        _config_cache = tomllib.load(f)

    return _config_cache


# ----------------------------------------------------------------------
# Bibliotheks‑API
# ----------------------------------------------------------------------
def send_notification(
    message: str,
    *,
    topic: Optional[str] = None,
    title: str = "",
    priority: str = "default",
    tags: str = "",
    click_url: str = "",
    actions: str = "",
    server: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    """
    Sendet eine ntfy‑Nachricht.

    Alle Parameter können entweder explizit übergeben oder aus der
    Konfigurationsdatei übernommen werden.
    """
    cfg = load_config()
    server = server or cfg.get("server")
    token  = token  or cfg.get("token")
    topic  = topic  or cfg.get("default_topic")

    if not all([server, token, topic]):
        raise ValueError("Server, Token und Topic müssen definiert sein.")

    url = f"{server.rstrip('/')}/{topic}"
    payload = message.encode("utf-8")

    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
        "Click": click_url,
        "Actions": actions,
        "Markdown": "yes",
        "Authorization": f"Bearer {token}",
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logging.info("Nachricht erfolgreich gesendet: %s", message)
    except requests.RequestException as exc:
        logging.error("Fehler beim Senden der Nachricht: %s", exc)
        raise


# ----------------------------------------------------------------------
# CLI‑Wrapper (Click)
# ----------------------------------------------------------------------
@click.command()
@click.option("-m", "--message", required=True, help="Nachrichtentext (Markdown möglich)")
@click.option("-t", "--topic", help="ntfy‑Topic (überschreibt default)")
@click.option("-T", "--title", default="", help="Titel der Nachricht")
@click.option("-r", "--priority", default="default", help="Priorität (default, high, urgent …)")
@click.option("-g", "--tags", default="", help="Kommagetrennte Tags")
@click.option("-c", "--click", default="", help="Click‑URL")
@click.option("-a", "--actions", default="", help="Aktionen (Button‑Definitionen)")
def cli_entrypoint(
        message: str,
        topic: Optional[str] = None,
        title: str = "",
        priority: str = "default",
        tags: str = "",
        click: str = "",
        actions: str = "",
        server: Optional[str] = None,
        token: Optional[str] = None,
):
    """Kommandozeilen‑Interface für ntfy‑Benachrichtigungen."""
    try:
        send_notification(
            message=message,
            topic=topic,
            title=title,
            priority=priority,
            tags=tags,
            click_url=click,
            actions=actions,
            server=server,
            token=token,
        )
        logging.info("✅ Nachricht erfolgreich gesendet")
    except Exception as e:
        logging.error(f"❌ Fehler beim Senden der Nachricht: {e}")
        sys.exit(1)


# ----------------------------------------------------------------------
# Für Nutzer, die das Modul *ohne* Click verwenden wollen
# ----------------------------------------------------------------------
if __name__ == "__main__":
    cli_entrypoint()
