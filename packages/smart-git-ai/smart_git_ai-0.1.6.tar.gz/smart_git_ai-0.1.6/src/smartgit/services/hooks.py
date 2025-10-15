"""Git hooks management."""

import os
import stat
from typing import List

from smartgit.core.exceptions import HookInstallationError
from smartgit.core.repository import GitRepository


class HookType:
    """Supported git hook types."""

    PREPARE_COMMIT_MSG = "prepare-commit-msg"
    POST_COMMIT = "post-commit"
    PRE_PUSH = "pre-push"


class HookManager:
    """
    Manages git hooks installation and removal.

    Handles installing custom hooks while preserving existing ones.
    """

    def __init__(self, repository: GitRepository) -> None:
        """
        Initialize hook manager.

        Args:
            repository: Git repository instance.
        """
        self.repository = repository
        self.hooks_dir = self.repository.root_path / ".git" / "hooks"

    def install_hook(self, hook_type: str, force: bool = False) -> None:
        """
        Install a git hook.

        Args:
            hook_type: Type of hook to install (e.g., "prepare-commit-msg").
            force: If True, overwrite existing hook.

        Raises:
            HookInstallationError: If installation fails.
        """
        if not self.hooks_dir.exists():
            raise HookInstallationError(
                "Hooks directory not found",
                details=str(self.hooks_dir),
            )

        hook_path = self.hooks_dir / hook_type
        backup_path = self.hooks_dir / f"{hook_type}.backup"

        # Check if hook already exists
        if hook_path.exists() and not force:
            # Check if it's already our hook
            content = hook_path.read_text()
            if "smartgit" in content:
                return

            # Backup existing hook
            if not backup_path.exists():
                hook_path.rename(backup_path)

        # Get hook template
        template = self._get_hook_template(hook_type)

        try:
            # Write hook
            hook_path.write_text(template)

            # Make executable
            current_permissions = os.stat(hook_path).st_mode
            os.chmod(
                hook_path,
                current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            )

        except Exception as e:
            # Restore backup if installation failed
            if backup_path.exists():
                backup_path.rename(hook_path)

            raise HookInstallationError(
                f"Failed to install {hook_type} hook",
                details=str(e),
            ) from e

    def uninstall_hook(self, hook_type: str, restore_backup: bool = True) -> None:
        """
        Uninstall a git hook.

        Args:
            hook_type: Type of hook to uninstall.
            restore_backup: If True, restore backed up hook.

        Raises:
            HookInstallationError: If uninstallation fails.
        """
        hook_path = self.hooks_dir / hook_type
        backup_path = self.hooks_dir / f"{hook_type}.backup"

        if not hook_path.exists():
            return

        try:
            # Check if it's our hook
            content = hook_path.read_text()
            if "smartgit" not in content:
                raise HookInstallationError(
                    f"Hook {hook_type} is not a smartgit hook",
                    details="Use --force to remove anyway",
                )

            # Remove hook
            hook_path.unlink()

            # Restore backup if requested
            if restore_backup and backup_path.exists():
                backup_path.rename(hook_path)

        except Exception as e:
            raise HookInstallationError(
                f"Failed to uninstall {hook_type} hook",
                details=str(e),
            ) from e

    def is_hook_installed(self, hook_type: str) -> bool:
        """
        Check if a git hook is installed.

        Args:
            hook_type: Type of hook to check.

        Returns:
            True if hook is installed, False otherwise.
        """
        hook_path = self.hooks_dir / hook_type

        if not hook_path.exists():
            return False

        # Check if it's our hook
        try:
            content = hook_path.read_text()
            return "smartgit" in content
        except Exception:
            return False

    def list_installed_hooks(self) -> List[str]:
        """
        List all installed smartgit hooks.

        Returns:
            List of installed hook names.
        """
        installed: List[str] = []

        if not self.hooks_dir.exists():
            return installed

        for hook_file in self.hooks_dir.iterdir():
            if hook_file.is_file() and not hook_file.name.endswith(".backup"):
                try:
                    content = hook_file.read_text()
                    if "smartgit" in content:
                        installed.append(hook_file.name)
                except Exception:
                    continue

        return installed

    def _get_hook_template(self, hook_type: str) -> str:
        """
        Get hook template content.

        Args:
            hook_type: Type of hook.

        Returns:
            Hook script content.

        Raises:
            HookInstallationError: If template not found.
        """
        # Try to load from package templates
        try:
            import importlib.resources as pkg_resources

            template_path = pkg_resources.files("smartgit.hooks") / f"{hook_type}.sh"
            if hasattr(template_path, "read_text"):
                return template_path.read_text()
        except Exception:
            pass

        # Fallback templates
        templates = {
            HookType.PREPARE_COMMIT_MSG: """#!/bin/bash
# Git AI prepare-commit-msg hook

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2
SHA1=$3

# Only run for regular commits (not merges, amends, etc.)
if [ -z "$COMMIT_SOURCE" ]; then
    if command -v smartgit &> /dev/null; then
        smartgit generate --hook --output "$COMMIT_MSG_FILE"
    else
        echo "Warning: smartgit command not found" >&2
    fi
fi
""",
        }

        template = templates.get(hook_type)
        if not template:
            raise HookInstallationError(
                f"No template found for hook: {hook_type}",
                details=f"Supported hooks: {', '.join(templates.keys())}",
            )

        return template
