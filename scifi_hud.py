#!/usr/bin/env python3
"""
CYBER-OS // NEURAL TERMINAL TELEMETRY HUD & EFFECTS
Cross-platform (Linux, macOS, Windows) zero-dependency 24-bit TrueColor
Cyberpunk Neon terminal interface.

Provides:
  - Startup boot animation & live system telemetry banner (default)
  - Live thread count, process count & scheduled jobs telemetry
  - Live auto-refreshing cockpit monitor (--watch)
  - Cyberpunk neon digital rain (--matrix)
  - Local network & port telemetry scanner (--scan)
"""

import argparse
import ctypes
import datetime
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
from typing import Tuple

from cyber_version import __version__


def enable_cross_platform_ansi():
    """Enable UTF-8 and 24-bit ANSI TrueColor sequences on Windows, macOS, and Linux."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if platform.system() == "Windows":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


enable_cross_platform_ansi()

# 24-bit TrueColor ANSI escape helpers (Cyberpunk Neon Palette)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

def _supports_truecolor() -> bool:
    """macOS Terminal.app only supports 256 colors; 24-bit sequences render as wrong colors there."""
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    if os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
        return False
    return True


def _rgb_to_256(r: int, g: int, b: int) -> int:
    """Nearest xterm-256 color cube index."""
    def lvl(v):
        return 0 if v < 48 else 1 if v < 115 else (v - 35) // 40
    return 16 + 36 * lvl(r) + 6 * lvl(g) + lvl(b)


def _fg(r: int, g: int, b: int) -> str:
    if _supports_truecolor():
        return f"\033[38;2;{r};{g};{b}m"
    return f"\033[38;5;{_rgb_to_256(r, g, b)}m"


# Neon Palette
CYAN = _fg(0, 243, 255)         # #00f3ff Electric Cyan
MAGENTA = _fg(255, 0, 160)      # #ff00a0 Neon Magenta
BLUE = _fg(90, 100, 255)        # #5a64ff Cyber Blue
PURPLE = _fg(189, 0, 255)       # #bd00ff Synthwave Purple
YELLOW = _fg(252, 238, 10)      # #fcee0a Cyberpunk Yellow
GREEN = _fg(0, 255, 159)        # #00ff9f Matrix/Neon Mint
RED = _fg(255, 42, 109)         # #ff2a6d Alert Crimson
GRAY = _fg(110, 120, 145)       # #6e7891 Muted Slate
WHITE = _fg(230, 245, 255)      # #e6f5ff Hologram White

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
    """Wrap a row in Neon Magenta double borders with exact right-side alignment."""
    content = truncate_visible(content, BOX_INNER_WIDTH)
    vlen = visible_len(content)
    pad = max(0, BOX_INNER_WIDTH - vlen)
    return f"{MAGENTA}║{RESET}{content}{' ' * pad}{MAGENTA}║{RESET}"


def get_cpu_usage() -> float:
    """Read instant CPU usage across Linux, macOS, and Windows."""
    if OS_NAME == "Linux":
        try:
            with open("/proc/stat", "r", encoding="utf-8") as f:
                line1 = f.readline()
            parts1 = [int(x) for x in line1.split()[1:]]
            idle1, total1 = parts1[3] + parts1[4], sum(parts1)
            time.sleep(0.05)
            with open("/proc/stat", "r", encoding="utf-8") as f:
                line2 = f.readline()
            parts2 = [int(x) for x in line2.split()[1:]]
            idle2, total2 = parts2[3] + parts2[4], sum(parts2)
            total_diff = total2 - total1
            if total_diff > 0:
                return max(0.0, min(100.0, 100.0 * (1.0 - (idle2 - idle1) / total_diff)))
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "loadpercentage"],
                stderr=subprocess.DEVNULL,
                timeout=1.5,
                text=True,
            )
            nums = [int(s) for s in out.split() if s.isdigit()]
            if nums:
                return float(sum(nums) / len(nums))
        except Exception:
            pass

    if hasattr(os, "getloadavg"):
        try:
            load1, _, _ = os.getloadavg()
            cpus = os.cpu_count() or 1
            return min(100.0, (load1 / cpus) * 100.0)
        except Exception:
            pass
    return 12.5


def get_cpu_model() -> str:
    if OS_NAME == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        model = line.split(":", 1)[1].strip()
                        for token in ["(R)", "(TM)", "CPU", "Processor"]:
                            model = model.replace(token, "")
                        return " ".join(model.split())[:28]
        except Exception:
            pass
    elif OS_NAME == "Darwin":
        try:
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stderr=subprocess.DEVNULL,
                timeout=1.0,
                text=True,
            ).strip()
            if out:
                return out[:28]
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "name"],
                stderr=subprocess.DEVNULL,
                timeout=1.5,
                text=True,
            )
            lines = [ln.strip() for ln in out.splitlines() if ln.strip() and "Name" not in ln]
            if lines:
                return lines[0][:28]
        except Exception:
            pass
    return (platform.processor() or f"{os.cpu_count() or 1}-Core Neural Unit")[:28]


def get_memory_info() -> Tuple[float, float, float]:
    """Return (used_gb, total_gb, percent) across Linux, macOS, and Windows."""
    if OS_NAME == "Linux":
        try:
            mem = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].strip().split()[0])
            total_kb = mem.get("MemTotal", 1)
            avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
            used_kb = max(0, total_kb - avail_kb)
            total_gb = total_kb / (1024 * 1024)
            used_gb = used_kb / (1024 * 1024)
            pct = (used_kb / total_kb) * 100.0
            return used_gb, total_gb, pct
        except Exception:
            pass
    elif OS_NAME == "Darwin":
        try:
            total_bytes = int(
                subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=1.0).strip()
            )
            vm_out = subprocess.check_output(["vm_stat"], text=True, timeout=1.0)
            page_size = 4096
            counts = {}
            for ln in vm_out.splitlines():
                if "page size of" in ln:
                    m = re.search(r"(\d+)\s+bytes", ln)
                    if m:
                        page_size = int(m.group(1))
                    continue
                m = re.match(r"\s*\"?([^:\"]+)\"?:\s*(\d+)", ln)
                if m:
                    counts[m.group(1).strip()] = int(m.group(2))
            # Activity Monitor "Memory Used" = App memory + Wired + Compressed
            used_pages = (
                counts.get("Anonymous pages", counts.get("Pages active", 0))
                + counts.get("Pages wired down", 0)
                + counts.get("Pages occupied by compressor", 0)
            )
            total_gb = total_bytes / (1024**3)
            used_gb = min(total_gb, (used_pages * page_size) / (1024**3))
            pct = (used_gb / total_gb) * 100.0 if total_gb > 0 else 0.0
            return used_gb, total_gb, pct
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = stat.ullTotalPhys / (1024**3)
            avail_gb = stat.ullAvailPhys / (1024**3)
            used_gb = max(0.0, total_gb - avail_gb)
            return used_gb, total_gb, float(stat.dwMemoryLoad)
        except Exception:
            pass
    return 0.0, 1.0, 0.0


def get_disk_info() -> Tuple[float, float, float]:
    candidates = [os.getcwd(), os.path.expanduser("~"), "/"]
    if OS_NAME == "Darwin":
        # "/" is the sealed read-only system volume; user data lives on the Data volume
        candidates.insert(0, "/System/Volumes/Data")
    for candidate in candidates:
        try:
            usage = shutil.disk_usage(candidate)
            if usage.used > 0 and usage.total > 0:
                total_gb = usage.total / (1024**3)
                used_gb = usage.used / (1024**3)
                pct = (usage.used / usage.total) * 100.0
                return used_gb, total_gb, pct
        except Exception:
            continue
    return 0.0, 1.0, 0.0


def get_uptime() -> str:
    if OS_NAME == "Linux":
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as f:
                seconds = int(float(f.read().split()[0]))
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            if days > 0:
                return f"{days}d {hours:02d}h {mins:02d}m"
            return f"{hours:02d}h {mins:02d}m {secs:02d}s"
        except Exception:
            pass
    elif OS_NAME == "Darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True, timeout=1.0)
            m = re.search(r"sec\s*=\s*(\d+)", out)
            if m:
                seconds = int(time.time()) - int(m.group(1))
                days, rem = divmod(seconds, 86400)
                hours, rem = divmod(rem, 3600)
                mins, _ = divmod(rem, 60)
                return f"{days}d {hours:02d}h {mins:02d}m"
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            seconds = int(ctypes.windll.kernel32.GetTickCount64() // 1000)
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            mins, _ = divmod(rem, 60)
            return f"{days}d {hours:02d}h {mins:02d}m"
        except Exception:
            pass
    return "ONLINE"


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.15)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def get_threads_and_jobs_summary() -> Tuple[int, int, int]:
    """Return (process_count, live_thread_count, scheduled_jobs_count) across platforms."""
    proc_count = 0
    thread_count = 0
    sched_count = 0

    # 1. Process & Live Thread Counts
    if OS_NAME == "Linux":
        try:
            for entry in os.scandir("/proc"):
                if entry.name.isdigit():
                    proc_count += 1
                    try:
                        with open(f"/proc/{entry.name}/status", "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("Threads:"):
                                    thread_count += int(line.split()[1])
                                    break
                    except Exception:
                        thread_count += 1
        except Exception:
            pass
        if proc_count == 0:
            try:
                out = subprocess.check_output(["ps", "-eo", "nlwp"], text=True, timeout=1.5)
                vals = [int(x.strip()) for x in out.splitlines()[1:] if x.strip().isdigit()]
                proc_count = len(vals)
                thread_count = sum(vals)
            except Exception:
                pass
    elif OS_NAME == "Darwin":
        try:
            out = subprocess.check_output(["ps", "-axo", "pid"], text=True, timeout=1.5)
            proc_count = max(0, len(out.splitlines()) - 1)
            thread_count = proc_count
            try:
                # `ps -M` prints one row per thread
                tout = subprocess.check_output(["ps", "-axM"], text=True, timeout=3.0)
                thread_count = max(proc_count, len(tout.splitlines()) - 1)
            except Exception:
                pass
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "process", "get", "ThreadCount"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            vals = [int(x.strip()) for x in out.splitlines() if x.strip().isdigit()]
            proc_count = len(vals)
            thread_count = sum(vals)
        except Exception:
            pass

    # 2. Scheduled Jobs Count (Cron / Systemd Timers / Launchd / Windows Task Scheduler / Active Daemons)
    if OS_NAME in ("Linux", "Darwin"):
        try:
            out = subprocess.check_output(
                ["crontab", "-l"], stderr=subprocess.DEVNULL, text=True, timeout=1.0
            )
            sched_count += sum(
                1 for ln in out.splitlines() if ln.strip() and not ln.strip().startswith("#")
            )
        except Exception:
            pass
        for cron_dir in ("/etc/cron.d", "/etc/cron.daily", "/etc/cron.hourly", "/etc/cron.weekly"):
            if os.path.isdir(cron_dir):
                try:
                    sched_count += len(
                        [f for f in os.listdir(cron_dir) if not f.startswith(".")]
                    )
                except Exception:
                    pass
        if sched_count == 0 and OS_NAME == "Linux":
            # Count active background service/timer daemons from /proc
            try:
                for entry in os.scandir("/proc"):
                    if entry.name.isdigit():
                        try:
                            with open(f"/proc/{entry.name}/status", "r", encoding="utf-8") as f:
                                first_line = f.readline()
                            if first_line.startswith("Name:"):
                                cname = first_line.split(":", 1)[1].strip()
                                if cname in ("cron", "crond", "atd", "anacron", "systemd-timesyn", "ollama", "dockerd", "containerd", "sshd", "redis-server", "postgres"):
                                    sched_count += 1
                        except Exception:
                            continue
            except Exception:
                pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["schtasks", "/query", "/fo", "csv", "/nh"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            sched_count = len([ln for ln in out.splitlines() if ln.strip()])
        except Exception:
            pass

    return proc_count, thread_count, sched_count


def make_bar(percent: float, width: int = 18) -> str:
    """Create a neon segmented progress bar."""
    percent = max(0.0, min(100.0, percent))
    filled = int(round((percent / 100.0) * width))
    empty = width - filled
    if percent < 60:
        color = CYAN
    elif percent < 85:
        color = YELLOW
    else:
        color = RED
    bar_str = f"{color}{'▰' * filled}{GRAY}{'▱' * empty}{RESET}"
    return f"[{bar_str}] {color}{BOLD}{percent:5.1f}%{RESET}"


def boot_sequence():
    """Fast sci-fi neural handshake boot animation."""
    steps = [
        f"{CYAN}⚡ INITIALIZING CYBER-OS KERNEL UPLINK ({OS_NAME.upper()})...{RESET}",
        f"{MAGENTA}❖ SYNCING QUANTUM TELEMETRY & THREAD SENSORS...{RESET}",
        f"{GREEN}✔ NEURAL INTERFACE LOCKED // ACCESS GRANTED{RESET}",
    ]
    for step in steps:
        sys.stdout.write(f"\r\033[K  {step}")
        sys.stdout.flush()
        time.sleep(0.11)
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def render_hud(animate_boot: bool = False):
    if animate_boot and sys.stdout.isatty():
        boot_sequence()

    user = os.environ.get("USER") or os.environ.get("USERNAME") or "operator"
    host = platform.node() or "cyber-deck"
    kernel = f"{OS_NAME} {platform.release()}"[:18]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d // %H:%M:%S")
    uptime_str = get_uptime()
    ip_str = get_local_ip()
    cpu_model = get_cpu_model()
    cores = os.cpu_count() or 1
    cpu_pct = get_cpu_usage()
    mem_used, mem_total, mem_pct = get_memory_info()
    disk_used, disk_total, disk_pct = get_disk_info()
    proc_cnt, thread_cnt, sched_cnt = get_threads_and_jobs_summary()

    border_top = f"{MAGENTA}╔{'═' * BOX_INNER_WIDTH}╗{RESET}"
    border_mid = f"{MAGENTA}╠{'═' * BOX_INNER_WIDTH}╣{RESET}"
    border_bot = f"{MAGENTA}╚{'═' * BOX_INNER_WIDTH}╝{RESET}"

    print(border_top)
    print(
        box_row(
            f" {CYAN}{BOLD}◢◤ CYBER-DECK // NEURAL TERMINAL OS v{__version__}{RESET}"
            f"            {YELLOW}⚡ STATUS: {GREEN}{BOLD}ONLINE{RESET}"
        )
    )
    print(
        box_row(
            f" {GRAY}OPERATOR:{RESET} {WHITE}{BOLD}{user}@{host}{RESET}"
            f"  {GRAY}│{RESET} {GRAY}TIME:{RESET} {CYAN}{now_str}{RESET}"
            f"  {GRAY}│{RESET} {GRAY}UP:{RESET} {PURPLE}{uptime_str}{RESET}"
        )
    )
    print(border_mid)

    # Telemetry rows
    print(
        box_row(
            f" {CYAN}❖ CPU CORE :{RESET} {make_bar(cpu_pct, 18)} "
            f"{GRAY}│{RESET} {WHITE}{cpu_model} ({cores}T){RESET}"
        )
    )
    print(
        box_row(
            f" {MAGENTA}❖ MEM GRID :{RESET} {make_bar(mem_pct, 18)} "
            f"{GRAY}│{RESET} {WHITE}{mem_used:.1f} GB / {mem_total:.1f} GB ALLOCATED{RESET}"
        )
    )
    print(
        box_row(
            f" {BLUE}❖ DISK VOL :{RESET} {make_bar(disk_pct, 18)} "
            f"{GRAY}│{RESET} {WHITE}{disk_used:.1f} GB / {disk_total:.1f} GB STORAGE{RESET}"
        )
    )
    print(border_mid)

    print(
        box_row(
            f" {YELLOW}◈ NET LINK :{RESET} {GREEN}{ip_str:<14}{RESET} "
            f"{GRAY}│{RESET} {YELLOW}◈ THREADS :{RESET} {CYAN}{BOLD}{thread_cnt:<5}{RESET}{GRAY}({proc_cnt} procs){RESET} "
            f"{GRAY}│{RESET} {YELLOW}◈ SCHED JOBS :{RESET} {MAGENTA}{BOLD}{sched_cnt}{RESET}"
        )
    )
    print(
        box_row(
            f" {PURPLE}◈ TELEMETRY:{RESET} "
            f"{CYAN}hud{RESET} • "
            f"{CYAN}cyber-watch{RESET} • "
            f"{CYAN}cyber-matrix{RESET} • "
            f"{CYAN}cyber-jobs{RESET} {GRAY}(threads/cron){RESET}"
        )
    )
    print(
        box_row(
            f" {MAGENTA}◈ ARSENAL  :{RESET} "
            f"{GREEN}{BOLD}cyber-tools{RESET} • "
            f"{CYAN}cyber-ports{RESET} • "
            f"{CYAN}cyber-kill{RESET} • "
            f"{CYAN}cyber-recon{RESET} • "
            f"{CYAN}cyber-audit{RESET}"
        )
    )
    print(
        box_row(
            f" {CYAN}◈ AI/VISION:{RESET} "
            f"{GREEN}{BOLD}cyber-cam{RESET} {GRAY}(age/mood/ASL){RESET} • "
            f"{CYAN}cyber-search{RESET}"
        )
    )
    print(border_bot)


def watch_hud():
    """Live auto-refreshing Cyberpunk cockpit HUD."""
    try:
        sys.stdout.write("\033[?25l\033[2J")
        while True:
            sys.stdout.write("\033[H")
            render_hud(animate_boot=False)
            print(f"\n  {GRAY}[ Press {CYAN}Ctrl+C{GRAY} to exit live telemetry feed ]{RESET}")
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()


def matrix_rain():
    """Cyberpunk Neon Matrix rain animation (Cyan, Magenta, Electric Blue)."""
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン⚡❖◢◤◈"
    try:
        cols, rows = shutil.get_terminal_size((80, 24))
        drops = [random.randint(-rows, 0) for _ in range(cols)]
        speeds = [random.randint(1, 2) for _ in range(cols)]
        colors = [CYAN, CYAN, MAGENTA, BLUE, GREEN]
        col_colors = [random.choice(colors) for _ in range(cols)]

        sys.stdout.write("\033[?25l\033[2J")
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            if len(drops) != cols:
                drops = [random.randint(-rows, 0) for _ in range(cols)]
                speeds = [random.randint(1, 2) for _ in range(cols)]
                col_colors = [random.choice(colors) for _ in range(cols)]

            output = []
            for x in range(0, cols - 1, 2):
                y = drops[x]
                if 0 <= y < rows - 1:
                    ch = random.choice(chars)
                    output.append(f"\033[{y + 1};{x + 1}H{WHITE}{BOLD}{ch}{RESET}")
                if 0 <= y - 1 < rows - 1:
                    ch_trail = random.choice(chars)
                    output.append(f"\033[{y};{x + 1}H{col_colors[x]}{ch_trail}{RESET}")
                erase_y = y - random.randint(8, 16)
                if 0 <= erase_y < rows - 1:
                    output.append(f"\033[{erase_y + 1};{x + 1}H ")

                drops[x] += speeds[x]
                if drops[x] - 16 > rows:
                    drops[x] = random.randint(-10, 0)
                    col_colors[x] = random.choice(colors)

            output.append(
                f"\033[{rows};2H{MAGENTA}╔══ {CYAN}{BOLD}CYBER-MATRIX NEURAL STREAM{RESET}"
                f"{MAGENTA} ══ {GRAY}[Press Ctrl+C to disconnect]{MAGENTA} ══╗{RESET}"
            )
            sys.stdout.write("".join(output))
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.flush()


def network_scan():
    """Real local socket/interface & port telemetry scan with sci-fi display."""
    print(f"\n{MAGENTA}╔{'═' * BOX_INNER_WIDTH}╗{RESET}")
    print(box_row(f" {CYAN}{BOLD}📡 CYBER-SCAN // LOCAL NODE & PORT TELEMETRY SWEEP{RESET}"))
    print(f"{MAGENTA}╚{'═' * BOX_INNER_WIDTH}╝{RESET}\n")

    ip = get_local_ip()
    hostname = socket.gethostname()
    print(f"  {GRAY}▸ HOST NODE   :{RESET} {WHITE}{BOLD}{hostname}{RESET}")
    print(f"  {GRAY}▸ PRIMARY IP  :{RESET} {CYAN}{BOLD}{ip}{RESET}\n")

    common_ports = [
        (22, "SSH-DAEMON"),
        (80, "HTTP-WEB"),
        (443, "HTTPS-TLS"),
        (3000, "DEV-PORTAL"),
        (5000, "AI-API-NODE"),
        (5432, "POSTGRES-DB"),
        (6379, "REDIS-CACHE"),
        (8000, "AGENT-SERVER"),
        (8080, "PROXY-GATE"),
        (9000, "SONAR-PORT"),
        (11434, "OLLAMA-LLM"),
    ]

    print(f"  {PURPLE}{BOLD}SWEEPING LOCALHOST QUANTUM PORTS...{RESET}")
    open_count = 0
    for port, label in common_ports:
        sys.stdout.write(f"  {GRAY}Scanning [{port:5d} // {label:<12}] ... {RESET}")
        sys.stdout.flush()
        time.sleep(0.03)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.08)
            res = s.connect_ex(("127.0.0.1", port))
            if res == 0:
                open_count += 1
                print(f"{GREEN}{BOLD}● ACTIVE / LISTENING{RESET}")
            else:
                print(f"{GRAY}○ CLOSED / SHIELDED{RESET}")

    print(
        f"\n  {CYAN}✔ SWEEP COMPLETE:{RESET} {WHITE}{open_count} active local service{'' if open_count == 1 else 's'} detected, "
        f"{len(common_ports) - open_count} shielded.{RESET}\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Cyberpunk Sci-Fi Terminal HUD (Linux, macOS, Windows)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--boot", action="store_true", help="Show boot animation before HUD")
    parser.add_argument("--watch", action="store_true", help="Live auto-refreshing HUD")
    parser.add_argument("--matrix", action="store_true", help="Cyberpunk neon Matrix rain")
    parser.add_argument("--scan", action="store_true", help="Local port & network telemetry sweep")
    args = parser.parse_args()

    if args.watch:
        watch_hud()
    elif args.matrix:
        matrix_rain()
    elif args.scan:
        network_scan()
    else:
        render_hud(animate_boot=args.boot)


if __name__ == "__main__":
    main()
