# coding=utf-8
import os
import importlib.resources

from typing import Any

TyArr = list[Any]
TyDic = dict[Any, Any]
TyModPath = str
TyMod = str
TyPac = str
TyPacPath = str
TyPath = str


class Pac:

    @staticmethod
    def sh_pac_path(cls) -> TyPacPath:
        _mod_path: TyModPath = cls.__module__
        _pac_path: TyPacPath = _mod_path.rsplit('.', 1)[0]
        return _pac_path

    @staticmethod
    def sh_mod_path(cls) -> TyModPath:
        _mod_path: TyModPath = cls.__module__
        return _mod_path

    @staticmethod
    def sh_mod(cls) -> TyMod:
        _mod_path: TyModPath = cls.__module__
        _mod: TyMod = _mod_path.split('.', 1)[0]
        return _mod

    @staticmethod
    def sh_path(pac_path: TyPac) -> TyPath:
        _path: TyPath = str(importlib.resources.files(pac_path))
        return _path

    @classmethod
    def sh_path_by_path_and_prefix(
            cls, pac_path: TyPac, path: TyPath, prefix: TyPath = ''
    ) -> TyPath:
        """
        show directory
        """
        _path: TyPath = os.path.join(prefix, path)
        _path = cls.sh_path_by_path(pac_path, _path)
        return _path

    @staticmethod
    def sh_path_by_path(
            pac_path: TyPac, path: TyPath) -> TyPath:
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
