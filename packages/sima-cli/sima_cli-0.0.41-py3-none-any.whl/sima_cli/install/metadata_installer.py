import os
import re
import tempfile
import click
import json
import sys
import shutil
import tarfile
import zipfile
import stat
import shlex
from urllib.parse import urlparse, quote, urljoin
from typing import Dict
from tqdm import tqdm
from pathlib import Path
import subprocess
import requests

from rich.console import Console
from rich.panel import Panel

from huggingface_hub import snapshot_download

from sima_cli.utils.disk import check_disk_space
from sima_cli.utils.env import get_environment_type, get_exact_devkit_type, get_sima_build_version
from sima_cli.download.downloader import download_file_from_url
from sima_cli.install.metadata_validator import validate_metadata, MetadataValidationError
from sima_cli.install.metadata_info import print_metadata_summary, parse_size_string_to_bytes
from sima_cli.utils.container_registries import install_from_cr

console = Console()

def _copy_dir(src: Path, dest: Path, label: str):
    """
    Copy files from src → dest, merging with existing files (no deletion).
    Does NOT overwrite files if they already exist.
    Ensures that all parent directories for dest are created.
    """
    if not src.exists():
        raise FileNotFoundError(f"SDK {label} not found: {src}")

    dest.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            _copy_dir(item, target, label)
        else:
            if not target.exists():
                shutil.copy2(item, target)
    
    click.echo(f"✅ Copied {label} into {dest}")

def _prepare_pipeline_project(repo_dir: Path):
    """
    Prepare a pipeline project by copying required SDK sources into the repo.

    Steps:
      1. Copy core sources into the project folder
      2. Parse .project/pluginsInfo
      3. Copy required plugin sources from the SDK plugin zoo
    """
    plugins_info_file = repo_dir / ".project" / "pluginsInfo.json"
    if not plugins_info_file.exists():
        return 

    click.echo("📦 Preparing pipeline project...")

    try:
        data = json.loads(plugins_info_file.read_text())
        plugins = data.get("pluginsInfo", [])
    except Exception as e:
        raise RuntimeError(f"Failed to read {plugins_info_file}: {e}")

    # Step a: copy core
    # Define what to copy
    copy_map = [
        (
            Path("/usr/local/simaai/plugin_zoo/gst-simaai-plugins-base/core"),
            repo_dir / "core",
            "core"
        ),
        (
            Path("/usr/local/simaai/utils/gst_app"),
            repo_dir / "dependencies" / "gst_app",
            "dependencies/gst_app"
        ),
        (
            Path("/usr/local/simaai/plugin_zoo/gst-simaai-plugins-base/gst/templates"),
            repo_dir / "plugins" / "templates",
            "plugins/templates"
        ),
    ]

    # Execute
    for src, dest, label in copy_map:
        _copy_dir(src, dest, label)

    # Step b/c: scan plugin paths and copy SDK plugins
    sdk_plugins_base = Path("/usr/local/simaai/plugin_zoo/gst-simaai-plugins-base/gst")
    sdk_alt_base = sdk_plugins_base / "PyGast-plugins"

    dest_plugins_dir = repo_dir / "plugins"
    dest_plugins_dir.mkdir(exist_ok=True)

    for plugin in plugins:
        try:
            path = plugin.get("path", "")
            if not path:
                continue
            parts = path.split("/")
            if len(parts) < 2:
                continue

            plugin_name = parts[1]

            # Look first in gst/, then fallback to gst/PyGast-plugins/
            sdk_plugin_path = sdk_plugins_base / plugin_name
            if not sdk_plugin_path.exists():
                sdk_plugin_path = sdk_alt_base / plugin_name

            if not sdk_plugin_path.exists():
                click.echo(
                    f"⚠️ Missing plugin source: {plugin_name} in the SDK, skipping. "
                    "It is likely a custom plugin already in the repo so it's safe to ignore this warning."
                )
                continue

            dest_plugin_path = dest_plugins_dir / plugin_name
            dest_plugin_path.mkdir(parents=True, exist_ok=True)

            # Walk the SDK plugin dir and copy only missing files
            for src_file in sdk_plugin_path.rglob("*"):
                if src_file.is_file():
                    rel_path = src_file.relative_to(sdk_plugin_path)
                    dest_file = dest_plugin_path / rel_path
                    if dest_file.exists():
                        click.echo(f"↩️  Skipped existing file in the repo: {dest_file}")
                        continue
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)

            click.echo(f"✅ Copied plugin {plugin_name} into {dest_plugin_path} (safe copy)")

        except Exception as e:
            click.echo(f"❌ Error copying plugin {plugin}: {e}")

    click.echo("🎉 Pipeline project prepared.")

def _download_requirements_wheels(repo_dir: Path):
    """
    Look for resources/dependencies/requirements.txt under the repo,
    parse each line, and download wheels into the same folder.
    Supports optional pip download flags in parentheses.

    Example line formats:
        jax==0.6.2
        jaxlib==0.6.2 (--platform manylinux2014_aarch64 --python-version 310 --abi cp310)
    """
    deps_dir = repo_dir / "resources" / "dependencies"
    req_file = deps_dir / "requirements.txt"

    if not req_file.exists():
        click.echo("⚠️  No requirements.txt found under resources/dependencies in the repo, skipping wheel download, safe to ignore this message")
        return

    deps_dir.mkdir(parents=True, exist_ok=True)

    with req_file.open("r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not lines:
        click.echo("⚠️ requirements.txt is empty, nothing to download.")
        return

    for line in lines:
        # Split package and extra params if present
        if "(" in line and ")" in line:
            pkg_part, extra = line.split("(", 1)
            package = pkg_part.strip()
            extra_args = shlex.split(extra.strip(") "))
        else:
            package = line.strip()
            extra_args = []

        click.echo(f"⬇️  Downloading {package} {extra_args if extra_args else ''}")

        try:
            cmd = [
                "pip3", "download", "--no-deps",
                "--only-binary=:all:",
                "-d", str(deps_dir),
                package,
            ] + extra_args

            rc = os.system(" ".join(shlex.quote(c) for c in cmd))
            if rc != 0:
                click.echo(f"❌ pip download failed for {package}")
            else:
                click.echo(f"✅ Downloaded {package} into {deps_dir}")
        except Exception as e:
            click.echo(f"❌ Error downloading {package}: {e}")

def _download_github_repo(owner: str, repo: str, ref: str, dest_folder: str, token: str = None) -> str:
    """
    Download and extract a GitHub repo tarball via the REST API (no git required).

    Args:
        owner (str): GitHub org/user
        repo (str): Repo name
        ref (str): Branch, tag, or commit (default = default branch)
        dest_folder (str): Where to extract
        token (str): Optional GitHub token for private repos

    Returns:
        str: Path to the extracted repo
    """
    # Encode ref for API, but sanitize separately for filesystem usage
    if ref:
        ref_encoded = quote(ref, safe="")  # safe for URL
        ref_safe = ref.replace("/", "_")   # safe for filesystem
        url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{ref_encoded}"
    else:
        ref_encoded = ref_safe = None
        url = f"https://api.github.com/repos/{owner}/{repo}/tarball"

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    click.echo(f"🐙 Downloading GitHub repo: {owner}/{repo}" + (f"@{ref}" if ref else ""))

    with requests.get(url, headers=headers, stream=True) as r:
        if r.status_code in (401, 403):
            raise PermissionError("Authentication required for GitHub repo")
        r.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp_file:
            for chunk in r.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = Path(tmp_file.name)

    # Use sanitized ref in folder name (if provided)
    repo_dir = Path(dest_folder) / repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    _extract_tar_strip_top_level(tmp_path, repo_dir)
    tmp_path.unlink(missing_ok=True)

    click.echo(f"✅ Downloaded GitHub repo to folder: {repo_dir}")
    _download_requirements_wheels(repo_dir=repo_dir)

    try:
        _prepare_pipeline_project(repo_dir)
    except Exception as e:
        click.echo(f"⚠️  Pipeline preparation skipped: {e}")

    return str(repo_dir)

def _download_assets(metadata: dict, base_url: str, dest_folder: str, internal: bool = False, skip_models: bool = False, tag: str = None) -> list:
    """
    Downloads resources defined in metadata to a local destination folder.

    Supports resource types:
        - Regular files or URLs
        - Hugging Face repos (hf:<repo_id>@revision)
        - GitHub repos (gh:<owner>/<repo>@ref)
        - Container registries (cr:<registry>/<image>[:tag])

    Args:
        metadata (dict): Parsed and validated metadata
        base_url (str): Base URL of the metadata file (used to resolve relative resource paths)
        dest_folder (str): Local path to download resources into
        internal (bool): Whether to use internal routing (e.g., Artifactory Docker registry)
        skip_models (bool): If True, skips downloading any file path starting with 'models/'
        tag (str): metadata.json tag from GitHub passed into resources if applicable

    Returns:
        list: Paths to the downloaded local files or pulled container image identifiers
    """
    resources = metadata.get("resources", [])
    if not resources:
        raise click.ClickException("❌ No 'resources' defined in metadata.")

    os.makedirs(dest_folder, exist_ok=True)
    local_paths = []

    # Filter model files if needed
    filtered_resources = []
    for r in resources:
        if skip_models and r.strip().lower().startswith("models/"):
            click.echo(f"⏭️  Skipping model file: {r}")
            continue
        filtered_resources.append(r)

    if not filtered_resources:
        click.echo("ℹ️ No non-model resources to download.")
        return []

    click.echo(f"📥 Downloading {len(filtered_resources)} resource(s) to: {dest_folder}\n")

    for resource in filtered_resources:
        try:
            # Handle Hugging Face snapshot-style URL: "hf:<repo_id>@version"
            if resource.startswith("hf:"):
                # Strip prefix and split by @
                resource_spec = resource[3:]
                if "@" in resource_spec:
                    repo_id, revision = resource_spec.split("@", 1)
                else:
                    repo_id, revision = resource_spec, None

                if "/" not in repo_id:
                    raise click.ClickException(f"❌ Invalid Hugging Face repo spec: {resource}")

                org, name = repo_id.split("/", 1)
                target_dir = os.path.join(dest_folder, name)

                click.echo(f"🤗 Downloading Hugging Face repo: {org}/{repo_id}" + (f"@{revision}" if revision else ""))
                model_path = snapshot_download(
                    repo_id=repo_id,
                    revision=revision,
                    local_dir=target_dir,
                    local_dir_use_symlinks=False
                )
                local_paths.append(model_path)
                continue

            # 🐙 GitHub repo
            if resource.startswith("gh:"):
                resource_spec = resource[3:]
                if "@" in resource_spec:
                    repo_id, ref = resource_spec.split("@", 1)
                else:
                    repo_id, ref = resource_spec, tag

                if "/" not in repo_id:
                    raise click.ClickException(f"❌ Invalid GitHub repo spec: {resource}")

                owner, name = repo_id.split("/", 1)

                try:
                    token = os.getenv("GITHUB_TOKEN", None)
                    repo_path = _download_github_repo(owner, name, ref, dest_folder, token)
                except Exception as e:
                    raise click.ClickException(
                        f"❌ Failed to download GitHub repo {owner}/{name}@{ref or 'default'}: {e}"
                    )
                local_paths.append(repo_path)
                continue

            # 🐳 Container registry support
            if resource.startswith("cr:"):
                install_from_cr(resource, internal=internal)
                continue

            # 🌐 Standard file or URL
            resource_url = urljoin(base_url, resource)
            local_path = download_file_from_url(
                url=resource_url,
                dest_folder=dest_folder,
                internal=internal
            )
            click.echo(f"✅ Downloaded: {resource}")
            local_paths.append(local_path)

        except Exception as e:
            raise click.ClickException(f"❌ Failed to download resource '{resource}': {e}")

    return local_paths


def selectable_resource_handler(metadata):
    selectable = metadata.get("selectable-resources")
    if not selectable:
        return metadata

    choices = [(f"{i.get('name','Unnamed')} ({i.get('url','')})" if i.get('url') else i.get('name','Unnamed')) for i in selectable]
    choices.append("Skip")

    from InquirerPy import inquirer
    
    sel = inquirer.select(message="Select an opt-in resource to download:", choices=choices).execute()
    if sel == "Skip":
        print("✅ No selectable resource chosen.")
        return metadata

    idx = choices.index(sel)
    entry = selectable[idx]
    res = entry.get("resource")
    if res:
        metadata.setdefault("resources", [])
        if res not in metadata["resources"]:
            metadata["resources"].append(res)
        print(f"✅ Selected: {entry.get('name','(unnamed)')} → {res}")
    return metadata

def _download_and_validate_metadata(metadata_url, internal=False):
    """
    Downloads (if remote), validates, and parses metadata from a given URL or local file path.

    Args:
        metadata_url (str): URL or local path to a metadata.json file
        internal (bool): Whether to use internal mirrors or logic in downloader

    Returns:
        tuple: (parsed metadata dict, folder containing the metadata file)
    """
    try:
        parsed = urlparse(metadata_url)

        # Case 1: Local file (e.g., /path/to/file or ./file)
        if parsed.scheme == "" or parsed.scheme == "file":
            metadata_path = parsed.path
            if not os.path.isfile(metadata_path):
                raise FileNotFoundError(f"File not found: {metadata_path}")
            click.echo(f"📄 Using local metadata file: {metadata_path}")

        # Case 2: Remote URL
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                metadata_path = download_file_from_url(
                    url=metadata_url,
                    dest_folder=tmpdir,
                    internal=internal
                )
                click.echo(f"⬇️  Downloaded metadata to: {metadata_path}")
                
                # Must copy to outside tmpdir since tmpdir will be deleted
                # But since we're returning contents only, no need to keep file
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                validate_metadata(metadata)
                click.echo("✅ Metadata validated successfully.")
                metadata = selectable_resource_handler(metadata)
                return metadata, os.path.dirname(metadata_path)

        # Common validation logic for local file
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        validate_metadata(metadata)
        metadata = selectable_resource_handler(metadata)
        click.echo("✅ Metadata validated successfully.")
        return metadata, os.path.dirname(os.path.abspath(metadata_path))

    except MetadataValidationError as e:
        click.echo(f"❌ Metadata validation failed: {e}")
        raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Failed to retrieve or parse metadata from {metadata_url}: {e}")
        raise click.Abort()
    
def _check_whether_disk_is_big_enough(metadata: dict):
    # Step 3: Disk space check
    try:
        install_size_str = metadata.get("size", {}).get("install")
        if install_size_str:
            required_bytes = parse_size_string_to_bytes(install_size_str)
            if not check_disk_space(required_bytes, folder="."):
                required_gb = required_bytes / 1e9
                raise click.ClickException(
                    f"Not enough disk space. At least {required_gb:.2f} GB required the in current directory."
                )

            available_bytes = shutil.disk_usage(".").free
            available_gb = available_bytes / 1e9
            required_gb = required_bytes / 1e9
            click.echo(f"🗄️  Available disk space: {available_gb:.2f} GB")
            click.echo(f"✅ Enough disk space for installation: requires {required_gb:.2f} GB")
            return True
    except Exception as e:
        click.echo(f"❌ Failed to validate disk space: {e}")
        raise click.Abort()

    return False

def _extract_tar_streaming(tar_path: Path, extract_dir: Path):
    """
    Extract tar while preserving full folder structure.
    """
    extracted_files = 0
    with tarfile.open(tar_path, "r:*") as tar:
        with tqdm(desc=f"📦 Extracting {tar_path.name}", unit=" file") as pbar:
            while True:
                member = tar.next()
                if member is None:
                    break

                # Don't strip anything — preserve full path
                if not member.name.strip():
                    print(f"⚠️ Skipping empty member in archive: {member}")
                    continue

                tar.extract(member, path=extract_dir)
                extracted_files += 1
                pbar.update(1)

    print(f"✅ Extracted {extracted_files} files to {extract_dir}/")

def _extract_zip_streaming(zip_path: Path, extract_dir: Path, overwrite: bool = True):
    """
    Extract a .zip file using streaming and flatten one top-level directory if present.
    - Handles directory entries correctly
    - Preserves unix perms when available
    - Zip-slip safe
    """
    def strip_top_level(p: str) -> Path:
        parts = Path(p).parts
        if not parts:
            return Path()
        return Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()
        with tqdm(total=len(members), desc=f"📦 Extracting {zip_path.name}", unit="file") as pbar:
            for info in members:
                # Compute flattened path
                stripped = strip_top_level(info.filename)

                # Some zips can have '' or '.' entries; skip them
                if str(stripped).strip() in {"", ".", "./"}:
                    pbar.update(1)
                    continue

                target = (extract_dir / stripped).resolve()

                # Zip-slip guard: ensure target stays under extract_dir
                if not str(target).startswith(str(extract_dir.resolve()) + os.sep):
                    pbar.update(1)
                    continue  # or raise RuntimeError("Unsafe zip path detected")

                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    pbar.update(1)
                    continue

                # Ensure parent exists
                target.parent.mkdir(parents=True, exist_ok=True)

                # Skip if exists and not overwriting
                if target.exists() and not overwrite:
                    pbar.update(1)
                    continue

                # Stream copy the file
                with zf.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                # Preserve unix permissions if present
                perms = info.external_attr >> 16
                if perms and not stat.S_ISDIR(perms):
                    try:
                        os.chmod(target, perms)
                    except Exception:
                        pass

                pbar.update(1)

    print(f"✅ Extracted {len(members)} entries to {extract_dir}/")

def _extract_tar_strip_top_level(tar_path: Path, extract_dir: Path):
    """Extract a GitHub tarball, stripping the top-level folder."""
    with tarfile.open(tar_path, "r:*") as tar:
        members = tar.getmembers()

        # Detect top-level prefix (first part before '/')
        top_level = None
        if members:
            first_name = members[0].name
            top_level = first_name.split("/", 1)[0]

        for member in members:
            # Strip top-level folder
            if top_level and member.name.startswith(top_level + "/"):
                member.name = member.name[len(top_level) + 1 :]
            if not member.name:
                continue
            tar.extract(member, path=extract_dir)

def _combine_multipart_files(folder: str):
    """
    Scan a folder for multipart files like name-split-aa, -ab, etc.,
    combine them into a single file, and remove the split parts.
    Then auto-extract .tar files with progress.
    """
    folder = Path(folder)
    parts_by_base = {}

    # Step 1: Group parts by base name
    for file in folder.iterdir():
        if not file.is_file():
            continue

        match = re.match(r"(.+)-split-([a-z]{2})$", file.name)
        if match:
            base, part = match.groups()
            parts_by_base.setdefault(base, []).append((part, file))

    # Step 2: Process each group
    for base, parts in parts_by_base.items():
        parts.sort(key=lambda x: x[0])
        output_file = folder / f"{base}.tar"
        total_size = sum(part_file.stat().st_size for _, part_file in parts)

        print(f"\n🧩 Reassembling: {output_file.name} from {len(parts)} parts")

        if not output_file.exists():
            with open(output_file, "wb") as outfile, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Combining {output_file.name}",
            ) as pbar:
                for _, part_file in parts:
                    with open(part_file, "rb") as infile:
                        while True:
                            chunk = infile.read(1024 * 1024)  # 1MB
                            if not chunk:
                                break
                            outfile.write(chunk)
                            pbar.update(len(chunk))

        # Step 3: Remove original parts
        # for _, part_file in parts:
        #     part_file.unlink()

        print(f"✅ Created: {output_file.name} ({output_file.stat().st_size / 1e6:.2f} MB)")

        # Step 4: Auto-extract .tar
        extract_dir = folder / base
        print(f"📦 Extracting {output_file.name} to {extract_dir}/")
        _extract_tar_streaming(output_file, extract_dir)

        print(f"✅ Extracted to: {extract_dir}/")

def _extract_archives_in_folder(folder: str, local_paths):
    """
    Extract .tar, .gz, .tar.gz, and .zip files in the given folder,
    but only if they are listed in local_paths.
    Uses streaming to avoid NFS performance issues.
    """
    folder = Path(folder)
    local_paths = {str(Path(p).resolve()) for p in local_paths}

    for file in folder.iterdir():
        if not file.is_file():
            continue

        file_resolved = str(file.resolve())
        if file_resolved not in local_paths:
            continue

        # TAR, GZ, TAR.GZ → all handled by _extract_tar_streaming
        if file.suffix in [".tar", ".gz"] or file.name.endswith(".tar.gz"):
            extract_dir = folder / file.stem.replace(".tar", "")
            print(f"📦 Extracting TAR/GZ: {file.name} to {extract_dir}/")
            _extract_tar_streaming(file, extract_dir)

        # ZIP
        elif file.suffix == ".zip":
            extract_dir = folder / file.stem
            print(f"📦 Extracting ZIP: {file.name} to {extract_dir}/")
            _extract_zip_streaming(file, extract_dir)

def _is_platform_compatible(metadata: dict) -> bool:
    """
    Determines if the current environment is compatible with the package metadata.

    Args:
        metadata (dict): Metadata that includes a 'platforms' section

    Returns:
        bool: True if compatible, False otherwise
    """
    env_type, env_subtype = get_environment_type()
    exact_devkit_type = get_exact_devkit_type()
    platforms = metadata.get("platforms", [])

    for i, platform_entry in enumerate(platforms):
        platform_type = platform_entry.get("type")

        # For SDK environment compatibility check.
        if (platform_type, env_type, env_subtype) == ("palette", "sdk", "palette"):
            return True

        if platform_type != env_type:
            continue

        # For board/devkit: check compatible_with list
        if env_type == "board":
            compat = platform_entry.get("compatible_with", [])
            if env_subtype not in compat and exact_devkit_type not in compat:
                continue

        # For host/sdk/generic: optionally check OS match
        if "os" in platform_entry:
            supported_oses = [os_name.lower() for os_name in platform_entry["os"]]
            if env_subtype.lower() not in supported_oses:
                continue

        # Passed all checks
        return True

    click.echo(f"❌ Current environment [{env_type}:{env_subtype}] is not compatible with the package")
    return False


def _print_post_install_message(metadata: Dict):
    """
    Print post-installation instructions from the metadata in a compact box.

    Args:
        metadata (Dict): The package metadata dictionary.
    """
    msg = metadata.get("installation", {}).get("post-message", "").strip()

    if msg:
        panel = Panel.fit(
            msg,
            title="[bold green]Post-Installation Instructions[/bold green]",
            title_align="left",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)

def _run_installation_script(metadata: Dict, extract_path: str = "."):
    """
    Run the installation script specified in the metadata.

    Args:
        metadata (dict): Metadata dictionary with an 'installation' key.
        extract_path (str): Path where the files were extracted.
    """
    script = metadata.get("installation", {}).get("script", "").strip()
    if not script:
        print("⚠️ No installation script provided. Follow package documentation to install the package.")
        return

    print(f"🚀 Running installation script in: {os.path.abspath(extract_path)}")
    print(f"📜 Script: {script}")

    # Determine shell type based on platform
    shell_executable = os.environ.get("COMSPEC") if os.name == "nt" else None

    try:
        subprocess.run(
            script,
            shell=True,
            executable=shell_executable,
            cwd=extract_path,
            check=True
        )
        _print_post_install_message(metadata=metadata)        
    except subprocess.CalledProcessError as e:
        print("❌ Installation failed with return code:", e.returncode)
        sys.exit(e.returncode)

    print("✅ Installation completed successfully.")

def _resolve_github_metadata_url(gh_ref: str) -> tuple[str, str]:
    """
    Resolve a GitHub shorthand like gh:org/repo@tag into a local metadata.json file path.
    If tag is omitted, defaults to 'main'.

    Args:
        gh_ref (str): Reference in the form 'gh:org/repo@tag'
    
    Returns:
        tuple[str, str]: (local_path_to_metadata_json, tag_used)
    """
    try:
        _, repo_ref = gh_ref.split(":", 1)  # strip 'gh:'
        if "@" in repo_ref:
            org_repo, tag = repo_ref.split("@", 1)
        else:
            org_repo, tag = repo_ref, "main"

        owner, repo = org_repo.split("/", 1)
        token = os.getenv("GITHUB_TOKEN")

        # Encode the ref safely for GitHub API
        tag_encoded = quote(tag, safe="")

        # GitHub API URL for raw file contents
        api_url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/metadata.json?ref={tag_encoded}"
        )
        headers = {"Accept": "application/vnd.github.v3.raw"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        r = requests.get(api_url, headers=headers)
        r.raise_for_status()

        # --- Sanitize tag for filesystem use ---
        tag_safe = tag.replace("/", "_")

        # Write metadata.json locally
        local_path = os.path.join("/tmp", f"{repo}-{tag_safe}-metadata.json")
        with open(local_path, "wb") as f:
            f.write(r.content)

        return local_path, tag
    except Exception as e:
        raise RuntimeError(f"Failed to resolve GitHub metadata URL {gh_ref}: {e}")

def install_from_metadata(metadata_url: str, internal: bool, install_dir: str = '.'):
    try:
        tag = None

        if metadata_url.startswith("gh:"):
            metadata_url, tag = _resolve_github_metadata_url(metadata_url)
            internal = False

        metadata, _ = _download_and_validate_metadata(metadata_url, internal)
        print_metadata_summary(metadata=metadata)

        if _check_whether_disk_is_big_enough(metadata):
            if _is_platform_compatible(metadata):
                local_paths = _download_assets(metadata, metadata_url, install_dir, internal, tag=tag)
                if len(local_paths) > 0:
                    _combine_multipart_files(install_dir)
                    _extract_archives_in_folder(install_dir, local_paths)
                    _run_installation_script(metadata=metadata, extract_path=install_dir)

    except Exception as e:
        click.echo(f"❌ Failed to install from metadata URL {metadata_url}: {e}")
        exit(1)

    return False

def metadata_resolver(component: str, version: str = None, tag: str = None) -> str:
    """
    Resolve the metadata.json URL for a given component and version/tag.

    Args:
        component (str): Component name (e.g., "examples.llima" or "assets/ragfps")
        version (str): Optional. If not provided, auto-detect from /etc/build.
        tag (str): Optional tag to use (e.g., "dev")

    Returns:
        str: Fully qualified metadata URL
    """

    if tag:
        metadata_name = f"metadata-{tag}.json"
    else:
        metadata_name = "metadata.json"

    # --- Asset case, assets are SDK version agnostic ---
    if component.startswith("assets/"):
        return f"https://docs.sima.ai/{component}/{metadata_name}"

    # --- Auto-detect SDK version if missing ---
    if not version:
        core_version, _ = get_sima_build_version()
        if core_version:
            version = core_version
        else:
            raise ValueError(
                "Version (-v) is required and could not be auto-detected "
                "from /etc/build or /etc/buildinfo."
            )

    sdk_path = f"SDK{version}"
    return f"https://docs.sima.ai/pkg_downloads/{sdk_path}/{component}/{metadata_name}"
