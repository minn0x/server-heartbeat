# Heartbeat

A lightweight Python script that sends a recurring ping to [healthchecks.io](https://healthchecks.io) every 5 minutes, confirming your Server / VPS is alive. On any network failure it immediately sends an explicit `/fail` ping so you get alerted right away rather than waiting for a missed heartbeat timeout.

---

## What it does

- Pings your healthchecks.io check URL on a fixed interval (default: every 5 minutes)
- On timeout or any request failure, sends a `/fail` ping for immediate alerting
- Logs all activity (success and failure) to a rotating log file capped at ~1 MB
- Mirrors all log output to stdout so it works cleanly with `systemd` or process managers

---

## Requirements

- Python 3.8 or newer

```bash
pip install requests apscheduler
```

| Package | Purpose |
|---------|---------|
| `requests` | HTTP pings to healthchecks.io |
| `apscheduler` | Interval scheduler |

---

## Setup

### 1. Get your healthchecks.io ping URL

1. Sign up or log in at [healthchecks.io](https://healthchecks.io)
2. Create a new check — set the **Period** to `5 minutes` and **Grace** to `1–2 minutes`
3. Copy the ping URL — it looks like:
   ```
   https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

### 2. Configure the script

Open `heartbeat.py` and replace `XXX` in the `PING_URL` constant with your actual UUID:

```python
# Before
PING_URL = "https://hc-ping.com/XXX"

# After
PING_URL = "https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 3. Run it

```bash
python heartbeat.py
```

---

## Running as a background service

### Windows — Task Scheduler

Create a basic task that runs `python heartbeat.py` at startup with the working directory set to the script folder.

### Linux — systemd

Create `/etc/systemd/system/heartbeat.service`:

```ini
[Unit]
Description=healthchecks.io heartbeat
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/heartbeat.py
WorkingDirectory=/path/to/
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl enable heartbeat
sudo systemctl start heartbeat
```

---

## Configuration

All options are at the top of `heartbeat.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `PING_URL` | `https://hc-ping.com/XXX` | **Required.** Replace `XXX` with your check UUID |
| `INTERVAL_MINUTES` | `5` | How often to ping in minutes |
| `LOG_FILE` | `heartbeat.log` | Log file path (relative to script location) |

---

## Log output

```
2026-05-23 21:00:00,000 - INFO - Starting heartbeat scheduler - Ping every 5 minutes
2026-05-23 21:00:00,001 - INFO - Target URL: https://hc-ping.com/xxxxxxxx-...
2026-05-23 21:00:00,312 - INFO - Heartbeat sent successfully - Status: 200
2026-05-23 21:05:00,401 - INFO - Heartbeat sent successfully - Status: 200
2026-05-23 21:10:00,000 - ERROR - Heartbeat FAILED - Request timeout
```

The log file rotates at ~900 KB and keeps one backup, keeping total disk usage under ~1 MB during normal operation.

---

## How healthchecks.io alerting works

healthchecks.io monitors your check in two ways:

- **Missed heartbeat** — if no ping arrives within the Period + Grace window, the check goes `Late` then `Down` and sends an alert
- **Explicit `/fail` ping** — if this script catches a network error, it immediately hits `https://hc-ping.com/<UUID>/fail`, which marks the check as `Down` right away without waiting for the grace period to expire

This means you get alerted both when the script itself fails to reach the internet *and* when the machine goes completely silent.

---

## License

Copyright (C) 2026 minn0x  
Licensed under the [GNU General Public License v3.0](LICENSE)
