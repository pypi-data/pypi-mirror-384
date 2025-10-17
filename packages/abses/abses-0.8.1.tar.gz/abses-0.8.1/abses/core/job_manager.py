#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Type

import pandas as pd

if TYPE_CHECKING:
    from abses.core.protocols import MainModelProtocol

    from .experiment import HookFunc


class ExperimentManager:
    """管理所有实验结果的单例类"""

    _instance = None
    model_cls: Type[MainModelProtocol]

    def __new__(cls, model_cls: Type[MainModelProtocol]):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model_cls = model_cls
        return cls._instance

    def __init__(self, model_cls: Type[MainModelProtocol]):
        if self.model_cls is not model_cls:
            raise TypeError(
                f"{self.__class__.__name__} is set, trying to initialize {model_cls.__name__} experiment."
            )
        if not hasattr(self, "_datasets"):
            # Each item should be a row-like mapping/Series to build a DataFrame
            self._datasets: Dict[Tuple[int, int], Dict[str, Any]] = {}
            self._seeds: Dict[Tuple[int, int], Optional[int]] = {}
            self._overrides: Dict[Tuple[int, int], Dict[str, Any]] = {}
            self._hooks: Dict[str, HookFunc] = {}

    @property
    def hooks(self) -> Dict[str, HookFunc]:
        """获取所有钩子"""
        return self._hooks

    @property
    def index(self) -> pd.MultiIndex:
        """获取所有实验结果的索引"""
        return pd.MultiIndex.from_tuples(
            self._datasets.keys(), names=["job_id", "repeat_id"]
        )

    def clean(self) -> None:
        """清理所有实验"""
        self._datasets.clear()
        self._seeds.clear()
        self._overrides.clear()

    def update_result(
        self,
        key: Tuple[int, int],
        overrides: Dict[str, Any],
        datasets: Dict[str, Any],
        seed: Optional[int] = None,
    ) -> None:
        """更新实验结果

        Args:
            key: (job_id, repeat_id) tuple
            overrides: Configuration overrides for this run
            datasets: Row-like mapping of metrics/values to store
            seed: Random seed used for this run
        """
        self._datasets[key] = datasets
        self._seeds[key] = seed
        self._overrides[key] = overrides

    def dict_to_df(self, results: dict) -> pd.DataFrame:
        """将嵌套字典转换为 DataFrame

        Args:
            results: 形如 {(job_id, repeat_id): {'metric': value}} 的字典

        Returns:
        包含 job_id, repeat_id 和指标值的 DataFrame
        """
        return pd.DataFrame(results.values(), index=self.index)

    def get_datasets(
        self,
        seed: bool = True,
    ) -> pd.DataFrame:
        """获取所有实验结果的 DataFrame"""
        to_concat = []
        to_concat.append(self.dict_to_df(self._overrides))
        if seed:
            seed = pd.Series(self._seeds, name="seed", index=self.index)
            to_concat.append(seed)
        to_concat.append(self.dict_to_df(self._datasets))
        return pd.concat(to_concat, axis=1).reset_index()

    def add_a_hook(
        self,
        hook_func: HookFunc,
        hook_name: Optional[str] = None,
    ) -> None:
        """Add a hook to the experiment."""
        if hook_name is None:
            hook_name = hook_func.__name__
        if hook_name in self._hooks:
            raise ValueError(f"Hook {hook_name} already exists.")
        if not callable(hook_func):
            raise TypeError("hook_func must be a callable.")
        self._hooks[hook_name] = hook_func
