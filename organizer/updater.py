"""Verificação e instalação de atualizações via GitHub Releases."""
import json
import os
import platform
import shlex
import shutil
import ssl
import stat
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from .version import __version__, __repo__

GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"
USER_AGENT = "OrganizadorArquivos-Updater"

_DATA_HOME = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
STATE_DIR = Path(_DATA_HOME) / "OrganizadorArquivos"
BACKUP_DIR = STATE_DIR / "backups"
PENDING_FILE = STATE_DIR / "pending_update.json"
READY_FILE = STATE_DIR / "update_ready"
BACKUP_TTL_DAYS = 7


def current_version():
    return __version__


def _ca_bundle():
    """Localiza um pacote de CAs confiáveis, inclusive dentro do AppImage."""
    candidates = []
    try:
        import certifi
        candidates.append(certifi.where())
    except Exception:
        pass
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "certifi", "cacert.pem"))
        candidates.append(os.path.join(meipass, "cacert.pem"))
    candidates.extend([
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/cert.pem",
    ])
    seen = set()
    for path in candidates:
        if path and path not in seen and os.path.isfile(path):
            return path
        if path:
            seen.add(path)
    return None


def _ssl_context():
    """Contexto SSL explícito: o bundle onefile pode não herdar os CAs do sistema."""
    cafile = _ca_bundle()
    if cafile:
        os.environ["SSL_CERT_FILE"] = cafile
        return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


def _http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_latest_release():
    return _http_get_json(GITHUB_API.format(repo=__repo__))


def _parse_version(tag):
    tag = tag.lstrip("vV")
    parts = []
    for p in tag.split("."):
        num = ""
        for ch in p:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(latest_tag, current=None):
    if current is None:
        current = __version__
    return _parse_version(latest_tag) > _parse_version(current)


def find_asset(release, name_contains=None, arch=None):
    if arch is None:
        arch = platform.machine()
    # map
    arch_map = {"x86_64": ["x86_64", "amd64", "x64"], "aarch64": ["aarch64", "arm64"]}
    candidates = arch_map.get(arch, [arch])
    assets = release.get("assets", [])
    for a in assets:
        n = a.get("name", "")
        if name_contains and name_contains not in n:
            continue
        if any(c in n for c in candidates):
            return a
    # fallback: first matching name_contains
    if name_contains:
        for a in assets:
            if name_contains in a.get("name", ""):
                return a
    return None


def check_for_updates():
    """Retorna (has_update, latest_tag, asset, release_url, release)."""
    try:
        rel = get_latest_release()
    except Exception as e:
        return False, None, None, None, None, str(e)
    tag = rel.get("tag_name", "")
    if not tag:
        return False, None, None, None, rel, "no tag"
    if not is_newer(tag):
        return False, tag, None, rel.get("html_url"), rel, None
    # prefer AppImage on Linux
    asset = None
    if platform.system() == "Linux":
        asset = find_asset(rel, "AppImage")
        if asset is None:
            asset = find_asset(rel, ".tar")
        if asset is None:
            # any linux binary
            for a in rel.get("assets", []):
                if "linux" in a.get("name", "").lower() or a.get("name", "").endswith((".AppImage", ".tar.gz", ".deb", ".rpm")):
                    asset = a
                    break
    return True, tag, asset, rel.get("html_url"), rel, None


def is_appimage():
    return bool(os.environ.get("APPIMAGE")) or str(sys.argv[0]).endswith(".AppImage")


def current_appimage_path():
    p = os.environ.get("APPIMAGE")
    if p:
        return Path(p)
    # fallback
    return Path(sys.argv[0]).resolve()


def download_asset(asset, dest_dir=None, progress=None):
    if dest_dir is None:
        dest_dir = Path(tempfile.gettempdir())
    else:
        dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    url = asset["browser_download_url"]
    name = asset["name"]
    dest = dest_dir / name
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 65536
        with open(dest, "wb") as f:
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if progress:
                    progress(downloaded, total)
    return dest


def cleanup_backups(ttl_days=BACKUP_TTL_DAYS, keep=1):
    """Mantém no máximo `keep` backups e apaga os mais antigos que `ttl_days`."""
    try:
        files = sorted(
            (p for p in BACKUP_DIR.iterdir() if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return
    now = time.time()
    for path in files[keep:]:
        try:
            path.unlink()
        except OSError:
            pass
    for path in files[:keep]:
        if now - path.stat().st_mtime > ttl_days * 86400:
            try:
                path.unlink()
            except OSError:
                pass


def mark_update_started_ok():
    """Chamado pela GUI após abrir: confirma que a nova versão iniciou."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        READY_FILE.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass
    cleanup_backups()


def apply_appimage_update(new_file):
    """Instala com backup centralizado e rollback automático se falhar."""
    new_file = Path(new_file).resolve()
    target = current_appimage_path().resolve()
    if not target.exists():
        raise RuntimeError("AppImage atual não encontrado")

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    # Antes de cada atualização, remove backups mais antigos.
    cleanup_backups(keep=0)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"{target.stem}_v{current_version()}_{stamp}{target.suffix}"
    shutil.move(str(target), str(backup))
    shutil.move(str(new_file), str(target))
    os.chmod(target, target.stat().st_mode | stat.S_IEXEC)

    pending = {
        "target": str(target),
        "backup": str(backup),
        "new_file": str(new_file),
        "version": current_version(),
        "time": time.time(),
    }
    PENDING_FILE.write_text(json.dumps(pending), encoding="utf-8")

    q = shlex.quote
    script = Path(tempfile.gettempdir()) / "organizador_update.sh"
    script.write_text(
        "#!/bin/bash\n"
        f"target={q(str(target))}\n"
        f"backup={q(str(backup))}\n"
        f"new_file={q(str(new_file))}\n"
        f"ready={q(str(READY_FILE))}\n"
        f"pending={q(str(PENDING_FILE))}\n"
        'rm -f "$ready"\n'
        "sleep 2\n"
        '"$target" &\n'
        "pid=$!\n"
        'deadline=$(( $(date +%s) + 90 ))\n'
        "ok=0\n"
        'while [ "$(date +%s)" -lt "$deadline" ]; do\n'
        '  if [ -f "$ready" ]; then ok=1; break; fi\n'
        '  if ! kill -0 "$pid" 2>/dev/null; then\n'
        '    wait "$pid"; rc=$?\n'
        '    if [ "$rc" -eq 0 ]; then ok=1; fi\n'
        "    break\n"
        "  fi\n"
        "  sleep 0.5\n"
        "done\n"
        'if [ "$ok" -eq 1 ]; then\n'
        '  rm -f "$ready" "$pending"\n'
        "else\n"
        '  kill "$pid" 2>/dev/null || true\n'
        '  wait "$pid" 2>/dev/null || true\n'
        '  mv -f "$backup" "$target"\n'
        '  chmod +x "$target"\n'
        '  rm -f "$new_file" "$pending" "$ready"\n'
        '  "$target" &\n'
        "fi\n"
        f'rm -f {q(str(script))}\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    import subprocess
    subprocess.Popen(
        ["/bin/bash", str(script)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True
