"""Download MovieLens-1M from GroupLens and convert it for RecBole."""

import csv
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

from .io import sha256_file


ML1M_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"


def _safe_extract(archive, destination):
    destination = Path(destination).resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if destination not in target.parents and target != destination:
            raise ValueError(f"Unsafe archive member: {member.filename}")
    archive.extractall(destination)


def download_ml1m(output_root="data/raw", url=ML1M_URL):
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    archive_path = root / "ml-1m.zip"
    if not archive_path.is_file():
        temporary = archive_path.with_suffix(".zip.tmp")
        with urllib.request.urlopen(url, timeout=180) as response, temporary.open("wb") as target:
            shutil.copyfileobj(response, target)
        temporary.replace(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        _safe_extract(archive, root)
    return {"archive": str(archive_path), "sha256": sha256_file(archive_path),
            "dataset_dir": str(root / "ml-1m"), "url": url}


def _read_dat(path):
    with Path(path).open(encoding="latin-1") as source:
        for line in source:
            yield line.rstrip("\n").split("::")


def convert_ml1m(raw_dir, output_root="data/recbole"):
    raw = Path(raw_dir).resolve()
    required = [raw / name for name in ("ratings.dat", "movies.dat", "users.dat")]
    if not all(path.is_file() for path in required):
        raise FileNotFoundError(f"Expected ratings.dat, movies.dat, users.dat in {raw}")
    out = Path(output_root).resolve() / "ml-1m"
    out.mkdir(parents=True, exist_ok=True)

    with (out / "ml-1m.inter").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, delimiter="\t", lineterminator="\n")
        writer.writerow(["user_id:token", "item_id:token", "rating:float", "timestamp:float"])
        writer.writerows(_read_dat(raw / "ratings.dat"))

    with (out / "ml-1m.item").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, delimiter="\t", lineterminator="\n")
        writer.writerow(["item_id:token", "movie_title:token_seq", "release_year:token",
                         "genre:token_seq"])
        for item_id, title, genres in _read_dat(raw / "movies.dat"):
            match = re.search(r"\((\d{4})\)\s*$", title)
            year = match.group(1) if match else "unknown"
            clean = title[:match.start()].strip() if match else title.strip()
            writer.writerow([item_id, clean, year, genres.replace("|", " ")])

    with (out / "ml-1m.user").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, delimiter="\t", lineterminator="\n")
        writer.writerow(["user_id:token", "age:token", "gender:token",
                         "occupation:token", "zip_code:token"])
        writer.writerows(_read_dat(raw / "users.dat"))
    return str(out)

