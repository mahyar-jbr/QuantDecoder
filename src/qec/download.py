"""Download a dataset archive, check that it is the expected file, and unpack it safely.

Each step is skipped when its result is already in place, so a second run does nothing.
"""

import logging
import shutil
import urllib.request
import zipfile
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path

log = logging.getLogger(__name__)

CHUNK_BYTES = 1 << 20
MARKER_NAME = ".unpacked"


class IntegrityError(Exception):
    """The downloaded file is not the expected one: its size or md5 is wrong."""


@dataclass(frozen=True)
class Archive:
    """A zip file to fetch: where it comes from, its file name, and how to recognise it."""

    url: str
    filename: str
    size: int
    md5: str


GOOGLE_QEC3V5 = Archive(
    url="https://zenodo.org/api/records/6804040/files/google_qec3v5_experiment_data.zip/content",
    filename="google_qec3v5_experiment_data.zip",
    size=315_490_804,
    md5="a7fd8b481c3087090093106382dc217d",
)


def md5_of(path: Path) -> str:
    """Return the md5 hex digest of a file, read in chunks to keep memory use small."""
    digest = md5()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def mismatch(path: Path, archive: Archive) -> str | None:
    """Say how the file differs from the expected archive, or return None if it matches."""
    size = path.stat().st_size
    if size != archive.size:
        return f"{path.name} has {size} bytes, expected {archive.size}"
    actual = md5_of(path)
    if actual != archive.md5:
        return f"{path.name} has md5 {actual}, expected {archive.md5}"
    return None


def download(archive: Archive, data_dir: Path) -> Path:
    """Return the checked zip in data_dir, fetching it first unless a good copy is already there.

    The file is written to a .part name and renamed only after its size and md5 match,
    so an interrupted or corrupted download never looks complete.
    """
    zip_path = data_dir / archive.filename
    if zip_path.exists() and mismatch(zip_path, archive) is None:
        log.info("Found a good copy of %s, skipping the download", archive.filename)
        return zip_path

    part = zip_path.with_name(zip_path.name + ".part")
    log.info("Downloading %s (%.1f MB)", archive.filename, archive.size / 1e6)
    try:
        with urllib.request.urlopen(archive.url, timeout=60) as response, part.open("wb") as out:
            shutil.copyfileobj(response, out, CHUNK_BYTES)
        problem = mismatch(part, archive)
        if problem:
            raise IntegrityError(problem)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    part.replace(zip_path)
    log.info("Size and md5 match")
    return zip_path


def unpack(zip_path: Path, target: Path) -> None:
    """Extract the zip into target, refusing any entry whose path would land outside target."""
    root = target.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not (root / name).resolve().is_relative_to(root):
                raise ValueError(f"{zip_path.name} has an entry outside the target folder: {name}")
        log.info("Unpacking into %s", target)
        zf.extractall(target)


def ensure_dataset(archive: Archive, data_dir: Path) -> Path:
    """Download, check and unpack the archive under data_dir, and return the unpacked folder."""
    target = data_dir / Path(archive.filename).stem
    marker = target / MARKER_NAME
    if marker.exists():
        log.info("Already downloaded, checked and unpacked: %s", target)
        return target
    data_dir.mkdir(parents=True, exist_ok=True)
    zip_path = download(archive, data_dir)
    unpack(zip_path, target)
    marker.write_text(f"{archive.filename} md5 {archive.md5}\n")
    return target
