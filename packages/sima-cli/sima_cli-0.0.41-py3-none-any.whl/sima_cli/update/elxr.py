import subprocess
import click

from sima_cli.utils.env import is_devkit_running_elxr

def update_elxr(version_or_url: str | None):
    """
    Update packages on an ELXR-based devkit using simaai-ota.
    Uses InquirerPy for interactive menus.
    """
    # 1. Check ELXR system
    if not is_devkit_running_elxr():
        click.echo("ℹ️  Not an ELXR devkit, skipping update")
        return

    from InquirerPy import inquirer

    # 2. Check network connectivity
    if subprocess.call(["ping", "-c", "1", "deb.debian.org"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) != 0:
        click.echo("⚠️  ELXR devkit not connected to the network, skipping update")
        return

    # 3. Choose update path
    if version_or_url is None:
        choice = inquirer.select(
            message="How would you like to update this ELXR devkit?",
            choices=[
                {"name": "Update all packages (no reinstall if up-to-date)", "value": "normal"},
                {"name": "Update all packages (force reinstall)", "value": "force"},
                {"name": "Update to a specific simaai-palette version", "value": "version"},
                {"name": "Fix u-boot environment (force reinstall + overwrite)", "value": "fix-uboot"},
            ],
            default="normal"
        ).execute()

        if choice == "normal":
            cmd = ["simaai-ota"]
            desc = "Update all packages (no reinstall)"
        elif choice == "force":
            cmd = ["simaai-ota", "-f"]
            desc = "Update all packages (force reinstall)"
        elif choice == "version":
            version = inquirer.text(
                message="Enter simaai-palette version (e.g., git202510090802.8e94f9f-620):"
            ).execute()
            cmd = ["simaai-ota", "-v", version]
            desc = f"Update to specific version {version}"
        elif choice == "fix-uboot":
            cmd = ["simaai-ota", "-f", "-o"]
            desc = "Fix u-boot env (force reinstall + overwrite)"
        else:
            click.echo("❌ Invalid choice, aborting update")
            return
    else:
        cmd = ["simaai-ota", "-v", version_or_url]
        desc = f"Update to specific version {version_or_url}"

    # 4. Execute
    cmd = ["sudo"] + cmd
    click.echo(f"➡️  {desc}\n   " + click.style(f"Running: {' '.join(cmd)}", fg="cyan"))

    # Check if passwordless sudo is available
    if subprocess.call(["sudo", "-n", "true"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL) != 0:
        click.echo("ℹ️  sudo may prompt you for a password...")

    subprocess.check_call(cmd)
    click.echo("✅ ELXR update completed successfully")

