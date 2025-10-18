import importlib
import datetime

from ut_dic.dic import Dic
from ut_cli.aoeq import AoEq
from ut_cli.doeq import DoEq
from ut_pac.cls import Cls
from ut_pac.pac import Pac

from typing import Any
TyAny = Any
TyArr = list[Any]
TyDic = dict[Any, Any]
TyPath = str
TyTup = tuple[Any, Any]

TnDic = None | TyDic
TnTup = tuple[None | Any, None | Any]


class Kwargs:
    """
    Keyword arguments processor
    """
    @staticmethod
    def sh_t_parms_task(cls_app, d_eq: TyDic) -> TyTup:
        if hasattr(cls_app, 'd_cmd2pac'):
            _cmd = Dic.locate(d_eq, 'cmd')
            _pac_path = Dic.locate(cls_app.d_cmd2pac, _cmd[0])
        else:
            _pac_path = Pac.sh_pac_path(cls_app)

        _pac_parms_path = f"{_pac_path}.parms"
        _pac_task_path = f"{_pac_path}.task"
        _parms = importlib.import_module(_pac_parms_path)
        _task = importlib.import_module(_pac_task_path)
        _t_parms_task: TyTup = (_parms.Parms, _task.Task)
        return _t_parms_task

    @classmethod
    def sh(cls, cls_com, cls_app, sys_argv: TyArr) -> TyDic:
        """
        show keyword arguments
        """
        _args = sys_argv[1:]
        _d_eq: TyDic = AoEq.sh_d_eq(_args)
        _cls_parms, _cls_task = cls.sh_t_parms_task(cls_app, _d_eq)
        if _cls_parms is not None:
            _d_parms = _cls_parms.d_parms
        else:
            _d_parms = None

        _kwargs: TyDic = DoEq.verify(_d_eq, _d_parms)
        _sh_prof = _kwargs.get('sh_prof')
        if callable(_sh_prof):
            _kwargs['sh_prof'] = _sh_prof()
        _kwargs['com'] = cls_com
        _kwargs['cls_app'] = cls_app
        _kwargs['cls_parms'] = _cls_parms
        _kwargs['cls_task'] = _cls_task

        _com_pac_path = Cls.sh_pac_path(cls_com)
        _nms_pac_path = Cls.sh_pac_path(cls_app)
        _app_pac_path = Cls.sh_pac_path(_cls_parms)
        _app_mod_name = Cls.sh_mod_namw(_cls_parms)

        _kwargs['com_pac_path'] = _com_pac_path
        _kwargs['nms_pac_path'] = _nms_pac_path
        _kwargs['app_pac_path'] = _app_pac_path
        _kwargs['app_mod_name'] = _app_mod_name

        _kwargs['com_pac_fpath'] = Pac.sh_path(_com_pac_path)
        _kwargs['nms_pac_fpath'] = Pac.sh_path(_nms_pac_path)
        _kwargs['app_pac_fpath'] = Pac.sh_path(_app_pac_path)

        _kwargs['now'] = datetime.datetime.now().strftime("%Y%m%d")

        return _kwargs
