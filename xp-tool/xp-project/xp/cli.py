"""xp - command line interface.

Usage:
    xp <command> [options]

Commands:
    login    Log in via the browser
    logout   Clear stored credentials
    whoami   Show the currently logged-in user
"""
import sys
import webbrowser

import click
import requests
import rich
from . import auth
from .config import get_base_url
from .server import CallbackServer

LOGIN_TIMEOUT_SECONDS = 300  # 5 minutes

from concepts import experience_system, trust_model, capability_model
from concepts.trust_model import RootDevice, RootEgo, Computer, Cause, Action, Other, Ego, ComputeEnvironment, HumanBrain

@click.group()
@click.version_option(package_name="xp")
def cli():
    """xp - authenticate and talk to the platform from your terminal."""
    pass


@cli.command()
def auto():
    """Create experience file"""
    click.echo("Retrospectively generating experience file...")
    token_data = auth.load_token()
    if not token_data:
        click.echo(f"Not logged in.")
        prefilled={}
    else:
        click.echo(f"Logged in as {token_data['user']['username']}.")
        prefilled = {"hub_client": token_data["user"]["username"]}
    prefilled["trust_model"] = {
        "compute_environment": {
            "name": None,   # a real Optional field -> fine as a literal value, no recursion needed
            "code": {
                "causal_mapping": { ... }  # see below, this one's different
            },
        },
    }
    rich.print(prefilled)
    new_xp = experience_system.Experience.create(prefilled=prefilled)
    new_xp.save_to("new_experience.xp")

@cli.command()
def login():
    """Log in via the browser."""
    base_url = get_base_url()

    state = auth.generate_state()
    pkce = auth.generate_pkce_pair()

    callback = CallbackServer(expected_state=state)
    callback.start()

    authorize_url = (
        f"{base_url}/cli/authorize"
        f"?state={state}"
        f"&redirect_uri={callback.redirect_uri}"
        f"&code_challenge={pkce.challenge}"
        f"&code_challenge_method=S256"
    )

    click.echo("Opening your browser to log in...")
    click.echo(f"If it doesn't open automatically, visit:\n  {authorize_url}\n")
    webbrowser.open(authorize_url)

    result = callback.wait_for_result(timeout=LOGIN_TIMEOUT_SECONDS)

    if result is None:
        click.echo("Timed out waiting for login. Please try again.", err=True)
        sys.exit(1)

    if "error" in result:
        click.echo(f"Login failed: {result['error']}", err=True)
        sys.exit(1)

    # Exchange the one-time code for a real token server-side, using the
    # PKCE verifier. The code alone (which briefly appears in browser
    # history / the redirect URL) is useless without this verifier.
    try:
        resp = requests.post(
            f"{base_url}/cli/token",
            json={
                "code": result["code"],
                "code_verifier": pkce.verifier,
                "redirect_uri": callback.redirect_uri,
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        click.echo(f"Failed to complete login: {e}", err=True)
        sys.exit(1)

    data = resp.json()
    auth.save_token(data)

    user = data.get("user", {})
    label = user.get("email") or user.get("username") or "your account"
    click.echo(f"Logged in as {label}.")


@cli.command()
def logout():
    """Clear stored credentials."""
    auth.clear_token()
    click.echo("Logged out.")


@cli.command()
def whoami():
    """Show the currently logged-in user."""
    token_data = auth.load_token()
    if not token_data:
        click.echo("Not logged in. Run `xp login`.", err=True)
        sys.exit(1)

    user = token_data.get("user", {})
    if user:
        click.echo(user.get("email") or user.get("username") or user)
    else:
        click.echo("Logged in (no user profile info stored).")


if __name__ == "__main__":
    cli()
