#!/usr/bin/env python3
import subprocess
import click
from pathlib import Path

@click.command()
@click.argument("direction", type=click.Choice(["first", "next", "prev"]))
def navcom(direction):
    """Navigate through git commits: first, next, or prev."""
    try:
        git_dir = subprocess.check_output(["git", "rev-parse", "--git-dir"], text=True).strip()
    except subprocess.CalledProcessError:
        click.echo("Error: Not in a git repository", err=True)
        raise SystemExit(1)

    git_dir_path = Path(git_dir)
    progress_file = git_dir_path / "nc-progress"
    commits_file = git_dir_path / "nc-commits"

    if not commits_file.exists():
        click.echo("Initializing commit history...")
        try:
            default_branch = (
                subprocess.check_output(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                .strip()
                .replace("refs/remotes/origin/", "")
            )
        except subprocess.CalledProcessError:
            for branch in ["main", "master", "develop", "unstable"]:
                if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]).returncode == 0:
                    default_branch = branch
                    break
            else:
                default_branch = subprocess.check_output(
                    ["git", "branch", "--show-current"], text=True
                ).strip() or "HEAD"

        click.echo(f"Using branch: {default_branch}")

        commits = subprocess.check_output(
            ["git", "log", default_branch, "--reverse", "--format=%H"], text=True
        ).splitlines()
        commits_file.write_text("\n".join(commits))
        progress_file.write_text("0")
        click.echo(f"Found {len(commits)} commits to navigate")

    current_index = int(progress_file.read_text().strip())
    commits = commits_file.read_text().splitlines()
    total_commits = len(commits)

    if direction == "first":
        target_index = 1
    elif direction == "next":
        target_index = current_index + 1
        if target_index > total_commits:
            click.echo("✓ You've navigated all commits!")
            click.echo("To restart: rm .git/nc-progress .git/nc-commits")
            raise SystemExit(0)
    else:
        target_index = current_index - 1
        if target_index < 1:
            click.echo("Error: Already at the first commit", err=True)
            raise SystemExit(1)

    commit_hash = commits[target_index - 1]
    subprocess.run(["git", "checkout", commit_hash], check=True)

    progress_file.write_text(str(target_index))

    click.echo("")
    click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    click.echo(f"Commit {target_index} of {total_commits}")
    click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    log_info = subprocess.check_output(
        ["git", "log", "-1", "--format=Commit:  %H%nAuthor:  %an <%ae>%nDate:    %ad%nSubject: %s", "--date=short"],
        text=True,
    )
    click.echo(log_info)
    click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    click.echo("")
    click.echo("Run 'navcom next' or 'navcom prev' to navigate commits")
