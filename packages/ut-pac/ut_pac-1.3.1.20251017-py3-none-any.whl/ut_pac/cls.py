# coding=utf-8
from typing import Any

from ut_pac.pac import Pac

TyArr = list[Any]
TyObjPath = str
TyModPath = str
TyPacPath = str
TyModule = str
TyModName = str
TyPath = str

TnPath = None | TyPath


class Cls:

    @staticmethod
    def sh_pac_path(cls) -> TyPacPath:
        _module: TyModule = cls.__module__
        _a_module: TyArr = _module.split('.')
        # Exclude the module itself)
        # Extract package and subpackages from the module name
        _path: TyObjPath = '.'.join(_a_module[:-1])
        return _path

    @staticmethod
    def sh_mod_path(cls) -> TyModPath:
        _module: TyModule = cls.__module__
        return _module

    @staticmethod
    def sh_mod_name(cls) -> TyModName:
        _module: TyModule = cls.__module__
        _mod_name: TyModName = _module.rsplit('.', 1)[0]
        return _mod_name

    @staticmethod
    def sh_path_by_paths_if_exists(cls, *paths: TyPath) -> TyPath:
        """
        show path
        """
        _pac_path: TyPacPath = cls.sh_pac_path(cls)
        _path: TyPath = Pac.sh_path_by_path_if_exists(_pac_path, *paths)
        return _path

    @staticmethod
    def sh_path_by_path_if_exists(cls, path: TyPath) -> TyPath:
        """
        show path
        """
        _pac_path: TyPacPath = cls.sh_pac_path(cls)
        _path: TyPath = Pac.sh_path_by_path_if_exists(_pac_path, path)
        return _path
