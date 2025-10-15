"""Main CLI entry point using Click."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table

from smartgit.core.exceptions import GitAIError, GitRepositoryError, NoChangesError
from smartgit.core.repository import GitRepository
from smartgit.services.commit_analyzer import CommitAnalyzer
from smartgit.services.commit_generator import CommitMessageGenerator
from smartgit.services.config import get_config_manager
from smartgit.services.hooks import HookManager, HookType
from smartgit.utils.git_helpers import GitUtilities

console = Console()


@click.group()
@click.version_option(package_name="smartgit")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    Git AI - AI-powered Git assistant with smart commit messages.

    Generate intelligent commit messages, manage git hooks, and access
    helpful git utilities to improve your development workflow.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("-c", "--context", help="Additional context about the changes")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Generate message without committing",
)
@click.option(
    "--hook",
    is_flag=True,
    hidden=True,
    help="Running from git hook",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for commit message (for hooks)",
)
@click.option(
    "--edit/--no-edit",
    default=True,
    help="Open editor to review message",
)
@click.pass_context
def generate(
    ctx: click.Context,
    context: Optional[str],
    dry_run: bool,
    hook: bool,
    output: Optional[str],
    edit: bool,
) -> None:
    """Generate an AI commit message for staged changes."""
    try:
        with console.status("[bold green]Analyzing changes..."):
            repo = GitRepository()
            generator = CommitMessageGenerator(repo)

            commit_message = generator.generate_from_staged(context=context)

        # Format the message
        formatted = commit_message.format(style=generator.config.commit_style)

        if hook and output:
            # Write to file for git hook
            Path(output).write_text(formatted)
            console.print("[green]✓[/green] Generated commit message")
            return

        # Display the message
        console.print("\n[bold cyan]Generated Commit Message:[/bold cyan]")
        console.print(Panel(Syntax(formatted, "text", theme="monokai"), expand=False))

        if commit_message.confidence_score < 0.7:
            console.print(
                f"[yellow]⚠[/yellow]  Low confidence: {commit_message.confidence_score:.0%}"
            )

        if dry_run:
            console.print("\n[dim]Dry run mode - not creating commit[/dim]")
            return

        # Confirm commit
        if edit or Confirm.ask("\nCreate commit with this message?", default=True):
            if edit:
                # Let git handle the editing via EDITOR
                temp_file = Path(".git/COMMIT_EDITMSG")
                temp_file.write_text(formatted)
                console.print("[dim]Opening editor...[/dim]")

                # User will edit in their EDITOR
                import subprocess

                editor = subprocess.run(
                    ["git", "commit", "-e", "-F", str(temp_file)],
                    check=False,
                )
                if editor.returncode == 0:
                    console.print("[green]✓[/green] Commit created")
                else:
                    console.print("[red]✗[/red] Commit cancelled")
            else:
                repo.commit(formatted)
                console.print("[green]✓[/green] Commit created")
        else:
            console.print("[yellow]Commit cancelled[/yellow]")

    except NoChangesError:
        console.print("[yellow]No staged changes to commit[/yellow]")
        console.print("Run: [cyan]git add <files>[/cyan] to stage changes")
        sys.exit(1)
    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if ctx.obj.get("verbose") and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        sys.exit(1)


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing hooks",
)
@click.option(
    "--with-cache-warming",
    is_flag=True,
    help="Also install post-commit hook for automatic cache warming",
)
def install(force: bool, with_cache_warming: bool) -> None:
    """Install git hooks for automatic commit message generation."""
    try:
        repo = GitRepository()
        hook_manager = HookManager(repo)

        with console.status("[bold green]Installing hooks..."):
            hook_manager.install_hook(HookType.PREPARE_COMMIT_MSG, force=force)

            if with_cache_warming:
                hook_manager.install_hook(HookType.POST_COMMIT, force=force)

        console.print("[green]✓[/green] Git hooks installed successfully")
        console.print("\nThe prepare-commit-msg hook will now generate AI commit messages")
        console.print("when you run: [cyan]git commit[/cyan] (without -m)")

        if with_cache_warming:
            console.print("\nThe post-commit hook will warm the cache in background")
            console.print("This makes [cyan]smartgit rescue[/cyan] commands instant!")

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)
    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@cli.command()
@click.option(
    "--restore",
    is_flag=True,
    help="Restore backed up hooks",
)
def uninstall(restore: bool) -> None:
    """Uninstall git hooks."""
    try:
        repo = GitRepository()
        hook_manager = HookManager(repo)

        # Uninstall all smartgit hooks
        uninstalled = []

        if hook_manager.is_hook_installed(HookType.PREPARE_COMMIT_MSG):
            hook_manager.uninstall_hook(HookType.PREPARE_COMMIT_MSG, restore_backup=restore)
            uninstalled.append("prepare-commit-msg")

        if hook_manager.is_hook_installed(HookType.POST_COMMIT):
            hook_manager.uninstall_hook(HookType.POST_COMMIT, restore_backup=restore)
            uninstalled.append("post-commit")

        if uninstalled:
            console.print(f"[green]✓[/green] Uninstalled hooks: {', '.join(uninstalled)}")
        else:
            console.print("[dim]No smartgit hooks found to uninstall[/dim]")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@cli.command()
def status() -> None:
    """Show git status and AI configuration."""
    try:
        repo = GitRepository()
        git_status = repo.get_status()
        repo_info = repo.get_repository_info()
        config = get_config_manager().config
        hook_manager = HookManager(repo)

        # Repository info
        console.print("\n[bold cyan]Repository:[/bold cyan]")
        console.print(f"  Path: {repo_info.root_path}")
        console.print(f"  Branch: {repo_info.current_branch}")
        if repo_info.remote_url:
            console.print(f"  Remote: {repo_info.remote_url}")

        # Git status
        console.print("\n[bold cyan]Status:[/bold cyan]")
        if git_status.is_clean:
            console.print("  [green]✓ Working tree clean[/green]")
        else:
            if git_status.staged_files:
                console.print(f"  Staged files: {len(git_status.staged_files)}")
            if git_status.unstaged_files:
                console.print(f"  Unstaged files: {len(git_status.unstaged_files)}")
            if git_status.untracked_files:
                console.print(f"  Untracked files: {len(git_status.untracked_files)}")

        # Hooks status
        console.print("\n[bold cyan]Hooks:[/bold cyan]")
        installed = hook_manager.list_installed_hooks()
        if installed:
            console.print(f"  [green]✓ Installed:[/green] {', '.join(installed)}")
        else:
            console.print("  [yellow]Not installed[/yellow]")

        # AI configuration
        console.print("\n[bold cyan]AI Configuration:[/bold cyan]")
        console.print(f"  Provider: {config.provider}")
        console.print(f"  Model: {config.model or 'default'}")
        console.print(f"  Style: {config.commit_style}")

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)


@cli.group()
def config() -> None:
    """Manage smartgit configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "is_global", is_flag=True, help="Set global config")
def config_set(key: str, value: str, is_global: bool) -> None:
    """Set a configuration value."""
    try:
        config_manager = get_config_manager()

        config_updates = {key: value}

        if is_global:
            config_manager.save_user_config(config_updates)
            console.print(f"[green]✓[/green] Set global config: {key} = {value}")
        else:
            config_manager.save_repo_config(config_updates)
            console.print(f"[green]✓[/green] Set repo config: {key} = {value}")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    try:
        config = get_config_manager().config

        table = Table(title="Git AI Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Provider", config.provider)
        table.add_row("Model", config.model or "default")
        table.add_row("Commit Style", config.commit_style)
        table.add_row("Auto Add", str(config.auto_add))
        table.add_row("Hook Enabled", str(config.hook_enabled))
        table.add_row("Max Subject Length", str(config.max_subject_length))

        console.print(table)

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@cli.group()
def cache() -> None:
    """Manage commit analysis cache."""
    pass


@cache.command("stats")
def cache_stats() -> None:
    """Show cache statistics."""
    try:
        from smartgit.cache.manager import get_cache_manager

        repo = GitRepository()
        cache_mgr = get_cache_manager(repo.root_path)

        stats = cache_mgr.get_stats()

        if not stats.get("enabled"):
            console.print("[yellow]Cache is disabled[/yellow]")
            return

        console.print("\n[bold cyan]📊 Cache Statistics[/bold cyan]\n")

        # Memory cache stats
        if "memory" in stats:
            mem_stats = stats["memory"]
            console.print("[bold]Memory Cache (L1):[/bold]")
            console.print(f"  Entries: {mem_stats['total_entries']}/{mem_stats['max_size']}")
            console.print(f"  Usage: {mem_stats['usage_percent']}%")
            console.print(f"  Hit rate: {mem_stats['hit_rate']}%")
            console.print(f"  Hits: {mem_stats['hits']}")
            console.print(f"  Misses: {mem_stats['misses']}")
            console.print(f"  Evictions: {mem_stats['evictions']}")
            console.print()

        # SQLite cache stats
        if "sqlite" in stats:
            sql_stats = stats["sqlite"]
            console.print("[bold]Persistent Cache (SQLite):[/bold]")
            console.print(f"  Total entries: {sql_stats['total_entries']}")
            console.print(f"  Total accesses: {sql_stats['total_accesses']}")
            console.print(f"  Unique repos: {sql_stats['unique_repos']}")
            console.print(f"  Unique commits: {sql_stats['unique_commits']}")
            console.print(f"  Avg accesses per entry: {sql_stats['avg_accesses_per_entry']}")
            console.print(f"  Database size: {sql_stats['db_size_kb']} KB")
            if sql_stats["oldest_entry"]:
                console.print(f"  Oldest entry: {sql_stats['oldest_entry']}")
            if sql_stats["newest_entry"]:
                console.print(f"  Newest entry: {sql_stats['newest_entry']}")
            console.print()

        console.print(f"[dim]Analysis version: {stats['analysis_version']}[/dim]")
        console.print(f"[dim]Repository ID: {stats['repository_id']}[/dim]")

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cache.command("clear")
@click.option(
    "--scope",
    type=click.Choice(["all", "repository", "memory"]),
    default="repository",
    help="Scope of cache to clear",
)
@click.option("--force", is_flag=True, help="Skip confirmation")
def cache_clear(scope: str, force: bool) -> None:
    """Clear cache entries."""
    try:
        from smartgit.cache.manager import get_cache_manager

        repo = GitRepository()
        cache_mgr = get_cache_manager(repo.root_path)

        scope_desc = {
            "all": "all repositories",
            "repository": "this repository",
            "memory": "memory cache only",
        }

        if not force:
            if not Confirm.ask(f"Clear cache for {scope_desc[scope]}?", default=False):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        count = cache_mgr.clear(scope=scope)
        console.print(f"[green]✓[/green] Cleared {count} cache entries")

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cache.command("evict")
@click.option(
    "--days",
    type=int,
    default=30,
    help="Evict entries older than N days",
)
@click.option("--force", is_flag=True, help="Skip confirmation")
def cache_evict(days: int, force: bool) -> None:
    """Evict old cache entries."""
    try:
        from smartgit.cache.manager import get_cache_manager

        repo = GitRepository()
        cache_mgr = get_cache_manager(repo.root_path)

        if not force:
            if not Confirm.ask(f"Evict cache entries older than {days} days?", default=True):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        count = cache_mgr.evict_old(max_age_days=days)
        console.print(f"[green]✓[/green] Evicted {count} old cache entries")

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cache.command("list")
@click.option("--limit", type=int, default=20, help="Maximum entries to show")
def cache_list(limit: int) -> None:
    """List cached entries for this repository."""
    try:
        from smartgit.cache.manager import get_cache_manager

        repo = GitRepository()
        cache_mgr = get_cache_manager(repo.root_path)

        entries = cache_mgr.list_entries(limit=limit)

        if not entries:
            console.print("[dim]No cache entries found[/dim]")
            return

        table = Table(title=f"Cached Entries (showing {len(entries)})")
        table.add_column("Commit", style="cyan", width=8)
        table.add_column("Type", style="dim", width=15)
        table.add_column("Provider", style="yellow", width=12)
        table.add_column("Cached", style="green", width=20)
        table.add_column("Accesses", style="magenta", justify="right")

        for entry in entries:
            table.add_row(
                entry.commit_sha[:7],
                entry.analysis_type,
                entry.provider_type,
                entry.cached_at.strftime("%Y-%m-%d %H:%M"),
                str(entry.access_count),
            )

        console.print(table)

    except GitRepositoryError:
        console.print("[red]✗ Error:[/red] Not a git repository")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cache.command("warm")
@click.option(
    "--commit",
    default="HEAD",
    help="Commit SHA or ref to warm (default: HEAD)",
)
@click.option(
    "--recent",
    type=int,
    help="Warm N recent commits instead of single commit",
)
@click.option(
    "--silent",
    is_flag=True,
    help="Suppress all output (for background operation)",
)
@click.option(
    "--repo",
    type=click.Path(exists=True),
    help="Repository path (default: current directory)",
)
def cache_warm(
    commit: str,
    recent: Optional[int],
    silent: bool,
    repo: Optional[str],
) -> None:
    """
    Warm cache by analyzing commits in background.

    This command pre-populates the cache with commit analysis,
    making subsequent rescue operations instant.
    """
    try:
        from smartgit.services.cache_warmer import (
            warm_cache_for_commit,
            warm_cache_for_recent,
        )

        repo_path = Path(repo) if repo else None

        if recent:
            # Warm recent commits
            count = warm_cache_for_recent(
                count=recent,
                repository_path=repo_path,
                silent=silent,
            )
            if not silent:
                if count > 0:
                    console.print(f"[green]✓[/green] Warmed cache for {count} commits")
                else:
                    console.print("[yellow]No commits to warm[/yellow]")
        else:
            # Warm single commit
            success = warm_cache_for_commit(
                commit_sha=commit,
                repository_path=repo_path,
                silent=silent,
            )
            if not silent:
                if success:
                    console.print(f"[green]✓[/green] Warmed cache for commit {commit}")
                else:
                    console.print(f"[red]✗[/red] Failed to warm cache for {commit}")

    except Exception as e:
        if not silent:
            console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.group()
def utils() -> None:
    """Git utility functions."""
    pass


@cli.group()
def rescue() -> None:
    """Git rescue operations for when you're in trouble."""
    pass


@utils.command("undo")
@click.option(
    "--hard",
    is_flag=True,
    help="Discard changes (default: keep as staged)",
)
def undo_commit(hard: bool) -> None:
    """Undo the last commit."""
    try:
        repo = GitRepository()

        if not Confirm.ask(
            "Undo the last commit?" + (" [red](changes will be lost!)[/red]" if hard else "")
        ):
            return

        repo.undo_last_commit(keep_changes=not hard)
        console.print("[green]✓[/green] Last commit undone")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@utils.command("cleanup")
@click.option("--remote", default="origin", help="Remote name")
def cleanup_branches(remote: str) -> None:
    """Delete local branches that have been merged."""
    try:
        repo = GitRepository()

        deleted = repo.clean_merged_branches(remote=remote)

        if deleted:
            console.print(f"[green]✓[/green] Deleted {len(deleted)} merged branches:")
            for branch in deleted:
                console.print(f"  - {branch}")
        else:
            console.print("[dim]No merged branches to clean up[/dim]")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@utils.command("stale")
@click.option("--days", default=30, help="Days to consider a branch stale")
def find_stale(days: int) -> None:
    """Find stale branches that haven't been updated recently."""
    try:
        repo = GitRepository()
        utils_service = GitUtilities(repo)

        stale = utils_service.find_stale_branches(days=days)

        if stale:
            table = Table(title=f"Branches not updated in {days} days")
            table.add_column("Branch", style="cyan")
            table.add_column("Last Updated", style="yellow")

            for branch in stale:
                last_updated = (
                    branch.last_commit_date.strftime("%Y-%m-%d")
                    if branch.last_commit_date
                    else "Unknown"
                )
                table.add_row(branch.name, last_updated)

            console.print(table)
        else:
            console.print("[dim]No stale branches found[/dim]")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@utils.command("large-files")
@click.option("--size", default=10.0, help="Size threshold in MB")
def find_large(size: float) -> None:
    """Find large files in the repository."""
    try:
        repo = GitRepository()
        utils_service = GitUtilities(repo)

        large = utils_service.find_large_files(size_mb=size)

        if large:
            table = Table(title=f"Files larger than {size} MB")
            table.add_column("File", style="cyan")
            table.add_column("Size (MB)", style="yellow", justify="right")

            for file_path, file_size in large:
                table.add_row(str(file_path), f"{file_size:.2f}")

            console.print(table)
        else:
            console.print(f"[dim]No files larger than {size} MB[/dim]")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@utils.command("suggest-gitignore")
def suggest_gitignore() -> None:
    """Suggest .gitignore entries based on untracked files."""
    try:
        repo = GitRepository()
        utils_service = GitUtilities(repo)

        suggestions = utils_service.suggest_gitignore_entries()

        if suggestions:
            console.print("[bold cyan]Suggested .gitignore entries:[/bold cyan]\n")
            for suggestion in suggestions:
                console.print(f"  {suggestion}")

            if Confirm.ask("\nAdd these to .gitignore?"):
                gitignore = repo.root_path / ".gitignore"
                existing = gitignore.read_text() if gitignore.exists() else ""

                with open(gitignore, "a") as f:
                    if existing and not existing.endswith("\n"):
                        f.write("\n")
                    f.write("\n# Added by smartgit\n")
                    for suggestion in suggestions:
                        f.write(f"{suggestion}\n")

                console.print("[green]✓[/green] Updated .gitignore")
        else:
            console.print("[dim]No suggestions[/dim]")

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        sys.exit(1)


@rescue.command("analyze-history")
@click.option("--max-commits", type=int, default=50, help="Maximum commits to analyze")
@click.option(
    "--branch",
    help="Branch to analyze (default: current branch)",
)
@click.option(
    "--min-quality",
    type=int,
    default=0,
    help="Only show commits with quality below this threshold (0-10)",
)
@click.pass_context
def analyze_commit_history(
    ctx: click.Context, max_commits: int, branch: Optional[str], min_quality: int
) -> None:
    """Analyze commit message quality using AI."""
    try:
        repo = GitRepository()
        config = get_config_manager().config
        analyzer = CommitAnalyzer(repo, config)

        # analyze_history has its own progress bar, no need for console.status
        analyses = analyzer.analyze_history(max_commits=max_commits, branch=branch)

        # Filter by quality if specified
        if min_quality > 0:
            analyses = [a for a in analyses if a.quality_score <= min_quality]

        if not analyses:
            console.print("[green]✓[/green] All commits have good quality!")
            return

        # Get statistics
        stats = analyzer.get_statistics(analyses)

        # Show summary
        console.print("\n[bold cyan]📊 Commit Quality Report[/bold cyan]")
        console.print(f"Analyzed {stats['total']} commits")
        console.print(f"Average quality: [bold]{stats['average_quality']}/10[/bold]")
        console.print()

        # Show category breakdown
        by_cat = stats["by_category"]
        console.print("[bold]By Category:[/bold]")
        if by_cat["excellent"] > 0:
            console.print(f"  [green]✓ Excellent:[/green] {by_cat['excellent']} commits")
        if by_cat["good"] > 0:
            console.print(f"  [blue]• Good:[/blue] {by_cat['good']} commits")
        if by_cat["poor"] > 0:
            console.print(f"  [yellow]⚠ Poor:[/yellow] {by_cat['poor']} commits")
        if by_cat["junk"] > 0:
            console.print(f"  [red]✗ Junk:[/red] {by_cat['junk']} commits")
        console.print()

        # Show detailed table for problematic commits
        problematic = [a for a in analyses if a.quality_score < 7]
        if problematic:
            table = Table(title="Commits Needing Attention", show_lines=True)
            table.add_column("Commit", style="dim", width=8)
            table.add_column("Message", style="cyan", width=30)
            table.add_column("Quality", justify="center", width=8)
            table.add_column("Issues", style="yellow", width=25)
            table.add_column("Suggestion", style="magenta", width=20)

            for analysis in problematic[:20]:  # Limit to first 20
                # Quality indicator
                if analysis.quality_score >= 7:
                    quality_display = f"[green]{analysis.quality_score}/10[/green]"
                elif analysis.quality_score >= 4:
                    quality_display = f"[yellow]{analysis.quality_score}/10[/yellow]"
                else:
                    quality_display = f"[red]{analysis.quality_score}/10[/red]"

                # Truncate message
                msg = (
                    analysis.message[:50] + "..."
                    if len(analysis.message) > 50
                    else analysis.message
                )

                # Format issues
                issues_text = ", ".join(analysis.issues[:2])  # Show first 2 issues
                if len(analysis.issues) > 2:
                    issues_text += f" +{len(analysis.issues) - 2} more"

                table.add_row(
                    analysis.commit_sha[:7],
                    msg,
                    quality_display,
                    issues_text,
                    analysis.suggestion,
                )

            console.print(table)

            if len(problematic) > 20:
                console.print(f"\n[dim]... and {len(problematic) - 20} more commits[/dim]")

        # Show improved messages for worst commits
        worst = sorted(analyses, key=lambda a: a.quality_score)[:5]
        has_improvements = any(a.improved_message for a in worst)

        if has_improvements:
            console.print("\n[bold cyan]💡 AI-Suggested Improvements (Top 5 Worst):[/bold cyan]\n")
            for analysis in worst:
                if analysis.improved_message:
                    console.print(f"[dim]{analysis.commit_sha[:7]}[/dim]")
                    console.print(f"  [red]Old:[/red] {analysis.message}")
                    console.print(f"  [green]New:[/green] {analysis.improved_message}")
                    console.print()

        # Show recommendations
        console.print("[bold cyan]📋 Recommendations:[/bold cyan]")
        if stats["needs_squashing"] > 0:
            console.print(
                f"  • [yellow]{stats['needs_squashing']}[/yellow] junk commits should be squashed"
            )
        if stats["needs_improvement"] > 0:
            console.print(
                f"  • [yellow]{stats['needs_improvement']}[/yellow] commits need better messages"
            )

        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]smartgit rescue improve-messages[/cyan] to fix poor messages")
        console.print(
            "  2. Run [cyan]smartgit rescue squash-junk[/cyan] to consolidate junk commits"
        )
        console.print(
            "  3. Run [cyan]smartgit rescue cleanup-history[/cyan] to do both automatically"
        )

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if ctx.obj.get("verbose") and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        sys.exit(1)


@rescue.command("improve-messages")
@click.option("--max-commits", type=int, default=50, help="Maximum commits to analyze")
@click.option(
    "--min-quality",
    type=int,
    default=7,
    help="Only improve commits with quality below this (0-10)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying them")
@click.option("--no-backup", is_flag=True, help="Skip creating backup branch")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def improve_commit_messages(
    ctx: click.Context,
    max_commits: int,
    min_quality: int,
    dry_run: bool,
    no_backup: bool,
    force: bool,
) -> None:
    """Improve commit messages using AI."""
    try:
        repo = GitRepository()
        config = get_config_manager().config
        analyzer = CommitAnalyzer(repo, config)

        # improve_commit_messages calls analyze_history internally which has its own progress bar
        improvements = analyzer.improve_commit_messages(
            max_commits=max_commits,
            min_quality=min_quality,
            create_backup=False,  # We'll handle backup separately
        )

        if not improvements:
            console.print("[green]✓[/green] All commits already have good quality messages!")
            return

        # Show what will be changed
        console.print(f"\n[bold cyan]📝 Found {len(improvements)} commits to improve[/bold cyan]\n")

        # Show preview table
        table = Table(title="Proposed Improvements", show_lines=True)
        table.add_column("Commit", style="dim", width=8)
        table.add_column("Current Message", style="red", width=35)
        table.add_column("Improved Message", style="green", width=35)

        for sha, new_message in list(improvements.items())[:10]:  # Show first 10
            try:
                commit = repo.repo.commit(sha)
                old_message = commit.message.strip().split("\n")[0]  # First line only

                # Truncate for display
                old_display = old_message[:50] + "..." if len(old_message) > 50 else old_message
                new_display = new_message[:50] + "..." if len(new_message) > 50 else new_message

                table.add_row(
                    sha[:7],
                    old_display,
                    new_display,
                )
            except Exception:
                continue

        console.print(table)

        if len(improvements) > 10:
            console.print(f"\n[dim]... and {len(improvements) - 10} more commits[/dim]")

        console.print("\n[bold yellow]⚠ Warning:[/bold yellow] This will rewrite git history")
        console.print("[dim]All commit SHAs will change[/dim]\n")

        if dry_run:
            console.print("[cyan]Dry run mode - no changes will be made[/cyan]")
            return

        # Confirm
        if not force and not Confirm.ask(
            f"\n[yellow]Rewrite {len(improvements)} commit messages?[/yellow]",
            default=False,
        ):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        # Create backup
        if not no_backup:
            with console.status("Creating backup branch..."):
                backup_name = analyzer.create_backup_branch()
            console.print(f"[green]✓[/green] Created backup branch: {backup_name}")

        # Rewrite messages
        with console.status("Rewriting commit messages (this may take a while)..."):
            analyzer.rewrite_commit_messages(improvements, create_backup=False)

        console.print(f"[green]✓[/green] Successfully improved {len(improvements)} commit messages")

        console.print("\n[bold cyan]Next steps:[/bold cyan]")
        console.print("  1. Review the changes: [cyan]git log --oneline[/cyan]")
        console.print(
            "  2. Force push to remote: [cyan]git push --force-with-lease origin <branch>[/cyan]"
        )
        console.print("  3. Notify team members to re-fetch")
        console.print(
            f"  4. Restore from backup if needed: [cyan]git checkout {backup_name if not no_backup else 'backup-branch'}[/cyan]"
        )

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if ctx.obj.get("verbose") and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        if "git-filter-repo is not installed" in str(e.message):
            console.print("\n[yellow]Install git-filter-repo:[/yellow]")
            console.print("  pip install git-filter-repo")
        sys.exit(1)


@rescue.command("squash-junk")
@click.option("--max-commits", type=int, default=50, help="Maximum commits to analyze")
@click.option(
    "--threshold",
    type=int,
    default=4,
    help="Quality threshold - commits below this are junk (0-10)",
)
@click.option("--dry-run", is_flag=True, help="Preview squash plan without applying")
@click.option("--no-backup", is_flag=True, help="Skip creating backup branch")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def squash_junk_commits_command(
    ctx: click.Context,
    max_commits: int,
    threshold: int,
    dry_run: bool,
    no_backup: bool,
    force: bool,
) -> None:
    """Identify and squash consecutive junk commits."""
    try:
        repo = GitRepository()
        config = get_config_manager().config
        analyzer = CommitAnalyzer(repo, config)

        # squash_junk_commits calls analyze_history internally which has its own progress bar
        squash_result = analyzer.squash_junk_commits(
            max_commits=max_commits,
            junk_threshold=threshold,
            create_backup=False,
        )

        if squash_result["groups_found"] == 0:
            console.print(
                "[green]✓[/green] No consecutive junk commits found. Your history looks clean!"
            )
            return

        # Show squash plan
        plan = squash_result["plan"]
        console.print(
            f"\n[bold cyan]🗑️  Found {squash_result['groups_found']} groups of junk commits "
            f"({squash_result['commits_to_squash']} commits total)[/bold cyan]\n"
        )

        # Show detailed plan
        for idx, group in enumerate(plan, 1):
            console.print(f"[bold]Group {idx}:[/bold] Squash {group['commit_count']} commits")
            console.print(f"  [dim]Commits:[/dim] {', '.join(group['commits'])}")
            console.print("[dim]  Current messages:[/dim]")
            for msg in group["messages"]:
                console.print(f"    • {msg}")
            console.print(f"  [green]→ New message:[/green] {group['squashed_message']}")
            console.print()

        console.print("[bold yellow]⚠ Warning:[/bold yellow] This will rewrite git history")
        console.print("[dim]All commit SHAs after the first squashed commit will change[/dim]\n")

        if dry_run:
            console.print("[cyan]Dry run mode - no changes will be made[/cyan]")
            return

        # Confirm
        if not force:
            total_commits = squash_result["commits_to_squash"]
            final_commits = sum(1 for _ in plan)
            reduction = total_commits - final_commits

            if not Confirm.ask(
                f"\n[yellow]Squash {total_commits} commits into {final_commits} "
                f"(reducing by {reduction} commits)?[/yellow]",
                default=False,
            ):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Create backup
        backup_name = None
        if not no_backup:
            with console.status("Creating backup branch..."):
                backup_name = analyzer.create_backup_branch("backup-before-squash")
            console.print(f"[green]✓[/green] Created backup branch: {backup_name}")

        # Execute squash
        with console.status("Squashing junk commits (this may take a while)..."):
            analyzer.execute_squash_plan(plan, create_backup=False)

        console.print(
            f"[green]✓[/green] Successfully squashed {squash_result['commits_to_squash']} "
            f"junk commits into {len(plan)} meaningful commits"
        )

        console.print("\n[bold cyan]Next steps:[/bold cyan]")
        console.print("  1. Review the changes: [cyan]git log --oneline[/cyan]")
        console.print(
            "  2. Force push to remote: [cyan]git push --force-with-lease origin <branch>[/cyan]"
        )
        console.print("  3. Notify team members to re-fetch")
        if backup_name:
            console.print(
                f"  4. Restore from backup if needed: [cyan]git checkout {backup_name}[/cyan]"
            )

    except GitAIError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if ctx.obj.get("verbose") and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
