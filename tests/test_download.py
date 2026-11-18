"""Tests for the dataset download: checksums, safe unpacking, and a second run doing nothing."""

import hashlib
import shutil
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from qec.download import CHUNK_BYTES, Archive, IntegrityError, ensure_dataset, md5_of


def make_zip(path: Path, members: dict[str, str]) -> Path:
    """Write a small zip with the given text members and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, text in members.items():
            zf.writestr(name, text)
    return path


def archive_for(zip_path: Path) -> Archive:
    """Describe a local zip as an Archive served from a file:// URL."""
    return Archive(
        url=zip_path.as_uri(),
        filename="sample.zip",
        size=zip_path.stat().st_size,
        md5=md5_of(zip_path),
    )


@pytest.fixture
def remote_zip(tmp_path: Path) -> Path:
    return make_zip(tmp_path / "remote" / "sample.zip", {"a.txt": "alpha", "sub/b.txt": "beta"})


def test_md5_of_matches_the_rfc_1321_test_vector(tmp_path: Path) -> None:
    path = tmp_path / "abc.txt"
    path.write_bytes(b"abc")
    assert md5_of(path) == "900150983cd24fb0d6963f7d28e17f72"


def test_md5_of_reads_files_bigger_than_one_chunk(tmp_path: Path) -> None:
    data = bytes(range(256)) * (3 * CHUNK_BYTES // 256) + b"tail"
    path = tmp_path / "big.bin"
    path.write_bytes(data)
    assert md5_of(path) == hashlib.md5(data).hexdigest()


def test_downloads_checks_and_unpacks(tmp_path: Path, remote_zip: Path) -> None:
    data_dir = tmp_path / "data"
    target = ensure_dataset(archive_for(remote_zip), data_dir)
    assert (target / "a.txt").read_text() == "alpha"
    assert (target / "sub" / "b.txt").read_text() == "beta"
    assert md5_of(data_dir / "sample.zip") == md5_of(remote_zip)
    assert not list(data_dir.glob("*.part"))


def test_second_run_does_nothing(tmp_path: Path, remote_zip: Path) -> None:
    archive = archive_for(remote_zip)
    data_dir = tmp_path / "data"
    target = ensure_dataset(archive, data_dir)
    (target / "a.txt").write_text("edited after the first run")
    remote_zip.unlink()  # any download attempt would now fail

    assert ensure_dataset(archive, data_dir) == target
    assert (target / "a.txt").read_text() == "edited after the first run"


def test_wrong_md5_is_rejected_and_nothing_is_kept(tmp_path: Path, remote_zip: Path) -> None:
    archive = replace(archive_for(remote_zip), md5="0" * 32)
    data_dir = tmp_path / "data"
    with pytest.raises(IntegrityError, match="md5"):
        ensure_dataset(archive, data_dir)
    assert list(data_dir.iterdir()) == []


def test_wrong_size_is_rejected(tmp_path: Path, remote_zip: Path) -> None:
    archive = replace(archive_for(remote_zip), size=remote_zip.stat().st_size + 1)
    with pytest.raises(IntegrityError, match="bytes"):
        ensure_dataset(archive, tmp_path / "data")


def test_good_local_copy_is_not_downloaded_again(tmp_path: Path, remote_zip: Path) -> None:
    archive = archive_for(remote_zip)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(remote_zip, data_dir / "sample.zip")
    remote_zip.unlink()  # so the zip can only come from the local copy

    target = ensure_dataset(archive, data_dir)
    assert (target / "a.txt").read_text() == "alpha"


def test_bad_local_copy_is_replaced(tmp_path: Path, remote_zip: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sample.zip").write_bytes(b"truncated")

    ensure_dataset(archive_for(remote_zip), data_dir)
    assert md5_of(data_dir / "sample.zip") == md5_of(remote_zip)


def test_entry_outside_the_target_folder_is_refused(tmp_path: Path) -> None:
    evil = make_zip(tmp_path / "remote" / "sample.zip", {"../escaped.txt": "should not be written"})
    data_dir = tmp_path / "data"
    with pytest.raises(ValueError, match="outside the target folder"):
        ensure_dataset(archive_for(evil), data_dir)
    assert not (data_dir / "escaped.txt").exists()
    assert not (data_dir / "sample" / ".unpacked").exists()
