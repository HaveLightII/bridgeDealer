"""Build the offline downloads from the published site files."""
import argparse
import gzip
import io
import os
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import zipfile


def write_tar(path, files):
    with path.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as archive:
            for name in files:
                data = Path(name).read_bytes()
                entry = tarfile.TarInfo(name)
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify existing download contents")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parent)
    boards = ["staticDealer.py", *sorted(p.as_posix() for p in Path("boards").rglob("*.html"))]
    packages = {
        "boards.zip": boards,
        "boards.tar.gz": boards,
        "bridgeDealer.tar.gz": ["index.html", *boards, "boards.zip"],
    }
    with TemporaryDirectory(dir=".") as tmp:
        for name, files in packages.items():
            if args.check:
                if name.endswith(".zip"):
                    with zipfile.ZipFile(name) as archive:
                        ok = sorted(archive.namelist()) == sorted(files) and all(
                            archive.read(f) == Path(f).read_bytes() for f in files)
                else:
                    with tarfile.open(name) as archive:
                        ok = sorted(archive.getnames()) == sorted(files) and all(
                            archive.extractfile(f).read() == Path(f).read_bytes() for f in files)
                if not ok:
                    raise SystemExit(f"{name} 已過期，請執行 python3 package_site.py")
                continue
            target = Path(tmp, name)
            if name.endswith(".zip"):
                with zipfile.ZipFile(target, "w") as archive:
                    for f in files:
                        archive.writestr(zipfile.ZipInfo(f), Path(f).read_bytes(),
                                         compress_type=zipfile.ZIP_DEFLATED)
            else:
                write_tar(target, files)
            target.replace(name)


if __name__ == "__main__":
    main()
