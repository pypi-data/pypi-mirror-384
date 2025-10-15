from pathlib import Path
import click
from git import Repo, GitCommandError
from .crypto import CryptoManager
from .config_manager import ConfigManager
import getpass
from datetime import datetime
import json
import os
import subprocess
import shutil
from tempfile import NamedTemporaryFile

class EnvManager:
    def __init__(self, project: str, env_name: str, repo_name:str):
        """
        repo_path: path to your local clone of the private repo
        """
        if not project or not env_name:
            raise ValueError("Project and environment name must not be empty.")

        self.project = project
        self.env_name = env_name

        cm = ConfigManager()
        cfg = cm.load()

        repo_key_path = cfg.get("configs", {}).get(repo_name, {}).get("key_path")
        self.repo_key_path = Path(os.path.expanduser(repo_key_path))
        self.crypto = CryptoManager(self.repo_key_path)

        repo_path = cfg.get("configs", {}).get(repo_name, {}).get("repo_path")
        self.repo_path = Path(os.path.expanduser(repo_path))
        if not self.repo_path.exists():
            raise FileNotFoundError( f"Repo path does not exist: {self.repo_path}. "
        "Run `gitenvy init --repo <URL>` first or check your config.")

        try:
            self.repo = Repo(str(self.repo_path))
        except GitCommandError as e:
            raise RuntimeError(f"Git error: {e}")

        try:
            self.git_user_name = self.repo.config_reader().get_value("user", "name")
        except (KeyError, IOError, AttributeError):
            self.git_user_name = getpass.getuser()  # fallback

    @staticmethod
    def init_repo(repo_url, path, branch=None):
        """
        Clone the repo if not exists, or pull and switch branch if exists.
        Returns: dict with 'success' (bool) and 'message' (str)
        """
        click.echo(f"Initializing repo from {repo_url}...")
        git_dir = os.path.join(path, ".git")
        if not os.path.exists(path):
            clone_cmd = ["git", "clone"]
            if branch:
                clone_cmd += ["-b", branch]
            clone_cmd += [repo_url, path]
            try:
                subprocess.run(clone_cmd, check=True)
                return {
                    "success": True,
                    "message": f"✅ Repo cloned successfully{' on branch ' + branch if branch else ''}"
                }
            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "message": f"⚠️ Git clone failed: {e}"
                }
        else:
            if os.path.exists(git_dir):
                try:
                    repo_obj = Repo(path)
                    repo_obj.remotes.origin.fetch()
                    if branch:
                        if branch in [b.name for b in repo_obj.branches]:
                            repo_obj.git.checkout(branch)
                        else:
                            repo_obj.git.checkout("-b", branch, f"origin/{branch}")
                    repo_obj.git.pull()
                    return {
                        "success": True,
                        "message": f"✅ Repo updated{' on branch ' + branch if branch else ''}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"⚠️ Git operation failed: {e}"
                    }
            else:
                return {
                    "success": False,
                    "message": "⚠️ Path exists but is not a git repo."
                }

    def push(self, env_file: str = ".env"):
        """
        Encrypt and push the .env file to the git repo.
        Always syncs with remote first. Performs rollback on failure.
        """
        env_file_path = Path(env_file)
        if not env_file_path.exists():
            raise FileNotFoundError(f".env file not found: {env_file_path}")

        click.echo(f"Pushing encrypted .env for {self.project}/{self.env_name}...")

        try:
            self.repo.remotes.origin.fetch()
            self.repo.remotes.origin.pull(rebase=True)
        except GitCommandError as e:
            raise RuntimeError(f"⚠️ Warning: could not sync latest changes before push: {e}")

        try:
            encrypted = self.crypto.encrypt(env_file_path.read_text())
        except Exception as e:
            raise RuntimeError(f"Encryption failed: {e}")

        base_dir = self.repo_path / self.project / self.env_name
        base_dir.mkdir(parents=True, exist_ok=True)

        existing_versions = [
            int(p.name) for p in base_dir.iterdir()
            if p.is_dir() and p.name.isdigit()
        ]
        next_version = str(max(existing_versions, default=0) + 1)

        out_dir = base_dir / next_version
        try:
            out_dir.mkdir(parents=False)
        except FileExistsError:
            next_version = str(max(existing_versions + [int(next_version)], default=0) + 1)
            out_dir = base_dir / next_version
            out_dir.mkdir(parents=True)

        out_file = out_dir / ".env.enc"
        try:
            out_file.write_bytes(encrypted)
        except PermissionError:
            raise PermissionError(f"No write permission for {out_file}")

        metadata = {
            "last_updated_by": self.git_user_name,
            "last_updated_at": datetime.utcnow().isoformat() + "Z",
            "version": int(next_version)
        }
        (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        try:
            self.repo.git.add(A=True)
            self.repo.index.commit(f"Add {self.project}/{self.env_name} version {next_version}")
            self.repo.remotes.origin.push()
        except GitCommandError as e:
            click.echo(f"⚠️ Git push failed: {e}")
            click.echo("Rolling back local changes...")

            # Only reset last commit if it was created by gitenvy
            last_commit = self.repo.head.commit.message
            if last_commit.startswith("Add") and f"{self.project}/{self.env_name}" in last_commit:
                try:
                    self.repo.git.reset("--hard", "HEAD~1")
                except Exception:
                    pass
                shutil.rmtree(out_dir, ignore_errors=True)

            raise RuntimeError(f"Push failed and local changes were rolled back.")

        return out_file


    def pull(self, version: str = "latest", out_path: str = ".env"):
        """
        Pull the latest (or specified) version of .env from git, decrypt, and save locally.
        Always fetches remote first and writes atomically to avoid corrupting existing files.
        """
        click.echo(f"Pulling version '{version}' of {self.project}/{self.env_name}...")
        
        try:
            self.repo.remotes.origin.fetch()
            self.repo.remotes.origin.pull()
        except GitCommandError as e:
            raise RuntimeError(f"⚠️ Could not pull latest changes: {e}")

        base_dir = self.repo_path / self.project / self.env_name
        if not base_dir.exists():
            raise FileNotFoundError(f"No versions found for {self.project}/{self.env_name}")

        versions = [int(p.name) for p in base_dir.iterdir() if p.is_dir() and p.name.isdigit()]
        if not versions:
            raise FileNotFoundError("No versions found")

        if version == "latest":
            version = str(max(versions))
        elif version not in map(str, versions):
            raise ValueError(f"Version {version} not found")

        enc_file = base_dir / version / ".env.enc"
        if not enc_file.exists():
            raise FileNotFoundError(f"Encrypted file missing for version {version}")

        try:
            decrypted = self.crypto.decrypt(enc_file)
        except Exception as e:
            raise RuntimeError(f"Decryption failed for version {version}: {e}")

        out_file = Path(out_path)
        try:
            with NamedTemporaryFile("w", delete=False, dir=out_file.parent) as tmp:
                tmp.write(decrypted)
                tmp_path = Path(tmp.name)
            shutil.move(str(tmp_path), out_file)
        except PermissionError:
            raise PermissionError(f"No write permission for {out_file}")
        except Exception as e:
            raise RuntimeError(f"Failed to save decrypted .env: {e}")
        return out_file
