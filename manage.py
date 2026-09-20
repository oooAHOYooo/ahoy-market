#!/usr/bin/env python3
"""Ahoy content manager — CRUD for static/data/*.json

Usage:
  manage.py <collection> list
  manage.py <collection> add
  manage.py <collection> toggle <id>
  manage.py <collection> edit <id> <field> <value>
  manage.py <collection> remove <id>
  manage.py news list [year]
  manage.py news add
  manage.py news remove <year> <month> <section> <index>

Collections: podcasts, events, videos, ambient, news
"""
import json, sys
from pathlib import Path
from datetime import date

DATA = Path(__file__).parent / "static/data"

COLLECTIONS = {
    "podcasts": {
        "file": DATA / "podcastCollection.json",
        "key": "podcasts",
        "id": "id",
        "toggle": ("active", True, False),
    },
    "events": {
        "file": DATA / "events.json",
        "key": "events",
        "id": "id",
        "toggle": ("status", "upcoming", "past"),
    },
    "videos": {
        "file": DATA / "videos.json",
        "key": "videos",
        "id": "id",
        "toggle": ("status", "available", "hidden"),
    },
    "ambient": {
        "file": DATA / "ambient-modes.json",
        "key": None,
        "id": "id",
        "toggle": None,
    },
}


def load(cfg):
    data = json.loads(cfg["file"].read_text())
    items = data[cfg["key"]] if cfg["key"] else data
    return data, items


def save(cfg, data):
    cfg["file"].write_text(json.dumps(data, indent=2) + "\n")


def find(items, id_field, id_val):
    for item in items:
        if str(item.get(id_field)) == str(id_val):
            return item
    return None


def cmd_list(cfg, args):
    _, items = load(cfg)
    for item in items:
        id_val = item.get(cfg["id"])
        title = item.get("title") or item.get("name") or ""
        toggle = ""
        if cfg["toggle"]:
            field = cfg["toggle"][0]
            toggle = f"  [{field}={item.get(field)}]"
        print(f"  {id_val}: {title}{toggle}")
    print(f"  ({len(items)} items)")


def cmd_toggle(cfg, args):
    if not cfg["toggle"]:
        print("Toggle not supported for this collection"); return
    if not args:
        print("Usage: toggle <id>"); return
    data, items = load(cfg)
    item = find(items, cfg["id"], args[0])
    if not item:
        print(f"Not found: {args[0]}"); return
    field, on, off = cfg["toggle"]
    item[field] = off if item[field] == on else on
    save(cfg, data)
    print(f"  {args[0]}: {field} = {item[field]}")


def cmd_edit(cfg, args):
    if len(args) < 3:
        print("Usage: edit <id> <field> <value>"); return
    id_val, field, value = args[0], args[1], " ".join(args[2:])
    data, items = load(cfg)
    item = find(items, cfg["id"], id_val)
    if not item:
        print(f"Not found: {id_val}"); return
    if field not in item:
        print(f"Unknown field: {field!r}. Valid: {', '.join(item.keys())}")
        return
    old = item[field]
    if isinstance(old, bool):
        value = value.lower() in ("true", "1", "yes")
    elif isinstance(old, int):
        try:
            value = int(value)
        except ValueError:
            print(f"  Field {field!r} must be an integer.")
            return
    item[field] = value
    save(cfg, data)
    print(f"  {id_val}: {field} = {value}")


def cmd_remove(cfg, args):
    if not args:
        print("Usage: remove <id>"); return
    data, items = load(cfg)
    keep = [i for i in items if str(i.get(cfg["id"])) != str(args[0])]
    if len(keep) == len(items):
        print(f"Not found: {args[0]}"); return
    if cfg["key"]:
        data[cfg["key"]] = keep
    else:
        data = keep
    save(cfg, data)
    print(f"  Removed {args[0]}")


def cmd_add(cfg, args):
    data, items = load(cfg)
    if not items:
        print("No existing items to use as template"); return
    template = items[0]
    new_item = {}
    print("Enter values (blank = keep default):")
    for field, val in template.items():
        if field == cfg["id"]:
            existing_ids = [i.get(cfg["id"]) for i in items if i.get(cfg["id"]) is not None]
            if existing_ids and all(isinstance(i, int) for i in existing_ids):
                suggested = max(existing_ids) + 1
                inp = input(f"  {field} [{suggested}]: ").strip()
                new_item[field] = int(inp) if inp else suggested
            else:
                example = existing_ids[0] if existing_ids else "id"
                inp = input(f"  {field} [e.g. {example!r}]: ").strip()
                new_item[field] = inp if inp else str(example)
        elif isinstance(val, (list, dict)):
            new_item[field] = type(val)()
        elif isinstance(val, bool):
            inp = input(f"  {field} [true/false, default={val}]: ").strip().lower()
            new_item[field] = (inp in ("true", "1", "yes")) if inp else val
        else:
            inp = input(f"  {field} [default={val!r}]: ").strip()
            new_item[field] = inp if inp else val
    items.append(new_item)
    if cfg["key"]:
        data[cfg["key"]] = items
    else:
        data = items
    save(cfg, data)
    print(f"  Added {new_item.get(cfg['id'])}")


# --- whats_new special handling ---

NEWS_FILE = DATA / "whats_new.json"


def news_load():
    return json.loads(NEWS_FILE.read_text())


def news_save(data):
    NEWS_FILE.write_text(json.dumps(data, indent=2) + "\n")


def cmd_news(subcmd, args):
    data = news_load()
    updates = data.get("updates", {})

    if subcmd == "list":
        years = sorted(updates.keys()) if updates else []
        if not years:
            print("  No updates yet.")
            return
        if len(years) > 1 and not args:
            print(f"  Available years: {', '.join(years)}  (listing {years[-1]})")
        year = args[0] if args else years[-1]
        for month, sections in updates.get(year, {}).items():
            for section, content in sections.items():
                items = content.get("items", []) if isinstance(content, dict) else []
                for i, item in enumerate(items):
                    print(f"  {year}/{month}/{section}[{i}]: {item.get('title', '')}")

    elif subcmd == "add":
        year  = input("  Year  [2026]: ").strip() or "2026"
        month = input("  Month [jan]:  ").strip() or "jan"
        section = input("  Section (music/videos/artists/platform/events/merch): ").strip()
        title = input("  Title: ").strip()
        desc  = input("  Description: ").strip()
        itype = input("  Type [content/feature/technical, default=content]: ").strip() or "content"
        link  = input("  Link [/]: ").strip() or "/"
        new_item = {"type": itype, "title": title, "description": desc,
                    "date": str(date.today()), "link": link}
        (updates
            .setdefault(year, {})
            .setdefault(month, {})
            .setdefault(section, {"title": section.title() + " Updates", "items": []})
            ["items"].append(new_item))
        data["updates"] = updates
        news_save(data)
        print(f"  Added to {year}/{month}/{section}")

    elif subcmd == "remove":
        if len(args) < 4:
            print("Usage: news remove <year> <month> <section> <index>"); return
        year, month, section, idx = args[0], args[1], args[2], int(args[3])
        if year not in updates:
            print(f"Year {year!r} not found. Available: {', '.join(sorted(updates.keys()))}")
            return
        months = updates[year]
        if month not in months:
            print(f"Month {month!r} not found in {year}. Available: {', '.join(sorted(months.keys()))}")
            return
        sections = months[month]
        if section not in sections:
            print(f"Section {section!r} not found in {year}/{month}. Available: {', '.join(sorted(sections.keys()))}")
            return
        content = sections[section]
        items = content.get("items", []) if isinstance(content, dict) else []
        if idx >= len(items):
            print(f"Index {idx} out of range (section has {len(items)} items)"); return
        removed = items.pop(idx)
        data["updates"] = updates
        news_save(data)
        print(f"  Removed: {removed.get('title')}")

    else:
        print("Usage: news list [year] | news add | news remove <year> <month> <section> <index>")


def usage():
    print(__doc__)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        usage(); sys.exit(1)

    collection, subcmd = argv[0], (argv[1] if len(argv) > 1 else "list")
    rest = argv[2:]

    if collection == "news":
        cmd_news(subcmd, rest)
    elif collection in COLLECTIONS:
        cfg = COLLECTIONS[collection]
        dispatch = {"list": cmd_list, "add": cmd_add, "toggle": cmd_toggle,
                    "edit": cmd_edit, "remove": cmd_remove}
        fn = dispatch.get(subcmd)
        if fn is None:
            print(f"Unknown subcommand: {subcmd!r}")
            usage()
        else:
            fn(cfg, rest)
    else:
        print(f"Unknown collection: {collection}")
        usage()
