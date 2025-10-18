import os
import time
import calendar
from datetime import datetime
import pytz
import logging
import logging.config
from logging import Logger
import psutil

from ut_dic.dic import Dic
from ut_ioc.jinja2_ import Jinja2_
from ut_pac.cls import Cls
from ut_pac.aopac import AoPac

from typing import Any
from collections.abc import Callable

TyAny = Any
TyArr = list[Any]
TyBool = bool
TyCallable = Callable[..., Any]
TyDateTime = datetime
TyDic = dict[Any, Any]
TyDir = str
TyLogger = Logger
TyPath = str
TyStr = str
TyTimeStamp = int

TnAny = None | Any
TnArr = None | TyArr
TnBool = None | bool
TnDic = None | TyDic
TnPath = None | TyPath
TnDateTime = None | TyDateTime
TnTimeStamp = None | TyTimeStamp


class Utils:

    @staticmethod
    def sh_calendar_ts(kwargs) -> TyTimeStamp:
        """Set static variable log level in log configuration handlers
        """
        _log_ts_type = kwargs.get('log_ts_type', 'ts')
        match _log_ts_type:
            case 'ts':
                return calendar.timegm(time.gmtime())
            case 'dt':
                # Example Unix timestamp (seconds since 1970-01-01 00:00:00 UTC)
                _timestamp = calendar.timegm(time.gmtime())
                # Convert timestamp to a naive datetime object in UTC
                _utc_time = datetime.utcfromtimestamp(_timestamp)
                # Localize the datetime object to UTC
                _utc_time = pytz.utc.localize(_utc_time)
                # Convert to a specific timezone (e.g., Europe/Berlin)
                _timezone = pytz.timezone('Europe/Berlin')
                localized_time = int(_utc_time.astimezone(_timezone).timestamp())
                return localized_time
            case _:
                return calendar.timegm(time.gmtime())

    @classmethod
    def sh_dir_run(cls, kwargs: TyDic) -> TyPath:
        """
        Show dir_run
        """
        _app_data: str = kwargs.get('app_data', '/data')
        _tenant: str = kwargs.get('tenant', '')
        _nms_pac_path = Dic.locate_key(kwargs, 'nms_pac_path')
        _username = cls.sh_username(kwargs)
        _cmd: TyStr = kwargs.get('cmd', '')
        _path: TyPath = os.path.join(
                _app_data, _tenant, 'RUN', _nms_pac_path, _username, *_cmd)
        return _path

    @classmethod
    def sh_d_dir_run(cls, kwargs) -> TyDic:
        """
        Read log file path with jinja2
        """
        _dir_run = cls.sh_dir_run(kwargs)
        if kwargs.get('log_sw_single_dir', True):
            _d_dir_run: TyDic = {
                    'dir_run_debs': f"{_dir_run}/debs",
                    'dir_run_infs': f"{_dir_run}/logs",
                    'dir_run_wrns': f"{_dir_run}/logs",
                    'dir_run_errs': f"{_dir_run}/logs",
                    'dir_run_crts': f"{_dir_run}/logs",
            }
        else:
            _d_dir_run = {
                    'dir_run_debs': f"{_dir_run}/debs",
                    'dir_run_infs': f"{_dir_run}/infs",
                    'dir_run_wrns': f"{_dir_run}/wrns",
                    'dir_run_errs': f"{_dir_run}/errs",
                    'dir_run_crts': f"{_dir_run}/crts",
            }
        return _d_dir_run

    @classmethod
    def sh_d_log_cfg(cls, kwargs: TyDic, log) -> TyDic:
        """Read log file path with jinja2
        """
        _d_dir_run = cls.sh_d_dir_run(kwargs)
        if kwargs.get('log_sw_mkdirs', True):
            aopath: TyArr = list(_d_dir_run.values())
            for _path in aopath:
                os.makedirs(_path, exist_ok=True)

        _path_log_cfg = cls.sh_path_log_cfg(kwargs)
        _module = Dic.locate(kwargs, 'app_mod_name')
        _pid = os.getpid()
        _ts = cls.sh_calendar_ts(kwargs)

        _d_log_cfg: TyDic = Jinja2_.read(
                _path_log_cfg, module=_module, pid=_pid, ts=_ts, **_d_dir_run)
        _level = cls.sh_level(kwargs)
        _log_type = kwargs.get('log_type', 'std')
        logger_name = _log_type
        _d_log_cfg['handlers'][f"{logger_name}_debug_console"]['level'] = _level
        _d_log_cfg['handlers'][f"{logger_name}_debug_file"]['level'] = _level

        return _d_log_cfg

    @classmethod
    def sh_path_log_cfg(cls_log, kwargs: TyDic) -> TyPath:
        """ show directory
        """
        _app_pac_path = Dic.locate_key(kwargs, 'app_pac_path')
        _log_pac_path = Cls.sh_pac_path(cls_log)
        _a_pac_path = [_app_pac_path, _log_pac_path]
        _log_type = kwargs.get('log_type', 'std')
        _path: TyPath = os.path.join('cfg', f"log.{_log_type}.yml")
        _path = AoPac.sh_path_by_path_if_exists(_a_pac_path, _path)
        return _path

    @staticmethod
    def sh_level(kwargs) -> int:
        _sw_debug = kwargs.get('sw_debug', False)
        if _sw_debug:
            return logging.DEBUG
        else:
            return logging.INFO

    @staticmethod
    def sh_username(kwargs: TyDic) -> str:
        """
        Show username
        """
        _log_type = kwargs.get('log_type', 'std')
        if _log_type == "usr":
            _username: str = psutil.Process().username()
        else:
            _username = ''
        return _username
