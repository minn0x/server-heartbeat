#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 minn0x
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
"""
heartbeat

heartbeat.py

Sends a recurring heartbeat ping to healthchecks.io every 5 minutes.
Logs success and failure to a rotating log file (max ~1 MB).
On failure, an explicit /fail ping is sent to healthchecks.io for
active alerting rather than relying on a missed heartbeat alone.

Usage:
    python heartbeat.py

Configuration:
    Set PING_URL to your healthchecks.io ping URL before deploying.
"""
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from logging.handlers import RotatingFileHandler

# Configuration
PING_URL = "https://hc-ping.com/XXX"  # Replace with your actual UUID
INTERVAL_MINUTES = 5
LOG_FILE = "heartbeat.log"

# Set up logging — max 1 MB total, single rolling file
rotating_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=900_000,    # Rotate at ~900 KB
    backupCount=1,       # Keep 1 backup → max ~1.8 MB worst case, typically ~1 MB
    encoding="utf-8",
)
rotating_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(rotating_handler)
logger.addHandler(logging.StreamHandler())

def send_fail_ping():
    """Best-effort /fail ping — never raises, network may already be down."""
    try:
        requests.get(PING_URL + "/fail", timeout=10)
    except Exception:
        pass

def send_heartbeat():
    """Send a heartbeat ping to healthchecks.io"""
    try:
        response = requests.get(PING_URL, timeout=10)
        response.raise_for_status()
        logging.info(f"Heartbeat sent successfully - Status: {response.status_code}")
    except requests.exceptions.Timeout:
        logging.error("Heartbeat FAILED - Request timeout")
        send_fail_ping()
    except requests.exceptions.RequestException as e:
        logging.error(f"Heartbeat FAILED - {type(e).__name__}: {e}")
        send_fail_ping()
    except Exception as e:
        logging.error(f"Heartbeat FAILED - Unexpected error: {e}")
        send_fail_ping()

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(
        send_heartbeat,
        trigger=IntervalTrigger(minutes=INTERVAL_MINUTES),
        id='heartbeat_job',
        name='Send heartbeat to healthchecks.io',
        replace_existing=True,
        misfire_grace_time=30,   # Allow up to 30s late firing before skipping
    )

    logging.info(f"Starting heartbeat scheduler - Ping every {INTERVAL_MINUTES} minutes")
    logging.info(f"Target URL: {PING_URL}")

    send_heartbeat()

    try:
        logging.info(f"Scheduler running, next ping in {INTERVAL_MINUTES} min")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Heartbeat scheduler stopped")
        scheduler.shutdown()