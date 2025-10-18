from ut_dic.dic import Dic

from typing import Any
TyDic = dict[Any, Any]


class Task:
    """
    Task processor
    """
    @classmethod
    def do(cls, kwargs: TyDic) -> None:
        """
        Execute do method of Task class
        """
        _cls_task = Dic.locate(kwargs, 'cls_task')
        _cls_task.do(kwargs)
