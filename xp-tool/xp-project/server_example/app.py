"""
Example endpoints implementing the `xp login` flow, meant to be dropped
into (or adapted for) the web server you already have.

This assumes you already have some way to know who's logged in via a
normal browser session (Flask-Login, a session cookie, whatever you use
today). Swap out `get_current_user()` / `DEV_USERS` for your real
implementation - everything else (code issuance, PKCE verification,
redirect_uri checks) is flow logic you can keep as-is.

Endpoints:
    GET/POST /cli/authorize   - browser lands here from `xp login`
    POST     /cli/token       - xp exchanges the code for a token here

Flow:
    1. xp opens /cli/authorize?state=...&redirect_uri=...&code_challenge=...
    2. If the browser session isn't logged in, show/redirect to your
       normal login page first.
    3. Once logged in, generate a short-lived one-time `code`, store it
       server-side alongside the code_challenge + redirect_uri + user id,
       and redirect the browser to redirect_uri?code=...&state=...
    4. xp POSTs {code, code_verifier, redirect_uri} to /cli/token.
    5. Verify code_verifier against the stored code_challenge (PKCE),
       verify the code hasn't expired or been used, verify redirect_uri
       matches, issue a real API token, and return it as JSON.

Run for dev:
    pip install flask
    python server_example/app.py
    # serves on http://localhost:5000
"""
import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

from flask import Flask, request, redirect, session, render_template_string, jsonify

app = Flask(__name__)
app.secret_key = "dev-only-secret-change-me"  # dev only - use a real secret in prod

# --- In-memory demo storage. Use Redis or your DB in production, and
# make sure entries actually expire / get cleaned up. ---
AUTH_CODES = {}  # code -> {user_id, code_challenge, redirect_uri, expires_at, used}
CODE_TTL_SECONDS = 120

# --- Stand-in for your real user store, just for local dev testing. ---
DEV_USERS = {"demo": {"id": "u_1", "email": "demo@example.com"}}


def get_current_user():
    """Replace with your real session/auth lookup."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    for u in DEV_USERS.values():
        if u["id"] == user_id:
            return u
    return None


LOGIN_PAGE = """
<!doctype html><html><body style="font-family:sans-serif;max-width:360px;margin:15vh auto;">
<h2>Log in</h2>
<p>The xp CLI wants to log in. (dev stub - try username "demo")</p>
<form method="post">
  <input name="username" placeholder="username" style="width:100%;padding:8px;margin-bottom:8px;box-sizing:border-box;">
  <button type="submit" style="width:100%;padding:8px;">Log in</button>
</form>
</body></html>
"""


@app.route("/cli/authorize", methods=["GET", "POST"])
def cli_authorize():
    state = request.values.get("state")
    redirect_uri = request.values.get("redirect_uri")
    code_challenge = request.values.get("code_challenge")

    if not (state and redirect_uri and code_challenge):
        return "Missing required parameters", 400

    # Only ever redirect back to a loopback address for the CLI flow.
    if not redirect_uri.startswith("http://127.0.0.1:"):
        return "Invalid redirect_uri", 400

    user = get_current_user()
    if not user:
        if request.method == "POST":
            username = request.form.get("username", "")
            dev_user = DEV_USERS.get(username)
            if dev_user:
                session["user_id"] = dev_user["id"]
                user = dev_user
        if not user:
            return render_template_string(LOGIN_PAGE)

    code = secrets.token_urlsafe(32)
    AUTH_CODES[code] = {
        "user_id": user["id"],
        "code_challenge": code_challenge,
        "redirect_uri": redirect_uri,
        "expires_at": time.time() + CODE_TTL_SECONDS,
        "used": False,
    }

    query = urlencode({"code": code, "state": state})
    return redirect(f"{redirect_uri}?{query}")


@app.route("/cli/token", methods=["POST"])
def cli_token():
    body = request.get_json(force=True, silent=True) or {}
    code = body.get("code")
    code_verifier = body.get("code_verifier")
    redirect_uri = body.get("redirect_uri")

    entry = AUTH_CODES.get(code)
    if not entry:
        return jsonify({"error": "invalid_code"}), 400

    if entry["used"] or time.time() > entry["expires_at"]:
        AUTH_CODES.pop(code, None)
        return jsonify({"error": "expired_or_used_code"}), 400

    if entry["redirect_uri"] != redirect_uri:
        return jsonify({"error": "redirect_uri_mismatch"}), 400

    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    if not secrets.compare_digest(expected_challenge, entry["code_challenge"]):
        return jsonify({"error": "invalid_code_verifier"}), 400

    entry["used"] = True

    user = next(u for u in DEV_USERS.values() if u["id"] == entry["user_id"])

    # TODO: replace with issuing a real, revocable API token tied to
    # this user (e.g. a row in an `api_tokens` table you can look up
    # and revoke later), rather than a token that isn't tracked anywhere.
    access_token = secrets.token_urlsafe(32)

    return jsonify({"access_token": access_token, "user": user})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
