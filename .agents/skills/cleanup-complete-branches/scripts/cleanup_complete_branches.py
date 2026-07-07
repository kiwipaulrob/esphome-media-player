#!/usr/bin/env python3
"""Safely remove completed local worktrees, local branches, and origin branches."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROTECTED_BRANCHES = {
    "main",
    "master",
    "develop",
    "dev",
    "release",
    "staging",
    "production",
}


@dataclass
class Completion:
    complete: bool
    reason: str


@dataclass
class Worktree:
    path: Path
    branch: str | None
    dirty: bool = False


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=check,
    )


def output(args: list[str], *, cwd: Path | None = None, check: bool = True) -> str:
    result = run(args, cwd=cwd, check=check)
    return result.stdout.strip()


def repo_root() -> Path:
    return Path(output(["git", "rev-parse", "--show-toplevel"])).resolve()


def current_branch(root: Path) -> str | None:
    branch = output(["git", "branch", "--show-current"], cwd=root)
    return branch or None


def local_branches(root: Path) -> set[str]:
    text = output(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"],
        cwd=root,
    )
    return {line.strip() for line in text.splitlines() if line.strip()}


def remote_branches(root: Path) -> set[str]:
    text = output(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"],
        cwd=root,
    )
    branches = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "origin/HEAD":
            continue
        if line.startswith("origin/"):
            branches.add(line.removeprefix("origin/"))
    return branches


def parse_worktrees(root: Path) -> list[Worktree]:
    text = output(["git", "worktree", "list", "--porcelain"], cwd=root)
    worktrees: list[Worktree] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("worktree"):
            return
        branch_ref = current.get("branch")
        branch = None
        if branch_ref and branch_ref.startswith("refs/heads/"):
            branch = branch_ref.removeprefix("refs/heads/")
        worktrees.append(Worktree(Path(current["worktree"]), branch))

    for line in text.splitlines():
        if not line:
            flush()
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    flush()

    for worktree in worktrees:
        status = output(["git", "status", "--porcelain"], cwd=worktree.path)
        worktree.dirty = bool(status)
    return worktrees


def is_ancestor(root: Path, older_ref: str, newer_ref: str) -> bool:
    result = run(
        ["git", "merge-base", "--is-ancestor", older_ref, newer_ref],
        cwd=root,
        check=False,
    )
    return result.returncode == 0


def gh_available(root: Path) -> bool:
    result = run(["gh", "auth", "status"], cwd=root, check=False)
    return result.returncode == 0


def github_owner(root: Path) -> str | None:
    result = run(
        ["gh", "repo", "view", "--json", "owner", "--jq", ".owner.login"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def merged_pr_completion(
    root: Path,
    owner: str | None,
    branch: str,
    *,
    include_closed_unmerged: bool,
) -> Completion | None:
    if not owner:
        return None

    result = run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "closed",
            "--head",
            f"{owner}:{branch}",
            "--limit",
            "20",
            "--json",
            "number,title,url,mergedAt,closedAt,state,headRefName,baseRefName",
        ],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        return None

    prs = json.loads(result.stdout or "[]")
    for pr in prs:
        if pr.get("mergedAt"):
            return Completion(True, f"merged PR #{pr['number']}: {pr['title']}")
    if include_closed_unmerged and prs:
        pr = prs[0]
        if pr.get("closedAt"):
            return Completion(True, f"closed unmerged PR #{pr['number']}: {pr['title']}")
    return None


def completion_for(
    root: Path,
    owner: str | None,
    branch: str,
    *,
    remote: bool,
    include_closed_unmerged: bool,
) -> Completion:
    pr_completion = merged_pr_completion(
        root,
        owner,
        branch,
        include_closed_unmerged=include_closed_unmerged,
    )
    if pr_completion:
        return pr_completion

    branch_ref = f"origin/{branch}" if remote else branch
    if is_ancestor(root, branch_ref, "origin/main"):
        return Completion(True, "merged into origin/main")

    return Completion(False, "no merged PR or origin/main merge found")


def print_section(title: str, rows: list[str]) -> None:
    print(f"\n{title}")
    if rows:
        for row in rows:
            print(f"  - {row}")
    else:
        print("  - none")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove completed git worktrees, local branches, and origin branches."
    )
    parser.add_argument("--apply", action="store_true", help="delete instead of previewing")
    parser.add_argument(
        "--include-closed-unmerged",
        action="store_true",
        help="treat closed unmerged PR branches as complete",
    )
    parser.add_argument(
        "--force-worktrees",
        action="store_true",
        help="allow removal of dirty completed worktrees",
    )
    parser.add_argument(
        "--protected",
        action="append",
        default=[],
        metavar="BRANCH",
        help="additional protected branch name; may be repeated",
    )
    args = parser.parse_args()

    root = repo_root()
    protected = PROTECTED_BRANCHES | set(args.protected)
    print(f"Repository: {root}")
    print("Mode: apply" if args.apply else "Mode: dry run")

    output(["git", "fetch", "origin", "--prune"], cwd=root)
    output(["git", "worktree", "prune"], cwd=root)

    active_branch = current_branch(root)
    local = local_branches(root)
    remote = remote_branches(root)
    worktrees = parse_worktrees(root)
    owner = github_owner(root) if gh_available(root) else None

    if owner:
        print(f"GitHub owner: {owner}")
    else:
        print("GitHub owner: unavailable; using git ancestry checks only")

    removable_worktrees: list[tuple[Worktree, Completion]] = []
    skipped_worktrees: list[str] = []
    branches_blocked_by_dirty_worktrees: set[str] = set()
    local_completions: dict[str, Completion] = {}
    remote_completions: dict[str, Completion] = {}

    for worktree in worktrees:
        if not worktree.branch or worktree.path == root:
            continue
        branch = worktree.branch
        if branch in protected or branch == active_branch:
            skipped_worktrees.append(f"{worktree.path} ({branch}): protected or active")
            continue
        completion = completion_for(
            root,
            owner,
            branch,
            remote=False,
            include_closed_unmerged=args.include_closed_unmerged,
        )
        local_completions[branch] = completion
        if not completion.complete:
            skipped_worktrees.append(f"{worktree.path} ({branch}): {completion.reason}")
            continue
        if worktree.dirty and not args.force_worktrees:
            branches_blocked_by_dirty_worktrees.add(branch)
            skipped_worktrees.append(f"{worktree.path} ({branch}): dirty worktree")
            continue
        removable_worktrees.append((worktree, completion))

    for branch in sorted(local):
        if branch in protected or branch == active_branch:
            continue
        if branch not in local_completions:
            local_completions[branch] = completion_for(
                root,
                owner,
                branch,
                remote=False,
                include_closed_unmerged=args.include_closed_unmerged,
            )

    for branch in sorted(remote):
        if branch in protected:
            continue
        remote_completions[branch] = completion_for(
            root,
            owner,
            branch,
            remote=True,
            include_closed_unmerged=args.include_closed_unmerged,
        )

    local_to_delete = [
        (branch, completion)
        for branch, completion in sorted(local_completions.items())
        if completion.complete
        and branch in local
        and branch != active_branch
        and branch not in branches_blocked_by_dirty_worktrees
    ]
    remote_to_delete = [
        (branch, completion)
        for branch, completion in sorted(remote_completions.items())
        if completion.complete and branch not in branches_blocked_by_dirty_worktrees
    ]

    print_section(
        "Worktrees to remove",
        [f"{wt.path} ({wt.branch}): {completion.reason}" for wt, completion in removable_worktrees],
    )
    print_section(
        "Local branches to delete",
        [f"{branch}: {completion.reason}" for branch, completion in local_to_delete],
    )
    print_section(
        "GitHub branches to delete",
        [f"origin/{branch}: {completion.reason}" for branch, completion in remote_to_delete],
    )
    print_section("Skipped worktrees", skipped_worktrees)

    ambiguous = [
        f"{branch}: {completion.reason}"
        for branch, completion in sorted(local_completions.items())
        if not completion.complete and branch not in protected and branch != active_branch
    ]
    print_section("Branches left alone", ambiguous)

    if not args.apply:
        print("\nNo changes made. Re-run with --apply to remove the listed completed items.")
        return 0

    failures: list[str] = []

    for worktree, _completion in removable_worktrees:
        command = ["git", "worktree", "remove", str(worktree.path)]
        if args.force_worktrees:
            command.append("--force")
        result = run(command, cwd=root, check=False)
        if result.returncode != 0:
            failures.append(f"worktree {worktree.path}: {result.stderr.strip()}")

    for branch, _completion in local_to_delete:
        result = run(["git", "branch", "-D", branch], cwd=root, check=False)
        if result.returncode != 0:
            failures.append(f"local branch {branch}: {result.stderr.strip()}")

    for branch, _completion in remote_to_delete:
        result = run(["git", "push", "origin", "--delete", branch], cwd=root, check=False)
        if result.returncode != 0:
            failures.append(f"origin/{branch}: {result.stderr.strip()}")

    if failures:
        print_section("Failures", failures)
        return 1

    print("\nCleanup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
