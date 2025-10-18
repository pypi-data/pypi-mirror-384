import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from prefect import get_run_logger

logger = get_run_logger()


def clone_pat_repo(git_pat, git_url, clone_base_path):
    """ Clone a Git repository using a Personal Access Token (PAT) for authentication."""
    # Retrieve environment variables
    access_token = git_pat # os.environ.get('GIT_PAT')
    repo_url = git_url # os.environ.get('GIT_URL')
    
    if not access_token or not repo_url:
        raise ValueError("Environment variables GIT_PAT or GIT_URL are not set")

    # Correctly format the URL with the PAT
    if 'https://' in repo_url:
        # Splitting the URL and inserting the PAT
        parts = repo_url.split('https://', 1)
        repo_url = f'https://{access_token}@{parts[1]}'
    else:
        raise ValueError("URL must begin with https:// for PAT authentication")

    # Directory where the repo will be cloned
    repo_path = os.path.join(clone_base_path, 'manifest-repo')

    # Clone the repository
    if not os.path.exists(repo_path):
        logger.info(f"Cloning repository into {repo_path}")
        repo = Repo.clone_from(repo_url, repo_path)
        logger.info("Repository cloned successfully.")
    else:
        logger.info(f"Repository already exists at {repo_path}")


def clone_ssh_repo(
    git_url: str,
    clone_base_path: str,
    repo_dir_name: str = "manifest-repo",
    depth: int = 1,
    ssh_key_env: str = "GIT_SSH_PRIVATE_KEY",
    known_hosts_env: str = "GIT_SSH_KNOWN_HOSTS",
) -> Path:
    """
    Clone/update a repo via SSH using key + known_hosts from env vars.
    - GIT_SSH_PRIVATE_KEY: full private key (BEGIN/END ...)
    - GIT_SSH_KNOWN_HOSTS: lines from `ssh-keyscan github.com`
    """
    if not git_url.startswith("git@"):
        raise ValueError("git_url must be an SSH URL like 'git@github.com:org/repo.git'")

    priv_key = os.environ.get(ssh_key_env)
    kh_data  = os.environ.get(known_hosts_env)
    if not priv_key:
        raise ValueError(f"Missing env var {ssh_key_env}")
    if not kh_data:
        raise ValueError(f"Missing env var {known_hosts_env}")

    base = Path(clone_base_path).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    repo_path = base / repo_dir_name

    tmpdir = Path(tempfile.mkdtemp(prefix="git_ssh_"))
    key_path = tmpdir / "id_rsa"
    kh_path  = tmpdir / "known_hosts"

    try:
        key_path.write_text(priv_key, encoding="utf-8")
        kh_path.write_text(kh_data, encoding="utf-8")
        try:
            os.chmod(key_path, 0o600)
        except PermissionError:
            pass  # ignore on platforms where chmod doesn't apply

        # Note: no StrictModes here
        ssh_cmd = (
            f"ssh -i {key_path} -o IdentitiesOnly=yes "
            f"-o UserKnownHostsFile={kh_path} "
            f"-o StrictHostKeyChecking=yes"
        )

        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = ssh_cmd

        if not repo_path.exists():
            cmd = ["git", "clone"]
            if depth and depth > 0:
                cmd += ["--depth", str(depth)]
            cmd += [git_url, str(repo_path)]
            subprocess.check_call(cmd, env=env)
        else:
            if not (repo_path / ".git").exists():
                raise RuntimeError(f"Path exists but is not a git repo: {repo_path}")
            subprocess.check_call(["git", "remote", "set-url", "origin", git_url], cwd=repo_path, env=env)
            subprocess.check_call(["git", "fetch", "--all", "--prune"], cwd=repo_path, env=env)
            subprocess.check_call(["git", "pull", "--ff-only", "origin"], cwd=repo_path, env=env)

        return repo_path

    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
