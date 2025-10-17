# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Matthew Watkins <mwatkins@linuxfoundation.org>

"""Typer-based CLI for gerrit-clone tool."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gerrit_clone import __version__
from gerrit_clone.clone_manager import clone_repositories
from gerrit_clone.config import ConfigurationError, load_config
from gerrit_clone.error_codes import (
    ExitCode,
    exit_for_configuration_error,
    DiscoveryError,
)
from gerrit_clone.file_logging import init_logging, cli_args_to_dict
from gerrit_clone.models import DiscoveryMethod
from gerrit_clone.rich_status import (
    create_status_manager,
    show_error_summary,
    show_final_results,
    handle_crash_display,
)


def _is_github_actions_context() -> bool:
    """Detect if running in GitHub Actions environment."""
    return (
        os.getenv("GITHUB_ACTIONS") == "true"
        or os.getenv("GITHUB_EVENT_NAME", "").strip() != ""
    )


# Show version information when --help is used
if "--help" in sys.argv:
    try:
        print(f"🏷️ gerrit-clone version {__version__}")
    except Exception:
        print("⚠️ gerrit-clone version information not available")


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console = Console()
        console.print(f"🏷️ gerrit-clone version [cyan]{__version__}[/cyan]")
        raise typer.Exit()


app = typer.Typer(
    name="gerrit-clone",
    help="A multi-threaded CLI tool for bulk cloning repositories from Gerrit servers.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version information",
    ),
) -> None:
    """Main CLI entry point with top-level options."""
    pass


@app.command()
def clone(
    host: str = typer.Option(
        ...,
        "--host",
        "-h",
        help="Gerrit server hostname",
        envvar="GERRIT_HOST",
    ),
    port: int | None = typer.Option(
        None,
        "--port",
        "-p",
        help="Gerrit port (default: 29418 for SSH, 443 for HTTPS)",
        envvar="GERRIT_PORT",
        min=1,
        max=65535,
    ),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        help="Base URL for Gerrit API (defaults to https://HOST)",
        envvar="GERRIT_BASE_URL",
    ),
    ssh_user: str | None = typer.Option(
        None,
        "--ssh-user",
        "-u",
        help="SSH username for clone operations",
        envvar="GERRIT_SSH_USER",
    ),
    ssh_identity_file: Path | None = typer.Option(
        None,
        "--ssh-private-key",
        "-i",
        help="SSH private key file for authentication",
        envvar="GERRIT_SSH_PRIVATE_KEY",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    path_prefix: Path = typer.Option(
        Path(),
        "--path-prefix",
        help="Base directory for clone hierarchy",
        envvar="GERRIT_PATH_PREFIX",
        file_okay=False,
        resolve_path=True,
    ),
    skip_archived: bool = typer.Option(
        True,
        "--skip-archived/--include-archived",
        help="Skip archived/read-only repositories",
        envvar="GERRIT_SKIP_ARCHIVED",
    ),
    include_project: list[str] = typer.Option(
        None,
        "--include-project",
        help="Restrict cloning to specific project(s). Repeat for multiple. Exact match required.",
        envvar=None,
    ),
    ssh_debug: bool = typer.Option(
        False,
        "--ssh-debug",
        help="Enable verbose SSH (-vvv) for troubleshooting authentication (single or few projects).",
        envvar="GERRIT_SSH_DEBUG",
    ),
    discovery_method: str = typer.Option(
        "ssh",
        "--discovery-method",
        help="Method for discovering projects: ssh (default), http (REST API only), or both (union of both methods with SSH metadata preferred)",
        envvar="GERRIT_DISCOVERY_METHOD",
    ),
    allow_nested_git: bool = typer.Option(
        True,
        "--allow-nested-git/--no-allow-nested-git",
        help="Allow nested git working trees when cloning both parent and child repositories",
        envvar="GERRIT_ALLOW_NESTED_GIT",
    ),
    nested_protection: bool = typer.Option(
        True,
        "--nested-protection/--no-nested-protection",
        help="Auto-add nested child repo paths to parent .git/info/exclude",
        envvar="GERRIT_NESTED_PROTECTION",
    ),
    move_conflicting: bool = typer.Option(
        True,
        "--move-conflicting/--no-move-conflicting",
        help="Move conflicting files/directories in parent repos to [NAME].parent to allow nested cloning",
        envvar="GERRIT_MOVE_CONFLICTING",
    ),
    threads: int | None = typer.Option(
        None,
        "--threads",
        "-t",
        help="Number of concurrent clone threads (default: auto)",
        envvar="GERRIT_THREADS",
        min=1,
    ),
    depth: int | None = typer.Option(
        None,
        "--depth",
        "-d",
        help="Create shallow clone with given depth",
        envvar="GERRIT_CLONE_DEPTH",
        min=1,
    ),
    branch: str | None = typer.Option(
        None,
        "--branch",
        "-b",
        help="Clone specific branch instead of default",
        envvar="GERRIT_BRANCH",
    ),
    use_https: bool = typer.Option(
        False,
        "--https/--ssh",
        help="Use HTTPS for cloning instead of SSH",
        envvar="GERRIT_USE_HTTPS",
    ),
    keep_remote_protocol: bool = typer.Option(
        False,
        "--keep-remote-protocol",
        help="Keep original clone protocol for remote (default: always set SSH)",
        envvar="GERRIT_KEEP_REMOTE_PROTOCOL",
    ),
    strict_host_checking: bool = typer.Option(
        True,
        "--strict-host/--accept-unknown-host",
        help="SSH strict host key checking",
        envvar="GERRIT_STRICT_HOST",
    ),
    clone_timeout: int = typer.Option(
        600,
        "--clone-timeout",
        help="Timeout per clone operation in seconds",
        envvar="GERRIT_CLONE_TIMEOUT",
        min=30,
    ),
    retry_attempts: int = typer.Option(
        3,
        "--retry-attempts",
        help="Maximum retry attempts per repository",
        envvar="GERRIT_RETRY_ATTEMPTS",
        min=1,
        max=10,
    ),
    retry_base_delay: float = typer.Option(
        2.0,
        "--retry-base-delay",
        help="Base delay for retry backoff in seconds",
        envvar="GERRIT_RETRY_BASE_DELAY",
        min=0.1,
    ),
    retry_factor: float = typer.Option(
        2.0,
        "--retry-factor",
        help="Exponential backoff factor for retries",
        envvar="GERRIT_RETRY_FACTOR",
        min=1.0,
    ),
    retry_max_delay: float = typer.Option(
        30.0,
        "--retry-max-delay",
        help="Maximum retry delay in seconds",
        envvar="GERRIT_RETRY_MAX_DELAY",
        min=1.0,
    ),
    manifest_filename: str = typer.Option(
        "clone-manifest.json",
        "--manifest-filename",
        help="Output manifest filename",
        envvar="GERRIT_MANIFEST_FILENAME",
    ),
    config_file: Path | None = typer.Option(
        None,
        "--config-file",
        "-c",
        help="Configuration file path (YAML or JSON)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug output",
        envvar="GERRIT_VERBOSE",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all output except errors",
        envvar="GERRIT_QUIET",
    ),
    cleanup: bool = typer.Option(
        False,
        "--cleanup/--no-cleanup",
        help="Remove cloned repositories (path-prefix) after run completes (success or failure)",
        envvar="GERRIT_CLEANUP",
    ),
    exit_on_error: bool = typer.Option(
        False,
        "--exit-on-error",
        "--stop-on-first-error",  # Backward compatibility
        help="Exit cloning immediately when the first error occurs (for debugging)",
        envvar="GERRIT_EXIT_ON_ERROR",
    ),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="Custom log file path (default: gerrit-clone.log in current directory)",
        envvar="GERRIT_LOG_FILE",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    disable_log_file: bool = typer.Option(
        False,
        "--disable-log-file",
        help="Disable creation of log file",
        envvar="GERRIT_DISABLE_LOG_FILE",
    ),
    log_level: str = typer.Option(
        "DEBUG",
        "--log-level",
        help="File logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        envvar="GERRIT_LOG_LEVEL",
    ),
) -> None:
    """Clone all repositories from a Gerrit server.

    This command discovers all projects on the specified Gerrit server and clones
    them in parallel while preserving the project hierarchy. Repositories are
    cloned over SSH and must be accessible with your configured SSH keys.

    Examples:

        # Clone all active repositories from gerrit.example.org
        gerrit-clone --host gerrit.example.org

        # Clone to specific directory with custom threads
        gerrit-clone --host gerrit.example.org --path-prefix ./repos --threads 8

        # Clone with shallow depth and specific branch
        gerrit-clone --host gerrit.example.org --depth 10 --branch main

        # Include archived repositories
        gerrit-clone --host gerrit.example.org --include-archived
    """
    # Set up console for error handling
    console = Console(stderr=True)

    # Initialize variables for exception handler scope
    file_logger = None
    error_collector = None
    log_file_path = None

    try:
        # Validate mutually exclusive options
        if verbose and quiet:
            console.print(
                "[red]Error:[/red] --verbose and --quiet cannot be used together"
            )
            raise typer.Exit(ExitCode.CONFIGURATION_ERROR)

        # Prepare CLI arguments for logging
        cli_args = cli_args_to_dict(
            host=host,
            port=port,
            base_url=base_url,
            ssh_user=ssh_user,
            ssh_identity_file=ssh_identity_file,
            path_prefix=path_prefix,
            skip_archived=skip_archived,
            include_project=include_project,
            ssh_debug=ssh_debug,
            allow_nested_git=allow_nested_git,
            nested_protection=nested_protection,
            move_conflicting=move_conflicting,
            threads=threads,
            depth=depth,
            branch=branch,
            use_https=use_https,
            keep_remote_protocol=keep_remote_protocol,
            strict_host_checking=strict_host_checking,
            clone_timeout=clone_timeout,
            retry_attempts=retry_attempts,
            retry_base_delay=retry_base_delay,
            retry_factor=retry_factor,
            retry_max_delay=retry_max_delay,
            manifest_filename=manifest_filename,
            config_file=config_file,
            verbose=verbose,
            quiet=quiet,
            cleanup=cleanup,
            exit_on_error=exit_on_error,
            log_file=log_file,
            disable_log_file=disable_log_file,
            log_level=log_level,
        )

        # Set up unified logging system (file + console)
        file_logger, error_collector = init_logging(
            log_file=log_file,
            disable_file=disable_log_file,
            log_level=log_level,
            console_level="DEBUG" if verbose else "INFO",
            quiet=quiet,
            verbose=verbose,
            cli_args=cli_args,
            host=host,
        )

        # Set log_file_path for error handling compatibility
        from gerrit_clone.file_logging import get_default_log_path

        log_file_path = log_file if log_file else get_default_log_path(host)

        # Log version to file in GitHub Actions environment (file only, no console)
        if _is_github_actions_context():
            try:
                file_logger.debug("gerrit-clone version %s", __version__)
            except Exception:
                file_logger.warning("Version information not available")

        # Parse discovery method
        try:
            discovery_method_enum = DiscoveryMethod(discovery_method.lower())
        except ValueError:
            console = Console()
            console.print(
                Panel(
                    Text(
                        f"Invalid discovery method '{discovery_method}'\nMust be one of: ssh, http, both",
                        style="bold red",
                    ),
                    title="Configuration Error",
                    border_style="red",
                )
            )
            raise typer.Exit(ExitCode.CONFIGURATION_ERROR)

        # Load and validate configuration
        try:
            config = load_config(
                host=host,
                port=port,
                base_url=base_url,
                ssh_user=ssh_user,
                ssh_identity_file=ssh_identity_file,
                path_prefix=path_prefix,
                skip_archived=skip_archived,
                allow_nested_git=allow_nested_git,
                nested_protection=nested_protection,
                move_conflicting=move_conflicting,
                threads=threads,
                depth=depth,
                branch=branch,
                use_https=use_https,
                keep_remote_protocol=keep_remote_protocol,
                strict_host_checking=strict_host_checking,
                clone_timeout=clone_timeout,
                retry_attempts=retry_attempts,
                retry_base_delay=retry_base_delay,
                retry_factor=retry_factor,
                retry_max_delay=retry_max_delay,
                manifest_filename=manifest_filename,
                config_file=config_file,
                verbose=verbose,
                quiet=quiet,
                include_projects=include_project,
                ssh_debug=ssh_debug,
                exit_on_error=exit_on_error,
                discovery_method=discovery_method_enum,
            )
        except ConfigurationError as e:
            if file_logger:
                file_logger.error("Configuration error: %s", str(e))
            if error_collector and log_file_path:
                error_collector.write_summary_to_file(log_file_path)
            console = Console()
            console.print(
                Panel(
                    Text(str(e), style="bold red"),
                    title="Configuration Error",
                    border_style="red",
                )
            )
            raise typer.Exit(ExitCode.CONFIGURATION_ERROR)

        # Show startup banner if not quiet
        if not quiet:
            _show_startup_banner(console, config)

        # Execute clone operation with Rich status integration
        try:
            batch_result = clone_repositories(config)
        except DiscoveryError as e:
            console = Console()
            console.print(
                Panel(
                    Text(
                        f"{e.message}\n{e.details}" if e.details else str(e.message),
                        style="bold red",
                    ),
                    title="Discovery Error",
                    border_style="red",
                )
            )
            raise typer.Exit(ExitCode.DISCOVERY_ERROR)

        # Show final results summary using Rich
        if not quiet:
            show_final_results(
                console, batch_result, str(log_file_path) if log_file_path else None
            )

        # Show error summary if there were issues
        if error_collector and not quiet:
            errors = [
                record.message
                for record in error_collector.errors + error_collector.critical_errors
            ]
            warnings = [record.message for record in error_collector.warnings]
            if errors or warnings:
                show_error_summary(console, errors, warnings)

        # Determine exit code based on results
        if batch_result.failed_count > 0:
            if file_logger:
                file_logger.debug(
                    "Clone completed with %d failures", batch_result.failed_count
                )
            exit_code = int(ExitCode.CLONE_ERROR)
        else:
            if file_logger:
                file_logger.debug("Clone completed successfully")
            exit_code = int(ExitCode.SUCCESS)

        # Optional cleanup
        if cleanup:
            from shutil import rmtree

            try:
                if file_logger:
                    file_logger.debug(
                        "Cleanup enabled - removing cloned directory: %s",
                        config.path_prefix,
                    )
                console.print(
                    f"[yellow]🧹 Cleanup enabled - removing cloned directory: {config.path_prefix}[/yellow]"
                )
                rmtree(config.path_prefix, ignore_errors=True)
                if file_logger:
                    file_logger.debug("Cleanup completed successfully")
                console.print(f"[green]Cleanup complete.[/green]")
            except Exception as e:
                if file_logger:
                    file_logger.debug("Cleanup failed: %s", str(e))
                console.print(f"[red]Cleanup failed:[/red] {e}")

        # Close file logging and write summary
        if error_collector and log_file_path:
            error_collector.write_summary_to_file(log_file_path)

        if exit_code != 0:
            raise typer.Exit(exit_code)
        return

    except KeyboardInterrupt:
        if file_logger:
            file_logger.warning("Operation cancelled by user (KeyboardInterrupt)")
        if error_collector and log_file_path:
            error_collector.write_summary_to_file(log_file_path)
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(int(ExitCode.INTERRUPT)) from None
    except typer.Exit:
        # Re-raise typer.Exit exceptions without catching them as generic exceptions
        if error_collector and log_file_path:
            error_collector.write_summary_to_file(log_file_path)
        raise
    except Exception as e:
        import traceback

        # Get the crash context from the traceback
        tb = traceback.extract_tb(e.__traceback__)
        crash_context = "unknown"
        crash_file = "unknown"
        crash_line = 0

        if tb:
            # Get the last frame (where the crash occurred)
            last_frame = tb[-1]
            crash_file = last_frame.filename
            crash_line = last_frame.lineno or 0
            crash_context = (
                f"{last_frame.name}() at {crash_file.split('/')[-1]}:{crash_line}"
            )

        if file_logger:
            file_logger.critical(
                "Tool crashed in %s: %s", crash_context, str(e), exc_info=True
            )
        if error_collector:
            error_collector.add_critical_error(
                f"Tool crashed: {type(e).__name__}: {str(e)}",
                context=f"function: {crash_context}",
                exception=e,
            )
        if error_collector and log_file_path:
            error_collector.write_summary_to_file(log_file_path)

        # Use Rich status system for crash display
        handle_crash_display(console, e, str(log_file_path) if log_file_path else None)

        if verbose:
            console.print_exception()
        raise typer.Exit(ExitCode.GENERAL_ERROR) from None


def _show_startup_banner(console: Console, config: Any) -> None:
    """Show startup banner with configuration summary."""
    # Show version first
    console.print(f"🏷️ [bold]gerrit-clone[/bold] version [cyan]{__version__}[/cyan]")
    console.print()

    # Create summary text
    lines = [
        f"Host: [cyan]{config.host}:{config.effective_port} [{config.protocol}][/cyan]",
        f"Output: [cyan]{config.path_prefix}[/cyan]",
        f"Threads: [cyan]{config.effective_threads}[/cyan]",
    ]

    if config.ssh_user:
        lines.append(f"SSH User: [cyan]{config.ssh_user}[/cyan]")

    if config.ssh_identity_file:
        lines.append(f"SSH Identity: [cyan]{config.ssh_identity_file}[/cyan]")

    if config.depth:
        lines.append(f"Depth: [cyan]{config.depth}[/cyan]")

    if config.branch:
        lines.append(f"Branch: [cyan]{config.branch}[/cyan]")

    lines.extend(
        [
            f"Discovery Method: [cyan]{str(getattr(config, 'discovery_method', DiscoveryMethod.SSH).value).upper()}[/cyan]",
            f"Skip Archived: [cyan]{config.skip_archived}[/cyan]",
            f"Allow Nested Git: [cyan]{getattr(config, 'allow_nested_git', False)}[/cyan]",
            f"Nested Protection: [cyan]{getattr(config, 'nested_protection', False)}[/cyan]",
            f"Move Conflicting: [cyan]{getattr(config, 'move_conflicting', True)}[/cyan]",
            f"Strict Host Check: [cyan]{config.strict_host_checking}[/cyan]",
            f"Include Filter: [cyan]{', '.join(config.include_projects) if getattr(config, 'include_projects', []) else '—'}[/cyan]",
            f"SSH Debug: [cyan]{getattr(config, 'ssh_debug', False)}[/cyan]",
            f"Exit on Error: [cyan]{getattr(config, 'exit_on_error', False)}[/cyan]",
        ]
    )

    summary_text = Text.from_markup("\n".join(lines))

    panel = Panel(
        summary_text,
        title="[bold]Gerrit Clone Configuration[/bold]",
        border_style="blue",
        padding=(1, 2),
    )

    console.print(panel)
    console.print()


@app.command(name="config")
def show_config(
    host: str | None = typer.Option(
        None,
        "--host",
        help="Gerrit server hostname",
        envvar="GERRIT_HOST",
    ),
    config_file: Path | None = typer.Option(
        None,
        "--config-file",
        "-c",
        help="Configuration file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Show effective configuration from all sources.

    This command shows the configuration that would be used for clone operations,
    including values from environment variables, config files, and defaults.
    """
    console = Console()

    try:
        # Load configuration (allowing missing host for config display)
        if host is None:
            host = "example.gerrit.org"  # Placeholder for config display

        config = load_config(host=host, config_file=config_file)

        # Display configuration
        config_lines = [
            f"Host: [cyan]{config.host}:{config.effective_port} [{config.protocol}][/cyan]",
            f"Base URL: [cyan]{config.base_url}[/cyan]",
            f"SSH User: [cyan]{config.ssh_user or 'default'}[/cyan]",
            f"SSH Identity: [cyan]{config.ssh_identity_file or 'default'}[/cyan]",
            f"Path Prefix: [cyan]{config.path_prefix}[/cyan]",
            f"Protocol: [cyan]{config.protocol}[/cyan]",
            f"Skip Archived: [cyan]{config.skip_archived}[/cyan]",
            f"Allow Nested Git: [cyan]{getattr(config, 'allow_nested_git', True)}[/cyan]",
            f"Nested Protection: [cyan]{getattr(config, 'nested_protection', True)}[/cyan]",
            f"Move Conflicting: [cyan]{getattr(config, 'move_conflicting', True)}[/cyan]",
            f"Threads: [cyan]{config.effective_threads}[/cyan]",
            f"Clone Timeout: [cyan]{config.clone_timeout}s[/cyan]",
            f"Strict Host Check: [cyan]{config.strict_host_checking}[/cyan]",
            "",
            f"Retry Max Attempts: [cyan]{config.retry_policy.max_attempts}[/cyan]",
            f"Retry Base Delay: [cyan]{config.retry_policy.base_delay}s[/cyan]",
            f"Retry Factor: [cyan]{config.retry_policy.factor}[/cyan]",
            f"Retry Max Delay: [cyan]{config.retry_policy.max_delay}s[/cyan]",
            "",
            f"Manifest File: [cyan]{config.manifest_filename}[/cyan]",
        ]

        if config.depth:
            config_lines.insert(-3, f"Clone Depth: [cyan]{config.depth}[/cyan]")

        if config.branch:
            config_lines.insert(-3, f"Clone Branch: [cyan]{config.branch}[/cyan]")

        config_text = Text.from_markup("\n".join(config_lines))

        panel = Panel(
            config_text,
            title="[bold]Effective Configuration[/bold]",
            border_style="green",
            padding=(1, 2),
        )

        console.print(panel)

    except ConfigurationError as e:
        console = Console()
        console.print(
            Panel(
                Text(str(e), style="bold red"),
                title="Configuration Error",
                border_style="red",
            )
        )
        raise typer.Exit(ExitCode.CONFIGURATION_ERROR)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(ExitCode.GENERAL_ERROR) from None


if __name__ == "__main__":
    app()
