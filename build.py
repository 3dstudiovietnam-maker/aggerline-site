#!/usr/bin/env python3
"""
Fire Fence site builder.

One template (src/template.html) + one JSON per language (src/i18n/<code>.json)
-> one static HTML file per language in the repo root.

Edit the template or the JSONs, never the generated .html files.
Run:  python3 build.py
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATE = ROOT / "src" / "template.html"
I18N = ROOT / "src" / "i18n"
BASE = "https://firefence.homes/"

# Display order in the language menu. Also the build order.
# This is the same set of 11 languages the HealthGuard apps ship with
# (client/src/lib/translations.ts), in the same order.
ORDER = ["en", "hu", "hi", "zh", "vi", "de", "es", "pt", "ru", "th", "ro"]

# Finished translations that are not in the 11 today. Add a code to ORDER
# above and it is built and appears in the menu — nothing else to change.
PARKED = ["fr", "it", "el", "tr", "hr"]

# Keys that are build-time metadata, not page text.
META = {"_lang", "_native", "_file"}


def load():
    langs = {}
    for code in ORDER:
        path = I18N / f"{code}.json"
        if not path.exists():
            sys.exit(f"missing translation file: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("_lang") != code:
            sys.exit(f"{path.name}: _lang is {data.get('_lang')!r}, expected {code!r}")
        langs[code] = data
    return langs


def check_keys(langs):
    reference = set(langs["en"]) - META
    problems = []
    for code, data in langs.items():
        keys = set(data) - META
        for missing in sorted(reference - keys):
            problems.append(f"{code}.json: missing key {missing!r}")
        for extra in sorted(keys - reference):
            problems.append(f"{code}.json: unknown key {extra!r}")
        for key in sorted(reference & keys):
            if not str(data[key]).strip():
                problems.append(f"{code}.json: empty value for {key!r}")
    return problems


def hreflang_block(langs):
    lines = []
    for code in ORDER:
        href = BASE + ("" if langs[code]["_file"] == "index.html" else langs[code]["_file"])
        lines.append(f'<link rel="alternate" hreflang="{code}" href="{href}">')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}">')
    return "\n".join(lines)


def lang_menu(langs, current):
    """Header dropdown. Pure HTML <details>, no JavaScript."""
    items = []
    for code in ORDER:
        data = langs[code]
        if code == current:
            items.append(
                f'        <span class="langpick-item is-current" aria-current="true">'
                f'{data["_native"]}</span>'
            )
        else:
            items.append(
                f'        <a class="langpick-item" hreflang="{code}" lang="{code}" '
                f'href="{data["_file"]}">{data["_native"]}</a>'
            )
    body = "\n".join(items)
    return (
        '      <details class="langpick">\n'
        f'        <summary aria-label="{langs[current]["nav_lang"]}">'
        f'{langs[current]["_native"]}</summary>\n'
        '        <div class="langpick-menu">\n'
        f"{body}\n"
        "        </div>\n"
        "      </details>"
    )


def lang_footer(langs, current):
    items = []
    for code in ORDER:
        data = langs[code]
        if code == current:
            items.append(f'    <span class="is-current">{data["_native"]}</span>')
        else:
            items.append(
                f'    <a hreflang="{code}" lang="{code}" href="{data["_file"]}">'
                f'{data["_native"]}</a>'
            )
    return "\n".join(items)


def main():
    langs = load()
    problems = check_keys(langs)
    if problems:
        print("\n".join(problems))
        sys.exit(f"\n{len(problems)} problem(s) — nothing was written.")

    template = TEMPLATE.read_text(encoding="utf-8")
    hreflang = hreflang_block(langs)
    written = []

    for code in ORDER:
        data = langs[code]
        page = template
        page = page.replace("{{lang}}", code)
        page = page.replace("{{hreflang}}", hreflang)
        page = page.replace("{{lang_menu}}", lang_menu(langs, code))
        page = page.replace("{{lang_footer}}", lang_footer(langs, code))
        for key, value in data.items():
            if key in META:
                continue
            page = page.replace("{{" + key + "}}", str(value))

        leftover = sorted(set(re.findall(r"\{\{[a-z0-9_]+\}\}", page)))
        if leftover:
            sys.exit(f"{code}: unresolved placeholders {leftover}")

        out = ROOT / data["_file"]
        out.write_text(page, encoding="utf-8")
        written.append(f"  {data['_file']:<12} {data['_native']:<12} {len(page):>6} bytes")

    print(f"built {len(written)} pages:")
    print("\n".join(written))


if __name__ == "__main__":
    main()
