"""A .phtiles file: spec.json + tiles/<mc_key>/<tile>.npz, zipped.

A project carries its results so a diagram that took an hour opens
instantly on another machine; loading unpacks the tiles into the
working cache, where the store finds them by key as usual.
"""
import re
import zipfile
from pathlib import Path, PurePosixPath

from phasetiles.spec import DiagramSpec

_TILE = re.compile(r"tiles/[0-9a-f]{16}/[0-9a-f]{16}\.npz")


def save_project(path, spec, store):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
        z.writestr("spec.json", spec.to_json())
        for f in store.files_for(spec):
            z.write(f, f"tiles/{spec.mc_key()}/{f.name}")
    tmp.replace(path)


def load_project(path, store):
    with zipfile.ZipFile(path) as z:
        spec = DiagramSpec.from_json(z.read("spec.json").decode())
        for name in z.namelist():
            # only tiles/<key>/<key>.npz, exactly as the store names
            # them: a '..' check alone lets '..\' and 'C:\' through,
            # which Windows reads as a path out of the cache
            if _TILE.fullmatch(name):
                p = PurePosixPath(name)
                dest = store.root / p.parts[1] / p.parts[2]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))
    return spec
