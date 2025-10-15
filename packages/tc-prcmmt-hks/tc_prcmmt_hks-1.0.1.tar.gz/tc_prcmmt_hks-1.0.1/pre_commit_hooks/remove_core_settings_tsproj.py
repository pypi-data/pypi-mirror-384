#!/usr/bin/env python3
"""
remove_settings_tsproj.py

- Durchsucht das aktuelle Verzeichnis (inkl. Unterordner) nach *.tsproj‑Dateien
- Entfernt jedes <Settings>-Element (inkl. aller Unterelemente)
- Schreibt die bereinigte Datei wieder zurück (ueberschreibt das Original)
"""

import sys
import pathlib
import xml.etree.ElementTree as ET
from typing import List


# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------
def _find_tsproj_files(base_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    Liefert eine sortierte Liste aller *.tsproj‑Dateien im angegebenen Verzeichnis.
    Die Suche ist rekursiv, sodass Unterordner ebenfalls beruecksichtigt werden.
    """
    if not base_dir.is_dir():
        sys.exit(f"Der Pfad '{base_dir}' ist kein gültiges Verzeichnis.")
    return sorted(base_dir.rglob("*.tsproj"))  # rglob = rekursives Glob


def _load_xml(path: pathlib.Path) -> ET.ElementTree:
    """Lädt die XML‑Datei und gibt das ElementTree‑Objekt zurueck."""
    try:
        return ET.parse(path)
    except ET.ParseError as exc:
        sys.exit("Fehler beim Parsen von '{path}': {exc}")
    except OSError as exc:
        sys.exit("Konnte Datei nicht oeffnen '{path}': {exc}")


def _remove_settings(tree: ET.ElementTree) -> bool:
    """Entfernt alle <Settings>-Elemente im Baum."""
    root = tree.getroot()
    removed = False

    for parent in root.iter():
        for child in list(parent):
            if child.tag == "Settings":
                parent.remove(child)
                removed = True
    return removed


def _indent(elem: ET.Element, level: int = 0) -> None:
    """
    Rekursive Einrückung (Fallback für Python < 3.9).
    Verhindert überflüssige Leerzeilen.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i


def _write_xml(tree: ET.ElementTree, out_path: pathlib.Path) -> None:
    """Schreibt das (geaenderte) XML mit sauberer Formatierung zurueck."""
    root = tree.getroot()
    if hasattr(ET, "indent"):               # Python ≥3.9
        ET.indent(tree, space="  ")
    else:
        _indent(root)

    tree.write(out_path, encoding="utf-8", xml_declaration=True)


# ----------------------------------------------------------------------
# Hauptlogik
# ----------------------------------------------------------------------
def main() -> int:
    # Basis‑Verzeichnis: das aktuelle Arbeitsverzeichnis, von dem aus das Skript gestartet wird
    base_dir = pathlib.Path.cwd()

    tsproj_files = _find_tsproj_files(base_dir)

    if not tsproj_files:
        sys.exit("Keine *.tsproj‑Dateien im Verzeichnis XYZ gefunden.")

#    print("*.tsproj‑Datei(en) im Verzeichnis XYZ gefunden.\n")

    for proj_path in tsproj_files:
        rel = proj_path.relative_to(base_dir)
        print("Verarbeite: {rel}")

        tree = _load_xml(proj_path)

        if _remove_settings(tree):
            _write_xml(tree, proj_path)   # überschreibt die Originaldatei
            print("   <Settings> entfernt und Datei gespeichert.\n")
            return 0 # Done
        else:
            print("   Kein <Settings>-Element gefunden - unveraendert.\n")
            return 1 # Error


if __name__ == "__main__":
    main()