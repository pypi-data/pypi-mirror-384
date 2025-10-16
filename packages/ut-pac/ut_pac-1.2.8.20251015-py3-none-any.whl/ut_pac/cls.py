# coding=utf-8
from typing import Any

import os
from ut_pac.pac import Pac

TyArr = list[Any]
TyDic = dict[Any, Any]
TyPackage = str
TyModPath = str
TyPacPath = str
TyMod = str
TyPath = str

TnPath = None | TyPath


class Cls:

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
    def sh_path_by_path(cls, path: TyPath) -> TyPath:
        # def sh_aopath_of_pac_by_path(cls, path: TyPath) -> Any:
        """
        show directory
        """
        _package = cls.sh_pac_path(cls)
        _path: TyPath = Pac.sh_path_by_path(_package, path)
        return _path

    @staticmethod
    def sh_path_by_paths(cls, *paths: TyPath) -> TyPath:
        # def sh_aopath_pac_by_paths(cls, *paths: TyPath) -> Any:
        """
        show directory
        """
        _package = cls.sh_pac_path(cls)
        _path: TyPath = os.sep.join(paths)
        _path = Pac.sh_path_by_path(_package, _path)
        return _path
