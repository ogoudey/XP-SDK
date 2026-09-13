"""`xp cap` — publish and read capability definitions.

Everything here goes through the gateway, never the backend directly: the
gateway holds the API key and resolves your bearer token to a user.
"""

import os
import pathlib
import re
import sys
from datetime import datetime

import click
import requests

from . import auth

DEFAULT_BASE_URL = "https://olimn.com"
TIMEOUT = 30
MAX_UPLOAD_BYTES = 256 * 1024

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


# ---------------- plumbing ---------------- #

def base_url():
    return os.environ.get("XP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def bearer():
    """Pull the access token out of whatever auth.load_token() hands back."""
    data = auth.load_token()
    if not data:
        raise click.ClickException("Not signed in. Run `xp login` first.")

    token = data.get("access_token") if isinstance(data, dict) else data
    if not token:
        raise click.ClickException("Stored credentials look wrong. Run `xp login` again.")

    # The token carries an expiry; saying so beats a bare 401 later.
    if isinstance(data, dict) and data.get("expires_at"):
        try:
            if datetime.fromisoformat(data["expires_at"]) < datetime.now():
                raise click.ClickException("Your token has expired. Run `xp login` again.")
        except ValueError:
            pass

    return {"Authorization": f"Bearer {token}"}


def call(method, path, **kwargs):
    """One request, with the errors turned into readable messages."""
    url = f"{base_url()}{path}"
    try:
        response = requests.request(
            method, url, headers=bearer(), timeout=TIMEOUT, **kwargs
        )
    except requests.Timeout:
        raise click.ClickException(f"{url} took longer than {TIMEOUT}s.")
    except requests.RequestException as exc:
        raise click.ClickException(f"Could not reach {base_url()}: {exc}")

    if response.status_code == 401:
        raise click.ClickException("Your token was rejected. Run `xp login` again.")
    if response.status_code == 403:
        raise click.ClickException(
            "Your account cannot do that — publishing needs the operator or admin role."
        )
    if response.status_code >= 400:
        detail = ""
        try:
            body = response.json()
            detail = body.get("message") or body.get("error") or ""
        except ValueError:
            detail = (response.text or "").strip()[:200]
        raise click.ClickException(
            f"{method} {path} failed ({response.status_code}){': ' + detail if detail else '.'}"
        )

    return response


def default_capability_id():
    """The current directory's name, which is usually the right answer."""
    name = pathlib.Path.cwd().name.lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9._-]", "-", name).strip("-.")
    return name if SLUG_RE.match(name) else None


def format_when(value):
    """Flask serialises datetimes as RFC-822 ("Sun, 13 Sep 2026 16:22:31 GMT"),
    which is too wide for a column. Fall back to the raw string if it is
    something else."""
    if not value:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return str(value)[:16]


def human_size(n):
    return f"{n} B" if n < 1024 else f"{n / 1024:.1f} KB"


# ---------------- commands ---------------- #

@click.group()
def cap():
    """Publish and read capability definitions."""


@cap.command("show")
@click.option("--quiet", "-q", is_flag=True, help="Print ids only, one per line.")
def show(quiet):
    """List the capabilities Central knows about."""
    if quiet:
        for capability_id in call("GET", "/capabilities").json():
            click.echo(capability_id)
        return

    rows = call("GET", "/capabilities", params={"detail": 1}).json()
    if not rows:
        click.echo("No capabilities published yet. Try `xp cap publish`.")
        return
    width = max(len(r) for r in rows)
    for row in rows:
        updated = format_when(row.get("updated_at"))
        source = row.get("source_name") or "—"
        click.echo(
            f"{row['capability_id']:<{width}}  "
            f"{human_size(row.get('size_bytes') or 0):>9}  "
            f"{source:<20.20}  {updated}"
        )


@cap.command("describe")
@click.argument("capability_id")
@click.option("--out", "-o", type=click.Path(dir_okay=False, writable=True),
              help="Write to a file instead of stdout.")
def describe(capability_id, out):
    """Print the definition for CAPABILITY_ID."""
    content = call("GET", f"/capabilities/{capability_id}").text

    if out:
        pathlib.Path(out).write_text(content, encoding="utf-8")
        click.echo(f"Wrote {out} ({human_size(len(content.encode()))}).", err=True)
        return

    # No pager and no rewrapping: piping into `less` or `glow` should work.
    click.echo(content, nl=not content.endswith("\n"))


@cap.command("publish")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, readable=True),
                default="README.md", required=False)
@click.option("--id", "capability_id",
              help="Capability id. Defaults to the current directory's name.")
@click.option("--yes", "-y", is_flag=True, help="Skip the overwrite prompt.")
def publish(path, capability_id, yes):
    """Upload PATH (default: ./README.md) as a capability definition."""
    capability_id = capability_id or default_capability_id()
    if not capability_id:
        raise click.ClickException(
            "Could not work out a capability id from this directory. Pass --id."
        )
    if not SLUG_RE.match(capability_id):
        raise click.ClickException(
            f"{capability_id!r} is not a valid id: lowercase letters, digits, "
            "dot, dash or underscore, up to 64 characters."
        )

    source = pathlib.Path(path)
    raw = source.read_bytes()

    if not raw.strip():
        raise click.ClickException(f"{path} is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise click.ClickException(
            f"{path} is {human_size(len(raw))}; the limit is "
            f"{human_size(MAX_UPLOAD_BYTES)}."
        )
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        raise click.ClickException(f"{path} is not UTF-8 text.")

    # Publishing replaces whatever is there, so say so when it is not new.
    if not yes and sys.stdin.isatty():
        existing = [r["capability_id"] for r in
                    call("GET", "/capabilities", params={"detail": 1}).json()]
        if capability_id in existing:
            click.confirm(
                f"{capability_id} already has a definition. Replace it?", abort=True
            )

    with source.open("rb") as handle:
        result = call(
            "POST", f"/capabilities/{capability_id}/sync",
            files={"file": (source.name, handle, "text/markdown")},
        ).json()

    click.echo(
        f"Published {result['capability_id']} "
        f"from {source.name} ({human_size(result['size_bytes'])})."
    )


@cap.command("rm")
@click.argument("capability_id")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@click.option("--backup", "-b", type=click.Path(dir_okay=False, writable=True),
              help="Save the definition to a file before deleting it.")
def rm(capability_id, yes, backup):
    """Delete the definition for CAPABILITY_ID."""
    if not SLUG_RE.match(capability_id):
        raise click.ClickException(f"{capability_id!r} is not a valid capability id.")
 
    # Fetch first: it confirms the thing exists, and makes --backup possible.
    content = call("GET", f"/capabilities/{capability_id}").text
 
    if backup:
        pathlib.Path(backup).write_text(content, encoding="utf-8")
        click.echo(f"Saved {backup} ({human_size(len(content.encode()))}).", err=True)
 
    if not yes:
        # Deliberately unlike `publish`, which just proceeds when it cannot
        # prompt. Deleting is unrecoverable, so with no terminal to ask on,
        # refuse rather than assume consent.
        if not sys.stdin.isatty():
            raise click.ClickException(
                f"Refusing to delete {capability_id} without a terminal to "
                "confirm on. Pass --yes if you meant it."
            )
        click.echo(f"{capability_id} is {human_size(len(content.encode()))} "
                   f"and cannot be recovered after this.")
        click.confirm(f"Delete {capability_id}?", abort=True)
 
    call("DELETE", f"/capabilities/{capability_id}")
    click.echo(f"Deleted {capability_id}.")
