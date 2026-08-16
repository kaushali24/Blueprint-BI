from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


SUPPORTED_SUFFIXES = {".txt", ".csv", ".json"}


@dataclass
class ZIPValidationResult:
    is_valid: bool
    supported_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@contextmanager
def temporary_zip_workspace(file_bytes: bytes):
    """Extract a ZIP archive into a temp directory and delete it when done."""
    temp_dir = Path(tempfile.mkdtemp(prefix="whatsapp-import-"))
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            warnings: list[str] = []
            for info in archive.infolist():
                if info.is_dir():
                    continue

                raw_name = info.filename.replace("\\", "/")
                pure_name = PurePosixPath(raw_name)
                normalized_parts = pure_name.parts

                if pure_name.is_absolute() or ".." in normalized_parts:
                    warnings.append(f"Skipping unsafe archive entry: {info.filename}")
                    continue

                destination = (temp_dir / pure_name).resolve()
                if temp_dir.resolve() not in destination.parents and destination != temp_dir.resolve():
                    warnings.append(f"Skipping unsafe archive path: {info.filename}")
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

            yield temp_dir, warnings
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def validate_zip_package(file_bytes: bytes) -> ZIPValidationResult:
    """Validate an uploaded WhatsApp export zip and list supported textual files."""
    result = ZIPValidationResult(is_valid=False, supported_files=[], errors=[], warnings=[])

    if not file_bytes:
        result.errors.append("Uploaded package is empty.")
        return result

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if not names:
                result.errors.append("Archive contains no files.")
                return result

            unsafe_entries = []
            for name in names:
                normalized = name.replace("\\", "/")
                pure_name = PurePosixPath(normalized)
                if pure_name.is_absolute() or ".." in pure_name.parts:
                    unsafe_entries.append(name)

            if unsafe_entries:
                result.errors.append("Archive contains unsafe file paths.")
                return result

            supported = [
                name
                for name in names
                if Path(name).suffix.lower() in SUPPORTED_SUFFIXES
            ]

            if not supported:
                result.errors.append("Archive contains no supported WhatsApp chat export files.")
                return result

            result.supported_files = supported
            result.is_valid = True
            return result
    except (OSError, ValueError, zipfile.BadZipFile):
        result.errors.append("Uploaded package is not a valid ZIP archive.")
        return result
