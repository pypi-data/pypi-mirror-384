# coding=utf-8

from typing import Any
TyArr = list[Any]
TyMod = str
TyPac = str
TyPointPath = str
TyStr = str

TnPac = None | TyPac


class Fnc:

    @staticmethod
    def sh_full_name(fnc) -> TyPointPath:
        # def sh_pacmod_name(fnc) -> TyPacModName:
        """
        show full qualified name of object
        """
        _class = fnc.__class__
        _module: TyPointPath = _class.__module__
        _qualname: TyPointPath = _class.__qualname__
        # Avoid prefixing built-in types
        if _module == "builtins":
            return _qualname
        return f"{_module}.{_qualname}"

    # @staticmethod
    # def sh_mod(fnc) -> TyMod:
    #     # def sh_pacmod_name(fnc) -> TyPacModName:
    #     """
    #     show module name of function
    #     """
    #     _mod: TyMod = fnc.__module__
    #     return _mod

    @staticmethod
    def sh_pac(fnc) -> TyPac:
        # def sh_pac_name(fnc) -> TyModName:
        """
        show module name of function
        """
        _module: TyPac = fnc.__module__
        _a_pac: TyArr = _module.split('.')
        _pac: TyPac = '.'.join(_a_pac[-1])
        return _pac

    @staticmethod
    def sh_pac_first(fnc) -> TnPac:
        # def sh_pac_name(fnc) -> TyModName:
        """
        show module name of function
        """
        _module = fnc.__module__
        _pac: TnPac = _module.split('.', 1)
        return _pac

    @staticmethod
    def sh_pac_last(fnc) -> TnPac:
        # def sh_pac_name(fnc) -> TyModName:
        """
        show module name of function
        """
        _module = fnc.__module__
        _pac: TnPac = _module.rsplit('.', 1)
        return _pac

    # @staticmethod
    # def sh_cls_name(fnc) -> TyClsName:
    #     """
    #     show class name of function
    #     """
    #     if hasattr(fnc, '__qualname__'):
    #         _cls_name: TyClsName = fnc.__qualname__.split('.', 1)
    #     return _cls_name

    # @classmethod
    # def sh_fnc_name(cls, fnc) -> TyFncName:
    #     """
    #     show class name of function
    #     """
    #     _pac: TyPac = cls.sh_pac(cls)
    #     _cls_name = cls.sh_cls_name(fnc)
    #     _fnc_name = '.'.join([_pac, _cls_name])
    #     return _fnc_name
