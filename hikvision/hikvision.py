import os
import ctypes
import sys
import functools
from .hk_define import *
from .hk_struct import LPNET_DVR_DEVICEINFO_V30, NET_DVR_FOCUSMODE_CFG, NET_DVR_JPEGPARA
from .hikvision_infrared import get_temper_info
import logging

logger = logging.getLogger('HCNetPythonSDK-Linux')
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter(
    fmt='[%(levelname)s] %(asctime)s %(filename)s[%(lineno)d, f%(funcName)s] %(message)s')
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(fmt)
logger.addHandler(stream_handler)


def _release_wrapper(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        print('kwargs', kwargs)
        if kwargs.get('release_resources', True):
            if args[0].user_id != -1:
                args[0]._destroy()
        return res

    return inner


class HIKVisionSDK(object):
    def __init__(self, lib_dir, ip, username, password, port=8000, channel=1, debug=True):
        self.lib_dir = lib_dir
        self.old_cwd = os.getcwd()
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.user_id = -1
        self.hk_so_lib = None
        self.channel = channel
        self.err_code = 0
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def init(self):
        """raise a exception if error"""
        logger.debug('开始改变工作目录 %s' % self.lib_dir)
        os.chdir(self.lib_dir)
        logger.debug('开始加载libhcnetsdk.so')
        self.hk_so_lib = ctypes.cdll.LoadLibrary("./libhcnetsdk.so")
        ok = self.hk_so_lib.NET_DVR_Init()
        if not ok:
            self.err_code = -1
            raise Exception("<<<海康sdk初始化失败")
        self._login()
        return self

    def _login(self):
        logger.debug('开始登录')
        device_info = LPNET_DVR_DEVICEINFO_V30()
        result = self.hk_so_lib.NET_DVR_Login_V30(bytes(self.ip, 'ascii'),
                                                                 self.port,
                                                                 bytes(self.username, 'ascii'),
                                                                 bytes(self.password, 'ascii'),
                                                                 ctypes.byref(device_info))
        if result == -1:
            error_num = self.hk_so_lib.NET_DVR_GetLastError()
            self.err_code = error_num
            self._destroy(logout=False)
            raise Exception("<<<海康SDK调用错误 ERRCODE: %s" % error_num)
        self.user_id = result

    def _destroy(self, logout=True):
        if logout:
            logger.debug('>>>开始注销资源')
            res = self.hk_so_lib.NET_DVR_Logout(self.user_id)
            if not res:
                logger.warning('<<<User退出失败')
        logger.debug('>>>开始释放资源')
        res = self.hk_so_lib.NET_DVR_Cleanup()
        if not res:
            logger.warning('<<<释放资源失败')
        os.chdir(self.old_cwd)
        logger.debug('>>>成功还原工作目录 %s' % os.getcwd())

    @_release_wrapper
    def take_picture(self, pic_pathname, release_resources=True) -> bool:
        if self.user_id == -1:
            logger.debug('未初始化或者初始化失败')
            return False
        logger.debug('开始拍照 %s' % pic_pathname)
        obj = NET_DVR_JPEGPARA()
        result = self.hk_so_lib.NET_DVR_CaptureJPEGPicture(self.user_id,
                                                           self.channel,
                                                           ctypes.byref(obj),
                                                           bytes(pic_pathname, 'utf-8'))

        if not result:
            error_num = self.hk_so_lib.NET_DVR_GetLastError()
            logger.warning('<<<拍照失败 ERRCODE: %s' % error_num)
            return False
        return True

    @_release_wrapper
    def get_zoom(self, release_resources=True) -> int:
        """-1 if failure"""
        if self.user_id == -1:
            logger.debug('<<<未初始化或者初始化失败 user_id %s' % self.user_id)
            return False
        struct_cfg = NET_DVR_FOCUSMODE_CFG()
        dw_returned = ctypes.c_uint16(0)
        result = self.hk_so_lib.NET_DVR_GetDVRConfig(self.user_id,
                                                     NET_DVR_GET_FOCUSMODECFG,
                                                     self.channel,
                                                     ctypes.byref(struct_cfg),
                                                     255,
                                                     ctypes.byref(dw_returned))
        if not result:
            logger.warning('<<<获取变焦失败')
            return -1
        return struct_cfg.fOpticalZoomLevel

    @_release_wrapper
    def set_zoom(self, zoom, release_resources) -> bool:
        if self.hk_so_lib == -1:
            logger.debug('<<<未初始化或者初始化失败')
            return False
        logger.debug('开始设置变倍 zoom %s' % zoom)
        struct_cfg = NET_DVR_FOCUSMODE_CFG()
        dw_returned = ctypes.c_uint16(0)
        result = self.hk_so_lib.NET_DVR_GetDVRConfig(self.user_id,
                                                     NET_DVR_GET_FOCUSMODECFG,
                                                     self.channel,
                                                     ctypes.byref(struct_cfg),
                                                     255,
                                                     ctypes.byref(dw_returned))
        if not result:
            logger.warning('<<<获取变倍失败')
            return False
        cur_zoom = struct_cfg.fOpticalZoomLevel
        logger.debug("当前变倍值为 %s " % cur_zoom)

        if cur_zoom == zoom:
            logger.debug('已经是相同的倍值')
            return True

        struct_cfg.fOpticalZoomLevel = zoom
        result = self.hk_so_lib.NET_DVR_SetDVRConfig(self.user_id,
                                                     NET_DVR_SET_FOCUSMODECFG,
                                                     self.channel,
                                                     ctypes.byref(struct_cfg),
                                                     255)
        if not result:
            print('<<<变倍失败')
            return False
        logger.debug('变倍成功 %s' % zoom)
        return True

    def get_infrared_value(self) -> tuple:
        os.chdir(self.lib_dir)
        logger.debug('开始获取红外')
        try:
            min_temper, max_temper, aver_temp = get_temper_info(ip=self.ip, username=self.username, password=self.password)
        except Exception as e:
            logger.error(e)
            min_temper, max_temper, aver_temp = -1, -1, -1
        logger.debug(" min_temper {0}, max_temper {1}, aver_temp {2}".format(min_temper, max_temper, aver_temp))
        os.chdir(self.old_cwd)
        return min_temper, max_temper, aver_temp
