#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JONAS - Just Operate Nicely And Securely
Copyright (C) 2025 Peter Filz

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import json
import uuid
import getpass
import tempfile
from pathlib import Path
from openai import OpenAI
from .shell_tools import run_shell_command, get_output_head, get_output_tail, search_output, display_output, get_output_raw, FUNCTION_TOOLS, delete_outputs, set_token_threshold, _output_storage
from rich.console import Console
from rich.markdown import Markdown
import sys
import io
import tty
import termios
import re
import platform

# Prüfe Betriebssystem beim Start
def check_os():
    """Prüft, ob das Betriebssystem unterstützt wird (macOS oder Linux)."""
    os_name = platform.system()
    if os_name not in ("Darwin", "Linux"):
        console = Console()
        width = 64
        console.print()
        console.print("[bold red]" + "╔" + "═" * (width - 2) + "╗" + "[/bold red]")
        console.print("[bold red]" + "║" + " " * (width - 2) + "║" + "[/bold red]")
        console.print("[bold red]" + "║" + "   JONAS ist nur für macOS und Linux verfügbar".ljust(width - 2) + "║" + "[/bold red]")
        console.print("[bold red]" + "║" + " " * (width - 2) + "║" + "[/bold red]")
        console.print("[bold red]" + "╠" + "═" * (width - 2) + "╣" + "[/bold red]")
        console.print("[bold red]" + "║" + " " * (width - 2) + "║" + "[/bold red]")
        console.print("[red]" + "║" + f"   Dein System: {os_name}".ljust(width - 2) + "║" + "[/red]")
        console.print("[bold red]" + "║" + " " * (width - 2) + "║" + "[/bold red]")
        console.print("[red]" + "║" + "   JONAS benötigt Unix-Shell-Befehle und ist nicht".ljust(width - 2) + "║" + "[/red]")
        console.print("[red]" + "║" + "   mit Windows kompatibel.".ljust(width - 2) + "║" + "[/red]")
        console.print("[bold red]" + "║" + " " * (width - 2) + "║" + "[/bold red]")
        console.print("[bold red]" + "╚" + "═" * (width - 2) + "╝" + "[/bold red]")
        console.print()
        sys.exit(1)

# OS-Prüfung durchführen
check_os()

def _transform_key(key: str) -> str:
    """Transformiert einen String durch Umkehrung der mittleren Zeichen.
    Erste und letzte 10 Zeichen bleiben unverändert.
    Funktion ist symmetrisch (Ver- und Entschlüsselung identisch).
    
    Args:
        key: Der zu transformierende String
    
    Returns:
        Transformierter String
    """
    if len(key) <= 20:
        return key  # Zu kurz, keine Transformation
    
    prefix = key[:10]
    suffix = key[-10:]
    middle = key[10:-10]
    
    # Umkehrung der mittleren Zeichen
    middle_reversed = middle[::-1]
    
    return prefix + middle_reversed + suffix

# Sanitization: Entfernt gefährliche ANSI/Control-Sequences
def sanitize_output(text: str, allow_colors: bool = True) -> str:
    """
    Entfernt gefährliche ANSI-Escape-Sequences und Control-Characters.
    Behält nur \n, \r, \t und druckbare Zeichen.
    
    Args:
        text: Der zu bereinigende Text
        allow_colors: Wenn True, werden SGR-Sequences (Farben) beibehalten
    
    Returns:
        Bereinigter Text
    """
    if not text:
        return text
    
    # Entferne gefährliche OSC-Sequences (Terminal-Links, Titel-Änderung, etc.)
    text = re.sub(r'\x1b\][^\x07]*\x07', '', text)
    text = re.sub(r'\x1b\][^\x1b]*\x1b\\', '', text)
    
    # Entferne gefährliche Cursor-Bewegungen und andere CSI-Sequences
    # Aber NICHT SGR (Select Graphic Rendition = Farben), wenn allow_colors=True
    if allow_colors:
        # Entferne nur gefährliche CSI-Sequences (nicht 'm' für Farben)
        # Cursor-Bewegung: A,B,C,D,E,F,G,H,J,K,S,T
        text = re.sub(r'\x1b\[[0-9;]*[ABCDEFGHJKSTfsu]', '', text)
    else:
        # Entferne alle CSI-Sequences inkl. Farben
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    
    # Entferne andere gefährliche ESC-Sequences (nicht CSI oder OSC)
    text = re.sub(r'\x1b[^[\]a-zA-Z]*[a-zA-Z]', '', text)
    
    # Entferne alle Control-Characters außer \n, \r, \t
    # Behalte nur: \n (0x0a), \r (0x0d), \t (0x09) und druckbare Zeichen (>= 0x20)
    sanitized = []
    for char in text:
        code = ord(char)
        if code in (0x0a, 0x0d, 0x09) or code >= 0x20:
            sanitized.append(char)
    
    return ''.join(sanitized)

# Konfigurationspfad (XDG-konform)
def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "jonas"

CONFIG_DIR = config_dir()
CONFIG_FILE = CONFIG_DIR / "config"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_TOKENLIMIT = 2000

def getpass_with_stars(prompt: str = "Password: ") -> str:
    """Passwort-Eingabe mit Sternchen-Anzeige"""
    print(prompt, end='', flush=True)
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        password = []
        while True:
            char = sys.stdin.read(1)
            if char in ('\r', '\n'):  # Enter
                print()
                break
            elif char == '\x03':  # Ctrl+C
                print()
                raise KeyboardInterrupt
            elif char in ('\x7f', '\x08'):  # Backspace
                if password:
                    password.pop()
                    # Lösche letztes Sternchen
                    print('\b \b', end='', flush=True)
            elif char >= ' ':  # Druckbare Zeichen
                password.append(char)
                print('*', end='', flush=True)
        return ''.join(password)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def parse_kv_config(text: str) -> dict:
    result = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        result[k.strip()] = v.strip()
    return result

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            cfg = parse_kv_config(CONFIG_FILE.read_text(encoding="utf-8"))
            # Transformiere API-Key zurück (Entschlüsselung)
            if 'OPENAI_API_KEY' in cfg and cfg['OPENAI_API_KEY']:
                cfg['OPENAI_API_KEY'] = _transform_key(cfg['OPENAI_API_KEY'])
            return cfg
        except Exception:
            return {}
    return {}

def write_config_secure(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, 0o700)
    except Exception:
        pass
    
    # Transformiere API-Key vor dem Speichern
    api_key = cfg.get('OPENAI_API_KEY', '')
    transformed_key = _transform_key(api_key) if api_key else ''
    
    content_lines = [
        f"OPENAI_API_KEY={transformed_key}",
        f"OPENAI_MODEL={cfg.get('OPENAI_MODEL', DEFAULT_MODEL)}",
        f"TOKENLIMIT={cfg.get('TOKENLIMIT', str(DEFAULT_TOKENLIMIT))}",
        "",
    ]
    content = "\n".join(content_lines)
    
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(CONFIG_DIR), encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    tmp_path.replace(CONFIG_FILE)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass

def interactive_configure(existing_cfg: dict = None) -> dict:
    """Interaktive Konfiguration mit Prompts"""
    if existing_cfg is None:
        existing_cfg = {}
    
    existing_api = existing_cfg.get("OPENAI_API_KEY")
    existing_model = existing_cfg.get("OPENAI_MODEL", DEFAULT_MODEL)
    existing_token = existing_cfg.get("TOKENLIMIT", str(DEFAULT_TOKENLIMIT))
    
    console.print("\n[bold cyan]Konfiguration[/bold cyan]\n")
    
    # Erklärung beim ersten Start (wenn kein API-Key vorhanden)
    if not existing_api:
        console.print("[dim]Vor der ersten Nutzung muss JONAS konfiguriert werden.[/dim]")
        console.print("[dim]Sie benötigen einen OpenAI API-Key.[/dim]")
        print()
    
    # API-Key mit Validierungs-Schleife
    available_models = []
    api_key = None
    try:
        while True:
            if existing_api:
                hint = f"(Enter = bestehenden Key behalten, aktuell: ***{existing_api[-4:]})"
                entered_key = getpass_with_stars(f"OpenAI API-Key {hint}: ").strip()
                if not entered_key:
                    api_key = existing_api
                else:
                    api_key = entered_key
            else:
                api_key = getpass_with_stars("OpenAI API-Key: ").strip()
                while not api_key:
                    console.print("[red]Ein API-Key ist erforderlich.[/red]")
                    api_key = getpass_with_stars("OpenAI API-Key: ").strip()
            
            # Zeilenumbruch nach API-Key-Eingabe
            print()
            
            # Validiere API-Key und hole Modell-Liste
            console.print("[dim]Validiere API-Key und lade Modell-Liste...[/dim]", end=" ")
            try:
                test_client = OpenAI(api_key=api_key)
                # Modell-Liste abrufen (kostenlos)
                models_response = test_client.models.list()
                available_models = [m.id for m in models_response.data]
                console.print("[green]✓ Gültig[/green]")
                print()
                break  # API-Key ist gültig, raus aus der Schleife
            except Exception as e:
                console.print("[red]✗ Ungültiger API-Key[/red]")
                console.print("[red]Bitte gültigen API-Key eingeben (Ctrl+C zum Abbrechen).[/red]")
                print()
                # Zurück zum Anfang der Schleife (existing_api bleibt erhalten)
        
        # Model mit Validierungs-Schleife
        while True:
            model = input(f"OPENAI_MODEL [{existing_model}]: ").strip()
            if not model:
                model = existing_model
            
            # Validiere Modell
            if model in available_models:
                break  # Modell ist gültig, raus aus der Schleife
            else:
                console.print(f"[red]Ungültiges Modell: '{model}'[/red]")
                console.print("[yellow]Bitte gültiges Modell eingeben (Ctrl+C zum Abbrechen).[/yellow]")
                print()
        
        # Leerzeile für harmonisches Layout
        print()
        
        # Tokenlimit mit Validierungs-Schleife
        while True:
            token_str = input(f"TOKENLIMIT [{existing_token}]: ").strip()
            if not token_str:
                token_str = existing_token
            
            try:
                token_int = int(token_str)
                if token_int <= 0:
                    raise ValueError("Muss größer als 0 sein")
                break  # Gültiger Wert, raus aus der Schleife
            except ValueError:
                console.print("[red]Ungültiger Wert. Bitte positive Ganzzahl eingeben (Ctrl+C zum Abbrechen).[/red]")
                print()
        
        final_cfg = {
            "OPENAI_API_KEY": api_key,
            "OPENAI_MODEL": model,
            "TOKENLIMIT": str(token_int),
        }
        
        write_config_secure(final_cfg)
        console.print("\n[green]Konfiguration gespeichert.[/green]")
        console.print(f"Speicherort: {CONFIG_FILE}")
        console.print(f"OPENAI_MODEL = {model}")
        console.print(f"TOKENLIMIT   = {token_int}")
        console.print(f"API-Key      = ***{api_key[-4:]}\n")
        
        return final_cfg
        
    except KeyboardInterrupt:
        console.print("\n\n[bold blue]Konfiguration abgebrochen.[/bold blue]")
        console.print("[bold blue]Auf Wiedersehen![/bold blue]")
        sys.exit(0)

# Console initialisieren (muss vor interactive_configure sein)
console = Console()

# Lade Konfiguration
cfg = load_config()
api_key = cfg.get("OPENAI_API_KEY")

# Wenn kein API-Key, interaktiv konfigurieren
if not api_key:
    cfg = interactive_configure(cfg)
    api_key = cfg.get("OPENAI_API_KEY")

# Validiere API-Key beim Start
try:
    client = OpenAI(api_key=api_key)
    # Teste mit einfachem API-Call
    client.models.list()
except Exception as e:
    console.print(f"\n[red]Fehler: Der gespeicherte API-Key ist ungültig oder wurde widerrufen.[/red]")
    console.print("[yellow]Bitte konfiguriere einen neuen API-Key.[/yellow]\n")
    cfg = interactive_configure(cfg)
    api_key = cfg.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

MODEL = cfg.get("OPENAI_MODEL", DEFAULT_MODEL)

# Setze TOKENLIMIT für shell_tools.py
token_limit = int(cfg.get("TOKENLIMIT", str(DEFAULT_TOKENLIMIT)))
set_token_threshold(token_limit)

# System-Prompt mit OS-Information
os_info = platform.system()
os_version = platform.release()

SYSTEMPROMPT = f"""Du bist JONAS, ein intelligenter Shell-Assistent.
Deine Aufgabe ist es, Benutzern bei der Systemverwaltung zu helfen, indem du Shell-Befehle ausführst und die Ergebnisse interpretierst.

SYSTEM-INFORMATION:
- Betriebssystem: {os_info} (Version: {os_version})
- JONAS läuft nur auf macOS (Darwin) und Linux
- Alle Shell-Befehle müssen Unix/Linux-kompatibel sein

Wichtige Hinweise:
- Sei präzise und hilfreich in deinen Antworten
- Achte bei der erstellung von Shell-Befehlen daruaf, dass die Ausgaben der Befehle nicht länger als nötig werden, um Token zu sparen.
- Nutze die verfügbaren Tools effizient
- Wenn Du mit einem Begfehl nicht weiter kommst, suche direkt ohne Nachfrage nach Alternativen.
- Der Anwender stellt eventuell unpräzise Fragen. Versuche dann herauszufinden, was er gemeint hat.
- Verwende Markdown in deinen Antworten - gerne auch Tabellen.

WICHTIG - Umgang mit großen Outputs:
- Wenn ein Shell-Befehl große Ausgaben erzeugt, wird diese automatisch als 'out1', 'out2', etc. gespeichert.
- Wenn der Benutzer nach einer kompletten Anzeige fragt, nutze display_output(output_id).
- display_output() zeigt dem Benutzer die komplette Ausgabe an, OHNE dass du sie analysieren musst - das spart Token.
- Nutze get_output_head(), get_output_tail() oder search_output() nur, wenn du die Daten analysieren oder filtern musst.
- Frage NICHT nach, ob der Benutzer die vollständige Ausgabe sehen möchte - wenn er "komplett" oder "alles" sagt, zeige es direkt mit display_output().

WICHTIG - Zugriff auf frühere Befehle:
- In der Konversations-Historie werden erfolgreich ausgeführte Shell-Befehle als JSON-Struktur gespeichert.
- Format: {{"answer": "deine Antwort", "executed_commands": [{{"command": "ls -la", "output_id": "out1"}}, ...]}}
- Du kannst auf diese Output-IDs auch später noch zugreifen mit get_output_head(), get_output_tail(), search_output() oder display_output().
- Wenn der Benutzer nach etwas fragt, das bereits in einem früheren Befehl abgerufen wurde, nutze die gespeicherte output_id statt den Befehl erneut auszuführen.

Gib niemals JSON mit answer/executed_commands aus.
Bestätige niemals eine ausgeführte Aktion, wenn du keinen function_call gemacht hast.
"""

# Globale Historie (nur User-Anfragen und finale Antworten)
global_history = {}

# Globale Variable für Thinking-Zeilen
_thinking_lines = 0

def add_to_global_history(session_id, user_message, assistant_response):
    """Fügt eine User-Nachricht und Assistent-Antwort zur globalen Historie hinzu.
    
    Args:
        session_id: Eindeutige Session-ID
        user_message: Die User-Nachricht
        assistant_response: Die finale Assistent-Antwort
    """
    if session_id not in global_history:
        global_history[session_id] = []
    
    global_history[session_id].extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_response}
    ])

    # Historie ggf. kürzen und verknüpfte Outputs entfernen
    trim_session_history(session_id, max_turns=15)

def get_dialog_history(session_id):
    """Gibt die Dialog-Historie für eine Session zurück.
    
    Args:
        session_id: Die Session-ID
        
    Returns:
        list: Liste der Dialog-Nachrichten
    """
    return global_history.get(session_id, [])

def trim_session_history(session_id, max_turns=15):
    """Kürzt die Session-Historie auf max_turns Paare (User/Assistant).
    Entfernt beim Trimmen auch referenzierte Output-IDs aus dem Speicher.
    
    Args:
        session_id: ID der Session
        max_turns: Maximale Anzahl an User/Assistant-Paaren, die behalten werden
    """
    history = global_history.get(session_id)
    if not history:
        return
    # Anzahl der Paare berechnen (wir fügen immer paarweise ein)
    pair_count = len(history) // 2
    if pair_count <= max_turns:
        return
    # Wie viele Paare müssen weg?
    to_remove_pairs = pair_count - max_turns
    # Sammle Output-IDs aus den zu entfernenden Assistent-Antworten
    output_ids_to_delete = []
    # Entferne von vorn jeweils User+Assistant
    for _ in range(to_remove_pairs):
        # Entferne User (falls vorhanden)
        if history and history[0].get("role") == "user":
            history.pop(0)
        # Entferne Assistant und parse eventuelle executed_commands
        if history and history[0].get("role") == "assistant":
            assistant_item = history.pop(0)
            content = assistant_item.get("content", "")
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    cmds = data.get("executed_commands")
                    if isinstance(cmds, list):
                        for c in cmds:
                            oid = c.get("output_id")
                            if isinstance(oid, str):
                                output_ids_to_delete.append(oid)
            except (json.JSONDecodeError, ValueError):
                pass
    # Outputs im Speicher löschen
    if output_ids_to_delete:
        delete_outputs(output_ids_to_delete)

def print_assistant_response(text):
    """Gibt die Assistent-Antwort als formatiertes Markdown aus."""
    if text:
        # Prüfe ob es eine JSON-Struktur ist
        display_text = text
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "answer" in data:
                # Extrahiere nur die Antwort für die Anzeige
                display_text = data["answer"]
        except (json.JSONDecodeError, ValueError):
            # Kein JSON, verwende Text direkt
            pass
        
        # Sanitize LLM-Antwort (verhindert ANSI/RTL/Zero-Width-Injection)
        display_text = sanitize_output(display_text, allow_colors=False)
        
        # Jonas-Label ausgeben
        console.print()  # Leerzeile vor der Antwort
        console.print("[bold cyan]Jonas:[/bold cyan]")
        
        # Text als Markdown parsen und ausgeben
        try:
            markdown = Markdown(display_text)
            console.print(markdown)
        except Exception:
            # Fallback: Text direkt ausgeben falls Markdown-Parsing fehlschlägt
            console.print(display_text)
        
        console.print()  # Leerzeile nach der Antwort

def show_thinking(message=None):
    """Zeigt 'Thinking' Text an.
    
    Args:
        message: Optionaler Text. Wenn None, wird "Einen Moment bitte..." angezeigt.
    """
    global _thinking_lines
    if message is None:
        message = "Einen Moment bitte..."
    
    # Berechne wie viele Zeilen die Nachricht benötigt
    term_width = get_terminal_width()
    # Entferne Markup-Tags für korrekte Längenberechnung
    message_without_markup = _strip_markup(message)
    num_lines = max(1, (_visual_len(message_without_markup) + term_width - 1) // term_width)
    _thinking_lines = num_lines
    
    console.print(f"[dim]{message}[/dim]", end="")

def clear_thinking():
    """Löscht die 'Thinking' Zeile(n)."""
    global _thinking_lines
    # Lösche alle Zeilen, die von show_thinking() ausgegeben wurden
    for _ in range(_thinking_lines):
        print("\r\033[K", end="", flush=True)
        if _ < _thinking_lines - 1:
            print("\033[F", end="", flush=True)  # Eine Zeile hoch (außer bei der letzten)
    _thinking_lines = 0

def get_terminal_width():
    """Ermittelt die Breite des Terminal-Fensters."""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except:
        return 80  # Fallback-Breite

import unicodedata

# Optionale Überschreibungen für visuelle Breiten je Codepoint
# Einige Terminals rendern bestimmte Symbole (z.B. ⚠) als Breite 1
_VISUAL_WIDTH_OVERRIDES = {
    0x26A0: 2,  # WARNING SIGN ⚠ often rendered as double-width
}

def _char_visual_width(ch: str) -> int:
    """Gibt die visuelle Breite eines Zeichens zurück (1 oder 2, 0 für kombinierende)."""
    # Kombinierende Zeichen haben Breite 0
    if unicodedata.combining(ch):
        return 0
    # Variation Selector-16 erzwingt Emoji-Präsentation, hat selbst Breite 0
    if ord(ch) == 0xFE0F:
        return 0
    # Überschreibungen
    cp = ord(ch)
    if cp in _VISUAL_WIDTH_OVERRIDES:
        return _VISUAL_WIDTH_OVERRIDES[cp]
    # Ostasiatische Breitenklassifikation
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("F", "W"):  # Fullwidth/Wide
        return 2
    # Einige Emojis sind als Neutral klassifiziert, aber sollten 2 breit sein
    # Heuristik: Zeichen im Emoji-Block behandeln wir als 2
    # (U+1F300–U+1FAFF grob abgedeckt)
    if 0x1F300 <= cp <= 0x1FAFF:
        return 2
    # Viele Symbole (z.B. ⚠) liegen in Misc Symbols/Dingbats
    if 0x2600 <= cp <= 0x27BF:  # Misc Symbols + Dingbats
        return 2
    return 1

def _visual_len(s: str) -> int:
    return sum(_char_visual_width(ch) for ch in s)

def _pad_visual(s: str, width: int) -> str:
    """Füllt s mit Spaces rechts auf, bis visuelle Breite == width."""
    cur = _visual_len(s)
    if cur >= width:
        return s
    return s + (" " * (width - cur))

# Regex für Rich-Markup-Tags: [tagname] oder [/tagname], aber nicht einzelne Ziffern wie [0]
_MARKUP_TAG_RE = re.compile(r"\[/?[a-zA-Z_][a-zA-Z0-9_]*\]")

def _strip_markup(s: str) -> str:
    """Entfernt Rich-Markup-Tags wie [magenta]...[/magenta] für Breitenberechnung."""
    return _MARKUP_TAG_RE.sub("", s)

def _clip_visual(s: str, width: int) -> str:
    """Clippt den String auf die gewünschte visuelle Breite."""
    if _visual_len(s) <= width:
        return s
    out = []
    cur = 0
    for ch in s:
        w = _char_visual_width(ch)
        if cur + w > width:
            break
        out.append(ch)
        cur += w
    return "".join(out)

def _wrap_visual(text: str, max_width: int) -> list:
    """Zeilenumbruch mit Erhalt von Mehrfach-Leerzeichen.
    Es wird bis zum Zeilenende gefüllt. Bevorzugt wird der letzte Space
    vor der Breite; wenn keiner vorhanden ist, wird hart umbrochen.
    Markup-Tags werden bei der Breitenberechnung ignoriert, aber im Output beibehalten.
    """
    lines = []
    for paragraph in text.split('\n'):
        if paragraph == "":
            lines.append("")
            continue

        # Berechne visuelle Breite ohne Markup
        stripped = _strip_markup(paragraph)
        if _visual_len(stripped) <= max_width:
            # Passt komplett in eine Zeile
            lines.append(paragraph)
            continue

        # Text muss umgebrochen werden
        # Wenn der Text Markup enthält, behalte es für die gesamte Zeile
        # (vereinfachte Lösung: Markup gilt für kompletten Text)
        has_markup = paragraph != stripped
        
        if has_markup:
            # Extrahiere öffnende und schließende Tags
            opening_tags = re.findall(r'\[[a-zA-Z_][a-zA-Z0-9_]*\]', paragraph)
            closing_tags = re.findall(r'\[/[a-zA-Z_][a-zA-Z0-9_]*\]', paragraph)
            markup_prefix = ''.join(opening_tags)
            markup_suffix = ''.join(closing_tags)
        else:
            markup_prefix = ""
            markup_suffix = ""
        
        # Text muss umgebrochen werden - arbeite mit dem Text ohne Markup
        start = 0
        n = len(stripped)
        while start < n:
            # Fülle eine Zeile bis max_width
            cur_w = 0
            idx = start
            last_space_idx = -1

            while idx < n:
                ch = stripped[idx]
                w = _char_visual_width(ch)
                if cur_w + w > max_width:
                    break
                cur_w += w
                if ch == ' ':
                    last_space_idx = idx
                idx += 1

            if idx == n:
                # Rest passt vollständig
                line_content = stripped[start:n]
                lines.append(f"{markup_prefix}{line_content}{markup_suffix}" if has_markup else line_content)
                start = n
                break

            # Zeilenumbruch bestimmen
            if last_space_idx >= start:
                # Breche am letzten Space
                line_content = stripped[start:last_space_idx + 1]
                lines.append(f"{markup_prefix}{line_content}{markup_suffix}" if has_markup else line_content)
                start = last_space_idx + 1
            else:
                # Kein Space im Fenster -> harter Umbruch
                take_w = 0
                take_idx = start
                while take_idx < n and take_w + _char_visual_width(stripped[take_idx]) <= max_width:
                    take_w += _char_visual_width(stripped[take_idx])
                    take_idx += 1
                line_content = stripped[start:take_idx]
                lines.append(f"{markup_prefix}{line_content}{markup_suffix}" if has_markup else line_content)
                start = take_idx

    return lines

def print_boxed_text(text, width=None):
    """Gibt Text in einer Box mit senkrechten Linien aus.
    
    Args:
        text: Der auszugebende Text
        width: Optionale Breite, sonst Terminal-Breite
    """
    if width is None:
        width = get_terminal_width()
    
    # Innenbreite berechnen (abzüglich der Rahmen und Padding)
    inner_width = width - 4  # 2 für Rahmen + 2 für Padding
    
    # Text in Zeilen aufteilen und umbrechen (visuelle Breite beachten)
    lines = _wrap_visual(text, inner_width)
    
    # Jede Zeile mit senkrechten Linien ausgeben
    for line in lines:
        # Padding anhand der visuellen Breite OHNE Markup berechnen
        visual_without_markup = _strip_markup(line)
        needed = inner_width - _visual_len(visual_without_markup)
        if needed < 0:
            # clippen und neu berechnen
            clipped = _clip_visual(visual_without_markup, inner_width)
            needed = inner_width - _visual_len(clipped)
            # ersetze line durch geclippte Variante (ohne Markup für diese seltenen Fälle)
            line = clipped
        padded_line = line + (" " * max(0, needed))
        console.print(f"│ {padded_line} │", highlight=False)

def print_boxed_raw(text, width=None):
    """Gibt eine einzelne Zeile ohne Umbruch aus und passt sie visuell an.
    Überschüssige Breite wird abgeschnitten, kürzere Zeilen werden gepolstert.
    """
    if width is None:
        width = get_terminal_width()
    inner_width = width - 4
    # Alle Whitespaces zu normalen Spaces normalisieren, um konsistente Breite zu erhalten
    normalized = "".join(" " if ch.isspace() else ch for ch in text)
    # Für Breite Markup entfernen
    to_measure = _strip_markup(normalized)
    clipped_plain = _clip_visual(to_measure, inner_width)
    needed = inner_width - _visual_len(clipped_plain)
    # Wir drucken die Originalzeichen mit Markup; fügen Padding anhand plain hinzu
    # Wenn plain geclippt wurde, ersetzen wir auch die Ausgabe durch geclippte Plain-Variante
    if to_measure != clipped_plain:
        out = clipped_plain
    else:
        out = normalized
    padded = out + (" " * max(0, needed))
    console.print(f"│ {padded} │")

def print_boxed_text_right(text, width=None):
    """Gibt Text rechtsbündig in einer Box aus.
    
    Args:
        text: Der auszugebende Text
        width: Optionale Breite, sonst Terminal-Breite
    """
    if width is None:
        width = get_terminal_width()
    
    # Innenbreite berechnen (abzüglich der Rahmen und Padding)
    inner_width = width - 4  # 2 für Rahmen + 2 für Padding
    
    # Visuelle Länge ohne Markup berechnen
    visual_without_markup = _strip_markup(text)
    text_len = _visual_len(visual_without_markup)
    
    # Padding links hinzufügen für rechtsbündige Ausrichtung
    padding_left = max(0, inner_width - text_len)
    padded_line = (" " * padding_left) + text
    
    # markup=False und highlight=False verhindern Farb-Interpretation
    console.print(f"│ {padded_line} │", markup=False, highlight=False)

def print_startup_screen():
    """Zeigt den Startbildschirm mit Box-Design an."""
    term_w = get_terminal_width()
    # Nutze eine Spalte weniger, um automatischen Zeilenumbruch am rechten Rand zu vermeiden
    width = max(20, term_w - 1)
    
    # Leerzeile vor der Box
    console.print()
    
    # Obere Linie
    console.print("┌" + "─" * (width - 2) + "┐")
    
    # Titel (ASCII-Art, ohne Icons)
    print_boxed_text("", width)  # Leerzeile
    print_boxed_raw("#######   #####   #     #   #####   ###### ", width)
    print_boxed_raw("     #   #     #  ##    #  #     #  #      ", width)
    print_boxed_raw("     #   #     #  # #   #  #     #  #      ", width)
    print_boxed_raw("     #   #     #  #  #  #  #######   ##### ", width)
    print_boxed_raw("#    #   #     #  #   # #  #     #       #", width)
    print_boxed_raw("#    #   #     #  #    ##  #     #       #", width)
    print_boxed_raw(" ####     #####   #     #  #     #  ###### ", width)
    print_boxed_text("", width)  # Leerzeile
    print_boxed_text("(Just Operate Nicely And Securely)", width)
    print_boxed_text_right("v1.4.5 by Peter Filz", width)
    print_boxed_text("", width)  # Leerzeile
    
    # Einleitung
    intro = "JONAS ist ein KI-gestützter Shell-Assistent, der natürliche Sprache in Shell-Befehle übersetzt. Er nutzt das umfangreiche UNIX-Wissen von Large Language Modellen, um dir bei Systemverwaltung, Monitoring und Automatisierung zu helfen."
    print_boxed_text(intro, width)
    print_boxed_text("", width)  # Leerzeile
    
    # Beschreibung
    print_boxed_text("[cyan]Gebe Anweisungen in natürlicher Sprache oder frage einfach, was Du zu Deinem System wissen möchtest.[/cyan]", width)
    print_boxed_text("", width)  # Leerzeile
    
    # Sicherheitshinweis (ohne Icons)
    print_boxed_text("[red]Shell-Befehle werden von JONAS nur nach vorheriger Bestätigung durch Dich ausgeführt.[/red]", width)
    print_boxed_text("", width)  # Leerzeile
    
    # Befehle (ohne Icons)
    print_boxed_text("VERFÜGBARE SONDERBEFEHLE IM CHAT:", width)
    print_boxed_text("", width)
    print_boxed_text("- [cyan]exit, quit, bye[/cyan]    — Chat beenden", width)
    print_boxed_text("- [cyan]new[/cyan]                — Starte neue Unterhaltung (spart Token)", width)
    print_boxed_text("- [cyan]config[/cyan]             — Konfiguration ändern", width)
    print_boxed_text("- [cyan]delconfig[/cyan]          — Konfiguration löschen und beenden", width)
    print_boxed_text("- [cyan]history[/cyan]            — Gespeicherte Session-Historie anzeigen", width)
    print_boxed_text("- [cyan]help[/cyan]               — Zeige Startbildschirm erneut", width)
    print_boxed_text("", width)  # Leerzeile
    
    # Aktuelle Konfiguration anzeigen
    current_cfg = load_config()
    api = current_cfg.get("OPENAI_API_KEY", "")
    model = current_cfg.get("OPENAI_MODEL", DEFAULT_MODEL)
    token = current_cfg.get("TOKENLIMIT", str(DEFAULT_TOKENLIMIT))
    print_boxed_text(f"[dim]Konfiguration: Model={model}, TokenLimit={token}, API-Key=***{api[-4:] if api else 'N/A'}[/dim]", width)
    print_boxed_text("", width)
    
    # Untere Linie
    console.print("└" + "─" * (width - 2) + "┘")
    console.print()  # Leerzeile nach der Box

# Tools werden aus tools.py importiert

# Tool-Definitionen werden aus tools.py importiert

def process_dialog_step(dialog_history):
    """Verarbeitet eine Dialog-Historie und gibt das finale Ergebnis als String zurück.
    
    Args:
        dialog_history: Liste von Nachrichten [{'role': 'user'/'assistant', 'content': str}]
    
    Returns:
        str: Das finale Ergebnis der Verarbeitung
    """
    if not dialog_history:
        return "Fehler: Keine Dialog-Historie vorhanden."
    
    # Extrahiere die letzte User-Nachricht
    user_message = None
    for msg in reversed(dialog_history):
        if msg.get('role') == 'user':
            user_message = msg.get('content')
            break
    
    if not user_message:
        return "Fehler: Keine User-Nachricht in der Dialog-Historie gefunden."
    
    try:
        # Konvertiere komplette Dialog-Historie (nur User + finale Assistant-Antworten)
        messages = []
        
        # System-Prompt als erste Nachricht hinzufügen
        if SYSTEMPROMPT:
            messages.append({
                "role": "system",
                "content": SYSTEMPROMPT
            })
        
        for msg in dialog_history:
            role = msg.get('role')
            content = msg.get('content')
            if role in ['user', 'assistant'] and content:
                messages.append({
                    "role": role,
                    "content": content
                })
        
        # Initiale Anfrage (ohne previous_response_id)
        response = client.responses.create(
            model=MODEL,
            tools=FUNCTION_TOOLS,
            input=messages,
        )
        
        # Verarbeite die Antwort und führe ggf. Tool-Calls aus
        final_response = _handle_response_internal(response)
        
        # Erstelle JSON-Struktur mit Antwort und ausgeführten Befehlen
        response_text = final_response.output_text or "(Keine Antwort erhalten)"
        executed_commands = getattr(final_response, '_executed_commands', [])
        
        # WICHTIG: Wenn das Modell versehentlich JSON mit executed_commands ausgibt,
        # aber wir keine echten Tool-Calls hatten, fordere es auf, den Tool-Call zu machen
        if not executed_commands:
            try:
                maybe_json = json.loads(response_text)
                if isinstance(maybe_json, dict) and "executed_commands" in maybe_json:
                    # Modell hat behauptet, Befehle ausgeführt zu haben, aber keine Tool-Calls gemacht
                    # Sende Korrektur-Nachricht ans Modell
                    correction_response = client.responses.create(
                        model=MODEL,
                        tools=FUNCTION_TOOLS,
                        previous_response_id=response.id,
                        input=[{
                            "role": "system",
                            "content": "SYSTEM-KORREKTUR: Du hast behauptet, eine Aktion ausgeführt zu haben, aber du hast KEINEN Tool-Call gemacht. Bitte führe die Aktion jetzt tatsächlich aus, indem du das entsprechende Tool aufrufst. Gib danach eine kurze Bestätigung."
                        }]
                    )
                    
                    # Verarbeite die korrigierte Antwort
                    final_response = _handle_response_internal(correction_response)
                    response_text = final_response.output_text or "(Keine Antwort erhalten)"
                    executed_commands = getattr(final_response, '_executed_commands', [])
            except (json.JSONDecodeError, ValueError):
                pass
        
        if executed_commands:
            # Erstelle JSON-Struktur
            response_data = {
                "answer": response_text,
                "executed_commands": executed_commands
            }
            return json.dumps(response_data, ensure_ascii=False)
        else:
            # Keine Befehle ausgeführt, gebe nur die Antwort zurück
            return response_text
        
    except Exception as e:
        return f"Fehler bei der Verarbeitung: {e}"

def _make_tool_output(call_id: str, result: str, use_new: bool) -> dict:
    """Erstellt Tool-Output im korrekten Schema (alt oder neu).
    
    Args:
        call_id: Die Tool-Call-ID
        result: Das Ergebnis des Tool-Calls
        use_new: True für neues Schema (tool_output), False für altes (function_call_output)
    
    Returns:
        Tool-Output-Dictionary im korrekten Format
    """
    if use_new:
        return {"type": "tool_output", "tool_call_id": call_id, "output": str(result)}
    else:
        return {"type": "function_call_output", "call_id": call_id, "output": str(result)}

def _handle_response_internal(response, max_iterations=10):
    """Interne Funktion zur Verarbeitung von Antworten mit Tool-Calls.
    Verarbeitet iterativ alle Tool-Calls bis keine mehr vorhanden sind.
    
    Args:
        response: Die initiale Response vom OpenAI API
        max_iterations: Maximale Anzahl von Tool-Call-Iterationen (Schutz vor Endlosschleifen)
    
    Returns:
        Die finale Response ohne weitere Tool-Calls
    """
    current_response = response
    iteration = 0
    executed_commands = []  # Trackt erfolgreich ausgeführte Shell-Befehle
    
    while iteration < max_iterations:
        iteration += 1
        
        # Sammle alle Tool-Calls aus der aktuellen Response
        tool_calls = []
        use_new_schema = False  # Flag für API-Version
        
        for item in getattr(current_response, "output", []) or []:
            # Unterstütze beide API-Versionen: "function_call" (alt) und "tool_call" (neu)
            item_type = getattr(item, "type", None)
            if item_type in ("function_call", "tool_call"):
                # Erkennen, ob neues Schema (tool_call) verwendet wurde
                if item_type == "tool_call":
                    use_new_schema = True
                
                # Unterstütze beide Attribute: "call_id" (alt) und "tool_call_id" (neu)
                tool_call_id = getattr(item, "tool_call_id", None) or getattr(item, "call_id", None)
                tool_name = getattr(item, "name", None)
                args_obj = getattr(item, "arguments", None)
                if isinstance(args_obj, str):
                    args_obj = json.loads(args_obj)
                
                # Sanitize alle String-Argumente vom LLM (zentrale Stelle!)
                # Dies verhindert ANSI-Injection und optische Täuschungen
                sanitized_args = {}
                for key, value in args_obj.items():
                    if isinstance(value, str):
                        sanitized_args[key] = sanitize_output(value, allow_colors=False)
                    else:
                        sanitized_args[key] = value
                
                tool_calls.append({
                    "call_id": tool_call_id,
                    "name": tool_name,
                    "arguments": sanitized_args
                })
        
        # Wenn keine Tool-Calls mehr vorhanden sind, sind wir fertig
        if not tool_calls:
            # Speichere ausgeführte Befehle in der Response
            current_response._executed_commands = executed_commands
            return current_response
        
        # Führe alle Tool-Calls aus
        tool_outputs = []
        
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call['name']
            
            # Unterscheide zwischen Tools, die Sicherheitsabfrage benötigen und solchen, die es nicht tun
            if tool_name == "run_shell_command":
                # Thinking-Text löschen vor Sicherheitsabfrage
                clear_thinking()
                
                # Sicherheitsabfrage
                # Argumente sind bereits zentral sanitized (siehe oben)
                command = tool_call['arguments'].get('command', '')
                intention = tool_call['arguments'].get('intention', '')
                readonly = tool_call['arguments'].get('readonly', False)
                
                # Farbe basierend auf readonly-Flag: Magenta für readonly, Rot für schreibend
                color = "magenta" if readonly else "red"
                
                # Berechne wie viele Zeilen die Ausgabe benötigt
                term_width = get_terminal_width()
                intention_text = f"Intention: {intention}"
                command_text = f"Befehl:    {command}"
                
                # Berechne Anzahl der Zeilen (inkl. Umbrüche)
                # Verwende _visual_len für korrekte Breitenberechnung
                intention_lines = max(1, (_visual_len(intention_text) + term_width - 1) // term_width)
                command_lines = max(1, (_visual_len(command_text) + term_width - 1) // term_width)
                total_lines = intention_lines + command_lines + 1  # +1 für Eingabezeile
                
                # Formatierte Sicherheitsabfrage ausgeben (Farbe abhängig von readonly)
                # Wiederhole die Frage bei ungültiger Eingabe
                confirm = None
                while confirm not in ("j", "ja", "y", "n", "nein", "no"):
                    console.print(f"Intention: [{color}]{intention}[/{color}]")
                    console.print(f"Befehl:    [{color}]{command}[/{color}]")
                    confirm = input("Ausführen? [j/N] ").strip().lower()
                    
                    # Bei ungültiger Eingabe: Zeilen löschen und erneut fragen
                    if confirm not in ("j", "ja", "y", "n", "nein", "no"):
                        for _ in range(total_lines):
                            print("\033[F\033[K", end="", flush=True)
                        continue
                    
                    # Alle Zeilen löschen nach gültiger Antwort
                    for _ in range(total_lines):
                        print("\033[F\033[K", end="", flush=True)
                    break
                
                # Thinking-Text wieder anzeigen wenn Tool ausgeführt wird
                if confirm in ("j", "ja", "y"):
                    show_thinking(f"Führe aus: {command}")
                
                if confirm not in ("j", "ja", "y"):
                    result = "Befehl wurde vom Benutzer abgebrochen."
                else:
                    # Tool ausführen
                    result = run_shell_command(command, intention)
                    
                    # Tracke ALLE ausgeführten Befehle (auch fehlgeschlagene)
                    # Dies ist wichtig, damit Jonas weiß, welche Befehle bereits ausgeführt wurden
                    
                    # Prüfe auf kleine Ausgabe mit versteckter Output-ID
                    if result.startswith("__STORED_AS_"):
                        match = re.match(r"__STORED_AS_(out\d+)__\|(.*)", result, re.DOTALL)
                        if match:
                            output_id = match.group(1)
                            actual_output = match.group(2)
                            executed_commands.append({
                                "command": command,
                                "output_id": output_id
                            })
                            # Ersetze result durch die eigentliche Ausgabe (ohne Marker)
                            result = actual_output
                    # Prüfe auf große Ausgabe
                    elif result.startswith("SUCCESS:") and "stored as '" in result:
                        match = re.search(r"stored as '(out\d+)'", result)
                        if match:
                            output_id = match.group(1)
                            executed_commands.append({
                                "command": command,
                                "output_id": output_id
                            })
                    else:
                        # Befehl wurde ausgeführt, aber hat keine Output-ID (z.B. Fehler)
                        # Tracke ihn trotzdem, damit Jonas weiß, dass er ausgeführt wurde
                        executed_commands.append({
                            "command": command,
                            "output_id": None
                        })
            
            elif tool_name == "get_output_head":
                # get_output_head benötigt keine Sicherheitsabfrage
                output_id = tool_call['arguments'].get('output_id', '')
                num_lines = tool_call['arguments'].get('num_lines', 10)
                result = get_output_head(output_id, num_lines)
            
            elif tool_name == "get_output_tail":
                # get_output_tail benötigt keine Sicherheitsabfrage
                output_id = tool_call['arguments'].get('output_id', '')
                num_lines = tool_call['arguments'].get('num_lines', 10)
                result = get_output_tail(output_id, num_lines)
            
            elif tool_name == "search_output":
                # search_output benötigt keine Sicherheitsabfrage
                output_id = tool_call['arguments'].get('output_id', '')
                search_term = tool_call['arguments'].get('search_term', '')
                max_results = tool_call['arguments'].get('max_results', 10)
                result = search_output(output_id, search_term, max_results)
            
            elif tool_name == "display_output":
                # display_output zeigt Output direkt an User, ohne ihn ans LLM zu senden
                output_id = tool_call['arguments'].get('output_id', '')
                result = display_output(output_id)
                
                # Prüfe auf speziellen Marker
                if result.startswith("__DISPLAY_OUTPUT__|"):
                    output_id = result.split("|")[1]
                    raw_output = get_output_raw(output_id)
                    
                    # Sanitize: Entferne gefährliche ANSI/Control-Sequences
                    raw_output = sanitize_output(raw_output)
                    
                    # Thinking-Text löschen vor Ausgabe
                    clear_thinking()
                    
                    # Ausgabe mit lila Trennlinien
                    term_width = get_terminal_width()
                    separator = "─" * (term_width - 1)
                    console.print(f"[magenta]{separator}[/magenta]")
                    console.print(raw_output, markup=False, highlight=False)
                    console.print(f"[magenta]{separator}[/magenta]")
                    
                    # Thinking-Text wieder anzeigen
                    show_thinking()
                    
                    # Ans LLM nur Bestätigung senden
                    result = f"Output '{output_id}' wurde dem Benutzer vollständig angezeigt."
            
            else:
                result = f"Unbekanntes Tool: {tool_name}"
            
            # Tool-Output sammeln (output muss ein String sein, kein Array)
            # Verwende korrektes Schema basierend auf dem vom Modell verwendeten Typ
            tool_outputs.append(_make_tool_output(tool_call["call_id"], result, use_new_schema))
        
        # Alle Ergebnisse zurück ans Modell
        new_response = client.responses.create(
            model=MODEL,
            tools=FUNCTION_TOOLS,
            previous_response_id=current_response.id,
            input=tool_outputs,
        )
        
        # Übertrage die executed_commands zur neuen Response
        # (wichtig, damit sie nicht verloren gehen bei mehreren Iterationen)
        current_response = new_response
        
        # Schleife läuft weiter und prüft, ob die neue Response weitere Tool-Calls enthält
    
    # Wenn wir hier ankommen, wurde das Maximum erreicht
    console.print(f"[red]Warnung: Maximale Anzahl von Tool-Call-Iterationen ({max_iterations}) erreicht![/red]")
    
    # Informiere das Modell über das Limit, damit es dem User eine Erklärung geben kann
    error_message = f"SYSTEM: Maximale Anzahl von Tool-Aufrufen ({max_iterations}) erreicht. Bitte fasse zusammen, was bisher erreicht wurde, und erkläre dem Benutzer die Situation."
    
    # Sende Fehlermeldung als finalen Input ans Modell
    final_response = client.responses.create(
        model=MODEL,
        tools=FUNCTION_TOOLS,
        previous_response_id=current_response.id,
        input=[{
            "type": "input_text",
            "text": error_message,
        }],
    )
    
    # Speichere ausgeführte Befehle auch bei Timeout
    final_response._executed_commands = executed_commands
    
    return final_response

def handle_response(response, conversation_id=None):
    """Legacy-Funktion für Kompatibilität - verarbeitet eine Modell-Antwort und führt ggf. Tool-Calls aus."""
    final_response = _handle_response_internal(response)
    print_assistant_response(final_response.output_text)
    return final_response

def main():
    """Hauptfunktion für den interaktiven Chat mit globaler Historie."""
    # Prüfe auf --version oder --help Parameter
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--version", "-v"):
            from . import __version__
            print(f"JONAS version {__version__}")
            sys.exit(0)
        elif arg in ("--help", "-h"):
            print("JONAS - Just Operate Nicely And Securely")
            print()
            print("Ein intelligenter Shell-Assistent mit OpenAI Integration.")
            print()
            print("Verwendung:")
            print("  jonas              Startet den interaktiven Chat")
            print("  jonas --version    Zeigt die Version an")
            print("  jonas --help       Zeigt diese Hilfe an")
            print()
            print("Im Chat verfügbare Befehle:")
            print("  exit, quit, bye    Chat beenden")
            print("  new                Neue Unterhaltung starten (spart Token)")
            print("  config             Konfiguration ändern")
            print("  delconfig          Konfiguration löschen")
            print("  history            Session-Historie anzeigen")
            print("  help               Startbildschirm erneut anzeigen")
            print()
            print("Weitere Informationen: https://github.com/peter-filz/jonas")
            sys.exit(0)
        else:
            print(f"Unbekannter Parameter: {sys.argv[1]}")
            print("Verwende 'jonas --help' für Hilfe.")
            sys.exit(1)
    
    print_startup_screen()
    
    import uuid
    session_id = str(uuid.uuid4())  # Eindeutige Session-ID
    
    while True:
        try:
            # Benutzereingabe
            user_input = input("\033[1;36mDu:\033[0m ").strip()
            
            # Formatiere die Eingabe um: Lösche die Zeile und gebe sie neu formatiert aus
            if user_input:
                # Berechne wie viele Zeilen die Eingabe mit "Du: " Präfix einnimmt
                term_width = get_terminal_width()
                input_with_prefix = f"Du: {user_input}"
                num_lines = max(1, (len(input_with_prefix) + term_width - 1) // term_width)
                
                # Lösche alle Zeilen der ursprünglichen Eingabe
                for _ in range(num_lines):
                    print("\033[F\033[K", end="", flush=True)
                
                # Gebe "Du:" und Eingabe auf separaten Zeilen aus
                console.print("[bold cyan]Du:[/bold cyan]")
                console.print(user_input)
            
            # Leere Eingabe ignorieren
            if user_input == "":
                continue
            
            # Exit-Bedingungen
            if user_input.lower() in ("exit", "quit", "bye"):
                console.print("[bold blue]Auf Wiedersehen![/bold blue]")
                break
            
            # Neue Unterhaltung starten
            if user_input.lower() == "new":
                session_id = str(uuid.uuid4())  # Neue Session-ID
                # Lösche alle Output-Zwischenspeicher (out1, out2, etc.)
                if _output_storage:
                    delete_outputs(list(_output_storage.keys()))
                console.print("[green]Neue Unterhaltung gestartet. Historie und Outputs gelöscht.[/green]\n")
                continue
            
            # Spezielle Befehle
            if user_input.lower() in ("config", "configure"):
                cfg = load_config()
                interactive_configure(cfg)
                # Neu laden nach Konfiguration
                cfg = load_config()
                global MODEL, client
                MODEL = cfg.get("OPENAI_MODEL", DEFAULT_MODEL)
                client = OpenAI(api_key=cfg.get("OPENAI_API_KEY"))
                # Aktualisiere TOKENLIMIT
                token_limit = int(cfg.get("TOKENLIMIT", str(DEFAULT_TOKENLIMIT)))
                set_token_threshold(token_limit)
                continue
            
            if user_input.lower() == "delconfig":
                if CONFIG_FILE.exists():
                    try:
                        CONFIG_FILE.unlink()
                        console.print("[green]Konfiguration gelöscht.[/green]")
                    except Exception as e:
                        console.print(f"[red]Fehler beim Löschen: {e}[/red]")
                else:
                    console.print("[yellow]Keine Konfiguration vorhanden.[/yellow]")
                console.print("[bold blue]Auf Wiedersehen![/bold blue]")
                break
            
            if user_input.lower() == "history":
                history = get_dialog_history(session_id)
                if not history:
                    console.print("[dim]Keine Historie vorhanden.[/dim]\n")
                else:
                    # Trennlinien hinzufügen
                    term_width = get_terminal_width()
                    separator = "─" * (term_width - 1)
                    console.print(f"[magenta]{separator}[/magenta]")
                    console.print("[bold cyan]Session-Historie:[/bold cyan]")
                    console.print(f"[magenta]{separator}[/magenta]\n")
                    
                    for i, msg in enumerate(history):
                        if msg["role"] == "user":
                            # Sanitize User-Eingabe (könnte theoretisch auch manipuliert sein)
                            user_content = sanitize_output(msg['content'], allow_colors=False)
                            console.print(f"[bold cyan]Du:[/bold cyan]")
                            console.print(f"{user_content}\n")
                        else:  # assistant
                            # Versuche JSON zu parsen
                            content = msg['content']
                            display_text = content
                            executed_cmds = None
                            
                            try:
                                data = json.loads(content)
                                if isinstance(data, dict) and "answer" in data:
                                    display_text = data["answer"]
                                    executed_cmds = data.get("executed_commands", [])
                            except (json.JSONDecodeError, ValueError):
                                pass
                            
                            # Sanitize LLM-Antwort
                            display_text = sanitize_output(display_text, allow_colors=False)
                            
                            console.print(f"[bold cyan]Jonas:[/bold cyan]")
                            try:
                                markdown = Markdown(display_text)
                                console.print(markdown)
                            except Exception:
                                console.print(display_text)
                            
                            # Zeige ausgeführte Befehle an
                            if executed_cmds:
                                console.print("[dim]Ausgeführte Befehle:[/dim]")
                                for cmd in executed_cmds:
                                    output_id = cmd.get('output_id')
                                    if output_id:
                                        console.print(f"  [dim]• {cmd['command']} → {output_id}[/dim]")
                                    else:
                                        console.print(f"  [dim]• {cmd['command']} (kein Output gespeichert)[/dim]")
                            
                            console.print()
                    
                    # Abschließende Trennlinie
                    console.print(f"[magenta]{separator}[/magenta]")
                continue
            
            if user_input.lower() == "help":
                print_startup_screen()
                continue
            
            # Aktuelle Dialog-Historie abrufen und neue User-Nachricht hinzufügen
            current_history = get_dialog_history(session_id).copy()
            current_history.append({"role": "user", "content": user_input})
            
            # Dialog-Schritt verarbeiten mit "Thinking"-Anzeige
            show_thinking()
            
            # Verwende die neue process_dialog_step Funktion
            assistant_response = process_dialog_step(current_history)
            
            # Thinking-Text löschen
            clear_thinking()
            
            # Antwort ausgeben
            print_assistant_response(assistant_response)
            
            # Zur globalen Historie hinzufügen (nur User-Anfrage und finale Antwort)
            add_to_global_history(session_id, user_input, assistant_response)
            
        except KeyboardInterrupt:
            console.print("\n\n[bold blue]Chat durch Ctrl+C beendet![/bold blue]")
            break
        except Exception as e:
            console.print(f"\n[red]Fehler:[/red] {e}")
            console.print("[yellow]Versuche es erneut...[/yellow]\n")

if __name__ == "__main__":
    main()