# coding=utf-8
from typing import Any

TyArr = list[Any]
TyDic = dict[Any, Any]
TyStr = str


class AoEq:
    """ Manage Array of Equates
    The static Class ``AoEq`` contains no variables and the subsequent methods
    to manage array of equates. Equates are statements which consist of a key,
    value string pair separated by the equate character '='.
    """
    @classmethod
    def sh_d_eq(cls, a_eq: TyArr) -> TyDic:
        """
        The show method ``sh_d_eq`` create a dictionary of equates: the keys
        are the equate keys; the values are the equate values.
        For the key 'cmd' the value is an array which represents the command
        and his nested sub-commands created by splitting the value.
        """
        _d_eq: TyDic = {}
        for eq in a_eq:
            _a_kv: TyArr = eq.split('=')
            _k = _a_kv[0]
            _v = _a_kv[1]
            if _k == 'cmd':
                _d_eq[_k] = _v.split()
            else:
                _d_eq[_k] = _v
        return _d_eq
