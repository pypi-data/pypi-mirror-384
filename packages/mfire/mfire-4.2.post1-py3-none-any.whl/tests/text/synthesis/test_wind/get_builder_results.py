import json
import shutil
from pathlib import Path

import numpy as np

REF_DIR: Path = Path(__file__).parent / "refs" / "test_wind_builder"

ONE_BLOCK_RES_DIR: Path = REF_DIR / "TestBuilderWindCase3OneBlock"
TWO_BLOCKS_RES_DIR: Path = REF_DIR / "TestBuilderWindCase3TwoBlocks"
TRICKY_RES_DIR: Path = REF_DIR / "TestBuilderWindCase3Tricky"


def convert_to_str(num: float | int) -> str:
    if np.isnan(num):
        return str(np.nan)
    num_as_int: int = int(num)
    num = num_as_int if num_as_int == num else num
    return str(num)


def get_term_hour(d: np.timedelta64) -> str:
    term: np.float64 = d / np.timedelta64(1, "h")
    term_as_int = int(term)

    if term == term_as_int:
        return "%02d" % term_as_int
    return "%.2f" % float(term)


def get_result(file_path: Path):
    with open(file_path, "r") as fp:
        d: dict = json.load(fp)

    case: str = d["case"]
    text: str = d["text"]
    valid_time: list = [np.datetime64(e) for e in d["input"]["valid_time"]]

    data_time: list = [get_term_hour(vt - valid_time[0]) for vt in valid_time]
    data_wf: list = [convert_to_str(e) for e in d["input"]["data_wf"]]
    data_wd: list = [convert_to_str(e) for e in d["input"]["data_wd"]]

    size_max = max(len(e) for e in data_time)
    size_max = max(size_max, max(len(e) for e in data_wf))
    size_max = max(size_max, max(len(e) for e in data_wd))

    data_time = [f"%{size_max}s" % s for s in data_time]
    data_wf = [f"%{size_max}s" % s for s in data_wf]
    data_wd = [f"%{size_max}s" % s for s in data_wd]

    res = (
        f"case: {case}\n"
        f"time: {'|'.join(data_time)}\n"
        f"wind: {'|'.join(data_wf)}\n"
        f"dir : {'|'.join(data_wd)}\n"
        f"text: {text}\n"
    )

    return res


def process_dir(dir_path: Path, output: Path | str):
    name: str = dir_path.name
    res = f"{name}\n"
    res += f"{'#'*len(name)}\n\n"

    for file_path in dir_path.glob("*.json"):
        res += f"{get_result(file_path)}\n"

    with open(output, "w") as fp:
        fp.write(res)


if __name__ == "__main__":
    out_dir: Path = Path("block_unit_tests_result")
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(exist_ok=True)

    process_dir(ONE_BLOCK_RES_DIR, out_dir / "one_block.txt")
    process_dir(TWO_BLOCKS_RES_DIR, out_dir / "two_blocks.txt")
    process_dir(TRICKY_RES_DIR, out_dir / "tricky.txt")
