from flask import Flask, request, jsonify, send_file, redirect, session, url_for
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
# repo scope required for /api/my_repos to return private repositories
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


@app.route('/health', methods=['GET'])
def health() -> Any:
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index() -> Any:
    """Serve the Pro UI."""
    return send_file(BASE_DIR / "index.html")


@app.route('/city')
def city_view() -> Any:
    return send_file(BASE_DIR / "city.html")


@app.route("/login")
def login() -> Any:
    """
    Start GitHub OAuth flow.

    Requires env vars:
      - GITHUB_CLIENT_ID
      - GITHUB_CLIENT_SECRET
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return (
            "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
            500,
        )

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    # Prefer explicit REDIRECT_URI from environment (must match GitHub app)
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
    """GitHub OAuth callback handler."""
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

    # Compute redirect_uri used in the flow (must match GitHub app)
    redirect_uri = REDIRECT_URI or "https://devcity-ai-1.onrender.com/oauth/callback"

    token_res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret":GITHUB_CLIENT_SECRET,
            "code": code,
            # Include redirect_uri if we supplied one when starting the flow
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
    """Return current login status for the UI."""
    if not _is_logged_in():
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": session.get("github_user")}), 200



@app.route('/api/analyze', methods=['POST'])
def analyze() -> Any:
    """
    Analyze a GitHub repository and create a saved snapshot.

    Request JSON:
    {
      "repo_url": "...",
      "label": "optional human-friendly snapshot name",
      "github_token": "optional GitHub personal access token"
    }
    """
    guard = _login_required()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    repo_url = (data.get('repo_url') or '').strip()
    label = (data.get('label') or '').strip()
    
    # Prioritize token from request, fall back to session token, then environment variable
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
            # file_count will be filled after analysis
            "file_count": 0,
        }

        # Run the scanner + feature engineering + SQLite storage pipeline
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
    """
    Get the latest city data in this pro instance (not tied to a snapshot).
    """
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
    """Return metadata for all saved snapshots."""
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
    # Sort newest first
    snapshots.sort(key=lambda s: s.get('id', ''), reverse=True)
    return jsonify(snapshots)


@app.route('/api/snapshots/<snapshot_id>', methods=['GET'])
def get_snapshot(snapshot_id: str) -> Any:
    """Return data for a single snapshot."""
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
    """
    Return files and their risk/anomaly scores for a snapshot,
    sorted by risk descending.
    """
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
    """Return the authenticated user's repositories (public + private).

    Requires the user to be logged in and that the OAuth token has the
    `repo` scope to access private repositories. Results are paginated
    transparently and returned as a simplified list.
    """
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

    # Simplify the payload we return to the UI
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

    # Sort by updated_at desc to show most recent first
    simplified.sort(key=lambda x: x.get('updated_at') or '', reverse=True)
    return jsonify(simplified)


@app.route('/api/diff', methods=['GET'])
def diff_snapshots() -> Any:
    """Compare two snapshots and return the delta."""
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
    LOGGER.info("Visit: http://localhost:5100")
    app.run(debug=True, host='0.0.0.0', port=5100)

