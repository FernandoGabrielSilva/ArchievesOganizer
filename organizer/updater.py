"""Verificação e instalação de atualizações via GitHub Releases."""
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import urllib.request
from pathlib import Path

from .version import __version__, __repo__

GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"
USER_AGENT = "OrganizadorArquivos-Updater"


def current_version():
    return __version__


def _http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
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
    with urllib.request.urlopen(req, timeout=60) as resp:
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


def apply_appimage_update(new_file):
    """Substitui o AppImage atual e reinicia. Usa script auxiliar."""
    new_file = Path(new_file)
    target = current_appimage_path()
    if not target.exists():
        raise RuntimeError("AppImage atual não encontrado")
    # make executable
    new_file.chmod(new_file.stat().st_mode | stat.S_IEXEC)
    script = Path(tempfile.gettempdir()) / "organizador_update.sh"
    script.write_text(
        "#!/bin/bash\n"
        "sleep 2\n"
        f'mv -f "{target}" "{target}.bak"\n'
        f'mv -f "{new_file}" "{target}"\n'
        f'chmod +x "{target}"\n'
        f'"{target}" &\n'
        f'rm -f "{script}"\n'
    )
    script.chmod(0o755)
    # launch detached
    import subprocess
    subprocess.Popen(["/bin/bash", str(script)], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True
