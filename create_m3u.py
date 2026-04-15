#!/usr/bin/env python3
"""
create_m3u.py — Generate .m3u playlist files for multi-disc .chd games
              and hide individual disc entries in EmulationStation's gamelist.xml.

Scans the current directory for .chd files containing "disc" in their name,
groups them by game title, creates one .m3u file per multi-disc game, and
marks every individual disc .chd as <hidden>true</hidden> in gamelist.xml so
only the .m3u entry appears in EmulationStation.
"""

import os
import re
from collections import defaultdict
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_title(filename: str) -> str:
    """
    Strip the disc identifier from a filename to get the base game title.
    Handles patterns like:
      - "Game Name (Disc 1).chd"
      - "Game Name (Disc1).chd"
      - "Game Name - Disc 2.chd"
      - "Game Name disc1.chd"
    """
    stem = os.path.splitext(filename)[0]
    title = re.sub(r'[\s\-_]*[\(\[]?\bdisc\s*\d+\b[\)\]]?', '', stem, flags=re.IGNORECASE)
    return title.strip(' -_')


def natural_sort_key(filename: str):
    """Sort filenames naturally so Disc 10 comes after Disc 9."""
    return [
        int(c) if c.isdigit() else c.lower()
        for c in re.split(r'(\d+)', filename)
    ]


# ---------------------------------------------------------------------------
# Disc discovery & .m3u writing
# ---------------------------------------------------------------------------

def find_disc_groups(directory: str = '.') -> dict[str, list[str]]:
    """
    Scan *directory* for .chd files whose name contains 'disc' (case-insensitive).
    Returns a dict mapping normalised game title → sorted list of filenames.
    """
    groups: dict[str, list[str]] = defaultdict(list)

    for entry in os.scandir(directory):
        if not entry.is_file():
            continue
        name = entry.name
        if not name.lower().endswith('.chd'):
            continue
        if 'disc' not in name.lower():
            continue
        title = normalize_title(name)
        groups[title].append(name)

    return {title: sorted(files, key=natural_sort_key)
            for title, files in groups.items()}


def write_m3u(title: str, files: list[str], directory: str = '.') -> str:
    """Write a .m3u file for *title* listing *files*. Returns the output path."""
    m3u_name = f"{title}.m3u"
    m3u_path = os.path.join(directory, m3u_name)
    with open(m3u_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(files) + '\n')
    return m3u_path


# ---------------------------------------------------------------------------
# gamelist.xml patching
# ---------------------------------------------------------------------------

def _normalize_path(raw: str) -> str:
    """
    Return just the basename from an ES path like './Game (Disc 1).chd'
    or '/full/path/to/Game (Disc 1).chd'.
    """
    return os.path.basename(raw.lstrip('./'))


def patch_gamelist(directory: str, disc_files: set[str]) -> None:
    """
    Open *directory*/gamelist.xml and set <hidden>true</hidden> on every
    <game> entry whose <path> resolves to a filename in *disc_files*.

    - If a <hidden> tag already exists it is updated.
    - If it doesn't exist it is inserted right after <path>.
    - The file is written back only when at least one change was made.
    - If gamelist.xml doesn't exist the function prints a warning and returns.
    """
    gamelist_path = os.path.join(directory, 'gamelist.xml')

    if not os.path.isfile(gamelist_path):
        print("  ⚠  gamelist.xml not found — skipping XML patch.")
        return

    # Preserve the original declaration / encoding as much as possible.
    ET.register_namespace('', '')          # avoid ns0: prefixes
    tree = ET.parse(gamelist_path)
    root = tree.getroot()

    changed = 0

    for game in root.findall('game'):
        path_el = game.find('path')
        if path_el is None or not path_el.text:
            continue

        basename = _normalize_path(path_el.text)
        if basename not in disc_files:
            continue

        hidden_el = game.find('hidden')
        if hidden_el is None:
            # Insert <hidden> right after <path> for tidy XML.
            path_index = list(game).index(path_el)
            hidden_el = ET.Element('hidden')
            game.insert(path_index + 1, hidden_el)

        if hidden_el.text != 'true':
            hidden_el.text = 'true'
            changed += 1

    if changed:
        # Indent for readability (Python 3.9+); graceful fallback for older versions.
        try:
            ET.indent(tree, space='  ')
        except AttributeError:
            pass

        tree.write(gamelist_path, encoding='utf-8', xml_declaration=True)
        print(f"  ✔  gamelist.xml updated — {changed} disc entry/entries hidden.")
    else:
        print("  ✓  gamelist.xml required no changes (entries already hidden or not found).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    directory = '.'
    groups = find_disc_groups(directory)

    if not groups:
        print("No multi-disc .chd files found in the current directory.")
        return

    print(f"Found {len(groups)} multi-disc game(s):\n")

    # Collect every individual disc filename for the XML patch step.
    all_disc_files: set[str] = set()

    for title, files in sorted(groups.items()):
        m3u_path = write_m3u(title, files, directory)
        print(f"  [{title}]")
        for f in files:
            print(f"    • {f}")
            all_disc_files.add(f)
        print(f"  → Created: {os.path.basename(m3u_path)}\n")

    print(f"Done. {len(groups)} .m3u file(s) written.\n")

    # --- Patch gamelist.xml ---
    print("Patching gamelist.xml …")
    patch_gamelist(directory, all_disc_files)


if __name__ == '__main__':
    main()
