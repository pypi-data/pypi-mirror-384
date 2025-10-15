# JONAS - Just Operate Nicely And Securely

[![PyPI version](https://badge.fury.io/py/jonas.svg)](https://pypi.org/project/jonas/)
[![Python versions](https://img.shields.io/pypi/pyversions/jonas.svg)](https://pypi.org/project/jonas/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Downloads](https://pepy.tech/badge/jonas)](https://pepy.tech/project/jonas)

> **Beschreibe einfach, was du erreichen willst – JONAS setzt es mit Shell-Befehlen um.**

JONAS ist dein intelligenter Shell-Assistent, der das umfangreiche UNIX-Know-how von Large Language Models nutzt, um komplexe Systemaufgaben durch natürliche Sprache zu steuern. Kein mühsames Nachschlagen von Befehlen mehr – sage JONAS einfach, was du brauchst.

## Warum JONAS?

### 🎯 Einfach in der Anwendung
Statt komplizierte Shell-Befehle zu recherchieren, beschreibst du einfach dein Ziel:
- *"Zeige mir alle Python-Prozesse"*
- *"Erstelle ein Backup meines Home-Verzeichnisses"*
- *"Installiere Docker und starte einen nginx-Container"*

JONAS versteht deine Absicht und führt die richtigen Befehle aus.

### 🔒 Sicherheit an erster Stelle
- **Explizite Freigabe**: Jeder Befehl wird vor der Ausführung angezeigt und erklärt
- **Intention transparent**: Du siehst, was der Befehl bewirken soll

### 🚀 Sofort einsatzbereit
```bash
pip install jonas
jonas
```
Das war's! JONAS ist systemweit verfügbar und einsatzbereit.

Beim ersten Start wirst du nach deinem **OpenAI API-Key** gefragt. Diesen kannst du auf [www.openai.com](https://www.openai.com) erstellen. Der Key wird lokal und sicher auf deinem System gespeichert.

### 💡 Intelligente Systemverwaltung
Nutze das gesamte UNIX-Wissen des LLM für:
- **Systemüberwachung**: Prozesse, Logs, Ressourcen im Blick
- **Updates & Installationen**: Software-Management ohne Handbuch
- **Konfiguration**: Erstelle und bearbeite Config-Dateien
- **Automatisierung**: Komplexe Workflows in natürlicher Sprache

### 💰 Sparsamer Token-Verbrauch
- Große Command-Outputs werden intelligent gespeichert
- Nur relevante Informationen werden an das LLM gesendet
- Session-Historie für Kontext ohne Token-Verschwendung
- **`new` Befehl**: Starte neue Unterhaltung und spare Token

## Features

- 🤖 **Intelligenter Chat**: Natürliche Gespräche mit automatischer Kontext-Verwaltung
- 🔧 **Tool-Calling**: Sichere Ausführung von Shell-Befehlen mit Bestätigung
- 📝 **Markdown-Rendering**: Schöne Formatierung von Antworten
- 🔄 **Mehrere Tool-Calls**: Parallele Ausführung mehrerer Befehle
- ⚡ **Thinking-Anzeige**: Visuelles Feedback während API-Aufrufen
- 🔒 **Sicherheitsabfragen**: Farbcodierte Bestätigung (Rot=schreibend, Magenta=lesend)
- 🎨 **Rich Terminal UI**: Farbige, formatierte Ausgaben mit Box-Design
- 📊 **Output-Management**: Große Outputs werden gespeichert und können durchsucht werden
- 🔍 **Output-Tools**: `get_output_head()`, `get_output_tail()`, `search_output()`, `display_output()`
- 📜 **Session-Historie**: Automatische Speicherung der letzten 15 Turns
- 🌐 **Web-Search**: Integrierte Web-Suche für aktuelle Informationen
- 🎯 **Auto-Korrektur**: Erkennt und korrigiert fehlende Tool-Calls

## Installation

### Via pip (empfohlen)

JONAS ist auf [PyPI](https://pypi.org/project/jonas/) verfügbar:

```bash
pip install jonas
```

Nach der Installation ist der Befehl `jonas` systemweit verfügbar:

```bash
jonas
```

### Aus dem Quellcode

1. **Repository klonen:**
   ```bash
   git clone https://github.com/peter-filz/jonas.git
   cd jonas
   ```

2. **Installieren:**
   ```bash
   pip install -e .
   ```

## Schnellstart

1. **Installieren:**
   ```bash
   pip install jonas
   ```

2. **Starten:**
   ```bash
   jonas
   ```

3. **Konfigurieren:**
   Beim ersten Start wirst du interaktiv nach folgenden Werten gefragt:
   - **OPENAI_API_KEY**: Dein OpenAI API-Schlüssel
   - **OPENAI_MODEL**: Das zu verwendende Modell (z.B. `gpt-4o-mini`, `gpt-4o`, `o1-mini`)
   - **TOKENLIMIT**: Token-Schwellenwert für Output-Speicherung (Standard: 2000)

4. **Verwenden:**
   Gib einfach Anweisungen in natürlicher Sprache ein!

## Konfiguration

Die Konfiguration wird in `jonas.cfg` gespeichert.

Zum Ändern der Konfiguration verwende im Chat:
```
config
```

## Verwendung

Starte JONAS einfach mit:
```bash
jonas
```

### Verfügbare Befehle:
- `exit`, `quit`, `bye` - Chat beenden
- `new` - Starte neue Unterhaltung (spart Token, löscht Historie und Outputs)
- `config` - Konfiguration ändern (API-Key, Model, TokenLimit)
- `delconfig` - Konfiguration löschen und beenden
- `history` - Gespeicherte Session-Historie anzeigen
- `help` - Startbildschirm erneut anzeigen

### Kommandozeilen-Parameter:
- `jonas` - Startet den interaktiven Chat
- `jonas --version` (oder `-v`) - Zeigt die Version an
- `jonas --help` (oder `-h`) - Zeigt die Hilfe an

### Natürliche Sprache:
- Gebe einfach Anweisungen in natürlicher Sprache ein

### Beispiel-Interaktion:

```
Du: Zeige mir den Inhalt von /Users
Intention: Verzeichnisinhalt anzeigen
Befehl:    ls /Users
Ausführen? [j/N] j

Jonas: Das Verzeichnis /Users enthält: Applications, Library, Users, ...

Du: Welche Python-Version verwendest du?
Intention: Python-Version prüfen
Befehl:    python3 --version
Ausführen? [j/N] j

Jonas: Ich verwende Python 3.12.0

Du: history
─────────────────────────────────────────────────────────
Session-Historie:
─────────────────────────────────────────────────────────

Du: Zeige mir den Inhalt von /Users
Jonas: Das Verzeichnis /Users enthält...
Ausgeführte Befehle:
  • ls /Users → out1

Du: exit
Auf Wiedersehen!
```

## Features im Detail

### Tool-Calling mit Sicherheit
- **Readonly-Flag**: Befehle werden als lesend (Magenta) oder schreibend (Rot) markiert
- **Intention-Anzeige**: Zeigt, was der Befehl tun soll
- **Bestätigungs-Prompts**: Jeder Befehl erfordert explizite Bestätigung
- **Auto-Korrektur**: Erkennt, wenn das Modell Aktionen behauptet ohne Tool-Call
- **Timeout**: 5 Minuten für längere Befehle (apt-get upgrade, docker build, etc.)

### Output-Management
- **Automatische Speicherung**: Outputs >300 Tokens werden als `out1`, `out2`, etc. gespeichert
- **get_output_head(output_id, num_lines)**: Zeigt die ersten N Zeilen
- **get_output_tail(output_id, num_lines)**: Zeigt die letzten N Zeilen
- **search_output(output_id, pattern)**: Durchsucht Output mit Regex
- **display_output(output_id)**: Zeigt kompletten Output an
- **Automatische Bereinigung**: Alte Outputs werden beim History-Trimming gelöscht

### Session-Historie
- **Automatisches Trimming**: Maximal 15 User/Assistant-Paare werden gespeichert
- **Persistente Output-IDs**: Zugriff auf frühere Befehlsausgaben
- **JSON-Struktur**: `{"answer": "...", "executed_commands": [...]}`
- **History-Befehl**: Zeigt alle gespeicherten Turns mit ausgeführten Befehlen

### Markdown-Rendering
- Tabellen werden korrekt formatiert
- Code-Blöcke mit Syntax-Highlighting
- Listen, Links und andere Markdown-Elemente
- Rich Terminal-Ausgaben mit Farben


## Projekt-Struktur

```
jonas/
├── jonas.py             # Haupt-Chat-Anwendung mit Dialog-Logik
├── shell_tools.py       # Tool-Definitionen und Shell-Ausführung
├── requirements.txt     # Python-Abhängigkeiten
├── jonas.cfg           # Konfigurationsdatei (wird beim ersten Start erstellt)
├── venv/               # Virtuelle Umgebung
└── README.md          # Diese Datei
```

## Abhängigkeiten

- `openai`: OpenAI API-Client (Responses API)
- `pydantic>=2.7.0`: Datenvalidierung
- `rich>=13.7.0`: Schöne Terminal-Ausgaben mit Markdown-Support
- `tiktoken>=0.5.0`: Token-Zählung für Output-Management
- `typer[all]>=0.12`: CLI-Framework

## Sicherheitshinweise

- ⚠️ **API-Keys** niemals committen!
- ⚠️ **Jeder Shell-Befehl** erfordert explizite Bestätigung
- ⚠️ **Timeout** (5 Minuten) verhindert hängende Prozesse
- ⚠️ **Readonly-Flag** signalisiert Risiko (Rot vs. Magenta)
- ⚠️ **Auto-Korrektur** verhindert Halluzinationen von Befehlsausführungen
- ⚠️ **Output-Bereinigung** beim History-Trimming

## Links

- **PyPI**: https://pypi.org/project/jonas/
- **GitHub**: https://github.com/peter-filz/jonas
- **Issues**: https://github.com/peter-filz/jonas/issues

## Autor

**Peter Filz**  
📧 peter.filz@googlemail.com

## Lizenz

GNU General Public License v3.0 oder später - siehe LICENSE-Datei für Details.

JONAS ist freie Software: Sie können sie unter den Bedingungen der GNU General Public License,
wie von der Free Software Foundation veröffentlicht, weitergeben und/oder modifizieren,
entweder gemäß Version 3 der Lizenz oder (nach Ihrer Option) jeder späteren Version.

Dieses Programm wird in der Hoffnung verteilt, dass es nützlich sein wird, aber
OHNE JEDE GEWÄHRLEISTUNG. Siehe die GNU General Public License für weitere Details.
