# coding=utf-8
import os
import importlib.resources

from typing import Any

TyArr = list[Any]
TyDic = dict[Any, Any]
TyMod = str
TyPac = str
TyPacPath = str
TyPath = str


class Pac:

    @staticmethod
    def sh_path(pac_path: TyPacPath) -> TyPath:
        _path: TyPath = str(importlib.resources.files(pac_path))
        return _path

    @classmethod
    def sh_path_by_paths_if_exists(
            cls, pac_path: TyPacPath, *paths: TyPath) -> TyPath:
        # def sh_path_by_path_and_prefix(
        """
        show directory
        """
        _path: TyPath = os.path.join(*paths)
        _path = cls.sh_path_by_path_if_exists(pac_path, _path)
        return _path

    @staticmethod
    def sh_path_by_path_if_exists(
            pac_path: TyPacPath, path: TyPath) -> TyPath:
        """ show directory
        """
        _path: TyPath = str(importlib.resources.files(pac_path).joinpath(path))
        if not _path:
            msg = f"path={path} does not exist in pac_path={pac_path}"
            raise Exception(msg)
        if os.path.exists(_path):
            return _path
        msg = f"path={_path} for pac_path={pac_path} does not exist"
        raise Exception(msg)
