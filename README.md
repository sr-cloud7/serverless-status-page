# ⚡ Serverless SRE Status Page & Uptime Monitor

An automated, lightweight, zero-cost SRE uptime monitoring system built with **Python**, **GitHub Actions**, and **GitHub Pages**.

![Uptime Monitor Workflow](https://github.com/sr-cloud7/serverless-status-page/actions/workflows/uptime.yml/badge.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)

---

## 📌 Overview

Maintaining uptime visibility is critical for software systems, but setting up dedicated monitoring infrastructure like Pingdom or Datadog can be cost-prohibitive for smaller projects or independent deployments.

This project implements an enterprise-grade **Serverless Monitoring and Status Page Pipeline**. It periodically tests targeted web services and APIs, auto-generates a static public dashboard hosted on GitHub Pages, and uses intelligent alert deduplication to automatically log incident tickets via GitHub Issues when an outage is detected.

---

## ✨ Key Features

* **🤖 100% Serverless Execution:** Runs on GitHub-hosted runners via GitHub Actions CRON schedule (every 5 minutes).
* **📊 Automated Dashboard Generation:** Dynamically generates a clean, responsive `index.html` static site detailing operational status and response latency (ms).
* **🚨 Smart Incident Management:** Automatically creates a structured GitHub Issue when an endpoint returns HTTP status codes $\ge 400$ or fails to establish a TCP connection.
* **🧠 Alert Deduplication:** Checks for active open incidents prior to creating a new ticket, preventing alert fatigue and issue spamming.
* **⚙️ Decoupled Architecture:** Monitored target endpoints are separated into a simple `targets.json` configuration file for straightforward maintenance.

---

## 🏗️ Architecture & Workflow

```text
┌─────────────────────────┐
│  GitHub Actions Cron    │ (Triggers every 5 min)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│       monitor.py        │
│  ─────────────────────  │
│  1. Read targets.json   │
│  2. Ping HTTP/HTTPS     │
│  3. Calculate Latency   │
└─────┬──────────────┬────┘
      │              │
 [Operational]    [Down / Timeout]
      │              │
      ▼              ▼
┌───────────┐  ┌─────────────────────────────────┐
│ Generate  │  │ Check Open GitHub Issues        │
│ index.html│  │ (Deduplicate) -> Create Issue 🚨│
└─────┬─────┘  └─────────────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ Deploy to GitHub Pages  │
└─────────────────────────┘
