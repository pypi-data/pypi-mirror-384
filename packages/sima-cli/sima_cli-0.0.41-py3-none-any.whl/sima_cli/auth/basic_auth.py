import os
import click
import getpass
import requests
import json
import subprocess
import shutil
import base64

from typing import Optional
from http.cookiejar import MozillaCookieJar
from sima_cli.__version__ import __version__
from sima_cli.utils.env import is_sima_board

HOME_DIR = os.path.expanduser("~/.sima-cli")
COOKIE_JAR_PATH = os.path.join(HOME_DIR, ".sima-cli-cookies.txt")
CSRF_PATH = os.path.join(HOME_DIR, ".sima-cli-csrf.json")

# Base URLs depending on environment
# Detect staging or production environment
if os.getenv("USE_STAGING_DEV_PORTAL", "false").lower() in ("1", "true", "yes"):
    DEV_PORTAL = "https://discourse-dev.sima.ai"
    DOCS_PORTAL = "https://docs-dev.sima.ai"
    click.secho("⚠️  Using STAGING developer portal: discourse-dev.sima.ai", fg="red", bold=True)
else:
    DEV_PORTAL = "https://developer.sima.ai"
    DOCS_PORTAL = "https://docs.sima.ai"

# Derived endpoints
CSRF_URL = f"{DEV_PORTAL}/session/csrf"
LOGIN_URL = f"{DEV_PORTAL}/session"
DUMMY_CHECK_URL = f"{DOCS_PORTAL}/pkg_downloads/validation"


HEADERS = {
    "User-Agent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) sima-cli/{__version__} Chrome/137.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{DEV_PORTAL}/login",
    "Origin": f"{DEV_PORTAL}",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

def _handle_eula_flow(session: requests.Session, username: str, domain: str) -> bool:
    try:
        click.echo("\n📄 To continue, you must accept the End-User License Agreement (EULA).")
        click.echo("👉 Please sign in to Developer Portal on your browser, then open the following URL to accept the EULA:")
        click.echo(f"\n  {DUMMY_CHECK_URL}\n")

        if not click.confirm("✅ Have you completed the EULA form in your browser?", default=True):
            click.echo("❌ EULA acceptance is required to continue.")
            return False

        return True

    except Exception as e:
        click.echo(f"❌ Error during EULA flow: {e}")
        return False

def _is_session_valid(session: requests.Session) -> bool:
    try:
        response = session.get(DUMMY_CHECK_URL, allow_redirects=False)

        if response.status_code == 200:
            return True
        elif response.status_code == 302:
            location = response.headers.get("Location", "")
            if "show-eula-form=1" in location:
                return _handle_eula_flow(session, username="", domain="")
            elif 'show-request-form=1' in location:
                click.echo("❌ Your account is valid, but you do not have permission to download assets. Please contact your sales representative or email support@sima.ai for assistance.")
                exit(0)

        return False
    except Exception as e:
        click.echo(f"❌ Error validating session: {e}")
        return False

def get_ecr_access_info(session: requests.Session) -> Optional[dict]:
    """
    Retrieve an ECR access token and proxy endpoint using the current authenticated session.

    Args:
        session (requests.Session): An authenticated session (with valid cookies).

    Returns:
        Optional[dict]: JSON response containing the ECR token info, or None if failed.
    """
    try:
        ecr_url = f"{DOCS_PORTAL}/pkg_downloads/ecr-token"
        response = session.get(ecr_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "authorizationToken" in data and "proxyEndpoint" in data:
            return data
        else:
            click.secho(
                "⚠️  Container registry token response missing 'authorizationToken'. "
                "Contact support@sima.ai for help.",
                fg="yellow",
            )
            return data
    except Exception as e:
        click.secho(f"❌ Failed to retrieve ECR token: {e}", fg="red")
        return None

def _delete_auth_files():
    for path in [COOKIE_JAR_PATH, CSRF_PATH]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                click.echo(f"⚠️ Could not delete {path}: {e}")


def _save_cookie_jar(session: requests.Session):
    cj = MozillaCookieJar(COOKIE_JAR_PATH)
    for c in session.cookies:
        cj.set_cookie(c)
    cj.save(ignore_discard=True)


def _load_cookie_jar(session: requests.Session):
    if os.path.exists(COOKIE_JAR_PATH):
        cj = MozillaCookieJar()
        cj.load(COOKIE_JAR_PATH, ignore_discard=True)
        session.cookies.update(cj)


def _load_csrf_token() -> str:
    if os.path.exists(CSRF_PATH):
        with open(CSRF_PATH, "r") as f:
            data = json.load(f)
            return data.get("csrf", "")
    return ""


def _fetch_and_store_csrf_token(session: requests.Session) -> str:
    try:
        resp = session.get(CSRF_URL)
        resp.raise_for_status()
        csrf_token = resp.json().get("csrf")
        if csrf_token:
            with open(CSRF_PATH, "w") as f:
                json.dump({"csrf": csrf_token}, f)
        return csrf_token
    except Exception as e:
        click.echo(f"❌ Failed to fetch CSRF token: {e}")
        return ""

def login_external():
    """Interactive login workflow with CSRF token, cookie caching, and TOTP handling."""
    for attempt in range(1, 4):
        session = requests.Session()
        session.headers.update(HEADERS)

        _load_cookie_jar(session)
        csrf_token = _load_csrf_token() or _fetch_and_store_csrf_token(session)
        if not csrf_token:
            click.echo("❌ CSRF token is missing or invalid.")
            continue
        session.headers["X-CSRF-Token"] = csrf_token

        if _is_session_valid(session):
            return session

        # Fresh login prompt
        _delete_auth_files()
        click.echo(f"🔐 Sima.ai Developer Portal Login Attempt {attempt}/3")
        username = click.prompt("Email or Username")
        password = getpass.getpass("Password: ")

        # Base payload (no TOTP yet)
        base_data = {
            "login": username,
            "password": password,
            "second_factor_method": "1",  # TOTP
        }

        def _post_login(payload: dict):
            """POST and return (status_code, json or None, text) with robust error handling."""
            try:
                resp = session.post(LOGIN_URL, data=payload, timeout=30)
            except Exception as e:
                return None, None, f"request failed: {e}"
            j = None
            try:
                j = resp.json()
            except Exception:
                pass
            return resp.status_code, j, (j or resp.text)

        # First try without TOTP (server may ask for it)
        status, j, raw = _post_login(base_data)

        # Helper: decide if success
        def _success():
            # Prefer server 'ok': True, but also double-check the session cookie validity
            if j and j.get("ok") is True:
                return True
            return _is_session_valid(session)

        # If immediate success
        if status == 200 and _success():
            _save_cookie_jar(session)
            welcome = (j.get("users", [{}])[0].get("name") if isinstance(j, dict) else "") or ""
            click.secho(f"✅ Login successful. Welcome to Sima Developer Portal{', ' + welcome if welcome else ''}!", fg = 'green')
            token, endpoint = resolve_public_registry()
            docker_login_with_token('sima_cli', token, endpoint)
            return session

        # See if TOTP is required/invalid; then prompt and retry up to 3 times
        def _needs_totp(payload_json):
            if not isinstance(payload_json, dict):
                return False
            if payload_json.get("totp_enabled") is True:
                return True
            reason = payload_json.get("reason") or payload_json.get("error")
            return str(reason) in {"invalid_second_factor", "second_factor_required"}

        if _needs_totp(j):
            # Try up to 3 TOTP attempts within this login attempt
            for totp_try in range(1, 4):
                totp = click.prompt(f"🔢 Enter Time-based One Time Password (TOTP code) (attempt {totp_try}/3)", hide_input=True)
                data = dict(base_data)
                data["second_factor_token"] = totp

                status, j2, raw2 = _post_login(data)
                if status == 200 and (j2 and j2.get("ok") is True or _is_session_valid(session)):
                    _save_cookie_jar(session)
                    welcome = (j2.get("users", [{}])[0].get("name") if isinstance(j2, dict) else "") or ""
                    click.secho(f"✅ Login successful. Welcome to Sima Developer Portal{', ' + welcome if welcome else ''}!", fg = 'green')
                    token, endpoint = resolve_public_registry()
                    docker_login_with_token('sima_cli', token, endpoint)
                    return session

                # If still invalid 2FA, let user try again; otherwise break to outer loop
                msg = ""
                if isinstance(j2, dict):
                    reason = j2.get("reason") or j2.get("error") or ""
                    msg = f" ({reason})" if reason else ""
                if isinstance(j2, dict) and str(j2.get("reason")) in {"invalid_second_factor"}:
                    click.echo(f"❌ Invalid authentication code. Please try again.{msg}")
                    continue
                else:
                    click.echo(f"❌ Login failed with TOTP{msg}.")
                    break  # go to next overall attempt

            # exhausted TOTP tries
            click.echo("❌ TOTP verification failed after 3 attempts.")
            continue  # next overall attempt

        # Not a TOTP case; report error and continue
        err_detail = ""
        if isinstance(j, dict):
            err_detail = j.get("error") or j.get("message") or ""
            reason = j.get("reason")
            if reason and reason != err_detail:
                err_detail = f"{err_detail} ({reason})" if err_detail else reason
        else:
            err_detail = str(raw)[:200]

        click.echo(f"❌ Server response code: {json.dumps(raw)}")
        click.echo(f"❌ Login failed. {err_detail or 'Please check your credentials and try again.'}")

    click.echo("❌ Login failed after 3 attempts.")
    raise SystemExit(1)

def resolve_public_registry(name: str = 'ecr'):
    """
    Resolve a short registry alias to its corresponding public container
    registry endpoint and ensure authentication if required.

    Args:
        name (str): Short alias for a known registry (e.g. 'ecr').

    Returns:
        Optional[str]: The resolved registry endpoint, or None on failure.
    """
    name = name.lower().strip()

    if not ensure_docker_available():
        return None, None

    if name == "ecr":
        click.secho("🔍 Resolving SiMa.ai container registry...", fg="cyan")

        try:
            session = login_external()
            if not session or not isinstance(session, requests.Session):
                click.secho("❌ No valid session found. Please login first using `sima-cli login`.", fg="red")
                return None, None

            ecr_info = get_ecr_access_info(session)
            if not ecr_info:
                click.secho("❌ Failed to retrieve container registry token information.", fg="red")
                return None, None

            token = ecr_info.get("authorizationToken")
            endpoint = ecr_info.get("proxyEndpoint")
            if not token or not endpoint:
                click.secho("⚠️  Missing 'authorizationToken' or 'proxyEndpoint' in container registry response.", fg="yellow")
                return None, None

            return token, endpoint

        except Exception as e:
            click.secho(f"❌ Unexpected error while resolving registry '{name}': {e}", fg="red")
            return None, None

    else:
        raise click.ClickException(f"❌ Unknown public registry alias: {name}")


def ensure_docker_available() -> bool:
    """
    Check if Docker CLI exists on PATH.

    - Returns True if Docker is available.
    - If missing, prints a gentle warning (only on non-SiMa hosts).
    - On SiMa boards (Modalix/Davinci), stays completely silent since Docker is optional.
    """
    if shutil.which("docker"):
        return True

    # Only warn on host systems, not on SiMa devkits
    if not is_sima_board():
        click.echo("⚠️  Docker CLI not found — container image pull and registry operations will be skipped until Docker is installed.")

    return False

def docker_login_with_token(username: str, token: str, registry: str = "artifacts.eng.sima.ai"):
    """
    Use `docker login` with --password-stdin to register Artifactory or ECR token.

    - Automatically detects and decodes AWS ECR base64 tokens of the form 'QVdTOmV5...'
    - Ensures Docker is available before attempting login.
    - Works even when Docker uses credential helpers (e.g., credsStore=desktop).
    """
    if ensure_docker_available():
        # Decode if token looks like base64 (AWS ECR style)
        try:
            decoded = base64.b64decode(token).decode("utf-8")
            if decoded.startswith("AWS:"):
                # ECR token detected → force username to AWS
                password = decoded.split("AWS:", 1)[1]
                username = "AWS"
            else:
                password = token
        except Exception:
            # Not a valid base64 string — use raw token
            password = token

        proc = subprocess.run(
            ["docker", "login", registry, "-u", username, "--password-stdin"],
            input=password.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if proc.returncode != 0:
            raise click.ClickException(f"❌ Docker login failed: {proc.stderr.decode().strip()}")

        click.echo(proc.stdout.decode().strip() or f"✅ Logged in to SiMa.ai container registry")
        return password