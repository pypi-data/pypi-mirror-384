import shutil
import zipfile
import tarfile
import gzip
import bz2
import lzma
from pathlib import Path


try:
    import py7zr        # for .7z
except ImportError:
    py7zr = None

try:
    import rarfile      # for .rar
except ImportError:
    rarfile = None


# ---------- Detection ---------------------------------------------------------
def detect_archive_type(path: str | Path) -> str:
    """Return a simple string label for the archive type, else 'unknown'."""
    p = Path(path).with_suffix("").name.lower()  # strip double-suffix like .tar.gz
    ext = Path(path).suffix.lower()

    if ext == ".zip":
        return "zip"
    if ext in {".tar"}:
        return "tar"
    if ext in {".gz"} and p.endswith(".tar"):
        return "tar.gz"
    if ext in {".bz2"} and p.endswith(".tar"):
        return "tar.bz2"
    if ext in {".xz"} and p.endswith(".tar"):
        return "tar.xz"
    if ext == ".gz":
        return "gzip"
    if ext == ".bz2":
        return "bzip2"
    if ext == ".xz":
        return "xz"
    if ext == ".7z":
        return "7z"
    if ext == ".rar":
        return "rar"
    return "unknown"


def _extract_stream(open_func, path: Path, out_dir: Path):
    """Helper for single-file compressed streams (.gz, .bz2, .xz)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / path.with_suffix("").name
    with open_func(path, "rb") as f_in, open(out_file, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


# ---------- Extraction --------------------------------------------------------
def extract_archive(path: str | Path, out_dir: str | Path) -> None:
    """Detect the archive type and extract it into out_dir."""
    path, out_dir = Path(path), Path(out_dir)
    archive_type = detect_archive_type(path)

    match archive_type:
        # --- ZIP
        case "zip":
            with zipfile.ZipFile(path) as zf:
                zf.extractall(out_dir)

        # --- tar.* (auto-deduces compression)
        case "tar" | "tar.gz" | "tar.bz2" | "tar.xz":
            with tarfile.open(path, mode="r:*") as tf:
                tf.extractall(out_dir)

        # --- single-file streams
        case "gzip":
            _extract_stream(gzip.open, path, out_dir)
        case "bzip2":
            _extract_stream(bz2.open, path, out_dir)
        case "xz":
            _extract_stream(lzma.open, path, out_dir)

        # --- 7-Zip
        case "7z":
            if py7zr is None:
                raise ImportError("py7zr not installed - run `pip install py7zr`")
            with py7zr.SevenZipFile(path, mode="r") as z:
                z.extractall(path=out_dir)

        # --- RAR
        case "rar":
            if rarfile is None:
                raise ImportError("rarfile not installed - run `pip install rarfile`")
            if not rarfile.is_rarfile(path):
                raise rarfile.BadRarFile(f"{path} is not a valid RAR archive")
            with rarfile.RarFile(path) as rf:
                rf.extractall(out_dir)

        # --- fallback
        case _:
            raise ValueError(f"Unsupported or unknown archive type: {archive_type}")