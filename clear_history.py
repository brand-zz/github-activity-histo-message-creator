import subprocess
import re
import sys
import os

def run_cmd(cmd, check=True, **kwargs):
    """Helper to run a command and handle errors."""
    try:
        # Set a longer timeout for potentially slow git operations
        return subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=300, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Stderr: {e.stderr.strip()}")
        print(f"Stdout: {e.stdout.strip()}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        return None

def main():
    """
    Rewrites git history to remove all commits with messages matching the "Pixel" pattern.
    """
    print("--- Advanced History Cleaner ---")

    # 1. Check for clean working directory
    status_result = run_cmd(['git', 'status', '--porcelain'])
    if status_result is None:
        sys.exit(1) # Error already printed by run_cmd
    if status_result.stdout:
        print("\nError: Your working directory is not clean (you have uncommitted changes or untracked files).")
        print("Please commit or stash your changes before running this script.")
        sys.exit(1)

    # 2. Find commits to remove
    pixel_pattern = re.compile(r'^Pixel \d+,\d+ - \d+/\d+$')
    try:
        log_result = run_cmd(['git', 'log', '--all', '--pretty=format:%H %s'])
        if log_result is None:
             raise Exception("Failed to get git log")
        all_commits = log_result.stdout.strip().split('\n')

        pixel_commits = [commit for commit in all_commits if commit and pixel_pattern.search(commit.split(' ', 1)[1])]

        if not pixel_commits:
            print("\nNo 'Pixel' commits found in the repository history. Nothing to do.")
            return

        print(f"\nFound {len(pixel_commits)} 'Pixel' commits that will be removed. Preview:")
        print('\n'.join(pixel_commits[:15]))
        if len(pixel_commits) > 15: print("...")

    except Exception as e:
        print(f"Could not read git log or parse commits. Aborting. Error: {e}")
        sys.exit(1)

    # 3. Use git filter-branch
    print("\nUsing 'git filter-branch' to rewrite history.")
    filter_script = (
        f'if git log -1 --format=%s "$GIT_COMMIT" | grep -qE "{pixel_pattern.pattern}"; '
        'then skip_commit "$@"; '
        'else git commit-tree "$@"; '
        'fi'
    )
    env = os.environ.copy()
    env['FILTER_BRANCH_SQUELCH_WARNING'] = '1'
    command = [
        'git', 'filter-branch', '-f',
        '--commit-filter', filter_script, '--', '--all'
    ]

    print(f"\nRunning command: {' '.join(command)}")
    print("Rewriting history... This may take a while.")
    result = run_cmd(command, env=env)

    if result:
        print("\nHistory rewritten successfully!")
        print("Running garbage collection to finalize changes...")
        run_cmd(['git', 'gc', '--prune=now', '--aggressive'])
        print("Cleanup complete.")
    else:
        print("\nAn error occurred during history rewriting.")

if __name__ == "__main__":
    main()
