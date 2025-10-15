#!/usr/bin/env python3
"""Clean, self-contained GitHub clones manager.

This module is intentionally compact and safe: it clones or updates GitHub
repositories for a user and does not write project scaffolding by default.
Helpers and a small BaseMake are inlined to avoid depending on external
shared packages.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeGuard, TypeVar, cast
from urllib import error as urllib_error
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Iterable
    from http.client import HTTPResponse

JsonDict = dict[str, object]

T_co = TypeVar("T_co", covariant=True)


class Factory(Protocol[T_co]):
    def __call__(self, *args: object, **kwargs: object) -> T_co: ...


def _json_loads(payload: str) -> object:
    return cast("object", json.loads(payload))


_ALLOWED_URL_SCHEMES = {"http", "https"}


def _urlopen(request: urllib.request.Request) -> HTTPResponse:
    scheme = urlsplit(request.full_url).scheme.lower()
    if scheme not in _ALLOWED_URL_SCHEMES:
        message = f"Refusing to open URL with scheme '{scheme}'"
        raise ValueError(message)
    return cast("HTTPResponse", urllib.request.urlopen(request))  # noqa: S310


def _is_json_dict(data: object) -> TypeGuard[JsonDict]:
    if not isinstance(data, dict):
        return False
    dict_obj = cast("dict[object, object]", data)
    return all(isinstance(key, str) for key in dict_obj)


def _is_json_list(data: object) -> TypeGuard[list[object]]:
    return isinstance(data, list)


@dataclass(frozen=True)
class RepoRecord:
    name: str
    full_name: str
    clone_url: str | None
    ssh_url: str | None
    fork: bool

    def matches(self, names: set[str] | None) -> bool:
        if names is None:
            return True
        return self.name in names or self.full_name in names

    def resolved_clone_url(self, token: str | None, *, allow_token_clone: bool) -> str:
        base_url = self.clone_url or self.ssh_url or ""
        if token and allow_token_clone and base_url.startswith("https://"):
            return base_url.replace("https://", f"https://{token}@")
        return base_url


def _coerce_repo_record(data: JsonDict) -> RepoRecord | None:
    name_obj = data.get("name")
    if not isinstance(name_obj, str) or not name_obj:
        return None
    full_name_obj = data.get("full_name")
    full_name = (
        full_name_obj if isinstance(full_name_obj, str) and full_name_obj else name_obj
    )
    clone_url_obj = data.get("clone_url")
    clone_url = (
        clone_url_obj if isinstance(clone_url_obj, str) and clone_url_obj else None
    )
    ssh_url_obj = data.get("ssh_url")
    ssh_url = ssh_url_obj if isinstance(ssh_url_obj, str) and ssh_url_obj else None
    fork_obj = data.get("fork")
    fork = fork_obj if isinstance(fork_obj, bool) else False
    return RepoRecord(
        name=name_obj,
        full_name=full_name,
        clone_url=clone_url,
        ssh_url=ssh_url,
        fork=fork,
    )


def _info(*args: object) -> None:
    print(" ".join(str(arg) for arg in args))


def _error(*args: object) -> None:
    print(" ".join(str(arg) for arg in args), file=sys.stderr)


class BaseMake:
    DEFAULT_TARGET_DIR: str | None = None  # dynamic; set after helper defined
    GIT_BIN: str = "git"
    TOKEN_ENV_VAR: str = "GITHUB_TOKEN"  # noqa: S105
    ALLOW_TOKEN_CLONE_ENV: str = "X_ALLOW_TOKEN_CLONE"  # noqa: S105
    RECLONE_ON_CORRUPT: bool = True
    # Auto-reclone/repair is enabled by default. The implementation performs a
    # safe backup before attempting reclone to avoid data loss.
    ALLOW_AUTO_RECLONE_ON_CORRUPT: bool = True
    CLONE_RETRIES: int = 1

    @classmethod
    def get_env(cls, name: str, default: str | None = None) -> str | None:
        value = os.environ.get(name)
        return value if value is not None else default

    @classmethod
    def get_env_bool(cls, name: str, *, default: bool = False) -> bool:
        env_value = os.environ.get(name)
        if env_value is None:
            return default
        return env_value.lower() in ("1", "true", "yes")

    def run_cmd(
        self, args: Iterable[str], *, check: bool = False
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603
            list(args), check=check, capture_output=True, text=True
        )

    def get_token(self) -> str | None:
        return os.environ.get(self.TOKEN_ENV_VAR)

    @property
    def allow_token_clone(self) -> bool:
        return self.get_env_bool(self.ALLOW_TOKEN_CLONE_ENV, default=False)

    def __init__(self, ctx: object | None = None) -> None:
        self._ctx = ctx


class x_cls_make_github_clones_x(BaseMake):  # noqa: N801
    PER_PAGE = 100
    USER_AGENT = "clone-script"

    def __init__(  # noqa: PLR0913
        self,
        username: str | None = None,
        target_dir: str | None = None,
        *,
        shallow: bool = False,
        include_forks: bool = False,
        force_reclone: bool = False,
        names: list[str] | str | None = None,
        token: str | None = None,
        include_private: bool = True,
        **_: object,
    ) -> None:
        self.username = username
        if not target_dir:
            target_dir = str(_repo_parent_root())
        self.target_dir = _normalize_target_dir(target_dir)
        self.shallow = shallow
        self.include_forks = include_forks
        self.force_reclone = force_reclone
        # Explicitly annotate attribute so mypy knows this can be Optional[list[str]]
        self.names: list[str] | None
        if isinstance(names, str):
            self.names = [n.strip() for n in names.split(",") if n.strip()]
        elif isinstance(names, list):
            # names is list[str] here; strip empties
            self.names = [n.strip() for n in names if n.strip()]
        else:
            self.names = None
        self.token = token or os.environ.get(self.TOKEN_ENV_VAR)
        self.include_private = include_private
        self.exit_code: int | None = None

    def _request_json(
        self, url: str, headers: dict[str, str] | None = None
    ) -> list[JsonDict]:
        req = urllib.request.Request(url, headers=headers or {})  # noqa: S310
        with _urlopen(req) as resp:
            raw_body = resp.read()
        payload = _json_loads(raw_body.decode("utf-8"))
        if _is_json_dict(payload):
            return [payload]
        if _is_json_list(payload):
            return [entry for entry in payload if _is_json_dict(entry)]
        return []

    def fetch_repos(  # noqa: C901
        self, username: str | None = None, *, include_forks: bool | None = None
    ) -> list[RepoRecord]:
        username = username or self.username
        include_forks = (
            include_forks if include_forks is not None else self.include_forks
        )
        if not username and not self.token:
            message = "username or token required"
            raise RuntimeError(message)
        per_page = self.PER_PAGE
        headers: dict[str, str] = {"User-Agent": self.USER_AGENT}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        collected: dict[str, RepoRecord] = {}

        def _collect(base_url: str) -> None:
            page = 1
            while True:
                sep = "&" if "?" in base_url else "?"
                url = f"{base_url}{sep}per_page={per_page}&page={page}"
                try:
                    data_list = self._request_json(url, headers=headers)
                except (ValueError, urllib_error.URLError):
                    break
                if not data_list:
                    break
                for raw in data_list:
                    repo = _coerce_repo_record(raw)
                    if repo is None:
                        continue
                    if not include_forks and repo.fork:
                        continue
                    collected[repo.full_name] = repo
                if len(data_list) < per_page:
                    break
                page += 1

        # Public/user visible repos
        if username:
            _collect(f"https://api.github.com/users/{username}/repos?type=all")
        # Private repos via /user/repos if token + include_private
        if self.token and self.include_private:
            _collect(
                "https://api.github.com/user/repos?affiliation=owner,collaborator,organization_member&visibility=all"
            )

        repos: list[RepoRecord] = list(collected.values())
        if self.names is not None:
            name_set = {name for name in self.names if name}
            repos = [repo for repo in repos if repo.matches(name_set)]
        return repos

    def _clone_or_update_repo(  # noqa: C901, PLR0912
        self, repo_dir: Path, git_url: str
    ) -> bool:
        repo_path = Path(repo_dir)
        if not repo_path.exists():
            _info(f"Cloning {git_url} into {repo_path}")
            args = [self.GIT_BIN, "clone", git_url, str(repo_path)]
            if self.shallow:
                args[2:2] = ["--depth", "1"]
            for _ in range(max(1, self.CLONE_RETRIES)):
                try:
                    proc = self.run_cmd(args)
                except OSError as exc:
                    _error("git clone failed:", exc)
                    return False
                if proc.returncode == 0:
                    return True
                _error("clone failed:", proc.stderr or proc.stdout)
            return False

        _info(f"Updating {repo_path}")
        stashed = False
        success = False
        try:
            self.run_cmd(
                [
                    self.GIT_BIN,
                    "-C",
                    str(repo_path),
                    "fetch",
                    "--all",
                    "--prune",
                ]
            )

            status = self.run_cmd(
                [self.GIT_BIN, "-C", str(repo_path), "status", "--porcelain"],
                check=False,
            )
            has_uncommitted = bool(status.stdout.strip())

            if has_uncommitted:
                stash = self.run_cmd(
                    [
                        self.GIT_BIN,
                        "-C",
                        str(repo_path),
                        "stash",
                        "push",
                        "-u",
                        "-m",
                        "autostash-for-update",
                    ]
                )
                stashed = stash.returncode == 0

            pull_args = [self.GIT_BIN, "-C", str(repo_path), "pull"]
            if not self.shallow:
                pull_args.extend(["--rebase", "--autostash"])
            pull = self.run_cmd(pull_args)
            if pull.returncode != 0:
                pull = self.run_cmd([self.GIT_BIN, "-C", str(repo_path), "pull"])

            if pull.returncode == 0:
                success = True
            else:
                _error("pull failed:", pull.stderr or pull.stdout)
        except OSError as exc:
            _error("failed to update repository:", exc)
        finally:
            if stashed:
                try:
                    pop = self.run_cmd(
                        [
                            self.GIT_BIN,
                            "-C",
                            str(repo_path),
                            "stash",
                            "pop",
                        ]
                    )
                except OSError as pop_exc:
                    _error("failed to pop stash:", pop_exc)
                else:
                    if pop.returncode != 0:
                        _error("stash pop failed:", pop.stderr or pop.stdout)
        return success

    def _attempt_update(self, repo_dir: Path, git_url: str) -> bool:
        repo_path = Path(repo_dir)
        try:
            if self.force_reclone:
                _info(f"force_reclone enabled; refreshing in-place {repo_path}")
                return self._force_refresh_repo(repo_path, git_url)

            if self._clone_or_update_repo(repo_path, git_url):
                return True

            return self._clone_to_temp_swap(repo_path, git_url)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            _error("exception while updating:", exc)
            return False

    def _force_refresh_repo(self, repo_dir: Path, git_url: str) -> bool:
        """Refresh an existing repo in-place without deleting files."""

        repo_path = Path(repo_dir)
        if not repo_path.exists():
            return self._clone_or_update_repo(repo_path, git_url)

        stashed = False
        success = False
        try:
            self._fetch_all(repo_path)
            if self._has_uncommitted_changes(repo_path):
                stashed = self._stash_changes(repo_path)
            success = self._pull_or_reset(repo_path)
        except OSError as exc:
            _error("force refresh exception:", exc)
            success = False
        finally:
            if stashed:
                self._pop_stash(repo_path)
        return success

    def _clone_to_temp_swap(self, repo_dir: Path, git_url: str) -> bool:
        """Clone into a temporary directory and atomically swap the repo."""

        repo_path = Path(repo_dir)
        try:
            tmp_dir, bak_dir = self._prepare_clone_paths(repo_path)
        except OSError as exc:
            _error("failed to ensure parent directory:", exc)
            return False

        if not self._clone_with_retries(tmp_dir, git_url):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return False

        backup_created = False
        if repo_path.exists():
            try:
                self._backup_repo(repo_path, bak_dir)
            except OSError as exc:
                _error("failed to backup existing repository:", exc)
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return False
            backup_created = True

        try:
            self._replace_repo(repo_path, tmp_dir)
        except OSError as exc:
            _error("failed to replace repository:", exc)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            if backup_created:
                self._restore_backup(bak_dir, repo_path)
            return False

        shutil.rmtree(bak_dir, ignore_errors=True)
        return True

    def _fetch_all(self, repo_path: Path) -> None:
        self.run_cmd(
            [
                self.GIT_BIN,
                "-C",
                str(repo_path),
                "fetch",
                "--all",
                "--prune",
            ]
        )

    def _has_uncommitted_changes(self, repo_path: Path) -> bool:
        status = self.run_cmd(
            [self.GIT_BIN, "-C", str(repo_path), "status", "--porcelain"],
            check=False,
        )
        return bool(status.stdout.strip())

    def _stash_changes(self, repo_path: Path) -> bool:
        stash = self.run_cmd(
            [
                self.GIT_BIN,
                "-C",
                str(repo_path),
                "stash",
                "push",
                "-u",
                "-m",
                "force-refresh-stash",
            ]
        )
        return stash.returncode == 0

    def _pull_or_reset(self, repo_path: Path) -> bool:
        pull_args = [self.GIT_BIN, "-C", str(repo_path), "pull"]
        if not self.shallow:
            pull_args.extend(["--rebase", "--autostash"])
        pull = self.run_cmd(pull_args)
        if pull.returncode == 0:
            return True

        self._fetch_all(repo_path)
        reset = self.run_cmd(
            [
                self.GIT_BIN,
                "-C",
                str(repo_path),
                "reset",
                "--hard",
                "origin/HEAD",
            ]
        )
        self.run_cmd([self.GIT_BIN, "-C", str(repo_path), "clean", "-fdx"])
        if reset.returncode != 0:
            _error("force refresh reset failed:", reset.stderr or reset.stdout)
            return False
        return True

    def _pop_stash(self, repo_path: Path) -> None:
        try:
            pop = self.run_cmd(
                [
                    self.GIT_BIN,
                    "-C",
                    str(repo_path),
                    "stash",
                    "pop",
                ]
            )
        except OSError as exc:
            _error("failed to pop stash:", exc)
            return
        if pop.returncode != 0:
            _error("stash pop failed:", pop.stderr or pop.stdout)

    def _prepare_clone_paths(self, repo_path: Path) -> tuple[Path, Path]:
        parent = repo_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        base = repo_path.name
        ts = int(time.time())
        tmp_dir = parent / f".{base}.tmp.{ts}"
        bak_dir = parent / f".{base}.bak.{ts}"
        return tmp_dir, bak_dir

    def _clone_with_retries(self, tmp_dir: Path, git_url: str) -> bool:
        args = [self.GIT_BIN, "clone", git_url, str(tmp_dir)]
        if self.shallow:
            args[2:2] = ["--depth", "1"]
        attempts = max(1, self.CLONE_RETRIES)
        for _ in range(attempts):
            try:
                proc = self.run_cmd(args)
            except OSError as exc:
                _error("git clone failed:", exc)
                return False
            if proc.returncode == 0:
                return True
            _error("clone failed:", proc.stderr or proc.stdout)
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return False

    def _backup_repo(self, repo_path: Path, bak_dir: Path) -> None:
        shutil.move(str(repo_path), str(bak_dir))

    def _replace_repo(self, repo_path: Path, tmp_dir: Path) -> None:
        shutil.move(str(tmp_dir), str(repo_path))

    def _restore_backup(self, bak_dir: Path, repo_path: Path) -> None:
        if bak_dir.exists() and not repo_path.exists():
            try:
                shutil.move(str(bak_dir), str(repo_path))
            except OSError as exc:
                _error("failed to restore original repository:", exc)

    def _repo_clone_url(self, repo: RepoRecord) -> str:
        return repo.resolved_clone_url(
            self.token, allow_token_clone=self.allow_token_clone
        )

    def sync(self, username: str | None = None, dest: str | None = None) -> int:
        username = username or self.username
        dest_candidate = dest or self.target_dir or self.DEFAULT_TARGET_DIR
        dest_path: Path = (
            Path(dest_candidate) if dest_candidate else _repo_parent_root()
        )
        dest_path.mkdir(parents=True, exist_ok=True)
        try:
            repos = self.fetch_repos(username=username)
        except (
            RuntimeError,
            urllib_error.URLError,
            OSError,
            ValueError,
        ) as exc:
            _error("failed to fetch repo list:", exc)
            return 2

        if self.names is not None:
            name_set = {name for name in self.names if name}
            repos = [repo for repo in repos if repo.matches(name_set)]

        exit_code = 0
        for repo in repos:
            name = repo.name
            if not name:
                continue
            repo_path = dest_path / name
            git_url = self._repo_clone_url(repo)
            if not git_url:
                _error(f"missing clone URL for {name}")
                exit_code = 3
                continue
            if not self._attempt_update(repo_path, git_url):
                exit_code = 3
        self.exit_code = exit_code
        return exit_code


_REPO_PARENT_ROOT_CACHE: dict[str, Path] = {}


def _compute_repo_parent_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        git_dir = ancestor / ".git"
        if git_dir.exists():
            return ancestor.parent
    return here.parent


def _repo_parent_root() -> Path:
    cached = _REPO_PARENT_ROOT_CACHE.get("value")
    if cached is not None:
        return cached
    result = _compute_repo_parent_root()
    _REPO_PARENT_ROOT_CACHE["value"] = result
    return result


def _normalize_target_dir(val: str | None) -> str:
    if val is None:
        return str(_repo_parent_root())
    return str(Path(val))


if BaseMake.DEFAULT_TARGET_DIR is None:
    BaseMake.DEFAULT_TARGET_DIR = str(_repo_parent_root())


def _as_callable(value: object) -> Factory[object] | None:
    if callable(value):
        return cast("Factory[object]", value)
    return None


def _is_unexpected_keyword_error(error: TypeError) -> bool:
    lowered = str(error).lower()
    return "unexpected keyword" in lowered or "got an unexpected keyword" in lowered


def _set_force_reclone_attr(cloner: object, *, flag: bool) -> None:
    with suppress(AttributeError, TypeError):
        setattr(cloner, "force_reclone", flag)  # noqa: B010


def _instantiate_cloner(  # noqa: PLR0913
    *,
    username: str,
    target_dir: str,
    shallow: bool,
    include_forks: bool,
    force_reclone: bool,
    ctx: object | None,
) -> x_cls_make_github_clones_x:
    try:
        cloner = x_cls_make_github_clones_x(
            username=username,
            target_dir=target_dir,
            shallow=shallow,
            include_forks=include_forks,
            force_reclone=force_reclone,
            ctx=ctx,
        )
    except TypeError as error:
        if not _is_unexpected_keyword_error(error):
            raise
        cloner = x_cls_make_github_clones_x(
            username=username,
            target_dir=target_dir,
            shallow=shallow,
            include_forks=include_forks,
        )
        _set_force_reclone_attr(cloner, flag=force_reclone)
    else:
        _set_force_reclone_attr(cloner, flag=force_reclone)
    return cloner


def _call_cloner_entrypoint(
    cloner: object,
    method_name: str,
    *,
    args: tuple[object, ...] = (),
    suppress_exceptions: tuple[type[BaseException], ...] = (),
) -> bool:
    candidate_attr: object = getattr(cloner, method_name, None)
    candidate = _as_callable(candidate_attr)
    if candidate is None:
        return False
    if suppress_exceptions:
        with suppress(*suppress_exceptions):
            candidate(*args)
    else:
        candidate(*args)
    return True


def _call_cloner_sync(cloner: object, *, username: str, target_dir: str) -> bool:
    sync_attr: object = getattr(cloner, "sync", None)
    sync_callable = _as_callable(sync_attr)
    if sync_callable is None:
        return False
    try:
        sync_callable(username, target_dir)
    except TypeError:
        sync_callable()
    return True


def _run_cloner(
    cloner: object,
    *,
    username: str,
    target_dir: str,
) -> None:
    if _call_cloner_entrypoint(cloner, "run"):
        return
    if _call_cloner_sync(cloner, username=username, target_dir=target_dir):
        return
    if _call_cloner_entrypoint(
        cloner,
        "main",
        suppress_exceptions=(RuntimeError, OSError, ValueError),
    ):
        return
    _info("No recognized cloner entrypoint found; skipping run")


def synchronize_workspace(  # noqa: PLR0913
    *,
    username: str,
    target_dir: str,
    shallow: bool,
    include_forks: bool,
    force_reclone: bool,
    ctx: object | None = None,
) -> x_cls_make_github_clones_x:
    """Instantiate and run the clones manager for the provided options."""

    cloner = _instantiate_cloner(
        username=username,
        target_dir=target_dir,
        shallow=shallow,
        include_forks=include_forks,
        force_reclone=force_reclone,
        ctx=ctx,
    )
    try:
        _run_cloner(cloner, username=username, target_dir=target_dir)
    except (
        RuntimeError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as exc:
        _error("Cloner run failed:", exc)
    return cloner


def resolve_workspace_root(
    cloner: object,
    *,
    default_root: str | os.PathLike[str] | None = None,
) -> Path:
    """Derive the workspace root containing cloned repositories.

    The orchestrator previously duplicated this logic; expose it here so the
    control center can remain lean and delegate to the clones package.
    """

    def _coerce_path(value: object) -> Path | None:
        if isinstance(value, Path):
            return value
        if isinstance(value, str):
            return Path(value)
        if isinstance(value, os.PathLike):  # pragma: no branch - simple guard
            return Path(os.fspath(cast("os.PathLike[str]", value)))
        return None

    target_dir_attr: object = getattr(cloner, "target_dir", None)
    root_candidate = _coerce_path(target_dir_attr)
    if root_candidate is None:
        base_default = default_root if default_root is not None else _repo_parent_root()
        root_candidate = _coerce_path(base_default) or _repo_parent_root()

    root_path = root_candidate
    if (root_path / ".git").is_dir():
        parent = root_path.parent
        with suppress(OSError):
            for entry in parent.iterdir():
                if entry == root_path:
                    continue
                if (entry / ".git").is_dir():
                    root_path = parent
                    break
    return root_path


def main() -> int:
    username = os.environ.get("X_GH_USER")
    if not username:
        _info("Set X_GH_USER to run the example")
        return 0
    m = x_cls_make_github_clones_x(username=username)
    return m.sync()


if __name__ == "__main__":
    sys.exit(main())
