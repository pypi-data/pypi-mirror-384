import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import tarfile
import zipfile
from typing import Any, BinaryIO, TextIO, cast

import yaml
from custom_python_logger import get_logger

logger = get_logger(__name__)


class _FileCompression:
    @staticmethod
    def gzip_file(input_path: str, output_path: str | None = None) -> str:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if output_path is None:
            output_path = input_path + ".gz"

        try:
            with open(input_path, "rb") as f_in:
                with gzip.open(output_path, "wb") as f_out:
                    f_out.write(f_in.read())
            return output_path
        except Exception as e:
            raise OSError(f"Error compressing file: {e}") from e

    @staticmethod
    def ungzip_file(gz_path: str, output_path: str | None = None) -> str:
        if not os.path.isfile(gz_path):
            raise FileNotFoundError(f"Gzipped file does not exist: {gz_path}")

        if output_path is None:
            if gz_path.endswith(".gz"):
                output_path = gz_path[:-3]  # Remove .gz extension
            else:
                output_path = gz_path + "_decompressed"

        try:
            with gzip.open(gz_path, "rb") as f_in:
                with open(output_path, "wb") as f_out:
                    f_out.write(f_in.read())
            return output_path
        except Exception as e:
            raise OSError(f"Error decompressing file: {e}") from e

    @staticmethod
    def compress_directory(directory: str, output_path: str | None = None) -> str:
        """Compress directory to tarball."""
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory does not exist: {directory}")

        if output_path is None:
            output_path = directory.rstrip(os.sep) + ".tar.gz"

        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(directory, arcname=os.path.basename(directory))

        return output_path

    @staticmethod
    def extract_archive(archive_path: str, output_dir: str | None = None) -> str:
        """Extract archive file."""
        if not os.path.isfile(archive_path):
            raise FileNotFoundError(f"Archive does not exist: {archive_path}")

        if output_dir is None:
            output_dir = os.path.splitext(archive_path)[0]
            # Handle double extensions like .tar.gz
            if output_dir.endswith(".tar"):
                output_dir = output_dir[:-4]

        _FilePath.ensure_dir(output_dir)

        if archive_path.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=output_dir)
        elif archive_path.endswith(".tar.bz2"):
            with tarfile.open(archive_path, "r:bz2") as tar:
                tar.extractall(path=output_dir)
        elif archive_path.endswith(".tar"):
            with tarfile.open(archive_path, "r") as tar:
                tar.extractall(path=output_dir)
        elif archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(output_dir)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path}")

        return output_dir


class _FileHash:
    @staticmethod
    def file_md5(filename: str, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def file_sha1(filename: str, chunk_size: int = 8192) -> str:
        """Calculate SHA1 hash of a file."""
        hash_sha1 = hashlib.sha1()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()

    @staticmethod
    def file_sha256(filename: str, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class _FileIO:
    @staticmethod
    def safe_open(filename: str, mode: str = "r", encoding: str | None = None, **kwargs: Any) -> TextIO | BinaryIO:
        if "b" in mode:
            return cast(BinaryIO, open(filename, mode, **kwargs))
        return cast(TextIO, open(filename, mode, encoding=encoding or "utf-8", **kwargs))

    @staticmethod
    def read_text(filename: str, encoding: str = "utf-8") -> str:
        with open(filename, encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write_text(text: str, filename: str, encoding: str = "utf-8") -> None:
        with open(filename, "w", encoding=encoding) as f:
            f.write(text)

    @staticmethod
    def read_json(filename: str) -> dict[str, Any]:
        with _FileIO.safe_open(filename, "r") as f:
            return json.load(f)

    @staticmethod
    def write_json(data: dict[str, Any], filename: str, indent: int = 2) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def read_yaml(filename: str) -> Any:
        with open(filename, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_yaml(data: Any, filename: str, **kwargs: Any) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, **kwargs)

    def read_csv(self, filename: str, **kwargs: Any) -> list[dict[str, Any]]:
        with self.safe_open(filename, "r", newline="") as f:
            reader = csv.DictReader(f, **kwargs)
            return list(reader)

    @staticmethod
    def write_csv(
        data: list[dict[str, Any]], filename: str, fieldnames: list[str] | None = None, **kwargs: Any
    ) -> None:
        if not data:
            return

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, **kwargs)
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def is_binary_file(path: str, chunk_size: int = 1024) -> bool:
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
        return b"\0" in chunk

    @staticmethod
    def is_file_empty(path: str) -> bool:
        return os.path.getsize(path) == 0


class _FileManipulation:
    @staticmethod
    def remove_emojis(text: str) -> str:
        return re.sub(r"[\U00010000-\U0010ffff]", "", text).strip()


class _FilePath:
    @staticmethod
    def ensure_dir(directory: str) -> str:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def get_file_extension(path: str) -> str:
        return os.path.splitext(path)[1][1:]

    @staticmethod
    def get_filename(path: str, with_extension: bool = True) -> str:
        if with_extension:
            return os.path.basename(path)
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def get_relative_path(path: str, base_path: str) -> str:
        return os.path.relpath(path, base_path)

    @staticmethod
    def list_files(directory: str, extension: str | None = None, recursive: bool = False) -> list[str]:
        result = []
        for root, _, files in os.walk(directory) if recursive else [(directory, [], os.listdir(directory))]:
            for file in files:
                if not extension or file.endswith(extension):
                    result.append(os.path.join(root, file))
        return result


class _FileSystem:
    @staticmethod
    def copy_file(src: str, dst: str) -> None:
        shutil.copy2(src, dst)

    @staticmethod
    def move_file(src: str, dst: str) -> None:
        shutil.move(src, dst)

    @staticmethod
    def delete_file(path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def file_size(path: str) -> int:
        return os.path.getsize(path)


class FileUtils:
    file_compression = _FileCompression
    file_hash = _FileHash
    file_io = _FileIO
    file_manipulation = _FileManipulation
    file_path = _FilePath
    file_system = _FileSystem
