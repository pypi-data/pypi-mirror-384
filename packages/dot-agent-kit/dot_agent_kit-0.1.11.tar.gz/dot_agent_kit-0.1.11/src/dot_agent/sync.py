import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dot_agent import list_available_files, read_resource_file
from dot_agent.config import DotAgentConfig


@dataclass(frozen=True, slots=True)
class FileSyncResult:
    changed: bool
    message: str
    diff: str | None = None


SyncStatus = Literal["up-to-date", "missing", "different", "excluded", "unavailable"]


def generate_diff(file_path: str, old_content: str, new_content: str) -> str:
    """Return a unified diff between old and new representations."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    from_file = f"a/{file_path}"
    to_file = f"b/{file_path}"

    diff_lines = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_file,
        tofile=to_file,
        lineterm="",
    )

    return "\n".join(diff_lines)


def sync_file(
    agent_dir: Path,
    relative_path: str,
    *,
    force: bool,
    dry_run: bool,
    available_resources: set[str],
) -> FileSyncResult:
    """Sync a single resource file into the .agent directory."""
    if relative_path not in available_resources:
        message = f"Unavailable resource: {relative_path}"
        return FileSyncResult(changed=False, message=message)

    package_content = read_resource_file(relative_path)
    local_path = agent_dir / relative_path

    if not local_path.exists():
        message = f"Would create {relative_path}" if dry_run else f"Created {relative_path}"
        if not dry_run:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(package_content, encoding="utf-8")
        return FileSyncResult(changed=True, message=message)

    local_content = local_path.read_text(encoding="utf-8")
    if local_content == package_content:
        return FileSyncResult(changed=False, message=f"Up-to-date: {relative_path}")

    diff = generate_diff(relative_path, local_content, package_content)
    if dry_run:
        return FileSyncResult(changed=True, message=f"Would update {relative_path}", diff=diff)

    if not force:
        # We still update automatically but keep the diff so the CLI can surface it.
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(package_content, encoding="utf-8")
        return FileSyncResult(
            changed=True,
            message=f"Updated {relative_path}",
            diff=diff,
        )

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(package_content, encoding="utf-8")
    return FileSyncResult(changed=True, message=f"Updated {relative_path}")


def _expand_managed_files(
    managed_files: tuple[str, ...],
    available_resources: set[str],
) -> list[str]:
    """Expand directory patterns in managed files to actual file paths."""
    expanded: list[str] = []
    for pattern in managed_files:
        if pattern.endswith("/"):
            # Directory pattern - expand to all matching files
            prefix = pattern
            for resource in sorted(available_resources):
                if resource.startswith(prefix):
                    expanded.append(resource)
        else:
            # Specific file path
            expanded.append(pattern)
    return expanded


def sync_all_files(
    agent_dir: Path,
    config: DotAgentConfig,
    *,
    force: bool,
    dry_run: bool,
) -> dict[str, FileSyncResult]:
    """Sync all managed files defined by the configuration."""
    results: dict[str, FileSyncResult] = {}

    available_resources = set(list_available_files())
    expanded_files = _expand_managed_files(config.managed_files, available_resources)

    for file_path in expanded_files:
        if file_path in config.exclude:
            results[file_path] = FileSyncResult(
                changed=False,
                message=f"Excluded: {file_path}",
            )
            continue

        results[file_path] = sync_file(
            agent_dir,
            file_path,
            force=force,
            dry_run=dry_run,
            available_resources=available_resources,
        )

    return results


def detect_status(agent_dir: Path, relative_path: str, available_resources: set[str]) -> SyncStatus:
    """Return the state of a managed file relative to packaged content."""
    if relative_path not in available_resources:
        return "unavailable"

    local_path = agent_dir / relative_path
    if not local_path.exists():
        return "missing"

    package_content = read_resource_file(relative_path)
    local_content = local_path.read_text(encoding="utf-8")
    if local_content == package_content:
        return "up-to-date"

    return "different"


def collect_statuses(agent_dir: Path, config: DotAgentConfig) -> dict[str, SyncStatus]:
    """Return the sync status for every managed file."""
    statuses: dict[str, SyncStatus] = {}
    available_resources = set(list_available_files())
    expanded_files = _expand_managed_files(config.managed_files, available_resources)

    for file_path in expanded_files:
        if file_path in config.exclude:
            statuses[file_path] = "excluded"
            continue

        statuses[file_path] = detect_status(agent_dir, file_path, available_resources)

    return statuses
