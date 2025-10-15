# model_zoo/models.py

import requests
import click
import os
import yaml
import zipfile
import shutil
from urllib.parse import urlparse
from rich import print
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from sima_cli.utils.config import get_auth_token
from sima_cli.utils.config_loader import artifactory_url
from sima_cli.download import download_file_from_url

ARTIFACTORY_BASE_URL = artifactory_url() + '/artifactory'

def _is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def _describe_app_internal(ver: str, app_name: str):
    repo = "vdp"
    base_path = f"vdp-app-config-default/{ver}/{app_name}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": "{base_path}",
            "$or": [
                {{ "name": {{ "$match": "*.yaml" }} }},
                {{ "name": {{ "$match": "*.yml" }} }}
            ],
            "type": "file"
        }}).include("repo","path","name")
    """.strip()

    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }
    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to list app files. Status: {response.status_code}")
        click.echo(response.text)
        return

    results = response.json().get("results", [])
    yaml_file = next((f for f in results if f["name"].endswith((".yaml", ".yml"))), None)

    if not yaml_file:
        click.echo(f"⚠️ No .yaml or .yml file found under: {base_path}")
        return

    # Download the YAML
    yaml_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{yaml_file['path']}/{yaml_file['name']}"
    response = requests.get(yaml_url, headers={"Authorization": f"Bearer {get_auth_token(internal=True)}"})
    if response.status_code != 200:
        click.echo(f"❌ Failed to fetch YAML: {response.status_code}")
        return

    try:
        data = yaml.safe_load(response.text)
    except yaml.YAMLError as e:
        click.echo(f"❌ Failed to parse YAML: {e}")
        return

    # ---- PIPELINE (new app YAML) ----
    if "pipeline" in data:
        pipeline = data.get("pipeline", {})

        header = f"[bold green]{pipeline.get('name', app_name)}[/bold green] - {pipeline.get('category', 'Unknown')}"
        desc = pipeline.get("short_description", "")

        console = Console()
        # Panel body holds description so it wraps
        body = Text(desc, style="yellow", no_wrap=False)
        panel_width = min(console.width, 100)

        print(Panel(body, title=header, expand=False, width=80))

        p_table = Table(title="Pipeline", header_style="bold magenta")
        p_table.add_column("Field")
        p_table.add_column("Value")
        p_table.add_row("Input Format", pipeline.get("in_format", "-"))
        p_table.add_row("Output Format", pipeline.get("out_format", "-"))

        perf = pipeline.get("performance", {})
        p_table.add_row("Davinci FPS", str(perf.get("davinci_fps", "-")))
        p_table.add_row("Modalix FPS", str(perf.get("modalix_fps", "-")))

        print(p_table)
    # ---- MODEL(S) ----
    if "model" in data:
        models = data["model"]
        if isinstance(models, dict):
            models = [models]
        elif not isinstance(models, list):
            models = []

        for idx, model in enumerate(models, start=1):
            title = f"Model #{idx}" if len(models) > 1 else "Model"
            m_table = Table(title=title, header_style="bold cyan")
            m_table.add_column("Field")
            m_table.add_column("Value")

            m_table.add_row("Name", model.get("name", "-"))

            if inp := model.get("input_description"):
                m_table.add_row("Resolution", str(inp.get("resolution", "-")))
                m_table.add_row("Format", inp.get("format", "-"))

            if resize := model.get("resize_configuration"):
                m_table.add_row("Resize Format", resize.get("input_image_format", "-"))
                m_table.add_row("Input Shape", str(resize.get("input_shape", "-")))
                m_table.add_row("Scaling Type", resize.get("scaling_type", "-"))
                m_table.add_row("Padding Type", resize.get("padding_type", "-"))
                m_table.add_row("Aspect Ratio", str(resize.get("aspect_ratio", "-")))

            if norm := model.get("normalization_configuration"):
                m_table.add_row("Channel Mean", str(norm.get("channel_mean", "-")))
                m_table.add_row("Channel Stddev", str(norm.get("channel_stddev", "-")))
                if "accuracy" in norm:
                    m_table.add_row("Accuracy", str(norm.get("accuracy", "-")))

            # Legacy model-centric fields
            if "dataset" in model:
                ds = model["dataset"]
                m_table.add_row("Dataset", ds.get("name", "-"))
                for k, v in (ds.get("params") or {}).items():
                    m_table.add_row(k, str(v))
                m_table.add_row("Accuracy", ds.get("accuracy", "-"))
                m_table.add_row("Calibration", ds.get("calibration", "-"))

            if "quantization_settings" in model:
                q = model["quantization_settings"]
                m_table.add_row("Calibration Samples", str(q.get("calibration_num_samples", "-")))
                m_table.add_row("Calibration Method", q.get("calibration_method", "-"))
                m_table.add_row("Requantization Mode", q.get("requantization_mode", "-"))
                m_table.add_row("Bias Correction", str(q.get("bias_correction", "-")))

            print(m_table)

    # ---- PIPELINE TRANSFORMS (legacy YAML) ----
    if "pipeline" in data and "transforms" in data["pipeline"]:
        transforms = data["pipeline"]["transforms"]
        if isinstance(transforms, list):
            t_table = Table(title="Pipeline Transforms", header_style="bold green")
            t_table.add_column("Name")
            t_table.add_column("Params")

            for step in transforms:
                name = step.get("name")
                params = step.get("params", {})
                param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "-"
                t_table.add_row(name, param_str)

            print(t_table)

    # If nothing useful parsed
    if not any(k in data for k in ("pipeline", "model")):
        click.echo("⚠️ YAML parsed, but no recognizable `pipeline` or `model` sections found.")

def _download_app_internal(ver: str, app_name: str):
    """
    Download a specific app (.zip file) from Artifactory App Zoo, unzip it,
    flatten the extracted content into the app folder, and clean up.
    """
    repo = "vdp"
    base_path = f"vdp-app-config-default/{ver}/{app_name}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": "{base_path}",
            "name": {{"$match": "*.zip"}},
            "type": "file"
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to list app files. Status: {response.status_code}, path: {aql_url}")
        click.echo(response.text)
        return None

    results = response.json().get("results", [])
    if not results:
        click.echo(f"⚠️ No .zip file found for app: {app_name}")
        return None

    # Expect only one .zip file per app
    file_info = results[0]
    file_path = file_info["path"]
    file_name = file_info["name"]
    download_url = f"{ARTIFACTORY_BASE_URL}/{repo}/{file_path}/{file_name}"

    dest_dir = os.path.join(os.getcwd(), app_name)
    os.makedirs(dest_dir, exist_ok=True)

    click.echo(f"⬇️  Downloading app '{app_name}' to '{dest_dir}'...")

    try:
        local_zip = download_file_from_url(download_url, dest_folder=dest_dir, internal=True)
        click.echo(f"✅ {file_name} -> {local_zip}")
    except Exception as e:
        click.echo(f"❌ Failed to download {file_name}: {e}")
        return None

    # Unzip into the destination folder
    try:
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(dest_dir)
        click.echo(f"📦 Extracted {file_name} into {dest_dir}")
    except Exception as e:
        click.echo(f"❌ Failed to unzip {file_name}: {e}")
        return None

    # Move contents up if unzipped into a nested folder
    extracted_root = os.path.join(dest_dir, file_name.replace(".zip", ""))
    if os.path.isdir(extracted_root):
        for item in os.listdir(extracted_root):
            src = os.path.join(extracted_root, item)
            dst = os.path.join(dest_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.move(src, dst)
            else:
                shutil.move(src, dst)
        shutil.rmtree(extracted_root)

    # Remove the original zip file
    try:
        os.remove(local_zip)
    except OSError:
        pass

    click.echo(f"✅ App '{app_name}' ready at {dest_dir}")
    return dest_dir

def _list_available_app_versions_internal(match_keyword: str = None):
    """
    List all available App Zoo versions from Artifactory (vdp-app-config-default).
    If match_keyword is provided, only versions containing the keyword (case-insensitive) are returned.
    """
    repo = "vdp"
    base_path = "vdp-app-config-default"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": {{"$match": "{base_path}/*"}},
            "type": "folder"
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)

    if response.status_code == 401:
        print('❌ You are not authorized to access Artifactory. Use `sima-cli -i login` with your Artifactory identity token to authenticate, then try again.')
        return []

    if response.status_code != 200:
        print(f"❌ Failed to retrieve app versions (status {response.status_code})")
        print(response.text)
        return []

    results = response.json().get("results", [])

    # Versions = folder names under vdp-app-config-default/
    versions = sorted({
        item["path"].replace(base_path + "/", "").split("/")[0]
        for item in results
        if item["path"].startswith(base_path + "/")
    })

    if match_keyword:
        mk = match_keyword.lower()
        versions = [v for v in versions if mk in v.lower()]

    return versions


def _list_available_apps_internal(version: str):
    """
    List available app folders from Artifactory for the given SDK version.
    Returns distinct top-level folders under vdp-app-config-default/{version}/.
    After selecting an app, shows its description and action menu.
    """
    repo = "vdp"
    base_prefix = f"vdp-app-config-default/{version}"
    aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "path": {{"$match": "{base_prefix}/*"}}
        }}).include("repo","path","name")
    """.strip()

    aql_url = f"{ARTIFACTORY_BASE_URL}/api/search/aql"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {get_auth_token(internal=True)}"
    }

    response = requests.post(aql_url, data=aql_query, headers=headers)
    if response.status_code != 200:
        click.echo(f"❌ Failed to retrieve app list (status {response.status_code})")
        click.echo(response.text)
        return None

    results = response.json().get("results", [])

    # Collect only top-level folder names under {version}/
    app_names = sorted({
        item["path"].replace(base_prefix + "/", "").split("/")[0]
        for item in results
        if item["path"].startswith(base_prefix + "/")
    })

    if not app_names:
        click.echo("⚠️ No apps found.")
        return None

    # Add Exit option at the bottom
    app_names_with_exit = app_names + ["Exit"]

    from InquirerPy import inquirer

    while True:
        # Step 1: Select app
        selected_app = inquirer.fuzzy(
            message=f"Select an app from version {version}:",
            choices=app_names_with_exit,
            max_height="70%",
            instruction="(Use ↑↓ to navigate, / to search, Enter to select)"
        ).execute()

        if not selected_app or selected_app == "Exit":
            click.echo("👋 Exiting.")
            break

        # Step 2: Describe the app
        _describe_app_internal(version, selected_app)

        # Step 3: Action menu
        action = inquirer.select(
            message=f"What would you like to do with {selected_app}?",
            choices=["Download", "Back", "Exit"],
            default="Back"
        ).execute()

        if action == "Download":
            _download_app_internal(version, selected_app)
            click.echo(f"✅ Downloaded {selected_app}")
            # loop back to menu again after download
        elif action == "Back":
            # back to app list (continue loop)
            continue
        elif action == "Exit":
            click.echo("👋 Exiting.")
            break


def list_apps(internal, ver):
    if internal:
        click.echo("App Zoo Source : SiMa Artifactory...")
        versions = _list_available_app_versions_internal(ver)

        if len(versions) == 1:
            # Exactly one match → go straight to listing apps
            return _list_available_apps_internal(versions[0])
        elif len(versions) == 0:
            print(f'❌ No version match found in Artifactory for [{ver}]')
            return []
        else:
            # Multiple matches → prompt user to choose
            click.echo("Multiple app zoo versions found matching your input:")

            from InquirerPy import inquirer
            selected_version = inquirer.fuzzy(
                message="Select a version:",
                choices=versions,
                max_height="70%",  # scrollable
                instruction="(Use ↑↓ to navigate, / to search, Enter to select)"
            ).execute()

            if not selected_version:
                click.echo("No selection made. Exiting.", err=True)
                raise SystemExit(1)

            return _list_available_apps_internal(selected_version)

    else:
        print('External app zoo not supported yet')
        return []

def download_app(internal, ver, model_name):
    if internal:
        click.echo("App Zoo Source : SiMa Artifactory...")
        return _download_app_internal(ver, model_name)
    else:
        print('External app zoo not supported yet')

def describe_app(internal, ver, model_name):
    if internal:
        click.echo("App Zoo Source : SiMa Artifactory...")
        return _describe_app_internal(ver, model_name)
    else:
        print('External app zoo not supported yet')

# Module CLI tests
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python models.py <version>")
    else:
        version_arg = sys.argv[1]
        _list_available_apps_internal(version_arg)
