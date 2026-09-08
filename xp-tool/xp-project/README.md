# xp

A CLI (`xp`) that authenticates against your own web service via the
browser, and a matching pair of server endpoints.

## How the login works

This is an OAuth-style **authorization code flow with PKCE**, adapted
so the "client" is a CLI on the user's own machine instead of a
registered OAuth app:

1. `xp login` generates a random `state` and a PKCE `code_verifier` /
   `code_challenge` pair, starts a tiny HTTP server on
   `127.0.0.1:<random free port>`, and opens your browser to:

   ```
   {base_url}/cli/authorize?state=...&redirect_uri=http://127.0.0.1:<port>/callback&code_challenge=...
   ```

2. Your web server shows its normal login page if the browser isn't
   already logged in. Once it is, it mints a short-lived, single-use
   `code`, stores it server-side next to the `code_challenge` and
   `redirect_uri`, and redirects the browser to
   `redirect_uri?code=...&state=...`.

3. The local server on the user's machine catches that redirect,
   checks `state` matches, and grabs `code`.

4. `xp` then POSTs `{code, code_verifier, redirect_uri}` to
   `{base_url}/cli/token`. Your server re-derives the challenge from
   the verifier (SHA-256 + base64url), checks it matches what was
   stored, checks the code hasn't expired or been used, and returns a
   real access token + user info as JSON.

5. `xp` stores the token (OS keychain via `keyring` if available,
   otherwise a `0600` file at `~/.xp/credentials.json`) and you're
   logged in.

**Why PKCE even for a "first-party" CLI:** the authorization `code`
briefly appears in a local redirect URL and could in principle be
observed (browser history, an accidental log line, etc). Without PKCE,
anyone with that code could exchange it for a token. With PKCE, they'd
also need the `code_verifier`, which never leaves the CLI process
until the final POST.

**Why loopback-only redirects:** the server rejects any
`redirect_uri` that isn't `http://127.0.0.1:...`, so this flow can't
be abused to redirect codes somewhere else.

## Project layout

```
xp/                     # the CLI package
  cli.py                # `xp login|logout|whoami`
  auth.py               # PKCE + token storage
  server.py             # local loopback callback server
  config.py             # base URL / paths
pyproject.toml          # `pip install -e .` -> `xp` command
server_example/
  app.py                # Flask endpoints: /cli/authorize, /cli/token
  requirements.txt
```

## Running it in dev

**1. Start the example server** (or wire these two routes into your
existing web server instead):

```bash
cd server_example
pip install -r requirements.txt
python app.py
# -> running on http://localhost:5000
```

**2. Install the CLI** in a separate terminal:

```bash
pip install -e .
```

**3. Log in:**

```bash
xp login
```

Your browser opens to the dev login stub - enter `demo` as the
username (that's the fake user baked into `server_example/app.py` for
testing). You should land on a "You're logged in" page, and the
terminal will print `Logged in as demo@example.com.`

**4. Check it worked:**

```bash
xp whoami
xp logout
```

By default `xp` talks to `http://localhost:5000`. Point it elsewhere with:

```bash
export XP_BASE_URL=https://your-real-domain.com
```

## Wiring into your real web server

Swap `get_current_user()` and `DEV_USERS` in `server_example/app.py`
for your actual session/user lookup, replace the in-memory
`AUTH_CODES` dict with Redis or a DB table (with real TTL cleanup),
and replace the placeholder `access_token = secrets.token_urlsafe(32)`
with your real token issuance so it's tied to the user and revocable
later. The `/cli/authorize` and `/cli/token` route logic itself
(state/PKCE/redirect_uri checks) can stay as-is.

## Adding more commands

Add new `@cli.command()` functions in `xp/cli.py`. To call your
authenticated API, read the stored token with `auth.load_token()` and
send it as a bearer token:

```python
token_data = auth.load_token()
headers = {"Authorization": f"Bearer {token_data['access_token']}"}
```
