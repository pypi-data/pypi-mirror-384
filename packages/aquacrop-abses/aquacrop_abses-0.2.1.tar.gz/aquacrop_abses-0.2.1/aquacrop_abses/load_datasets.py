#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
加载气象数据集
"""

from datetime import date
from functools import wraps
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Dict, Literal, Optional, cast

import pandas as pd
import yaml
from aquacrop.entities.crop import crop_params
from aquacrop.utils import get_filepath, prepare_weather
from loguru import logger

CROPS_FOLDER = resources.files("res") / "crops"
COLS: list[str] = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]

# 读取字典
_KW = resources.files("res") / "kw_dictionary.yaml"
with open(Path(str(_KW)), "r", encoding="utf-8") as f:
    KWARGS = yaml.safe_load(f)


TestData = Literal[
    "soil", "tmin", "tmax", "prec", "pet", "mete", "1993", "1994", "demo"
]
METE_VARS = ("MinTemp", "MaxTemp", "Precipitation", "ReferenceET")
TEST_PATTERN = "test_{var}_CMFD_01dy_010deg_%Y01-%Y12.nc"
_DEMO_PATTERN = "mete/test_{var}_CMFD_01dy_010deg_199301-199312.nc"
_NAMES = {
    "soil": "soil_test.tif",
    "1993": "mete/test_mete_199301-199312.nc",
    "1994": "mete/test_mete_199401-199412.nc",
    "demo": "mete/test_mete_199301-199412.nc",
    "tmin": _DEMO_PATTERN.format(var="min_temp"),
    "tmax": _DEMO_PATTERN.format(var="max_temp"),
    "prec": _DEMO_PATTERN.format(var="prec_mm"),
    "pet": _DEMO_PATTERN.format(var="pet"),
}
METE_VAR_MAPPING = {
    "MinTemp": "min_temp",
    "MaxTemp": "max_temp",
    "Precipitation": "prec_mm",
    "ReferenceET": "pet",
}


def demo_climate_df() -> pd.DataFrame:
    """获取示例气象数据"""
    path = get_filepath("champion_climate.txt")
    return prepare_weather(path)


def get_test_data_path(file_name: Optional[TestData] = None) -> Traversable:
    """获取测试数据路径"""
    path = resources.files("res")
    if file_name is None:
        return path
    if file_name == "mete":
        return path / "mete"
    return path / _NAMES[file_name]


def clean_crop_type(crop: str) -> str:
    """清洗并检查作物类型是否有效"""
    crop = KWARGS["crops"].get(crop, crop)
    if crop not in crop_params.keys():
        logger.critical(f"Unknown crop type: {crop}")
        raise ValueError(f"Unknown crop type: {crop}")
    return crop


def check_file_path(func=None, *, path_arg_name="path"):
    """Decorator to check if the file path exists."""
    if func is None:
        return lambda func: check_file_path(func, path_arg_name=path_arg_name)

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the path parameter based on its name or position
        path_index = (
            func.__code__.co_varnames.index(path_arg_name)
            if path_arg_name in func.__code__.co_varnames
            else 0
        )
        path = kwargs.get(
            path_arg_name, args[path_index] if path_index < len(args) else None
        )

        # Perform the path checks
        if isinstance(path, str):
            path = Path(path)
        if not isinstance(path, Path):
            raise ValueError(f"Invalid type for path: {type(path)}")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File {path} not found.")

        # Proceed with the original function
        return func(*args, **kwargs)

    return wrapper


def get_crop_dates(crop, folder: Optional[Path] = None) -> Dict[str, str]:
    """获取作物的种植和收获日期。

    Args:
        path: Path, the path to the file.

    Returns:
        tuple, (planting_date, harvesting_date)
    """
    if folder is None:
        logger.debug(f"Loading crops from {CROPS_FOLDER}")
        folder = cast(Path, CROPS_FOLDER)
    with open(folder / f"{crop}.yaml", "r", encoding="utf-8") as file:
        crop = yaml.safe_load(file)
    start_dt: date = crop["start"]
    end_dt: date = crop["end"]
    return {
        "planting_date": start_dt.strftime(r"%m/%d"),
        "harvest_date": end_dt.strftime(r"%m/%d"),
    }


def check_climate_dataframe(df: pd.DataFrame) -> bool:
    """Check if the climate dataframe is valid for AquaCrop.

    Args:
        df: pd.DataFrame, the climate dataframe.

    Raises:
        NameError: if the name of the columns is not valid.
        TypeError: if the type of the columns is not valid.
        TimeoutError: if the time is not monotonic increasing.

    Returns:
        pd.DataFrame, the climate dataframe.
    """
    # 检查列名
    for i, col in enumerate(COLS):
        if col != df.columns[i]:
            raise NameError(f"No. {i} column {df.columns[i]} is not expected ({col}).")
    # 检查时间列
    if not df["Date"].dtype == "datetime64[ns]":
        raise TypeError("Date column must be datetime64[ns]")
    # 检查时间列是否连续
    if not df["Date"].is_monotonic_increasing:
        raise TimeoutError("Date column must be monotonic increasing.")
    return True
