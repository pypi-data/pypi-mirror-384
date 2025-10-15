"""TinySemVer - A tiny but mighty Semantic Versioning tool.

This package provides automated semantic versioning for Git repositories
following Conventional Commits. It can generate changelogs and release notes
with or without LLM assistance.

Example:
    >>> from tinysemver import bump
    >>> new_version = bump(
    ...     path=".",
    ...     dry_run=True,
    ...     verbose=True,
    ...     version_file="VERSION",
    ...     changelog_file="CHANGELOG.md"
    ... )
"""

from tinysemver.tinysemver import (
    # Main function
    bump,
    # Version utilities
    parse_version,
    bump_version,
    # Commit utilities
    commit_starts_with_verb,
    normalize_verbs,
    group_commits,
    convert_commits_to_message,
    # Git utilities
    get_last_tag,
    get_commits_since_tag,
    get_diff_for_commit,
    # File utilities
    patch_with_regex,
    # Tag creation
    create_tag,
    # Types
    SemVer,
    BumpType,
    PathLike,
    Commit,
    ChangeDiff,
    # Exceptions
    NoNewCommitsError,
)

__version__ = "2.1.1"
__all__ = [
    # Main function
    "bump",
    # Version utilities
    "parse_version",
    "bump_version",
    # Commit utilities
    "commit_starts_with_verb",
    "normalize_verbs",
    "group_commits",
    "convert_commits_to_message",
    # Git utilities
    "get_last_tag",
    "get_commits_since_tag",
    "get_diff_for_commit",
    # File utilities
    "patch_with_regex",
    # Tag creation
    "create_tag",
    # Types
    "SemVer",
    "BumpType",
    "PathLike",
    "Commit",
    "ChangeDiff",
    # Exceptions
    "NoNewCommitsError",
]
