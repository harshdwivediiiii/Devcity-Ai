from flask import Flask, request, jsonify, render_template_string, redirect, session, url_for
import json
import os
import logging
from datetime import datetime
import secrets
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from src import scan_pipeline


LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

from werkzeug.middleware.proxy_fix import ProxyFix

# Load local .env file if present
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
_sk = os.environ.get("SECRET_KEY")
if not _sk:
    LOGGER.warning(
        "SECRET_KEY not set - using random key. Sessions will break on restart."
    )
    _sk = secrets.token_hex(32)
app.secret_key = _sk

GITHUB_CLIENT_ID = (os.environ.get("GITHUB_CLIENT_ID") or "").strip()
GITHUB_CLIENT_SECRET = (os.environ.get("GITHUB_CLIENT_SECRET") or "").strip()
GITHUB_OAUTH_SCOPES = (os.environ.get("GITHUB_OAUTH_SCOPES") or "read:user repo").strip()
REDIRECT_URI = (os.environ.get("REDIRECT_URI") or "").strip()


def _is_logged_in() -> bool:
    return bool(session.get("github_user") and session.get("github_access_token"))


def _login_required() -> Any | None:
    if not _is_logged_in():
        return _json_error("GitHub login required", "AUTH_REQUIRED", 401)
    return None


def _json_error(
    error: str,
    code: str,
    status: int,
    detail: str | None = None,
) -> tuple[Any, int]:
    payload = {"error": error, "code": code}
    if detail:
        payload["detail"] = detail
    return jsonify(payload), status



# ============================================================
# Embedded HTML (do not modify - kept pixel-identical to originals)
# ============================================================

INDEX_HTML = r"""{% raw %}<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>DevCity AI — See Your Code as a City</title>
    <meta name="description"
        content="DevCity AI turns any GitHub repository into an interactive 3D city. Spot risk, complexity and tech debt at a glance — powered by AI." />
    <meta property="og:title" content="DevCity AI — See Your Code as a City" />
    <meta property="og:description"
        content="Turn any GitHub repo into a 3D city. AI-powered risk, complexity and architecture insights." />
    <meta property="og:type" content="website" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
        rel="stylesheet" />
    <style>
        :root {
            --bg: #05060a;
            --bg-2: #0a0d18;
            --surface: rgba(15, 19, 33, 0.65);
            --surface-2: rgba(22, 28, 48, 0.55);
            --border: rgba(120, 140, 200, 0.14);
            --border-strong: rgba(140, 160, 220, 0.28);
            --text: #e8ecf7;
            --text-dim: #aab1c8;
            --text-faint: #6b7493;
            --accent: #7c5cff;
            --accent-2: #22d3ee;
            --accent-3: #34d399;
            --warn: #f59e0b;
            --danger: #ef4444;
            --grad: linear-gradient(135deg, #7c5cff 0%, #22d3ee 60%, #34d399 100%);
            --grad-soft: linear-gradient(135deg, rgba(124, 92, 255, .18), rgba(34, 211, 238, .12));
            --shadow-glow: 0 30px 80px -30px rgba(124, 92, 255, .55);
            --radius: 16px;
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', system-ui, sans-serif;
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }

        body.product-mode {
            --accent: #6366f1;
            --accent-2: #06b6d4;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        button {
            font-family: inherit;
            cursor: pointer;
        }

        code,
        .mono {
            font-family: 'JetBrains Mono', ui-monospace, monospace;
        }

        /* Ambient bg */
        .bg-layer {
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background:
                radial-gradient(900px 600px at 12% -10%, rgba(124, 92, 255, .18), transparent 60%),
                radial-gradient(900px 600px at 100% 10%, rgba(34, 211, 238, .14), transparent 60%),
                radial-gradient(800px 600px at 50% 100%, rgba(52, 211, 153, .10), transparent 60%);
        }

        .bg-grid {
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(140, 160, 220, .05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(140, 160, 220, .05) 1px, transparent 1px);
            background-size: 56px 56px;
            mask-image: radial-gradient(ellipse at center, #000 30%, transparent 80%);
        }

        /* Nav */
        nav.top {
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(20px) saturate(140%);
            -webkit-backdrop-filter: blur(20px) saturate(140%);
            background: rgba(5, 6, 10, .55);
            border-bottom: 1px solid var(--border);
        }

        .nav-inner {
            max-width: 1240px;
            margin: 0 auto;
            padding: 14px 22px;
            display: flex;
            align-items: center;
            gap: 22px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            letter-spacing: -.02em;
        }

        .brand-mark {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: var(--grad);
            box-shadow: 0 6px 20px -6px rgba(124, 92, 255, .6);
            position: relative;
            overflow: hidden;
        }

        .brand-mark::after {
            content: '';
            position: absolute;
            inset: 4px;
            border-radius: 5px;
            background: linear-gradient(180deg, rgba(255, 255, 255, .3), rgba(255, 255, 255, 0));
        }

        .nav-links {
            display: flex;
            gap: 22px;
            margin-left: 18px;
        }

        .nav-links a {
            color: var(--text-dim);
            font-size: 14px;
            font-weight: 500;
            transition: color .2s;
        }

        .nav-links a:hover {
            color: var(--text);
        }

        .nav-spacer {
            flex: 1;
        }

        .mode-toggle {
            display: inline-flex;
            padding: 4px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: var(--surface-2);
            font-size: 12px;
            font-weight: 600;
        }

        .mode-toggle button {
            background: transparent;
            color: var(--text-dim);
            border: 0;
            padding: 6px 12px;
            border-radius: 999px;
        }

        .mode-toggle button.active {
            background: var(--grad);
            color: #0a0a14;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 12px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
            color: var(--text);
            font-size: 14px;
            font-weight: 600;
            transition: transform .15s, border-color .2s, background .2s;
        }

        .btn:hover {
            transform: translateY(-1px);
            border-color: rgba(180, 200, 255, .4);
        }

        .btn-primary {
            background: var(--grad);
            color: #0a0a14;
            border: 0;
            box-shadow: var(--shadow-glow);
        }

        .btn-primary:hover {
            filter: brightness(1.08);
        }

        .btn-sm {
            padding: 7px 12px;
            font-size: 13px;
            border-radius: 10px;
        }

        .btn .kbd {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            padding: 2px 6px;
            border: 1px solid var(--border-strong);
            border-radius: 5px;
            opacity: .8;
        }

        /* Layout */
        main {
            position: relative;
            z-index: 1;
            max-width: 1240px;
            margin: 0 auto;
            padding: 0 22px;
        }

        section {
            padding: 96px 0;
            position: relative;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border: 1px solid var(--border-strong);
            border-radius: 999px;
            background: var(--surface-2);
            font-size: 12px;
            font-weight: 600;
            color: var(--text-dim);
            letter-spacing: .04em;
        }

        .eyebrow .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-3);
            box-shadow: 0 0 10px var(--accent-3);
        }

        h1,
        h2,
        h3 {
            letter-spacing: -.025em;
            margin: 0;
        }

        h1 {
            font-size: clamp(40px, 6vw, 72px);
            font-weight: 800;
            line-height: 1.02;
        }

        h2 {
            font-size: clamp(28px, 3.6vw, 44px);
            font-weight: 800;
            line-height: 1.1;
        }

        h3 {
            font-size: 18px;
            font-weight: 700;
        }

        .gradient-text {
            background: var(--grad);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .lead {
            color: var(--text-dim);
            font-size: clamp(16px, 1.4vw, 19px);
            line-height: 1.55;
            max-width: 620px;
        }

        .center {
            text-align: center;
        }

        .center .lead {
            margin: 14px auto 0;
        }

        /* Hero */
        .hero {
            padding: 70px 0 60px;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.05fr 1fr;
            gap: 48px;
            align-items: center;
        }

        .hero h1 .gradient-text {
            display: inline-block;
        }

        .hero .lead {
            margin-top: 22px;
        }

        .analyze-card {
            margin-top: 30px;
            padding: 18px;
            border: 1px solid var(--border-strong);
            border-radius: 18px;
            background: var(--surface);
            backdrop-filter: blur(20px);
            box-shadow: var(--shadow-glow);
        }

        .analyze-row {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .analyze-row .gh-pre {
            display: flex;
            align-items: center;
            gap: 8px;
            padding-left: 12px;
            color: var(--text-faint);
            font-size: 14px;
        }

        .analyze-input {
            flex: 1;
            min-width: 0;
            background: transparent;
            border: 0;
            outline: 0;
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            padding: 12px 8px;
        }

        .sample-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .chip {
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid var(--border-strong);
            background: var(--surface-2);
            color: var(--text-dim);
            font-size: 12px;
            font-weight: 500;
            transition: all .15s;
        }

        .chip:hover {
            color: var(--text);
            border-color: rgba(180, 200, 255, .4);
        }

        .analyze-status {
            margin-top: 12px;
            font-size: 12px;
            color: var(--text-faint);
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 18px;
        }

        .analyze-status.error {
            color: #fca5a5;
        }

        .analyze-status.success {
            color: var(--accent-3);
        }

        .spinner {
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255, 255, 255, .2);
            border-top-color: var(--accent-2);
            border-radius: 50%;
            animation: spin .9s linear infinite;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }

        .hero-trust {
            display: flex;
            flex-wrap: wrap;
            gap: 16px 28px;
            margin-top: 28px;
            color: var(--text-faint);
            font-size: 13px;
        }

        .hero-trust span {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .hero-trust svg {
            width: 14px;
            height: 14px;
            color: var(--accent-3);
        }

        /* 3D hero canvas */
        .hero-stage {
            position: relative;
            aspect-ratio: 1.05/1;
            border: 1px solid var(--border-strong);
            border-radius: 24px;
            overflow: hidden;
            background: linear-gradient(180deg, #0a0d18 0%, #060810 100%);
            box-shadow: 0 40px 100px -40px rgba(124, 92, 255, .45), inset 0 0 0 1px rgba(255, 255, 255, .02);
        }

        .hero-stage canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        .stage-overlay {
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: radial-gradient(80% 60% at 50% 110%, rgba(124, 92, 255, .25), transparent 70%);
        }

        .stage-badge {
            position: absolute;
            top: 14px;
            left: 14px;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(0, 0, 0, .45);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            font-size: 11px;
            color: var(--text-dim);
            font-weight: 600;
            letter-spacing: .05em;
        }

        .stage-tooltip {
            position: absolute;
            pointer-events: none;
            padding: 8px 10px;
            border-radius: 10px;
            background: rgba(0, 0, 0, .75);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-strong);
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text);
            transform: translate(-50%, -120%);
            opacity: 0;
            transition: opacity .15s;
            z-index: 4;
        }

        .stage-tooltip b {
            color: var(--accent-2);
        }

        .stage-controls {
            position: absolute;
            bottom: 12px;
            right: 12px;
            display: flex;
            gap: 6px;
        }

        .stage-controls button {
            background: rgba(0, 0, 0, .55);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-strong);
            color: var(--text-dim);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            font-size: 14px;
        }

        .stage-controls button:hover {
            color: var(--text);
        }

        .stage-fileinfo {
            position: absolute;
            left: 14px;
            bottom: 14px;
            right: 60px;
            padding: 10px 12px;
            border-radius: 12px;
            background: rgba(0, 0, 0, .55);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-strong);
            font-size: 12px;
            color: var(--text-dim);
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        .stage-fileinfo .name {
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
        }

        .stage-fileinfo .pill {
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(124, 92, 255, .15);
            color: #c4b5fd;
            border: 1px solid rgba(124, 92, 255, .35);
        }

        .stage-fileinfo .pill.risk-high {
            background: rgba(239, 68, 68, .15);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, .35);
        }

        .stage-fileinfo .pill.risk-med {
            background: rgba(245, 158, 11, .15);
            color: #fcd34d;
            border-color: rgba(245, 158, 11, .35);
        }

        .stage-fileinfo .pill.risk-low {
            background: rgba(52, 211, 153, .15);
            color: #6ee7b7;
            border-color: rgba(52, 211, 153, .35);
        }

        /* Stats counter */
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-top: 60px;
        }

        .stat {
            padding: 22px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: var(--surface);
            backdrop-filter: blur(14px);
        }

        .stat .num {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -.03em;
            background: var(--grad);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .stat .lbl {
            color: var(--text-faint);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-top: 6px;
        }

        /* Score widget */
        .score-grid {
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 32px;
            margin-top: 36px;
            align-items: center;
        }

        .score-card {
            padding: 28px;
            border-radius: 20px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
            backdrop-filter: blur(16px);
        }

        .score-row {
            display: flex;
            align-items: center;
            gap: 24px;
        }

        .score-ring {
            position: relative;
            width: 160px;
            height: 160px;
            flex-shrink: 0;
        }

        .score-ring svg {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .score-ring .track {
            stroke: rgba(255, 255, 255, .06);
        }

        .score-ring .bar {
            stroke: url(#scoreGrad);
            transition: stroke-dashoffset 1.2s cubic-bezier(.2, .7, .3, 1);
        }

        .score-ring .center {
            position: absolute;
            inset: 0;
            display: grid;
            place-items: center;
            text-align: center;
        }

        .score-ring .num {
            font-size: 38px;
            font-weight: 800;
            letter-spacing: -.04em;
        }

        .score-ring .lbl {
            font-size: 11px;
            color: var(--text-faint);
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .score-meta {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .score-meta .item {
            padding: 12px 14px;
            border-radius: 12px;
            background: var(--surface-2);
            border: 1px solid var(--border);
        }

        .score-meta .k {
            font-size: 11px;
            color: var(--text-faint);
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .score-meta .v {
            font-size: 18px;
            font-weight: 700;
            margin-top: 4px;
        }

        .v.risk-low {
            color: var(--accent-3);
        }

        .v.risk-med {
            color: var(--warn);
        }

        .v.risk-high {
            color: var(--danger);
        }

        /* Pipeline */
        .pipeline {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-top: 40px;
        }

        .pipe-step {
            padding: 18px;
            border-radius: 14px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
            text-align: center;
            position: relative;
        }

        .pipe-step .icon {
            width: 44px;
            height: 44px;
            margin: 0 auto 12px;
            border-radius: 12px;
            background: var(--grad-soft);
            border: 1px solid var(--border-strong);
            display: grid;
            place-items: center;
            font-size: 20px;
        }

        .pipe-step.active {
            border-color: rgba(124, 92, 255, .6);
            box-shadow: 0 0 24px -6px rgba(124, 92, 255, .5);
        }

        .pipe-step.active .icon {
            background: var(--grad);
            color: #0a0a14;
        }

        .pipe-step h4 {
            margin: 0 0 4px;
            font-size: 14px;
            font-weight: 700;
        }

        .pipe-step p {
            margin: 0;
            font-size: 12px;
            color: var(--text-faint);
        }

        /* Heatmap preview */
        .heatmap-card {
            padding: 24px;
            border-radius: 20px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
        }

        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(16, 1fr);
            gap: 4px;
            margin-top: 14px;
        }

        .heat-cell {
            aspect-ratio: 1/1;
            border-radius: 4px;
            transition: transform .15s;
            cursor: pointer;
        }

        .heat-cell:hover {
            transform: scale(1.4);
            z-index: 2;
            position: relative;
        }

        .heatmap-legend {
            display: flex;
            gap: 14px;
            margin-top: 14px;
            align-items: center;
            font-size: 12px;
            color: var(--text-faint);
        }

        .heatmap-legend .swatch {
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 4px;
            margin-right: 6px;
            vertical-align: middle;
        }

        /* AI panel */
        .ai-panel {
            padding: 24px;
            border-radius: 20px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
        }

        .ai-row {
            display: flex;
            gap: 12px;
            padding: 12px 0;
            border-top: 1px solid var(--border);
        }

        .ai-row:first-of-type {
            border-top: 0;
            padding-top: 0;
        }

        .ai-row .badge {
            flex-shrink: 0;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            height: max-content;
        }

        .badge.high {
            background: rgba(239, 68, 68, .15);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, .3);
        }

        .badge.med {
            background: rgba(245, 158, 11, .15);
            color: #fcd34d;
            border: 1px solid rgba(245, 158, 11, .3);
        }

        .ai-row .body .file {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: var(--text);
            margin-bottom: 4px;
        }

        .ai-row .body .reason {
            font-size: 13px;
            color: var(--text-dim);
        }

        /* Compare */
        .compare-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 36px;
        }

        .compare-card {
            padding: 24px;
            border-radius: 18px;
            border: 1px solid var(--border);
            background: var(--surface);
        }

        .compare-card.ours {
            border-color: rgba(124, 92, 255, .45);
            box-shadow: 0 20px 60px -30px rgba(124, 92, 255, .5);
            position: relative;
        }

        .compare-card.ours::before {
            content: 'DevCity AI';
            position: absolute;
            top: -10px;
            right: 16px;
            background: var(--grad);
            color: #0a0a14;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
        }

        .compare-card h4 {
            margin: 0 0 8px;
            font-size: 16px;
            font-weight: 700;
        }

        .compare-card .feat {
            display: flex;
            gap: 8px;
            padding: 8px 0;
            font-size: 13px;
            color: var(--text-dim);
            border-top: 1px solid var(--border);
        }

        .compare-card .feat:first-of-type {
            border-top: 0;
        }

        .compare-card .feat svg {
            width: 16px;
            height: 16px;
            flex-shrink: 0;
            margin-top: 1px;
        }

        .feat.yes svg {
            color: var(--accent-3);
        }

        .feat.no svg {
            color: var(--text-faint);
        }

        /* GitHub repo preview */
        .gh-preview {
            padding: 24px;
            border-radius: 18px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
        }

        .gh-row {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
            margin-top: 8px;
        }

        .gh-row.blurred {
            filter: blur(4px);
            opacity: .7;
        }

        .gh-row:nth-child(odd) {
            background: var(--surface-2);
        }

        .gh-row .repo-name {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            flex: 1;
        }

        .gh-row .meta {
            font-size: 12px;
            color: var(--text-faint);
            display: flex;
            gap: 12px;
        }

        .gh-overlay {
            position: absolute;
            inset: 0;
            display: grid;
            place-items: center;
            padding: 20px;
            text-align: center;
            background: linear-gradient(180deg, rgba(5, 6, 10, .4) 0%, rgba(5, 6, 10, .85) 100%);
            border-radius: 18px;
        }

        /* Onboarding */
        .steps {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-top: 36px;
        }

        .step {
            padding: 22px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: var(--surface);
            position: relative;
        }

        .step .n {
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-2);
            letter-spacing: .12em;
        }

        .step h4 {
            margin: 8px 0 6px;
            font-size: 16px;
            font-weight: 700;
        }

        .step p {
            margin: 0;
            font-size: 13px;
            color: var(--text-dim);
        }

        /* Final CTA */
        .final-cta {
            margin: 40px 0 80px;
            padding: 56px 28px;
            border-radius: 28px;
            border: 1px solid var(--border-strong);
            background: var(--surface);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .final-cta::before {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(80% 70% at 50% 0%, rgba(124, 92, 255, .25), transparent 60%);
            pointer-events: none;
        }

        .final-cta h2 {
            position: relative;
        }

        .final-cta .lead {
            position: relative;
        }

        .final-cta .actions {
            position: relative;
            margin-top: 28px;
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }

        footer {
            padding: 30px 0 60px;
            color: var(--text-faint);
            font-size: 13px;
            text-align: center;
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }

        /* Command bar */
        .cmd-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, .55);
            backdrop-filter: blur(6px);
            z-index: 100;
            display: none;
            align-items: flex-start;
            justify-content: center;
            padding-top: 14vh;
        }

        .cmd-overlay.open {
            display: flex;
        }

        .cmd-box {
            width: min(560px, 92vw);
            border-radius: 16px;
            border: 1px solid var(--border-strong);
            background: rgba(15, 19, 33, .92);
            backdrop-filter: blur(20px);
            overflow: hidden;
            box-shadow: 0 30px 80px -20px rgba(0, 0, 0, .7);
        }

        .cmd-input {
            width: 100%;
            background: transparent;
            border: 0;
            outline: 0;
            color: var(--text);
            padding: 18px 20px;
            font-size: 16px;
            border-bottom: 1px solid var(--border);
        }

        .cmd-list {
            max-height: 60vh;
            overflow: auto;
            padding: 6px;
        }

        .cmd-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--text-dim);
            cursor: pointer;
        }

        .cmd-item.active,
        .cmd-item:hover {
            background: var(--surface-2);
            color: var(--text);
        }

        .cmd-item .k {
            font-size: 11px;
            color: var(--text-faint);
            margin-left: auto;
            font-family: 'JetBrains Mono', monospace;
        }

        /* AI mini chat */
        .chat-fab {
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 60;
            width: 54px;
            height: 54px;
            border-radius: 50%;
            border: 0;
            background: var(--grad);
            box-shadow: 0 10px 30px -10px rgba(124, 92, 255, .7);
            color: #0a0a14;
            font-size: 22px;
            display: grid;
            place-items: center;
        }

        .chat-panel {
            position: fixed;
            right: 22px;
            bottom: 90px;
            z-index: 61;
            width: min(360px, 92vw);
            border-radius: 18px;
            border: 1px solid var(--border-strong);
            background: rgba(15, 19, 33, .92);
            backdrop-filter: blur(20px);
            display: none;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 30px 80px -20px rgba(0, 0, 0, .7);
        }

        .chat-panel.open {
            display: flex;
        }

        .chat-head {
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .chat-head .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-3);
            box-shadow: 0 0 8px var(--accent-3);
        }

        .chat-head h4 {
            margin: 0;
            font-size: 14px;
            font-weight: 700;
        }

        .chat-msgs {
            padding: 14px;
            max-height: 280px;
            overflow: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 13px;
        }

        .chat-msg {
            padding: 10px 12px;
            border-radius: 12px;
            max-width: 85%;
        }

        .chat-msg.user {
            align-self: flex-end;
            background: var(--grad-soft);
            border: 1px solid var(--border-strong);
        }

        .chat-msg.bot {
            background: var(--surface-2);
            border: 1px solid var(--border);
            color: var(--text-dim);
        }

        .chat-form {
            display: flex;
            gap: 8px;
            padding: 12px;
            border-top: 1px solid var(--border);
        }

        .chat-form input {
            flex: 1;
            background: var(--surface-2);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 9px 12px;
            border-radius: 10px;
            font-size: 13px;
            outline: none;
        }

        .chat-form input:focus {
            border-color: var(--accent);
        }

        .chat-form button {
            background: var(--grad);
            border: 0;
            color: #0a0a14;
            font-weight: 700;
            padding: 0 14px;
            border-radius: 10px;
        }

        /* Responsive */
        @media (max-width: 960px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }

            .stats {
                grid-template-columns: repeat(2, 1fr);
            }

            .score-grid {
                grid-template-columns: 1fr;
            }

            .pipeline {
                grid-template-columns: repeat(2, 1fr);
            }

            .compare-grid {
                grid-template-columns: 1fr;
            }

            .steps {
                grid-template-columns: repeat(2, 1fr);
            }

            .nav-links {
                display: none;
            }

            section {
                padding: 70px 0;
            }
        }

        @media (max-width: 560px) {
            main {
                padding: 0 16px;
            }

            .stats {
                grid-template-columns: 1fr 1fr;
            }

            .pipeline {
                grid-template-columns: 1fr;
            }

            .steps {
                grid-template-columns: 1fr;
            }

            .analyze-row {
                flex-wrap: wrap;
            }

            .analyze-row .gh-pre {
                display: none;
            }

            .hero-stage {
                aspect-ratio: 1/1;
            }

            .stage-fileinfo {
                right: 14px;
            }
        }

        /* Reveal */
        .reveal {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity .8s ease, transform .8s ease;
        }

        .reveal.in {
            opacity: 1;
            transform: none;
        }

        @media (prefers-reduced-motion: reduce) {
            .reveal {
                opacity: 1;
                transform: none;
                transition: none;
            }
        }

        /* Auth Gate */
        .hero-login-btn {
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 999px;
            background: rgba(124, 92, 255, 0.15);
            border: 1px solid rgba(124, 92, 255, 0.4);
            box-shadow: 0 10px 30px -10px rgba(124, 92, 255, 0.4);
            backdrop-filter: blur(14px);
            transition: all 0.3s ease;
            color: var(--text);
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .hero-login-btn:hover {
            box-shadow: 0 15px 40px -10px rgba(124, 92, 255, 0.6);
            transform: translateY(-2px);
            border-color: var(--accent);
            background: rgba(124, 92, 255, 0.25);
        }

        .analyze-wrapper {
            position: relative;
            margin-top: 30px;
            border-radius: 18px;
            overflow: hidden;
        }

        .login-overlay {
            position: absolute;
            inset: 0;
            z-index: 10;
            background: rgba(10, 13, 24, 0.65);
            backdrop-filter: blur(6px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 24px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            border-radius: 18px;
        }

        .analyze-wrapper.locked .analyze-card {
            opacity: 0.4;
            pointer-events: none;
        }

        .analyze-wrapper.locked .login-overlay {
            opacity: 1;
            pointer-events: auto;
        }

        /* Modals */
        .auth-modal-overlay {
            position: fixed;
            inset: 0;
            z-index: 9999;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }

        .auth-modal-overlay.open {
            opacity: 1;
            pointer-events: auto;
        }

        .auth-modal-box {
            background: var(--surface-2);
            border: 1px solid var(--border-strong);
            border-radius: 20px;
            padding: 32px;
            width: min(400px, 92vw);
            text-align: center;
            position: relative;
            transform: scale(0.95);
            transition: transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
            box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.8);
        }

        .auth-modal-overlay.open .auth-modal-box {
            transform: scale(1);
        }

        .btn-close-modal {
            position: absolute;
            top: 16px;
            right: 16px;
            background: transparent;
            border: none;
            color: var(--text-faint);
            font-size: 18px;
            cursor: pointer;
            padding: 4px;
        }

        .btn-close-modal:hover {
            color: var(--text);
        }

        @media (max-width: 768px) {
            .login-overlay {
                display: none !important;
            }

            .analyze-wrapper.locked::after {
                content: '';
                position: absolute;
                inset: 0;
                z-index: 10;
                cursor: pointer;
            }

            .auth-modal-box {
                position: absolute;
                bottom: 0;
                width: 100%;
                max-width: 100%;
                border-radius: 24px 24px 0 0;
                padding-bottom: max(32px, env(safe-area-inset-bottom));
                transform: translateY(100%);
            }

            .auth-modal-overlay.open .auth-modal-box {
                transform: translateY(0);
            }
        }
    </style>
</head>

<body>
    <div class="bg-layer"></div>
    <div class="bg-grid"></div>

    <nav class="top">
        <div class="nav-inner">
            <a href="#top" class="brand">
                <div class="brand-mark"></div>
                <span>DevCity <span style="color: var(--text-faint); font-weight: 600;">AI</span></span>
            </a>
            <div class="nav-links">
                <a href="#how">How it works</a>
                <a href="#insights">AI Insights</a>
                <a href="#compare">Compare</a>
                <a href="#start">Get started</a>
            </div>
            <div class="nav-spacer"></div>
            <div class="mode-toggle" role="tablist" aria-label="UI mode">
                <button class="active" data-mode="developer">Developer</button>
                <button data-mode="product">Product</button>
            </div>
            <button class="btn btn-sm" id="cmdBtn" aria-label="Open command bar">
                <span>⌘</span><span>Search</span><span class="kbd">/</span>
            </button>
            <a class="btn btn-sm btn-primary" href="#analyze">Launch app</a>
        </div>
    </nav>

    <main id="top">

        <!-- HERO -->
        <section class="hero">
            <div class="hero-grid">
                <div class="reveal">
                    <span class="eyebrow"><span class="dot"></span> Code intelligence, reimagined</span>
                    <h1 style="margin-top: 18px;">See your code as a <span class="gradient-text">3D city.</span></h1>
                    <p class="lead">DevCity AI turns any GitHub repository into an interactive city of buildings — each
                        file scaled by complexity, colored by risk, and explained by AI.</p>

                    <!-- GITHUB LOGIN BUTTON (HERO) -->
                    <div id="heroLoginArea" style="margin-top: 28px; display: none;">
                        <button class="hero-login-btn github-login-btn">
                            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                                <path
                                    d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.1.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.36-2.22-.26-4.55-1.14-4.55-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.4 9.4 0 0 1 12 6.84a9.4 9.4 0 0 1 2.5.34c1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.81-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.27 10.27 0 0 0 22 12.26C22 6.58 17.52 2 12 2z">
                                </path>
                            </svg>
                            Sign in with GitHub
                        </button>
                    </div>

                    <!-- USER PROFILE / LOGGED IN STATE -->
                    <div id="heroUserArea" style="margin-top: 28px; display: none; align-items: center; gap: 14px;">
                        <img id="userAvatar" src="" alt="Avatar"
                            style="width: 44px; height: 44px; border-radius: 50%; border: 2px solid var(--border-strong); box-shadow: var(--shadow-glow);" />
                        <div>
                            <div id="userName" style="font-weight: 700; font-size: 16px; color: var(--text);"></div>
                            <a href="/logout"
                                style="font-size: 13px; color: var(--text-faint); text-decoration: underline;">Sign
                                out</a>
                        </div>
                    </div>

                    <div class="analyze-wrapper locked" id="analyzeWrapper">
                        <form class="analyze-card" id="analyzeForm" autocomplete="off" style="margin-top: 0;">
                            <div class="analyze-row">
                                <span class="gh-pre">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                        <path
                                            d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.1.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.36-2.22-.26-4.55-1.14-4.55-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.4 9.4 0 0 1 12 6.84a9.4 9.4 0 0 1 2.5.34c1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.81-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.27 10.27 0 0 0 22 12.26C22 6.58 17.52 2 12 2z" />
                                    </svg>
                                    <span>github.com/</span>
                                </span>
                                <input class="analyze-input" id="repoInput" type="text" placeholder="vercel/next.js"
                                    spellcheck="false" />
                                <button class="btn btn-primary" id="analyzeBtn" type="submit">Analyze repo</button>
                            </div>
                            <div class="sample-row">
                                <span style="font-size: 12px; color: var(--text-faint); padding: 6px 0;">Try:</span>
                                <button class="chip" type="button" data-sample="facebook/react">⚛️ React</button>
                                <button class="chip" type="button" data-sample="expressjs/express">🟢 Node
                                    backend</button>
                                <button class="chip" type="button" data-sample="huggingface/transformers">🤖 AI
                                    project</button>
                                <button class="chip" type="button" data-sample="tailwindlabs/tailwindcss">🎨
                                    Tailwind</button>
                            </div>
                            <div class="analyze-status" id="analyzeStatus"></div>
                        </form>

                        <!-- DESKTOP OVERLAY -->
                        <div id="analyzeOverlay" class="login-overlay">
                            <p style="margin: 0 0 14px; font-weight: 600; font-size: 15px; color: var(--text);">Sign in
                                with GitHub to analyze repositories and generate your AI Code City</p>
                            <button class="btn btn-primary github-login-btn">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                                    <path
                                        d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.1.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.36-2.22-.26-4.55-1.14-4.55-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.4 9.4 0 0 1 12 6.84a9.4 9.4 0 0 1 2.5.34c1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.81-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.27 10.27 0 0 0 22 12.26C22 6.58 17.52 2 12 2z">
                                    </path>
                                </svg>
                                Continue with GitHub
                            </button>
                        </div>
                    </div> <!-- /analyze-wrapper -->

                    <div class="hero-trust">
                        <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <path d="M5 12l5 5L20 7" />
                            </svg> No signup to demo</span>
                        <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <path d="M5 12l5 5L20 7" />
                            </svg> Public repos out of the box</span>
                        <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <path d="M5 12l5 5L20 7" />
                            </svg> AI insights</span>
                    </div>
                </div>

                <!-- 3D HERO STAGE -->
                <div class="hero-stage reveal" id="heroStage">
                    <span class="stage-badge">LIVE 3D • Drag to rotate</span>
                    <canvas id="heroCanvas"></canvas>
                    <div class="stage-overlay"></div>
                    <div class="stage-tooltip" id="stageTooltip"></div>
                    <div class="stage-fileinfo" id="stageInfo">
                        <span class="name">src/app/page.tsx</span>
                        <span class="pill">324 LOC</span>
                        <span class="pill risk-low">Healthy</span>
                    </div>
                    <div class="stage-controls">
                        <button id="stageReset" title="Reset view">⟲</button>
                        <button id="stageFly" title="Fly through">▶</button>
                    </div>
                </div>
            </div>

            <!-- LIVE STATS -->
            <div class="stats">
                <div class="stat reveal">
                    <div class="num" data-count="48329">0</div>
                    <div class="lbl">Repositories analyzed</div>
                </div>
                <div class="stat reveal">
                    <div class="num" data-count="14823490">0</div>
                    <div class="lbl">Files processed</div>
                </div>
                <div class="stat reveal">
                    <div class="num" data-count="9217">0</div>
                    <div class="lbl">Active developers</div>
                </div>
                <div class="stat reveal">
                    <div class="num" data-count="38" data-suffix="%">0</div>
                    <div class="lbl">Avg risk reduction</div>
                </div>
            </div>
        </section>

        <!-- AI SCORE WIDGET -->
        <section id="insights" class="reveal">
            <span class="eyebrow"><span class="dot"
                    style="background: var(--accent-2); box-shadow: 0 0 10px var(--accent-2);"></span> AI repo
                score</span>
            <h2 style="margin-top: 14px;">Health, risk &amp; tech debt — <span class="gradient-text">scored
                    instantly.</span></h2>
            <p class="lead">Every repo gets an objective health score, a risk grade, and AI-written summaries you can
                ship to your standup.</p>

            <div class="score-grid">
                <div class="score-card">
                    <div class="score-row">
                        <div class="score-ring">
                            <svg viewBox="0 0 120 120" aria-hidden="true">
                                <defs>
                                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
                                        <stop offset="0%" stop-color="#7c5cff" />
                                        <stop offset="60%" stop-color="#22d3ee" />
                                        <stop offset="100%" stop-color="#34d399" />
                                    </linearGradient>
                                </defs>
                                <circle class="track" cx="60" cy="60" r="50" fill="none" stroke-width="10" />
                                <circle class="bar" id="scoreBar" cx="60" cy="60" r="50" fill="none" stroke-width="10"
                                    stroke-linecap="round" stroke-dasharray="314.159" stroke-dashoffset="314.159" />
                            </svg>
                            <div class="center">
                                <div class="num" id="scoreNum">82</div>
                                <div class="lbl">Health</div>
                            </div>
                        </div>
                        <div class="score-meta">
                            <div class="item">
                                <div class="k">Risk level</div>
                                <div class="v risk-low" id="scoreRisk">Low</div>
                            </div>
                            <div class="item">
                                <div class="k">Complexity</div>
                                <div class="v" id="scoreCx">B+</div>
                            </div>
                            <div class="item">
                                <div class="k">Tech debt</div>
                                <div class="v" id="scoreDebt">Moderate</div>
                            </div>
                            <div class="item">
                                <div class="k">Files scanned</div>
                                <div class="v" id="scoreFiles">412</div>
                            </div>
                        </div>
                    </div>
                    <p style="color: var(--text-dim); font-size: 13px; line-height: 1.55; margin: 18px 0 0;"
                        id="scoreSummary">
                        This repo follows a clean modular structure. Two hot files in <code
                            class="mono">src/core/</code> account for ~38% of the risk — see suggestions on the right.
                    </p>
                </div>

                <!-- HEATMAP -->
                <div class="heatmap-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Risk heatmap</h3>
                        <span style="font-size: 12px; color: var(--text-faint);">Hover a tile</span>
                    </div>
                    <div class="heatmap-grid" id="heatmapGrid"></div>
                    <div class="heatmap-legend">
                        <span><span class="swatch" style="background: #34d399;"></span>Healthy</span>
                        <span><span class="swatch" style="background: #f59e0b;"></span>Watch</span>
                        <span><span class="swatch" style="background: #ef4444;"></span>Risky</span>
                        <span style="margin-left: auto;" id="heatHover">—</span>
                    </div>
                </div>
            </div>

            <!-- AI INSIGHT PREVIEW -->
            <div class="ai-panel reveal" style="margin-top: 22px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <h3 style="display:inline-flex; align-items:center; gap:8px;">
                        <span
                            style="width:8px; height:8px; border-radius:50%; background: var(--accent); box-shadow:0 0 10px var(--accent);"></span>
                        AI insight preview
                    </h3>
                    <span style="font-size:11px; color: var(--text-faint); margin-left:auto;">Sample output</span>
                </div>
                <div class="ai-row">
                    <span class="badge high">HIGH</span>
                    <div class="body">
                        <div class="file">src/core/scheduler.ts</div>
                        <div class="reason">Cyclomatic complexity 47 with 12 callers. Split scheduling logic into a
                            state machine and extract retry policy.</div>
                    </div>
                </div>
                <div class="ai-row">
                    <span class="badge high">HIGH</span>
                    <div class="body">
                        <div class="file">packages/legacy/auth.js</div>
                        <div class="reason">Last meaningful change 14 months ago, no tests, used by 6 entry points. Wrap
                            in adapter and migrate consumers.</div>
                    </div>
                </div>
                <div class="ai-row">
                    <span class="badge med">MED</span>
                    <div class="body">
                        <div class="file">app/api/billing/route.ts</div>
                        <div class="reason">Mixes input validation, persistence, and webhook dispatch. Extract domain
                            layer to clarify failure modes.</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- HOW IT WORKS -->
        <section id="how" class="reveal">
            <div class="center">
                <span class="eyebrow"><span class="dot"></span> How it works</span>
                <h2 style="margin-top: 14px;">From repo to <span class="gradient-text">city</span> in seconds.</h2>
                <p class="lead">A purpose-built pipeline that scans your tree, scores each file, and renders a navigable
                    3D model of your codebase.</p>
            </div>
            <div class="pipeline" id="pipeline">
                <div class="pipe-step active">
                    <div class="icon">🐙</div>
                    <h4>GitHub Repo</h4>
                    <p>Paste a URL. Public repos work instantly.</p>
                </div>
                <div class="pipe-step">
                    <div class="icon">🔍</div>
                    <h4>AI Scanner</h4>
                    <p>Walks the tree, parses files, scores risk.</p>
                </div>
                <div class="pipe-step">
                    <div class="icon">🏙️</div>
                    <h4>City Generator</h4>
                    <p>Maps folders to districts, files to buildings.</p>
                </div>
                <div class="pipe-step">
                    <div class="icon">🔥</div>
                    <h4>Risk Map</h4>
                    <p>Color, height &amp; glow visualize hotspots.</p>
                </div>
                <div class="pipe-step">
                    <div class="icon">🧠</div>
                    <h4>Insights</h4>
                    <p>AI explains what to refactor first.</p>
                </div>
            </div>
        </section>

        <!-- COMPARE -->
        <section id="compare" class="reveal">
            <div class="center">
                <span class="eyebrow"><span class="dot"></span> Why DevCity AI</span>
                <h2 style="margin-top: 14px;">The only tool that <span class="gradient-text">shows you the shape</span>
                    of your codebase.</h2>
            </div>
            <div class="compare-grid">
                <div class="compare-card">
                    <h4>GitHub</h4>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> Source hosting</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> No 3D visualization</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> No risk explanations</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> No snapshot timeline</div>
                </div>
                <div class="compare-card">
                    <h4>SonarQube</h4>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> Static analysis</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> Tables &amp; charts only</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> Heavy onboarding</div>
                    <div class="feat no"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg> No AI summaries</div>
                </div>
                <div class="compare-card ours">
                    <h4>DevCity AI</h4>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> Interactive 3D city</div>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> AI risk &amp; refactor insights</div>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> Snapshot timeline &amp; diffs</div>
                    <div class="feat yes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M5 12l5 5L20 7" />
                        </svg> Zero-config — paste &amp; go</div>
                </div>
            </div>
        </section>

        <!-- GITHUB PREVIEW -->
        <section class="reveal">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center;"
                class="gh-section-grid">
                <div>
                    <span class="eyebrow"><span class="dot"></span> GitHub access (preview)</span>
                    <h2 style="margin-top: 14px;">Connect your repos, <span class="gradient-text">when you're
                            ready.</span></h2>
                    <p class="lead">DevCity AI works on public repos out of the box. To analyze private repos, sign in
                        with GitHub. We request <strong>read-only</strong> access to repository contents — never write.
                    </p>
                    <ul style="color: var(--text-dim); font-size: 14px; line-height: 1.8; padding-left: 20px;">
                        <li>✅ Read repository contents (files &amp; metadata)</li>
                        <li>✅ List repositories you select</li>
                        <li>🔒 No write access, no commits, no PRs</li>
                        <li>🗑 Revoke any time from your GitHub settings</li>
                    </ul>
                </div>
                <div class="gh-preview" id="ghPreviewContainer" style="position: relative;">
                    <div class="gh-row blurred"><span class="repo-name">your-org/payments-api</span><span class="meta"><span>★
                                1.2k</span><span>TypeScript</span></span></div>
                    <div class="gh-row blurred"><span class="repo-name">your-org/web-app</span><span class="meta"><span>★
                                842</span><span>React</span></span></div>
                    <div class="gh-row blurred"><span class="repo-name">your-org/data-pipelines</span><span class="meta"><span>★
                                318</span><span>Python</span></span></div>
                    <div class="gh-row blurred"><span class="repo-name">your-org/infra</span><span class="meta"><span>★
                                98</span><span>Terraform</span></span></div>
                    <div class="gh-overlay">
                        <div>
                            <div style="font-size: 32px; margin-bottom: 8px;">🔒</div>
                            <div style="font-weight: 700; margin-bottom: 6px;">Sign in to view your repos</div>
                            <div style="color: var(--text-dim); font-size: 13px; margin-bottom: 14px;">Read-only ·
                                Revocable · Open source.</div>
                            <button class="btn btn-primary btn-sm github-login-btn" type="button">Connect GitHub
                                Account</button>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ONBOARDING -->
        <section id="start" class="reveal">
            <div class="center">
                <span class="eyebrow"><span class="dot"></span> Get started</span>
                <h2 style="margin-top: 14px;">Four steps to your <span class="gradient-text">code city.</span></h2>
            </div>
            <div class="steps">
                <div class="step">
                    <div class="n">STEP 01</div>
                    <h4>Paste a repo</h4>
                    <p>Drop a GitHub URL or pick a sample.</p>
                </div>
                <div class="step">
                    <div class="n">STEP 02</div>
                    <h4>Choose a mode</h4>
                    <p>Risk, complexity, or anomaly view.</p>
                </div>
                <div class="step">
                    <div class="n">STEP 03</div>
                    <h4>Generate the city</h4>
                    <p>We build a 3D model in seconds.</p>
                </div>
                <div class="step">
                    <div class="n">STEP 04</div>
                    <h4>Explore &amp; refactor</h4>
                    <p>Use AI insights to ship cleaner code.</p>
                </div>
            </div>

            <div class="final-cta">
                <span class="eyebrow"><span class="dot"></span> Ready when you are</span>
                <h2 style="margin: 14px 0 10px;">Turn your repo into a <span class="gradient-text">3D city</span> right
                    now.</h2>
                <p class="lead" style="margin: 0 auto;">Free demo on any public GitHub repository. No signup, no credit
                    card.</p>
                <div class="actions">
                    <a href="#analyze" class="btn btn-primary"
                        onclick="document.getElementById('repoInput').focus(); return false;">Analyze a repo →</a>
                    <a href="/city" class="btn">Open last analysis</a>
                </div>
            </div>
        </section>

        <footer>
            <div>DevCity AI<a href="https://github.com" style="color: var(--text-dim);">github</a></div>
        </footer>
    </main>

    <!-- FAB chat -->
    <button class="chat-fab" id="chatFab" aria-label="Ask DevCity AI">💬</button>
    <div class="chat-panel" id="chatPanel" role="dialog" aria-label="DevCity AI chat">
        <div class="chat-head"><span class="dot"></span>
            <h4>Ask DevCity AI</h4><span style="font-size:11px; color: var(--text-faint); margin-left:auto;">Demo</span>
        </div>
        <div class="chat-msgs" id="chatMsgs">
            <div class="chat-msg bot">Hi! Ask me anything about a repository's risk or what to refactor first.</div>
        </div>
        <form class="chat-form" id="chatForm">
            <input id="chatInput" placeholder="e.g. Which file is risky?" />
            <button type="submit">Send</button>
        </form>
    </div>

    <!-- Command bar -->
    <div class="cmd-overlay" id="cmdOverlay" role="dialog" aria-label="Command bar">
        <div class="cmd-box">
            <input class="cmd-input" id="cmdInput" placeholder="Search features, jump sections, run demo…" />
            <div class="cmd-list" id="cmdList"></div>
        </div>
    </div>

    <!-- Auth Modal -->
    <div class="auth-modal-overlay" id="authModal">
        <div class="auth-modal-box">
            <button class="btn-close-modal" id="closeAuthModal" aria-label="Close modal">✕</button>
            <div style="font-size: 32px; margin-bottom: 12px;">🔒</div>
            <h3 style="margin-bottom: 8px;">Authentication Required</h3>
            <p style="color: var(--text-dim); font-size: 14px; margin-bottom: 24px;">Please sign in with GitHub to
                access repository analysis features.</p>
            <button class="btn btn-primary github-login-btn" style="width: 100%; justify-content: center;">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                    <path
                        d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.1.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.36-3.37-1.36-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.36-2.22-.26-4.55-1.14-4.55-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.4 9.4 0 0 1 12 6.84a9.4 9.4 0 0 1 2.5.34c1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.81-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.27 10.27 0 0 0 22 12.26C22 6.58 17.52 2 12 2z">
                    </path>
                </svg>
                Sign in with GitHub
            </button>
        </div>
    </div>

    <script src="https://unpkg.com/three@0.136.0/build/three.min.js"></script>
    <script>
        /* =====================  AUTH LOGIC  ===================== */
        const authState = { isAuthenticated: false, user: null };

        async function checkAuth() {
            try {
                const res = await fetch('/api/me');
                if (res.ok) {
                    const data = await res.json();
                    authState.isAuthenticated = !!data.authenticated;
                    authState.user = data.user || null;
                } else {
                    authState.isAuthenticated = false;
                }
            } catch (err) {
                authState.isAuthenticated = false;
            }
            updateUIForAuth();
        }

        function updateUIForAuth() {
            const loginArea = document.getElementById('heroLoginArea');
            const userArea = document.getElementById('heroUserArea');
            const wrapper = document.getElementById('analyzeWrapper');

            if (authState.isAuthenticated) {
                if (loginArea) loginArea.style.display = 'none';
                if (userArea) userArea.style.display = 'flex';
                if (wrapper) wrapper.classList.remove('locked');

                if (authState.user) {
                    const nameEl = document.getElementById('userName');
                    const avatarEl = document.getElementById('userAvatar');
                    if (nameEl) nameEl.textContent = authState.user.name || authState.user.login;
                    if (avatarEl) avatarEl.src = authState.user.avatar_url;
                }

                const ghOverlay = document.querySelector('.gh-overlay');
                if (ghOverlay) ghOverlay.style.display = 'none';

                fetch('/api/my_repos')
                    .then(res => res.json())
                    .then(repos => {
                        const container = document.getElementById('ghPreviewContainer');
                        if (container && Array.isArray(repos)) {
                            container.querySelectorAll('.gh-row').forEach(e => e.remove());
                            repos.slice(0, 4).forEach(repo => {
                                const row = document.createElement('div');
                                row.className = 'gh-row';
                                row.style.cursor = 'pointer';
                                row.innerHTML = `<span class="repo-name" style="flex:1;">${repo.full_name}</span><span class="meta"><span>★ ${repo.stargazers_count || 0}</span><span>${repo.language || 'Unknown'}</span></span>`;
                                row.onclick = () => {
                                    const repoInput = document.getElementById('repoInput');
                                    if (repoInput) {
                                        repoInput.value = repo.full_name;
                                        document.getElementById('analyzeForm').requestSubmit();
                                        window.scrollTo({ top: 0, behavior: 'smooth' });
                                    }
                                };
                                container.appendChild(row);
                            });
                        }
                    })
                    .catch(err => console.error('Failed to fetch repos', err));
            } else {
                if (loginArea) loginArea.style.display = 'block';
                if (userArea) userArea.style.display = 'none';
                if (wrapper) wrapper.classList.add('locked');
                
                const ghOverlay = document.querySelector('.gh-overlay');
                if (ghOverlay) ghOverlay.style.display = 'grid';
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            checkAuth();

            // Login buttons routing
            document.body.addEventListener('click', (e) => {
                const loginBtn = e.target.closest('.github-login-btn');
                if (loginBtn) {
                    e.preventDefault();
                    window.location.href = '/login';
                }
            });

            // Close modal button
            const closeModalBtn = document.getElementById('closeAuthModal');
            if (closeModalBtn) {
                closeModalBtn.addEventListener('click', () => {
                    const modal = document.getElementById('authModal');
                    if (modal) modal.classList.remove('open');
                });
            }
        });

        /* =====================  HERO 3D SCENE  ===================== */
        (function initHero() {
            const canvas = document.getElementById('heroCanvas');
            const stage = document.getElementById('heroStage');
            const tooltip = document.getElementById('stageTooltip');
            const info = document.getElementById('stageInfo');
            if (!canvas || !window.THREE) return;

            const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            renderer.setClearColor(0x000000, 0);

            const scene = new THREE.Scene();
            scene.fog = new THREE.Fog(0x05060a, 80, 220);

            const camera = new THREE.PerspectiveCamera(45, 1, 1, 600);
            const baseCamPos = new THREE.Vector3(80, 70, 80);
            camera.position.copy(baseCamPos);
            camera.lookAt(0, 0, 0);

            // Lights
            scene.add(new THREE.AmbientLight(0x6677aa, 0.55));
            const key = new THREE.DirectionalLight(0xa78bfa, 0.9);
            key.position.set(40, 80, 30);
            scene.add(key);
            const rim = new THREE.DirectionalLight(0x22d3ee, 0.5);
            rim.position.set(-40, 50, -40);
            scene.add(rim);

            // Ground
            const ground = new THREE.Mesh(
                new THREE.CircleGeometry(110, 48),
                new THREE.MeshBasicMaterial({ color: 0x0a0d18, transparent: true, opacity: 0.85 })
            );
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.1;
            scene.add(ground);

            // Grid
            const grid = new THREE.GridHelper(160, 32, 0x1a2440, 0x0f1424);
            grid.position.y = 0;
            scene.add(grid);

            // Buildings - sample repo
            const sample = [
                { name: 'app/page.tsx', loc: 320, risk: 0.18 },
                { name: 'app/layout.tsx', loc: 180, risk: 0.10 },
                { name: 'components/Header.tsx', loc: 220, risk: 0.22 },
                { name: 'components/Footer.tsx', loc: 90, risk: 0.08 },
                { name: 'lib/api.ts', loc: 410, risk: 0.55 },
                { name: 'lib/auth.ts', loc: 280, risk: 0.74 },
                { name: 'lib/db.ts', loc: 360, risk: 0.62 },
                { name: 'lib/utils.ts', loc: 140, risk: 0.12 },
                { name: 'core/scheduler.ts', loc: 540, risk: 0.92 },
                { name: 'core/queue.ts', loc: 320, risk: 0.68 },
                { name: 'core/worker.ts', loc: 270, risk: 0.45 },
                { name: 'core/cache.ts', loc: 200, risk: 0.30 },
                { name: 'pages/index.tsx', loc: 240, risk: 0.20 },
                { name: 'pages/dashboard.tsx', loc: 380, risk: 0.40 },
                { name: 'styles/global.css', loc: 110, risk: 0.05 },
                { name: 'tests/api.test.ts', loc: 160, risk: 0.10 },
                { name: 'tests/auth.test.ts', loc: 130, risk: 0.08 },
                { name: 'utils/date.ts', loc: 70, risk: 0.05 },
                { name: 'utils/string.ts', loc: 60, risk: 0.05 },
                { name: 'hooks/useAuth.ts', loc: 150, risk: 0.25 },
                { name: 'hooks/useApi.ts', loc: 180, risk: 0.30 },
                { name: 'config/env.ts', loc: 60, risk: 0.10 },
                { name: 'types/index.ts', loc: 90, risk: 0.05 },
                { name: 'middleware.ts', loc: 130, risk: 0.35 },
                { name: 'public/sw.js', loc: 220, risk: 0.50 },
            ];

            function lerp(a, b, t) { return a + (b - a) * t; }
            function riskColor(r) {
                // green -> yellow -> red
                if (r < 0.5) {
                    const t = r / 0.5;
                    return new THREE.Color(lerp(0.20, 0.96, t), lerp(0.83, 0.62, t), lerp(0.46, 0.04, t));
                }
                const t = (r - 0.5) / 0.5;
                return new THREE.Color(lerp(0.96, 0.94, t), lerp(0.62, 0.27, t), lerp(0.04, 0.27, t));
            }

            const buildings = [];
            const cols = 5;
            const spacing = 11;
            sample.forEach((f, i) => {
                const x = (i % cols - (cols - 1) / 2) * spacing;
                const z = (Math.floor(i / cols) - 2) * spacing;
                const w = 5 + Math.sqrt(f.loc) * 0.18;
                const h = 4 + f.loc * 0.04 + f.risk * 18;
                const d = w;
                const color = riskColor(f.risk);
                const geom = new THREE.BoxGeometry(w, h, d);
                const mat = new THREE.MeshPhongMaterial({
                    color, shininess: 30, specular: 0x222244, transparent: true, opacity: 0.95
                });
                const mesh = new THREE.Mesh(geom, mat);
                mesh.position.set(x, h / 2, z);
                mesh.userData = { ...f, baseY: h / 2, baseColor: color.clone() };
                scene.add(mesh);
                buildings.push(mesh);

                // glowing top edge
                const edges = new THREE.LineSegments(
                    new THREE.EdgesGeometry(geom),
                    new THREE.LineBasicMaterial({ color: 0x7c5cff, transparent: true, opacity: 0.18 })
                );
                edges.position.copy(mesh.position);
                scene.add(edges);
            });

            // Sizing
            function resize() {
                const r = stage.getBoundingClientRect();
                renderer.setSize(r.width, r.height, false);
                camera.aspect = r.width / r.height;
                camera.updateProjectionMatrix();
            }
            resize();
            new ResizeObserver(resize).observe(stage);

            // Mouse / drag
            let dragging = false, lastX = 0, lastY = 0, theta = Math.PI / 4, phi = Math.PI / 4, radius = baseCamPos.length();
            let target = new THREE.Vector3(0, 0, 0);
            function applyCam() {
                camera.position.x = target.x + radius * Math.sin(phi) * Math.cos(theta);
                camera.position.z = target.z + radius * Math.sin(phi) * Math.sin(theta);
                camera.position.y = target.y + radius * Math.cos(phi);
                camera.lookAt(target);
            }
            applyCam();

            function ptr(e) { const t = e.touches ? e.touches[0] : e; return { x: t.clientX, y: t.clientY }; }
            canvas.addEventListener('mousedown', (e) => { dragging = true; const p = ptr(e); lastX = p.x; lastY = p.y; });
            window.addEventListener('mouseup', () => dragging = false);
            window.addEventListener('mousemove', (e) => {
                if (!dragging) return;
                const p = ptr(e);
                theta -= (p.x - lastX) * 0.005;
                phi = Math.max(0.2, Math.min(Math.PI / 2 - 0.05, phi - (p.y - lastY) * 0.005));
                lastX = p.x; lastY = p.y;
                applyCam();
            });
            canvas.addEventListener('touchstart', (e) => { dragging = true; const p = ptr(e); lastX = p.x; lastY = p.y; }, { passive: true });
            canvas.addEventListener('touchmove', (e) => {
                if (!dragging) return;
                const p = ptr(e);
                theta -= (p.x - lastX) * 0.005;
                phi = Math.max(0.2, Math.min(Math.PI / 2 - 0.05, phi - (p.y - lastY) * 0.005));
                lastX = p.x; lastY = p.y;
                applyCam();
            }, { passive: true });
            canvas.addEventListener('touchend', () => dragging = false);
            canvas.addEventListener('wheel', (e) => {
                e.preventDefault();
                radius = Math.max(50, Math.min(180, radius + e.deltaY * 0.06));
                applyCam();
            }, { passive: false });

            // Hover & click
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let hovered = null;
            let lastRay = 0;

            function setInfo(b) {
                if (!b) return;
                const f = b.userData;
                const r = f.risk;
                const cls = r > 0.66 ? 'risk-high' : r > 0.33 ? 'risk-med' : 'risk-low';
                const label = r > 0.66 ? 'High Risk' : r > 0.33 ? 'Needs Refactor' : 'Healthy';
                info.innerHTML = `<span class="name">${f.name}</span>
      <span class="pill">${f.loc} LOC</span>
      <span class="pill ${cls}">${label}</span>`;
            }

            canvas.addEventListener('mousemove', (e) => {
                const now = performance.now();
                if (now - lastRay < 50) return; // throttle
                lastRay = now;
                const r = canvas.getBoundingClientRect();
                mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
                mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
                raycaster.setFromCamera(mouse, camera);
                const hits = raycaster.intersectObjects(buildings);
                if (hits.length) {
                    const m = hits[0].object;
                    if (hovered !== m) {
                        if (hovered) hovered.material.color.copy(hovered.userData.baseColor);
                        hovered = m;
                        m.material.color.copy(m.userData.baseColor).multiplyScalar(1.4);
                    }
                    tooltip.style.opacity = 1;
                    tooltip.style.left = (e.clientX - r.left) + 'px';
                    tooltip.style.top = (e.clientY - r.top) + 'px';
                    tooltip.innerHTML = `<b>${m.userData.name}</b><br>${m.userData.loc} LOC · risk ${(m.userData.risk * 100) | 0}%`;
                } else {
                    if (hovered) hovered.material.color.copy(hovered.userData.baseColor);
                    hovered = null;
                    tooltip.style.opacity = 0;
                }
            });
            canvas.addEventListener('click', () => { if (hovered) setInfo(hovered); });
            canvas.addEventListener('mouseleave', () => {
                if (hovered) hovered.material.color.copy(hovered.userData.baseColor);
                hovered = null;
                tooltip.style.opacity = 0;
            });

            // Auto rotate when idle
            let lastInteract = performance.now();
            ['mousemove', 'mousedown', 'wheel', 'touchstart'].forEach((ev) => {
                canvas.addEventListener(ev, () => lastInteract = performance.now(), { passive: true });
            });

            // Reset & flythrough
            document.getElementById('stageReset').onclick = () => {
                theta = Math.PI / 4; phi = Math.PI / 4; radius = baseCamPos.length();
                target.set(0, 0, 0); applyCam();
            };
            let flying = false;
            document.getElementById('stageFly').onclick = () => { flying = !flying; };

            // Parallax with scroll
            let parallax = 0;
            window.addEventListener('scroll', () => {
                parallax = Math.min(80, window.scrollY * 0.05);
            }, { passive: true });

            // Animate
            let pulse = 0;
            function animate() {
                requestAnimationFrame(animate);
                const idle = performance.now() - lastInteract > 2200;
                if (idle && !dragging) theta += 0.0015;
                if (flying) {
                    theta += 0.004;
                    phi = 0.55 + Math.sin(performance.now() * 0.0003) * 0.15;
                    radius = 100 + Math.sin(performance.now() * 0.0005) * 25;
                }
                target.y = parallax * 0.04;
                applyCam();

                // pulse high risk
                pulse += 0.04;
                buildings.forEach((b) => {
                    if (b.userData.risk > 0.66) {
                        b.material.opacity = 0.85 + Math.sin(pulse + b.position.x) * 0.12;
                    }
                });
                renderer.render(scene, camera);
            }
            animate();
        })();

        /* =====================  REVEAL  ===================== */
        const io = new IntersectionObserver((es) => {
            es.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
        }, { threshold: 0.12 });
        document.querySelectorAll('.reveal').forEach(el => io.observe(el));

        /* =====================  STATS COUNTER  ===================== */
        const statsObs = new IntersectionObserver((es) => {
            es.forEach(e => {
                if (!e.isIntersecting) return;
                const el = e.target;
                const target = +el.dataset.count;
                const suffix = el.dataset.suffix || '';
                const dur = 1600;
                const start = performance.now();
                function tick(now) {
                    const t = Math.min(1, (now - start) / dur);
                    const eased = 1 - Math.pow(1 - t, 3);
                    const v = Math.floor(target * eased);
                    el.textContent = v.toLocaleString() + suffix;
                    if (t < 1) requestAnimationFrame(tick);
                }
                requestAnimationFrame(tick);
                statsObs.unobserve(el);
            });
        }, { threshold: 0.6 });
        document.querySelectorAll('[data-count]').forEach(el => statsObs.observe(el));

        /* =====================  SCORE RING  ===================== */
        (function initScore() {
            const bar = document.getElementById('scoreBar');
            const num = document.getElementById('scoreNum');
            const C = 2 * Math.PI * 50;
            bar.style.strokeDasharray = C;
            bar.style.strokeDashoffset = C;
            const obs = new IntersectionObserver((es) => {
                es.forEach(e => {
                    if (!e.isIntersecting) return;
                    const score = +num.textContent || 82;
                    bar.style.strokeDashoffset = C * (1 - score / 100);
                    obs.disconnect();
                });
            }, { threshold: 0.5 });
            obs.observe(bar);
        })();

        /* =====================  HEATMAP  ===================== */
        (function initHeatmap() {
            const grid = document.getElementById('heatmapGrid');
            const hover = document.getElementById('heatHover');
            const cells = 16 * 8;
            const dirs = ['app', 'lib', 'core', 'hooks', 'utils', 'tests', 'config', 'styles'];
            const files = ['index', 'page', 'route', 'auth', 'db', 'cache', 'queue', 'scheduler', 'utils', 'header', 'footer', 'api', 'worker', 'env'];
            for (let i = 0; i < cells; i++) {
                const r = Math.pow(Math.random(), 1.6); // skew toward green
                const c = document.createElement('div');
                c.className = 'heat-cell';
                c.style.background = (function () {
                    if (r < 0.5) {
                        const t = r / 0.5;
                        const g = Math.round(0.83 * 255 + (0.62 - 0.83) * 255 * t);
                        const rd = Math.round(0.20 * 255 + (0.96 - 0.20) * 255 * t);
                        const b = Math.round(0.46 * 255 + (0.04 - 0.46) * 255 * t);
                        return `rgb(${rd},${g},${b})`;
                    }
                    const t = (r - 0.5) / 0.5;
                    const rd = Math.round(0.96 * 255 + (0.94 - 0.96) * 255 * t);
                    const g = Math.round(0.62 * 255 + (0.27 - 0.62) * 255 * t);
                    const b = Math.round(0.04 * 255 + (0.27 - 0.04) * 255 * t);
                    return `rgb(${rd},${g},${b})`;
                })();
                c.style.opacity = 0.55 + r * 0.45;
                const dir = dirs[i % dirs.length];
                const f = files[(i * 7) % files.length];
                c.dataset.label = `${dir}/${f}.ts · risk ${(r * 100) | 0}%`;
                c.addEventListener('mouseenter', () => hover.textContent = c.dataset.label);
                grid.appendChild(c);
            }
        })();

        /* =====================  PIPELINE STEP CYCLE  ===================== */
        (function initPipeline() {
            const steps = document.querySelectorAll('#pipeline .pipe-step');
            let i = 0;
            setInterval(() => {
                steps.forEach(s => s.classList.remove('active'));
                steps[i].classList.add('active');
                i = (i + 1) % steps.length;
            }, 1700);
        })();

        /* =====================  MODE TOGGLE  ===================== */
        document.querySelectorAll('.mode-toggle button').forEach(b => {
            b.onclick = () => {
                document.querySelectorAll('.mode-toggle button').forEach(x => x.classList.remove('active'));
                b.classList.add('active');
                document.body.classList.toggle('product-mode', b.dataset.mode === 'product');
            };
        });

        /* =====================  ANALYZE FORM  ===================== */
        (function initAnalyze() {
            const form = document.getElementById('analyzeForm');
            const input = document.getElementById('repoInput');
            const btn = document.getElementById('analyzeBtn');
            const status = document.getElementById('analyzeStatus');
            const scoreNum = document.getElementById('scoreNum');
            const scoreBar = document.getElementById('scoreBar');
            const scoreRisk = document.getElementById('scoreRisk');
            const scoreCx = document.getElementById('scoreCx');
            const scoreDebt = document.getElementById('scoreDebt');
            const scoreFiles = document.getElementById('scoreFiles');
            const scoreSummary = document.getElementById('scoreSummary');
            const C = 2 * Math.PI * 50;

            document.querySelectorAll('[data-sample]').forEach(b => {
                b.onclick = (e) => {
                    if (!authState.isAuthenticated) {
                        e.preventDefault();
                        e.stopPropagation();
                        document.getElementById('authModal').classList.add('open');
                        return;
                    }
                    input.value = b.dataset.sample;
                    input.focus();
                };
            });

            function setStatus(text, kind) {
                status.className = 'analyze-status' + (kind ? ' ' + kind : '');
                status.innerHTML = (kind === 'loading' ? '<span class="spinner"></span>' : '') + text;
            }

            function applyInsights(d) {
                const ins = d.insights;
                if (!ins) return;
                const score = Math.max(0, Math.min(100, Math.round(ins.health_score)));
                scoreNum.textContent = score;
                scoreBar.style.strokeDashoffset = C * (1 - score / 100);
                scoreRisk.textContent = ins.risk_level || '—';
                scoreRisk.className = 'v ' + (ins.risk_level === 'High' ? 'risk-high' : ins.risk_level === 'Medium' ? 'risk-med' : 'risk-low');
                scoreCx.textContent = ins.complexity_grade || '—';
                scoreDebt.textContent = ins.tech_debt || '—';
                scoreFiles.textContent = (d.files || []).length;
                if (ins.summary) scoreSummary.textContent = ins.summary;
                // top risks → ai panel
                const panel = document.querySelector('.ai-panel');
                if (panel && Array.isArray(ins.top_risks) && ins.top_risks.length) {
                    panel.querySelectorAll('.ai-row').forEach(r => r.remove());
                    ins.top_risks.slice(0, 4).forEach((r, i) => {
                        const row = document.createElement('div');
                        row.className = 'ai-row';
                        row.innerHTML = `<span class="badge ${i < 2 ? 'high' : 'med'}">${i < 2 ? 'HIGH' : 'MED'}</span>
          <div class="body"><div class="file">${r.path}</div><div class="reason">${r.reason} <em style="color: var(--accent-2)">→ ${r.suggestion}</em></div></div>`;
                        panel.appendChild(row);
                    });
                }
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const repo = input.value.trim();

                // 🔐 Frontend Auth Guard
                const me = await fetch("/api/me", { credentials: "include" });
                const auth = await me.json();
                if (!auth.authenticated) {
                    window.location.href = "/login";
                    return;
                }

                if (!repo) { setStatus('Paste a GitHub repo (e.g. vercel/next.js)', 'error'); return; }
                btn.disabled = true;
                setStatus('Fetching repo tree, scoring files, asking the AI…', 'loading');
                
                try {
                    const res = await fetch('/api/analyze', {
                        method: 'POST',
                        credentials: 'include',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ repo_url: repo }),
                    });
                    
                    const text = await res.text();
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (err) {
                        throw new Error("Backend returned non-JSON response: " + text.slice(0, 50));
                    }

                    if (!res.ok) throw new Error(data.error || 'Analyze failed');
                    // Persist for /city
                    try { localStorage.setItem('cityData', JSON.stringify(data)); } catch { }
                    applyInsights(data);
                    setStatus(`✓ Analyzed ${data.snapshot?.repo_url || repo} · ${data.snapshot?.file_count || 0} files. Opening city…`, 'success');
                    setTimeout(() => { window.location.href = '/city'; }, 900);
                } catch (err) {
                    console.error("Analysis Error:", err);
                    setStatus('✗ ' + (err.message || 'Could not analyze that repo'), 'error');
                } finally {
                    btn.disabled = false;
                }
            });
        })();

        /* =====================  COMMAND BAR  ===================== */
        (function initCmd() {
            const overlay = document.getElementById('cmdOverlay');
            const input = document.getElementById('cmdInput');
            const list = document.getElementById('cmdList');
            const items = [
                { label: 'Analyze a repo', kbd: '↵', do: () => { close(); document.getElementById('repoInput').focus(); } },
                { label: 'Open dashboard (last analysis)', kbd: 'D', do: () => location.href = '/city' },
                { label: 'Jump to: How it works', kbd: '1', do: () => { close(); document.getElementById('how').scrollIntoView({ behavior: 'smooth' }); } },
                { label: 'Jump to: AI Insights', kbd: '2', do: () => { close(); document.getElementById('insights').scrollIntoView({ behavior: 'smooth' }); } },
                { label: 'Jump to: Compare', kbd: '3', do: () => { close(); document.getElementById('compare').scrollIntoView({ behavior: 'smooth' }); } },
                { label: 'Run demo: React repo', do: () => { close(); document.getElementById('repoInput').value = 'facebook/react'; document.getElementById('analyzeForm').requestSubmit(); } },
                { label: 'Run demo: Express backend', do: () => { close(); document.getElementById('repoInput').value = 'expressjs/express'; document.getElementById('analyzeForm').requestSubmit(); } },
                { label: 'Toggle Product / Developer mode', do: () => { close(); document.querySelector('.mode-toggle button:not(.active)').click(); } },
            ];
            let active = 0;
            function render() {
                const q = input.value.toLowerCase();
                const matches = items.filter(it => it.label.toLowerCase().includes(q));
                list.innerHTML = matches.map((it, i) => `<div class="cmd-item ${i === active ? 'active' : ''}" data-i="${items.indexOf(it)}">${it.label}${it.kbd ? `<span class="k">${it.kbd}</span>` : ''}</div>`).join('');
                list.querySelectorAll('.cmd-item').forEach(el => el.onclick = () => items[+el.dataset.i].do());
            }
            function open() { overlay.classList.add('open'); input.value = ''; active = 0; render(); setTimeout(() => input.focus(), 10); }
            function close() { overlay.classList.remove('open'); }
            document.getElementById('cmdBtn').onclick = open;
            overlay.onclick = (e) => { if (e.target === overlay) close(); };
            input.addEventListener('input', () => { active = 0; render(); });
            input.addEventListener('keydown', (e) => {
                const visible = list.querySelectorAll('.cmd-item');
                if (e.key === 'ArrowDown') { active = Math.min(visible.length - 1, active + 1); render(); }
                else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); render(); }
                else if (e.key === 'Enter') { const el = visible[active]; if (el) items[+el.dataset.i].do(); }
                else if (e.key === 'Escape') close();
            });
            window.addEventListener('keydown', (e) => {
                if ((e.key === '/' || (e.key === 'k' && (e.metaKey || e.ctrlKey))) && document.activeElement.tagName !== 'INPUT') {
                    e.preventDefault(); open();
                } else if (e.key === 'Escape' && overlay.classList.contains('open')) {
                    close();
                }
            });
        })();

        /* =====================  AI MINI CHAT (mock)  ===================== */
        (function initChat() {
            const fab = document.getElementById('chatFab');
            const panel = document.getElementById('chatPanel');
            const form = document.getElementById('chatForm');
            const input = document.getElementById('chatInput');
            const msgs = document.getElementById('chatMsgs');
            fab.onclick = () => panel.classList.toggle('open');
            const responses = {
                risky: "Based on the demo repo, `core/scheduler.ts` and `lib/auth.ts` are highest risk — high complexity, many callers, and tests are sparse.",
                refactor: "Start with `core/scheduler.ts`: extract a state machine and isolate the retry policy. Then wrap `lib/auth.ts` behind an adapter.",
                architecture: "The codebase has clear app/lib/core layering. Watch for `lib/` modules importing from `core/` — that should be the other way around.",
                default: "Try a real repo: paste a GitHub URL above and I'll analyze its risk hotspots in seconds.",
            };
            form.onsubmit = (e) => {
                e.preventDefault();
                const v = input.value.trim();
                if (!v) return;
                const u = document.createElement('div'); u.className = 'chat-msg user'; u.textContent = v; msgs.appendChild(u);
                input.value = '';
                msgs.scrollTop = msgs.scrollHeight;
                setTimeout(() => {
                    const lower = v.toLowerCase();
                    let r = responses.default;
                    if (/risk|risky/.test(lower)) r = responses.risky;
                    else if (/refactor|fix/.test(lower)) r = responses.refactor;
                    else if (/architect|structure/.test(lower)) r = responses.architecture;
                    const b = document.createElement('div'); b.className = 'chat-msg bot'; b.textContent = r; msgs.appendChild(b);
                    msgs.scrollTop = msgs.scrollHeight;
                }, 450);
            };
        })();
    </script>
</body>

</html>{% endraw %}"""

CITY_HTML = r"""{% raw %}<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>DevCity AI — 3D Code City</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link
    href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
    rel="stylesheet" />
  <style>
    /* ================================================================
   DevCity AI — Premium Dashboard Styles
   Glassmorphism · Dark/Light · Mobile-first
================================================================ */
    :root {
      color-scheme: dark;
      --bg-0: #020617;
      --bg-1: #0f172a;
      --panel: rgba(15, 23, 42, 0.72);
      --panel-strong: rgba(15, 23, 42, 0.88);
      --panel-border: rgba(148, 163, 184, 0.18);
      --panel-border-strong: rgba(148, 163, 184, 0.32);
      --text: #e2e8f0;
      --text-dim: #94a3b8;
      --text-faint: #64748b;
      --accent: #38bdf8;
      --accent-2: #a855f7;
      --accent-soft: rgba(56, 189, 248, 0.16);
      --danger: #fb7185;
      --warning: #f59e0b;
      --success: #22c55e;
      --bg-grad:
        radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.12), transparent 28%),
        radial-gradient(circle at 85% 15%, rgba(168, 85, 247, 0.10), transparent 22%),
        linear-gradient(180deg, #0f172a 0%, #020617 100%);
      --shadow-lg: 0 18px 60px rgba(2, 6, 23, 0.45);
      --radius: 16px;
      --radius-sm: 10px;
      --t-fast: 160ms;
      --t-med: 240ms;
    }

    :root.light {
      color-scheme: light;
      --bg-0: #f8fafc;
      --bg-1: #eef2f7;
      --panel: rgba(255, 255, 255, 0.78);
      --panel-strong: rgba(255, 255, 255, 0.94);
      --panel-border: rgba(15, 23, 42, 0.10);
      --panel-border-strong: rgba(15, 23, 42, 0.18);
      --text: #0f172a;
      --text-dim: #475569;
      --text-faint: #94a3b8;
      --accent: #0284c7;
      --accent-2: #7c3aed;
      --bg-grad:
        radial-gradient(circle at 15% 20%, rgba(2, 132, 199, 0.10), transparent 28%),
        radial-gradient(circle at 85% 15%, rgba(124, 58, 237, 0.08), transparent 22%),
        linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
      --shadow-lg: 0 18px 60px rgba(15, 23, 42, 0.10);
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      background: var(--bg-grad);
      color: var(--text);
      font-family: "Space Grotesk", system-ui, sans-serif;
      transition: background var(--t-med) ease, color var(--t-med) ease;
      -webkit-font-smoothing: antialiased;
    }

    body {
      position: relative;
    }

    #scene-root,
    canvas {
      display: block;
      width: 100vw;
      height: 100vh;
    }

    #scene-root {
      position: fixed;
      inset: 0;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      height: 100dvh;
      z-index: 0;
      touch-action: none;
      /* let OrbitControls own gestures */
    }

    #scene-root canvas {
      width: 100% !important;
      height: 100% !important;
      outline: none;
    }

    .chrome {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 5;
    }

    .chrome>* {
      pointer-events: auto;
    }

    /* ---------- Glass primitives ---------- */
    .glass {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      box-shadow: var(--shadow-lg);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: var(--radius);
    }

    .glass-strong {
      background: var(--panel-strong);
    }

    button,
    .btn {
      appearance: none;
      border: 1px solid var(--panel-border-strong);
      background: var(--panel);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 999px;
      font: 600 13px/1 "Space Grotesk", sans-serif;
      cursor: pointer;
      transition: transform var(--t-fast) ease, background var(--t-fast) ease, border-color var(--t-fast) ease, color var(--t-fast) ease;
      backdrop-filter: blur(16px);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }

    button:hover,
    .btn:hover {
      transform: translateY(-1px);
      border-color: var(--accent);
      color: var(--accent);
    }

    button.active,
    .btn.active {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--accent);
    }

    button:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }

    /* ---------- Top bar ---------- */
    .topbar {
      position: fixed;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      gap: 12px;
      align-items: flex-start;
      flex-wrap: wrap;
      z-index: 10;
    }

    .topbar-left,
    .topbar-right {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .topbar-right {
      margin-left: auto;
    }

    .title-card {
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 200px;
    }

    .title-card .eyebrow {
      font: 600 10px/1.2 "JetBrains Mono", monospace;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--text-dim);
    }

    .title-card h1 {
      margin: 0;
      font-size: 18px;
      line-height: 1.1;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    /* ---------- Search ---------- */
    .search-wrap {
      position: relative;
      display: flex;
      align-items: center;
      background: var(--panel);
      border: 1px solid var(--panel-border-strong);
      border-radius: 999px;
      padding: 0 12px 0 38px;
      height: 38px;
      min-width: 200px;
      backdrop-filter: blur(16px);
      transition: border-color var(--t-fast) ease, box-shadow var(--t-fast) ease;
    }

    .search-wrap:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }

    .search-wrap::before {
      content: "";
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      width: 14px;
      height: 14px;
      background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='7'/><path d='m20 20-3.5-3.5'/></svg>");
      background-size: contain;
      background-repeat: no-repeat;
      opacity: 0.8;
    }

    .search-wrap input {
      border: none;
      background: transparent;
      outline: none;
      color: var(--text);
      font: 500 13px "Space Grotesk", sans-serif;
      flex: 1;
      min-width: 0;
    }

    .search-wrap input::placeholder {
      color: var(--text-faint);
    }

    /* ---------- Mode toggle pill group ---------- */
    .mode-group {
      display: inline-flex;
      background: var(--panel);
      border: 1px solid var(--panel-border-strong);
      border-radius: 999px;
      padding: 4px;
      gap: 2px;
      backdrop-filter: blur(16px);
    }

    .mode-group button {
      border: none;
      background: transparent;
      padding: 7px 12px;
      border-radius: 999px;
      font-size: 12px;
      color: var(--text-dim);
    }

    .mode-group button:hover {
      color: var(--text);
      transform: none;
    }

    .mode-group button.active {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: white;
      border: none;
    }

    /* ---------- Floating right-side stack panels ---------- */
    .side-panels {
      position: fixed;
      top: 80px;
      right: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      width: min(340px, calc(100vw - 32px));
      max-height: calc(100vh - 240px);
      overflow-y: auto;
      z-index: 9;
      scrollbar-width: thin;
      scrollbar-color: var(--panel-border-strong) transparent;
    }

    .side-panels::-webkit-scrollbar {
      width: 6px;
    }

    .side-panels::-webkit-scrollbar-thumb {
      background: var(--panel-border-strong);
      border-radius: 3px;
    }

    .panel {
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      animation: panel-in var(--t-med) ease;
    }

    @keyframes panel-in {
      from {
        opacity: 0;
        transform: translateY(8px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .panel-title {
      font: 600 11px/1.2 "JetBrains Mono", monospace;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-dim);
    }

    .panel-collapse {
      background: transparent;
      border: none;
      padding: 4px;
      color: var(--text-dim);
      cursor: pointer;
      font-size: 14px;
      border-radius: 4px;
    }

    .panel-collapse:hover {
      color: var(--accent);
      transform: none;
    }

    .panel.collapsed .panel-body {
      display: none;
    }

    /* ---------- Hover/Detail panel ---------- */
    .detail-panel h2 {
      margin: 0;
      font-size: 17px;
      line-height: 1.2;
      word-break: break-word;
    }

    .detail-panel .path {
      color: var(--text-dim);
      font-size: 11px;
      line-height: 1.4;
      font-family: "JetBrains Mono", monospace;
      word-break: break-all;
    }

    .health-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font: 600 11px/1 "Space Grotesk", sans-serif;
      width: fit-content;
    }

    .health-tag .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .health-tag.healthy {
      background: rgba(34, 197, 94, 0.16);
      color: #4ade80;
    }

    .health-tag.healthy .dot {
      background: #22c55e;
      box-shadow: 0 0 8px #22c55e;
    }

    .health-tag.warn {
      background: rgba(245, 158, 11, 0.16);
      color: #fbbf24;
    }

    .health-tag.warn .dot {
      background: #f59e0b;
      box-shadow: 0 0 8px #f59e0b;
    }

    .health-tag.risk {
      background: rgba(251, 113, 133, 0.16);
      color: #fb7185;
    }

    .health-tag.risk .dot {
      background: #fb7185;
      box-shadow: 0 0 8px #fb7185;
    }

    .stat-row {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }

    .stat {
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      background: rgba(2, 6, 23, 0.4);
      border: 1px solid var(--panel-border);
    }

    :root.light .stat {
      background: rgba(255, 255, 255, 0.6);
    }

    .stat-label {
      display: block;
      margin-bottom: 4px;
      font: 600 10px/1 "JetBrains Mono", monospace;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-dim);
    }

    .stat-value {
      font-size: 15px;
      font-weight: 700;
    }

    /* mini bar */
    .mini-bar {
      position: relative;
      height: 4px;
      background: rgba(148, 163, 184, 0.18);
      border-radius: 2px;
      margin-top: 6px;
      overflow: hidden;
    }

    .mini-bar>span {
      position: absolute;
      inset: 0 auto 0 0;
      border-radius: 2px;
      transition: width var(--t-med) ease, background var(--t-med) ease;
    }

    .detail-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 4px;
    }

    .detail-actions button {
      padding: 8px 12px;
      font-size: 12px;
    }

    .code-preview {
      margin-top: 6px;
      background: rgba(2, 6, 23, 0.6);
      border: 1px solid var(--panel-border);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      max-height: 160px;
      overflow: auto;
      font: 500 11px/1.55 "JetBrains Mono", monospace;
      color: var(--text-dim);
      white-space: pre;
    }

    :root.light .code-preview {
      background: rgba(15, 23, 42, 0.04);
      color: #334155;
    }

    /* ---------- Analytics, AI panels ---------- */
    .kv-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .kv-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: var(--text-dim);
    }

    .kv-item strong {
      color: var(--text);
      font-weight: 600;
    }

    .dist-bar {
      display: flex;
      height: 8px;
      border-radius: 4px;
      overflow: hidden;
      background: rgba(148, 163, 184, 0.16);
    }

    .dist-bar>span {
      display: block;
      transition: flex-grow var(--t-med) ease;
    }

    .health-score {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 10px 0;
    }

    .health-ring {
      --p: 0;
      --c: var(--success);
      width: 64px;
      height: 64px;
      border-radius: 50%;
      flex-shrink: 0;
      background:
        conic-gradient(var(--c) calc(var(--p) * 1%), rgba(148, 163, 184, 0.18) 0);
      display: grid;
      place-items: center;
      position: relative;
      transition: background var(--t-med) ease;
    }

    .health-ring::before {
      content: "";
      position: absolute;
      inset: 6px;
      border-radius: 50%;
      background: var(--panel-strong);
    }

    .health-ring span {
      position: relative;
      font-weight: 700;
      font-size: 18px;
    }

    .health-meta {
      flex: 1;
      min-width: 0;
    }

    .health-meta .label {
      font-size: 11px;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .health-meta .desc {
      font-size: 12px;
      color: var(--text-dim);
      margin-top: 2px;
    }

    .badges {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    .badge {
      font: 600 10px/1 "JetBrains Mono", monospace;
      padding: 5px 8px;
      border-radius: 6px;
      background: rgba(56, 189, 248, 0.12);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.24);
      letter-spacing: 0.06em;
    }

    .badge.danger {
      background: rgba(251, 113, 133, 0.12);
      color: #fb7185;
      border-color: rgba(251, 113, 133, 0.24);
    }

    .badge.success {
      background: rgba(34, 197, 94, 0.12);
      color: #4ade80;
      border-color: rgba(34, 197, 94, 0.24);
    }

    .risky-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 180px;
      overflow-y: auto;
    }

    .risky-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 10px;
      border-radius: 8px;
      background: rgba(2, 6, 23, 0.4);
      border: 1px solid var(--panel-border);
      cursor: pointer;
      transition: background var(--t-fast) ease, border-color var(--t-fast) ease;
    }

    :root.light .risky-item {
      background: rgba(255, 255, 255, 0.6);
    }

    .risky-item:hover {
      border-color: var(--accent);
      background: var(--accent-soft);
    }

    .risky-item .name {
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
      min-width: 0;
    }

    .risky-item .score {
      font: 700 11px/1 "JetBrains Mono", monospace;
      padding: 3px 6px;
      border-radius: 4px;
      background: rgba(251, 113, 133, 0.16);
      color: #fb7185;
      margin-left: 8px;
    }

    .ai-text {
      font-size: 12px;
      line-height: 1.6;
      color: var(--text-dim);
      max-height: 200px;
      overflow-y: auto;
      white-space: pre-wrap;
    }

    .ai-text strong {
      color: var(--text);
    }

    .ai-loading {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-dim);
    }

    .spinner {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      border: 2px solid var(--panel-border-strong);
      border-top-color: var(--accent);
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    /* ---------- Bottom bar (timeline) ---------- */
    .bottombar {
      position: fixed;
      left: 16px;
      right: 16px;
      bottom: 16px;
      display: flex;
      gap: 12px;
      align-items: stretch;
      z-index: 9;
    }

    .timeline-panel {
      flex: 1;
      min-width: 0;
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .timeline-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .timeline-label {
      font: 600 11px/1.2 "JetBrains Mono", monospace;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-dim);
    }

    .timeline-stamp {
      font: 600 12px/1 "JetBrains Mono", monospace;
      color: var(--accent);
    }

    .timeline-row {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .timeline-row input[type="range"] {
      flex: 1;
      -webkit-appearance: none;
      appearance: none;
      height: 4px;
      border-radius: 2px;
      background: linear-gradient(to right, var(--accent), var(--accent-2));
      outline: none;
      cursor: pointer;
    }

    .timeline-row input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: white;
      border: 2px solid var(--accent);
      box-shadow: 0 2px 8px rgba(56, 189, 248, 0.4);
      cursor: pointer;
      transition: transform var(--t-fast) ease;
    }

    .timeline-row input[type="range"]::-webkit-slider-thumb:hover {
      transform: scale(1.15);
    }

    .timeline-row input[type="range"]::-moz-range-thumb {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: white;
      border: 2px solid var(--accent);
      cursor: pointer;
    }

    .timeline-play {
      padding: 8px 12px;
      font-size: 12px;
      flex-shrink: 0;
    }

    /* ---------- Minimap ---------- */
    .minimap-wrap {
      width: 180px;
      height: 180px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex-shrink: 0;
    }

    .minimap-label {
      font: 600 10px/1 "JetBrains Mono", monospace;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-dim);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    #minimap-canvas {
      width: 100%;
      flex: 1;
      border-radius: 8px;
      background: rgba(2, 6, 23, 0.6);
      cursor: crosshair;
      display: block;
    }

    :root.light #minimap-canvas {
      background: rgba(15, 23, 42, 0.06);
    }

    /* ---------- Empty state ---------- */
    .empty-state {
      position: fixed;
      inset: 50%;
      transform: translate(-50%, -50%);
      width: min(460px, calc(100vw - 32px));
      padding: 28px;
      border-radius: 24px;
      text-align: center;
      z-index: 20;
    }

    .empty-state h2 {
      margin: 0 0 10px;
      font-size: 26px;
    }

    .empty-state p {
      margin: 0 0 20px;
      color: var(--text-dim);
      line-height: 1.6;
    }

    .empty-state button {
      min-width: 180px;
    }

    .hidden {
      display: none !important;
    }

    /* ---------- Toast ---------- */
    .toast {
      position: fixed;
      left: 50%;
      top: 80px;
      transform: translateX(-50%) translateY(-20px);
      padding: 10px 16px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      background: var(--panel-strong);
      border: 1px solid var(--panel-border-strong);
      backdrop-filter: blur(20px);
      box-shadow: var(--shadow-lg);
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--t-med) ease, transform var(--t-med) ease;
      z-index: 100;
    }

    .toast.visible {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    /* ---------- Floating Action Button (FAB) ---------- */
    .fab-wrap {
      position: fixed;
      right: max(16px, env(safe-area-inset-right));
      bottom: max(16px, env(safe-area-inset-bottom));
      z-index: 200;
      display: none;
      /* shown on mobile only */
      flex-direction: column;
      align-items: flex-end;
      gap: 10px;
      pointer-events: auto;
    }

    .fab {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      border: 1px solid var(--panel-border-strong);
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #fff;
      font-size: 22px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 12px 32px rgba(2, 6, 23, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
      transition: transform var(--t-fast) ease, box-shadow var(--t-fast) ease;
    }

    .fab:active {
      transform: scale(0.94);
    }

    .fab.secondary {
      width: 44px;
      height: 44px;
      font-size: 16px;
      background: var(--panel-strong);
      color: var(--text);
      backdrop-filter: blur(20px);
    }

    .fab-menu {
      display: none;
      flex-direction: column;
      gap: 8px;
      align-items: flex-end;
    }

    .fab-menu.open {
      display: flex;
    }

    .fab-menu .row {
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--panel-strong);
      border: 1px solid var(--panel-border);
      backdrop-filter: blur(18px);
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 13px;
      color: var(--text);
      box-shadow: var(--shadow-lg);
      cursor: pointer;
      white-space: nowrap;
    }

    .fab-menu .row:active {
      transform: scale(0.97);
    }

    .fab-search-row {
      display: none;
      background: var(--panel-strong);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      padding: 6px 10px;
      backdrop-filter: blur(18px);
      width: min(78vw, 320px);
    }

    .fab-search-row.open {
      display: flex;
    }

    .fab-search-row input {
      flex: 1;
      background: transparent;
      border: 0;
      outline: none;
      color: var(--text);
      font: 500 14px "Space Grotesk", sans-serif;
      padding: 6px;
    }

    /* ---------- Immersive Mode (hides all UI) ---------- */
    body.immersive .topbar,
    body.immersive .side-panels,
    body.immersive .bottombar,
    body.immersive .toast {
      display: none !important;
    }

    body.immersive .fab-wrap {
      display: flex;
    }

    /* always show FAB to escape immersive */

    /* ---------- Mobile ---------- */
    @media (max-width: 880px) {

      /* Make the canvas the unambiguous main view */
      body {
        overscroll-behavior: none;
      }

      /* Hide heavy desktop chrome by default on mobile.
     Users open it via the FAB → "Show Dashboard". */
      .topbar,
      .side-panels,
      .bottombar {
        display: none;
      }

      /* When the user explicitly opens the dashboard on mobile, show it
     as bottom-stacked panels that don't cover the whole screen. */
      body.show-dashboard .topbar {
        display: flex;
        position: fixed;
        top: max(8px, env(safe-area-inset-top));
        left: 8px;
        right: 8px;
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
        z-index: 150;
      }

      body.show-dashboard .topbar-right {
        width: 100%;
        flex-wrap: wrap;
      }

      body.show-dashboard .title-card {
        min-width: 0;
        flex: 1;
      }

      body.show-dashboard .search-wrap {
        flex: 1 1 100%;
        min-width: 0;
      }

      body.show-dashboard .side-panels {
        display: flex;
        top: auto;
        right: 8px;
        left: 8px;
        bottom: calc(220px + env(safe-area-inset-bottom));
        width: auto;
        max-height: 45vh;
        flex-direction: row;
        overflow-x: auto;
        overflow-y: hidden;
        scroll-snap-type: x mandatory;
        z-index: 140;
      }

      body.show-dashboard .panel {
        min-width: 280px;
        scroll-snap-align: start;
      }

      body.show-dashboard .bottombar {
        display: flex;
        left: 8px;
        right: 8px;
        bottom: calc(8px + env(safe-area-inset-bottom));
        flex-direction: column;
        z-index: 140;
      }

      body.show-dashboard .minimap-wrap {
        width: 100%;
        height: 130px;
        flex-direction: row;
      }

      body.show-dashboard .minimap-label {
        writing-mode: horizontal-tb;
      }

      body.show-dashboard #minimap-canvas {
        width: 110px;
        height: 110px;
        flex: 0 0 110px;
      }

      /* Hide hover panels by default on mobile (touch != hover) */
      .hover-panel {
        display: none;
      }

      /* Show FAB on mobile */
      .fab-wrap {
        display: flex;
      }

      /* Empty state should still be reachable */
      .empty-state {
        z-index: 250;
      }
    }

    /* Reduce motion */
    @media (prefers-reduced-motion: reduce) {

      *,
      *::before,
      *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
      }
    }
    /* ================================================================
       PRO TOOLS — additive UI for advanced features
       (Heatmap · Dependencies · Filters · Risk Alerts · Cluster labels ·
        Smart highlight · Focus exit · AI bottom sheet)
       Designed to coexist with existing UI; no overrides above.
    ================================================================ */
    .pro-toolbar {
      position: fixed;
      top: calc(env(safe-area-inset-top, 0px) + 78px);
      right: 14px;
      z-index: 6;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 10px;
      border-radius: 14px;
      background: var(--panel);
      border: 1px solid var(--panel-border);
      backdrop-filter: blur(18px) saturate(140%);
      -webkit-backdrop-filter: blur(18px) saturate(140%);
      box-shadow: var(--shadow-lg);
      max-width: 220px;
      transition: opacity var(--t-med) ease, transform var(--t-med) ease;
    }
    body.immersive .pro-toolbar { opacity: 0; pointer-events: none; transform: translateX(20px); }
    .pro-toolbar .pt-title {
      font-size: 10px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--text-faint);
      padding: 0 4px 2px;
    }
    .pro-toolbar button.pt-btn {
      all: unset;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      padding: 7px 10px;
      border-radius: 10px;
      color: var(--text);
      border: 1px solid transparent;
      background: rgba(255,255,255,0.02);
      transition: background var(--t-fast), border-color var(--t-fast), transform var(--t-fast);
      user-select: none;
    }
    .pro-toolbar button.pt-btn:hover { background: var(--accent-soft); }
    .pro-toolbar button.pt-btn.active {
      background: linear-gradient(135deg, var(--accent-soft), rgba(168,85,247,0.18));
      border-color: var(--panel-border-strong);
      color: var(--text);
    }
    .pro-toolbar button.pt-btn .pt-ic { width: 16px; text-align: center; opacity: 0.9; }
    .pro-toolbar button.pt-btn:active { transform: scale(0.97); }

    /* Filter chip bar (file types) */
    .filter-bar {
      position: fixed;
      left: 50%;
      transform: translateX(-50%);
      top: calc(env(safe-area-inset-top, 0px) + 78px);
      z-index: 5;
      display: flex;
      gap: 6px;
      padding: 8px 10px;
      border-radius: 999px;
      background: var(--panel);
      border: 1px solid var(--panel-border);
      backdrop-filter: blur(16px) saturate(140%);
      -webkit-backdrop-filter: blur(16px) saturate(140%);
      box-shadow: var(--shadow-lg);
      max-width: min(680px, 92vw);
      overflow-x: auto;
      scrollbar-width: none;
    }
    .filter-bar::-webkit-scrollbar { display: none; }
    body.immersive .filter-bar { opacity: 0; pointer-events: none; }
    .filter-chip {
      flex: 0 0 auto;
      font-size: 11px;
      padding: 5px 11px;
      border-radius: 999px;
      cursor: pointer;
      color: var(--text-dim);
      border: 1px solid var(--panel-border);
      background: transparent;
      transition: all var(--t-fast);
      white-space: nowrap;
      user-select: none;
    }
    .filter-chip:hover { color: var(--text); border-color: var(--panel-border-strong); }
    .filter-chip.active {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--text);
    }
    .filter-chip .cnt {
      font-size: 9px;
      opacity: 0.7;
      margin-left: 4px;
    }

    /* Exit-focus floating button */
    .focus-exit {
      position: fixed;
      top: calc(env(safe-area-inset-top, 0px) + 78px);
      left: 14px;
      z-index: 7;
      display: none;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 999px;
      background: var(--panel-strong);
      border: 1px solid var(--panel-border-strong);
      color: var(--text);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: var(--shadow-lg);
      animation: focusEnter 240ms ease;
    }
    .focus-exit.visible { display: inline-flex; }
    @keyframes focusEnter { from { opacity: 0; transform: translateY(-6px);} to { opacity: 1; transform: none;} }

    /* AI bottom sheet (mobile-first, also visible desktop on demand) */
    .ai-sheet {
      position: fixed;
      left: 50%;
      bottom: 16px;
      transform: translate(-50%, calc(100% + 24px));
      width: min(520px, calc(100vw - 28px));
      z-index: 8;
      padding: 14px 16px 16px;
      border-radius: 18px;
      background: var(--panel-strong);
      border: 1px solid var(--panel-border-strong);
      backdrop-filter: blur(22px) saturate(160%);
      -webkit-backdrop-filter: blur(22px) saturate(160%);
      box-shadow: var(--shadow-lg);
      transition: transform 320ms cubic-bezier(.2,.8,.2,1), opacity 240ms ease;
      opacity: 0;
      pointer-events: none;
    }
    .ai-sheet.visible {
      transform: translate(-50%, 0);
      opacity: 1;
      pointer-events: auto;
    }
    .ai-sheet .ai-sheet-grip {
      width: 38px; height: 4px;
      border-radius: 2px;
      background: var(--panel-border-strong);
      margin: 0 auto 10px;
    }
    .ai-sheet .ai-sheet-title {
      display: flex; align-items: center; justify-content: space-between;
      font-size: 13px; font-weight: 700; margin-bottom: 8px;
    }
    .ai-sheet .ai-sheet-title button {
      all: unset; cursor: pointer; padding: 4px 8px;
      border-radius: 8px; font-size: 11px; color: var(--text-dim);
      border: 1px solid var(--panel-border);
    }
    .ai-sheet .ai-sheet-body {
      font-size: 12px; line-height: 1.55; color: var(--text-dim);
      max-height: 38vh; overflow-y: auto;
    }
    .ai-sheet .ai-sheet-body strong { color: var(--text); }
    .ai-sheet .ai-row { display:flex; gap:8px; margin: 6px 0; }
    .ai-sheet .ai-row .pill {
      font-size: 10px; padding: 2px 8px; border-radius: 999px;
      background: var(--accent-soft); color: var(--accent);
      border: 1px solid var(--panel-border);
    }
    .ai-sheet .ai-row .pill.warn { background: rgba(245,158,11,0.16); color: var(--warning); }
    .ai-sheet .ai-row .pill.risk { background: rgba(251,113,133,0.16); color: var(--danger); }

    /* Pulsing risk alert ring (DOM overlay around top-risk meshes is too costly;
       instead we pulse meshes via shader-less material — but we also flash the
       risky-list rows to call attention). */
    @keyframes riskFlash {
      0%, 100% { box-shadow: 0 0 0 0 rgba(251,113,133,0.0); }
      50%      { box-shadow: 0 0 0 4px rgba(251,113,133,0.35); }
    }
    .risky-item.alert {
      animation: riskFlash 1.6s ease-in-out infinite;
      border-radius: 8px;
    }

    /* District labels (HTML overlay) */
    .district-label {
      position: fixed;
      pointer-events: none;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text);
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--panel);
      border: 1px solid var(--panel-border);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      transform: translate(-50%, -50%);
      z-index: 3;
      white-space: nowrap;
      transition: opacity var(--t-fast);
      opacity: 0;
    }
    .district-label.visible { opacity: 0.9; }

    /* Mobile responsive tweaks for new UI */
    @media (max-width: 880px) {
      .pro-toolbar {
        top: auto;
        bottom: calc(env(safe-area-inset-bottom, 0px) + 96px);
        right: 12px;
        max-width: 54px;
        padding: 6px;
      }
      .pro-toolbar .pt-title { display: none; }
      .pro-toolbar button.pt-btn { padding: 8px; font-size: 0; gap: 0; }
      .pro-toolbar button.pt-btn .pt-ic { font-size: 14px; }
      .filter-bar {
        top: calc(env(safe-area-inset-top, 0px) + 70px);
        max-width: calc(100vw - 24px);
      }
      .focus-exit {
        top: calc(env(safe-area-inset-top, 0px) + 70px);
        left: 12px;
      }
    }
  </style>
</head>

<body>

  <div id="scene-root"></div>

  <!-- Toast -->
  <div id="toast" class="toast" role="status" aria-live="polite"></div>

  <!-- Top bar -->
  <header class="topbar">
    <div class="topbar-left">
      <button class="back-button" onclick="history.length > 1 ? history.back() : (location.href='/')">← Back</button>
      <div class="title-card glass">
        <span class="eyebrow">Immersive · 3D City</span>
        <h1>DevCity AI</h1>
      </div>
    </div>

    <div class="topbar-right">
      <div class="search-wrap" role="search">
        <input id="search-input" type="text" placeholder="Search files…" autocomplete="off" spellcheck="false" />
      </div>

      <div class="mode-group" role="group" aria-label="Visualization mode">
        <button data-mode="default" class="active" title="Default view">Default</button>
        <button data-mode="risk" title="Color buildings by risk score">🔴 Risk</button>
        <button data-mode="complexity" title="Exaggerate height by complexity">🟡 Complexity</button>
        <button data-mode="anomaly" title="Highlight statistical outliers">🟣 Anomaly</button>
      </div>

      <button id="theme-toggle" title="Toggle theme">🌙</button>
      <button id="perf-toggle" title="Toggle performance mode">⚡</button>
      <button id="flythrough-toggle" title="Cinematic auto fly-through">🎥</button>
    </div>
  </header>

  <!-- Side / floating panels -->
  <aside class="side-panels" id="side-panels">

    <!-- File detail / hover panel -->
    <section class="panel glass detail-panel" id="detail-panel">
      <div class="panel-header">
        <span class="panel-title">File Inspector</span>
        <button class="panel-collapse" data-toggle="detail-panel" aria-label="Collapse">−</button>
      </div>
      <div class="panel-body" id="detail-body">
        <div id="detail-empty" style="font-size:12px;color:var(--text-dim);">
          Hover or click a building to inspect a file.
        </div>
        <div id="detail-content" class="hidden" style="display:flex;flex-direction:column;gap:10px;">
          <div id="health-tag" class="health-tag healthy"><span class="dot"></span><span
              id="health-tag-text">Healthy</span></div>
          <h2 id="detail-name">—</h2>
          <div class="path" id="detail-path">—</div>

          <div class="stat-row">
            <div class="stat">
              <span class="stat-label">Complexity</span>
              <span class="stat-value" id="detail-complexity">—</span>
              <div class="mini-bar"><span id="bar-complexity" style="background:var(--accent);"></span></div>
            </div>
            <div class="stat">
              <span class="stat-label">Size (LOC)</span>
              <span class="stat-value" id="detail-size">—</span>
              <div class="mini-bar"><span id="bar-size" style="background:var(--accent-2);"></span></div>
            </div>
            <div class="stat">
              <span class="stat-label">Risk</span>
              <span class="stat-value" id="detail-risk">—</span>
              <div class="mini-bar"><span id="bar-risk" style="background:var(--danger);"></span></div>
            </div>
            <div class="stat">
              <span class="stat-label">Height</span>
              <span class="stat-value" id="detail-height">—</span>
            </div>
          </div>

          <div class="detail-actions">
            <button id="open-github">↗ Open in GitHub</button>
            <button id="toggle-preview">👁 Code Preview</button>
          </div>
          <pre id="code-preview" class="code-preview hidden"></pre>
        </div>
      </div>
    </section>

    <!-- Analytics overlay -->
    <section class="panel glass" id="analytics-panel">
      <div class="panel-header">
        <span class="panel-title">📊 Analytics</span>
        <button class="panel-collapse" data-toggle="analytics-panel" aria-label="Collapse">−</button>
      </div>
      <div class="panel-body" style="display:flex;flex-direction:column;gap:10px;">
        <div class="health-score">
          <div class="health-ring" id="health-ring"><span id="health-score-num">—</span></div>
          <div class="health-meta">
            <div class="label">Repo Health</div>
            <div class="desc" id="health-desc">Calculating…</div>
            <div class="badges" id="badges" style="margin-top:6px;"></div>
          </div>
        </div>
        <div class="kv-list">
          <div class="kv-item"><span>Total files</span><strong id="stat-total">—</strong></div>
          <div class="kv-item"><span>Avg complexity</span><strong id="stat-complexity">—</strong></div>
          <div class="kv-item"><span>Total LOC</span><strong id="stat-loc">—</strong></div>
          <div class="kv-item"><span>Districts</span><strong id="stat-districts">—</strong></div>
        </div>
        <div>
          <div class="kv-item" style="margin-bottom:6px;"><span>Risk distribution</span></div>
          <div class="dist-bar" id="dist-bar" aria-label="Risk distribution">
            <span style="background:#22c55e;flex:1;"></span>
            <span style="background:#f59e0b;flex:1;"></span>
            <span style="background:#fb7185;flex:1;"></span>
          </div>
          <div class="kv-item" style="margin-top:4px;font-size:10px;">
            <span style="color:#22c55e;">● Healthy</span>
            <span style="color:#f59e0b;">● Watch</span>
            <span style="color:#fb7185;">● High</span>
          </div>
        </div>
      </div>
    </section>

    <!-- AI Insights panel -->
    <section class="panel glass" id="ai-panel">
      <div class="panel-header">
        <span class="panel-title">🧬 AI Insights</span>
        <div style="display:flex;gap:6px;">
          <button id="ai-refresh" class="panel-collapse" title="Re-run AI analysis" style="font-size:13px;">↻</button>
          <button class="panel-collapse" data-toggle="ai-panel" aria-label="Collapse">−</button>
        </div>
      </div>
      <div class="panel-body" style="display:flex;flex-direction:column;gap:10px;">
        <div>
          <div class="panel-title" style="margin-bottom:6px;">Top Risky Files</div>
          <div class="risky-list" id="risky-list"></div>
        </div>
        <div>
          <div class="panel-title" style="margin-bottom:6px;">Suggested Refactors</div>
          <div class="ai-text" id="ai-text">
            <div class="ai-loading">
              <div class="spinner"></div>Generating insights…
            </div>
          </div>
        </div>
      </div>
    </section>
  </aside>

  <!-- Bottom bar: timeline + minimap -->
  <footer class="bottombar">
    <section class="timeline-panel glass">
      <div class="timeline-header">
        <span class="timeline-label">⏳ Snapshot Timeline</span>
        <span class="timeline-stamp" id="timeline-stamp">—</span>
      </div>
      <div class="timeline-row">
        <button id="timeline-play" class="timeline-play" title="Play/Pause">▶</button>
        <input type="range" id="timeline-slider" min="0" max="0" value="0" step="1" />
      </div>
    </section>
    <section class="minimap-wrap glass">
      <div class="minimap-label"><span>🧭 Minimap</span><span id="minimap-coords"
          style="color:var(--text-faint);font-weight:500;">—</span></div>
      <canvas id="minimap-canvas" width="320" height="320" aria-label="Minimap"></canvas>
    </section>
  </footer>

  <!-- Empty state -->
  <div id="empty-state" class="empty-state glass hidden">
    <h2>No data found</h2>
    <p>Please analyze a repo first. This view reads the latest analysis payload from <code>localStorage.cityData</code>.
    </p>
    <button onclick="history.length > 1 ? history.back() : (location.href='/')">← Back to Dashboard</button>
  </div>

  <!-- Mobile FAB: single floating control to access everything -->
  <div id="fab-wrap" class="fab-wrap" aria-label="Quick controls">
    <div id="fab-search-row" class="fab-search-row">
      <input id="fab-search-input" type="text" placeholder="Search files…" autocomplete="off" spellcheck="false" />
    </div>
    <div id="fab-menu" class="fab-menu" role="menu">
      <button class="row" data-fab="search" role="menuitem">🔍 Search file</button>
      <button class="row" data-fab="mode-default" role="menuitem">🏙 Default mode</button>
      <button class="row" data-fab="mode-risk" role="menuitem">🔴 Risk mode</button>
      <button class="row" data-fab="mode-complexity" role="menuitem">🟡 Complexity mode</button>
      <button class="row" data-fab="mode-anomaly" role="menuitem">🟣 Anomaly mode</button>
      <button class="row" data-fab="reset" role="menuitem">🎯 Reset camera</button>
      <button class="row" data-fab="dashboard" role="menuitem">📊 Show dashboard</button>
      <button class="row" data-fab="immersive" role="menuitem">🕶 Toggle immersive</button>
    </div>
    <button id="fab-toggle" class="fab" aria-label="Open quick controls" aria-expanded="false">＋</button>
  </div>


  <script src="https://unpkg.com/three@0.136.0/build/three.min.js"></script>
  <script src="https://unpkg.com/three@0.136.0/examples/js/controls/OrbitControls.js"></script>
  <script>
    /* ================================================================
       DevCity AI — Premium Interactive 3D City
       Modular sections:
         1. Utilities & data normalization
         2. Three.js scene bootstrap
         3. City builder + visualization modes
         4. Interaction (hover, click, double-click, focus)
         5. Camera transitions / fly-through
         6. UI: search, theme, perf, panels, timeline, minimap
         7. Analytics + AI insights
    ================================================================ */

    /* ---------- DOM refs ---------- */
    const $ = (id) => document.getElementById(id);
    const sceneRoot = $('scene-root');
    const emptyState = $('empty-state');
    const toastEl = $('toast');

    /* ---------- 1. Utilities ---------- */
    const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
    const lerp = (a, b, t) => a + (b - a) * t;
    const easeInOutCubic = (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const toNumber = (v, f = 0) => { const n = Number(v); return Number.isFinite(n) ? n : f; };
    const isMobile = () => window.matchMedia('(max-width: 880px)').matches
      || ('ontouchstart' in window && Math.min(window.innerWidth, window.innerHeight) < 820);

    function showToast(msg, ms = 2200) {
      toastEl.textContent = msg;
      toastEl.classList.add('visible');
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => toastEl.classList.remove('visible'), ms);
    }

    function lerpColor(a, b, t) {
      return new THREE.Color(a).lerp(new THREE.Color(b), clamp(t, 0, 1));
    }

    function readCityPayload() {
      try { return JSON.parse(localStorage.getItem('cityData')); }
      catch (e) { console.warn('Failed to parse cityData', e); return null; }
    }
    function extractFiles(payload) {
      if (Array.isArray(payload)) return payload;
      if (payload && Array.isArray(payload.data)) return payload.data;
      if (payload && Array.isArray(payload.files)) return payload.files;
      return [];
    }
    function extractSnapshots(payload) {
      // Optional snapshot system: payload.snapshots = [{ timestamp, files: [...] }, ...]
      if (payload && Array.isArray(payload.snapshots) && payload.snapshots.length) {
        return payload.snapshots.map((s, i) => ({
          timestamp: s.timestamp || s.date || `Snapshot ${i + 1}`,
          files: extractFiles(s)
        }));
      }
      return null;
    }

    function getDirectory(path) {
      const p = String(path || '');
      const parts = p.split('/').filter(Boolean);
      if (parts.length <= 1) return '/';
      return parts.slice(0, -1).join('/');
    }

    function riskColor(file, complexity) {
      if (file.risk_score !== undefined && file.risk_score !== null && file.risk_score !== '') {
        return lerpColor(0x22c55e, 0xef4444, clamp(toNumber(file.risk_score, 0), 0, 1));
      }
      if (typeof file.color === 'string' && file.color.trim()) {
        try { return new THREE.Color(file.color); } catch { }
      }
      return lerpColor(0x38bdf8, 0xf59e0b, clamp(complexity / 60, 0, 1));
    }

    function normalizeFiles(rawFiles) {
      const out = [];
      const cols = Math.max(1, Math.ceil(Math.sqrt(rawFiles.length || 1)));
      let cx = 0, cy = 0, rowD = 0;

      rawFiles.forEach((f, i) => {
        const size = Math.max(1, toNumber(f.size, toNumber(f.loc, 1)));
        const complexity = Math.max(1, toNumber(f.complexity, toNumber(f.h, 2) / 2 || 1));
        const w = Math.max(4, toNumber(f.w, Math.sqrt(size) * 0.7 + 4));
        const d = Math.max(4, toNumber(f.d, Math.sqrt(size) * 0.7 + 4));
        const h = Math.max(6, toNumber(f.h, complexity * 2.4));
        const hasLayout = Number.isFinite(Number(f.x)) && Number.isFinite(Number(f.y));

        if (!hasLayout) {
          if (i > 0 && i % cols === 0) { cx = 0; cy += rowD + 8; rowD = 0; }
          rowD = Math.max(rowD, d);
        }

        const c = riskColor(f, complexity);
        out.push({
          ...f,
          name: f.name || f.path || `File ${i + 1}`,
          path: f.path || f.name || `file-${i + 1}`,
          size, complexity, w, d, h,
          x: hasLayout ? toNumber(f.x, 0) : cx,
          y: hasLayout ? toNumber(f.y, 0) : cy,
          color: `#${c.getHexString()}`,
          risk_score: toNumber(f.risk_score, 0),
          directory: getDirectory(f.path || f.name)
        });

        if (!hasLayout) cx += w + 8;
      });
      return out;
    }

    function computeBounds(files) {
      return files.reduce((b, f) => ({
        minX: Math.min(b.minX, f.x),
        maxX: Math.max(b.maxX, f.x + f.w),
        minY: Math.min(b.minY, f.y),
        maxY: Math.max(b.maxY, f.y + f.d),
        maxH: Math.max(b.maxH, f.h)
      }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity, maxH: 0 });
    }

    /* ---------- State ---------- */
    const State = {
      scene: null, camera: null, renderer: null, controls: null,
      cityGroup: null, ground: null, gridHelper: null, lights: [],
      raycaster: null, pointer: new THREE.Vector2(2, 2),
      files: [],            // current snapshot (normalized)
      meshes: [],           // building meshes
      edges: [],            // edge line segments
      districtMeshes: [],   // district plates
      bounds: null,
      hoveredMesh: null,
      selectedMesh: null,
      mode: 'default',
      perfMode: false,
      shadowsEnabled: true,
      flyingThrough: false,
      cameraTween: null,    // active camera animation
      snapshots: null,      // [{timestamp, files}]
      currentSnapshot: 0,
      timelinePlaying: false,
      payload: null,
      repoUrl: null         // detected GitHub repo base URL
    };

    /* ---------- 2. Scene bootstrap ---------- */
    function initScene() {
      const isLight = document.documentElement.classList.contains('light');
      State.scene = new THREE.Scene();
      State.scene.fog = new THREE.FogExp2(isLight ? 0xeef2f7 : 0x020617, 0.0014);

      State.camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 6000);

      State.renderer = new THREE.WebGLRenderer({ antialias: !isMobile(), alpha: true, powerPreference: 'high-performance' });
      State.renderer.setSize(window.innerWidth, window.innerHeight);
      // Mobile: cap pixel ratio at 1 to keep the city smooth & fully visible
      State.renderer.setPixelRatio(isMobile() ? 1 : Math.min(window.devicePixelRatio || 1, 2));
      State.renderer.shadowMap.enabled = !isMobile();
      State.renderer.shadowMap.type = isMobile() ? THREE.BasicShadowMap : THREE.PCFSoftShadowMap;
      State.renderer.outputEncoding = THREE.sRGBEncoding;
      sceneRoot.appendChild(State.renderer.domElement);

      State.controls = new THREE.OrbitControls(State.camera, State.renderer.domElement);
      State.controls.enableDamping = true;
      State.controls.dampingFactor = 0.07;
      State.controls.screenSpacePanning = true;
      State.controls.maxPolarAngle = Math.PI / 2.05;
      // Touch gestures: 1-finger rotate, 2-finger pinch-zoom + pan
      State.controls.enableZoom = true;
      State.controls.enablePan = true;
      State.controls.zoomSpeed = isMobile() ? 0.9 : 1.0;
      State.controls.rotateSpeed = isMobile() ? 0.6 : 1.0;
      if (THREE.TOUCH) {
        State.controls.touches = {
          ONE: THREE.TOUCH.ROTATE,
          TWO: THREE.TOUCH.DOLLY_PAN
        };
      }

      State.raycaster = new THREE.Raycaster();

      // Pointer events (mouse + touch)
      const dom = State.renderer.domElement;
      dom.addEventListener('mousemove', onPointerMove);
      dom.addEventListener('mouseleave', () => updateHover(null));
      dom.addEventListener('click', onClick);
      dom.addEventListener('dblclick', onDoubleClick);
      // touch tap → click
      dom.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
          const t = e.touches[0];
          onPointerMove({ clientX: t.clientX, clientY: t.clientY });
        }
      }, { passive: true });

      // Mobile: double-tap canvas → toggle immersive mode
      setupDoubleTapImmersive(dom);

      window.addEventListener('resize', onResize);
      window.addEventListener('orientationchange', () => setTimeout(onResize, 150));
      window.addEventListener('beforeunload', () => cancelAnimationFrame(State.rafId));
    }

    function onResize() {
      if (!State.camera || !State.renderer) return;
      State.camera.aspect = window.innerWidth / window.innerHeight;
      State.camera.updateProjectionMatrix();
      State.renderer.setSize(window.innerWidth, window.innerHeight);
      const mobile = isMobile();
      State.renderer.setPixelRatio(
        mobile ? 1 : Math.min(window.devicePixelRatio || 1, State.perfMode ? 1 : 2)
      );
    }

    function onPointerMove(e) {
      const r = State.renderer.domElement.getBoundingClientRect();
      State.pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      State.pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;
    }

    /* ---------- 3. City builder ---------- */
    function clearCity() {
      if (!State.cityGroup) return;
      State.scene.remove(State.cityGroup);
      State.cityGroup.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        if (o.material) {
          if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
          else o.material.dispose();
        }
      });
      if (State.ground) { State.scene.remove(State.ground); State.ground.geometry.dispose(); State.ground.material.dispose(); State.ground = null; }
      if (State.gridHelper) { State.scene.remove(State.gridHelper); State.gridHelper = null; }
      State.lights.forEach((l) => State.scene.remove(l));
      State.lights = [];
      State.meshes = []; State.edges = []; State.districtMeshes = [];
    }

    function createLights(bounds) {
      const isLight = document.documentElement.classList.contains('light');
      const ambient = new THREE.AmbientLight(isLight ? 0xffffff : 0xbcd4ff, isLight ? 0.85 : 0.65);
      State.scene.add(ambient); State.lights.push(ambient);

      const key = new THREE.DirectionalLight(0xffffff, isLight ? 0.9 : 1.15);
      key.position.set(bounds.maxX + 80, bounds.maxH + 180, bounds.maxY + 60);
      key.castShadow = State.shadowsEnabled;
      if (State.shadowsEnabled) {
        key.shadow.mapSize.width = State.perfMode ? 1024 : 2048;
        key.shadow.mapSize.height = State.perfMode ? 1024 : 2048;
        key.shadow.camera.near = 1; key.shadow.camera.far = 1200;
        const s = Math.max(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY);
        key.shadow.camera.left = -s; key.shadow.camera.right = s;
        key.shadow.camera.top = s; key.shadow.camera.bottom = -s;
      }
      State.scene.add(key); State.lights.push(key);

      if (!State.perfMode) {
        const fill = new THREE.PointLight(0x38bdf8, 0.55, 900);
        fill.position.set(bounds.minX - 60, 120, bounds.maxY + 120);
        State.scene.add(fill); State.lights.push(fill);

        const rim = new THREE.PointLight(0xa855f7, 0.35, 800);
        rim.position.set(bounds.maxX + 60, 80, bounds.minY - 80);
        State.scene.add(rim); State.lights.push(rim);
      }
    }

    function createGround(gridSize) {
      const isLight = document.documentElement.classList.contains('light');
      const planeGeo = new THREE.PlaneGeometry(gridSize, gridSize);
      const planeMat = new THREE.MeshStandardMaterial({
        color: isLight ? 0xe5ecf3 : 0x0b1222,
        roughness: 0.95, metalness: 0.06
      });
      State.ground = new THREE.Mesh(planeGeo, planeMat);
      State.ground.rotation.x = -Math.PI / 2;
      State.ground.receiveShadow = State.shadowsEnabled;
      State.scene.add(State.ground);

      State.gridHelper = new THREE.GridHelper(
        gridSize, Math.max(10, Math.round(gridSize / 12)),
        isLight ? 0xb8c4d4 : 0x16324f,
        isLight ? 0xd1d9e2 : 0x0f2036
      );
      State.gridHelper.position.y = 0.05;
      State.scene.add(State.gridHelper);
    }

    /* District plates: subtle colored ground tiles per directory */
    function createDistricts(files, centerX, centerY) {
      const groups = new Map();
      files.forEach((f) => {
        const k = f.directory || '/';
        if (!groups.has(k)) groups.set(k, { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });
        const g = groups.get(k);
        g.minX = Math.min(g.minX, f.x);
        g.maxX = Math.max(g.maxX, f.x + f.w);
        g.minY = Math.min(g.minY, f.y);
        g.maxY = Math.max(g.maxY, f.y + f.d);
      });

      let i = 0;
      const palette = [0x38bdf8, 0xa855f7, 0xf59e0b, 0x22c55e, 0xfb7185, 0x14b8a6, 0xef4444, 0x6366f1];
      groups.forEach((g, dir) => {
        const w = Math.max(8, g.maxX - g.minX) + 6;
        const d = Math.max(8, g.maxY - g.minY) + 6;
        const cx = (g.minX + g.maxX) / 2 - centerX;
        const cz = (g.minY + g.maxY) / 2 - centerY;

        const color = palette[i % palette.length];
        const mat = new THREE.MeshStandardMaterial({
          color, transparent: true, opacity: 0.07,
          roughness: 1, metalness: 0
        });
        const plate = new THREE.Mesh(new THREE.BoxGeometry(w, 0.4, d), mat);
        plate.position.set(cx, 0.2, cz);
        plate.userData.isDistrict = true;
        plate.userData.dir = dir;
        State.cityGroup.add(plate);
        State.districtMeshes.push(plate);

        // subtle outline
        const edgeGeo = new THREE.EdgesGeometry(plate.geometry);
        const edge = new THREE.LineSegments(
          edgeGeo,
          new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35 })
        );
        edge.position.copy(plate.position);
        State.cityGroup.add(edge);
        i++;
      });
    }

    function buildCity(files) {
      clearCity();
      State.cityGroup = new THREE.Group();
      State.scene.add(State.cityGroup);
      State.files = files;

      const bounds = computeBounds(files);
      State.bounds = bounds;
      const cx = (bounds.minX + bounds.maxX) / 2;
      const cy = (bounds.minY + bounds.maxY) / 2;
      const cw = Math.max(80, bounds.maxX - bounds.minX);
      const cd = Math.max(80, bounds.maxY - bounds.minY);
      const gridSize = Math.max(cw, cd) * 1.8;

      createGround(gridSize);
      createLights(bounds);
      createDistricts(files, cx, cy);

      files.forEach((f) => {
        const geo = new THREE.BoxGeometry(f.w, f.h, f.d);
        const color = new THREE.Color(f.color);
        const mat = new THREE.MeshStandardMaterial({
          color,
          emissive: color.clone(),
          emissiveIntensity: 0.18,
          roughness: State.perfMode ? 0.7 : 0.32,
          metalness: State.perfMode ? 0 : 0.22,
          flatShading: State.perfMode
        });
        const m = new THREE.Mesh(geo, mat);
        m.castShadow = State.shadowsEnabled;
        m.receiveShadow = State.shadowsEnabled;
        m.position.set(
          f.x + f.w / 2 - cx,
          f.h / 2,
          f.y + f.d / 2 - cy
        );
        m.userData = {
          file: f,
          baseColor: color.clone(),
          baseEmissive: color.clone(),
          baseEmissiveIntensity: 0.18,
          baseHeight: f.h,
          basePos: m.position.clone()
        };
        State.cityGroup.add(m);
        State.meshes.push(m);

        if (!State.perfMode) {
          const eGeo = new THREE.EdgesGeometry(geo);
          const eMat = new THREE.LineBasicMaterial({ color: color.clone().offsetHSL(0, 0, 0.18) });
          const edges = new THREE.LineSegments(eGeo, eMat);
          edges.position.copy(m.position);
          edges.userData.parentMesh = m;
          State.cityGroup.add(edges);
          State.edges.push(edges);
        }
      });

      // Initial camera framing — wider & more top-down on mobile so the
      // whole city is visible at first glance with no UI obstruction.
      const mobile = isMobile();
      const dist = Math.max(cw, cd) * (mobile ? 1.65 : 1.15);
      if (mobile) {
        // High isometric / near-top-down view, centered on origin
        State.camera.position.set(dist * 0.55, bounds.maxH + dist * 0.95, dist * 0.55);
      } else {
        State.camera.position.set(dist * 0.75, bounds.maxH + dist * 0.55, dist);
      }
      State.camera.lookAt(0, bounds.maxH * 0.2, 0);
      State.controls.target.set(0, Math.max(10, bounds.maxH * 0.22), 0);
      // Prevent accidental zoom-in clipping on mobile pinch
      State.controls.minDistance = Math.max(mobile ? 80 : 40, dist * (mobile ? 0.35 : 0.18));
      State.controls.maxDistance = dist * 3.2;
      State.controls.update();

      applyMode(State.mode);
    }

    /* Visualization modes */
    function applyMode(mode) {
      State.mode = mode;
      document.querySelectorAll('.mode-group button').forEach((b) =>
        b.classList.toggle('active', b.dataset.mode === mode));

      // Compute outliers (z-score on complexity) for anomaly mode
      let outliers = new Set();
      if (mode === 'anomaly') {
        const cs = State.files.map((f) => f.complexity);
        const mean = cs.reduce((a, b) => a + b, 0) / cs.length;
        const sd = Math.sqrt(cs.reduce((s, v) => s + (v - mean) ** 2, 0) / cs.length) || 1;
        State.files.forEach((f) => {
          if (Math.abs((f.complexity - mean) / sd) > 1.5) outliers.add(f.path);
        });
      }

      State.meshes.forEach((m, i) => {
        const f = m.userData.file;
        const pos = m.userData.basePos.clone();
        let h = m.userData.baseHeight;
        let color = m.userData.baseColor.clone();
        let emissiveIntensity = 0.18;

        if (mode === 'risk') {
          color = lerpColor(0x22c55e, 0xef4444, clamp(f.risk_score || 0, 0, 1));
          emissiveIntensity = 0.25 + (f.risk_score || 0) * 0.4;
        } else if (mode === 'complexity') {
          h = m.userData.baseHeight * (1 + clamp(f.complexity / 30, 0, 2.5));
          color = lerpColor(0x38bdf8, 0xf59e0b, clamp(f.complexity / 60, 0, 1));
          emissiveIntensity = 0.22 + clamp(f.complexity / 100, 0, 0.5);
        } else if (mode === 'anomaly') {
          if (outliers.has(f.path)) {
            color = new THREE.Color(0xa855f7);
            emissiveIntensity = 0.7;
            m.userData.isOutlier = true;
          } else {
            color = m.userData.baseColor.clone();
            emissiveIntensity = 0.1;
            m.userData.isOutlier = false;
          }
        }

        // Animate scale (height) by adjusting Y scale
        const targetScaleY = h / m.userData.baseHeight;
        tweenValue(m.scale.y, targetScaleY, 400, (v) => {
          m.scale.y = v;
          m.position.y = (m.userData.baseHeight * v) / 2;
          // sync edge geometry
          const edge = State.edges.find((e) => e.userData.parentMesh === m);
          if (edge) { edge.scale.y = v; edge.position.y = m.position.y; }
        });

        m.material.color.copy(color);
        m.material.emissive.copy(color);
        m.userData.baseEmissiveIntensity = emissiveIntensity;
        m.material.emissiveIntensity = emissiveIntensity;
      });
    }

    /* Lightweight tween util (no deps) */
    function tweenValue(from, to, ms, onUpdate) {
      if (Math.abs(from - to) < 0.001) { onUpdate(to); return; }
      const start = performance.now();
      const id = Symbol();
      function step(now) {
        const t = clamp((now - start) / ms, 0, 1);
        const v = lerp(from, to, easeInOutCubic(t));
        onUpdate(v);
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
      return id;
    }

    /* ---------- 4. Interaction ---------- */
    function pickIntersect() {
      State.raycaster.setFromCamera(State.pointer, State.camera);
      return State.raycaster.intersectObjects(State.meshes, false);
    }

    function updateHover(mesh) {
      if (State.hoveredMesh && State.hoveredMesh !== mesh && State.hoveredMesh !== State.selectedMesh) {
        State.hoveredMesh.material.emissiveIntensity = State.hoveredMesh.userData.baseEmissiveIntensity;
      }
      State.hoveredMesh = mesh;
      if (mesh && mesh !== State.selectedMesh) {
        mesh.material.emissiveIntensity = 0.55;
      }
      if (mesh) {
        populateDetail(mesh.userData.file);
      } else if (!State.selectedMesh) {
        showDetailEmpty();
      }
    }

    function onClick() {
      const hits = pickIntersect();
      if (!hits.length) {
        deselect(); return;
      }
      const m = hits[0].object;
      selectMesh(m);
      // Smooth zoom-in
      flyToMesh(m, { distanceFactor: 2.6, duration: 900 });
    }
    function onDoubleClick() {
      const hits = pickIntersect();
      if (!hits.length) return;
      const m = hits[0].object;
      selectMesh(m);
      // Focus mode: very close, isolate visually
      flyToMesh(m, { distanceFactor: 1.4, duration: 1100, focus: true });
    }

    function selectMesh(mesh) {
      if (State.selectedMesh && State.selectedMesh !== mesh) {
        State.selectedMesh.material.emissiveIntensity = State.selectedMesh.userData.baseEmissiveIntensity;
      }
      State.selectedMesh = mesh;
      mesh.material.emissiveIntensity = 0.85;
      populateDetail(mesh.userData.file);
    }
    function deselect() {
      if (State.selectedMesh) {
        State.selectedMesh.material.emissiveIntensity = State.selectedMesh.userData.baseEmissiveIntensity;
        // restore opacity if it was dimmed during focus
        State.meshes.forEach((m) => { m.material.opacity = 1; m.material.transparent = false; });
        State.selectedMesh = null;
      }
    }

    /* ---------- 5. Camera transitions / fly-through ---------- */
    function flyToMesh(mesh, { distanceFactor = 2.5, duration = 900, focus = false } = {}) {
      const f = mesh.userData.file;
      const target = mesh.position.clone();
      target.y = mesh.userData.baseHeight * (mesh.scale.y || 1) * 0.5;

      const dist = Math.max(f.w, f.d, mesh.userData.baseHeight) * distanceFactor;
      const dir = new THREE.Vector3(0.6, 0.55, 0.8).normalize();
      const camTarget = target.clone().add(dir.multiplyScalar(dist));

      animateCamera(camTarget, target, duration);

      if (focus) {
        // Dim all other buildings
        State.meshes.forEach((m) => {
          if (m === mesh) {
            m.material.transparent = false; m.material.opacity = 1;
          } else {
            m.material.transparent = true; m.material.opacity = 0.18;
          }
        });
      } else {
        State.meshes.forEach((m) => { m.material.transparent = false; m.material.opacity = 1; });
      }
    }

    function animateCamera(toPos, toTarget, duration = 900) {
      if (State.cameraTween) cancelAnimationFrame(State.cameraTween);
      const fromPos = State.camera.position.clone();
      const fromTarget = State.controls.target.clone();
      const start = performance.now();
      function step(now) {
        const t = clamp((now - start) / duration, 0, 1);
        const e = easeInOutCubic(t);
        State.camera.position.lerpVectors(fromPos, toPos, e);
        State.controls.target.lerpVectors(fromTarget, toTarget, e);
        State.controls.update();
        if (t < 1) State.cameraTween = requestAnimationFrame(step);
        else State.cameraTween = null;
      }
      State.cameraTween = requestAnimationFrame(step);
    }

    /* Auto fly-through: cinematic loop around the city */
    let flythroughT = 0;
    function tickFlythrough(dt) {
      if (!State.flyingThrough || !State.bounds) return;
      flythroughT += dt * 0.00015;
      const r = Math.max(State.bounds.maxX - State.bounds.minX, State.bounds.maxY - State.bounds.minY) * 0.85;
      const y = State.bounds.maxH * 1.6 + 40 + Math.sin(flythroughT * 1.3) * 30;
      State.camera.position.set(
        Math.cos(flythroughT) * r,
        y,
        Math.sin(flythroughT) * r
      );
      State.controls.target.set(0, State.bounds.maxH * 0.25, 0);
    }

    /* ---------- 6. UI wiring ---------- */
    /* Theme */
    $('theme-toggle').addEventListener('click', () => {
      const root = document.documentElement;
      const isLight = root.classList.toggle('light');
      $('theme-toggle').textContent = isLight ? '☀️' : '🌙';
      // Re-tint scene
      if (State.scene) {
        State.scene.fog.color.set(isLight ? 0xeef2f7 : 0x020617);
        if (State.ground) State.ground.material.color.set(isLight ? 0xe5ecf3 : 0x0b1222);
        if (State.gridHelper) {
          State.scene.remove(State.gridHelper);
          const gridSize = Math.max(State.bounds.maxX - State.bounds.minX, State.bounds.maxY - State.bounds.minY) * 1.8;
          State.gridHelper = new THREE.GridHelper(
            gridSize, Math.max(10, Math.round(gridSize / 12)),
            isLight ? 0xb8c4d4 : 0x16324f,
            isLight ? 0xd1d9e2 : 0x0f2036
          );
          State.gridHelper.position.y = 0.05;
          State.scene.add(State.gridHelper);
        }
      }
      drawMinimap();
    });

    /* Performance mode */
    $('perf-toggle').addEventListener('click', () => {
      State.perfMode = !State.perfMode;
      State.shadowsEnabled = !State.perfMode;
      $('perf-toggle').classList.toggle('active', State.perfMode);
      showToast(State.perfMode ? '⚡ Performance mode on' : 'Performance mode off');
      if (State.files.length) buildCity(State.files);
      onResize();
    });

    /* Mode toggle buttons */
    document.querySelectorAll('.mode-group button').forEach((b) => {
      b.addEventListener('click', () => applyMode(b.dataset.mode));
    });

    /* Fly-through */
    $('flythrough-toggle').addEventListener('click', () => {
      State.flyingThrough = !State.flyingThrough;
      $('flythrough-toggle').classList.toggle('active', State.flyingThrough);
      showToast(State.flyingThrough ? '🎥 Fly-through started' : 'Fly-through stopped');
      if (!State.flyingThrough && State.bounds) {
        // Restore default framing
        const cw = State.bounds.maxX - State.bounds.minX;
        const cd = State.bounds.maxY - State.bounds.minY;
        const dist = Math.max(cw, cd) * 1.15;
        animateCamera(
          new THREE.Vector3(dist * 0.75, State.bounds.maxH + dist * 0.55, dist),
          new THREE.Vector3(0, State.bounds.maxH * 0.22, 0),
          1100
        );
      }
    });

    /* Search */
    $('search-input').addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        State.meshes.forEach((m) => { m.material.opacity = 1; m.material.transparent = false; });
        return;
      }
      let firstHit = null;
      State.meshes.forEach((m) => {
        const f = m.userData.file;
        const hit = (f.name || '').toLowerCase().includes(q) || (f.path || '').toLowerCase().includes(q);
        m.material.transparent = true;
        m.material.opacity = hit ? 1 : 0.12;
        m.material.emissiveIntensity = hit ? 0.7 : m.userData.baseEmissiveIntensity * 0.5;
        if (hit && !firstHit) firstHit = m;
      });
      if (firstHit) flyToMesh(firstHit, { distanceFactor: 2.4, duration: 900 });
    });

    /* Panel collapse */
    document.querySelectorAll('.panel-collapse[data-toggle]').forEach((b) => {
      b.addEventListener('click', () => {
        const p = $(b.dataset.toggle);
        p.classList.toggle('collapsed');
        b.textContent = p.classList.contains('collapsed') ? '+' : '−';
      });
    });

    /* ---------- Reset camera (used by FAB & double-tap) ---------- */
    function resetCamera() {
      if (!State.bounds) return;
      const cw = State.bounds.maxX - State.bounds.minX;
      const cd = State.bounds.maxY - State.bounds.minY;
      const mobile = isMobile();
      const dist = Math.max(cw, cd) * (mobile ? 1.65 : 1.15);
      const toPos = mobile
        ? new THREE.Vector3(dist * 0.55, State.bounds.maxH + dist * 0.95, dist * 0.55)
        : new THREE.Vector3(dist * 0.75, State.bounds.maxH + dist * 0.55, dist);
      animateCamera(toPos, new THREE.Vector3(0, State.bounds.maxH * 0.22, 0), 900);
    }

    /* ---------- Immersive Mode ---------- */
    function setImmersive(on) {
      document.body.classList.toggle('immersive', on);
      if (on) document.body.classList.remove('show-dashboard');
      showToast(on ? '🕶 Immersive mode ON — double-tap to exit' : 'Immersive mode OFF');
      // Resize to be safe (some browsers reflow on UI hide)
      setTimeout(onResize, 60);
    }
    function toggleImmersive() {
      setImmersive(!document.body.classList.contains('immersive'));
    }

    function setupDoubleTapImmersive(dom) {
      let lastTap = 0;
      dom.addEventListener('touchend', (e) => {
        if (e.touches.length > 0) return;
        const now = Date.now();
        if (now - lastTap < 320) {
          toggleImmersive();
          e.preventDefault();
          lastTap = 0;
        } else {
          lastTap = now;
        }
      }, { passive: false });
    }

    /* ---------- FAB (mobile floating control) ---------- */
    (function setupFab() {
      const wrap = $('fab-wrap');
      const toggle = $('fab-toggle');
      const menu = $('fab-menu');
      const searchRow = $('fab-search-row');
      const searchInput = $('fab-search-input');
      if (!wrap || !toggle || !menu) return;

      function closeMenu() {
        menu.classList.remove('open');
        searchRow.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = '＋';
      }
      function openMenu() {
        menu.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
        toggle.textContent = '✕';
      }

      toggle.addEventListener('click', () => {
        if (menu.classList.contains('open')) closeMenu();
        else openMenu();
      });

      // Mirror desktop search → keep panels in sync
      searchInput.addEventListener('input', (e) => {
        const desktopInput = $('search-input');
        if (desktopInput) {
          desktopInput.value = e.target.value;
          desktopInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });

      menu.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-fab]');
        if (!btn) return;
        const action = btn.dataset.fab;
        switch (action) {
          case 'search':
            searchRow.classList.toggle('open');
            if (searchRow.classList.contains('open')) {
              setTimeout(() => searchInput.focus(), 50);
            }
            return;
          case 'mode-default': applyMode('default'); break;
          case 'mode-risk': applyMode('risk'); break;
          case 'mode-complexity': applyMode('complexity'); break;
          case 'mode-anomaly': applyMode('anomaly'); break;
          case 'reset': resetCamera(); break;
          case 'dashboard':
            document.body.classList.toggle('show-dashboard');
            if (document.body.classList.contains('show-dashboard')) {
              document.body.classList.remove('immersive');
            }
            break;
          case 'immersive': toggleImmersive(); break;
        }
        closeMenu();
      });

      // Close FAB when tapping the canvas
      document.addEventListener('touchstart', (e) => {
        if (!menu.classList.contains('open')) return;
        if (wrap.contains(e.target)) return;
        closeMenu();
      }, { passive: true });
    })();

    $('open-github').addEventListener('click', () => {
      if (!State.selectedMesh) return;
      const f = State.selectedMesh.userData.file;
      const base = State.repoUrl;
      if (f.url) { window.open(f.url, '_blank'); return; }
      if (base) { window.open(`${base.replace(/\/$/, '')}/blob/main/${f.path}`, '_blank'); return; }
      showToast('No GitHub URL available for this repo');
    });

    $('toggle-preview').addEventListener('click', () => {
      if (!State.selectedMesh) return;
      const f = State.selectedMesh.userData.file;
      const pre = $('code-preview');
      pre.classList.toggle('hidden');
      if (!pre.classList.contains('hidden')) {
        const lang = (f.path || f.name || '').split('.').pop() || 'txt';
        pre.textContent = f.preview || generateMockPreview(f, lang);
      }
    });

    function generateMockPreview(f, lang) {
      return `// ${f.path}
// Lines of code: ${f.size}  ·  Complexity: ${f.complexity.toFixed(1)}
// Risk score: ${(f.risk_score || 0).toFixed(3)}
//
// (Code preview unavailable — connect a source provider
//  to load real file contents here.)

export function ${(f.name || 'module').replace(/[^\w]/g, '_').slice(0, 24)}() {
  // …${f.size} LOC of ${lang.toUpperCase()} omitted
}`;
    }

    /* Timeline */
    const slider = $('timeline-slider');
    const stamp = $('timeline-stamp');
    const playBtn = $('timeline-play');

    function setupTimeline() {
      if (!State.snapshots || State.snapshots.length <= 1) {
        $('timeline-slider').disabled = true;
        $('timeline-play').disabled = true;
        stamp.textContent = 'Single snapshot';
        return;
      }
      slider.max = State.snapshots.length - 1;
      slider.value = State.currentSnapshot;
      stamp.textContent = State.snapshots[State.currentSnapshot].timestamp;
      slider.addEventListener('input', () => {
        const i = Number(slider.value);
        State.currentSnapshot = i;
        stamp.textContent = State.snapshots[i].timestamp;
        const norm = normalizeFiles(State.snapshots[i].files);
        buildCity(norm);
        refreshAnalytics();
        drawMinimap();
      });
      playBtn.addEventListener('click', () => {
        State.timelinePlaying = !State.timelinePlaying;
        playBtn.textContent = State.timelinePlaying ? '⏸' : '▶';
        if (State.timelinePlaying) tickTimeline();
      });
    }
    function tickTimeline() {
      if (!State.timelinePlaying) return;
      const next = (State.currentSnapshot + 1) % State.snapshots.length;
      slider.value = next;
      slider.dispatchEvent(new Event('input'));
      setTimeout(tickTimeline, 1500);
    }

    /* ---------- 7. Detail / Analytics / AI ---------- */
    function showDetailEmpty() {
      $('detail-empty').classList.remove('hidden');
      $('detail-content').classList.add('hidden');
    }
    function populateDetail(f) {
      $('detail-empty').classList.add('hidden');
      $('detail-content').classList.remove('hidden');
      const tag = $('health-tag'), tagText = $('health-tag-text');
      tag.classList.remove('healthy', 'warn', 'risk');
      if (f.risk_score >= 0.66) { tag.classList.add('risk'); tagText.textContent = '🔴 High Risk · Needs Refactor'; }
      else if (f.risk_score >= 0.33 || f.complexity > 30) { tag.classList.add('warn'); tagText.textContent = '⚠️ Watch Closely'; }
      else { tag.classList.add('healthy'); tagText.textContent = '🟢 Healthy'; }

      $('detail-name').textContent = f.name;
      $('detail-path').textContent = f.path || f.name;
      $('detail-complexity').textContent = f.complexity.toFixed(1);
      $('detail-size').textContent = String(f.size);
      $('detail-risk').textContent = (f.risk_score || 0) > 0 ? f.risk_score.toFixed(3) : 'N/A';
      $('detail-height').textContent = `${f.h.toFixed(1)}m`;

      // mini bars (relative to dataset)
      const maxC = Math.max(...State.files.map((x) => x.complexity), 1);
      const maxS = Math.max(...State.files.map((x) => x.size), 1);
      $('bar-complexity').style.width = `${(f.complexity / maxC) * 100}%`;
      $('bar-size').style.width = `${(f.size / maxS) * 100}%`;
      $('bar-risk').style.width = `${clamp(f.risk_score || 0, 0, 1) * 100}%`;
    }

    function refreshAnalytics() {
      const n = State.files.length;
      if (!n) return;
      const totalLoc = State.files.reduce((s, f) => s + f.size, 0);
      const avgC = State.files.reduce((s, f) => s + f.complexity, 0) / n;
      const dirs = new Set(State.files.map((f) => f.directory)).size;

      $('stat-total').textContent = n;
      $('stat-complexity').textContent = avgC.toFixed(1);
      $('stat-loc').textContent = totalLoc.toLocaleString();
      $('stat-districts').textContent = dirs;

      // Risk distribution
      let healthy = 0, watch = 0, risk = 0;
      State.files.forEach((f) => {
        const r = f.risk_score || 0;
        if (r >= 0.66) risk++;
        else if (r >= 0.33) watch++;
        else healthy++;
      });
      const bars = $('dist-bar').children;
      bars[0].style.flex = healthy || 0.01;
      bars[1].style.flex = watch || 0.01;
      bars[2].style.flex = risk || 0.01;

      // Health score (0–100): inverse weighted risk + complexity penalty
      const meanRisk = State.files.reduce((s, f) => s + (f.risk_score || 0), 0) / n;
      const complexityPenalty = clamp(avgC / 60, 0, 1);
      const score = Math.round(clamp(100 - (meanRisk * 70) - (complexityPenalty * 30), 0, 100));
      const ring = $('health-ring');
      ring.style.setProperty('--p', score);
      const c = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#fb7185';
      ring.style.setProperty('--c', c);
      $('health-score-num').textContent = score;
      $('health-desc').textContent = score >= 75 ? 'In great shape' : score >= 50 ? 'Some hotspots to watch' : 'Significant tech debt';

      const badges = $('badges');
      badges.innerHTML = '';
      const add = (cls, label) => {
        const b = document.createElement('span');
        b.className = `badge ${cls}`; b.textContent = label;
        badges.appendChild(b);
      };
      if (score >= 75) add('success', '🟢 CLEAN REPO');
      if (risk >= Math.max(3, n * 0.15)) add('danger', '🔴 HIGH TECH DEBT');
      if (avgC > 25) add('danger', '⚠ COMPLEXITY');
      if (n > 50) add('', '🏙 LARGE PROJECT');

      // Top risky list
      const list = $('risky-list');
      list.innerHTML = '';
      const top = [...State.files].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0)).slice(0, 5);
      top.forEach((f) => {
        const row = document.createElement('div');
        row.className = 'risky-item';
        row.innerHTML = `<span class="name" title="${f.path}">${f.name}</span><span class="score">${(f.risk_score || 0).toFixed(2)}</span>`;
        row.addEventListener('click', () => {
          const m = State.meshes.find((mm) => mm.userData.file.path === f.path);
          if (m) { selectMesh(m); flyToMesh(m, { distanceFactor: 2.4, duration: 900 }); }
        });
        list.appendChild(row);
      });
    }

    /* AI Insights — tries Lovable Cloud edge function first, falls back to mock */
    async function loadAIInsights() {
      const el = $('ai-text');
      el.innerHTML = `<div class="ai-loading"><div class="spinner"></div>Generating insights…</div>`;
      const top = [...State.files]
        .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
        .slice(0, 8)
        .map((f) => ({ path: f.path, risk: +f.risk_score.toFixed(3), complexity: +f.complexity.toFixed(1), size: f.size }));

      try {
        const resp = await fetch('/api/ai-insights', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            files: top,
            totalFiles: State.files.length,
            avgComplexity: State.files.reduce((s, f) => s + f.complexity, 0) / State.files.length
          }),
          // short fail to fall back to mock if endpoint missing
          signal: AbortSignal.timeout(8000)
        });
        if (!resp.ok) throw new Error(`AI endpoint ${resp.status}`);
        const data = await resp.json();
        el.innerHTML = renderAIText(data.text || data.message || JSON.stringify(data, null, 2));
      } catch (e) {
        console.warn('AI endpoint unavailable, using mock insights:', e.message);
        el.innerHTML = renderAIText(buildMockInsights(top));
      }
    }

    function renderAIText(text) {
      const safe = String(text)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
      return safe;
    }

    function buildMockInsights(top) {
      const t = top[0];
      return `**Top hotspot:** \`${t?.path || 'n/a'}\` — risk ${t?.risk?.toFixed(2)}, complexity ${t?.complexity?.toFixed(1)}.
Consider splitting this module into smaller responsibilities and adding test coverage before further changes.

**Pattern detected:** ${top.filter(f => f.complexity > 30).length} files exceed a complexity threshold of 30, suggesting branching/conditional sprawl. Extracting strategy objects or pure helpers tends to reduce this.

**Anomalies:** ${top.filter(f => f.risk > 0.7).length} files combine high risk with above-average size — these are change-magnets and good targets for incremental refactor sprints.

**Suggestion:** prioritize the top 3 risky files for a refactor pass; aim for ≤ 200 LOC per module and < 15 cyclomatic complexity.`;
    }

    $('ai-refresh').addEventListener('click', loadAIInsights);

    /* ---------- Minimap ---------- */
    const minimap = $('minimap-canvas');
    const mctx = minimap.getContext('2d');

    function drawMinimap() {
      if (!State.bounds || !State.files.length) return;
      const W = minimap.width, H = minimap.height;
      const isLight = document.documentElement.classList.contains('light');
      mctx.clearRect(0, 0, W, H);
      mctx.fillStyle = isLight ? 'rgba(15,23,42,0.04)' : 'rgba(2,6,23,0.6)';
      mctx.fillRect(0, 0, W, H);

      const b = State.bounds;
      const cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
      const cw = b.maxX - b.minX, cd = b.maxY - b.minY;
      const pad = 12;
      const scale = Math.min((W - pad * 2) / cw, (H - pad * 2) / cd);

      State.files.forEach((f) => {
        const x = (f.x + f.w / 2 - cx) * scale + W / 2;
        const y = (f.y + f.d / 2 - cy) * scale + H / 2;
        const w = Math.max(2, f.w * scale);
        const d = Math.max(2, f.d * scale);
        mctx.fillStyle = f.color;
        mctx.globalAlpha = 0.85;
        mctx.fillRect(x - w / 2, y - d / 2, w, d);
      });
      mctx.globalAlpha = 1;

      // Camera indicator
      const camX = State.camera.position.x * scale + W / 2;
      const camZ = State.camera.position.z * scale + H / 2;
      mctx.beginPath();
      mctx.arc(camX, camZ, 6, 0, Math.PI * 2);
      mctx.fillStyle = '#38bdf8';
      mctx.fill();
      mctx.strokeStyle = 'white'; mctx.lineWidth = 2; mctx.stroke();

      // View frustum line
      const tx = State.controls.target.x * scale + W / 2;
      const tz = State.controls.target.z * scale + H / 2;
      mctx.beginPath();
      mctx.moveTo(camX, camZ); mctx.lineTo(tx, tz);
      mctx.strokeStyle = 'rgba(56,189,248,0.6)';
      mctx.lineWidth = 1.5;
      mctx.stroke();

      $('minimap-coords').textContent =
        `${State.camera.position.x.toFixed(0)}, ${State.camera.position.z.toFixed(0)}`;
    }

    minimap.addEventListener('click', (e) => {
      if (!State.bounds) return;
      const rect = minimap.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width * minimap.width;
      const py = (e.clientY - rect.top) / rect.height * minimap.height;
      const W = minimap.width, H = minimap.height;
      const b = State.bounds;
      const cw = b.maxX - b.minX, cd = b.maxY - b.minY;
      const pad = 12;
      const scale = Math.min((W - pad * 2) / cw, (H - pad * 2) / cd);
      const worldX = (px - W / 2) / scale;
      const worldZ = (py - H / 2) / scale;
      // keep current height/distance, re-aim
      const offset = State.camera.position.clone().sub(State.controls.target);
      const newTarget = new THREE.Vector3(worldX, State.controls.target.y, worldZ);
      animateCamera(newTarget.clone().add(offset), newTarget, 700);
    });

    /* ---------- Animation loop ---------- */
    let lastTime = performance.now();
    function animate(now = performance.now()) {
      State.rafId = requestAnimationFrame(animate);
      const dt = now - lastTime; lastTime = now;

      if (State.controls) State.controls.update();
      tickFlythrough(dt);

      // Anomaly pulse
      if (State.mode === 'anomaly') {
        const k = 0.5 + 0.5 * Math.sin(now * 0.004);
        State.meshes.forEach((m) => {
          if (m.userData.isOutlier) m.material.emissiveIntensity = 0.45 + k * 0.55;
        });
      }

      // Hover raycast (throttled; skip on mobile + when flying through)
      const rayInterval = isMobile() ? 250 : 60;
      if (!State.flyingThrough && !isMobile() && now - (animate._lastRay || 0) > rayInterval) {
        animate._lastRay = now;
        const hits = pickIntersect();
        updateHover(hits.length ? hits[0].object : null);
      }

      if (State.renderer) State.renderer.render(State.scene, State.camera);

      // Minimap throttled
      if (now - (drawMinimap._last || 0) > 80) {
        drawMinimap._last = now;
        drawMinimap();
      }
    }

    /* ---------- Bootstrap ---------- */
    function detectRepoUrl(payload) {
      if (!payload) return null;
      if (typeof payload.repo_url === 'string') return payload.repo_url;
      if (typeof payload.repository === 'string') return payload.repository;
      if (payload.repo && typeof payload.repo.url === 'string') return payload.repo.url;
      return null;
    }

    function boot() {
      const data = readCityPayload();
      if (!data) { emptyState.classList.remove('hidden'); return; }
      State.payload = data;
      State.repoUrl = detectRepoUrl(data);

      const snapshots = extractSnapshots(data);
      if (snapshots && snapshots.length) {
        State.snapshots = snapshots;
        State.currentSnapshot = snapshots.length - 1;
      }

      const baseFiles = snapshots
        ? normalizeFiles(snapshots[State.currentSnapshot].files)
        : normalizeFiles(extractFiles(data));

      if (!baseFiles.length) { emptyState.classList.remove('hidden'); return; }

      initScene();
      buildCity(baseFiles);
      refreshAnalytics();
      setupTimeline();
      drawMinimap();
      loadAIInsights();
      animate();
    }

    /* ================================================================
       PRO TOOLS — Advanced features (additive, non-breaking)
       Hooks into existing State + meshes; never mutates existing handlers.
    ================================================================ */
    const ProTools = (() => {
      const state = {
        heatmap: false,
        deps: false,
        alerts: false,
        clusters: false,
        focused: null,         // mesh currently in focus mode
        depsGroup: null,       // THREE.Group of dependency lines
        heatmapMesh: null,     // ground heat plane
        districtLabels: [],    // {el, x, z}
        activeFilters: new Set(),  // empty = show all
        allExtensions: [],
      };

      function ext(path) {
        const m = String(path || '').match(/\.([a-zA-Z0-9]+)$/);
        return m ? m[1].toLowerCase() : 'other';
      }

      /* ---------- Inject DOM ---------- */
      function injectDOM() {
        // Pro toolbar
        const tb = document.createElement('aside');
        tb.className = 'pro-toolbar';
        tb.id = 'pro-toolbar';
        tb.innerHTML = `
          <div class="pt-title">Pro Tools</div>
          <button class="pt-btn" id="pt-heatmap" title="Toggle risk heatmap"><span class="pt-ic">🔥</span><span>Heatmap</span></button>
          <button class="pt-btn" id="pt-deps" title="Toggle dependency lines"><span class="pt-ic">🔗</span><span>Dependencies</span></button>
          <button class="pt-btn" id="pt-alerts" title="Pulse top risky files"><span class="pt-ic">⚠️</span><span>Risk Alerts</span></button>
          <button class="pt-btn" id="pt-clusters" title="Show district labels"><span class="pt-ic">🏘</span><span>Clusters</span></button>
          <button class="pt-btn" id="pt-worst" title="Highlight & tour the 10 worst files"><span class="pt-ic">🧠</span><span>Worst 10</span></button>
          <button class="pt-btn" id="pt-ai-sheet" title="Show AI insight sheet"><span class="pt-ic">🤖</span><span>AI Sheet</span></button>
        `;
        document.body.appendChild(tb);

        // Filter chip bar
        const fb = document.createElement('div');
        fb.className = 'filter-bar';
        fb.id = 'filter-bar';
        document.body.appendChild(fb);

        // Focus-exit button
        const fx = document.createElement('button');
        fx.className = 'focus-exit';
        fx.id = 'focus-exit';
        fx.innerHTML = '✕ Exit Focus';
        document.body.appendChild(fx);

        // AI Bottom Sheet
        const sheet = document.createElement('div');
        sheet.className = 'ai-sheet';
        sheet.id = 'ai-sheet';
        sheet.innerHTML = `
          <div class="ai-sheet-grip"></div>
          <div class="ai-sheet-title">
            <span>🤖 AI Insight</span>
            <button id="ai-sheet-close">Close</button>
          </div>
          <div class="ai-sheet-body" id="ai-sheet-body">
            Tap any building for contextual AI insights.
          </div>
        `;
        document.body.appendChild(sheet);
      }

      /* ---------- Heatmap ---------- */
      function buildHeatmap() {
        if (!State.bounds || !State.scene) return;
        clearHeatmap();
        const cw = State.bounds.maxX - State.bounds.minX;
        const cd = State.bounds.maxY - State.bounds.minY;
        const size = Math.max(80, Math.max(cw, cd)) * 1.4;
        // Build a canvas texture sampling risk density
        const RES = 128;
        const cnv = document.createElement('canvas');
        cnv.width = RES; cnv.height = RES;
        const ctx = cnv.getContext('2d');
        ctx.fillStyle = 'rgba(0,0,0,0)';
        ctx.fillRect(0, 0, RES, RES);
        const cx = (State.bounds.minX + State.bounds.maxX) / 2;
        const cy = (State.bounds.minY + State.bounds.maxY) / 2;
        // Splatter risk gradients
        State.files.forEach((f) => {
          const r = clamp(f.risk_score || 0, 0, 1);
          if (r < 0.05) return;
          const u = ((f.x + f.w / 2 - cx) / size + 0.5) * RES;
          const v = ((f.y + f.d / 2 - cy) / size + 0.5) * RES;
          const rad = Math.max(8, Math.sqrt(f.size) * 1.2 * (RES / size));
          const grad = ctx.createRadialGradient(u, v, 0, u, v, rad);
          // green->yellow->red
          const col = r < 0.33 ? `rgba(34,197,94,${0.4 * r + 0.2})`
                    : r < 0.66 ? `rgba(245,158,11,${0.6 * r})`
                               : `rgba(239,68,68,${0.55 + 0.4 * r})`;
          grad.addColorStop(0, col);
          grad.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = grad;
          ctx.beginPath(); ctx.arc(u, v, rad, 0, Math.PI * 2); ctx.fill();
        });
        const tex = new THREE.CanvasTexture(cnv);
        tex.minFilter = THREE.LinearFilter;
        const mat = new THREE.MeshBasicMaterial({
          map: tex, transparent: true, opacity: 0, depthWrite: false
        });
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(size, size), mat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = 0.18; // just above ground/grid
        plane.renderOrder = 2;
        State.scene.add(plane);
        state.heatmapMesh = plane;
        // Fade in
        const start = performance.now();
        (function fade() {
          const t = clamp((performance.now() - start) / 500, 0, 1);
          mat.opacity = 0.85 * t;
          if (t < 1) requestAnimationFrame(fade);
        })();
      }
      function clearHeatmap() {
        if (state.heatmapMesh) {
          State.scene.remove(state.heatmapMesh);
          state.heatmapMesh.geometry.dispose();
          if (state.heatmapMesh.material.map) state.heatmapMesh.material.map.dispose();
          state.heatmapMesh.material.dispose();
          state.heatmapMesh = null;
        }
      }
      function toggleHeatmap() {
        state.heatmap = !state.heatmap;
        $('pt-heatmap').classList.toggle('active', state.heatmap);
        if (state.heatmap) buildHeatmap(); else clearHeatmap();
        showToast(state.heatmap ? '🔥 Heatmap mode on' : 'Heatmap off');
      }

      /* ---------- Dependency lines ---------- */
      function extractDeps() {
        // Look for dep info on each file: deps / dependencies / imports / edges (array of paths)
        // Also accept payload.edges = [{from, to}]
        const map = new Map(State.files.map((f) => [f.path, f]));
        const edges = [];
        const payload = State.payload || {};
        if (Array.isArray(payload.edges)) {
          payload.edges.forEach((e) => {
            const a = map.get(e.from || e.source); const b = map.get(e.to || e.target);
            if (a && b) edges.push([a, b]);
          });
        }
        State.files.forEach((f) => {
          const list = f.deps || f.dependencies || f.imports || [];
          if (!Array.isArray(list)) return;
          list.forEach((p) => {
            const target = map.get(p) || State.files.find((x) => x.path && x.path.endsWith(p));
            if (target && target !== f) edges.push([f, target]);
          });
        });
        return edges;
      }
      function buildDeps() {
        clearDeps();
        const edges = extractDeps();
        if (!edges.length) {
          showToast('No dependency data in payload');
          state.deps = false;
          $('pt-deps').classList.remove('active');
          return;
        }
        const grp = new THREE.Group();
        const mat = new THREE.LineBasicMaterial({
          color: 0x38bdf8, transparent: true, opacity: 0.55
        });
        const cx = (State.bounds.minX + State.bounds.maxX) / 2;
        const cy = (State.bounds.minY + State.bounds.maxY) / 2;
        edges.forEach(([a, b]) => {
          const ax = a.x + a.w / 2 - cx, az = a.y + a.d / 2 - cy;
          const bx = b.x + b.w / 2 - cx, bz = b.y + b.d / 2 - cy;
          const ay = a.h * 0.6, by = b.h * 0.6;
          // Curve: midpoint lifted
          const mid = new THREE.Vector3((ax + bx) / 2, Math.max(ay, by) + 12, (az + bz) / 2);
          const curve = new THREE.QuadraticBezierCurve3(
            new THREE.Vector3(ax, ay, az), mid, new THREE.Vector3(bx, by, bz)
          );
          const pts = curve.getPoints(20);
          const geo = new THREE.BufferGeometry().setFromPoints(pts);
          grp.add(new THREE.Line(geo, mat));
        });
        State.scene.add(grp);
        state.depsGroup = grp;
        showToast(`🔗 ${edges.length} dependency edge${edges.length !== 1 ? 's' : ''}`);
      }
      function clearDeps() {
        if (state.depsGroup) {
          State.scene.remove(state.depsGroup);
          state.depsGroup.traverse((o) => {
            if (o.geometry) o.geometry.dispose();
            if (o.material) o.material.dispose();
          });
          state.depsGroup = null;
        }
      }
      function toggleDeps() {
        state.deps = !state.deps;
        $('pt-deps').classList.toggle('active', state.deps);
        if (state.deps) buildDeps(); else { clearDeps(); showToast('Dependencies hidden'); }
      }

      /* ---------- Risk alerts (pulsing top 5) ---------- */
      function setAlerts(on) {
        state.alerts = on;
        $('pt-alerts').classList.toggle('active', on);
        const top = [...State.files]
          .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
          .slice(0, 5)
          .map((f) => f.path);
        const set = new Set(top);
        State.meshes.forEach((m) => {
          m.userData.isAlert = on && set.has(m.userData.file.path);
        });
        // Mirror in risky list rows
        document.querySelectorAll('.risky-item').forEach((row) => {
          if (on) row.classList.add('alert'); else row.classList.remove('alert');
        });
        showToast(on ? '⚠️ Risk alerts on' : 'Risk alerts off');
      }
      function toggleAlerts() { setAlerts(!state.alerts); }
      function tickAlerts(now) {
        if (!state.alerts) return;
        const k = 0.5 + 0.5 * Math.sin(now * 0.006);
        State.meshes.forEach((m) => {
          if (m.userData.isAlert) {
            m.material.emissiveIntensity = 0.5 + k * 0.6;
          }
        });
      }

      /* ---------- Cluster (district) labels ---------- */
      function buildClusterLabels() {
        clearClusterLabels();
        if (!State.bounds) return;
        const groups = new Map();
        const cx = (State.bounds.minX + State.bounds.maxX) / 2;
        const cy = (State.bounds.minY + State.bounds.maxY) / 2;
        State.files.forEach((f) => {
          const k = f.directory || '/';
          if (!groups.has(k)) groups.set(k, { sx: 0, sz: 0, n: 0 });
          const g = groups.get(k);
          g.sx += f.x + f.w / 2 - cx;
          g.sz += f.y + f.d / 2 - cy;
          g.n++;
        });
        groups.forEach((g, dir) => {
          const el = document.createElement('div');
          el.className = 'district-label';
          el.textContent = (dir === '/' ? 'root' : dir.split('/').pop() || dir);
          el.title = dir;
          document.body.appendChild(el);
          state.districtLabels.push({ el, x: g.sx / g.n, z: g.sz / g.n });
        });
        // trigger fade-in
        requestAnimationFrame(() => state.districtLabels.forEach((d) => d.el.classList.add('visible')));
      }
      function clearClusterLabels() {
        state.districtLabels.forEach((d) => d.el.remove());
        state.districtLabels = [];
      }
      function tickClusterLabels() {
        if (!state.clusters || !state.districtLabels.length || !State.camera) return;
        const v = new THREE.Vector3();
        const W = window.innerWidth, H = window.innerHeight;
        state.districtLabels.forEach((d) => {
          v.set(d.x, 6, d.z).project(State.camera);
          const sx = (v.x * 0.5 + 0.5) * W;
          const sy = (-v.y * 0.5 + 0.5) * H;
          const onScreen = v.z > -1 && v.z < 1;
          d.el.style.left = sx + 'px';
          d.el.style.top = sy + 'px';
          d.el.style.opacity = onScreen ? '0.9' : '0';
        });
      }
      function toggleClusters() {
        state.clusters = !state.clusters;
        $('pt-clusters').classList.toggle('active', state.clusters);
        if (state.clusters) buildClusterLabels();
        else clearClusterLabels();
      }

      /* ---------- File-type filters ---------- */
      function buildFilterBar() {
        const bar = $('filter-bar');
        bar.innerHTML = '';
        const counts = new Map();
        State.files.forEach((f) => {
          const e = ext(f.path || f.name);
          counts.set(e, (counts.get(e) || 0) + 1);
        });
        const exts = [...counts.entries()].sort((a, b) => b[1] - a[1]);
        state.allExtensions = exts.map((e) => e[0]);
        // "All" chip
        const allChip = document.createElement('button');
        allChip.className = 'filter-chip active';
        allChip.dataset.ext = '__all__';
        allChip.innerHTML = `All <span class="cnt">${State.files.length}</span>`;
        bar.appendChild(allChip);
        exts.slice(0, 14).forEach(([e, c]) => {
          const chip = document.createElement('button');
          chip.className = 'filter-chip';
          chip.dataset.ext = e;
          chip.innerHTML = `.${e} <span class="cnt">${c}</span>`;
          bar.appendChild(chip);
        });
        bar.addEventListener('click', (ev) => {
          const chip = ev.target.closest('.filter-chip');
          if (!chip) return;
          const e = chip.dataset.ext;
          if (e === '__all__') {
            state.activeFilters.clear();
            bar.querySelectorAll('.filter-chip').forEach((c) => c.classList.remove('active'));
            chip.classList.add('active');
          } else {
            bar.querySelector('[data-ext="__all__"]').classList.remove('active');
            chip.classList.toggle('active');
            if (chip.classList.contains('active')) state.activeFilters.add(e);
            else state.activeFilters.delete(e);
            if (!state.activeFilters.size) {
              bar.querySelector('[data-ext="__all__"]').classList.add('active');
            }
          }
          applyFilters();
        }, { once: false });
      }
      function applyFilters() {
        const active = state.activeFilters;
        State.meshes.forEach((m) => {
          const e = ext(m.userData.file.path || m.userData.file.name);
          const visible = !active.size || active.has(e);
          // Smooth: use opacity, keep raycast for visible only
          if (visible) {
            m.visible = true;
            m.material.transparent = false;
            m.material.opacity = 1;
          } else {
            m.material.transparent = true;
            const start = m.material.opacity;
            tweenValue(start, 0.04, 280, (v) => {
              m.material.opacity = v;
              if (v <= 0.06) m.visible = false; else m.visible = true;
            });
          }
        });
      }

      /* ---------- Smart highlight: top 10 worst, sequential focus ---------- */
      let worstSeq = null;
      function showWorst() {
        const worst = [...State.files]
          .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
          .slice(0, 10);
        if (!worst.length) return;
        // Dim everything not in worst
        const set = new Set(worst.map((f) => f.path));
        State.meshes.forEach((m) => {
          const inSet = set.has(m.userData.file.path);
          m.material.transparent = !inSet;
          m.material.opacity = inSet ? 1 : 0.1;
          if (inSet) {
            m.userData.isAlert = true; // pulse
          }
        });
        $('pt-worst').classList.add('active');
        showToast('🧠 Touring 10 worst files…');
        let i = 0;
        if (worstSeq) clearInterval(worstSeq);
        const tour = () => {
          if (i >= worst.length) {
            clearInterval(worstSeq); worstSeq = null;
            showToast('Tour complete · tap Worst 10 again to reset');
            return;
          }
          const f = worst[i++];
          const m = State.meshes.find((mm) => mm.userData.file.path === f.path);
          if (m) { selectMesh(m); flyToMesh(m, { distanceFactor: 2.4, duration: 1100 }); pushAISheet(f); }
        };
        tour();
        worstSeq = setInterval(tour, 2600);
      }
      function resetWorst() {
        if (worstSeq) { clearInterval(worstSeq); worstSeq = null; }
        State.meshes.forEach((m) => {
          m.material.transparent = false;
          m.material.opacity = 1;
          m.userData.isAlert = state.alerts && m.userData.isAlert;
        });
        $('pt-worst').classList.remove('active');
      }
      function toggleWorst() {
        if ($('pt-worst').classList.contains('active')) resetWorst();
        else showWorst();
      }

      /* ---------- Focus mode (with exit button) ---------- */
      function enterFocus(mesh) {
        state.focused = mesh;
        $('focus-exit').classList.add('visible');
      }
      function exitFocus() {
        state.focused = null;
        $('focus-exit').classList.remove('visible');
        State.meshes.forEach((m) => { m.material.transparent = false; m.material.opacity = 1; });
        deselect();
        if (State.bounds) {
          const cw = State.bounds.maxX - State.bounds.minX;
          const cd = State.bounds.maxY - State.bounds.minY;
          const dist = Math.max(cw, cd) * 1.15;
          animateCamera(
            new THREE.Vector3(dist * 0.75, State.bounds.maxH + dist * 0.55, dist),
            new THREE.Vector3(0, State.bounds.maxH * 0.22, 0),
            900
          );
        }
      }

      /* ---------- AI Insight Sheet ---------- */
      function pushAISheet(file) {
        const sheet = $('ai-sheet');
        const body = $('ai-sheet-body');
        const r = file.risk_score || 0;
        const tag = r >= 0.66 ? '<span class="pill risk">High Risk</span>'
                  : r >= 0.33 ? '<span class="pill warn">Watch</span>'
                              : '<span class="pill">Healthy</span>';
        const reasons = [];
        if (file.complexity > 30) reasons.push(`High cyclomatic complexity (${file.complexity.toFixed(1)})`);
        if (file.size > 400) reasons.push(`Large file (${file.size} LOC) — hard to reason about`);
        if (r > 0.5) reasons.push(`Elevated risk score (${r.toFixed(2)}) — frequent change-magnet`);
        if (!reasons.length) reasons.push('No major risk signals detected.');
        const suggestions = [];
        if (file.complexity > 30) suggestions.push('Extract helper functions / strategy objects to flatten branching.');
        if (file.size > 400) suggestions.push('Split into smaller modules by responsibility (~200 LOC ceiling).');
        if (r > 0.5) suggestions.push('Add focused tests before any further changes; isolate side-effects.');
        if (!suggestions.length) suggestions.push('Looks healthy — keep current patterns.');

        body.innerHTML = `
          <div class="ai-row">${tag}<strong>${file.name}</strong></div>
          <div style="font-size:11px;color:var(--text-faint);margin-bottom:6px;">${file.path || ''}</div>
          <div><strong>Why it matters</strong><ul style="margin:4px 0 8px 18px;padding:0;">
            ${reasons.map((x) => `<li>${x}</li>`).join('')}
          </ul></div>
          <div><strong>Suggested improvements</strong><ul style="margin:4px 0 0 18px;padding:0;">
            ${suggestions.map((x) => `<li>${x}</li>`).join('')}
          </ul></div>
        `;
        sheet.classList.add('visible');
      }
      function hideAISheet() { $('ai-sheet').classList.remove('visible'); }

      /* ---------- Wiring ---------- */
      function wire() {
        $('pt-heatmap').addEventListener('click', toggleHeatmap);
        $('pt-deps').addEventListener('click', toggleDeps);
        $('pt-alerts').addEventListener('click', toggleAlerts);
        $('pt-clusters').addEventListener('click', toggleClusters);
        $('pt-worst').addEventListener('click', toggleWorst);
        $('pt-ai-sheet').addEventListener('click', () => {
          if ($('ai-sheet').classList.contains('visible')) hideAISheet();
          else if (State.selectedMesh) pushAISheet(State.selectedMesh.userData.file);
          else showToast('Tap a building first');
        });
        $('ai-sheet-close').addEventListener('click', hideAISheet);
        $('focus-exit').addEventListener('click', exitFocus);

        // Hook clicks: when a building is clicked, push AI sheet + register focus
        // (We listen at capture phase on canvas so existing onClick still runs.)
        const dom = State.renderer && State.renderer.domElement;
        if (dom) {
          dom.addEventListener('click', () => {
            // Defer one frame so existing handler sets selectedMesh first
            requestAnimationFrame(() => {
              if (State.selectedMesh) {
                pushAISheet(State.selectedMesh.userData.file);
                enterFocus(State.selectedMesh);
              }
            });
          });
          dom.addEventListener('dblclick', () => {
            requestAnimationFrame(() => {
              if (State.selectedMesh) {
                pushAISheet(State.selectedMesh.userData.file);
                enterFocus(State.selectedMesh);
              }
            });
          });
        }

        // Rebuild filter bar after city built (handles snapshot changes too)
        buildFilterBar();
      }

      /* ---------- Per-frame tick ---------- */
      function tick(now) {
        tickAlerts(now);
        tickClusterLabels();
      }

      return {
        init() {
          injectDOM();
          // Defer wiring until scene is ready (boot() calls initScene + buildCity)
          requestAnimationFrame(() => {
            if (!State.renderer) return setTimeout(this.init.bind(this), 60);
            wire();
          });
        },
        tick,
        rebuildAfterSnapshot() {
          // Called when the user changes snapshot via timeline
          buildFilterBar();
          if (state.heatmap) buildHeatmap();
          if (state.deps) buildDeps();
          if (state.clusters) buildClusterLabels();
          if (state.alerts) setAlerts(true);
        }
      };
    })();

    /* Hook into the existing animate loop without modifying it:
       Wrap requestAnimationFrame on first call by patching renderer.render once
       — simpler approach: just attach a separate rAF that runs in parallel. */
    (function startProToolsTicker() {
      function loop(now) {
        ProTools.tick(now);
        requestAnimationFrame(loop);
      }
      requestAnimationFrame(loop);
    })();

    /* Patch timeline change to refresh ProTools-built artifacts */
    (function hookSnapshotChange() {
      const origSlider = document.getElementById('timeline-slider');
      if (!origSlider) return;
      origSlider.addEventListener('input', () => {
        // Run after existing handler rebuilds the city
        setTimeout(() => ProTools.rebuildAfterSnapshot(), 50);
      });
    })();

    /* Initialize ProTools after boot */
    const _origBoot = typeof boot === 'function' ? boot : null;

    boot();
    ProTools.init();
  </script>
</body>

</html>{% endraw %}"""


@app.route('/health', methods=['GET'])
def health() -> Any:
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index() -> Any:
    """Serve the Pro UI."""
    return render_template_string(INDEX_HTML)


@app.route('/city')
def city_view() -> Any:
    return render_template_string(CITY_HTML)


@app.route("/login")
def login() -> Any:
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return (
            "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
            500,
        )

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    redirect_uri = REDIRECT_URI or "https://devcity-ai-1.onrender.com/oauth/callback"
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": GITHUB_OAUTH_SCOPES,
        "state": state,
        "allow_signup": "true",
    }
    authorize_url = "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(
        params
    )
    return redirect(authorize_url)


@app.route("/oauth/callback")
def oauth_callback() -> Any:
    error = request.args.get("error")
    if error:
        desc = request.args.get("error_description") or error
        return f"GitHub OAuth error: {desc}", 400

    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.get("oauth_state")
    session.pop("oauth_state", None)

    if not code or not state or not expected_state or state != expected_state:
        return "Invalid OAuth state. Please try logging in again.", 400

    redirect_uri = REDIRECT_URI or "https://devcity-ai-1.onrender.com/oauth/callback"

    token_res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            **({"redirect_uri": redirect_uri} if redirect_uri else {}),
        },
        timeout=30,
    )
    token_res.raise_for_status()
    token_payload = token_res.json()
    access_token = token_payload.get("access_token")
    if not access_token:
        return "Failed to get GitHub access token.", 400

    user_res = requests.get(
        "https://api.github.com/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=30,
    )
    user_res.raise_for_status()
    user = user_res.json()

    session["github_access_token"] = access_token
    session["github_user"] = {
        "id": user.get("id"),
        "login": user.get("login"),
        "name": user.get("name"),
        "avatar_url": user.get("avatar_url"),
    }

    return redirect("/")


@app.route("/logout")
def logout() -> Any:
    session.clear()
    return redirect("/")


@app.route("/api/me", methods=["GET"])
def me() -> Any:
    if not _is_logged_in():
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": session.get("github_user")}), 200


@app.route('/api/analyze', methods=['POST'])
def analyze() -> Any:
    guard = _login_required()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    repo_url = (data.get('repo_url') or '').strip()
    label = (data.get('label') or '').strip()

    session_token = session.get("github_access_token") if _is_logged_in() else ""
    github_token = (
        (data.get("github_token") or "")
        or (session_token or "")
        or (os.environ.get("GITHUB_TOKEN") or "")
    ).strip()

    if not repo_url:
        return _json_error("Repository URL is required", "BAD_REQUEST", 400)

    LOGGER.info("[PRO] Received repo URL: %s", repo_url)

    try:
        now = datetime.utcnow()
        timestamp = now.strftime('%Y%m%d-%H%M%S')
        snapshot_id = f"{timestamp}"
        snapshot_meta = {
            "id": snapshot_id,
            "created_at": now.isoformat() + "Z",
            "repo_url": repo_url,
            "label": label or repo_url,
            "file_count": 0,
        }

        city_data = scan_pipeline.analyze_and_store(
            repo_url=repo_url,
            label=label,
            snapshot_meta=snapshot_meta,
            github_token=github_token or None,
        )
        snapshot_meta["file_count"] = len(city_data)

        return jsonify({
            'success': True,
            'data': city_data,
            'snapshot': snapshot_meta,
            'message': "Analysis complete",
        })
    except PermissionError as error:
        return _json_error(
            "Clone failed - check token permissions",
            "SCAN_FAILED",
            403,
            str(error),
        )
    except FileNotFoundError as error:
        return _json_error(
            "git not found on PATH",
            "SERVER_ERROR",
            500,
            str(error),
        )
    except Exception as e:
        LOGGER.exception("[PRO] Unexpected error in /api/analyze")
        return _json_error(str(e), "SERVER_ERROR", 500)


@app.route('/api/data', methods=['GET'])
def get_current_data() -> Any:
    data_file = BASE_DIR / 'city_data2.json'
    if data_file.exists():
        try:
            return jsonify(json.loads(data_file.read_text(encoding='utf-8')))
        except json.JSONDecodeError:
            return _json_error(
                'The city_data2.json file is not valid JSON.',
                'BAD_REQUEST',
                400,
            )
    return jsonify([])


@app.route('/api/snapshots', methods=['GET'])
def list_snapshots() -> Any:
    guard = _login_required()
    if guard:
        return guard
    snapshots = []
    for path in sorted(SNAPSHOT_DIR.iterdir(), key=lambda entry: entry.name):
        if path.suffix != '.json':
            continue
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            meta = payload.get('meta', {})
            snapshots.append(meta)
        except Exception as e:
            LOGGER.warning("[PRO] Failed to load snapshot %s: %s", path.name, e)
    snapshots.sort(key=lambda s: s.get('id', ''), reverse=True)
    return jsonify(snapshots)


@app.route('/api/snapshots/<snapshot_id>', methods=['GET'])
def get_snapshot(snapshot_id: str) -> Any:
    guard = _login_required()
    if guard:
        return guard
    path = SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not path.exists():
        return _json_error('Snapshot not found', 'NOT_FOUND', 404)
    payload = json.loads(path.read_text(encoding='utf-8'))
    return jsonify(payload)


@app.route('/api/snapshots/<snapshot_id>/risk', methods=['GET'])
def get_snapshot_risk(snapshot_id: str) -> Any:
    guard = _login_required()
    if guard:
        return guard
    path = SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not path.exists():
        return _json_error('Snapshot not found', 'NOT_FOUND', 404)
    payload = json.loads(path.read_text(encoding='utf-8'))
    data = payload.get('data', [])
    enriched = []
    for rec in data:
        enriched.append({
            "name": rec.get("name"),
            "size": rec.get("size"),
            "h": rec.get("h"),
            "risk_score": rec.get("risk_score", 0.0),
            "anomaly_score": rec.get("anomaly_score", 0.0),
        })
    enriched.sort(key=lambda r: r.get("risk_score", 0.0), reverse=True)
    return jsonify(enriched)


@app.route('/api/model_status', methods=['GET'])
def model_status() -> Any:
    from model_loader import get_model_meta

    meta = get_model_meta()
    if meta is None:
        return jsonify({"trained": False})
    return jsonify({"trained": True, **meta})


@app.route('/api/my_repos', methods=['GET'])
def my_repos() -> Any:
    guard = _login_required()
    if guard:
        return guard

    access_token = session.get('github_access_token')
    if not access_token:
        return _json_error('GitHub access token missing', 'AUTH_REQUIRED', 401)

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}',
    }

    url = 'https://api.github.com/user/repos'
    params = {'per_page': 100, 'type': 'all', 'sort': 'updated'}
    repos = []

    try:
        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            page = resp.json() or []
            repos.extend(page)

            link = resp.headers.get('Link', '')
            if 'rel="next"' in link:
                import re
                m = re.search(r'<([^>]+)>;\s*rel="next"', link)
                if m:
                    url = m.group(1)
                    params = None
                    continue
            break
    except requests.HTTPError as e:
        response = getattr(e, 'response', None)
        if response is not None and response.status_code == 403:
            return _json_error('GitHub rate limit exceeded', 'RATE_LIMIT', 429, str(e))
        return _json_error('Failed to fetch repos', 'SERVER_ERROR', 502, str(e))
    except Exception as e:
        return _json_error('Unexpected error', 'SERVER_ERROR', 500, str(e))

    simplified = []
    for r in repos:
        simplified.append({
            'id': r.get('id'),
            'name': r.get('name'),
            'full_name': r.get('full_name'),
            'private': r.get('private'),
            'html_url': r.get('html_url'),
            'description': r.get('description'),
            'language': r.get('language'),
            'updated_at': r.get('updated_at'),
            'stargazers_count': r.get('stargazers_count'),
            'forks_count': r.get('forks_count'),
            'owner': {
                'login': r.get('owner', {}).get('login'),
                'id': r.get('owner', {}).get('id'),
            },
        })

    simplified.sort(key=lambda x: x.get('updated_at') or '', reverse=True)
    return jsonify(simplified)


@app.route('/api/diff', methods=['GET'])
def diff_snapshots() -> Any:
    guard = _login_required()
    if guard:
        return guard
    snap1_id = request.args.get('snap1')
    snap2_id = request.args.get('snap2')

    if not snap1_id or not snap2_id:
        return _json_error('Two snapshot IDs are required', 'BAD_REQUEST', 400)

    path1 = SNAPSHOT_DIR / f"{snap1_id}.json"
    path2 = SNAPSHOT_DIR / f"{snap2_id}.json"

    if not path1.exists() or not path2.exists():
        return _json_error('One or both snapshots not found', 'NOT_FOUND', 404)

    data1 = json.loads(path1.read_text(encoding='utf-8'))['data']
    data2 = json.loads(path2.read_text(encoding='utf-8'))['data']

    files1 = {(f.get('path') or f['name']): f for f in data1}
    files2 = {(f.get('path') or f['name']): f for f in data2}

    added = [f for name, f in files2.items() if name not in files1]
    removed = [f for name, f in files1.items() if name not in files2]

    modified = []
    for path_key, f2 in files2.items():
        if path_key in files1:
            f1 = files1[path_key]
            if f1.get('complexity') != f2.get('complexity') or f1.get('size') != f2.get('size'):
                modified.append({
                    'name': f2.get('name'),
                    'path': path_key,
                    'complexity_change': (f2.get('complexity') or 0) - (f1.get('complexity') or 0),
                    'size_change': (f2.get('size') or 0) - (f1.get('size') or 0),
                    'risk_score_change': (f2.get('risk_score') or 0) - (f1.get('risk_score') or 0),
                    'new_data': f2,
                })

    return jsonify({
        'added': added,
        'removed': removed,
        'modified': modified,
    })


# Gunicorn entry point
application = app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOGGER.info("DevCity AI starting...")
    LOGGER.info("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
