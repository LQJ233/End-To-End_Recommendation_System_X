import atexit
import os
import shutil
import tempfile
from pathlib import Path

from app.artifacts import DEFAULT_MODEL_ROOT


def _prepare_isolated_model_root() -> None:
    real_root = Path(DEFAULT_MODEL_ROOT)
    versions = sorted(
        [
            path
            for path in real_root.iterdir()
            if path.is_dir() and (path / "manifest.json").exists()
        ],
        key=lambda path: path.name,
    )
    if not versions:
        return

    temp_root = Path(tempfile.mkdtemp(prefix="recsys-model-tests-"))
    target = temp_root / versions[-1].name
    target.mkdir(parents=True)
    for source in versions[-1].iterdir():
        destination = target / source.name
        if source.name == "milvus.db":
            shutil.copytree(source, destination)
        else:
            destination.symlink_to(source)
    os.environ["RECSYS_MODEL_ROOT"] = str(temp_root)
    atexit.register(shutil.rmtree, temp_root, ignore_errors=True)


_prepare_isolated_model_root()
