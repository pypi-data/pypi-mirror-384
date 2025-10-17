import logging

from hopara.filter import Filter
from hopara.hopara import Hopara
from hopara.table import Table
from hopara.view import View
from hopara.type import ColumnType, TypeParam

_log = None


def init_logger():
    global _log
    if _log is None:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        _log = logging.getLogger('pyhopara')
        _log.addHandler(handler)
        _log.setLevel(logging.INFO)
    return _log


init_logger()
