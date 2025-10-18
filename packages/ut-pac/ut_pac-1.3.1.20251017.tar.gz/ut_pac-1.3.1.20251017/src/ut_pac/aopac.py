# coding=utf-8
from typing import Any

import os

from ut_pac.pac import Pac

TyArr = list[Any]
TyDic = dict[Any, Any]
TyPac = str
TyPath = str
TyAoPac = str | list[str]
TyAoPath = list[TyPath]

TnPath = None | TyPath


class AoPac:

    @staticmethod
    def sh_path_by_path_if_exists(
            aopac: TyAoPac, path: TyPath) -> TyPath:
        if not isinstance(aopac, (list, tuple)):
            _aopac = [aopac]
        else:
            _aopac = aopac
        _aopath : TyAoPath = []
        for _pac in _aopac:
            _path: TyPath = Pac.sh_path_by_path(_pac, path)
            if os.path.exists(_path):
                return _path
            _aopath.append(_path)
        msg = f"No path in array _aopath={_aopath} exists"
        raise Exception(msg)

    @staticmethod
    def sh_aopath_by_path(
            aopac: TyAoPac, path: TyPath) -> TyAoPath:
        if not isinstance(aopac, list):
            _aopac = [aopac]
        else:
            _aopac = aopac
        _aopath: TyAoPath = []
        for _pac in _aopac:
            _path = Pac.sh_path_by_path(_pac, path)
            _aopath.append(_path)
        return _aopath

    @classmethod
    def sh_aopath_by_paths(
            cls, aopac: TyAoPac, *paths: TyPath) -> TyAoPac:
        """
        Show the array of paths created by the array of packages
        and the given path extended by the given prefix.
        """
        _path: TyPath = os.path.join(*paths)
        _aopath: TyAoPath = cls.sh_aopath_by_path(aopac, _path)
        return _aopath
