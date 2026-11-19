"""Configuração persistente do Organizador de Arquivos."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "organizador-arquivos"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_DIR = Path.home() / ".local" / "share" / "organizador-arquivos" / "history"

DEFAULT_CATEGORIES = {
    "Imagens": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".tif",
                ".heic", ".heif", ".raw", ".ico", ".psd", ".ai", ".xcf"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".mpg",
               ".mpeg", ".3gp", ".ts", ".vob"],
    "Musicas": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff",
                ".mid", ".midi"],
    "Documentos": [".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".tex", ".epub",
                   ".mobi", ".pages"],
    "Planilhas": [".xls", ".xlsx", ".ods", ".csv", ".tsv"],
    "Apresentacoes": [".ppt", ".pptx", ".odp", ".key"],
    "Compactados": [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar", ".zst"],
    "Codigo": [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass",
               ".c", ".cpp", ".h", ".hpp", ".java", ".kt", ".go", ".rs", ".rb", ".php", ".sh",
               ".bash", ".zsh", ".json", ".yaml", ".yml", ".toml", ".xml", ".sql", ".lua",
               ".swift", ".dart", ".r", ".m", ".pl"],
    "Executaveis": [".exe", ".AppImage", ".deb", ".rpm", ".apk", ".msi", ".dmg", ".run",
                    ".bin", ".sh"],
    "Fontes": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Dados": [".db", ".sqlite", ".sqlite3", ".jsonl", ".parquet", ".feather"],
    "Outros": [],
}

DEFAULT_CONFIG = {
    "source_dirs": [str(Path.home() / "Downloads")],
    "destination_base": str(Path.home()),
    "recursive": False,
    "conflict_policy": "rename",  # rename | overwrite | skip
    "include_hidden": False,
    "ignore_dirs": [".git", "node_modules", "__pycache__", ".cache", ".local", ".config",
                    ".steam", ".wine", ".npm", ".cargo", ".rustup", ".gradle", ".venv",
                    "venv", "dist", "build", ".idea", ".vscode", "target"],
    "skip_unknown": False,
    "theme": "dark",
    "language": "pt_BR",
    "categories": DEFAULT_CATEGORIES,
    "category_destinations": {k: k for k in DEFAULT_CATEGORIES},
}


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # merge with defaults for missing keys
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            if "categories" not in data:
                merged["categories"] = DEFAULT_CATEGORIES
            if "category_destinations" not in data:
                merged["category_destinations"] = {k: k for k in merged["categories"]}
            # ensure all categories have destinations
            for c in merged["categories"]:
                merged["category_destinations"].setdefault(c, c)
            return merged
        except Exception:
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def build_extension_map(cfg: dict) -> dict:
    m = {}
    for cat, exts in cfg.get("categories", {}).items():
        for e in exts:
            m[e.lower()] = cat
    return m
