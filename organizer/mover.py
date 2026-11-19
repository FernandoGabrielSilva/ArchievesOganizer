"""Execução dos movimentos e histórico para desfazer."""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from .config import HISTORY_DIR, ensure_dirs


def execute_moves(moves: list, cfg: dict) -> dict:
    """Executa a lista de movimentos. Retorna dict com resultados e id do histórico."""
    ensure_dirs()
    policy = cfg.get("conflict_policy", "rename")
    results = []
    errors = []
    done = []
    for m in moves:
        src = Path(m["src"])
        dst = Path(m["dst"])
        if not src.exists():
            errors.append({"src": str(src), "error": "arquivo não existe mais"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        # resolve conflict
        from .classifier import resolve_conflict
        final_dst = resolve_conflict(dst, policy)
        if final_dst is None:
            results.append({"src": str(src), "dst": str(dst), "status": "skipped (conflict)"})
            continue
        try:
            shutil.move(str(src), str(final_dst))
            record = {"src": str(src), "dst": str(final_dst), "category": m["category"]}
            done.append(record)
            results.append({"src": str(src), "dst": str(final_dst), "status": "ok"})
        except Exception as e:
            errors.append({"src": str(src), "error": str(e)})
    # save history
    hist_id = None
    if done:
        ensure_dirs()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        hist_id = ts
        hist_file = HISTORY_DIR / f"{ts}.json"
        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump({"id": ts, "created": datetime.now().isoformat(),
                       "moves": done, "config_snapshot": {
                           "source_dirs": cfg.get("source_dirs"),
                           "destination_base": cfg.get("destination_base"),
                       }}, f, indent=2, ensure_ascii=False)
    return {"moved": len(done), "skipped": len(results) - len(done),
            "errors": errors, "results": results, "history_id": hist_id}


def list_history() -> list:
    ensure_dirs()
    out = []
    for p in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            out.append({"id": data.get("id", p.stem), "file": str(p),
                        "created": data.get("created"), "count": len(data.get("moves", []))})
        except Exception:
            continue
    return out


def undo_history(hist_id: str) -> dict:
    ensure_dirs()
    p = HISTORY_DIR / f"{hist_id}.json"
    if not p.exists():
        return {"error": "histórico não encontrado"}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    moves = data.get("moves", [])
    restored = 0
    errors = []
    # undo in reverse order
    for m in reversed(moves):
        src = Path(m["dst"])
        dst = Path(m["src"])
        if not src.exists():
            errors.append({"src": str(src), "error": "arquivo movido não encontrado"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            # if original src exists now, rename
            final = dst
            if final.exists():
                i = 1
                while final.exists():
                    final = dst.parent / f"{dst.stem} ({i}){dst.suffix}"
                    i += 1
            shutil.move(str(src), str(final))
            restored += 1
        except Exception as e:
            errors.append({"src": str(src), "error": str(e)})
    # mark undone by renaming file
    try:
        p.rename(p.with_suffix(".json.undone"))
    except Exception:
        pass
    return {"restored": restored, "errors": errors}
