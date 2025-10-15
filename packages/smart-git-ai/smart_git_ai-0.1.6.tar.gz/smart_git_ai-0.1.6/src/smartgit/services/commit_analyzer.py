"""Service for analyzing and improving commit messages using AI."""

import os
import shutil
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from git import GitCommandError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from smartgit.cache.manager import get_cache_manager
from smartgit.core.exceptions import GitOperationError
from smartgit.core.repository import GitRepository
from smartgit.providers.factory import ProviderFactory
from smartgit.services.config import SmartGitConfig

if TYPE_CHECKING:
    from smartgit.providers.base import AIProvider


@dataclass
class CommitQuality:
    """Represents the quality analysis of a commit."""

    commit_sha: str
    message: str
    quality_score: int  # 0-10
    category: str  # "excellent", "good", "poor", "junk"
    issues: List[str]  # List of problems found
    suggestion: str  # What to do about it
    improved_message: Optional[str] = None  # AI-generated better message


class CommitAnalyzer:
    """
    Service for analyzing commit message quality using AI.

    Uses Claude AI to evaluate commit messages and provide suggestions
    for improvement or consolidation.
    """

    def __init__(self, repository: GitRepository, config: SmartGitConfig) -> None:
        """Initialize commit analyzer."""
        self.repository = repository
        self.config = config

        # Only create provider if API key is available
        self.provider: Optional[AIProvider]
        try:
            if config.api_key:
                self.provider = ProviderFactory.create(
                    config.provider,
                    config.api_key,
                    config.model,
                )
                self.provider_type = config.provider
            else:
                self.provider = None
                self.provider_type = "fallback"
        except Exception:
            self.provider = None
            self.provider_type = "fallback"

        # Initialize cache manager
        cache_enabled = getattr(config, "cache_enabled", True)
        cache_max_workers = getattr(config, "cache_max_workers", 10)
        cache_memory_size = getattr(config, "cache_memory_size", 100)
        cache_use_memory = getattr(config, "cache_use_memory", True)

        self.cache_manager = get_cache_manager(
            repository.root_path,
            enabled=cache_enabled,
            memory_size=cache_memory_size,
            use_memory_cache=cache_use_memory,
        )

        # Performance settings
        self.max_workers = cache_max_workers
        self.rate_limit_delay = getattr(config, "cache_rate_limit_delay", 0.1)

        # Thread safety for git operations
        self._git_lock = threading.Lock()

    def _should_skip_commit(self, message: str) -> bool:
        """
        Check if a commit should be skipped from rescue operations.

        Commits with "release:" prefix should not be analyzed, improved, or squashed
        as they represent release commits.

        Args:
            message: Commit message to check.

        Returns:
            True if commit should be skipped, False otherwise.
        """
        return message.strip().lower().startswith("release:")

    def analyze_commit(self, commit_sha: str, use_cache: bool = True) -> CommitQuality:
        """
        Analyze a single commit's message quality.

        Args:
            commit_sha: SHA of the commit to analyze.
            use_cache: Whether to use cache (default: True).

        Returns:
            CommitQuality analysis.
        """
        try:
            # Try cache first
            if use_cache:
                cached_data = self.cache_manager.get_commit_quality(
                    commit_sha=commit_sha,
                    provider_type=self.provider_type,
                )
                if cached_data:
                    return self._deserialize_commit_quality(cached_data)

            # Cache miss - do analysis
            commit = self.repository.repo.commit(commit_sha)
            message = commit.message.strip()
            diff = self._get_commit_diff(commit_sha)

            # Use AI to analyze
            analysis = self._ai_analyze_commit(message, diff, commit_sha)

            # Store in cache
            if use_cache:
                self.cache_manager.put_commit_quality(
                    commit_sha=commit_sha,
                    provider_type=self.provider_type,
                    data=self._serialize_commit_quality(analysis),
                )

            return analysis

        except GitCommandError as e:
            raise GitOperationError(
                f"Failed to analyze commit {commit_sha}",
                details=str(e),
            ) from e

    def analyze_history(
        self,
        max_commits: int = 50,
        branch: Optional[str] = None,
        use_cache: bool = True,
        show_progress: bool = True,
    ) -> List[CommitQuality]:
        """
        Analyze multiple commits in git history (optimized with caching and parallelization).

        Args:
            max_commits: Maximum number of commits to analyze.
            branch: Branch to analyze (None = current branch).
            use_cache: Whether to use cache (default: True).
            show_progress: Whether to show progress bar (default: True).

        Returns:
            List of CommitQuality analyses (in chronological order, newest first).
        """
        try:
            # Step 1: Get commits
            if branch:
                commits = list(self.repository.repo.iter_commits(branch, max_count=max_commits))
            else:
                commits = list(self.repository.repo.iter_commits(max_count=max_commits))

            if not commits:
                return []

            # Filter out release commits
            commits = [c for c in commits if not self._should_skip_commit(c.message)]

            if not commits:
                return []

            # Step 2: Separate cached vs uncached
            cached_results = {}
            uncached_commits = []

            if use_cache:
                for commit in commits:
                    cached_data = self.cache_manager.get_commit_quality(
                        commit_sha=commit.hexsha,
                        provider_type=self.provider_type,
                    )

                    if cached_data:
                        cached_results[commit.hexsha] = self._deserialize_commit_quality(
                            cached_data
                        )
                    else:
                        uncached_commits.append(commit)
            else:
                uncached_commits = commits

            # Show cache statistics
            if show_progress and use_cache:
                console = Console()

                cached_count = len(cached_results)
                uncached_count = len(uncached_commits)

                if cached_count > 0:
                    console.print(
                        f"[green]Found {cached_count} commit(s) in cache (skipping AI analysis)[/green]"
                    )

                if uncached_count > 0:
                    console.print(f"[cyan]Analyzing {uncached_count} commit(s) with AI...[/cyan]")

            # Step 3: Analyze uncached commits in parallel
            if uncached_commits:
                uncached_results = self._analyze_parallel(
                    uncached_commits,
                    use_cache=use_cache,
                    show_progress=show_progress
                    and len(uncached_commits) > 5,  # Only show for 5+ commits
                )

                # Merge results
                for sha, result in uncached_results.items():
                    cached_results[sha] = result

            # Step 4: Return in original order (newest first)
            return [cached_results[c.hexsha] for c in commits]

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to analyze git history",
                details=str(e),
            ) from e

    def _get_commit_diff(self, commit_sha: str, max_lines: int = 100) -> str:
        """Get diff for a commit, limited to max_lines (thread-safe)."""
        try:
            # Lock git operations to avoid thread-safety issues
            with self._git_lock:
                diff_output = self.repository.git.show(
                    commit_sha,
                    "--pretty=",
                    "--unified=3",
                )

            # Limit diff size
            lines = diff_output.split("\n")
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                truncated_count = len(diff_output.split("\n")) - max_lines
                lines.append(f"\n... (truncated, {truncated_count} more lines)")

            return "\n".join(lines)

        except GitCommandError:
            return "[Unable to retrieve diff]"

    def _ai_analyze_commit(
        self, message: str, diff: str, commit_sha: str = "unknown"
    ) -> CommitQuality:
        """Use AI to analyze commit message quality."""
        prompt = f"""You are a git commit message expert. Analyze this commit and rate its quality.

COMMIT MESSAGE:
{message}

CHANGES (diff):
{diff}

Evaluate the commit message based on:
1. Clarity: Is it clear what changed and why?
2. Convention: Does it follow Conventional Commits format (type(scope): description)?
3. Completeness: Does it describe the actual changes in the diff?
4. Usefulness: Would this help someone understand the change later?

Common issues to check for:
- Vague messages: "fix", "update", "changes", "wip", "test", "temp"
- Missing type prefix: feat/fix/docs/style/refactor/test/chore
- Too generic: "fix bug", "update code"
- Doesn't match the diff content

Respond in this EXACT format:
QUALITY: [score 0-10]
CATEGORY: [excellent/good/poor/junk]
ISSUES: [comma-separated list of issues, or "none"]
SUGGESTION: [one-line suggestion: "Keep as is" / "Should improve" / "Should squash" / "Should rewrite"]
IMPROVED: [if score < 7, provide an improved conventional commit message based on the diff, otherwise write "N/A"]

Example responses:
QUALITY: 2
CATEGORY: junk
ISSUES: vague message, no context, doesn't follow convention
SUGGESTION: Should squash with nearby commits
IMPROVED: feat(auth): implement JWT token validation middleware

QUALITY: 9
CATEGORY: excellent
ISSUES: none
SUGGESTION: Keep as is
IMPROVED: N/A"""

        # Check if AI provider is available
        if not self.provider:
            return self._fallback_analysis(message, commit_sha)

        try:
            # Call AI provider
            response = self.provider.generate_text(prompt)

            # Parse response
            return self._parse_ai_response(message, response, commit_sha)

        except Exception:
            # Fallback to basic analysis if AI fails
            return self._fallback_analysis(message, commit_sha)

    def _parse_ai_response(
        self, original_message: str, ai_response: str, commit_sha: str = "unknown"
    ) -> CommitQuality:
        """Parse AI response into CommitQuality object."""
        lines = ai_response.strip().split("\n")
        data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower()] = value.strip()

        # Extract values with defaults
        quality_score = int(data.get("quality", "5"))
        category = data.get("category", "poor")
        issues_str = data.get("issues", "unknown")
        suggestion = data.get("suggestion", "Should review")
        improved = data.get("improved", "N/A")

        # Parse issues
        if issues_str.lower() == "none":
            issues = []
        else:
            issues = [issue.strip() for issue in issues_str.split(",")]

        return CommitQuality(
            commit_sha=commit_sha,
            message=original_message,
            quality_score=quality_score,
            category=category,
            issues=issues,
            suggestion=suggestion,
            improved_message=improved if improved != "N/A" else None,
        )

    def _fallback_analysis(self, message: str, commit_sha: str = "unknown") -> CommitQuality:
        """Fallback analysis without AI (pattern-based)."""
        message_lower = message.lower().strip()

        # Junk patterns
        junk_patterns = ["wip", "test", "temp", "tmp", "fix", "update", "changes", "cleanup"]
        is_junk = any(pattern in message_lower for pattern in junk_patterns)

        # Check for conventional commit format
        has_type = any(
            message.startswith(t)
            for t in [
                "feat:",
                "fix:",
                "docs:",
                "style:",
                "refactor:",
                "test:",
                "chore:",
                "perf:",
                "ci:",
                "build:",
            ]
        )

        # Determine quality
        if is_junk:
            quality_score = 2
            category = "junk"
            suggestion = "Should squash with nearby commits"
        elif not has_type:
            quality_score = 4
            category = "poor"
            suggestion = "Should improve with conventional format"
        elif len(message) < 10:
            quality_score = 5
            category = "poor"
            suggestion = "Should add more detail"
        else:
            quality_score = 7
            category = "good"
            suggestion = "Could be slightly improved"

        issues = []
        if is_junk:
            issues.append("vague or placeholder message")
        if not has_type:
            issues.append("missing conventional commit type")
        if len(message) < 10:
            issues.append("message too short")

        return CommitQuality(
            commit_sha=commit_sha,
            message=message,
            quality_score=quality_score,
            category=category,
            issues=issues if issues else ["none"],
            suggestion=suggestion,
            improved_message=None,
        )

    def get_statistics(self, analyses: List[CommitQuality]) -> dict:
        """Get statistics from a list of commit analyses."""
        if not analyses:
            return {}

        total = len(analyses)
        avg_quality = sum(a.quality_score for a in analyses) / total

        by_category = {
            "excellent": len([a for a in analyses if a.category == "excellent"]),
            "good": len([a for a in analyses if a.category == "good"]),
            "poor": len([a for a in analyses if a.category == "poor"]),
            "junk": len([a for a in analyses if a.category == "junk"]),
        }

        needs_improvement = len([a for a in analyses if a.quality_score < 7])
        needs_squashing = len([a for a in analyses if a.category == "junk"])

        return {
            "total": total,
            "average_quality": round(avg_quality, 1),
            "by_category": by_category,
            "needs_improvement": needs_improvement,
            "needs_squashing": needs_squashing,
        }

    def _analyze_parallel(
        self,
        commits: List,
        use_cache: bool = True,
        show_progress: bool = True,
    ) -> Dict[str, CommitQuality]:
        """
        Analyze multiple commits in parallel.

        Args:
            commits: List of git commit objects to analyze.
            use_cache: Whether to use cache.
            show_progress: Whether to show progress bar.

        Returns:
            Dict mapping commit SHA to CommitQuality.
        """
        results = {}

        # Create progress bar
        progress = (
            Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            )
            if show_progress
            else None
        )

        try:
            if progress:
                task = progress.add_task("[cyan]Analyzing commits...", total=len(commits))
                progress.start()

            # Process in batches to respect rate limits
            batch_size = self.max_workers

            for i in range(0, len(commits), batch_size):
                batch = commits[i : i + batch_size]

                # Parallel processing within batch
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks
                    future_to_commit = {
                        executor.submit(
                            self._analyze_single_threadsafe, commit.hexsha, use_cache
                        ): commit
                        for commit in batch
                    }

                    # Collect results as they complete
                    for future in as_completed(future_to_commit):
                        commit = future_to_commit[future]
                        try:
                            result = future.result()
                            results[commit.hexsha] = result

                            if progress:
                                progress.update(task, advance=1)

                        except Exception as e:
                            if progress:
                                # Use progress console to avoid overlap
                                progress.console.print(
                                    f"[red]Error analyzing {commit.hexsha[:7]}: {e}[/red]"
                                )
                            # Create a fallback analysis
                            results[commit.hexsha] = self._fallback_analysis(
                                commit.message, commit.hexsha
                            )
                            if progress:
                                progress.update(task, advance=1)

                # Rate limiting between batches
                if i + batch_size < len(commits):
                    time.sleep(self.rate_limit_delay)

        finally:
            if progress:
                progress.stop()

        return results

    def _analyze_single_threadsafe(self, commit_sha: str, use_cache: bool = True) -> CommitQuality:
        """
        Analyze a single commit (thread-safe version for parallel execution).

        Args:
            commit_sha: Commit SHA to analyze.
            use_cache: Whether to use cache.

        Returns:
            CommitQuality analysis.
        """
        # This is called from multiple threads, so protect git operations
        with self._git_lock:
            commit = self.repository.repo.commit(commit_sha)
            message = commit.message.strip()

        # Try AI analysis first
        if self.provider:
            try:
                diff = self._get_commit_diff(commit_sha)
                analysis = self._ai_analyze_commit(message, diff, commit_sha)

                # Cache the result
                if use_cache:
                    self.cache_manager.put_commit_quality(
                        commit_sha=commit_sha,
                        provider_type=self.provider_type,
                        data=self._serialize_commit_quality(analysis),
                    )

                return analysis
            except Exception:
                # Fallback if AI fails
                pass

        # Pattern-based fallback
        analysis = self._fallback_analysis(message, commit_sha)

        # Cache the fallback result too
        if use_cache:
            self.cache_manager.put_commit_quality(
                commit_sha=commit_sha,
                provider_type=self.provider_type,
                data=self._serialize_commit_quality(analysis),
            )

        return analysis

    def _serialize_commit_quality(self, quality: CommitQuality) -> Dict[str, Any]:
        """Convert CommitQuality to dict for caching."""
        return asdict(quality)

    def _deserialize_commit_quality(self, data: Dict[str, Any]) -> CommitQuality:
        """Convert dict back to CommitQuality."""
        return CommitQuality(**data)

    def generate_improved_message(self, commit_sha: str) -> str:
        """
        Generate an improved commit message for a specific commit.

        Args:
            commit_sha: SHA of commit to improve.

        Returns:
            Improved commit message.
        """
        try:
            commit = self.repository.repo.commit(commit_sha)
            message = commit.message.strip()
            diff = self._get_commit_diff(commit_sha)

            # Check if AI provider is available
            if not self.provider:
                return self._basic_improve_message(message)

            # Ask AI for improvement
            prompt = f"""You are a git commit message expert. Rewrite this commit message following Conventional Commits format.

CURRENT MESSAGE:
{message}

ACTUAL CHANGES (diff):
{diff}

Generate a SINGLE LINE commit message that:
1. Follows format: type(scope): description
2. Uses correct type: feat/fix/docs/style/refactor/test/chore/perf/ci/build
3. Accurately describes what the diff shows
4. Is concise but informative (max 72 chars for subject)
5. Uses imperative mood ("add" not "added")

If changes warrant a body, add it after a blank line.

Return ONLY the improved commit message, nothing else."""

            improved = self.provider.generate_text(prompt)
            return improved.strip()

        except Exception:
            # Fallback: try to improve with pattern-based approach
            return self._basic_improve_message(message)

    def _basic_improve_message(self, message: str) -> str:
        """Basic message improvement without AI."""
        # Remove common junk prefixes
        message = message.strip()
        for prefix in ["WIP:", "wip:", "test:", "temp:", "tmp:"]:
            if message.lower().startswith(prefix.lower()):
                message = message[len(prefix) :].strip()

        # If still too generic, try to add context
        if message.lower() in ["fix", "update", "changes", "cleanup"]:
            return f"chore: {message}"

        # If doesn't have type, add one
        if not any(
            message.startswith(t)
            for t in [
                "feat:",
                "fix:",
                "docs:",
                "style:",
                "refactor:",
                "test:",
                "chore:",
                "perf:",
                "ci:",
                "build:",
            ]
        ):
            return f"chore: {message}"

        return message

    def improve_commit_messages(
        self,
        max_commits: int = 50,
        min_quality: int = 7,
        create_backup: bool = True,
    ) -> Dict[str, str]:
        """
        Generate improved messages for commits below quality threshold.

        Args:
            max_commits: Maximum commits to analyze.
            min_quality: Only improve commits with quality below this (0-10).
            create_backup: Whether to create backup branch.

        Returns:
            Dict mapping commit SHA to improved message.
        """
        # Analyze history
        analyses = self.analyze_history(max_commits=max_commits)

        # Filter commits needing improvement (excluding release commits)
        to_improve = [
            a
            for a in analyses
            if a.quality_score < min_quality and not self._should_skip_commit(a.message)
        ]

        # Generate improved messages
        improvements = {}
        for analysis in to_improve:
            # Use AI-generated improvement if available
            if analysis.improved_message:
                improvements[analysis.commit_sha] = analysis.improved_message
            else:
                # Generate new improvement
                improved = self.generate_improved_message(analysis.commit_sha)
                improvements[analysis.commit_sha] = improved

        return improvements

    def create_backup_branch(self, suffix: str = "backup-before-improve") -> str:
        """Create backup branch before dangerous operations."""
        try:
            current_branch = self.repository.repo.active_branch.name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_name = f"{current_branch}-{suffix}-{timestamp}"

            # Create backup branch
            self.repository.git.branch(backup_name)

            return backup_name

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to create backup branch",
                details=str(e),
            ) from e

    def rewrite_commit_messages(
        self,
        commit_message_map: Dict[str, str],
        create_backup: bool = True,
    ) -> bool:
        """
        Rewrite commit messages in git history.

        Args:
            commit_message_map: Dict mapping commit SHA to new message.
            create_backup: Whether to create backup branch first.

        Returns:
            True if successful.

        Raises:
            GitOperationError: If rewriting fails.
        """
        # Check if git-filter-repo is available
        if not shutil.which("git-filter-repo"):
            raise GitOperationError(
                "git-filter-repo is not installed",
                details="Install with: pip install git-filter-repo",
            )

        if create_backup:
            self.create_backup_branch()

        try:
            # Create temporary file with message mappings
            # Format: old_sha==>new_message
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                for sha, new_message in commit_message_map.items():
                    # Escape newlines in message for filter-repo
                    escaped_message = new_message.replace("\n", "\\n")
                    f.write(f"{sha}==>{escaped_message}\n")
                mapping_file = f.name

            # Use git filter-repo to rewrite messages
            subprocess.run(
                [
                    "git-filter-repo",
                    "--commit-callback",
                    f"""
import sys
mappings = {{}}
with open('{mapping_file}', 'r') as f:
    for line in f:
        if '==>' in line:
            sha, msg = line.strip().split('==>', 1)
            mappings[sha] = msg.replace('\\\\n', '\\n')

old_sha = commit.original_id.decode('utf-8')
if old_sha in mappings:
    commit.message = mappings[old_sha].encode('utf-8')
""",
                    "--force",
                ],
                cwd=self.repository.root_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Clean up temp file
            Path(mapping_file).unlink()
            return True

        except subprocess.CalledProcessError as e:
            raise GitOperationError(
                "Failed to rewrite commit messages",
                details=e.stderr or str(e),
            ) from e

    def identify_junk_groups(
        self,
        max_commits: int = 50,
        junk_threshold: int = 4,
    ) -> List[List[CommitQuality]]:
        """
        Identify groups of consecutive junk commits.

        Args:
            max_commits: Maximum commits to analyze.
            junk_threshold: Commits with quality below this are considered junk.

        Returns:
            List of groups, where each group is a list of consecutive junk commits.
        """
        # Analyze history
        analyses = self.analyze_history(max_commits=max_commits)

        # Group consecutive junk commits
        groups = []
        current_group: List[CommitQuality] = []

        for analysis in reversed(analyses):  # Process from oldest to newest
            # Skip release commits
            if self._should_skip_commit(analysis.message):
                # End of junk sequence if we hit a release commit
                if current_group:
                    groups.append(current_group)
                    current_group = []
                continue

            if analysis.quality_score < junk_threshold or analysis.category == "junk":
                current_group.append(analysis)
            else:
                # End of junk sequence
                if current_group:
                    groups.append(current_group)
                    current_group = []

        # Don't forget the last group
        if current_group:
            groups.append(current_group)

        return groups

    def generate_squashed_message(self, commits: List[CommitQuality]) -> str:
        """
        Generate a meaningful message for a group of junk commits.

        Args:
            commits: List of junk commits to squash.

        Returns:
            Generated commit message.
        """
        if not commits:
            return "chore: consolidate changes"

        # Collect all diffs
        combined_diff = []
        for commit in commits:
            try:
                diff = self._get_commit_diff(commit.commit_sha, max_lines=50)
                combined_diff.append(diff)
            except Exception:
                pass

        full_diff = "\n\n".join(combined_diff)

        # Use AI to generate meaningful message
        if self.provider:
            try:
                prompt = f"""You are a git commit message expert. These {len(commits)} junk commits need to be squashed into one:

ORIGINAL MESSAGES:
{chr(10).join(f"- {c.message}" for c in commits)}

COMBINED CHANGES (diff):
{full_diff[:2000]}  # Limit to avoid token overflow

Generate a SINGLE LINE commit message that:
1. Follows format: type(scope): description
2. Accurately describes what all these changes accomplish together
3. Is concise but informative (max 72 chars)
4. Uses imperative mood

Return ONLY the improved commit message, nothing else."""

                improved = self.provider.generate_text(prompt)
                return improved.strip()
            except Exception:
                pass

        # Fallback: create basic message
        if len(commits) == 1:
            return self._basic_improve_message(commits[0].message)
        else:
            # Multiple commits - create a generic message
            return f"chore: consolidate {len(commits)} commits"

    def squash_junk_commits(
        self,
        max_commits: int = 50,
        junk_threshold: int = 4,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """
        Identify and squash consecutive junk commits.

        Args:
            max_commits: Maximum commits to analyze.
            junk_threshold: Commits with quality below this are junk.
            create_backup: Whether to create backup branch.

        Returns:
            Dict with squash plan details.

        Raises:
            GitOperationError: If squashing fails.
        """
        # Identify junk groups
        junk_groups = self.identify_junk_groups(max_commits, junk_threshold)

        if not junk_groups:
            return {
                "groups_found": 0,
                "commits_to_squash": 0,
                "plan": [],
            }

        # Generate squash plan
        plan = []
        total_commits_to_squash = 0

        for group in junk_groups:
            if len(group) < 2:
                # Skip single commits - not worth squashing alone
                continue

            total_commits_to_squash += len(group)
            suggested_message = self.generate_squashed_message(group)

            plan.append(
                {
                    "commits": [c.commit_sha[:7] for c in group],
                    "messages": [c.message for c in group],
                    "squashed_message": suggested_message,
                    "commit_count": len(group),
                }
            )

        return {
            "groups_found": len(plan),
            "commits_to_squash": total_commits_to_squash,
            "plan": plan,
        }

    def execute_squash_plan(
        self,
        plan: List[Dict],
        create_backup: bool = True,
    ) -> bool:
        """
        Execute a squash plan by squashing each group sequentially.

        Args:
            plan: Squash plan from squash_junk_commits.
            create_backup: Whether to create backup branch.

        Returns:
            True if successful.

        Raises:
            GitOperationError: If squashing fails.
        """
        if not plan:
            return True

        if create_backup:
            self.create_backup_branch("backup-before-squash")

        try:
            # Build a set of commits to squash for quick lookup
            # Format: {short_sha: (group_idx, position_in_group, new_message)}
            squash_map = {}
            for group_idx, group in enumerate(plan):
                for pos, short_sha in enumerate(group["commits"]):
                    squash_map[short_sha] = (group_idx, pos, group["squashed_message"])

            # Get all commits that need to be in the rebase
            # Start from parent of the first junk commit
            first_junk_sha = plan[0]["commits"][0]

            # Get full SHA for first commit
            full_first_sha = self.repository.git.rev_parse(first_junk_sha)

            # Get parent
            try:
                parent_sha = self.repository.git.rev_parse(f"{full_first_sha}^")
            except GitCommandError:
                # No parent - this is root commit, can't squash
                raise GitOperationError(
                    "Cannot squash commits - first commit is root commit",
                    details="Root commits cannot be squashed",
                ) from None

            # Get all commits from parent to HEAD
            commits_list = list(self.repository.repo.iter_commits(f"{parent_sha}..HEAD"))
            commits_list.reverse()  # Oldest first

            # Build rebase todo script
            todo_lines = []
            for commit in commits_list:
                short_sha = commit.hexsha[:7]

                if short_sha in squash_map:
                    group_idx, pos, new_message = squash_map[short_sha]

                    if pos == 0:
                        # First commit in group - pick it
                        todo_lines.append(f"pick {short_sha} {commit.summary}\n")
                        # Add exec to change the message after squashing
                        escaped_msg = new_message.replace("'", "'\"'\"'")
                        todo_lines.append(f"exec git commit --amend -m '{escaped_msg}'\n")
                    else:
                        # Subsequent commits in group - fixup into first
                        todo_lines.append(f"fixup {short_sha} {commit.summary}\n")
                else:
                    # Not a junk commit - keep as is
                    todo_lines.append(f"pick {short_sha} {commit.summary}\n")

            # Write todo file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.writelines(todo_lines)
                todo_file = f.name

            # Run git rebase with the todo file
            env = {**os.environ, "GIT_SEQUENCE_EDITOR": f"cat {todo_file} >"}

            result = subprocess.run(
                ["git", "rebase", "-i", parent_sha],
                cwd=self.repository.root_path,
                env=env,
                capture_output=True,
                text=True,
            )

            # Clean up
            Path(todo_file).unlink(missing_ok=True)

            if result.returncode != 0:
                raise GitOperationError(
                    "Failed to squash commits", details=result.stderr or result.stdout
                )

            return True

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to squash commits",
                details=str(e),
            ) from e
