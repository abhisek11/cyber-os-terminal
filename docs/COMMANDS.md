# 🕹️ CYBER-OS Command Reference

Every command, every flag, with copy-paste examples.

- **Shortcut** — the short command you get after running the installer (`bash install.sh` or `install.ps1`).
- **PowerShell** — the same shortcut on Windows.
- **Direct** — works anywhere without installing, from the repo folder (`python` instead of `python3` on Windows).

> ⚠️ Only scan, probe or audit machines and domains **you own or are authorized to test**.

## Contents

| Area | Commands |
| :-- | :-- |
| [Telemetry HUD](#-telemetry-hud) | [`hud`](#hud) · [`cyber-watch`](#cyber-watch) · [`cyber-matrix`](#cyber-matrix) · [`cyber-scan`](#cyber-scan) · [`cyber-cockpit`](#cyber-cockpit) |
| [Ports & processes](#-ports--processes) | [`cyber-ports`](#cyber-ports) · [`cyber-kill`](#cyber-kill) · [`cyber-jobs`](#cyber-jobs) · [`cyber-conn`](#cyber-conn) · [`cyber-nmap`](#cyber-nmap) |
| [Recon & web security](#-recon--web-security) | [`cyber-recon`](#cyber-recon) · [`cyber-ssl`](#cyber-ssl) · [`cyber-headers`](#cyber-headers) |
| [Crypto & encoding](#-crypto--encoding) | [`cyber-hash`](#cyber-hash) · [`cyber-decode`](#cyber-decode) · [`cyber-keygen`](#cyber-keygen) |
| [Host defence](#-host-defence) | [`cyber-fim`](#cyber-fim) · [`cyber-audit`](#cyber-audit) · [`cyber-secrets`](#cyber-secrets) · [`cyber-arsenal`](#cyber-arsenal) |
| [Search](#-search) | [`cyber-search`](#cyber-search) · [`cyber-find`](#cyber-find) · [`cyber-history`](#cyber-history) · [`cyber-web`](#cyber-web) |
| [Camera cockpit](#-camera-cockpit) | [`cyber-cam`](#cyber-cam) |
| [Menu](#-interactive-menu) | [`cyber-tools`](#cyber-tools) |
| [Shell extras](#-shell-extras) | `ls` · `ll` · `la` · `lt` · `cat` · `top` · `ports` · `gs` · `glog` |

Every Python module also prints its own flags with `--help`:

```bash
python3 scifi_hud.py --help
python3 cyber_tools.py --help
python3 cyber_search.py --help
python3 cyber_vision.py --help
```

---

## 📊 Telemetry HUD

### `hud`

Prints the neon status panel once: host, OS, uptime, CPU / memory / disk bars, local IP, total threads and processes, scheduled jobs, and a list of the main commands. It also runs automatically (with a short boot animation) the first time a new terminal opens.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `hud` | `hud` | `python3 scifi_hud.py` |

| Flag | Meaning |
| :-- | :-- |
| `--boot` | Play the "neural interface" boot animation first |

```bash
hud                 # draw the panel once
hud --boot          # with the boot animation
python3 scifi_hud.py | less -R    # page through it, keeping colors
```

Don't want the HUD at every new terminal? Set `export CYBER_HUD_SHOWN=1` before the line that sources `cyberpunk_shell.sh` in your `~/.bashrc` / `~/.zshrc`.

### `cyber-watch`

Same panel, redrawn every second until you press **Ctrl+C**. Good for a side pane or second monitor.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-watch` | `cyber-watch` | `python3 scifi_hud.py --watch` |

```bash
cyber-watch
```

Needs a terminal at least 88 columns wide (narrower layouts: [#16](https://github.com/abhisek11/cyber-os-terminal/issues/16)).

### `cyber-matrix`

Full-screen neon "digital rain" animation. **Ctrl+C** to exit.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-matrix` | `cyber-matrix` | `python3 scifi_hud.py --matrix` |

```bash
cyber-matrix
```

### `cyber-scan`

Quick sweep of your **own machine**: prints the hostname and primary IP, then checks a fixed list of developer ports (22, 80, 443, 3000, 5000, 5432, 6379, 8000, 8080, …) on localhost and shows which are open. For any other target or range, use [`cyber-ports`](#cyber-ports).

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-scan` | `cyber-scan` | `python3 scifi_hud.py --scan` |

```bash
cyber-scan
```

### `cyber-cockpit`

Opens a tmux session named `cyberdeck` using the bundled cyberpunk tmux theme: the live HUD on the left, a shell on the right. Run it again to re-attach. Without tmux it falls back to `cyber-watch`.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-cockpit` | *not available yet* ([#50](https://github.com/abhisek11/cyber-os-terminal/issues/50)) | `tmux -f tmux.cyberpunk.conf new-session -A -s cyberdeck "python3 scifi_hud.py --watch"` |

```bash
cyber-cockpit                 # start or re-attach
tmux kill-session -t cyberdeck  # close it completely
```

Requires `tmux` (`sudo apt install tmux` / `brew install tmux`).

---

## 🔌 Ports & processes

### `cyber-ports`

Multi-threaded TCP scanner. For each open port it shows the service name, the process (PID and thread count) that owns it when the target is your own machine, and the first line of the server's banner (e.g. `HTTP/1.0 200 OK`, `SSH-2.0-OpenSSH_9.6`).

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-ports [target] [range]` | `cyber-ports [-Target] [-Range]` | `python3 cyber_tools.py --ports TARGET --range RANGE` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `target` | `127.0.0.1` | Hostname or IP to scan |
| `range` | `common` | `common` (39 well-known ports), a list `22,80,443`, a range `1-1024`, or a mix `22,80,8000-8100` |

```bash
cyber-ports                                   # localhost, common ports
cyber-ports 127.0.0.1 1-1024                  # first 1024 ports
cyber-ports 192.168.1.10 22,80,443            # three specific ports on a LAN box
cyber-ports localhost 3000-3010,5173,8000     # find which dev servers are running
python3 cyber_tools.py --ports scanme.nmap.org --range 22,80   # Nmap's public test host
```

```powershell
cyber-ports 127.0.0.1 1-1024
cyber-ports -Target 127.0.0.1 -Range "22,80,443"   # quote lists in PowerShell
```

![Terminal output for a localhost port scan](screenshots/commands/cyber-ports.png)

How ranges are read (from PR #47): ends are inclusive, `1024-1` is treated as `1-1024`, `0-2` is trimmed to `1,2`, and bad input such as `web-80` prints a red `✖ Invalid port spec` message. Planned: IPv6, UDP and `--top 1000` ([#23](https://github.com/abhisek11/cyber-os-terminal/issues/23)).

### `cyber-kill`

Finds whatever is holding a port and terminates it — the classic fix for *"Error: listen EADDRINUSE: address already in use :::3000"*.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-kill PORT` | `cyber-kill PORT` | `python3 cyber_tools.py --kill-port PORT [--force]` |

| Argument | Meaning |
| :-- | :-- |
| `PORT` | Port number (required) |
| `--force` | Hard kill (`SIGKILL` / `taskkill /F`). The shortcut **always** adds this. |

```bash
cyber-kill 3000                                # free port 3000 (force)
python3 cyber_tools.py --kill-port 8000        # try SIGTERM first
python3 cyber_tools.py --kill-port 8000 --force
sudo python3 cyber_tools.py --kill-port 80     # ports owned by root need sudo
```

It finds the owning process with `lsof`, then `ss` or `fuser` on Linux, or `netstat` on Windows. On a Linux box without those tools it reads the socket tables in `/proc`, so only a process that really holds the port is killed. It prints the PID table before killing. Be careful with system ports such as `22` (SSH) — killing `sshd` drops remote sessions. Open work: confirmation prompt ([#5](https://github.com/abhisek11/cyber-os-terminal/issues/5)), a truly graceful mode ([#4](https://github.com/abhisek11/cyber-os-terminal/issues/4), [#51](https://github.com/abhisek11/cyber-os-terminal/issues/51)), safer matching on Windows ([#3](https://github.com/abhisek11/cyber-os-terminal/issues/3)).

### `cyber-jobs`

Counts every process and live thread, ranks the top processes by thread count and memory, and lists scheduled work: your crontab, `/etc/cron.*`, systemd timers and running services on Linux, and Task Scheduler on Windows.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-jobs` | `cyber-jobs` | `python3 cyber_tools.py --jobs` |

```bash
cyber-jobs
cyber-jobs | less -R        # scroll through a long list
sudo python3 cyber_tools.py --jobs     # include root's crontab
```

macOS `launchd` jobs aren't listed yet ([#27](https://github.com/abhisek11/cyber-os-terminal/issues/27)).

### `cyber-conn`

Lists active TCP connections and listening sockets (local address → remote address, state).

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-conn` | `cyber-conn` | `python3 cyber_tools.py --conn` |

```bash
cyber-conn
```

On Linux it reads `/proc/net/tcp`; on macOS and Windows it currently probes common localhost ports instead. Full IPv6/UDP and process names: [#22](https://github.com/abhisek11/cyber-os-terminal/issues/22).

### `cyber-nmap`

Runs `nmap -F -sV TARGET` (fast scan of the top 100 ports with service versions) if `nmap` is installed; otherwise falls back to the built-in scanner on ports 1–1024.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-nmap [target]` | `cyber-nmap [-Target]` | `python3 cyber_tools.py --nmap TARGET` |

```bash
cyber-nmap                      # 127.0.0.1
cyber-nmap 192.168.1.1          # your router
cyber-nmap scanme.nmap.org      # Nmap's public test host
```

---

## 🌐 Recon & web security

### `cyber-recon`

Domain / IP intelligence: IPv4 + IPv6 addresses, reverse DNS (PTR), ASN / ISP / country, and `MX`, `NS`, `TXT` records when `dig` is installed.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-recon [target]` | `cyber-recon [-Target]` | `python3 cyber_tools.py --recon TARGET` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `target` | `example.com` | Domain name or IP address |

```bash
cyber-recon github.com
cyber-recon 1.1.1.1
cyber-recon mycompany.com      # check your own MX/TXT (SPF, DMARC) records
```

The ASN/geo lookup sends the IP to a public service ([#7](https://github.com/abhisek11/cyber-os-terminal/issues/7) tracks making it HTTPS and skipping private ranges).

### `cyber-ssl`

Connects over TLS and reports the protocol version, cipher suite, certificate subject and issuer, SAN domains, and **days until the certificate expires**.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-ssl [host[:port]]` | `cyber-ssl [-Target]` | `python3 cyber_tools.py --ssl HOST[:PORT]` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `host[:port]` | `github.com` | Host name, optional port (default 443) |

```bash
cyber-ssl github.com
cyber-ssl mail.google.com:465        # SMTPS
cyber-ssl my-staging.example.com:8443
```

Expired or self-signed certificates currently fail the handshake and only show an error ([#8](https://github.com/abhisek11/cyber-os-terminal/issues/8)).

### `cyber-headers`

Fetches a URL and grades its HTTP security headers from **A+ to F**: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and shows the `Server` and `X-Powered-By` headers, which can reveal your software versions.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-headers [url]` | `cyber-headers [-Url]` | `python3 cyber_tools.py --headers URL` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `url` | `https://github.com` | Full URL including `https://` |

```bash
cyber-headers https://github.com
cyber-headers https://my-app.vercel.app
cyber-headers http://localhost:3000      # check your dev server before deploying
```

Known issues: certificate checks are disabled and error pages are graded too ([#6](https://github.com/abhisek11/cyber-os-terminal/issues/6)).

---

## 🔐 Crypto & encoding

### `cyber-hash`

Prints MD5, SHA-1, SHA-256, SHA-384, SHA-512 and BLAKE2b-256 digests. If the argument is an existing file path it hashes the **file**, otherwise it hashes the **text**.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-hash [text-or-file]` | `cyber-hash [-InputVal]` | `python3 cyber_tools.py --hash TEXT_OR_FILE` |

```bash
cyber-hash "hello world"                       # hash a string
cyber-hash ./scifi_hud.py                      # hash a file
cyber-hash ~/Downloads/ubuntu-24.04.iso        # compare with the publisher's SHA-256
```

![Terminal output for hashing a text string](screenshots/commands/cyber-hash.png)

### `cyber-decode`

Auto-detects and decodes a payload: **JWT** (pretty-prints header and payload, shows the signature), **Base64**, **hex** and **URL-encoding**, and also shows the input re-encoded as Base64 and hex.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-decode PAYLOAD` | `cyber-decode PAYLOAD` | `python3 cyber_tools.py --decode PAYLOAD` |

```bash
cyber-decode "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.sig"   # JWT → {"alg":"HS256"} {"sub":"123"}
cyber-decode 68656c6c6f                                     # hex → hello
cyber-decode aGVsbG8gd29ybGQ=                               # base64 → hello world
cyber-decode "name%3Dneo%26role%3Dadmin"                    # URL → name=neo&role=admin
```

![Terminal output for decoding a hexadecimal payload](screenshots/commands/cyber-decode.png)

Always quote JWTs and anything with `&`, `=` or `%`. JWT signatures are **not verified** — this is for reading tokens, not trusting them. Spurious Base64 output on plain words: [#10](https://github.com/abhisek11/cyber-os-terminal/issues/10).

### `cyber-keygen`

Generates secrets with Python's cryptographically secure `secrets` module: a complex password, an alphanumeric password, an API-style key, an AES-256 hex key, a Base64 secret and a UUIDv4.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-keygen [length]` | `cyber-keygen [-Length]` | `python3 cyber_tools.py --keygen [LEN]` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `length` | `32` | Length of the passwords |

```bash
cyber-keygen            # 32-character passwords
cyber-keygen 48         # longer
cyber-keygen 16         # for systems with short limits
```

Generated values are printed to the screen (and your scrollback) — copy what you need and clear the terminal. The entropy rating is being corrected in [#9](https://github.com/abhisek11/cyber-os-terminal/issues/9).

---

## 🔒 Host defence

### `cyber-fim`

File Integrity Monitor. The **first** run records a SHA-256 of every file in the folder into `.cyber_fim.json`. **Later** runs compare against it and report `MODIFIED`, `ADDED` and `DELETED` files.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-fim [dir]` | `cyber-fim [-Dir]` | `python3 cyber_tools.py --fim [DIR]` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `dir` | `.` (current folder) | Folder to baseline / verify |

```bash
cyber-fim ~/deploy/site          # 1st run: creates the baseline
# ...time passes...
cyber-fim ~/deploy/site          # 2nd run: shows ⚠ MODIFIED : index.html
rm ~/deploy/site/.cyber_fim.json && cyber-fim ~/deploy/site   # accept changes (re-baseline)
```

Files over 25 MB are skipped. The baseline lives inside the watched folder, so anyone who can change the files can also change the baseline — improvements in [#24](https://github.com/abhisek11/cyber-os-terminal/issues/24).

### `cyber-audit`

Security posture check. On Linux: kernel hardening settings (ASLR, `kptr_restrict`, `dmesg_restrict`, ptrace scope, TCP SYN cookies), permissions on sensitive files such as `/etc/passwd` and `/etc/shadow`, and SUID binaries. Prints a ✔ / ⚠ per item.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-audit` | `cyber-audit` | `python3 cyber_tools.py --audit` |

```bash
cyber-audit
sudo python3 cyber_tools.py --audit      # read everything (some files need root)
```

macOS and Windows checks are still minimal ([#26](https://github.com/abhisek11/cyber-os-terminal/issues/26)).

### `cyber-secrets`

Scans a folder for leaked credentials before you commit or publish: AWS access keys, private key blocks, GitHub tokens, OpenAI-style `sk-` keys, Google API keys, Slack tokens, and generic `api_key = "…"` / `password = "…"` assignments. Skips `.git`, `node_modules` and binary files.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-secrets [dir]` | `cyber-secrets [-Dir]` | `python3 cyber_tools.py --secrets [DIR]` |

```bash
cyber-secrets                    # current folder
cyber-secrets ~/projects/api     # a project before pushing it
```

Matches are shown masked, up to 20. CI exit codes, `--json` and more patterns: [#25](https://github.com/abhisek11/cyber-os-terminal/issues/25).

### `cyber-arsenal`

Shows which native security tools are installed (`nmap`, `whois`, `dig`, `nc`, `tcpdump`, `tshark`, `curl`, `openssl`, `ss`, `ufw`, …) with the install command for any that are missing.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-arsenal` | `cyber-arsenal` | `python3 cyber_tools.py --arsenal` |

```bash
cyber-arsenal
bash install.sh --packages       # install the missing ones (Linux/macOS)
```

---

## 🔎 Search

### `cyber-search`

**Omni-search**: one query across local files (current folder), your browser history, and the web (DuckDuckGo, Wikipedia, GitHub) at the same time.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-search QUERY…` | `cyber-search "QUERY"` | `python3 cyber_search.py QUERY` or `--omni QUERY` |

| Flag (direct) | Meaning |
| :-- | :-- |
| `--json` | Machine-readable output |

```bash
cyber-search langgraph                 # one word
cyber-search kafka consumer lag        # several words (bash/zsh)
python3 cyber_search.py --omni "rate limiter" --json | jq .
```

```powershell
cyber-search "kafka consumer lag"      # PowerShell needs quotes for now (#50)
```

Your query is sent to DuckDuckGo, Wikipedia and GitHub. For private terms use `cyber-find` / `cyber-history` instead (an `--offline` switch is planned: [#20](https://github.com/abhisek11/cyber-os-terminal/issues/20)).

### `cyber-find`

Searches **file names and file contents** under a folder, showing matching lines with line numbers. Skips `.git`, virtualenvs, `node_modules`, caches, hidden folders and binary files. Up to 25 name matches and 25 content matches.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-find QUERY [dir]` | `cyber-find [-Query] [-Dir]` | `python3 cyber_search.py --files QUERY --dir DIR` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `QUERY` | `cyber` | Text to look for (case-insensitive) |
| `dir` | `.` | Folder to search |

```bash
cyber-find TODO                         # in the current project
cyber-find "API_KEY" ~/projects         # where is this variable used?
cyber-find docker-compose ~             # find a file by name
python3 cyber_search.py --files "def main" --dir . --json
```

Regex, case-sensitive and `.gitignore` support: [#21](https://github.com/abhisek11/cyber-os-terminal/issues/21).

### `cyber-history`

Searches your **local** browser history (Chrome, Chromium, Brave, Edge, Firefox) by title and URL. Works while the browser is open — it reads a temporary copy of the database. Nothing is uploaded.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-history [query…]` | `cyber-history [-Query]` | `python3 cyber_search.py --history [QUERY]` |

| Argument | Default | Meaning |
| :-- | :-- | :-- |
| `query` | `recent` | Text to match. `recent`, `all` or `*` lists your latest visits |

```bash
cyber-history                    # latest visits
cyber-history github pull        # pages about GitHub PRs you've visited
cyber-history localhost:3000     # find that dev URL you had open yesterday
python3 cyber_search.py --history stripe --json
```

Safari, Opera, Vivaldi and Arc: [#19](https://github.com/abhisek11/cyber-os-terminal/issues/19). Result ordering across browsers: [#18](https://github.com/abhisek11/cyber-os-terminal/issues/18).

### `cyber-web`

Searches the web from the terminal: DuckDuckGo results, matching Wikipedia articles and GitHub repositories (with star counts).

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-web QUERY…` | `cyber-web "QUERY"` | `python3 cyber_search.py --web QUERY [--open]` |

| Flag (direct) | Meaning |
| :-- | :-- |
| `--open` | Open the top result in your default browser |
| `--json` | Machine-readable output |

```bash
cyber-web "rust async tutorial"
cyber-web langgraph agents
python3 cyber_search.py --web "fastapi websockets" --open
```

GitHub's API allows about 60 unauthenticated searches per hour per IP.

---

## 📷 Camera cockpit

### `cyber-cam`

Starts a local web cockpit at `http://127.0.0.1:8765` that uses your webcam and microphone for face detection, age/mood estimation, hand gestures, ASL letters and voice commands — gestures and phrases can trigger the other commands (port scan, jobs, audit, history, search). The server listens on your own machine only (`127.0.0.1`).

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-cam [flags]` | `cyber-cam [flags]` | `python3 cyber_vision.py [flags]` |

| Flag | Default | Meaning |
| :-- | :-- | :-- |
| `--port PORT` | `8765` | Local port for the cockpit page |
| `--no-browser` | off | Don't open the browser automatically |
| `--native` | off | Use a native OpenCV window instead (`pip install opencv-python`) |

```bash
cyber-cam                          # opens the cockpit in your browser
cyber-cam --port 9000              # if 8765 is taken
cyber-cam --no-browser             # then open http://127.0.0.1:8765 yourself
cyber-cam --native                 # desktop window, no browser
```

| Gesture (hold ~1.5 s) | Action |
| :-- | :-- |
| ✌️ Peace | Port & process scan |
| ☝️ Point | Threads & scheduled jobs |
| 🤟 I love you | Security audit |
| 🤙 Shaka | Browser history |
| 👍 Thumbs up | Omni-search on the signed ASL word |

Voice examples: *"scan ports"*, *"kill port 8000"*, *"check jobs"*, *"search files for invoice"*, *"detect my age and mood"*.

Needs a Chromium-based browser, camera/microphone permission, and internet on first load (the vision models come from a CDN — [#38](https://github.com/abhisek11/cyber-os-terminal/issues/38)). Press **Ctrl+C** in the terminal to stop the server.

---

## 🎮 Interactive menu

### `cyber-tools`

A numbered menu of every security module — type a number, answer the prompts, and it runs the tool. Handy when you don't remember a command.

| Shortcut | PowerShell | Direct |
| :-- | :-- | :-- |
| `cyber-tools` | `cyber-tools` | `python3 cyber_tools.py --menu` |

```bash
cyber-tools
#   ⚡ SELECT MODULE (0-15) ❯ 1
#   ▸ Target IP/Host [127.0.0.1]: ⏎
#   ▸ Port Range [common / 1-1024]: 1-1024
```

| # | Module | Same as |
| :-- | :-- | :-- |
| 1 | Port & process scanner | `cyber-ports` |
| 2 | Kill port job | `cyber-kill` |
| 3 | Jobs, threads & cron | `cyber-jobs` |
| 4 | Domain / DNS / IP recon | `cyber-recon` |
| 5 | SSL/TLS inspector | `cyber-ssl` |
| 6 | HTTP security headers | `cyber-headers` |
| 7 | Active TCP connections | `cyber-conn` |
| 8 | Hash & JWT decode | `cyber-hash` / `cyber-decode` |
| 9 | Key generator | `cyber-keygen` |
| 10 | File integrity | `cyber-fim` |
| 11 | Kernel & host audit | `cyber-audit` |
| 12 | Secret leak scanner | `cyber-secrets` |
| 13 | Cyber arsenal | `cyber-arsenal` |
| 14 | Camera cockpit | `cyber-cam` |
| 15 | Omni-search | `cyber-search` |
| 0 | Exit | |

---

## 🧰 Shell extras

The bash/zsh profile also upgrades a few everyday commands **if** the modern tool is installed (otherwise it falls back to the normal one):

| Command | Becomes | Install |
| :-- | :-- | :-- |
| `ls`, `ll`, `la`, `lt` | `eza` with icons and git status (or `lsd`) | `brew install eza` / `apt install eza` |
| `cat` | `bat` with line numbers and syntax colors | `brew install bat` / `apt install bat` |
| `top` | `btop` (or `htop`) | `brew install btop` / `apt install btop` |
| `ports` | `ss -tulanp` — all listening sockets | built in (Linux) |
| `gs` | `git status -sb` | |
| `glog` | `git log --graph --oneline --decorate --all` | |
| `df`, `free`, `grep` | human-readable sizes / colored matches | |

```bash
ll                 # long listing with icons and git status
lt                 # tree view, 2 levels
cat app.py         # syntax-highlighted
\cat app.py        # the original cat (bypass the alias)
```

Note: the `cat` and `ls` aliases force colors, which adds escape codes when you pipe them (`cat file | jq`). Use `\cat` / `command cat` in pipes until [#28](https://github.com/abhisek11/cyber-os-terminal/issues/28) is fixed.

---

Found a command that behaves differently from this page? [Open an issue](https://github.com/abhisek11/cyber-os-terminal/issues/new/choose). Want to add output screenshots? See [#52](https://github.com/abhisek11/cyber-os-terminal/issues/52).
