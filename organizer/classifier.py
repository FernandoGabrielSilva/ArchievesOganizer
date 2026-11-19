"""Classificação de arquivos por extensão."""
import os
from pathlib import Path
from .config import build_extension_map


def category_of(path: Path, ext_map: dict) -> str:
    ext = path.suffix.lower()
    if ext in ext_map:
        return ext_map[ext]
    # arquivos sem extensão conhecida
    return "Outros"


def is_ignored_dir(name: str, ignore_list: list) -> bool:
    if name.startswith(".") and name not in (".", ".."):
        # hidden dirs ignored unless explicitly allowed handled elsewhere
        pass
    return name in ignore_list


def plan_moves(cfg: dict) -> list:
    """Retorna lista de dicts: {src, dst, category}."""
    from .config import build_extension_map
    ext_map = build_extension_map(cfg)
    base = Path(cfg["destination_base"]).expanduser()
    recursive = cfg.get("recursive", False)
    include_hidden = cfg.get("include_hidden", False)
    ignore_dirs = set(cfg.get("ignore_dirs", []))
    skip_unknown = cfg.get("skip_unknown", False)
    cat_dest = cfg.get("category_destinations", {})
    moves = []
    seen_src = set()

    for src_dir in cfg.get("source_dirs", []):
        root = Path(src_dir).expanduser()
        if not root.exists() or not root.is_dir():
            continue
        # walk
        if recursive:
            walker = os.walk(root)
        else:
            # only top-level files
            walker = [(str(root), [], [p.name for p in root.iterdir() if p.is_file()])]
        for dirpath, dirnames, filenames in walker:
            # filter dirs
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            if not include_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                filenames = [f for f in filenames if not f.startswith(".")] if not include_hidden else filenames
            # skip if this dir itself should be ignored (already filtered)
            for fname in filenames:
                src = Path(dirpath) / fname
                if not src.is_file():
                    continue
                if str(src) in seen_src:
                    continue
                seen_src.add(str(src))
                cat = category_of(src, ext_map)
                if cat == "Outros" and skip_unknown:
                    continue
                # avoid moving files already in their destination category folder? 
                # compute relative subdir if recursive preserve
                rel_parent = src.parent.relative_to(root) if src.parent != root else Path(".")
                dest_sub = cat_dest.get(cat, cat)
                dst_dir = base / dest_sub
                if recursive and rel_parent != Path("."):
                    # preserve subfolder structure under category
                    dst_dir = dst_dir / rel_parent
                dst = dst_dir / src.name
                # avoid moving a file onto itself
                if src.resolve() == dst.resolve():
                    continue
                # avoid moving files that are inside a source that is also a destination? still ok
                moves.append({"src": str(src), "dst": str(dst), "category": cat})
    return moves


def resolve_conflict(dst: Path, policy: str) -> Path:
    """Given a destination path that may exist, apply conflict policy."""
    if not dst.exists():
        return dst
    if policy == "overwrite":
        return dst
    if policy == "skip":
        return None
    # rename
    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent
    i = 1
    while True:
        cand = parent / f"{stem} ({i}){suffix}"
        if not cand.exists():
            return cand
        i += 1
