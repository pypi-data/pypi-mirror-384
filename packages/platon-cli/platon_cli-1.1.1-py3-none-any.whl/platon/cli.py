#!/usr/bin/env python3
"""
Platon CLI - Unified tool for Vault and Kubernetes operations
"""

import os
import click
import sys
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
from rich.prompt import Confirm, Prompt
import questionary
from pathlib import Path

from .config import Config
from .vault import VaultManager
from .kubectl import KubectlManager
from .git import GitRepo
from .utils import (
    handle_error,
    format_output,
    export_to_file,
    watch_logs,
    fuzzy_select,
)

console = Console()
config = Config()


def check_vault_installation():
    """Check if vault is installed and prompt user on first run"""
    if config.vault_checked:
        return True

    import shutil
    vault_path = shutil.which("vault")

    if vault_path:
        try:
            result = subprocess.run(
                ["vault", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            console.print("[green]✓[/green] HashiCorp Vault detected")
            console.print(f"[dim]{result.stdout.strip()}[/dim]")
            config.vault_checked = True
            config.save()
            return True
        except subprocess.CalledProcessError:
            pass

    console.print("[yellow]HashiCorp Vault is not installed or not in PATH[/yellow]")
    console.print("\nPlaton CLI requires HashiCorp Vault to manage secrets.")
    console.print("Install it from: [cyan]https://developer.hashicorp.com/vault/install[/cyan]")

    console.print("\nInstallation options:")
    console.print("  macOS:   brew install vault")
    console.print("  Linux:   See https://developer.hashicorp.com/vault/install")
    console.print("  Windows: choco install vault or download binary")

    if Confirm.ask("\nDo you have Vault installed but not in PATH?", default=False):
        console.print("[yellow]Please add Vault to your PATH and restart the CLI[/yellow]")

    if Confirm.ask("Mark Vault as checked (skip this warning)?", default=False):
        config.vault_checked = True
        config.save()
        return True

    return False


@click.group(invoke_without_command=True)
@click.option("--config-file", default=None, help="Path to config file")
@click.option("--profile", default="default", help="Profile to use")
@click.option("--install-completion", is_flag=True, hidden=True, help="Install shell completion")
@click.option("--show-completion", is_flag=True, hidden=True, help="Show completion script")
@click.pass_context
def cli(ctx, config_file, profile, install_completion, show_completion):
    """Platon CLI - Manage Vault secrets and Kubernetes resources"""

    if install_completion or show_completion:
        shell = Path(os.environ.get("SHELL", "bash")).name
        if show_completion:
            completion(shell)
        else:
            _install_completion(shell)
        sys.exit(0)

    if not check_vault_installation():
        console.print("\n[yellow]Continuing without Vault verification...[/yellow]")

    ctx.ensure_object(dict)
    
    if config_file:
        config.load(config_file)
    
    ctx.obj["config"] = config
    ctx.obj["profile"] = profile
    
    # Auto-detect repo if in git directory
    try:
        repo = GitRepo.from_cwd()
        ctx.obj["repo"] = repo
        ctx.obj["vault"] = VaultManager(repo)
        ctx.obj["kubectl"] = KubectlManager(repo)
    except Exception:
        ctx.obj["repo"] = None
    
    # If no command, show interactive menu
    if ctx.invoked_subcommand is None:
        interactive_menu(ctx)


def interactive_menu(ctx):
    """Interactive TUI menu"""
    if not ctx.obj.get("repo"):
        console.print("[red]Not in a git repository![/red]")
        sys.exit(1)

    repo = ctx.obj["repo"]

    # Display repo info
    panel = Panel(
        f"[green]Repository:[/green] {repo.path}\n"
        f"[green]Vault Path:[/green] {repo.vault_path}\n"
        f"[green]Namespace:[/green] {repo.namespace}",
        title="[bold blue]Platon CLI[/bold blue]",
        border_style="blue",
    )
    console.print(panel)

    while True:
        try:
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "Vault Operations",
                    "Kubernetes Operations",
                    "Sync Operations",
                    "Status & Info",
                    "Settings",
                    "Exit",
                ],
            ).ask()

            if choice == "Exit" or choice is None:
                break
            elif choice == "Vault Operations":
                vault_menu(ctx)
            elif choice == "Kubernetes Operations":
                kubectl_menu(ctx)
            elif choice == "Sync Operations":
                sync_menu(ctx)
            elif choice == "Status & Info":
                status_menu(ctx)
            elif choice == "Settings":
                settings_menu(ctx)
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


def vault_menu(ctx):
    """Vault operations submenu"""
    vault = ctx.obj["vault"]

    while True:
        try:
            choice = questionary.select(
                "Vault Operations:",
                choices=[
                    "List all secrets",
                    "Get secret",
                    "Add/Update secret",
                    "Delete secret",
                    "Import from file",
                    "Export secrets",
                    "Back",
                ],
            ).ask()

            if choice == "Back" or choice is None:
                break
            elif choice == "List all secrets":
                try:
                    secrets = vault.list_secrets()
                    table = Table(title="Vault Secrets")
                    table.add_column("Key", style="cyan")
                    table.add_column("Value", style="green")
                    for key, value in secrets.items():
                        masked = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
                        table.add_row(key, masked)
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Get secret":
                key = Prompt.ask("Enter secret key")
                value = vault.get_secret(key)
                if value:
                    console.print(f"[green]{key}[/green]: {value}")
                else:
                    console.print(f"[red]Secret {key} not found[/red]")
            elif choice == "Add/Update secret":
                key = Prompt.ask("Enter secret key")
                value = Prompt.ask("Enter secret value", password=True)
                try:
                    vault.set_secret(key, value)
                    console.print(f"[green]✓[/green] Secret {key} updated")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Delete secret":
                key = Prompt.ask("Enter secret key")
                if Confirm.ask(f"Delete secret {key}?"):
                    try:
                        vault.delete_secret(key)
                        console.print(f"[green]✓[/green] Secret {key} deleted")
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Import from file":
                try:
                    file_path = Prompt.ask("Path to file", default=".env")

                    format_choice = questionary.select(
                        "File format:",
                        choices=["env", "json", "yaml", "dotenv"],
                    ).ask()

                    if format_choice is None:
                        continue

                    from .utils import parse_file_to_dict
                    data = parse_file_to_dict(file_path, format_choice)

                    if not data:
                        console.print(f"[yellow]No variables found in {file_path}[/yellow]")
                        continue

                    console.print(f"[yellow]Found {len(data)} variables:[/yellow]")
                    for key in data.keys():
                        console.print(f"  {key}")

                    if Confirm.ask(f"Import these {len(data)} secrets to Vault?"):
                        result = vault.import_from_file(file_path, format_choice, merge=True)
                        console.print(f"[green]✓[/green] Imported {result['imported']} secrets")
                except FileNotFoundError:
                    console.print(f"[red]File not found: {file_path}[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Export secrets":
                try:
                    format_choice = questionary.select(
                        "Export format:",
                        choices=["env", "json", "yaml", "dotenv"],
                    ).ask()

                    if format_choice is None:
                        continue

                    secrets = vault.list_secrets()
                    formatted = format_output(secrets, format_choice)
                    console.print(formatted)

                    if Confirm.ask("Save to file?"):
                        filename = Prompt.ask("Filename", default=f"secrets.{format_choice}")
                        export_to_file(formatted, Path(filename), format_choice)
                        console.print(f"[green]✓[/green] Exported to {filename}")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


def kubectl_menu(ctx):
    """Kubernetes operations submenu"""
    kubectl = ctx.obj["kubectl"]

    while True:
        try:
            choice = questionary.select(
                "Kubernetes Operations:",
                choices=[
                    "List pods",
                    "List deployments",
                    "View deployment details",
                    "Describe deployment",
                    "Delete pod",
                    "Delete pods by label",
                    "View logs",
                    "Describe pod",
                    "Execute command",
                    "Scale deployment",
                    "Restart deployment",
                    "Back",
                ],
            ).ask()

            if choice == "Back" or choice is None:
                break
            elif choice == "List pods":
                try:
                    pods = kubectl.get_pods()
                    if not pods:
                        console.print("[yellow]No pods found[/yellow]")
                        continue
                    table = Table(title=f"Pods in {kubectl.namespace}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Status", style="green")
                    table.add_column("Restarts", style="yellow")
                    table.add_column("Age", style="blue")

                    for pod in pods:
                        table.add_row(
                            pod["name"],
                            pod["status"],
                            str(pod["restarts"]),
                            pod["age"],
                        )
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "List deployments":
                try:
                    deployments = kubectl.get_deployments()
                    if not deployments:
                        console.print("[yellow]No deployments found[/yellow]")
                        continue
                    table = Table(title=f"Deployments in {kubectl.namespace}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Ready", style="green")
                    table.add_column("Available", style="green")
                    table.add_column("Age", style="blue")

                    for dep in deployments:
                        table.add_row(
                            dep["name"],
                            f"{dep['ready']}/{dep['replicas']}",
                            str(dep["available"]),
                            dep["age"],
                        )
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "View deployment details":
                try:
                    deployments = kubectl.get_deployments()
                    if not deployments:
                        console.print("[yellow]No deployments found[/yellow]")
                        continue

                    dep_choices = [d["name"] for d in deployments]
                    selected = fuzzy_select(dep_choices, "Select deployment:")

                    deployment = kubectl.get_deployment(selected)

                    console.print(Panel(
                        f"[green]Name:[/green] {deployment['name']}\n"
                        f"[green]Namespace:[/green] {deployment['namespace']}\n"
                        f"[green]Replicas:[/green] {deployment['replicas']}\n"
                        f"[green]Ready:[/green] {deployment['ready']}\n"
                        f"[green]Available:[/green] {deployment['available']}\n"
                        f"[green]Updated:[/green] {deployment['updated']}\n"
                        f"[green]Strategy:[/green] {deployment['strategy']}\n"
                        f"[green]Age:[/green] {deployment['age']}",
                        title=f"Deployment: {deployment['name']}",
                        border_style="blue",
                    ))

                    if deployment['containers']:
                        console.print("\n[bold]Containers:[/bold]")
                        for container in deployment['containers']:
                            console.print(f"  [cyan]{container['name']}[/cyan]")
                            console.print(f"    Image: {container['image']}")
                            if container['ports']:
                                ports = ', '.join([str(p.get('containerPort', '')) for p in container['ports']])
                                console.print(f"    Ports: {ports}")

                    if deployment['selector']:
                        console.print("\n[bold]Selector:[/bold]")
                        for key, value in deployment['selector'].items():
                            console.print(f"  {key}={value}")

                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Describe deployment":
                try:
                    deployments = kubectl.get_deployments()
                    if not deployments:
                        console.print("[yellow]No deployments found[/yellow]")
                        continue

                    dep_choices = [d["name"] for d in deployments]
                    selected = fuzzy_select(dep_choices, "Select deployment:")

                    description = kubectl.describe_deployment(selected)
                    console.print(description)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Delete pod":
                try:
                    pods = kubectl.get_pods()

                    if not pods:
                        console.print("[yellow]No pods found[/yellow]")
                        continue

                    pod_choices = [p['name'] for p in pods]
                    selected = fuzzy_select(pod_choices, "Select pod to delete:")

                    pod_name = selected
                    force = questionary.confirm("Force delete?", default=False).ask()

                    if Confirm.ask(f"Delete pod {pod_name}?"):
                        kubectl.delete_pod(pod_name, force=force)
                        console.print(f"[green]✓[/green] Deleted pod {pod_name}")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Delete pods by label":
                try:
                    label = Prompt.ask("Label selector (e.g., app=myapp)")
                    namespace = Prompt.ask("Namespace (leave empty for current)", default="")

                    if Confirm.ask(f"Delete all pods with label '{label}'?"):
                        kubectl.delete_pods_by_label(label, namespace=namespace if namespace else None)
                        console.print(f"[green]✓[/green] Deleted pods matching label {label}")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Describe pod":
                try:
                    pods = kubectl.get_pods()

                    if not pods:
                        console.print("[yellow]No pods found[/yellow]")
                        continue

                    pod_choices = [p['name'] for p in pods]
                    selected = fuzzy_select(pod_choices, "Select pod:")

                    pod_name = selected
                    description = kubectl.describe_pod(pod_name)
                    console.print(description)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "View logs":
                try:
                    pods = kubectl.get_pods()
                    if not pods:
                        console.print("[yellow]No pods found[/yellow]")
                        continue
                    pod = fuzzy_select([p["name"] for p in pods], "Select pod:")
                    follow = Confirm.ask("Follow logs?", default=False)
                    kubectl.logs(pod, follow=follow)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Execute command":
                try:
                    pods = kubectl.get_pods()
                    if not pods:
                        console.print("[yellow]No pods found[/yellow]")
                        continue
                    pod = fuzzy_select([p["name"] for p in pods], "Select pod:")
                    command = Prompt.ask("Command", default="/bin/bash")
                    kubectl.exec(pod, command)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Scale deployment":
                deployment = Prompt.ask("Deployment name")
                replicas = Prompt.ask("Number of replicas", default="1")
                try:
                    kubectl.scale(deployment, int(replicas))
                    console.print(f"[green]✓[/green] Scaled {deployment} to {replicas} replicas")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Restart deployment":
                deployment = Prompt.ask("Deployment name")
                if Confirm.ask(f"Restart {deployment}?"):
                    try:
                        kubectl.restart(deployment)
                        console.print(f"[green]✓[/green] Restarted {deployment}")
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {str(e)}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


def sync_menu(ctx):
    """Sync operations submenu"""
    vault = ctx.obj["vault"]

    while True:
        try:
            choice = questionary.select(
                "Sync Operations:",
                choices=[
                    "Sync Vault to environment",
                    "Preview sync (dry-run)",
                    "Back",
                ],
            ).ask()

            if choice == "Back" or choice is None:
                break
            elif choice == "Sync Vault to environment":
                try:
                    secrets = vault.list_secrets()
                    if Confirm.ask(f"Export {len(secrets)} secrets to environment?"):
                        for key, value in secrets.items():
                            os.environ[key] = value
                        console.print(f"[green]✓[/green] Exported {len(secrets)} secrets to environment")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Preview sync (dry-run)":
                try:
                    secrets = vault.list_secrets()
                    console.print(f"[yellow]Would export {len(secrets)} secrets:[/yellow]")
                    for key in secrets:
                        console.print(f"  {key}")
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


def status_menu(ctx):
    """Status and info submenu"""
    repo = ctx.obj["repo"]
    vault = ctx.obj["vault"]
    kubectl = ctx.obj["kubectl"]

    while True:
        try:
            choice = questionary.select(
                "Status & Info:",
                choices=[
                    "Vault status",
                    "Kubernetes status",
                    "Repository info",
                    "All status",
                    "Back",
                ],
            ).ask()

            if choice == "Back" or choice is None:
                break
            elif choice == "Vault status":
                try:
                    vault_status = vault.health_check()
                    console.print(Panel(
                        f"[green]Status:[/green] {vault_status['status']}\n"
                        f"[green]Secrets:[/green] {vault_status['secret_count']}\n"
                        f"[green]Last Modified:[/green] {vault_status['last_modified']}",
                        title="Vault Status",
                        border_style="green" if vault_status["healthy"] else "red",
                    ))
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Kubernetes status":
                try:
                    k8s_status = kubectl.health_check()
                    console.print(Panel(
                        f"[green]Cluster:[/green] {k8s_status['cluster']}\n"
                        f"[green]Pods:[/green] {k8s_status['pod_count']}\n"
                        f"[green]Deployments:[/green] {k8s_status['deployment_count']}",
                        title="Kubernetes Status",
                        border_style="green" if k8s_status["healthy"] else "red",
                    ))
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
            elif choice == "Repository info":
                console.print(Panel(
                    f"[green]Repository:[/green] {repo.path}\n"
                    f"[green]Vault Path:[/green] {repo.vault_path}\n"
                    f"[green]Namespace:[/green] {repo.namespace}\n"
                    f"[green]Remote URL:[/green] {repo.remote_url}",
                    title="Repository Info",
                    border_style="blue",
                ))
            elif choice == "All status":
                try:
                    vault_status = vault.health_check()
                    k8s_status = kubectl.health_check()

                    console.print(Panel(
                        f"[green]Repository:[/green] {repo.path}\n"
                        f"[green]Vault Path:[/green] {repo.vault_path}\n"
                        f"[green]Namespace:[/green] {repo.namespace}",
                        title="Repository Info",
                        border_style="blue",
                    ))

                    console.print(Panel(
                        f"[green]Status:[/green] {vault_status['status']}\n"
                        f"[green]Secrets:[/green] {vault_status['secret_count']}\n"
                        f"[green]Last Modified:[/green] {vault_status['last_modified']}",
                        title="Vault Status",
                        border_style="green" if vault_status["healthy"] else "red",
                    ))

                    console.print(Panel(
                        f"[green]Cluster:[/green] {k8s_status['cluster']}\n"
                        f"[green]Pods:[/green] {k8s_status['pod_count']}\n"
                        f"[green]Deployments:[/green] {k8s_status['deployment_count']}",
                        title="Kubernetes Status",
                        border_style="green" if k8s_status["healthy"] else "red",
                    ))
                except Exception as e:
                    console.print(f"[red]Error:[/red] {str(e)}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


def settings_menu(ctx):
    """Settings submenu"""
    config = ctx.obj["config"]

    while True:
        try:
            choice = questionary.select(
                "Settings:",
                choices=[
                    "View configuration",
                    "List profiles",
                    "Switch profile",
                    "Edit configuration file",
                    "Back",
                ],
            ).ask()

            if choice == "Back" or choice is None:
                break
            elif choice == "View configuration":
                profile = config.get_profile()
                table = Table(title=f"Configuration (Profile: {config.current_profile})")
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Vault Address", profile.vault_addr or "Not set")
                table.add_row("Vault Mount", profile.vault_mount)
                table.add_row("Kubectl Context", profile.kubectl_context or "Default")
                table.add_row("Kubectl Namespace", profile.kubectl_namespace or "Default")
                table.add_row("Default Format", profile.default_format)
                table.add_row("Theme", profile.theme)
                table.add_row("Config File", str(config.config_file))

                console.print(table)
            elif choice == "List profiles":
                profiles = config.list_profiles()
                table = Table(title="Profiles")
                table.add_column("Name", style="cyan")
                table.add_column("Current", style="yellow")
                table.add_column("Vault Address", style="green")

                for name, profile in profiles.items():
                    is_current = "✓" if name == config.current_profile else ""
                    table.add_row(name, is_current, profile.vault_addr or "Not set")

                console.print(table)
            elif choice == "Switch profile":
                try:
                    profiles = list(config.list_profiles().keys())
                    if len(profiles) > 1:
                        profile_name = questionary.select(
                            "Select profile:",
                            choices=profiles,
                        ).ask()

                        if profile_name is not None:
                            config.set_profile(profile_name)
                            console.print(f"[green]✓[/green] Switched to profile: {profile_name}")
                    else:
                        console.print("[yellow]Only one profile exists[/yellow]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]Cancelled[/yellow]")
            elif choice == "Edit configuration file":
                console.print(f"Config file: {config.config_file}")
                if Confirm.ask("Open in editor?"):
                    import subprocess
                    editor = os.environ.get("EDITOR", "nano")
                    try:
                        subprocess.run([editor, str(config.config_file)])
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {str(e)}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            break


@cli.group()
def vault():
    """Vault secret management commands"""
    pass


@vault.command("get")
@click.argument("key", required=False)
@click.option("--all", is_flag=True, help="Get all secrets")
@click.option("--format", type=click.Choice(["table", "json", "yaml", "env"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Output to file")
@click.pass_context
def vault_get(ctx, key, all, format, output):
    """Get secrets from Vault"""
    vault = ctx.obj["vault"]
    
    if all or not key:
        secrets = vault.list_secrets()
        formatted = format_output(secrets, format)
        
        if output:
            export_to_file(formatted, output, format)
            console.print(f"[green]✓[/green] Exported to {output}")
        else:
            console.print(formatted)
    else:
        value = vault.get_secret(key)
        console.print(f"{key}={value}")


@vault.command("set")
@click.argument("key")
@click.argument("value", required=False)
@click.option("--from-file", type=click.Path(exists=True), help="Read value from file")
@click.option("--from-stdin", is_flag=True, help="Read value from stdin")
@click.pass_context
def vault_set(ctx, key, value, from_file, from_stdin):
    """Set a secret in Vault"""
    vault = ctx.obj["vault"]
    
    if from_file:
        value = Path(from_file).read_text().strip()
    elif from_stdin:
        value = sys.stdin.read().strip()
    elif not value:
        value = Prompt.ask(f"Enter value for {key}", password=True)
    
    vault.set_secret(key, value)
    console.print(f"[green]✓[/green] Secret {key} updated")


@vault.command("delete")
@click.argument("key")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.pass_context
def vault_delete(ctx, key, force):
    """Delete a secret from Vault"""
    vault = ctx.obj["vault"]
    
    if not force and not Confirm.ask(f"Delete secret {key}?"):
        return
    
    vault.delete_secret(key)
    console.print(f"[green]✓[/green] Secret {key} deleted")


@vault.command("export")
@click.option("--format", type=click.Choice(["env", "json", "yaml", "dotenv"]), default="env")
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--clipboard", is_flag=True, help="Copy to clipboard")
@click.pass_context
def vault_export(ctx, format, output, clipboard):
    """Export secrets to various formats"""
    vault = ctx.obj["vault"]
    secrets = vault.list_secrets()
    
    formatted = format_output(secrets, format)
    
    if clipboard:
        import pyperclip
        pyperclip.copy(formatted)
        console.print("[green]✓[/green] Copied to clipboard")
    elif output:
        export_to_file(formatted, output, format)
        console.print(f"[green]✓[/green] Exported to {output}")
    else:
        console.print(formatted)


@vault.command("diff")
@click.option("--version1", type=int, help="First version")
@click.option("--version2", type=int, help="Second version")
@click.pass_context
def vault_diff(ctx, version1, version2):
    """Compare vault secret versions"""
    vault = ctx.obj["vault"]
    diff = vault.diff_versions(version1, version2)

    syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)


@vault.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["env", "json", "yaml", "dotenv"]), help="File format (auto-detected if not specified)")
@click.option("--no-merge", is_flag=True, help="Replace all secrets instead of merging")
@click.option("--dry-run", is_flag=True, help="Show what would be imported")
@click.pass_context
def vault_import(ctx, file_path, format, no_merge, dry_run):
    """Import secrets from file to Vault"""
    vault = ctx.obj["vault"]

    from .utils import parse_file_to_dict

    try:
        if not format:
            if file_path.endswith('.json'):
                format = 'json'
            elif file_path.endswith(('.yaml', '.yml')):
                format = 'yaml'
            else:
                format = 'env'

        data = parse_file_to_dict(file_path, format)

        if not data:
            console.print(f"[yellow]No variables found in {file_path}[/yellow]")
            return

        if dry_run:
            console.print(f"[yellow]Would import {len(data)} secrets from {file_path}:[/yellow]")
            for key in data.keys():
                console.print(f"  {key}")

            if not no_merge:
                existing = vault.list_secrets()
                existing_keys = set(existing.keys())
                new_keys = set(data.keys())

                if existing_keys & new_keys:
                    console.print(f"\n[yellow]Would overwrite {len(existing_keys & new_keys)} existing secrets:[/yellow]")
                    for key in existing_keys & new_keys:
                        console.print(f"  {key}")
        else:
            if not no_merge and not Confirm.ask(f"Import {len(data)} secrets from {file_path}?"):
                return

            result = vault.import_from_file(file_path, format, merge=not no_merge)
            console.print(f"[green]✓[/green] Imported {result['imported']} secrets to Vault")

    except FileNotFoundError:
        console.print(f"[red]File not found: {file_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@cli.group()
def k8s():
    """Kubernetes resource management"""
    pass


@k8s.command("pods")
@click.option("--watch", "-w", is_flag=True, help="Watch for changes")
@click.option("--selector", "-l", help="Label selector")
@click.option("--namespace", "-n", help="Specific namespace to query")
@click.pass_context
def k8s_pods(ctx, watch, selector, namespace):
    """List pods"""
    kubectl = ctx.obj["kubectl"]

    if watch:
        watch_logs(lambda: kubectl.get_pods(selector, namespace=namespace))
    else:
        pods = kubectl.get_pods(selector, namespace=namespace)
        ns_title = namespace or kubectl.namespace
        table = Table(title=f"Pods in {ns_title}")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Restarts", style="yellow")
        table.add_column("Age", style="blue")

        for pod in pods:
            table.add_row(
                pod["name"],
                pod["status"],
                str(pod["restarts"]),
                pod["age"],
            )
        console.print(table)


@k8s.command("deployments")
@click.option("--namespace", "-n", help="Specific namespace to query")
@click.option("--output", "-o", type=click.Choice(["table", "json", "yaml"]), default="table")
@click.pass_context
def k8s_deployments(ctx, namespace, output):
    """List deployments"""
    kubectl = ctx.obj["kubectl"]
    deployments = kubectl.get_deployments(namespace=namespace)

    if output == "json":
        import json
        console.print(json.dumps(deployments, indent=2))
    elif output == "yaml":
        import yaml
        console.print(yaml.dump(deployments))
    else:
        ns_title = namespace or kubectl.namespace
        table = Table(title=f"Deployments in {ns_title}")
        table.add_column("Name", style="cyan")
        table.add_column("Ready", style="green")
        table.add_column("Available", style="green")
        table.add_column("Age", style="blue")

        for dep in deployments:
            table.add_row(
                dep["name"],
                f"{dep['ready']}/{dep['replicas']}",
                str(dep["available"]),
                dep["age"],
            )
        console.print(table)


@k8s.command("deployment")
@click.argument("deployment_name", required=False)
@click.option("--namespace", "-n", help="Namespace (defaults to repo namespace)")
@click.option("--output", "-o", type=click.Choice(["panel", "json", "yaml"]), default="panel")
@click.pass_context
def k8s_deployment(ctx, deployment_name, namespace, output):
    """Get deployment details"""
    kubectl = ctx.obj["kubectl"]

    if not deployment_name:
        deployments = kubectl.get_deployments(namespace=namespace)
        deployment_name = fuzzy_select([d["name"] for d in deployments], "Select deployment:")

    deployment = kubectl.get_deployment(deployment_name, namespace=namespace)

    if output == "json":
        import json
        console.print(json.dumps(deployment, indent=2))
    elif output == "yaml":
        import yaml
        console.print(yaml.dump(deployment))
    else:
        console.print(Panel(
            f"[green]Name:[/green] {deployment['name']}\n"
            f"[green]Namespace:[/green] {deployment['namespace']}\n"
            f"[green]Replicas:[/green] {deployment['replicas']}\n"
            f"[green]Ready:[/green] {deployment['ready']}\n"
            f"[green]Available:[/green] {deployment['available']}\n"
            f"[green]Updated:[/green] {deployment['updated']}\n"
            f"[green]Strategy:[/green] {deployment['strategy']}\n"
            f"[green]Age:[/green] {deployment['age']}",
            title=f"Deployment: {deployment['name']}",
            border_style="blue",
        ))

        if deployment['containers']:
            console.print("\n[bold]Containers:[/bold]")
            for container in deployment['containers']:
                console.print(f"  [cyan]{container['name']}[/cyan]")
                console.print(f"    Image: {container['image']}")
                if container['ports']:
                    ports = ', '.join([str(p.get('containerPort', '')) for p in container['ports']])
                    console.print(f"    Ports: {ports}")

        if deployment['selector']:
            console.print("\n[bold]Selector:[/bold]")
            for key, value in deployment['selector'].items():
                console.print(f"  {key}={value}")


@k8s.command("describe-deployment")
@click.argument("deployment_name", required=False)
@click.option("--namespace", "-n", help="Namespace (defaults to repo namespace)")
@click.pass_context
def k8s_describe_deployment(ctx, deployment_name, namespace):
    """Describe a deployment"""
    kubectl = ctx.obj["kubectl"]

    if not deployment_name:
        deployments = kubectl.get_deployments(namespace=namespace)
        deployment_name = fuzzy_select([d["name"] for d in deployments], "Select deployment:")

    description = kubectl.describe_deployment(deployment_name, namespace=namespace)
    console.print(description)


@k8s.command("delete")
@click.argument("pod_name")
@click.option("--namespace", "-n", help="Namespace (defaults to repo namespace)")
@click.option("--force", "-f", is_flag=True, help="Force delete with grace period 0")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def k8s_delete(ctx, pod_name, namespace, force, yes):
    """Delete a pod"""
    kubectl = ctx.obj["kubectl"]

    if not yes and not Confirm.ask(f"Delete pod {pod_name}?"):
        return

    kubectl.delete_pod(pod_name, namespace=namespace, force=force)
    console.print(f"[green]✓[/green] Deleted pod {pod_name}")


@k8s.command("delete-by-label")
@click.argument("label")
@click.option("--namespace", "-n", help="Namespace (defaults to repo namespace)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def k8s_delete_by_label(ctx, label, namespace, yes):
    """Delete pods matching a label selector"""
    kubectl = ctx.obj["kubectl"]

    if not yes and not Confirm.ask(f"Delete all pods with label '{label}'?"):
        return

    kubectl.delete_pods_by_label(label, namespace=namespace)
    console.print(f"[green]✓[/green] Deleted pods matching label {label}")


@k8s.command("describe")
@click.argument("pod_name")
@click.option("--namespace", "-n", help="Namespace (defaults to repo namespace)")
@click.pass_context
def k8s_describe(ctx, pod_name, namespace):
    """Describe a pod"""
    kubectl = ctx.obj["kubectl"]
    description = kubectl.describe_pod(pod_name, namespace=namespace)
    console.print(description)


@k8s.command("logs")
@click.argument("pod", required=False)
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--previous", is_flag=True, help="Show previous logs")
@click.option("--tail", type=int, default=100, help="Lines to show")
@click.option("--container", "-c", help="Container name")
@click.pass_context
def k8s_logs(ctx, pod, follow, previous, tail, container):
    """View pod logs"""
    kubectl = ctx.obj["kubectl"]
    
    if not pod:
        pods = kubectl.get_pods()
        pod = fuzzy_select([p["name"] for p in pods], "Select pod:")
    
    kubectl.logs(pod, follow=follow, previous=previous, tail=tail, container=container)


@k8s.command("exec")
@click.argument("pod", required=False)
@click.option("--container", "-c", help="Container name")
@click.option("--command", default="/bin/bash", help="Command to run")
@click.pass_context
def k8s_exec(ctx, pod, container, command):
    """Execute command in pod"""
    kubectl = ctx.obj["kubectl"]
    
    if not pod:
        pods = kubectl.get_pods()
        pod = fuzzy_select([p["name"] for p in pods], "Select pod:")
    
    kubectl.exec(pod, command, container=container)


@k8s.command("scale")
@click.argument("deployment")
@click.argument("replicas", type=int)
@click.pass_context
def k8s_scale(ctx, deployment, replicas):
    """Scale deployment"""
    kubectl = ctx.obj["kubectl"]
    kubectl.scale(deployment, replicas)
    console.print(f"[green]✓[/green] Scaled {deployment} to {replicas} replicas")


@k8s.command("restart")
@click.argument("deployment")
@click.pass_context
def k8s_restart(ctx, deployment):
    """Restart deployment"""
    kubectl = ctx.obj["kubectl"]
    kubectl.restart(deployment)
    console.print(f"[green]✓[/green] Restarted {deployment}")


@cli.command("sync")
@click.option("--direction", type=click.Choice(["to-env", "from-env"]), default="to-env")
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
@click.pass_context
def sync(ctx, direction, dry_run):
    """Sync secrets between Vault and environment"""
    vault = ctx.obj["vault"]
    
    if direction == "to-env":
        secrets = vault.list_secrets()
        
        if dry_run:
            console.print("[yellow]Would export:[/yellow]")
            for key in secrets:
                console.print(f"  {key}")
        else:
            for key, value in secrets.items():
                import os
                os.environ[key] = value
            console.print(f"[green]✓[/green] Exported {len(secrets)} secrets to environment")
    else:
        # Sync from env to vault
        console.print("[red]Not implemented yet[/red]")


@cli.command("status")
@click.pass_context
def status(ctx):
    """Show overall status"""
    repo = ctx.obj["repo"]
    vault = ctx.obj["vault"]
    kubectl = ctx.obj["kubectl"]
    
    # Create status panels
    vault_status = vault.health_check()
    k8s_status = kubectl.health_check()
    
    console.print(Panel(
        f"[green]Vault:[/green] {vault_status['status']}\n"
        f"[green]Secrets:[/green] {vault_status['secret_count']}\n"
        f"[green]Last Modified:[/green] {vault_status['last_modified']}",
        title="Vault Status",
        border_style="green" if vault_status["healthy"] else "red",
    ))
    
    console.print(Panel(
        f"[green]Cluster:[/green] {k8s_status['cluster']}\n"
        f"[green]Pods:[/green] {k8s_status['pod_count']}\n"
        f"[green]Deployments:[/green] {k8s_status['deployment_count']}",
        title="Kubernetes Status",
        border_style="green" if k8s_status["healthy"] else "red",
    ))


@cli.command("init")
@click.option("--template", type=click.Choice(["basic", "advanced"]), default="basic")
@click.pass_context
def init(ctx, template):
    """Initialize configuration for current repo"""
    repo = ctx.obj.get("repo")

    if not repo:
        console.print("[red]Not in a git repository[/red]")
        return

    config_file = Path(".platon.yaml")

    if config_file.exists():
        if not Confirm.ask("Config already exists. Overwrite?"):
            return

    config_data = {
        "vault_path": repo.vault_path,
        "namespace": repo.namespace,
        "template": template,
    }

    import yaml
    config_file.write_text(yaml.dump(config_data))
    console.print(f"[green]✓[/green] Created {config_file}")


def _install_completion(shell):
    """Install completion for the current shell"""
    if shell == "bash":
        rcfile = Path.home() / ".bashrc"
        marker = "# platon completion"
        script_call = 'eval "$(platon completion bash)"'
    elif shell == "zsh":
        rcfile = Path.home() / ".zshrc"
        marker = "# platon completion"
        script_call = 'eval "$(platon completion zsh)"'
    else:
        console.print(f"[red]Unsupported shell: {shell}[/red]")
        return

    if rcfile.exists():
        content = rcfile.read_text()
        if marker in content:
            console.print(f"[yellow]Completion already installed in {rcfile}[/yellow]")
            return

    with open(rcfile, "a") as f:
        f.write(f"\n{marker}\n{script_call}\n")

    console.print(f"[green]✓[/green] Completion installed to {rcfile}")
    console.print(f"[yellow]Run:[/yellow] source {rcfile}")


@cli.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh"]), required=False)
def completion(shell):
    """Generate shell completion script"""
    if not shell:
        shell = Path(os.environ.get("SHELL", "bash")).name

    if shell == "bash":
        script = """
# Platon CLI bash completion
_platon_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _PLATON_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

_platon_completion_setup() {
    complete -o nosort -F _platon_completion platon
    complete -o nosort -F _platon_completion plt
}

_platon_completion_setup;
"""
        console.print(script)
        console.print("\n[green]To enable bash completion, run:[/green]")
        console.print("  platon completion bash >> ~/.bashrc")
        console.print("  source ~/.bashrc")

    elif shell == "zsh":
        script = """
# Platon CLI zsh completion
#compdef platon plt

_platon() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[platon] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _PLATON_COMPLETE=zsh_complete platon)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _platon platon
compdef _platon plt
"""
        console.print(script)
        console.print("\n[green]To enable zsh completion, run:[/green]")
        console.print("  platon completion zsh >> ~/.zshrc")
        console.print("  source ~/.zshrc")


def main():
    """Entry point"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
