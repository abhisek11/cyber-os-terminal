#!/usr/bin/env python3
"""
CYBER-OS // NEURAL SECURITY, PORT-KILLER, JOB/THREAD & RECONNAISSANCE ARSENAL
Cross-platform (Linux, macOS, Windows) zero-dependency 24-bit TrueColor
Cyberpunk Neon cybersecurity & process/job management toolkit.

Provides both an interactive TUI menu (`cyber-tools`) and direct CLI modes:
  1. Multi-threaded TCP Port, Process & Banner Scanner (--ports)
  2. Kill Port Job / Terminate Process on Port         (--kill-port <PORT>)
  3. Live Thread Counts, Process & Scheduled Jobs Scan (--jobs)
  4. Domain / IP Recon, DNS & RDAP/WHOIS Lookup        (--recon)
  5. SSL/TLS Certificate & Cipher Inspector            (--ssl)
  6. HTTP Security Header & Server Auditor             (--headers)
  7. Active Network Connections & Socket Monitor       (--conn)
  8. Multi-Algo Crypto Hasher (String / File)          (--hash)
  9. Universal Payload Decoder (Base64/Hex/URL/JWT)    (--decode)
 10. Quantum CSPRNG Key & Password Generator           (--keygen)
 11. File Integrity Monitor (SHA-256 Baseline/Diff)    (--fim)
 12. System Security, Kernel & Auth Forensics Audit    (--audit)
 13. Source Code Secret & Credential Leak Scanner      (--secrets)
 14. Cross-Platform Cyber Arsenal & Nmap Wrapper       (--arsenal / --nmap)
"""

import argparse
import base64
import concurrent.futures
import ctypes
import datetime
import hashlib
import json
import math
import os
import platform
import re
import secrets
import shutil
import signal
import socket
import ssl
import stat
import string
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Dict, List, Optional, Tuple


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
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


enable_cross_platform_ansi()

# 24-bit TrueColor ANSI escape helpers (Cyberpunk Neon Palette)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[38;2;0;243;255m"         # #00f3ff Electric Cyan
MAGENTA = "\033[38;2;255;0;160m"      # #ff00a0 Neon Magenta
BLUE = "\033[38;2;90;100;255m"        # #5a64ff Cyber Blue
PURPLE = "\033[38;2;189;0;255m"       # #bd00ff Synthwave Purple
YELLOW = "\033[38;2;252;238;10m"      # #fcee0a Cyberpunk Yellow
GREEN = "\033[38;2;0;255;159m"        # #00ff9f Matrix/Neon Mint
RED = "\033[38;2;255;42;109m"         # #ff2a6d Alert Crimson
GRAY = "\033[38;2;110;120;145m"       # #6e7891 Muted Slate
WHITE = "\033[38;2;230;245;255m"      # #e6f5ff Hologram White

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
BOX_INNER_WIDTH = 86
OS_NAME = platform.system()

COMMON_PORTS: Dict[int, str] = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPCBIND",
    135: "MSRPC",
    139: "NETBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "ORACLE",
    2049: "NFS",
    2375: "DOCKER",
    3000: "DEV-HTTP",
    3306: "MYSQL",
    3389: "RDP",
    4200: "ANGULAR",
    5000: "FLASK/API",
    5173: "VITE-DEV",
    5432: "POSTGRES",
    5601: "KIBANA",
    5900: "VNC",
    6379: "REDIS",
    6443: "K8S-API",
    8000: "HTTP-ALT",
    8080: "HTTP-PROXY",
    8443: "HTTPS-ALT",
    8888: "JUPYTER",
    9000: "SONAR/PORT",
    9090: "PROMETHEUS",
    9200: "ELASTIC",
    11434: "OLLAMA",
    27017: "MONGODB",
}


def visible_len(text: str) -> int:
    """Terminal display width: strips ANSI codes and counts wide glyphs (e.g. ⚡) as 2 columns."""
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        for ch in ANSI_RE.sub("", text)
    )


def box_row(content: str) -> str:
    vlen = visible_len(content)
    pad = max(0, BOX_INNER_WIDTH - vlen)
    return f"{MAGENTA}║{RESET}{content}{' ' * pad}{MAGENTA}║{RESET}"


def print_header(title: str, subtitle: str = ""):
    print(f"\n{MAGENTA}╔{'═' * BOX_INNER_WIDTH}╗{RESET}")
    print(box_row(f" {CYAN}{BOLD}⚡ {title}{RESET}"))
    if subtitle:
        print(box_row(f" {GRAY}{subtitle}{RESET}"))
    print(f"{MAGENTA}╚{'═' * BOX_INNER_WIDTH}╝{RESET}")


def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    freq: Dict[str, int] = {}
    for ch in data:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ============================================================================
# HELPER: CROSS-PLATFORM PORT -> PID / PROCESS / THREAD MAPPER
# ============================================================================
def get_process_details(pid: int) -> Tuple[str, int, str]:
    """Return (proc_name, thread_count, cmdline) for a given PID across Linux/macOS/Windows."""
    name = f"pid-{pid}"
    threads = 1
    cmdline = ""

    if OS_NAME == "Linux":
        try:
            with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
                for ln in f:
                    if ln.startswith("Name:"):
                        name = ln.split(":", 1)[1].strip()
                    elif ln.startswith("Threads:"):
                        threads = int(ln.split(":", 1)[1].strip())
        except Exception:
            pass
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                raw = f.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
                if raw:
                    cmdline = raw
        except Exception:
            pass
    elif OS_NAME == "Darwin":
        try:
            out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "comm=,args="],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.0,
            ).strip()
            if out:
                parts = out.split(None, 1)
                name = os.path.basename(parts[0])
                cmdline = parts[1] if len(parts) > 1 else parts[0]
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "process", "where", f"ProcessId={pid}", "get", "Name,ThreadCount,CommandLine", "/format:csv"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1.5,
            )
            for ln in out.splitlines():
                if f",{pid}" in ln or ln.strip().endswith(str(pid)):
                    cols = ln.strip().split(",")
                    if len(cols) >= 4:
                        cmdline = cols[1]
                        name = cols[2]
                        threads = int(cols[3]) if cols[3].isdigit() else 1
        except Exception:
            pass

    return name, threads, cmdline or name


def find_pids_by_port(port: int) -> List[int]:
    """Find PIDs listening on or using a local TCP/UDP port across Linux, macOS, and Windows."""
    pids = set()

    # 1. Try lsof (works on macOS and Linux)
    if shutil.which("lsof"):
        try:
            out = subprocess.check_output(
                ["lsof", "-nP", f"-i:{port}", "-t"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            for ln in out.splitlines():
                if ln.strip().isdigit():
                    pids.add(int(ln.strip()))
        except Exception:
            pass

    # 2. Try ss -tulpn on Linux
    if not pids and OS_NAME == "Linux" and shutil.which("ss"):
        try:
            out = subprocess.check_output(
                ["ss", "-tulpn", f"sport = :{port}"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            for m in re.finditer(r"pid=(\d+)", out):
                pids.add(int(m.group(1)))
        except Exception:
            pass

    # 3. Try fuser on Linux
    if not pids and OS_NAME == "Linux" and shutil.which("fuser"):
        try:
            out = subprocess.check_output(
                ["fuser", f"{port}/tcp"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            for tok in out.split():
                if tok.strip().isdigit():
                    pids.add(int(tok.strip()))
        except Exception:
            pass

    # 4. Try netstat -ano on Windows
    if not pids and OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["netstat", "-ano"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.5,
            )
            for ln in out.splitlines():
                if f":{port} " in ln and ("LISTENING" in ln or "ESTABLISHED" in ln):
                    parts = ln.split()
                    if parts and parts[-1].isdigit():
                        pids.add(int(parts[-1]))
        except Exception:
            pass

    # 5. Fallback: scan /proc/<pid>/cmdline for explicit port arguments (e.g., --port 8000, :8000, 8000)
    if not pids and OS_NAME == "Linux":
        port_pat = re.compile(rf"(?:--port[=\s]+|:[0]*|\b){port}\b")
        try:
            for entry in os.scandir("/proc"):
                if not entry.name.isdigit():
                    continue
                pid = int(entry.name)
                if pid == os.getpid():
                    continue
                try:
                    with open(f"/proc/{entry.name}/cmdline", "rb") as f:
                        cmd = f.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
                    if "cyber_tools.py" in cmd:
                        continue
                    if port_pat.search(cmd):
                        pids.add(pid)
                except Exception:
                    continue
        except Exception:
            pass

    return sorted(pids)


# ============================================================================
# 1. MULTI-THREADED PORT, PROCESS & BANNER SCANNER
# ============================================================================
PORT_SPEC_HINT = "use e.g. 22,80,443 or 1-1024"


def parse_port_spec(spec: str) -> List[int]:
    if not spec or spec.lower() == "common":
        return sorted(COMMON_PORTS.keys())
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"Invalid port spec '{spec}' — {PORT_SPEC_HINT}")
        if "-" in part:
            start_s, end_s = (edge.strip() for edge in part.split("-", 1))
            if not (start_s.isdigit() and end_s.isdigit()):
                raise ValueError(f"Invalid port spec '{part}' — {PORT_SPEC_HINT}")
            start, end = int(start_s), int(end_s)
            if start > end:
                start, end = end, start
            start, end = max(1, start), min(65535, end)
            if start > end:
                raise ValueError(f"Port range '{part}' is outside 1-65535 — {PORT_SPEC_HINT}")
            ports.update(range(start, end + 1))
        elif part.isdigit():
            p = int(part)
            if not 1 <= p <= 65535:
                raise ValueError(f"Port '{part}' is outside 1-65535 — {PORT_SPEC_HINT}")
            ports.add(p)
        else:
            raise ValueError(f"Invalid port spec '{part}' — {PORT_SPEC_HINT}")
    return sorted(ports)


def probe_port(host: str, port: int, timeout: float = 0.4) -> Tuple[int, bool, str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) != 0:
                return port, False, ""
            banner = ""
            try:
                if port in (80, 3000, 5000, 5173, 8000, 8080, 8888):
                    s.sendall(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
                s.settimeout(0.25)
                raw = s.recv(128)
                if raw:
                    first_line = raw.decode("utf-8", errors="ignore").splitlines()[0].strip()
                    banner = re.sub(r"[^\x20-\x7e]", "", first_line)[:36]
            except Exception:
                pass
            return port, True, banner
    except Exception:
        return port, False, ""


def tool_port_scanner(target: str, port_spec: str = "common", timeout: float = 0.4):
    print_header(
        "CYBER-PORT // MULTI-THREADED TCP, PROCESS & BANNER SCANNER",
        f"Target Node: {target}  │  Port Spec: {port_spec}",
    )
    try:
        ip = socket.gethostbyname(target)
    except Exception as e:
        print(f"  {RED}✖ DNS resolution failed for '{target}': {e}{RESET}\n")
        return

    is_local = ip.startswith("127.") or ip == "0.0.0.0" or target in ("localhost", socket.gethostname())
    try:
        ports = parse_port_spec(port_spec)
    except ValueError as e:
        print(f"  {RED}✖ {e}{RESET}\n")
        return
    print(f"\n  {GRAY}▸ RESOLVED IP   :{RESET} {CYAN}{BOLD}{ip}{RESET}")
    print(f"  {GRAY}▸ PORTS QUEUED  :{RESET} {WHITE}{len(ports)} ports{RESET}\n")

    t0 = time.time()
    open_ports: List[Tuple[int, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        futures = [executor.submit(probe_port, ip, p, timeout) for p in ports]
        for fut in concurrent.futures.as_completed(futures):
            port, is_open, banner = fut.result()
            if is_open:
                open_ports.append((port, banner))

    open_ports.sort(key=lambda x: x[0])
    elapsed = time.time() - t0

    if not open_ports:
        print(f"  {YELLOW}○ No open TCP ports detected among {len(ports)} scanned ports ({elapsed:.2f}s).{RESET}\n")
        return

    print(
        f"  {MAGENTA}{'PORT':<8} {'STATE':<10} {'SERVICE':<12} "
        f"{'PID / PROCESS (THREADS)':<28} {'BANNER / FINGERPRINT'}{RESET}"
    )
    print(f"  {GRAY}{'─' * 82}{RESET}")
    for port, banner in open_ports:
        svc = COMMON_PORTS.get(port, "CUSTOM")
        proc_info = "Remote Host"
        if is_local:
            pids = find_pids_by_port(port)
            if pids:
                pname, pthreads, _ = get_process_details(pids[0])
                proc_info = f"PID {pids[0]} ({pname}, {pthreads}T)"
            else:
                proc_info = "System / Protected PID"
        banner_disp = banner if banner else "—"
        print(
            f"  {CYAN}{BOLD}{port:<8}{RESET} "
            f"{GREEN}{BOLD}{'● OPEN':<10}{RESET} "
            f"{YELLOW}{svc:<12}{RESET} "
            f"{PURPLE}{proc_info:<28}{RESET} "
            f"{WHITE}{banner_disp}{RESET}"
        )

    print(
        f"\n  {GREEN}✔ SCAN COMPLETE:{RESET} {WHITE}{len(open_ports)} open port(s) found "
        f"out of {len(ports)} scanned in {CYAN}{elapsed:.2f}s{RESET}."
    )
    if is_local:
        print(f"  {GRAY}Tip: Run {CYAN}cyber-kill <PORT>{GRAY} to terminate any stuck local port job.{RESET}\n")
    else:
        print()


# ============================================================================
# 2. KILL PORT JOB (TERMINATE PROCESS OCCUPYING A PORT)
# ============================================================================
def tool_kill_port(port: int, force: bool = False, timeout: float = 5.0):
    print_header(
        "CYBER-KILL // PORT JOB & PROCESS TERMINATION ENGINE",
        f"Target Port: TCP/UDP :{port}  │  Signal Mode: {'SIGKILL (FORCE)' if force else f'SIGTERM / GRACEFUL (timeout {timeout}s)'}",
    )

    pids = find_pids_by_port(port)
    if not pids:
        # Check if port is actually open on localhost
        _, is_open, _ = probe_port("127.0.0.1", port, timeout=0.2)
        if is_open:
            print(
                f"\n  {YELLOW}⚠ Port {port} is open, but the owning process belongs to root/another user.{RESET}"
            )
            print(f"  {GRAY}Try running with elevated privileges: {CYAN}sudo python3 cyber_tools.py --kill-port {port}{RESET}\n")
        else:
            print(f"\n  {GREEN}✔ Port {port} is already free (no active process listening on :{port}).{RESET}\n")
        return

    print(f"\n  {YELLOW}⚡ FOUND {len(pids)} PROCESS JOB(S) BOUND TO PORT {port}:{RESET}\n")
    for pid in pids:
        name, threads, cmdline = get_process_details(pid)
        print(f"  {CYAN}▸ PID          :{RESET} {WHITE}{BOLD}{pid}{RESET}")
        print(f"  {CYAN}▸ PROCESS NAME :{RESET} {GREEN}{BOLD}{name}{RESET}")
        print(f"  {CYAN}▸ LIVE THREADS :{RESET} {PURPLE}{threads} thread(s){RESET}")
        print(f"  {CYAN}▸ COMMAND LINE :{RESET} {GRAY}{cmdline[:68]}{RESET}\n")

        try:
            if OS_NAME == "Windows":
                cmd = ["taskkill", "/PID", str(pid)]
                if force:
                    cmd.append("/F")
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  {GREEN}{BOLD}✔ TERMINATED:{RESET} {WHITE}PID {pid} ({name}) freed from port {port}.{RESET}\n")
            else:
                if force:
                    os.kill(pid, signal.SIGKILL)
                    print(f"  {GREEN}{BOLD}✔ TERMINATED:{RESET} {WHITE}PID {pid} ({name}) freed from port {port}.{RESET}\n")
                else:
                    os.kill(pid, signal.SIGTERM)
                    deadline = time.time() + timeout
                    terminated = False
                    while time.time() < deadline:
                        try:
                            os.kill(pid, 0)  # probe if still alive
                            time.sleep(0.1)
                        except OSError:
                            terminated = True
                            break
                    if terminated:
                        print(f"  {GREEN}{BOLD}✔ TERMINATED:{RESET} {WHITE}PID {pid} ({name}) freed from port {port}.{RESET}\n")
                    else:
                        print(f"  {YELLOW}⚠ STILL RUNNING:{RESET} PID {pid} ({name}) did not exit within {timeout}s. Rerun with {CYAN}--force{RESET}.\n")
        except PermissionError:
            print(f"  {RED}✖ PERMISSION DENIED:{RESET} Cannot kill PID {pid} ({name}). Try with {CYAN}sudo{RESET}.\n")
        except Exception as e:
            print(f"  {RED}✖ FAILED TO TERMINATE PID {pid}: {e}{RESET}\n")


# ============================================================================
# 3. JOB SCAN, LIVE THREAD COUNTS & SCHEDULED JOBS INVENTORY
# ============================================================================
def tool_jobs_and_threads():
    print_header(
        "CYBER-JOBS // LIVE THREAD TELEMETRY, PROCESS JOBS & SCHEDULER AUDIT",
        f"Platform: {OS_NAME} ({platform.release()})  │  CPU Cores: {os.cpu_count() or 1}",
    )

    # 1. Enumerate all processes & their live thread counts
    procs: List[Tuple[int, str, int, float, str]] = []  # (pid, name, threads, mem_mb, state)
    total_threads = 0

    if OS_NAME == "Linux":
        try:
            for entry in os.scandir("/proc"):
                if not entry.name.isdigit():
                    continue
                pid = int(entry.name)
                name = ""
                threads = 1
                rss_kb = 0
                state = "R"
                try:
                    with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
                        for ln in f:
                            if ln.startswith("Name:"):
                                name = ln.split(":", 1)[1].strip()
                            elif ln.startswith("State:"):
                                state = ln.split(":", 1)[1].strip().split()[0]
                            elif ln.startswith("Threads:"):
                                threads = int(ln.split(":", 1)[1].strip())
                            elif ln.startswith("VmRSS:"):
                                rss_kb = int(ln.split(":", 1)[1].strip().split()[0])
                    total_threads += threads
                    procs.append((pid, name, threads, rss_kb / 1024.0, state))
                except Exception:
                    continue
        except Exception:
            pass
    elif OS_NAME == "Darwin":
        try:
            out = subprocess.check_output(
                ["ps", "-axo", "pid=,rss=,state=,comm="],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
            )
            for ln in out.splitlines():
                parts = ln.strip().split(None, 3)
                if len(parts) >= 4 and parts[0].isdigit():
                    pid = int(parts[0])
                    rss_mb = int(parts[1]) / 1024.0 if parts[1].isdigit() else 0.0
                    state = parts[2]
                    name = os.path.basename(parts[3])
                    procs.append((pid, name, 1, rss_mb, state))
                    total_threads += 1
        except Exception:
            pass
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "process", "get", "ProcessId,Name,ThreadCount,WorkingSetSize", "/format:csv"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.5,
            )
            for ln in out.splitlines():
                cols = ln.strip().split(",")
                if len(cols) >= 5 and cols[2].isdigit():
                    name = cols[1]
                    pid = int(cols[2])
                    threads = int(cols[3]) if cols[3].isdigit() else 1
                    mem_mb = int(cols[4]) / (1024 * 1024) if cols[4].isdigit() else 0.0
                    total_threads += threads
                    procs.append((pid, name, threads, mem_mb, "RUNNING"))
        except Exception:
            pass

    print(f"\n  {PURPLE}{BOLD}[1] SYSTEM-WIDE LIVE THREAD & PROCESS TELEMETRY{RESET}")
    print(f"  {GRAY}▸ Total Active Processes :{RESET} {WHITE}{BOLD}{len(procs)}{RESET}")
    print(f"  {GRAY}▸ Total Live Threads     :{RESET} {CYAN}{BOLD}{total_threads} live threads{RESET}")
    avg_t = (total_threads / len(procs)) if procs else 0.0
    print(f"  {GRAY}▸ Avg Threads / Process  :{RESET} {GREEN}{avg_t:.1f} threads/proc{RESET}\n")

    # Sort by thread count descending, then memory descending
    procs.sort(key=lambda x: (x[2], x[3]), reverse=True)
    print(f"  {MAGENTA}{'PID':<10} {'PROCESS NAME':<26} {'LIVE THREADS':<16} {'MEMORY (MB)':<15} {'STATE'}{RESET}")
    print(f"  {GRAY}{'─' * 78}{RESET}")
    for pid, name, threads, mem_mb, state in procs[:12]:
        t_color = YELLOW if threads >= 25 else (CYAN if threads >= 8 else WHITE)
        print(
            f"  {CYAN}{pid:<10}{RESET} "
            f"{WHITE}{BOLD}{name[:24]:<26}{RESET} "
            f"{t_color}{BOLD}{f'{threads} threads':<16}{RESET} "
            f"{GREEN}{f'{mem_mb:7.1f} MB':<15}{RESET} "
            f"{PURPLE}{state}{RESET}"
        )

    # 2. Scheduled Jobs Scan (Crontab, /etc/cron*, Systemd Timers, Launchd, Windows Task Scheduler, Active Daemons)
    print(f"\n  {PURPLE}{BOLD}[2] SCHEDULED JOBS, DAEMONS & SYSTEM TIMERS INVENTORY{RESET}")
    user_cron_jobs: List[str] = []
    sys_cron_count = 0
    systemd_timers_count = 0
    win_tasks_count = 0
    daemon_jobs: List[str] = []

    if OS_NAME in ("Linux", "Darwin"):
        try:
            out = subprocess.check_output(
                ["crontab", "-l"], stderr=subprocess.DEVNULL, text=True, timeout=1.5
            )
            user_cron_jobs = [
                ln.strip() for ln in out.splitlines() if ln.strip() and not ln.strip().startswith("#")
            ]
        except Exception:
            pass

        for cdir in ("/etc/cron.d", "/etc/cron.daily", "/etc/cron.hourly", "/etc/cron.weekly", "/etc/cron.monthly"):
            if os.path.isdir(cdir):
                try:
                    sys_cron_count += len([f for f in os.listdir(cdir) if not f.startswith(".")])
                except Exception:
                    pass

        if OS_NAME == "Linux" and shutil.which("systemctl"):
            try:
                out = subprocess.check_output(
                    ["systemctl", "list-timers", "--all", "--no-legend", "--no-pager"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=2.0,
                )
                systemd_timers_count = len([ln for ln in out.splitlines() if ln.strip()])
            except Exception:
                pass

        for pid, name, threads, _, _ in procs:
            if name in ("cron", "crond", "atd", "anacron", "systemd-timesyn", "ollama", "dockerd", "containerd", "sshd", "redis-server", "postgres"):
                daemon_jobs.append(f"{name} (PID {pid}, {threads}T)")
    elif OS_NAME == "Windows":
        try:
            out = subprocess.check_output(
                ["schtasks", "/query", "/fo", "csv", "/nh"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.5,
            )
            win_tasks_count = len([ln for ln in out.splitlines() if ln.strip()])
        except Exception:
            pass

    total_scheduled = len(user_cron_jobs) + sys_cron_count + systemd_timers_count + win_tasks_count + len(daemon_jobs)
    print(f"  {GRAY}▸ User Crontab Jobs      :{RESET} {CYAN}{BOLD}{len(user_cron_jobs)}{RESET}")
    if OS_NAME in ("Linux", "Darwin"):
        print(f"  {GRAY}▸ System Cron Scripts    :{RESET} {YELLOW}{BOLD}{sys_cron_count}{RESET} (/etc/cron.*)")
        print(f"  {GRAY}▸ Active Service Daemons :{RESET} {GREEN}{BOLD}{len(daemon_jobs)}{RESET} ({', '.join(daemon_jobs[:5]) or 'None'})")
    if OS_NAME == "Linux":
        print(f"  {GRAY}▸ Systemd Active Timers  :{RESET} {GREEN}{BOLD}{systemd_timers_count}{RESET}")
    if OS_NAME == "Windows":
        print(f"  {GRAY}▸ Windows Scheduled Tasks:{RESET} {GREEN}{BOLD}{win_tasks_count}{RESET}")
    print(f"  {GRAY}▸ TOTAL SCHEDULED / BG   :{RESET} {MAGENTA}{BOLD}{total_scheduled} active scheduled/daemon job(s){RESET}")

    if user_cron_jobs:
        print(f"\n  {CYAN}Active User Crontab Entries:{RESET}")
        for job in user_cron_jobs[:8]:
            print(f"    {GREEN}• {job[:76]}{RESET}")
    print()


# ============================================================================
# 4. DOMAIN / IP RECON, DNS & WHOIS / RDAP TELEMETRY
# ============================================================================
def tool_recon(target: str):
    if "://" in target:
        target = urllib.parse.urlparse(target).hostname or target
    target = target.strip("/")

    print_header(
        "CYBER-RECON // DNS, REVERSE-IP & RDAP/WHOIS INTELLIGENCE",
        f"Target Entity: {target}",
    )

    ipv4_list, ipv6_list = set(), set()
    try:
        for res in socket.getaddrinfo(target, None):
            fam, _, _, _, sockaddr = res
            if fam == socket.AF_INET:
                ipv4_list.add(sockaddr[0])
            elif fam == socket.AF_INET6:
                ipv6_list.add(sockaddr[0])
    except Exception as e:
        print(f"\n  {RED}✖ Resolution error: {e}{RESET}")

    print(f"\n  {PURPLE}{BOLD}[1] NETWORK ADDRESS RESOLUTION{RESET}")
    print(f"  {GRAY}▸ IPv4 Addresses :{RESET} {CYAN}{', '.join(sorted(ipv4_list)) or 'None'}{RESET}")
    print(f"  {GRAY}▸ IPv6 Addresses :{RESET} {BLUE}{', '.join(sorted(ipv6_list)) or 'None'}{RESET}")

    primary_ip = sorted(ipv4_list)[0] if ipv4_list else None
    if primary_ip:
        try:
            rev_host, _, _ = socket.gethostbyaddr(primary_ip)
        except Exception:
            rev_host = "No PTR record"
        print(f"  {GRAY}▸ Reverse PTR    :{RESET} {WHITE}{rev_host}{RESET}")

    if primary_ip and not primary_ip.startswith(("127.", "10.", "192.168.")):
        print(f"\n  {PURPLE}{BOLD}[2] ASN & GEOLOCATION TELEMETRY{RESET}")
        try:
            req = urllib.request.Request(
                f"http://ip-api.com/json/{primary_ip}?fields=status,country,regionName,city,isp,org,as",
                headers={"User-Agent": "CyberOS-Recon/4.5"},
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if data.get("status") == "success":
                    print(f"  {GRAY}▸ ASN / ISP      :{RESET} {YELLOW}{data.get('as', '—')} ({data.get('isp', '—')}){RESET}")
                    print(f"  {GRAY}▸ Organization   :{RESET} {WHITE}{data.get('org', '—')}{RESET}")
                    print(
                        f"  {GRAY}▸ Geo Location   :{RESET} {GREEN}{data.get('city', '—')}, "
                        f"{data.get('regionName', '—')}, {data.get('country', '—')}{RESET}"
                    )
        except Exception:
            print(f"  {GRAY}▸ External ASN lookup skipped or offline.{RESET}")

    if shutil.which("dig"):
        print(f"\n  {PURPLE}{BOLD}[3] DNS RECORD MATRIX (MX / NS / TXT){RESET}")
        for rtype in ("NS", "MX", "TXT"):
            try:
                out = subprocess.check_output(
                    ["dig", "+short", target, rtype],
                    stderr=subprocess.DEVNULL,
                    timeout=3.0,
                    text=True,
                ).strip()
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()][:3]
                val = " | ".join(lines) if lines else "—"
                print(f"  {GRAY}▸ {rtype:<6} Records :{RESET} {WHITE}{val[:70]}{RESET}")
            except Exception:
                pass
    print()


# ============================================================================
# 5. SSL/TLS CERTIFICATE & CIPHER INSPECTOR
# ============================================================================
def tool_ssl_inspector(target: str):
    if "://" in target:
        parsed = urllib.parse.urlparse(target)
        host = parsed.hostname or target
        port = parsed.port or 443
    elif ":" in target:
        host, port_s = target.rsplit(":", 1)
        port = int(port_s)
    else:
        host, port = target, 443

    print_header(
        "CYBER-SSL // TLS HANDSHAKE, CIPHER & X.509 CERTIFICATE AUDITOR",
        f"Target Endpoint: {host}:{port}",
    )

    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=4.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
    except Exception as e:
        print(f"\n  {RED}✖ TLS Handshake Error: {e}{RESET}\n")
        return

    subject = dict(x[0] for x in cert.get("subject", ()))
    issuer = dict(x[0] for x in cert.get("issuer", ()))
    not_before = cert.get("notBefore", "")
    not_after = cert.get("notAfter", "")

    days_left_str = "Unknown"
    if not_after:
        try:
            exp_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=datetime.timezone.utc
            )
            days_left = (exp_dt - datetime.datetime.now(datetime.timezone.utc)).days
            color = GREEN if days_left > 30 else (YELLOW if days_left > 7 else RED)
            days_left_str = f"{color}{BOLD}{days_left} days remaining{RESET}"
        except Exception:
            pass

    sans = [val for typ, val in cert.get("subjectAltName", ()) if typ == "DNS"]

    print(f"\n  {GRAY}▸ TLS PROTOCOL   :{RESET} {CYAN}{BOLD}{version}{RESET}")
    if cipher:
        print(f"  {GRAY}▸ CIPHER SUITE   :{RESET} {GREEN}{cipher[0]} ({cipher[2]}-bit){RESET}")
    print(f"  {GRAY}▸ COMMON NAME    :{RESET} {WHITE}{BOLD}{subject.get('commonName', '—')}{RESET}")
    print(f"  {GRAY}▸ ISSUER CA      :{RESET} {YELLOW}{issuer.get('organizationName', '—')} ({issuer.get('commonName', '—')}){RESET}")
    print(f"  {GRAY}▸ VALID FROM     :{RESET} {WHITE}{not_before}{RESET}")
    print(f"  {GRAY}▸ VALID UNTIL    :{RESET} {WHITE}{not_after}{RESET} ({days_left_str})")
    print(f"  {GRAY}▸ SAN DOMAINS    :{RESET} {CYAN}{', '.join(sans[:6]) or '—'}{RESET}\n")


# ============================================================================
# 6. HTTP SECURITY HEADER & SERVER AUDITOR
# ============================================================================
def tool_http_headers(url: str):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print_header(
        "CYBER-HEADERS // HTTP SECURITY HEADER & FINGERPRINT AUDITOR",
        f"Target URL: {url}",
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "CyberOS-SecAudit/4.5"})
        with urllib.request.urlopen(req, timeout=5.0, context=ctx) as resp:
            status = resp.status
            headers = {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        status = e.code
        headers = {k.lower(): v for k, v in e.headers.items()}
    except Exception as e:
        print(f"\n  {RED}✖ HTTP Request failed: {e}{RESET}\n")
        return

    print(f"\n  {GRAY}▸ HTTP STATUS    :{RESET} {GREEN if status < 400 else YELLOW}{BOLD}HTTP {status}{RESET}")
    print(f"  {GRAY}▸ SERVER BANNER  :{RESET} {CYAN}{headers.get('server', 'Hidden / Hardened')}{RESET}")
    print(f"  {GRAY}▸ X-POWERED-BY   :{RESET} {YELLOW}{headers.get('x-powered-by', 'None (Good)')}{RESET}\n")

    sec_checks = [
        ("strict-transport-security", "HSTS (Strict-Transport-Security)", 20),
        ("content-security-policy", "CSP (Content-Security-Policy)", 25),
        ("x-frame-options", "X-Frame-Options (Clickjacking)", 15),
        ("x-content-type-options", "X-Content-Type-Options (MIME Sniff)", 15),
        ("referrer-policy", "Referrer-Policy", 15),
        ("permissions-policy", "Permissions-Policy", 10),
    ]

    score = 0
    print(f"  {MAGENTA}{'SECURITY HEADER':<38} {'STATUS':<14} {'VALUE'}{RESET}")
    print(f"  {GRAY}{'─' * 78}{RESET}")
    for key, label, weight in sec_checks:
        val = headers.get(key)
        if val:
            score += weight
            short_val = val[:32] + ("..." if len(val) > 32 else "")
            print(f"  {WHITE}{label:<38}{RESET} {GREEN}{BOLD}{'✔ PRESENT':<14}{RESET} {CYAN}{short_val}{RESET}")
        else:
            print(f"  {WHITE}{label:<38}{RESET} {RED}{'✖ MISSING':<14}{RESET} {GRAY}Not configured{RESET}")

    grade = "A+" if score >= 90 else ("A" if score >= 75 else ("B" if score >= 60 else ("C" if score >= 40 else "F")))
    grade_color = GREEN if grade.startswith("A") else (YELLOW if grade in ("B", "C") else RED)
    print(f"\n  {PURPLE}◈ SECURITY POSTURE SCORE :{RESET} {grade_color}{BOLD}{score}/100 (GRADE: {grade}){RESET}\n")


# ============================================================================
# 7. ACTIVE NETWORK CONNECTIONS & SOCKET MONITOR
# ============================================================================
def _decode_proc_ip(hex_ip: str, hex_port: str) -> str:
    port = int(hex_port, 16)
    if len(hex_ip) == 8:
        ip_int = int(hex_ip, 16)
        ip_str = socket.inet_ntoa(ip_int.to_bytes(4, "little"))
        return f"{ip_str}:{port}"
    return f"[IPv6]:{port}"


def tool_connections():
    print_header(
        "CYBER-CONN // ACTIVE SOCKET & NETWORK TELEMETRY MONITOR",
        "Inspecting local listening daemons & established peer sessions",
    )

    TCP_STATES = {
        "01": f"{GREEN}ESTABLISHED{RESET}",
        "02": f"{YELLOW}SYN_SENT{RESET}",
        "06": f"{GRAY}TIME_WAIT{RESET}",
        "0A": f"{CYAN}{BOLD}LISTEN{RESET}",
    }

    rows = []
    if OS_NAME == "Linux":
        try:
            with open("/proc/net/tcp", "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]
            for ln in lines[:35]:
                parts = ln.split()
                if len(parts) < 4:
                    continue
                local = _decode_proc_ip(*parts[1].split(":"))
                remote = _decode_proc_ip(*parts[2].split(":"))
                state_code = parts[3]
                state_str = TCP_STATES.get(state_code, f"{PURPLE}STATE_{state_code}{RESET}")
                rows.append((local, remote, state_str))
        except Exception:
            pass

    if not rows:
        for port, svc in sorted(COMMON_PORTS.items()):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.05)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    pids = find_pids_by_port(port)
                    pid_tag = f"PID:{pids[0]}" if pids else svc
                    rows.append((f"127.0.0.1:{port}", f"0.0.0.0:* ({pid_tag})", f"{CYAN}{BOLD}LISTEN{RESET}"))

    print(f"\n  {MAGENTA}{'LOCAL ADDRESS':<26} {'REMOTE PEER / PROCESS':<28} {'SOCKET STATE'}{RESET}")
    print(f"  {GRAY}{'─' * 74}{RESET}")
    for local, remote, state_str in rows[:25]:
        print(f"  {WHITE}{local:<26}{RESET} {CYAN}{remote:<28}{RESET} {state_str}")
    print(f"\n  {GRAY}Total active TCP socket entries: {WHITE}{len(rows)}{RESET}\n")


# ============================================================================
# 8. CRYPTO HASHER & UNIVERSAL DECODER (BASE64 / HEX / JWT)
# ============================================================================
def tool_crypto_hash(target: str):
    is_file = os.path.isfile(target)
    print_header(
        "CYBER-HASH // MULTI-ALGORITHM CRYPTOGRAPHIC DIGEST ENGINE",
        f"Source ({'FILE' if is_file else 'STRING'}): {target}",
    )

    if is_file:
        with open(target, "rb") as f:
            data = f.read()
    else:
        data = target.encode("utf-8")

    algos = [
        ("MD5", hashlib.md5(data).hexdigest()),
        ("SHA-1", hashlib.sha1(data).hexdigest()),
        ("SHA-256", hashlib.sha256(data).hexdigest()),
        ("SHA-384", hashlib.sha384(data).hexdigest()),
        ("SHA-512", hashlib.sha512(data).hexdigest()),
        ("BLAKE2b-256", hashlib.blake2b(data, digest_size=32).hexdigest()),
    ]

    print(f"\n  {GRAY}▸ PAYLOAD SIZE   :{RESET} {WHITE}{len(data)} bytes{RESET}\n")
    for name, digest in algos:
        print(f"  {CYAN}{BOLD}{name:<13}{RESET} {GRAY}│{RESET} {GREEN}{digest}{RESET}")
    print()


def tool_decode(payload: str):
    print_header(
        "CYBER-DECODE // UNIVERSAL PAYLOAD & JWT TOKEN INSPECTOR",
        f"Input Length: {len(payload)} chars",
    )
    print()

    parts = payload.strip().split(".")
    if len(parts) == 3 and all(len(p) >= 4 for p in parts[:2]):
        print(f"  {YELLOW}{BOLD}⚡ DETECTED JSON WEB TOKEN (JWT){RESET}")
        for idx, label in enumerate(("HEADER", "PAYLOAD")):
            seg = parts[idx]
            pad = "=" * ((4 - len(seg) % 4) % 4)
            try:
                raw = base64.urlsafe_b64decode(seg + pad).decode("utf-8", errors="replace")
                parsed = json.loads(raw)
                pretty = json.dumps(parsed, indent=2)
                print(f"\n  {CYAN}{BOLD}▸ JWT {label}:{RESET}")
                for line in pretty.splitlines():
                    print(f"    {GREEN}{line}{RESET}")
                if label == "PAYLOAD" and "exp" in parsed:
                    exp_dt = datetime.datetime.fromtimestamp(int(parsed["exp"]), datetime.timezone.utc)
                    now_dt = datetime.datetime.now(datetime.timezone.utc)
                    status = f"{GREEN}VALID{RESET}" if exp_dt > now_dt else f"{RED}EXPIRED{RESET}"
                    print(f"    {YELLOW}⌚ Expiration (UTC): {exp_dt.isoformat()} ({status}){RESET}")
            except Exception as e:
                print(f"  {RED}✖ Failed to decode JWT {label}: {e}{RESET}")
        print(f"\n  {PURPLE}▸ SIGNATURE (Base64URL):{RESET} {GRAY}{parts[2]}{RESET}\n")
        return

    try:
        padded = payload.strip() + "=" * ((4 - len(payload.strip()) % 4) % 4)
        b64_out = base64.b64decode(padded, validate=False).decode("utf-8", errors="ignore")
        if b64_out and any(c in string.printable for c in b64_out):
            print(f"  {CYAN}{BOLD}▸ BASE64 DECODED :{RESET} {GREEN}{b64_out}{RESET}")
    except Exception:
        pass

    clean_hex = re.sub(r"^0x|\s+", "", payload.strip())
    if len(clean_hex) % 2 == 0 and all(c in string.hexdigits for c in clean_hex):
        try:
            hex_out = bytes.fromhex(clean_hex).decode("utf-8", errors="replace")
            print(f"  {MAGENTA}{BOLD}▸ HEX DECODED    :{RESET} {GREEN}{hex_out}{RESET}")
        except Exception:
            pass

    url_out = urllib.parse.unquote(payload)
    if url_out != payload:
        print(f"  {YELLOW}{BOLD}▸ URL DECODED    :{RESET} {GREEN}{url_out}{RESET}")

    b64_enc = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    hex_enc = payload.encode("utf-8").hex()
    print(f"\n  {GRAY}▸ AS BASE64 ENC  :{RESET} {WHITE}{b64_enc}{RESET}")
    print(f"  {GRAY}▸ AS HEX ENC     :{RESET} {WHITE}{hex_enc}{RESET}\n")


# ============================================================================
# 9. QUANTUM CSPRNG KEY & PASSWORD GENERATOR
# ============================================================================
def tool_keygen(length: int = 32):
    length = max(8, min(256, length))
    print_header(
        "CYBER-KEYGEN // CSPRNG HIGH-ENTROPY KEY & SECRET FORGE",
        f"Cryptographic Random Generator (Length: {length})",
    )

    alphabet_full = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    alphabet_alnum = string.ascii_letters + string.digits

    pw_complex = "".join(secrets.choice(alphabet_full) for _ in range(length))
    pw_alnum = "".join(secrets.choice(alphabet_alnum) for _ in range(length))
    api_token = f"cyber_live_{secrets.token_urlsafe(24)}"
    hex_key = secrets.token_hex(32)
    b64_key = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
    uuid_val = str(uuid.uuid4())

    ent_bits = shannon_entropy(pw_complex) * len(pw_complex)

    print(f"\n  {CYAN}{BOLD}▸ ULTRA PASSWORD  :{RESET} {GREEN}{BOLD}{pw_complex}{RESET}")
    print(f"  {CYAN}{BOLD}▸ ALPHANUMERIC    :{RESET} {WHITE}{pw_alnum}{RESET}")
    print(f"  {MAGENTA}{BOLD}▸ API BEARER KEY  :{RESET} {YELLOW}{api_token}{RESET}")
    print(f"  {BLUE}{BOLD}▸ AES-256 HEX KEY :{RESET} {CYAN}{hex_key}{RESET}")
    print(f"  {PURPLE}{BOLD}▸ BASE64 SECRET   :{RESET} {WHITE}{b64_key}{RESET}")
    print(f"  {GRAY}{BOLD}▸ UUIDv4 NODE ID  :{RESET} {GRAY}{uuid_val}{RESET}")
    print(f"\n  {YELLOW}⚡ ENTROPY RATING :{RESET} {GREEN}{BOLD}{ent_bits:.1f} bits{RESET} (Cryptographically Secure)\n")


# ============================================================================
# 10. FILE INTEGRITY MONITOR (FIM)
# ============================================================================
def tool_fim(directory: str, baseline_file: str = ".cyber_fim.json"):
    target_dir = os.path.abspath(directory)
    manifest_path = os.path.join(target_dir, baseline_file)
    print_header(
        "CYBER-FIM // SHA-256 FILE INTEGRITY & TAMPER DETECTOR",
        f"Target Directory: {target_dir}",
    )

    current_hashes: Dict[str, str] = {}
    skip_dirs = {".git", ".venv", "node_modules", "__pycache__"}

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname == baseline_file:
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, target_dir)
            try:
                if os.path.islink(fpath) or os.path.getsize(fpath) > 25 * 1024 * 1024:
                    continue
                with open(fpath, "rb") as f:
                    current_hashes[rel] = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                continue

    if not os.path.exists(manifest_path):
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "files": current_hashes,
                },
                f,
                indent=2,
            )
        print(
            f"\n  {GREEN}✔ CREATED NEW SHA-256 BASELINE:{RESET} {WHITE}{len(current_hashes)} files indexed "
            f"in {CYAN}{manifest_path}{RESET}"
        )
        print(f"  {GRAY}Run this command again anytime to verify file integrity against tampering.{RESET}\n")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        saved = json.load(f)
    old_hashes: Dict[str, str] = saved.get("files", {})

    modified = [k for k in current_hashes if k in old_hashes and current_hashes[k] != old_hashes[k]]
    added = [k for k in current_hashes if k not in old_hashes]
    deleted = [k for k in old_hashes if k not in current_hashes]

    print(f"\n  {GRAY}▸ Baseline Timestamp :{RESET} {CYAN}{saved.get('created_at', 'Unknown')}{RESET}")
    print(f"  {GRAY}▸ Files Verified     :{RESET} {WHITE}{len(current_hashes)}{RESET}\n")

    if not modified and not added and not deleted:
        print(f"  {GREEN}{BOLD}✔ INTEGRITY VERIFIED: Zero unauthorized modifications detected.{RESET}\n")
        return

    for k in modified:
        print(f"  {RED}{BOLD}⚠ MODIFIED :{RESET} {WHITE}{k}{RESET}")
    for k in added:
        print(f"  {YELLOW}{BOLD}✚ ADDED    :{RESET} {WHITE}{k}{RESET}")
    for k in deleted:
        print(f"  {MAGENTA}{BOLD}✖ DELETED  :{RESET} {WHITE}{k}{RESET}")
    print()


# ============================================================================
# 11. SYSTEM SECURITY & KERNEL FORENSICS AUDIT
# ============================================================================
def _read_sysctl(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        key = path.replace("/proc/sys/", "").replace("/", ".")
        try:
            return subprocess.check_output(
                ["sysctl", "-n", key], stderr=subprocess.DEVNULL, timeout=1.0, text=True
            ).strip()
        except Exception:
            return "N/A"


def tool_system_audit():
    print_header(
        "CYBER-AUDIT // KERNEL HARDENING, PERMISSIONS & HOST SECURITY SWEEP",
        f"Analyzing {OS_NAME} security controls & privilege boundaries",
    )

    checks = [
        (
            "ASLR (Address Space Layout Randomization)",
            "/proc/sys/kernel/randomize_va_space",
            "2",
            "Full memory randomization active",
        ),
        (
            "Kernel Pointer Restriction (kptr_restrict)",
            "/proc/sys/kernel/kptr_restrict",
            ("1", "2"),
            "Prevents kernel address leaks",
        ),
        (
            "DMESG Restriction (dmesg_restrict)",
            "/proc/sys/kernel/dmesg_restrict",
            "1",
            "Restricts unprivileged kernel log access",
        ),
        (
            "Ptrace Scope (Yama LSM)",
            "/proc/sys/kernel/yama/ptrace_scope",
            ("1", "2", "3"),
            "Blocks cross-process memory debugging",
        ),
        (
            "IPv4 SYN Cookies (DDoS Protection)",
            "/proc/sys/net/ipv4/tcp_syncookies",
            "1",
            "Mitigates TCP SYN flood attacks",
        ),
    ]

    print(f"\n  {PURPLE}{BOLD}[1] KERNEL & OS HARDENING TELEMETRY{RESET}")
    for name, path, expected, desc in checks:
        val = _read_sysctl(path)
        if val == "N/A":
            badge_raw = "🔒 SANDBOX/OS"
            badge = f"{CYAN}{BOLD}{badge_raw:<18}{RESET}"
        else:
            ok = (val in expected) if isinstance(expected, tuple) else (val == expected)
            badge_raw = f"✔ HARDENED ({val})" if ok else f"⚠ SUBOPTIMAL ({val})"
            color = f"{GREEN}{BOLD}" if ok else f"{YELLOW}{BOLD}"
            badge = f"{color}{badge_raw:<18}{RESET}"
        print(f"  {WHITE}{name:<44}{RESET} {badge} {GRAY}{desc}{RESET}")

    print(f"\n  {PURPLE}{BOLD}[2] CRITICAL FILE PERMISSION AUDIT{RESET}")
    crit_files = [
        ("/etc/passwd", 0o644),
        ("/etc/shadow", 0o640),
        ("/etc/ssh/sshd_config", 0o600),
    ]
    found_any = False
    for fpath, _ in crit_files:
        if os.path.exists(fpath):
            found_any = True
            mode = stat.S_IMODE(os.stat(fpath).st_mode)
            ok = (mode & 0o002) == 0
            print(
                f"  {WHITE}{fpath:<44}{RESET} "
                f"{GREEN if ok else RED}{'✔ SECURE' if ok else '✖ PERMISSIVE'} ({oct(mode)}){RESET}"
            )
    if not found_any:
        print(f"  {GRAY}▸ Non-POSIX filesystem ({OS_NAME}) — ACL permissions managed by OS.{RESET}")

    if os.path.isdir("/usr/bin"):
        print(f"\n  {PURPLE}{BOLD}[3] PRIVILEGED SUID BINARIES (/usr/bin sample){RESET}")
        suid_bins = []
        try:
            for entry in os.scandir("/usr/bin"):
                try:
                    st = entry.stat(follow_symlinks=False)
                    if st.st_mode & stat.S_ISUID:
                        suid_bins.append(entry.name)
                except Exception:
                    continue
        except Exception:
            pass
        print(
            f"  {GRAY}▸ Detected {WHITE}{len(suid_bins)}{GRAY} SUID binaries in /usr/bin: "
            f"{CYAN}{', '.join(sorted(suid_bins)[:10])}{RESET}\n"
        )
    else:
        print()


# ============================================================================
# 12. SOURCE CODE SECRET & CREDENTIAL LEAK SCANNER
# ============================================================================
SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")),
    ("GitHub Personal/App Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}")),
    ("OpenAI / AI API Key", re.compile(r"sk-[A-Za-z0-9\-_]{20,}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Slack Webhook / Token", re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,48}")),
    ("Generic Secret Assignment", re.compile(r"(?i)(?:api_key|secret_key|access_token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]")),
]


def tool_secret_scanner(target_dir: str = "."):
    abs_dir = os.path.abspath(target_dir)
    print_header(
        "CYBER-SECRETS // CREDENTIAL, API KEY & PRIVATE KEY LEAK SCANNER",
        f"Scanning Workspace: {abs_dir}",
    )

    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}
    findings = []
    files_scanned = 0

    for root, dirs, files in os.walk(abs_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname.endswith((".pyc", ".png", ".jpg", ".lock", ".whl", ".so")):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, abs_dir)
            try:
                if os.path.getsize(fpath) > 2 * 1024 * 1024:
                    continue
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    files_scanned += 1
                    for lineno, line in enumerate(f, 1):
                        for label, pat in SECRET_PATTERNS:
                            m = pat.search(line)
                            if m:
                                val = m.group(0)
                                masked = val[:8] + "..." + val[-4:] if len(val) > 14 else val[:6] + "***"
                                findings.append((rel, lineno, label, masked))
            except Exception:
                continue

    print(f"\n  {GRAY}▸ Files Scanned  :{RESET} {WHITE}{files_scanned}{RESET}")
    if not findings:
        print(f"  {GREEN}{BOLD}✔ ZERO EXPOSED SECRETS DETECTED.{RESET}\n")
        return

    print(f"  {YELLOW}⚠ POTENTIAL CREDENTIAL FINDINGS ({len(findings)}):{RESET}\n")
    for rel, lineno, label, masked in findings[:20]:
        print(f"  {RED}● {label:<28}{RESET} {CYAN}{rel}:{lineno:<5}{RESET} {GRAY}({masked}){RESET}")
    print()


# ============================================================================
# 13. CROSS-PLATFORM CYBER ARSENAL STATUS & NMAP WRAPPER
# ============================================================================
LINUX_CYBER_PACKAGES = [
    ("nmap", "Network Mapper & Port/OS Scanner", "apt/brew/winget install nmap"),
    ("whois", "Domain & IP ASN Registry Client", "apt/brew install whois"),
    ("dig", "DNS Interrogation Utility", "apt install dnsutils / brew install bind"),
    ("nc", "Netcat TCP/UDP Swiss Army Knife", "apt/brew install netcat"),
    ("tcpdump", "Raw Packet Analyzer & Sniffer", "apt/brew install tcpdump"),
    ("tshark", "Wireshark Terminal Packet Analyzer", "apt/brew/winget install wireshark"),
    ("curl", "HTTP/TLS Probe & Transfer Engine", "Built-in / apt/brew install curl"),
    ("openssl", "SSL/TLS & Cryptography Toolkit", "Built-in / apt/brew install openssl"),
    ("ss", "Kernel Socket Statistics Inspector", "iproute2 (Linux)"),
    ("ufw", "Uncomplicated Firewall Manager", "apt install ufw"),
]


def tool_arsenal_status():
    print_header(
        "CYBER-ARSENAL // CROSS-PLATFORM SECURITY BINARY TELEMETRY",
        f"Checking installed system security tools on {OS_NAME}",
    )
    print(f"\n  {MAGENTA}{'BINARY':<12} {'STATUS':<15} {'DESCRIPTION':<36} {'LOCATION / HINT'}{RESET}")
    print(f"  {GRAY}{'─' * 82}{RESET}")
    installed_count = 0
    for cmd, desc, hint in LINUX_CYBER_PACKAGES:
        path = shutil.which(cmd)
        if path:
            installed_count += 1
            badge_raw = "✔ READY"
            status = f"{GREEN}{BOLD}{badge_raw:<15}{RESET}"
            loc = f"{CYAN}{path}{RESET}"
        else:
            badge_raw = "○ NOT FOUND"
            status = f"{YELLOW}{badge_raw:<15}{RESET}"
            loc = f"{GRAY}{hint}{RESET}"
        print(f"  {WHITE}{BOLD}{cmd:<12}{RESET} {status} {WHITE}{desc:<36}{RESET} {loc}")

    print(
        f"\n  {CYAN}◈ ARSENAL READINESS :{RESET} {WHITE}{installed_count}/{len(LINUX_CYBER_PACKAGES)} "
        f"native security binaries online.{RESET}\n"
    )


def tool_nmap_wrapper(target: str):
    if shutil.which("nmap"):
        print_header("CYBER-NMAP // NATIVE NMAP SERVICE & SCRIPT SCANNER", f"Target: {target}")
        print(f"\n  {CYAN}⚡ Launching nmap -F -sV {target}...{RESET}\n")
        subprocess.run(["nmap", "-F", "-sV", target], check=False)
    else:
        print(f"\n  {YELLOW}⚠ Native 'nmap' binary not installed; falling back to built-in Cyber-Port Scanner:{RESET}")
        tool_port_scanner(target, "1-1024")


# ============================================================================
# 14. INTERACTIVE CYBER-DECK MENU
# ============================================================================
def interactive_menu():
    while True:
        print(f"\n{MAGENTA}╔{'═' * BOX_INNER_WIDTH}╗{RESET}")
        print(
            box_row(
                f" {CYAN}{BOLD}◢◤ CYBER-OS // SECURITY, PORT-KILLER & RECON ARSENAL v4.5{RESET}"
                f"   {GREEN}{BOLD}[{OS_NAME.upper()}]{RESET}"
            )
        )
        print(f"{MAGENTA}╠{'═' * BOX_INNER_WIDTH}╣{RESET}")
        menu_rows = [
            (("1", "Port & Process Scanner", "cyber-ports", WHITE), ("8", "Hash & JWT Decode", "cyber-hash", WHITE)),
            (("2", "Kill Port Job", "cyber-kill", WHITE), ("9", "Key Generator", "cyber-keygen", WHITE)),
            (("3", "Jobs, Threads & Cron", "cyber-jobs", WHITE), ("10", "File Integrity", "cyber-fim", WHITE)),
            (("4", "Domain / DNS / IP Recon", "cyber-recon", WHITE), ("11", "Kernel & Host Audit", "cyber-audit", WHITE)),
            (("5", "SSL/TLS Inspector", "cyber-ssl", WHITE), ("12", "Secret Leak Scanner", "cyber-secrets", WHITE)),
            (("6", "HTTP Security Headers", "cyber-headers", WHITE), ("13", "Cyber Arsenal", "cyber-arsenal", WHITE)),
            (("7", "Active TCP Connections", "cyber-conn", WHITE), ("14", "Face/Age/Mood/ASL", "cyber-cam", GREEN + BOLD)),
            (("15", "Omni-Search Engine", "cyber-search", YELLOW + BOLD), ("0", "Exit Cyber-Deck", "", GRAY)),
        ]

        def menu_cell(num: str, label: str, alias: str, color: str, width: int) -> str:
            key_color = RED if num == "0" else CYAN
            cell = f" {key_color}[{num:>2}]{RESET} {color}{label}{RESET}"
            if alias:
                cell += f" {GRAY}({alias}){RESET}"
            return cell + " " * max(0, width - visible_len(cell))

        for left, right in menu_rows:
            print(box_row(menu_cell(*left, width=43) + f"{GRAY}│{RESET}" + menu_cell(*right, width=42)))
        print(f"{MAGENTA}╚{'═' * BOX_INNER_WIDTH}╝{RESET}")

        try:
            choice = input(f"\n  {MAGENTA}╔═[{CYAN}⚡ SELECT MODULE (0-15){MAGENTA}]═❯ {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {CYAN}⚡ Disconnecting from Cyber-Deck Arsenal...{RESET}\n")
            break

        if choice in ("0", "q", "exit"):
            print(f"\n  {CYAN}⚡ Disconnecting from Cyber-Deck Arsenal...{RESET}\n")
            break
        elif choice == "1":
            target = input(f"  {CYAN}▸ Target IP/Host [127.0.0.1]: {RESET}").strip() or "127.0.0.1"
            ports = input(f"  {CYAN}▸ Port Range [common / 1-1024]: {RESET}").strip() or "common"
            tool_port_scanner(target, ports)
        elif choice == "2":
            port_s = input(f"  {CYAN}▸ Enter Port Number to Kill (e.g. 3000, 8000): {RESET}").strip()
            if port_s.isdigit():
                force_s = input(f"  {CYAN}▸ Force kill? [y/N]: {RESET}").strip().lower()
                force = force_s in ("y", "yes")
                tool_kill_port(int(port_s), force=force)
            else:
                print(f"  {RED}✖ Invalid port number.{RESET}")
        elif choice == "3":
            tool_jobs_and_threads()
        elif choice == "4":
            target = input(f"  {CYAN}▸ Target Domain or IP [example.com]: {RESET}").strip() or "example.com"
            tool_recon(target)
        elif choice == "5":
            target = input(f"  {CYAN}▸ Target HTTPS Host [github.com]: {RESET}").strip() or "github.com"
            tool_ssl_inspector(target)
        elif choice == "6":
            url = input(f"  {CYAN}▸ Target URL [https://github.com]: {RESET}").strip() or "https://github.com"
            tool_http_headers(url)
        elif choice == "7":
            tool_connections()
        elif choice == "8":
            mode = input(f"  {CYAN}▸ [H]ash string/file or [D]ecode Base64/Hex/JWT? [H/d]: {RESET}").strip().lower()
            if mode == "d":
                payload = input(f"  {CYAN}▸ Enter encoded string or JWT: {RESET}").strip()
                if payload:
                    tool_decode(payload)
            else:
                val = input(f"  {CYAN}▸ Enter string or file path to hash: {RESET}").strip()
                if val:
                    tool_crypto_hash(val)
        elif choice == "9":
            length_s = input(f"  {CYAN}▸ Key/Password Length [32]: {RESET}").strip() or "32"
            tool_keygen(int(length_s) if length_s.isdigit() else 32)
        elif choice == "10":
            d = input(f"  {CYAN}▸ Directory to baseline/verify [.]: {RESET}").strip() or "."
            tool_fim(d)
        elif choice == "11":
            tool_system_audit()
        elif choice == "12":
            d = input(f"  {CYAN}▸ Directory to scan for leaked secrets [.]: {RESET}").strip() or "."
            tool_secret_scanner(d)
        elif choice == "13":
            tool_arsenal_status()
        elif choice == "14":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, os.path.join(script_dir, "cyber_vision.py")], check=False)
        elif choice == "15":
            q = input(f"  {CYAN}▸ Enter Omni-Search Query (Files + Browser History + Web): {RESET}").strip()
            if q:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                subprocess.run([sys.executable, os.path.join(script_dir, "cyber_search.py"), "--omni", q], check=False)
        else:
            print(f"  {RED}✖ Invalid selection '{choice}'. Choose 0-15.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="CYBER-OS // Neural Security, Port-Killer & Recon Arsenal")
    parser.add_argument("--menu", action="store_true", help="Launch interactive Cyber-Deck menu")
    parser.add_argument("--ports", metavar="TARGET", help="Multi-threaded TCP port, process & banner scanner")
    parser.add_argument("--range", default="common", help="Port range for --ports (e.g. 'common', '1-1024', '22,80,443')")
    parser.add_argument("--kill-port", type=int, metavar="PORT", help="Find and terminate process listening on PORT")
    parser.add_argument("--force", action="store_true", help="Force kill (SIGKILL / /F) when using --kill-port")
    parser.add_argument("--timeout", type=float, default=5.0, metavar="SECS", help="Seconds to wait for graceful shutdown before reporting still running (default: 5)")
    parser.add_argument("--jobs", action="store_true", help="Scan live thread counts, active processes & scheduled cron/system jobs")
    parser.add_argument("--recon", metavar="DOMAIN_OR_IP", help="DNS, reverse PTR, and ASN/Geo reconnaissance")
    parser.add_argument("--ssl", metavar="HOST", help="SSL/TLS certificate & cipher suite inspector")
    parser.add_argument("--headers", metavar="URL", help="HTTP security header & server posture auditor")
    parser.add_argument("--conn", action="store_true", help="Active TCP network connections & listening sockets")
    parser.add_argument("--hash", metavar="TEXT_OR_FILE", help="Compute MD5, SHA1, SHA256, SHA512, BLAKE2b digests")
    parser.add_argument("--decode", metavar="PAYLOAD", help="Decode Base64, Hex, URL, or inspect JWT token")
    parser.add_argument("--keygen", nargs="?", const=32, type=int, metavar="LEN", help="Generate CSPRNG keys & passwords")
    parser.add_argument("--fim", nargs="?", const=".", metavar="DIR", help="SHA-256 File Integrity Monitor baseline/verify")
    parser.add_argument("--audit", action="store_true", help="System security, kernel sysctl & SUID forensics audit")
    parser.add_argument("--secrets", nargs="?", const=".", metavar="DIR", help="Scan workspace for leaked API keys & secrets")
    parser.add_argument("--arsenal", action="store_true", help="Check installed system security packages")
    parser.add_argument("--nmap", metavar="TARGET", help="Run nmap wrapper (or built-in port scan fallback)")

    args = parser.parse_args()

    if args.ports:
        tool_port_scanner(args.ports, args.range)
    elif args.kill_port is not None:
        tool_kill_port(args.kill_port, force=args.force, timeout=args.timeout)
    elif args.jobs:
        tool_jobs_and_threads()
    elif args.recon:
        tool_recon(args.recon)
    elif args.ssl:
        tool_ssl_inspector(args.ssl)
    elif args.headers:
        tool_http_headers(args.headers)
    elif args.conn:
        tool_connections()
    elif args.hash:
        tool_crypto_hash(args.hash)
    elif args.decode:
        tool_decode(args.decode)
    elif args.keygen is not None:
        tool_keygen(args.keygen)
    elif args.fim is not None:
        tool_fim(args.fim)
    elif args.audit:
        tool_system_audit()
    elif args.secrets is not None:
        tool_secret_scanner(args.secrets)
    elif args.arsenal:
        tool_arsenal_status()
    elif args.nmap:
        tool_nmap_wrapper(args.nmap)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
