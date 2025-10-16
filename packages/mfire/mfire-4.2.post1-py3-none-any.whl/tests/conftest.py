import filecmp
import logging
import os
import shutil
from pathlib import Path
from typing import Any, List

import numpy as np
import pytest

import mfire.utils.mfxarray as xr
from mfire.settings import Settings
from mfire.utils.json import JsonFile
from tests.functions_test import assert_identically_close

logging.getLogger("faker").setLevel(logging.ERROR)


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "validation: mark test to run only for validation step"
    )


@pytest.fixture(autouse=True)
def test_cleanup(tmp_path):
    Settings().clean()
    yield
    shutil.rmtree(tmp_path)


def create_nc_field_SG(name: str, vmin: int, vmax: int, units: str):
    coords = {
        "valid_time": [np.datetime64("2022-06-08T00:00:00.000000000")],
        "latitude": np.arange(90, -90.25, -0.25),
        "longitude": np.arange(-180, 180, 0.25),
    }
    arr = np.random.randint(vmin, vmax)
    da = (vmax - vmin) * xr.DataArray(arr, coords=coords, dims=coords, name=name) + vmin
    da.attrs["units"] = units
    return da


@pytest.fixture(scope="session")
def working_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path_working_dir = tmp_path_factory.mktemp("working_dir")
    Settings().set_full_working_dir(working_dir=tmp_path_working_dir)

    data_dir = Settings().data_dirname
    data_dir.mkdir(parents=True, exist_ok=True)

    # Settings SG files
    sg_fields = (
        ("r_700", 0, 100, "%"),
        ("msl", 94036, 105782, "hPa"),
        ("t2m", 194, 323, "K"),
        ("wbpt_850", 232, 302, "K"),
        ("u10", -25, 31, "m/s"),
        ("v10", -28, 26, "m/s"),
        ("u_850", -48, 45, "m/s"),
        ("v_850", -50, 35, "m/s"),
    )

    for field in sg_fields:
        create_nc_field_SG(*field).to_netcdf(data_dir / f"{field[0]}.nc")

    # Setting SG mask
    coords = {
        "latitude": np.arange(80, -0.25, -0.25),
        "longitude": np.arange(-50, 60.25, 0.25),
        "id": ["global"],
    }
    xr.DataArray(
        np.ones([len(v) for v in coords.values()]),
        coords=coords,
        dims=tuple(coords),
        name="globd025",
    ).to_netcdf(data_dir / "situation_generale_marine.nc")

    return tmp_path_working_dir


@pytest.fixture()
def tmp_path_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def root_path(request):
    return request.config.rootdir


@pytest.fixture()
def root_path_cwd(monkeypatch, request):
    monkeypatch.chdir(request.config.rootdir)
    return request.config.rootdir


@pytest.fixture()
def test_file(request, tmp_path) -> Path | List[Path]:
    info = getattr(request, "param", {})
    extension = info.get("extension", "txt")
    nbr = info.get("nbr", 1)
    name = info.get("name", "file")
    if nbr > 1:
        files = [tmp_path / f"{name}_{i}.{extension}" for i in range(nbr)]
    else:
        files = [tmp_path / f"{name}.{extension}"]

    content = info.get("content", "")
    for f in files:
        with open(f, "w") as file_writer:
            file_writer.write(content)

    yield files if nbr > 1 else files[0]


def _assert_equals_result(ref_path: Path, output_path: Path, data: Any):
    output_json = JsonFile(output_path)
    ref_json = JsonFile(ref_path)

    if not ref_path.exists():
        if os.environ.get("GITLAB_CI") == "true":
            assert False, f"Reference file {ref_path} is missing!"
        # Load and dump to be able to handle None key by sorting
        ref_json.dump(JsonFile.loads(JsonFile.dumps(data)), indent=2, sort_keys=True)
    else:
        # Load and dump to be able to handle None key by sorting
        output_json.dump(JsonFile.loads(JsonFile.dumps(data)), indent=2, sort_keys=True)

        if not ref_json.is_equal_to(output_json):
            if os.environ.get("GITLAB_CI") != "true":  # Allow to correct differences
                os.system(f"meld {ref_path} {output_path}")

            if not ref_json.is_equal_to(output_json):
                assert False


@pytest.fixture()
def assert_equals_result(request, tmp_path):
    file_path = Path(request.module.__file__).parent
    file_path /= (
        Path("refs") / Path(request.module.__file__).stem / request.node.parent.name
    )

    file_path.mkdir(parents=True, exist_ok=True)

    filename = f"{request.node.name}.json"
    filename = filename.replace("\\", "").replace("/", "")

    ref_path = file_path / filename

    output_path = tmp_path / filename
    return lambda data: _assert_equals_result(ref_path, output_path, data)


def _assert_equals_file(ref_path: Path, output_path: Path, data: Path):
    assert data.exists()

    ref_path = Path(f"{ref_path}_{data.name}")
    output_path = Path(f"{output_path}_{data.name}")

    if data.suffix == ".json":
        _assert_equals_result(ref_path, output_path, JsonFile(data).load())
    elif not ref_path.exists():
        if os.environ.get("GITLAB_CI") == "true":
            assert False, f"Reference file {ref_path} is missing!"
        else:
            shutil.copyfile(data, ref_path)
    else:
        shutil.copyfile(data, output_path)
        if data.suffix == ".nc":
            assert_identically_close(
                xr.open_dataset(ref_path), xr.open_dataset(output_path)
            )
        elif data.suffix == ".netcdf":
            assert_identically_close(
                xr.open_dataarray(ref_path), xr.open_dataarray(output_path)
            )
        else:
            assert filecmp.cmp(ref_path, output_path, shallow=False)


@pytest.fixture()
def assert_equals_file(request, tmp_path):
    file_path = Path(request.module.__file__).parent
    file_path /= (
        Path("refs") / Path(request.module.__file__).stem / request.node.parent.name
    )

    file_path.mkdir(parents=True, exist_ok=True)

    filename = request.node.name.replace("\\", "").replace("/", "")
    ref_path = file_path / filename
    output_path = tmp_path / filename

    return lambda data: _assert_equals_file(ref_path, output_path, data)
