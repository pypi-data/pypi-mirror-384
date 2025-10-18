"""CLI interface for Atlo."""

from pathlib import Path
from typing import Optional

import typer

from atlo import __version__
from atlo.config import load_atlo_config
from atlo.init_template import DEFAULT_CONFIG_TEMPLATE, create_interactive_config
from atlo.parser import find_atlantis_yaml, parse_atlantis_yaml
from atlo.utils import (
    check_atlantis_yaml_exists,
    console,
    create_projects_table,
    print_banner,
    print_command_menu,
    print_error,
    print_info,
    print_success,
)
from atlo.workflow import WorkflowRunner, get_workflow_steps


def complete_project_dir(incomplete: str):
    """Autocomplete project directories from atlantis.yaml."""
    try:
        atlantis_yaml_path = find_atlantis_yaml()
        if atlantis_yaml_path:
            atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
            projects = atlantis_config.list_projects()
            for project in projects:
                project_dir = project.get("dir", "")
                if project_dir.startswith(incomplete):
                    yield project_dir
    except Exception:
        pass


def complete_workspace(incomplete: str):
    """Autocomplete workspace names from atlantis.yaml."""
    try:
        atlantis_yaml_path = find_atlantis_yaml()
        if atlantis_yaml_path:
            atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
            projects = atlantis_config.list_projects()
            workspaces = set()
            for project in projects:
                workspace = project.get("workspace")
                if workspace:
                    workspaces.add(workspace)
            for workspace in sorted(workspaces):
                if workspace.startswith(incomplete):
                    yield workspace
    except Exception:
        pass


def complete_workflow(incomplete: str):
    """Autocomplete workflow names from atlantis.yaml."""
    try:
        atlantis_yaml_path = find_atlantis_yaml()
        if atlantis_yaml_path:
            atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
            workflows = atlantis_config.workflows
            for workflow_name in workflows.keys():
                if workflow_name.startswith(incomplete):
                    yield workflow_name
    except Exception:
        pass


app = typer.Typer(
    name="atlo",
    help="Run Atlantis workflows locally",
    add_completion=True,
)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
):
    """Atlo - Run Atlantis workflows locally."""
    if version:
        console.print(f"atlo version {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_banner()
        atlantis_yaml_found = check_atlantis_yaml_exists()
        print_command_menu(atlantis_yaml_found=atlantis_yaml_found)


@app.command()
def plan(
    directory: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (e.g., terraform/api)",
        autocompletion=complete_project_dir,
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Terraform workspace (e.g., stage, prod)",
        autocompletion=complete_workspace,
    ),
    workflow: str = typer.Option(
        "default",
        "--workflow",
        help="Workflow name to use",
        autocompletion=complete_workflow,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug output",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show commands without executing them",
    ),
    force_init: bool = typer.Option(
        False,
        "--force-init",
        help="Force terraform init even if already initialized",
    ),
    base_branch: Optional[str] = typer.Option(
        None,
        "--base-branch",
        help="Base branch to compare against (auto-detect if not specified)",
    ),
    all_projects: bool = typer.Option(
        False,
        "--all",
        help="Plan all projects (ignore git changes)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show full terraform output for each project",
    ),
    parallel: Optional[int] = typer.Option(
        None,
        "--parallel",
        help="Max parallel projects (1-10, overrides config)",
        min=1,
        max=10,
    ),
    filter_patterns: Optional[list[str]] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Only run projects matching glob pattern (can specify multiple)",
    ),
    exclude_patterns: Optional[list[str]] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Exclude projects matching glob pattern (can specify multiple)",
    ),
):
    """Run a Terraform plan using Atlantis workflow configuration.

    When run without --dir, automatically detects changed projects based on git diff.

    Examples:

        atlo plan
        # Auto-detect changed projects

        atlo plan --all
        # Plan all projects

        atlo plan --filter "envs/prod/*"
        # Only run production projects

        atlo plan --all --filter "envs/*/core" --exclude "envs/test/*"
        # All core projects except test

        atlo plan --base-branch develop
        # Compare against develop branch

        atlo plan --dir terraform/api --workspace stage
        # Manual mode - plan specific project

        atlo plan --verbose --parallel 4
        # Auto-detect with full output, 4 parallel workers
    """
    print_banner()

    # Find and parse atlantis.yaml
    atlantis_yaml_path = find_atlantis_yaml()

    if atlantis_yaml_path is None:
        print_error("Could not find atlantis.yaml in current directory or parent directories")
        console.print(
            "\n[yellow]Tip:[/yellow] Make sure you're running atlo from within "
            "a repository that has an atlantis.yaml file.\n"
        )
        raise typer.Exit(code=1)

    if debug:
        print_info(f"Found atlantis.yaml at: {atlantis_yaml_path}")

    try:
        atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
    except Exception as e:
        print_error(f"Failed to parse atlantis.yaml: {str(e)}")
        raise typer.Exit(code=1)

    # Load atlo config
    atlo_config = load_atlo_config()

    # Check if we should run in auto-detection mode or manual mode
    if directory:
        # Manual mode - run single project
        _run_single_project(
            atlantis_config=atlantis_config,
            atlo_config=atlo_config,
            directory=directory,
            workspace=workspace,
            workflow=workflow,
            debug=debug,
            dry_run=dry_run,
            force_init=force_init,
        )
    else:
        # Auto-detection mode - find and run multiple projects
        _run_auto_detection(
            atlantis_config=atlantis_config,
            atlo_config=atlo_config,
            workflow=workflow,
            debug=debug,
            dry_run=dry_run,
            force_init=force_init,
            base_branch=base_branch,
            all_projects=all_projects,
            verbose=verbose,
            parallel=parallel,
            filter_patterns=filter_patterns,
            exclude_patterns=exclude_patterns,
        )


def _run_single_project(
    atlantis_config,
    atlo_config,
    directory: str,
    workspace: Optional[str],
    workflow: str,
    debug: bool,
    dry_run: bool,
    force_init: bool,
):
    """Run plan for a single project (manual mode)."""
    # Display run info
    console.print()
    console.print(f"[cyan]Directory:[/cyan] {directory}")
    if workspace:
        console.print(f"[cyan]Workspace:[/cyan] {workspace}")
    console.print(f"[cyan]Workflow:[/cyan] {workflow}")
    console.print()

    # Create and run workflow
    runner = WorkflowRunner(
        atlantis_config=atlantis_config,
        atlo_config=atlo_config,
        debug=debug,
        dry_run=dry_run,
        force_init=force_init,
    )

    success, _output = runner.run_plan(
        directory=directory,
        workspace=workspace,
        workflow_name=workflow,
    )

    if not success:
        raise typer.Exit(code=1)


def _run_auto_detection(
    atlantis_config,
    atlo_config,
    workflow: str,
    debug: bool,
    dry_run: bool,
    force_init: bool,
    base_branch: Optional[str],
    all_projects: bool,
    verbose: bool,
    parallel: Optional[int],
    filter_patterns: Optional[list[str]],
    exclude_patterns: Optional[list[str]],
):
    """Run plan for auto-detected projects."""
    from atlo.detector import ChangeDetector, ProjectMatcher
    from atlo.logs import LogManager
    from atlo.multi_runner import MultiProjectRunner

    # Detect changed files
    console.print()
    if all_projects:
        print_info("Planning all projects (--all flag)")
        changed_files = []
    else:
        with console.status("[bold cyan]Detecting changed files...", spinner="dots"):
            detector = ChangeDetector()
            if base_branch is None:
                base_branch = detector.detect_base_branch()
            changed_files = detector.get_changed_files(base_branch)

        # Show what we're comparing
        console.print(
            f"[dim]Comparing: current branch vs [cyan]{base_branch}[/cyan] "
            "(includes uncommitted + committed changes)[/dim]"
        )

        if changed_files:
            print_success(f"Found {len(changed_files)} changed file(s)")
            if debug:
                for f in changed_files[:10]:  # Show first 10
                    console.print(f"  [dim]- {f}[/dim]")
                if len(changed_files) > 10:
                    console.print(f"  [dim]... and {len(changed_files) - 10} more[/dim]")
        else:
            print_info("No changed files detected")

    # Match projects
    with console.status("[bold cyan]Matching projects...", spinner="dots"):
        matcher = ProjectMatcher(atlantis_config)
        project_matches = matcher.match_projects(
            changed_files, all_projects, filter_patterns, exclude_patterns
        )

    # Show filter info if applied
    if filter_patterns:
        console.print(f"[dim]Filter: {', '.join(filter_patterns)}[/dim]")
    if exclude_patterns:
        console.print(f"[dim]Exclude: {', '.join(exclude_patterns)}[/dim]")

    if not project_matches:
        console.print("\n[yellow]No projects match the changed files[/yellow]")
        if filter_patterns or exclude_patterns:
            console.print("[dim]Tip:[/dim] Check your filter/exclude patterns\n")
        else:
            console.print("\n[dim]Tip:[/dim] Use [cyan]--all[/cyan] to plan all projects\n")
        return

    print_success(f"Detected {len(project_matches)} project(s) requiring planning")
    if debug:
        for pm in project_matches:
            console.print(f"  [dim]- {pm.name} ({pm.reason})[/dim]")
    console.print()

    if dry_run:
        console.print("[bold cyan]Dry run mode - projects that would be planned:[/bold cyan]\n")

        # Show first 10 projects in detail
        for pm in project_matches[:10]:
            console.print(f"  • {pm.name}")
            console.print(f"    [dim]Directory: {pm.dir}[/dim]")
            if pm.workspace:
                console.print(f"    [dim]Workspace: {pm.workspace}[/dim]")
            console.print(f"    [dim]Reason: {pm.reason}[/dim]")
            console.print()

        # If there are more, show a summary
        if len(project_matches) > 10:
            console.print(f"[yellow]... and {len(project_matches) - 10} more projects[/yellow]")
            console.print(
                "\n[dim]Tip:[/dim] Remove [cyan]--dry-run[/cyan] to execute, "
                "or add [cyan]--verbose[/cyan] to see all projects\n"
            )

        return

    # Create log directory
    log_dir = LogManager.create_run_dir()

    # Determine max workers (CLI flag overrides config)
    max_workers = parallel if parallel is not None else atlo_config.max_parallel_projects

    # Create workflow runner
    runner = WorkflowRunner(
        atlantis_config=atlantis_config,
        atlo_config=atlo_config,
        debug=debug,
        dry_run=False,
        force_init=force_init,
    )

    # Run all projects
    multi_runner = MultiProjectRunner(
        workflow_runner=runner,
        project_matches=project_matches,
        log_dir=log_dir,
        workflow_name=workflow,
        max_workers=max_workers,
    )

    manifest = multi_runner.run_all(verbose=verbose)

    # Save manifest
    LogManager.save_manifest(log_dir, manifest)


def _handle_detection_error(error_message: str):
    """Handle errors during detection phase."""
    print_error(f"Detection failed: {error_message}")
    console.print("\n[dim]Tip:[/dim] You can run a specific project manually:")
    console.print("  [cyan]atlo plan --dir terraform/api --workspace stage[/cyan]\n")
    raise typer.Exit(code=1)


@app.command()
def show_workflow(
    name: str = typer.Option(
        "default",
        "--name",
        "-n",
        help="Workflow name to display",
        autocompletion=complete_workflow,
    ),
):
    """Show the configuration for a specific workflow.

    Examples:

        atlo show-workflow

        atlo show-workflow --name custom
    """
    print_banner()

    # Find and parse atlantis.yaml
    atlantis_yaml_path = find_atlantis_yaml()

    if atlantis_yaml_path is None:
        print_error("Could not find atlantis.yaml in current directory or parent directories")
        raise typer.Exit(code=1)

    try:
        atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
    except Exception as e:
        print_error(f"Failed to parse atlantis.yaml: {str(e)}")
        raise typer.Exit(code=1)

    # Get workflow
    workflow = atlantis_config.get_workflow(name)

    if workflow is None:
        print_error(f"Workflow '{name}' not found")
        raise typer.Exit(code=1)

    # Display workflow
    console.print()
    console.print(f"[bold cyan]Workflow:[/bold cyan] {name}\n")

    # Show plan steps
    plan_steps = get_workflow_steps(workflow, "plan")
    if plan_steps:
        console.print("[bold green]Plan steps:[/bold green]")
        for i, step in enumerate(plan_steps, 1):
            console.print(f"  {i}. {step}")

    # Show apply steps if present
    apply_steps = get_workflow_steps(workflow, "apply")
    if apply_steps:
        console.print("\n[bold green]Apply steps:[/bold green]")
        for i, step in enumerate(apply_steps, 1):
            console.print(f"  {i}. {step}")

    console.print()


@app.command()
def list_projects():
    """List all projects defined in atlantis.yaml.

    Examples:

        atlo list-projects
    """
    print_banner()

    # Find and parse atlantis.yaml
    atlantis_yaml_path = find_atlantis_yaml()

    if atlantis_yaml_path is None:
        print_error("Could not find atlantis.yaml in current directory or parent directories")
        raise typer.Exit(code=1)

    try:
        atlantis_config = parse_atlantis_yaml(atlantis_yaml_path)
    except Exception as e:
        print_error(f"Failed to parse atlantis.yaml: {str(e)}")
        raise typer.Exit(code=1)

    # Get projects
    projects = atlantis_config.list_projects()

    if not projects:
        console.print("\n[yellow]No projects defined in atlantis.yaml[/yellow]\n")
        return

    # Display projects table
    console.print()
    table = create_projects_table(projects)
    console.print(table)
    console.print()


@app.command()
def logs(
    project: Optional[str] = typer.Argument(
        None,
        help="Project name to view logs for",
    ),
    all_logs: bool = typer.Option(
        False,
        "--all",
        help="View all logs from the run",
    ),
    failures: bool = typer.Option(
        False,
        "--failures",
        help="View only failed project logs",
    ),
    run: Optional[str] = typer.Option(
        None,
        "--run",
        help="Specific run timestamp to view (e.g., 2025-10-17_14-30-45)",
    ),
):
    """View logs from previous atlo plan runs.

    Examples:

        atlo logs
        # Show summary of last run

        atlo logs envs/dev
        # View specific project log

        atlo logs --failures
        # View only failed project logs

        atlo logs --all
        # View all logs from last run

        atlo logs --run 2025-10-17_14-30-45
        # View specific run
    """
    from atlo.logs import LogManager, LogViewer

    print_banner()

    # Determine which run to view
    if run:
        run_dir = Path(f".atlo/logs/{run}")
        if not run_dir.exists():
            print_error(f"Run directory not found: {run_dir}")
            console.print("\nAvailable runs:")
            for run_path in LogManager.list_runs()[:5]:
                console.print(f"  [cyan]{run_path.name}[/cyan]")
            console.print()
            raise typer.Exit(code=1)
    else:
        run_dir = LogManager.get_latest_run()
        if not run_dir:
            console.print("\n[yellow]No log runs found[/yellow]")
            console.print("\n[dim]Tip:[/dim] Run [cyan]atlo plan[/cyan] to create logs\n")
            return

    # Create viewer
    viewer = LogViewer(run_dir)

    # Display based on options
    if project:
        viewer.view_project(project)
    elif failures:
        viewer.view_failures()
    elif all_logs:
        viewer.view_all()
    else:
        # Default: show summary
        viewer.print_summary()


@app.command()
def init(
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Use default values without prompting",
    ),
):
    """Initialize atlo configuration in the current directory.

    Creates a .atlo.yaml file with sensible defaults and helpful comments.

    Examples:

        atlo init

        atlo init --yes
    """
    print_banner()

    config_path = Path(".atlo.yaml")

    if config_path.exists():
        if not yes:
            overwrite = typer.confirm(
                "\n.atlo.yaml already exists. Overwrite?",
                default=False,
            )
            if not overwrite:
                print_info("Cancelled")
                raise typer.Exit()
        else:
            print_info(".atlo.yaml already exists, overwriting...")

    if yes:
        config_content = DEFAULT_CONFIG_TEMPLATE
        print_info("Using default configuration...")
    else:
        config_content = create_interactive_config()

    config_path.write_text(config_content)
    console.print()
    print_success("Created .atlo.yaml")
    console.print("\nYou can now run: [cyan]atlo plan[/cyan]\n")


@app.command()
def export(
    format: str = typer.Argument(
        ...,
        help="Export format (json, junit, markdown, github)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (defaults to format-specific name)",
    ),
    run: Optional[str] = typer.Option(
        None,
        "--run",
        help="Specific run timestamp to export (e.g., 2025-10-17_14-30-45)",
    ),
):
    """Export run results to various formats.

    Examples:

        atlo export json

        atlo export markdown --output report.md

        atlo export github --run 2025-10-17_14-30-45

        atlo export junit --output test-results.xml
    """
    from atlo.export import ResultExporter
    from atlo.logs import LogManager

    print_banner()

    # Determine which run to export
    if run:
        run_dir = Path(f".atlo/logs/{run}")
        if not run_dir.exists():
            print_error(f"Run directory not found: {run_dir}")
            console.print("\nAvailable runs:")
            for run_path in LogManager.list_runs()[:5]:
                console.print(f"  [cyan]{run_path.name}[/cyan]")
            console.print()
            raise typer.Exit(code=1)
    else:
        run_dir = LogManager.get_latest_run()
        if not run_dir:
            console.print("\n[yellow]No log runs found[/yellow]")
            console.print("\n[dim]Tip:[/dim] Run [cyan]atlo plan[/cyan] first\n")
            raise typer.Exit(code=1)

    # Load manifest
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print_error(f"Manifest not found: {manifest_path}")
        raise typer.Exit(code=1)

    import json

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Determine output path
    if output is None:
        output_map = {
            "json": "atlo-results.json",
            "junit": "atlo-results.xml",
            "markdown": "atlo-results.md",
            "github": "atlo-github-summary.md",
        }
        output = output_map.get(format.lower())
        if output is None:
            print_error(f"Unknown format: {format}")
            console.print("\n[dim]Supported formats:[/dim] json, junit, markdown, github\n")
            raise typer.Exit(code=1)

    output_path = Path(output)

    # Export based on format
    console.print()
    exporter = ResultExporter()

    format_lower = format.lower()
    if format_lower == "json":
        exporter.export_json(manifest, output_path)
    elif format_lower == "junit":
        exporter.export_junit(manifest, output_path)
    elif format_lower == "markdown":
        exporter.export_markdown(manifest, output_path)
    elif format_lower == "github":
        exporter.export_github_actions(manifest, output_path)
    else:
        print_error(f"Unknown format: {format}")
        console.print("\n[dim]Supported formats:[/dim] json, junit, markdown, github\n")
        raise typer.Exit(code=1)

    print_success(f"Exported results to: {output_path}")
    console.print()


@app.command()
def diff(
    run1: Optional[str] = typer.Argument(
        None,
        help="First run timestamp (defaults to second-latest)",
    ),
    run2: Optional[str] = typer.Argument(
        None,
        help="Second run timestamp (defaults to latest)",
    ),
):
    """Compare results between two atlo runs.

    Examples:

        atlo diff
        # Compare last two runs

        atlo diff 2025-10-17_14-30-45 2025-10-17_15-45-30
        # Compare specific runs
    """
    from atlo.diff import RunDiff
    from atlo.logs import LogManager

    print_banner()

    # Get list of runs
    all_runs = LogManager.list_runs()

    if len(all_runs) < 2:
        console.print("\n[yellow]Need at least 2 runs to compare[/yellow]")
        console.print("\n[dim]Tip:[/dim] Run [cyan]atlo plan[/cyan] multiple times\n")
        raise typer.Exit(code=1)

    # Determine which runs to compare
    if run1 is None and run2 is None:
        # Default: compare last two runs
        run1_dir = all_runs[1]
        run2_dir = all_runs[0]
    elif run1 is not None and run2 is None:
        # Compare specified run with latest
        run1_dir = Path(f".atlo/logs/{run1}")
        run2_dir = all_runs[0]
        if not run1_dir.exists():
            print_error(f"Run directory not found: {run1_dir}")
            console.print("\nAvailable runs:")
            for run_path in all_runs[:5]:
                console.print(f"  [cyan]{run_path.name}[/cyan]")
            console.print()
            raise typer.Exit(code=1)
    else:
        # Compare two specified runs
        run1_dir = Path(f".atlo/logs/{run1}")
        run2_dir = Path(f".atlo/logs/{run2}")
        if not run1_dir.exists():
            print_error(f"Run directory not found: {run1_dir}")
            raise typer.Exit(code=1)
        if not run2_dir.exists():
            print_error(f"Run directory not found: {run2_dir}")
            raise typer.Exit(code=1)

    # Load manifests
    manifest1_path = run1_dir / "manifest.json"
    manifest2_path = run2_dir / "manifest.json"

    if not manifest1_path.exists():
        print_error(f"Manifest not found: {manifest1_path}")
        raise typer.Exit(code=1)
    if not manifest2_path.exists():
        print_error(f"Manifest not found: {manifest2_path}")
        raise typer.Exit(code=1)

    import json

    with open(manifest1_path) as f:
        manifest1 = json.load(f)
    with open(manifest2_path) as f:
        manifest2 = json.load(f)

    # Generate and print diff
    diff_viewer = RunDiff(manifest1, manifest2)
    diff_viewer.print_diff()


@app.command()
def completion(
    shell: Optional[str] = typer.Argument(
        None,
        help="Shell type (bash, zsh, fish, powershell)",
    ),
    install: bool = typer.Option(
        False,
        "--install",
        help="Install completion for the specified shell",
    ),
):
    """Show or install shell completion.

    Examples:

        atlo completion bash
        # Show bash completion script

        atlo completion zsh --install
        # Install zsh completion

        atlo completion
        # Show instructions for all shells
    """
    print_banner()

    if shell is None:
        # Show instructions for all shells
        console.print("\n[bold cyan]Shell Completion Setup[/bold cyan]\n")
        console.print("To enable tab completion for atlo, run one of the following:\n")

        console.print("[bold]Bash:[/bold]")
        console.print("  atlo completion bash --install")
        console.print("  [dim]Or add to ~/.bashrc:[/dim]")
        console.print('  [dim]eval "$(atlo completion bash)"[/dim]\n')

        console.print("[bold]Zsh:[/bold]")
        console.print("  atlo completion zsh --install")
        console.print("  [dim]Or add to ~/.zshrc:[/dim]")
        console.print('  [dim]eval "$(atlo completion zsh)"[/dim]\n')

        console.print("[bold]Fish:[/bold]")
        console.print("  atlo completion fish --install")
        console.print("  [dim]Or add to ~/.config/fish/config.fish:[/dim]")
        console.print("  [dim]atlo completion fish | source[/dim]\n")

        console.print("[bold]PowerShell:[/bold]")
        console.print("  atlo completion powershell --install")
        console.print("  [dim]Or add to PowerShell profile[/dim]\n")

        return

    # Validate shell
    valid_shells = ["bash", "zsh", "fish", "powershell"]
    shell_lower = shell.lower()
    if shell_lower not in valid_shells:
        print_error(f"Unknown shell: {shell}")
        console.print(f"\n[dim]Valid shells:[/dim] {', '.join(valid_shells)}\n")
        raise typer.Exit(code=1)

    if install:
        # Install completion
        import subprocess

        console.print(f"\nInstalling {shell} completion...\n")

        try:
            # Use typer's built-in completion installation
            result = subprocess.run(
                [
                    "typer",
                    "atlo.cli:app",
                    "utils",
                    "completion",
                    "install",
                    "--shell",
                    shell_lower,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print_success(f"Installed {shell} completion")
                console.print(
                    "\n[dim]Restart your shell or source your config file to activate[/dim]\n"
                )
            else:
                # Fallback: show manual instructions
                print_error("Automatic installation failed")
                console.print("\n[yellow]Manual setup:[/yellow]\n")
                console.print(f"Add this to your {shell} config file:\n")
                console.print(f'  eval "$(atlo completion {shell})"\n')

        except FileNotFoundError:
            # typer CLI not available, show script
            print_error("Automatic installation not available")
            console.print("\n[yellow]Manual setup:[/yellow]\n")
            console.print(f"Add this to your {shell} config file:\n")
            console.print(f'  eval "$(atlo completion {shell})"\n')
    else:
        # Show completion script
        import subprocess

        try:
            result = subprocess.run(
                ["typer", "atlo.cli:app", "utils", "completion", "show", "--shell", shell_lower],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(result.stdout)
            else:
                print_error("Failed to generate completion script")
                raise typer.Exit(code=1)
        except FileNotFoundError:
            print_error("Completion generation not available")
            console.print("\n[dim]Tip:[/dim] Install with: [cyan]pip install typer-cli[/cyan]\n")
            raise typer.Exit(code=1)


@app.command()
def version():
    """Show the version of Atlo.

    Examples:

        atlo version
    """
    print_banner()
    console.print(f"\n[bold cyan]Version:[/bold cyan] {__version__}\n")


if __name__ == "__main__":
    app()
