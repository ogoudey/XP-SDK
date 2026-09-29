"""xp - command line interface.

Usage:
    xp <command> [options]

Commands:
    login    Log in via the browser
    logout   Clear stored credentials
    whoami   Show the currently logged-in user
    write    hiuh
"""
import sys
import webbrowser
from pathlib import Path
import click
import requests
import rich
from . import auth
from .config import get_base_url
from .server import CallbackServer
from concepts.experience import SharedExperience

LOGIN_TIMEOUT_SECONDS = 300  # 5 minutes

@click.group()
@click.version_option(package_name="xp")
def cli():
    """xp - authenticate and talk to the platform from your terminal."""
    pass


from . import cap
cli.add_command(cap.cap)


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

from . import writer

TEMPLATES = {
    
}

@cli.command()
@click.option("--local-dir", required=True, type=click.Path(file_okay=False, path_type=Path),
              help="Directory to write the dataset entry into.")
@click.option("--dataset-type", required=True, type=click.Choice(["raw", "lerobot"]),
              help="Which kind of dataset entry to author.")
def write(local_dir: Path, dataset_type: str):
    """Run the wizard to author a new dataset entry."""
    
    click.echo(f"Building a '{dataset_type}' entry...")
    instance = writer.template_experience

    out_path = _write_output(instance, local_dir, dataset_type)
    click.echo(f"Wrote {out_path}")

def _write_output(model_instance, local_dir: Path, dataset_type: str) -> Path:
    local_dir.mkdir(parents=True, exist_ok=True)
    match dataset_type:
        case "raw":
            out_path = local_dir / f"experience.json"
            out_path.write_text(model_instance.model_dump_json(indent=2))
            return out_path
        case "lerobot":
            out_path = local_dir / f"experience.json"
            out_path.write_text(model_instance.model_dump_json(indent=2))
            return out_path
        case _:
            click.error(f"Dataset type {dataset_type} not recognized...")
            raise

if __name__ == "__main__":
    cli()
