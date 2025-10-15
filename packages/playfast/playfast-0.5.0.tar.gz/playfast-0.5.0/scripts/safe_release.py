"""Safe release workflow with conflict prevention."""

from pathlib import Path
import subprocess
import sys


def run(
    cmd: list[str], check: bool = True, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run command and return result."""
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True, cwd=cwd)


def main() -> None:
    """Execute safe release workflow."""
    print("\n=== Safe Release Workflow ===\n")

    # 0. Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("ERROR: Run this from project root!")
        sys.exit(1)

    # 1. Check clean working tree
    result = run(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("ERROR: Working tree is not clean!")
        print("Commit or stash changes first.")
        print(result.stdout)
        sys.exit(1)
    print("OK: Working tree is clean\n")

    # 2. Sync with remote
    print("Step 1: Syncing with remote...")
    run(["git", "fetch", "origin", "--tags"])

    # Check if behind
    local = run(["git", "rev-parse", "@"]).stdout.strip()
    try:
        remote = run(["git", "rev-parse", "@{u}"]).stdout.strip()
    except subprocess.CalledProcessError:
        print("WARNING: No upstream branch set")
        remote = local

    if local != remote:
        print("ERROR: Local branch is not in sync with remote!")
        print("Run: git pull --tags origin main")
        sys.exit(1)

    print("   OK: In sync with remote\n")

    # 3. Check for existing unreleased commits
    result = run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode == 0:
        last_tag = result.stdout.strip()
        print(f"Step 2: Checking commits since {last_tag}")

        # Count commits since last tag
        result = run(["git", "rev-list", f"{last_tag}..HEAD", "--count"])
        commit_count = int(result.stdout.strip())

        if commit_count == 0:
            print("   No new commits since last release")
            print("   Nothing to release!")
            sys.exit(0)

        print(f"   {commit_count} new commit(s) to release\n")
    else:
        print("Step 2: No previous tags found (first release)\n")

    # 4. Preview next version
    print("Step 3: Calculating next version...")
    result = run(["semantic-release", "version", "--print"], check=False)
    if result.returncode != 0:
        print("ERROR: Failed to calculate next version")
        print(result.stderr)
        sys.exit(1)

    next_version = result.stdout.strip()
    print(f"   Next version: {next_version}\n")

    # 5. Confirm
    response = input(f"Create release {next_version}? [y/N]: ")
    if response.lower() != "y":
        print("Release cancelled")
        sys.exit(0)

    # 6. Create release (local only)
    print("\nStep 4: Creating release (local only)...")
    try:
        # Run the existing release command
        result = run(["poe", "release"])
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Release failed: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

    # 7. Show what was created
    print("\nStep 5: Release created successfully!\n")
    result = run(["git", "log", "-1", "--oneline"])
    print(f"   Commit: {result.stdout.strip()}")

    result = run(["git", "describe", "--tags", "--exact-match"], check=False)
    if result.returncode == 0:
        tag = result.stdout.strip()
        print(f"   Tag: {tag}")
    else:
        print("   WARNING: No tag found on HEAD")

    # 8. Final confirmation before push
    print("\n" + "=" * 50)
    response = input("\nPush to remote? [y/N]: ")
    if response.lower() == "y":
        print("\nStep 6: Pushing to remote...")
        run(["git", "push", "origin", "main"])
        run(["git", "push", "origin", "--tags"])
        print("\nOK: Release pushed successfully!")
        print("\nNext step: Wait for CI to pass, then run:")
        print("  uv run poe release_publish")
    else:
        print("\nRelease created locally. Push manually when ready:")
        print("  git push origin main")
        print("  git push origin --tags")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nRelease cancelled by user")
        sys.exit(1)
