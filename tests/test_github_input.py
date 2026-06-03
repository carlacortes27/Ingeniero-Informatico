import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from ci2_lab import main as main_module
from ci2_lab.utils import GitHubCloneError, clone_github_repo, is_github_url


def test_is_github_url_accepts_only_https_github_repo_host() -> None:
    assert is_github_url("https://github.com/user/repo")
    assert not is_github_url("http://github.com/user/repo")
    assert not is_github_url("https://example.com/user/repo")
    assert not is_github_url("./local/repo")


def test_clone_github_repo_uses_shallow_clone(monkeypatch, tmp_path) -> None:
    calls = []

    def fake_mkdtemp(prefix: str) -> str:
        root = tmp_path / f"{prefix}repo"
        root.mkdir()
        return str(root)

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[-1]).mkdir()
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("ci2_lab.utils.tempfile.mkdtemp", fake_mkdtemp)
    monkeypatch.setattr("ci2_lab.utils.subprocess.run", fake_run)

    local_path, repo_name = clone_github_repo("https://github.com/user/repo")

    assert repo_name == "repo"
    assert Path(local_path) == tmp_path / "ci2-lab-repo" / "repo"
    assert calls[0][0] == [
        "git",
        "clone",
        "--depth",
        "1",
        "https://github.com/user/repo",
        str(tmp_path / "ci2-lab-repo" / "repo"),
    ]
    assert calls[0][1]["check"] is True


def test_clone_github_repo_rejects_invalid_repo_url(monkeypatch) -> None:
    run = Mock()
    monkeypatch.setattr("ci2_lab.utils.subprocess.run", run)

    with pytest.raises(GitHubCloneError, match="URL"):
        clone_github_repo("https://github.com/user")

    run.assert_not_called()


def test_clone_github_repo_reports_clone_failure(monkeypatch, tmp_path) -> None:
    temp_root = tmp_path / "clone-root"
    temp_root.mkdir()

    monkeypatch.setattr("ci2_lab.utils.tempfile.mkdtemp", lambda prefix: str(temp_root))

    def fail_clone(command, **kwargs):
        raise subprocess.CalledProcessError(128, command, stderr="Repository not found")

    monkeypatch.setattr("ci2_lab.utils.subprocess.run", fail_clone)

    with pytest.raises(GitHubCloneError, match="Repository not found"):
        clone_github_repo("https://github.com/user/private")

    assert not temp_root.exists()


def test_main_cleans_temporary_directory_after_github_scan(monkeypatch, tmp_path) -> None:
    repo_path = tmp_path / "temp-root" / "repo"
    repo_path.mkdir(parents=True)
    removed = []

    monkeypatch.setattr(
        main_module,
        "clone_github_repo",
        lambda url: (str(repo_path), "repo"),
    )
    monkeypatch.setattr(
        main_module.AuditorAgent,
        "scan",
        lambda self, path: Mock(audit={"is_valid": True}),
    )
    monkeypatch.setattr(
        main_module,
        "remove_temporary_directory",
        lambda path: removed.append(path),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["ci2-lab", "scan", "https://github.com/user/repo"],
    )

    assert main_module.main() == 0
    assert removed == [str(repo_path.parent)]
