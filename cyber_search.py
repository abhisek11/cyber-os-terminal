#!/usr/bin/env python3
"""
CYBER-OS // OMNI-SEARCH ENGINE (FILES, BROWSER HISTORY, WEB & INTERNET)
Cross-platform (Linux, macOS, Windows) zero-dependency 24-bit TrueColor
intelligence search engine.

Capabilities:
  1. Omni-Search (--omni <query>)       : Simultaneous File + Browser History + Web Search
  2. File & Code Search (--files <q>)   : Fast filename & inside-file content search
  3. Browser History (--history <q>)    : Chrome, Firefox, Brave, Edge, Chromium SQLite forensics
  4. Web & Internet Search (--web <q>)  : Live DuckDuckGo, Wikipedia & GitHub intelligence
  5. Browser Bookmarks (--bookmarks <q>): Extract & search browser bookmarks across profiles
"""

import argparse
import concurrent.futures
import ctypes
import datetime
import glob
import html
import json
import os
import platform
import re
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Dict, List, Tuple

from cyber_version import __version__


def enable_cross_platform_ansi():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if platform.system() == "Windows":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


enable_cross_platform_ansi()

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[38;2;0;243;255m"
MAGENTA = "\033[38;2;255;0;160m"
BLUE = "\033[38;2;90;100;255m"
PURPLE = "\033[38;2;189;0;255m"
YELLOW = "\033[38;2;252;238;10m"
GREEN = "\033[38;2;0;255;159m"
RED = "\033[38;2;255;42;109m"
GRAY = "\033[38;2;110;120;145m"
WHITE = "\033[38;2;230;245;255m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
BOX_INNER_WIDTH = 86
OS_NAME = platform.system()


def visible_len(text: str) -> int:
    """Terminal display width: strips ANSI codes and counts wide glyphs (e.g. ⚡) as 2 columns."""
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        for ch in ANSI_RE.sub("", text)
    )


def truncate_visible(text: str, width: int) -> str:
    """Cut text to at most `width` terminal columns, ending with an ellipsis.

    ANSI color codes take no columns and are kept, and RESET is appended when the cut text
    had any, so a color never runs past the cut. Text that already fits is returned as is.
    """
    if visible_len(text) <= width:
        return text
    if width <= 0:
        return ""
    budget = width - 1  # one column for the ellipsis
    out = []
    used = 0
    pos = 0
    while pos < len(text):
        match = ANSI_RE.match(text, pos)
        if match:
            out.append(match.group())
            pos = match.end()
            continue
        ch_width = visible_len(text[pos])
        if used + ch_width > budget:
            break
        out.append(text[pos])
        used += ch_width
        pos += 1
    suffix = RESET if ANSI_RE.search(text) else ""
    return "".join(out) + "…" + suffix


def box_row(content: str) -> str:
    content = truncate_visible(content, BOX_INNER_WIDTH)
    vlen = visible_len(content)
    pad = max(0, BOX_INNER_WIDTH - vlen)
    return f"{MAGENTA}║{RESET}{content}{' ' * pad}{MAGENTA}║{RESET}"


def print_header(title: str, subtitle: str = ""):
    print(f"\n{MAGENTA}╔{'═' * BOX_INNER_WIDTH}╗{RESET}")
    print(box_row(f" {CYAN}{BOLD}⚡ {title}{RESET}"))
    if subtitle:
        print(box_row(f" {GRAY}{subtitle[:BOX_INNER_WIDTH - 2]}{RESET}"))
    print(f"{MAGENTA}╚{'═' * BOX_INNER_WIDTH}╝{RESET}")


# ============================================================================
# 1. DEEP LOCAL FILE & CONTENT SEARCH
# ============================================================================
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".cache",
    "snap",
    "AppData",
    "Library",
}

BINARY_EXTS = {
    ".pyc", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".jpeg", ".gif",
    ".webp", ".mp4", ".mp3", ".wav", ".zip", ".tar", ".gz", ".pdf", ".woff",
    ".woff2", ".ttf", ".otf", ".sqlite", ".db", ".lock",
}


def search_local_files(
    query: str, root_dir: str = ".", max_results: int = 25
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (filename_matches, content_matches) for query inside root_dir."""
    abs_root = os.path.abspath(os.path.expanduser(root_dir))
    q_lower = query.lower().strip()
    name_matches: List[Dict[str, Any]] = []
    content_matches: List[Dict[str, Any]] = []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, abs_root)
            ext = os.path.splitext(fname)[1].lower()

            # 1. Check filename match
            if q_lower in fname.lower() or q_lower in rel_path.lower():
                try:
                    st = os.stat(fpath)
                    size_kb = st.st_size / 1024.0
                    mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    size_kb, mtime = 0.0, "—"
                name_matches.append(
                    {"path": rel_path, "abs_path": fpath, "size_kb": size_kb, "mtime": mtime}
                )

            # 2. Check inside-file text match
            if len(content_matches) < max_results and ext not in BINARY_EXTS:
                try:
                    if os.path.getsize(fpath) > 1_500_000:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            if q_lower in line.lower():
                                content_matches.append(
                                    {
                                        "path": rel_path,
                                        "abs_path": fpath,
                                        "line": lineno,
                                        "snippet": line.strip()[:90],
                                    }
                                )
                                if len(content_matches) >= max_results:
                                    break
                except Exception:
                    continue

        if len(name_matches) >= max_results and len(content_matches) >= max_results:
            break

    return name_matches[:max_results], content_matches[:max_results]


def render_file_search(query: str, root_dir: str = "."):
    print_header(
        "CYBER-FILES // DEEP LOCAL FILE & SOURCE CONTENT SCANNER",
        f"Query: '{query}'  │  Search Root: {os.path.abspath(os.path.expanduser(root_dir))}",
    )
    name_hits, content_hits = search_local_files(query, root_dir)

    print(f"\n  {PURPLE}{BOLD}[1] FILENAME MATCHES ({len(name_hits)}){RESET}")
    if not name_hits:
        print(f"  {GRAY}○ No matching file names found.{RESET}")
    else:
        for item in name_hits[:15]:
            print(
                f"  {CYAN}▸ {item['path']:<48}{RESET} "
                f"{YELLOW}{item['size_kb']:7.1f} KB{RESET}  {GRAY}{item['mtime']}{RESET}"
            )

    print(f"\n  {PURPLE}{BOLD}[2] INSIDE-FILE CONTENT MATCHES ({len(content_hits)}){RESET}")
    if not content_hits:
        print(f"  {GRAY}○ No matching text lines inside files.{RESET}\n")
    else:
        for hit in content_hits[:15]:
            loc = f"{hit['path']}:{hit['line']}"
            print(f"  {GREEN}● {loc:<42}{RESET} {WHITE}{hit['snippet']}{RESET}")
        print()


# ============================================================================
# 2. MULTI-BROWSER HISTORY & BOOKMARKS FORENSICS ENGINE
# ============================================================================
def _discover_browser_dbs() -> List[Tuple[str, str, str]]:
    """Return list of (browser_name, db_type, db_path) across Linux, macOS, and Windows."""
    home = os.path.expanduser("~")
    real_home = f"/home/{os.environ.get('USER', '')}" if OS_NAME == "Linux" else home
    roots = list({home, real_home})

    patterns: List[Tuple[str, str, str]] = []
    for h in roots:
        # Chrome / Chromium / Brave / Edge (Linux)
        patterns.extend([
            ("Chrome", "chromium", f"{h}/.config/google-chrome/*/History"),
            ("Chromium", "chromium", f"{h}/.config/chromium/*/History"),
            ("Chromium-Snap", "chromium", f"{h}/snap/chromium/common/chromium/*/History"),
            ("Brave", "chromium", f"{h}/.config/BraveSoftware/Brave-Browser/*/History"),
            ("Edge", "chromium", f"{h}/.config/microsoft-edge/*/History"),
            # Firefox (Linux + Desktop Old Firefox Data backup)
            ("Firefox", "firefox", f"{h}/.mozilla/firefox/*/places.sqlite"),
            ("Firefox-Snap", "firefox", f"{h}/snap/firefox/common/.mozilla/firefox/*/places.sqlite"),
            ("Firefox-Backup", "firefox", f"{h}/Desktop/Old Firefox Data/*/places.sqlite"),
            # macOS paths
            ("Chrome", "chromium", f"{h}/Library/Application Support/Google/Chrome/*/History"),
            ("Brave", "chromium", f"{h}/Library/Application Support/BraveSoftware/Brave-Browser/*/History"),
            ("Edge", "chromium", f"{h}/Library/Application Support/Microsoft Edge/*/History"),
            ("Firefox", "firefox", f"{h}/Library/Application Support/Firefox/Profiles/*/places.sqlite"),
        ])

    if OS_NAME == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", "")
        roaming_app = os.environ.get("APPDATA", "")
        if local_app:
            patterns.extend([
                ("Chrome", "chromium", os.path.join(local_app, r"Google\Chrome\User Data\*\History")),
                ("Brave", "chromium", os.path.join(local_app, r"BraveSoftware\Brave-Browser\User Data\*\History")),
                ("Edge", "chromium", os.path.join(local_app, r"Microsoft\Edge\User Data\*\History")),
            ])
        if roaming_app:
            patterns.append(
                ("Firefox", "firefox", os.path.join(roaming_app, r"Mozilla\Firefox\Profiles\*\places.sqlite"))
            )

    found: List[Tuple[str, str, str]] = []
    seen = set()
    for bname, btype, pat in patterns:
        for path in glob.glob(pat):
            if os.path.isfile(path) and path not in seen:
                seen.add(path)
                found.append((bname, btype, path))
    return found


def search_browser_history(query: str = "", limit: int = 25) -> List[Dict[str, Any]]:
    """Query all discovered browser SQLite databases safely (even if locked by active browser)."""
    dbs = _discover_browser_dbs()
    results: List[Dict[str, Any]] = []
    q_clean = "" if query.strip() in ("*", "all", "recent") else query.strip()
    like_pat = f"%{q_clean}%"

    for bname, btype, db_path in dbs:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(tmp_fd)
        try:
            shutil.copy2(db_path, tmp_path)
            conn = sqlite3.connect(tmp_path, timeout=2.0)
            cur = conn.cursor()
            if btype == "chromium":
                cur.execute(
                    """
                    SELECT url, title, visit_count, last_visit_time
                    FROM urls
                    WHERE (url LIKE ? OR title LIKE ?)
                    ORDER BY last_visit_time DESC
                    LIMIT ?
                    """,
                    (like_pat, like_pat, limit),
                )
                for url, title, vcount, last_vt in cur.fetchall():
                    # Chrome timestamp is microseconds since 1601-01-01
                    ts_str = "—"
                    if last_vt and last_vt > 0:
                        try:
                            epoch_sec = (last_vt / 1_000_000.0) - 11644473600.0
                            if epoch_sec > 0:
                                ts_str = datetime.datetime.fromtimestamp(epoch_sec).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            pass
                    results.append({
                        "browser": bname,
                        "title": (title or url)[:65],
                        "url": url,
                        "visits": vcount or 1,
                        "time": ts_str,
                    })
            elif btype == "firefox":
                cur.execute(
                    """
                    SELECT url, title, visit_count, last_visit_date
                    FROM moz_places
                    WHERE (url LIKE ? OR title LIKE ?) AND visit_count > 0
                    ORDER BY last_visit_date DESC
                    LIMIT ?
                    """,
                    (like_pat, like_pat, limit),
                )
                for url, title, vcount, last_vd in cur.fetchall():
                    ts_str = "—"
                    if last_vd and last_vd > 0:
                        try:
                            ts_str = datetime.datetime.fromtimestamp(last_vd / 1_000_000.0).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            pass
                    results.append({
                        "browser": bname,
                        "title": (title or url)[:65],
                        "url": url,
                        "visits": vcount or 1,
                        "time": ts_str,
                    })
            conn.close()
        except Exception:
            pass
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    return results[:limit]


def render_browser_history(query: str = "recent", limit: int = 25):
    print_header(
        "CYBER-HISTORY // MULTI-BROWSER SQLITE HISTORY FORENSICS",
        f"Query: '{query}'  │  Browsers: Chrome, Firefox, Brave, Edge, Chromium",
    )
    dbs = _discover_browser_dbs()
    print(f"\n  {GRAY}▸ Detected Browser Databases :{RESET} {CYAN}{len(dbs)} profile{'' if len(dbs) == 1 else 's'}{RESET}")
    for bname, _, path in dbs[:4]:
        print(f"    {GRAY}• {bname:<14}:{RESET} {WHITE}{path}{RESET}")

    items = search_browser_history(query, limit=limit)
    if not items:
        print(f"\n  {YELLOW}○ No matching browser history entries found for '{query}'.{RESET}\n")
        return

    print(f"\n  {MAGENTA}{'BROWSER':<12} {'LAST VISIT':<17} {'VISITS':<8} {'TITLE & URL'}{RESET}")
    print(f"  {GRAY}{'─' * 82}{RESET}")
    for r in items:
        print(
            f"  {CYAN}{BOLD}{r['browser']:<12}{RESET} "
            f"{PURPLE}{r['time']:<17}{RESET} "
            f"{YELLOW}{str(r['visits']):<8}{RESET} "
            f"{WHITE}{BOLD}{r['title']}{RESET}"
        )
        print(f"  {' ' * 39}{GREEN}{r['url'][:82]}{RESET}")
    print()


# ============================================================================
# 3. LIVE WEB & INTERNET INTELLIGENCE SEARCH
# ============================================================================
def search_web_internet(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Query DuckDuckGo HTML, Wikipedia OpenSearch & GitHub Repositories for live internet results."""
    results: List[Dict[str, str]] = []
    encoded_q = urllib.parse.quote_plus(query)

    # 1. DuckDuckGo HTML Search
    try:
        req = urllib.request.Request(
            f"https://html.duckduckgo.com/html/?q={encoded_q}",
            headers={
                "User-Agent": f"Mozilla/5.0 (X11; Linux x86_64) CyberOS/{__version__}",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=4.5) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
        for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.DOTALL
        ):
            raw_href, raw_title = m.group(1), m.group(2)
            # Extract real URL if wrapped in uddg=
            if "uddg=" in raw_href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                real_url = qs.get("uddg", [raw_href])[0]
            else:
                real_url = raw_href
            clean_title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
            if real_url.startswith("http"):
                results.append({"source": "WEB", "title": clean_title[:72], "url": real_url})
            if len(results) >= max_results:
                break
    except Exception:
        pass

    # 2. Wikipedia OpenSearch API
    try:
        w_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_q}&limit=4&namespace=0&format=json"
        req = urllib.request.Request(w_url, headers={"User-Agent": f"CyberOS/{__version__}"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            w_data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            if len(w_data) >= 4:
                titles, _, urls = w_data[1], w_data[2], w_data[3]
                for t, u in zip(titles, urls):
                    results.append({"source": "WIKI", "title": t, "url": u})
    except Exception:
        pass

    # 3. GitHub Public Repositories Search API
    try:
        gh_url = f"https://api.github.com/search/repositories?q={encoded_q}&per_page=4"
        req = urllib.request.Request(gh_url, headers={"User-Agent": f"CyberOS/{__version__}"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            gh_data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            for repo in gh_data.get("items", [])[:4]:
                desc = repo.get("description") or ""
                stars = repo.get("stargazers_count", 0)
                results.append({
                    "source": f"GITHUB ★{stars}",
                    "title": f"{repo.get('full_name')} — {desc[:55]}",
                    "url": repo.get("html_url", ""),
                })
    except Exception:
        pass

    return results[: max_results + 4]


def render_web_search(query: str, open_browser: bool = False):
    print_header(
        "CYBER-WEB // LIVE INTERNET, WIKIPEDIA & GITHUB INTELLIGENCE",
        f"Search Query: '{query}'",
    )
    items = search_web_internet(query)
    if not items:
        print(f"\n  {YELLOW}○ No live web results fetched (check internet connection).{RESET}\n")
    else:
        print()
        for idx, r in enumerate(items, 1):
            print(f"  {CYAN}{BOLD}[{idx:02d}] [{r['source']}]{RESET} {WHITE}{BOLD}{r['title']}{RESET}")
            print(f"       {GREEN}{r['url']}{RESET}")
        print()

    if open_browser:
        target_url = items[0]["url"] if items else f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}"
        print(f"  {MAGENTA}⚡ Launching browser:{RESET} {CYAN}{target_url}{RESET}\n")
        webbrowser.open(target_url)


# ============================================================================
# 4. UNIFIED OMNI-SEARCH (FILES + BROWSER HISTORY + INTERNET)
# ============================================================================
def render_omni_search(query: str, root_dir: str = ".", open_browser: bool = False):
    print_header(
        "CYBER-OMNI // UNIFIED NEURAL SEARCH (FILES + HISTORY + INTERNET)",
        f"Omni-Query: '{query}'",
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        fut_files = ex.submit(search_local_files, query, root_dir, 8)
        fut_hist = ex.submit(search_browser_history, query, 8)
        fut_web = ex.submit(search_web_internet, query, 6)

        name_hits, content_hits = fut_files.result()
        hist_hits = fut_hist.result()
        web_hits = fut_web.result()

    # 1. Local Files
    print(f"\n  {PURPLE}{BOLD}━━━ [1] LOCAL FILES & CODE MATCHES ({len(name_hits)} files, {len(content_hits)} lines) ━━━{RESET}")
    for f in name_hits[:5]:
        print(f"  {CYAN}▸ [FILE]{RESET} {WHITE}{f['path']:<48}{RESET} {GRAY}({f['size_kb']:.1f} KB){RESET}")
    for c in content_hits[:5]:
        print(f"  {GREEN}▸ [CODE]{RESET} {CYAN}{c['path']}:{c['line']:<6}{RESET} {WHITE}{c['snippet'][:60]}{RESET}")
    if not name_hits and not content_hits:
        print(f"  {GRAY}○ No local file matches in {os.path.abspath(root_dir)}.{RESET}")

    # 2. Browser History
    print(f"\n  {PURPLE}{BOLD}━━━ [2] BROWSER HISTORY MATCHES ({len(hist_hits)}) ━━━{RESET}")
    for h in hist_hits[:6]:
        print(f"  {YELLOW}▸ [{h['browser']}]{RESET} {WHITE}{h['title']}{RESET} {GRAY}({h['time']}){RESET}")
        print(f"    {GREEN}{h['url'][:80]}{RESET}")
    if not hist_hits:
        print(f"  {GRAY}○ No matching browser history records.{RESET}")

    # 3. Live Internet & Web
    print(f"\n  {PURPLE}{BOLD}━━━ [3] LIVE WEB, WIKI & GITHUB MATCHES ({len(web_hits)}) ━━━{RESET}")
    for w in web_hits[:6]:
        print(f"  {MAGENTA}▸ [{w['source']}]{RESET} {WHITE}{BOLD}{w['title']}{RESET}")
        print(f"    {CYAN}{w['url']}{RESET}")
    if not web_hits:
        print(f"  {GRAY}○ No live internet results available.{RESET}")
    print()

    if open_browser and web_hits:
        webbrowser.open(web_hits[0]["url"])


def main():
    parser = argparse.ArgumentParser(description="CYBER-OS // Omni-Search Engine (Files, History, Web)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("query", nargs="?", default="", help="Search query string")
    parser.add_argument("--omni", metavar="QUERY", help="Search Files + Browser History + Live Web simultaneously")
    parser.add_argument("--files", metavar="QUERY", help="Search local filenames and file contents")
    parser.add_argument("--dir", default=".", help="Root directory for file search (default: current directory)")
    parser.add_argument("--history", nargs="?", const="recent", metavar="QUERY", help="Search Chrome/Firefox/Brave/Edge history")
    parser.add_argument("--web", metavar="QUERY", help="Search live Internet (DuckDuckGo, Wikipedia, GitHub)")
    parser.add_argument("--open", action="store_true", help="Open top web result in browser")
    parser.add_argument("--json", action="store_true", help="Return JSON output (used by Cyber-Vision HUD)")

    args = parser.parse_args()

    q = args.omni or args.query
    if args.json and q:
        name_hits, content_hits = search_local_files(q, args.dir, 8)
        hist_hits = search_browser_history(q, 8)
        web_hits = search_web_internet(q, 6)
        print(json.dumps({
            "query": q,
            "files": name_hits,
            "code": content_hits,
            "history": hist_hits,
            "web": web_hits,
        }))
        return

    if args.files:
        render_file_search(args.files, args.dir)
    elif args.history is not None:
        render_browser_history(args.history)
    elif args.web:
        render_web_search(args.web, open_browser=args.open)
    elif q:
        render_omni_search(q, args.dir, open_browser=args.open)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
