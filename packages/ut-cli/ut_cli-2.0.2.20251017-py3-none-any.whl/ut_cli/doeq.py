# coding=utf-8

from ut_dic.dic import Dic
from ut_obj.str import Str
from ut_obj.strdate import StrDate

from typing import Any
from collections.abc import Callable

TyArr = list[Any]
TyDic = dict[Any, Any]
TyCallable = Any | Callable[..., Any]
TyTup = tuple[Any, Any]
TyStr = str

TnArr = None | TyArr
TnDic = None | TyDic
TnTup = None | TyTup
TnStr = None | TyStr


class DoEq:
    """ Manage Commandline Arguments
    """
    msg1 = "Wrong parameter: {}; valid parameters are: {}"
    msg2 = "Parameter={} value={} is invalid; valid values are={}"

    @classmethod
    def verify_value(cls, value, _type) -> None:
        match _type[0]:
            case '{':
                _range = Str.sh_dic(_type)
                if value not in _range:
                    _msg = cls.msg2.format(value, _range)
                    raise Exception(_msg)
            case '[':
                _range = Str.sh_dic(_type)
                if value not in _range:
                    _msg = cls.msg2.format(value, _range)
                    raise Exception(_msg)

    @classmethod
    def verify_key_value(cls, key, value, d_parms: TyDic) -> TyTup:
        _type: TnStr = d_parms.get(key)
        if _type is None:
            raise Exception(cls.msg1.format(key, d_parms))
        match _type:
            case 'str':
                _value = value
            case 'int':
                _value = int(value)
            case 'bool':
                _value = Str.sh_boolean(value)
            case 'dict':
                value = Str.sh_dic(value)
            case 'list':
                _value = Str.sh_arr(value)
            case '%Y-%m-%d':
                _value = StrDate.sh(value, _type)
            case '_':
                _value = value
                cls.verify_value(_value, _type)
        return key, _value

    @classmethod
    def verify(cls, d_eq: TyDic, d_parms: TnDic) -> TyDic:
        if not d_parms:
            return d_eq

        _cmd = d_eq.get('cmd', [])
        _d_parms = Dic.locate(d_parms, _cmd)

        _d_eq_new = {}
        for _k, _v in d_eq.items():
            _k, _v = cls.verify_key_value(_k, _v, _d_parms)
            _d_eq_new[_k] = _v
        return _d_eq_new
