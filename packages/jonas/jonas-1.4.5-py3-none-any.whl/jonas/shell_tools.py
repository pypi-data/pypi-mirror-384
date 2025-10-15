#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JONAS - Shell Tools Module
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

import subprocess
import os

# Versuche tiktoken zu importieren, falls verfügbar
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Globaler Speicher für Command-Ausgaben
_output_storage = {}
_output_counter = 0

# Token-Schwellenwert für direkte Rückgabe vs. Speicherung (Default)
TOKEN_THRESHOLD = 300

def set_token_threshold(threshold: int):
    """Setzt den Token-Schwellenwert für Output-Speicherung.
    
    Args:
        threshold: Maximale Anzahl Tokens für direkte Rückgabe
    """
    global TOKEN_THRESHOLD
    TOKEN_THRESHOLD = threshold

def _count_tokens(text: str, model: str = "gpt-4") -> int:
    """Zählt die Anzahl der Tokens in einem Text.
    
    Args:
        text: Der zu zählende Text
        model: Das Modell für die Token-Zählung (default: gpt-4)
    
    Returns:
        Anzahl der Tokens
    """
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            pass
    
    # Fallback: Grobe Schätzung (1 Token ≈ 4 Zeichen)
    return len(text) // 4

def run_shell_command(command: str, intention: str) -> str:
    """Run a shell command on the local machine (macOS/Linux).
    
    For small outputs (<300 tokens), returns the output directly.
    For large outputs (≥300 tokens), stores it in a buffer and returns a reference.
    """
    global _output_counter, _output_storage
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,  # Nicht automatisch Exception werfen, wir prüfen manuell
            capture_output=True,
            text=True,
            timeout=300,  # Timeout: 5 Minuten für längere Befehle wie apt-get upgrade
        )
        
        # Prüfe auf Fehler (nur Exit Code != 0)
        # Hinweis: stderr wird nicht mehr als Fehlerindikator verwendet, da viele
        # erfolgreiche Befehle (curl, git, npm, etc.) auch nach stderr schreiben
        if result.returncode != 0:
            # Fehler aufgetreten - NICHT speichern
            # Kombiniere stdout und stderr für vollständige Fehlermeldung
            error_parts = []
            if result.stderr and result.stderr.strip():
                error_parts.append(result.stderr.strip())
            if result.stdout and result.stdout.strip():
                error_parts.append(result.stdout.strip())
            error_msg = "\n".join(error_parts) if error_parts else "(keine Fehlermeldung)"
            output = f"Fehler (Exit Code {result.returncode}):\n{error_msg}"
            return output  # Direkt zurückgeben ohne Speicherung
        else:
            # Erfolgreiche Ausführung (Exit Code 0)
            # Kombiniere stdout und stderr, da manche Befehle ihre Ausgabe nach stderr schreiben
            output_parts = []
            if result.stdout and result.stdout.strip():
                output_parts.append(result.stdout.strip())
            if result.stderr and result.stderr.strip():
                output_parts.append(result.stderr.strip())
            output = "\n".join(output_parts) if output_parts else "(kein Output)"
            
    except subprocess.TimeoutExpired:
        return "Fehler: Befehl hat das Timeout von 5 Minuten (300 Sekunden) überschritten"
    except Exception as e:
        return f"Exception: {e}"
    
    # Ab hier nur erfolgreiche Befehle
    # Token-Anzahl und Zeilenanzahl ermitteln
    token_count = _count_tokens(output)
    total_lines = len(output.split('\n'))
    
    # IMMER im Dictionary speichern (auch kleine Ausgaben für History-Tracking)
    _output_counter += 1
    output_id = f"out{_output_counter}"
    _output_storage[output_id] = output
    
    # Bei kleinen Ausgaben: Direkt zurückgeben (aber im Hintergrund gespeichert)
    if token_count < TOKEN_THRESHOLD:
        return f"__STORED_AS_{output_id}__|{output}"
    
    # Bei großen Ausgaben: Nur Referenz zurückgeben
    return f"SUCCESS: Large output ({token_count} tokens, {total_lines} lines) stored as '{output_id}'. Use get_output_head(), get_output_tail() or search_output() to retrieve specific parts."


def get_output_head(output_id: str, num_lines: int = 10) -> str:
    """Retrieves the first N lines from a stored command output.
    
    Args:
        output_id: The output identifier (e.g., 'out1', 'out2', etc.)
        num_lines: Number of lines to retrieve (default: 10, max: 100)
    
    Returns:
        The first N lines or an error message if not found.
    """
    if output_id not in _output_storage:
        available = ", ".join(_output_storage.keys()) if _output_storage else "keine"
        return f"Fehler: Output-ID '{output_id}' nicht gefunden. Verfügbare IDs: {available}"
    
    output = _output_storage[output_id]
    lines = output.split('\n')
    total_lines = len(lines)
    
    # Begrenzung auf maximal 100 Zeilen
    num_lines = min(max(1, num_lines), 100)
    num_lines = min(num_lines, total_lines)
    
    selected_lines = lines[:num_lines]
    result = '\n'.join(selected_lines)
    
    # Token-Limit prüfen
    output_text = f"Erste {num_lines} Zeilen von {total_lines}:\n{result}"
    if _count_tokens(output_text) >= TOKEN_THRESHOLD:
        return "Die Ausgabe überschreitet die zulässige Größe. Bitte ändere Deine Anforderung so, dass das Ergebnis weniger Token enthält."
    
    return output_text

def get_output_tail(output_id: str, num_lines: int = 10) -> str:
    """Retrieves the last N lines from a stored command output.
    
    Args:
        output_id: The output identifier (e.g., 'out1', 'out2', etc.)
        num_lines: Number of lines to retrieve (default: 10, max: 100)
    
    Returns:
        The last N lines or an error message if not found.
    """
    if output_id not in _output_storage:
        available = ", ".join(_output_storage.keys()) if _output_storage else "keine"
        return f"Fehler: Output-ID '{output_id}' nicht gefunden. Verfügbare IDs: {available}"
    
    output = _output_storage[output_id]
    lines = output.split('\n')
    total_lines = len(lines)
    
    # Begrenzung auf maximal 100 Zeilen
    num_lines = min(max(1, num_lines), 100)
    num_lines = min(num_lines, total_lines)
    
    selected_lines = lines[-num_lines:]
    start_line = total_lines - num_lines + 1
    result = '\n'.join(selected_lines)
    
    # Token-Limit prüfen
    output_text = f"Letzte {num_lines} Zeilen (Zeilen {start_line}-{total_lines}):\n{result}"
    if _count_tokens(output_text) >= TOKEN_THRESHOLD:
        return "Die Ausgabe überschreitet die zulässige Größe. Bitte ändere Deine Anforderung so, dass das Ergebnis weniger Token enthält."
    
    return output_text

def search_output(output_id: str, search_term: str, max_results: int = 10) -> str:
    """Searches for a term in a stored command output and returns matches with context.
    
    Args:
        output_id: The output identifier (e.g., 'out1', 'out2', etc.)
        search_term: The term to search for (case-insensitive)
        max_results: Maximum number of result blocks to return (default: 10)
    
    Returns:
        Search results with 5 lines of context before and after each match.
    """
    if output_id not in _output_storage:
        available = ", ".join(_output_storage.keys()) if _output_storage else "keine"
        return f"Fehler: Output-ID '{output_id}' nicht gefunden. Verfügbare IDs: {available}"
    
    output = _output_storage[output_id]
    lines = output.split('\n')
    total_lines = len(lines)
    
    # Finde alle Zeilen mit dem Suchbegriff (case-insensitive)
    search_lower = search_term.lower()
    matches = []
    for i, line in enumerate(lines):
        if search_lower in line.lower():
            matches.append(i)
    
    if not matches:
        return f"Keine Treffer für '{search_term}' in {output_id} gefunden."
    
    # Zu viele Treffer?
    if len(matches) > max_results * 3:  # Grobe Schätzung
        return f"Zu viele Treffer ({len(matches)}) für '{search_term}' gefunden. Bitte präzisiere deine Suche."
    
    # Erstelle Blöcke mit Kontext (5 Zeilen davor und danach)
    blocks = []
    i = 0
    while i < len(matches):
        start = max(0, matches[i] - 5)
        end = matches[i] + 5
        
        # Fasse benachbarte Treffer zusammen (innerhalb von 10 Zeilen)
        while i + 1 < len(matches) and matches[i + 1] <= end + 5:
            i += 1
            end = matches[i] + 5
        
        end = min(total_lines - 1, end)
        blocks.append((start, end))
        i += 1
    
    # Zu viele Blöcke?
    if len(blocks) > max_results:
        return f"Zu viele Treffer-Blöcke ({len(blocks)}) für '{search_term}' gefunden. Bitte präzisiere deine Suche."
    
    # Formatiere die Ergebnisse
    results = []
    for start, end in blocks:
        block_lines = lines[start:end + 1]
        block_text = '\n'.join(block_lines)
        results.append(f"Gefunden in diesem Block (Zeile {start + 1} bis {end + 1}):\n{block_text}")
    
    header = f"Gefunden {len(matches)} Treffer für '{search_term}' in {len(blocks)} Block(en):\n\n"
    output_text = header + "\n\n".join(results)
    
    # Token-Limit prüfen
    if _count_tokens(output_text) >= TOKEN_THRESHOLD:
        return "Die Ausgabe überschreitet die zulässige Größe. Bitte ändere Deine Anforderung so, dass das Ergebnis weniger Token enthält."
    
    return output_text

def display_output(output_id: str) -> str:
    """Displays the full stored output directly to the user without sending it to the LLM.
    This is useful for large outputs that the user wants to see but the LLM doesn't need to process.
    
    Args:
        output_id: The output identifier (e.g., 'out1', 'out2', etc.)
    
    Returns:
        A special marker that triggers direct display in jonas.py
    """
    if output_id not in _output_storage:
        available = ", ".join(_output_storage.keys()) if _output_storage else "keine"
        return f"Fehler: Output-ID '{output_id}' nicht gefunden. Verfügbare IDs: {available}"
    
    # Spezieller Marker, der jonas.py signalisiert, den Output direkt anzuzeigen
    return f"__DISPLAY_OUTPUT__|{output_id}"

# Interner Helper (nicht als Tool exponiert): gibt den Roh-Output zurück
def get_output_raw(output_id: str) -> str:
    """Liefert den gespeicherten Roh-Output zu einer output_id oder eine Fehlermeldung.
    Hinweis: Diese Funktion ist für den internen Gebrauch in jonas.py gedacht und wird NICHT
    in FUNCTION_TOOLS exponiert, um große Texte nicht in die Chat-Historie zu senden.
    """
    if output_id not in _output_storage:
        available = ", ".join(_output_storage.keys()) if _output_storage else "keine"
        return f"Fehler: Output-ID '{output_id}' nicht gefunden. Verfügbare IDs: {available}"
    return _output_storage[output_id]

# Interner Helper (nicht als Tool exponiert): löscht gespeicherte Outputs
def delete_output(output_id: str) -> bool:
    """Löscht einen gespeicherten Output anhand der ID.
    
    Args:
        output_id: ID wie 'out1', 'out2', ...
    
    Returns:
        True, wenn gelöscht; False, wenn ID nicht vorhanden war.
    """
    if output_id in _output_storage:
        try:
            del _output_storage[output_id]
        except Exception:
            # Im Fehlerfall still sein; Rückgabe False aus Konsistenzgründen
            return False
        return True
    return False

def delete_outputs(output_ids) -> int:
    """Löscht mehrere gespeicherte Outputs.
    
    Args:
        output_ids: Iterable von Output-IDs
    
    Returns:
        Anzahl der tatsächlich gelöschten Einträge.
    """
    count = 0
    for oid in output_ids or []:
        if delete_output(oid):
            count += 1
    return count


# Tool-Definitionen für das Responses API, die in jonas.py verwendet werden
FUNCTION_TOOLS = [
    {
        "type": "web_search"
    },
    {
        "type": "function",
        "name": "run_shell_command",
        "description": "Executes a shell command on the local machine. For SMALL outputs (<300 tokens), returns the output directly. For LARGE outputs (≥300 tokens), stores it with an ID (e.g., 'out1') and you must use get_output_head(), get_output_tail(), search_output(), or get_output_lines() to retrieve parts of it.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "intention": {"type": "string", "description": "A brief description of what the command does"},
                "readonly": {"type": "boolean", "description": "Set to true if this command only reads data and does not modify the system (e.g., ls, ps, cat). Set to false if it modifies the system (e.g., touch, rm, mkdir, chmod)."},
            },
            "required": ["command", "intention", "readonly"],
        },
    },
    {
        "type": "function",
        "name": "get_output_head",
        "description": "Retrieves the first N lines from a stored command output. Useful for previewing large outputs.",
        "parameters": {
            "type": "object",
            "properties": {
                "output_id": {"type": "string", "description": "The output identifier (e.g., 'out1', 'out2')"},
                "num_lines": {"type": "integer", "description": "Number of lines to retrieve (default: 10, max: 100)"},
            },
            "required": ["output_id"],
        },
    },
    {
        "type": "function",
        "name": "get_output_tail",
        "description": "Retrieves the last N lines from a stored command output. Useful for checking the end of large outputs.",
        "parameters": {
            "type": "object",
            "properties": {
                "output_id": {"type": "string", "description": "The output identifier (e.g., 'out1', 'out2')"},
                "num_lines": {"type": "integer", "description": "Number of lines to retrieve (default: 10, max: 100)"},
            },
            "required": ["output_id"],
        },
    },
    {
        "type": "function",
        "name": "search_output",
        "description": "Searches for a term (case-insensitive) in a stored command output. Returns matches with 5 lines of context before and after. Merges nearby matches. Returns error if too many results found (user should refine search).",
        "parameters": {
            "type": "object",
            "properties": {
                "output_id": {"type": "string", "description": "The output identifier (e.g., 'out1', 'out2')"},
                "search_term": {"type": "string", "description": "The term to search for (case-insensitive)"},
                "max_results": {"type": "integer", "description": "Maximum number of result blocks (default: 10)"},
            },
            "required": ["output_id", "search_term"],
        },
    },
    {
        "type": "function",
        "name": "display_output",
        "description": "Displays the complete stored output directly to the user WITHOUT sending it to the LLM. Use this when the user wants to see the full output but you don't need to analyze it. The output will be shown with visual separators.",
        "parameters": {
            "type": "object",
            "properties": {
                "output_id": {"type": "string", "description": "The output identifier (e.g., 'out1', 'out2')"},
            },
            "required": ["output_id"],
        },
    }
   
]