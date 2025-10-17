import pathlib
import platform
import re
import shutil
import typing
from typing import Tuple, Union, List, Any
import adbutils
import numpy as np
from haitest.device import HMDriver, AndroidDriver, WebDriver
from haitest.device.device import HaitestGesture

if platform.system().lower() == 'darwin':
    import tidevice
    from haitest.device import IOSDriver
    from tidevice import ConnectionType

from haitest.utils.event import StopEvent
from haitest.utils.param import OSType, DriverType, DeviceButton, AppInfo
from haitest.device import Device
from hypium.utils.shell import run_command

from haitest.utils.ppocr.ocr_struct import pred_to_row
from haitest.utils.ppocr.ppocr import detect_and_ocr
from haitest import register_tencent_log_parser

GL_DEVICE: Device = None
"""General API"""


def init_driver(
        os_type: OSType = None,
        udid: str = None, **kwargs):
    """初始化设备驱动及环境.

    Args:
        os_type (OSType): 设备系统，安卓为OSType.ANDROID，iOS为OSType.IOS
        udid (str): 设备ID
        **kwargs: 脚本执行产出路径的修改等

    """
    register_tencent_log_parser(udid)
    global GL_DEVICE
    if os_type is OSType.HM:
        GL_DEVICE = HMDriver(udid, **kwargs)
    elif os_type is OSType.ANDROID:
        GL_DEVICE = AndroidDriver(udid, **kwargs)
    elif os_type is OSType.IOS:
        if platform.system().lower() == 'darwin':
            GL_DEVICE = IOSDriver(udid, **kwargs)
            GL_DEVICE.start_cloudphone()
        else:
            return None
    elif os_type is OSType.WEB:
        GL_DEVICE = WebDriver(udid, **kwargs)
    else:
        return None
    return GL_DEVICE


def hdc_find_device():
    """ 【鸿蒙】通过hdc查找可用的鸿蒙设备

    Args:
        无
    Returns:
        list: hdc返回的鸿蒙设备列表，每个元素含有以下属性 [udid、conn_type、status]

    """
    if shutil.which("hdc_std"):
        cmd = "hdc_std"
    elif shutil.which("hdc"):
        cmd = "hdc"
    else:
        return [], "harmony: No hdc/hdc_std command found"
    result = run_command(f"{cmd} list targets")
    if "Empty" in result:
        return [], ""
    devices = result.strip().splitlines()
    ret = []
    for device in devices:
        infos = device.strip().split()
        if len(infos) == 1:
            ret.append({"udid": infos[0].strip(), "conn_type": "usb", "status": "device"})
        elif len(infos) == 2:
            ret.append({"udid": infos[0].strip(), "conn_type": "usb", "status": infos[1].strip()})

    return ret, ''


def adb_find_device():
    """ 【Andoird】通过adb查找可用的安卓设备

    Args:
        无
    Returns:
        list: adb返回的安卓设备列表，每个元素含有以下属性 [udid、conn_type、status]

    """
    with adbutils.adb._connect() as c:
        c.send_command("host:devices")
        c.check_okay()
        output = c.read_string_block()
        device_list = []
        for line in output.splitlines():
            parts = line.strip().split("\t")
            if len(parts) != 2:
                continue
            device_list.append({"udid": parts[0], "conn_type": "usb", "status": parts[1]})
    return device_list


def tidevice_find_device():
    """ 【iOS】通过tidevice查找可用的苹果设备

    Args:
        无
    Returns:
        list: tidevice返回的ios设备列表，每个元素含有以下属性 [udid、conn_type、status]

    """
    devices = []
    if platform.system().lower() == 'darwin':
        ios_devices = tidevice.Device()._usbmux.device_list()
        devices = [{"udid": device.udid,
                    "conn_type": "usb" if device.conn_type == ConnectionType.USB else "network",
                    "status": "device"} for device in ios_devices]
    return devices


def device_list(os_type: OSType):
    """ 获取已连接的对应平台的设备的列表

    Args:
        os_type: 类型OSType，常用值:OSType.IOS, OSType.ANDROID, OSType.HM
    Returns:
        list: 返回的对应类型的设备列表，每个元素含有以下属性 [udid、conn_type、status]
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_udid",
            "method": "device_list",
        }
    """
    if os_type is OSType.HM:
        devices, msg = hdc_find_device()
        msg = "harmony ：No device to connect" if not devices and not msg else msg
        return devices, msg
    elif os_type is OSType.ANDROID:
        devices = adb_find_device()
        msg = "android ：No device to connect" if not devices else ''
    elif os_type is OSType.IOS:
        devices = tidevice_find_device()
        msg = "ios ：No device to connect" if not devices else ''
    else:
        devices = []
        msg = 'os_type={} not supported'.format(os_type)

    return devices, msg


def get_os_type() -> OSType:
    """返回设备类型.

    Args:

    Returns:
        OSType: 设备类型
    """
    global GL_DEVICE
    return GL_DEVICE.get_os_type()


def install_app(app_path: str, need_resign=False, resign_bundle="") -> bool:
    """安装应用.

    Args:
        app_path (str): 安装包路径
        need_resign (bool): 可缺省, 默认为False。只有ios涉及，需要重签名时传入True
        resign_bundle (str): 可缺省, 默认为空。只有ios涉及，need_resign为True时，此参数必须传入非空的bundleId
    Returns:
        bool: 安装是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_udid",
            "method": "install_app",
            "app_path": "/path/to/your/apk"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.install_app(app_path, need_resign, resign_bundle)


def uninstall_app(pkg: str) -> bool:
    """卸载应用.

    Args:
        pkg (str): 被卸载应用的包名，android和鸿蒙为应用的packageName,ios则对应为bundleid
    Returns:
        bool: 卸载是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_udid",
            "method": "uninstall_app",
            "pkg": "com.your.app.bundle.id"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.uninstall_app(pkg)


def start_app(pkg: str, clear_data: bool = False, **kwargs) -> bool:
    """启动应用.

    Args:
        pkg (str): iOS为应用bundle id，Android和鸿蒙对应为包名
        clear_data (bool): 可缺省，默认为False。仅android相关，清除应用数据
    Returns:
        bool: 启动是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_udid",
            "method": "start_app",
            "pkg": "com.your.app.bundle.id"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.start_app(pkg, clear_data=clear_data, **kwargs)


def restart_app(pkg: str, **kwargs) -> bool:
    """重启应用.

    Args:
        pkg (str): iOS系统为被重启应用的bundleId,android和鸿蒙对应为应用的包名
    Returns:
        bool: 重启是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_udid",
            "method": "restart_app",
            "pkg": "com.your.app.bundle.id"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.restart_app(pkg, **kwargs)


def stop_app(pkg: str) -> bool:
    """结束应用.

    Args:
        pkg (str): iOS系统为被结束应用的bundleId,android和鸿蒙对应为应用的包名
    Returns:
        bool: 结束是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_udid",
            "method": "stop_app",
            "pkg": "com.your.app.bundle.id"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.stop_app(pkg)


def current_app() -> str:
    """获取当前应用.
    Args:
        无
    Returns:
        str: 当前ios应用bundleid，android应用的packageName
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_udid",
            "method": "current_app"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.current_app()


def clear_safari(close_pages: bool = False) -> bool:
    """【Deprecated】清除iOS设备Safari历史缓存数据

    Args:
        close_pages(bool): 仅ios可用，为True则关闭Safari的所有页面
    Returns:
        bool: 是否清除成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_udid",
            "method": "clear_safari"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.clear_safari(close_pages)


def click_pos(pos: Union[list, tuple], duration: Union[int, float] = 0.05, times: int = 1):
    """坐标点击.

    Args:
        pos (tuple or list): 相对坐标，取值区间[0, 1.0]
        duration (int or float): 点击持续时间，可缺省，默认0.05秒，单位为秒
        times (int): 点击次数，可缺省，默认1次，传入2可实现双击效果
    Return:
        bool: 点击是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "click_pos",
            "pos": [0.14, 0.95],
            "duration": 0.5,
            "times": 2,
        }
    """
    global GL_DEVICE
    return GL_DEVICE.click_pos(pos, duration=duration, times=times)


def slide_pos(
        pos_from: Union[tuple, list],
        pos_to: Union[tuple, list] = None,
        pos_shift: Union[tuple, list] = None,
        down_duration: Union[int, float] = 0,
        up_duration: Union[int, float] = 0,
        velocity: Union[int, float] = 0.01):
    """坐标滑动.

    Args:
        pos_from (tuple or list): 滑动起始坐标
        pos_to (tuple or list): 滑动结束坐标，为None时则根据pos_shift滑动
        pos_shift (tuple or list): 滑动偏移距离
        down_duration (int or float): 起始位置按下时长（s），以实现拖拽功能(仅android和鸿蒙生效)
        up_duration (int or float): 移动后等待时长（s），以实现摇杆移动功能(仅android和鸿蒙生效)
        velocity (int or float): 移动间隔，以控制移动速度(Android)
    Return:
        bool: 滑动是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "slide_pos",
            "pos_from": [0.15, 0.50],
            "pos_to": [0.85, 0.50],
            "pos_shift": [0.0, 0.0],
            "down_duration": 0.5,
            "up_duration": 0.5,
            "velocity": 0.1
        }

    """

    global GL_DEVICE
    return GL_DEVICE.slide_pos(pos_from, pos_to=pos_to, pos_shift=pos_shift, down_duration=down_duration,
                               up_duration=up_duration, velocity=velocity)


def inject_gesture(gesture: HaitestGesture):
    """
    @func 执行自定义滑动手势操作
    @param gesture: 描述手势操作的Gesture对象
    @param speed: 默认操作速度, 当生成Gesture对象的某个步骤中没有传入操作时间的默认使用该速度进行操作
    @example:   # 创建一个gesture对象
                gesture = HaitestGesture()
                # 获取控件计算器的位置
                pos = = driver.findComponent(BY.text("计算器")).getBoundsCenter()
                # 获取屏幕尺寸
                size = driver.getDisplaySize()
                # 起始位置, 长按2秒
                gesture.start(pos.to_tuple(), 2)
                # 移动到屏幕边缘 停留2秒
                gesture.move(Point(size.X - 20, int(size.Y / 2)).to_tuple(), 2)
                # 移动到(360, 500)的位置 停留2秒结束
                gesture.move(Point(360, 500).to_tuple(), 2)
                # 执行gesture对象描述的操作
                haitest.api.inject_gesture(gesture)
    """
    global GL_DEVICE
    return GL_DEVICE.inject_gesture(gesture)


def get_img() -> np.ndarray:
    """获取设备当前画面.

    Args:
        无
    Returns:
        ndarray: 画面图像的numpy数组
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "get_img",
        }

    """
    global GL_DEVICE
    return GL_DEVICE.get_img()


def rel2abs(pos: Union[tuple, list]) -> List[int]:
    """相对坐标转换为绝对坐标.

    Args:
        pos (tuple or list): 相对坐标
    Returns:
        tuple: 绝对坐标
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "rel2abs",
            "pos": [0.12, 0.34]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.rel2abs(pos)


def abs2rel(pos: Union[tuple, list]) -> List[int]:
    """绝对坐标转换为相对坐标.

    Args:
        pos (tuple or list): 绝对坐标
    Returns:
        tuple: 相对坐标
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "abs2rel",
            "pos": [120, 340]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.abs2rel(pos)


def open_url(url: str) -> bool:
    """
    [仅android和鸿蒙]通过url执行快捷操作，实现通过url跳转到特定界面

    Args:
        url (str): 待跳转界面的url
    Returns:
        bool: 是否跳转成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "open_url",
            "url": "input_your_url",
        }
    """
    global GL_DEVICE
    return GL_DEVICE.open_url(url)


def find_cv(
        tpl: Union[np.ndarray, str],
        img: Union[np.ndarray, str] = None,
        timeout: int = 30,
        threshold: float = 0.8,
        pos: Union[tuple, list] = None,
        pos_weight: float = 0.05,
        ratio_lv: int = 21,
        is_translucent: bool = False,
        to_gray: bool = False,
        tpl_l: Union[np.ndarray, str] = None,
        deviation: Union[tuple, list] = None,
        time_interval: float = 0.5, **kwargs) -> Tuple:
    """基于多尺寸模板匹配的图像查找.

    Args:
        tpl (ndarray or str): 待匹配查找的目标图像
        img (ndarray or str): 在该图上进行查找，为None时则获取当前设备画面
        timeout (int): 查找超时时间
        threshold (float): 匹配阈值 (0-1.0)
        pos (tuple or list): 目标图像的坐标，以辅助定位图像位置
        pos_weight (float): 坐标辅助定位的权重
        tpl_l (ndarray or str): 备选的尺寸更大的目标图像，以辅助定位
        deviation (tuple or list): 偏差，目标及备选目标间的偏差
        ratio_lv (int): 缩放范围，数值越大则进行更大尺寸范围的匹配查找
        is_translucent (bool): 目标图像是否为半透明，为True则会进行图像预处理
        to_gray (bool): 是否将图像转换为灰度图
        time_interval(float): 循环查找的时间间隔，默认为0.5s
    Returns:
        list: 查找到的坐标，未找到则返回None
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "find_cv",
            "tpl": "input_your_template_img",
            "img": "your_screenshot_img",
            "threshold": 0.85
        }

    """
    global GL_DEVICE
    return GL_DEVICE.find_cv(tpl, img=img, timeout=timeout, threshold=threshold, pos=pos, pos_weight=pos_weight,
                             ratio_lv=ratio_lv, is_translucent=is_translucent, to_gray=to_gray, tpl_l=tpl_l,
                             deviation=deviation, time_interval=time_interval)


def find_ocr(
        word: str,
        left_word: str = None,
        right_word: str = None,
        timeout: int = 30,
        time_interval: float = 0.5,
        **kwargs) -> Tuple:
    """基于OCR文字识别的查找.

    Args:
        word (str): 待查找文字
        right_word (str): 待查找文字右侧文字
        left_word (str): 待查找文字左侧文字
        timeout (int): 查找超时时间
        time_interval(float): 循环查找的时间间隔，默认为0.5s
        **kwargs: 其他扩展参数，full_match (Boolean): 是否完全匹配。默认True
    Returns:
        list: 查找到的中心点坐标
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "find_ocr",
            "word": "主页"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.find_ocr(word, left_word=left_word, right_word=right_word,
                              timeout=timeout, time_interval=time_interval, **kwargs)


def get_text(img: str, iou_th=0.1) -> list:
    """查找图像中的所有文本.

    Args:
        img (str): 待识别的图像
        text_type (str): OCR识别的文本类型，"ch"为中英文，"en"为英文
        iou_th: 行分割阈值
    Returns:
        list: 查找到的文本结果。列表中元素如
        [[[127.0, 242.0], [201.0, 242.0], [201.0, 261.0], [127.0, 261.0]], ['注册/登录', 0.96725357]]，
        分别为左上、右上、右下、左下点坐标及识别结果与匹配度

    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "get_text",
            "img": "imgbase64str or ndarray object"
        }

    """
    text_list = detect_and_ocr(img)
    rows = pred_to_row(text_list, iou_th)
    for row in rows:
        print(row)

    return rows


def find_ui(xpath: str, timeout: int = 30, **kwargs) -> Tuple:
    """基于控件查找.

    Args:
        xpath (str): 控件xpath
        timeout (int): 查找超时时间
        **kwargs: 其他扩展参数，full_match (Boolean): 是否完全匹配。默认True
    Returns:
        list: 查找到的中心点坐标
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "find_ui",
            "xpath": "//XCUIElementTypeIcon[@label='天气']"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.find_ui(xpath, timeout=timeout, **kwargs)


def find(loc, by: DriverType = DriverType.UI, timeout: int = 30, **kwarg) -> Tuple:
    """查找

    Args:
        loc: 待查找的元素，具体形式需符合基于的查找类型
        by (DriverType): 查找类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        timeout (int): 查找超时时间
        **kwarg: 基于不同的查找类型，其他需要的参数，具体参见各find函数
    Returns:
        list: 查找到的坐标，未找到则返回None
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "find",
            "loc": "//XCUIElementTypeIcon[@label='天气']",
            "by": 1,
            "timeout": 30
        }

    """
    global GL_DEVICE
    return GL_DEVICE.find(loc, by=by, timeout=timeout, **kwarg)


def multi_find(
        ctrl: str = "",
        img: Union[np.ndarray, str] = None,
        pos: Union[list, tuple] = None,
        by: DriverType = DriverType.UI,
        ctrl_timeout: int = 30,
        img_timeout: int = 10,
        **kwargs) -> Tuple[Any, DriverType]:
    """综合查找.

    优先基于控件定位，未查找到则基于图片匹配+坐标定位，仍未找到则返回传入坐标

    Args:
        ctrl (str): 待查找的控件
        img (ndarray or str): 待匹配查找的图像
        pos (list or tuple): 目标图像的坐标，以辅助定位图像位置
        by (DriverType): ctrl的控件类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        ctrl_timeout (int): 基于控件查找的超时时间
        img_timeout (int): 基于图像匹配查找的超时时间
        **kwargs: 不同查找类型需要设置的参数，具体参见各find函数
    Returns:
        list, DriverType: 查找到的中心点坐标及查找结果基于的查找类型
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "multi_find",
            "ctrl": "//XCUIElementTypeIcon[@label='天气']",
            "img": "your_template_image_str"
            "pos": [0.2, 0.4],
            "timeout": 30
        }

    """
    global GL_DEVICE
    return GL_DEVICE.multi_find(ctrl=ctrl, img=img, pos=pos, by=by, ctrl_timeout=ctrl_timeout,
                                img_timeout=img_timeout, **kwargs)


def click(
        loc=None,
        by: DriverType = DriverType.UI,
        offset: Union[list, tuple] = None,
        timeout: int = 30,
        duration: float = 0.05,
        times: int = 1, **kwargs) -> bool:
    """点击.

    Args:
        loc: 待点击的元素，具体形式需符合基于的点击类型
        by (DriverType): 查找类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (float): 点击的按压时长，以实现长按
        times (int): 点击次数，以实现双击等效果
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数
    Returns:
        bool: 操作是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "click",
            "loc": "//XCUIElementTypeIcon[@label='天气']",
            "by": 1,
            "timeout": 30
        }

    """
    global GL_DEVICE
    return GL_DEVICE.click(loc=loc, by=by, offset=offset, timeout=timeout, duration=duration, times=times, **kwargs)


def double_click(
        loc=None,
        by: DriverType = DriverType.POS,
        offset: Union[list, tuple] = None,
        timeout: int = 30,
        duration: float = 0.05, **kwargs) -> bool:
    """双击.

    Args:
        loc: 待操作的元素，具体形式需符合基于的操作类型
        by (DriverType): 查找类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (float): 点击的按压时长，以实现长按
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数
    Returns:
        bool: 操作是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "double_click",
            "loc": "//XCUIElementTypeIcon[@label='天气']",
            "by": 1,
            "timeout": 30
        }

    """
    global GL_DEVICE
    return GL_DEVICE.double_click(loc=loc, by=by, offset=offset, timeout=timeout, duration=duration, **kwargs)


def long_click(
        loc=None,
        by: DriverType = DriverType.POS,
        offset: Union[list, tuple] = None,
        timeout: int = 30,
        duration: Union[int, float] = 1, **kwargs) -> bool:
    """长按.

    Args:
        loc: 待操作的元素，具体形式需符合基于的操作类型
        by (DriverType): 查找类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        offset (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
        timeout (int): 定位元素的超时时间
        duration (int or float): 点击的按压时长
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数
    Returns:
        bool: 操作是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "long_click",
            "loc": "//XCUIElementTypeIcon[@label='天气']",
            "by": 1,
            "timeout": 30
        }

    """
    global GL_DEVICE
    return GL_DEVICE.long_click(loc=loc, by=by, offset=offset, timeout=timeout, duration=duration, **kwargs)


def slide(
        loc_from=None,
        loc_to=None,
        loc_shift: Union[tuple, list] = None,
        by: DriverType = DriverType.POS,
        timeout: int = 120,
        down_duration: Union[int, float] = 0,
        up_duration: Union[int, float] = 0,
        velocity: Union[int, float] = 0.01, **kwargs) -> bool:
    """滑动.

    Args:
        loc_from: 滑动起始元素位置
        loc_to: 滑动结束元素位置，为None时则根据loc_shift滑动
        loc_shift (tuple or list): 滑动偏移距离
        by (DriverType): : 查找类型，具体枚举值如下:
            原生控件DriverType.UI(1)，
            图像匹配DriverType.CV(3)，
            文字识别DriverType.OCR(2)，
            坐标DriverType.POS(0)，
            GA Unity为DriverType.GA_UNITY(5)，
            GA UE为DriverType.GA_UE(6)
        timeout (int): 定位元素的超时时间
        down_duration (int or float): 起始位置按下时长（s），以实现拖拽功能
        up_duration (int or float): 移动后等待时长（s），以实现摇杆移动功能
        velocity (int or float): 移动间隔，以控制移动速度(Android)
        **kwargs: 基于不同的查找类型，其他需要的参数，具体参见各find函数
    Returns:
        bool: 操作是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "slide",
            "loc_from": "//XCUIElementTypeIcon[@label='天气']",
            "loc_to": "//XCUIElementTypeIcon[@label='电话']",
            "loc_shift": [0.0, 0.0],
            "by": 1
        }


    """
    # 兼容老API，未来将废弃参数duration
    global GL_DEVICE
    return GL_DEVICE.slide(loc_from=loc_from, loc_to=loc_to, loc_shift=loc_shift, by=by, timeout=timeout,
                           down_duration=down_duration, up_duration=up_duration, velocity=velocity, **kwargs)


def get_uitree(xml=False) -> dict:
    """获取控件树.

    Args:
        xml (bool): 为True时返回xml格式数据，否则json格式
    Returns:
        dict: 控件树
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "get_uitree",
            "xml": True
        }
    """
    global GL_DEVICE
    return GL_DEVICE.get_uitree(xml=xml)


def get_element(xpath, timeout=30):
    """根据xpath获取元素列表.

    Args:
        xpath (str): 获取元素的xpath
        timeout (int): 等待时间(秒)
    Returns:
        element: 元素对象。 None:没有匹配到
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "get_element",
            "xpath": "//XCUIElementTypeIcon[@label='照片']"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.get_element(xpath, timeout=timeout)


def get_elements(xpath: str) -> list:
    """根据xpath获取元素列表.

    Args:
        xpath (str): 获取元素的xpath
    Returns:
        list: 元素对象的list
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "get_elements",
            "xpath": "//XCUIElementTypeIcon[@label='照片']"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.get_elements(xpath)


def input_text(
        text: str,
        timeout: int = 30,
        depth: int = 10):
    """文本输入.

    Args:
        text (str): 待输入的文本
        xpath (xpath): iOS需要基于控件输入，xpath形式定位
        timeout (int): 超时时间
        depth (int): source tree的最大深度值，部分应用数值设置过大会导致操作不稳定，过小则可能导致输入失败
        ime (IMEType): Android文本输入采用的方式
    Returns:
        bool: 输入是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "input_text",
            "text": "测试输入内容abc123"
            "xpath": "//XCUIElementTypeSearchField[@label='搜索']"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.input_text(text, timeout=timeout, depth=depth)


def press(name: DeviceButton):
    """设备功能键操作.

    Args:
        name (DeviceButton): 详见DeviceButton
    Returns:
        bool: 点击是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "press",
            "name": 3
        }

    """
    global GL_DEVICE
    return GL_DEVICE.press(name)


def screenshot(
        label: str = "screenshot",
        img_path: str = None,
        pos: Union[tuple, list] = None,
        pos_list: list = None) -> str:
    """截图.

    Args:
        label (str): 图像存储的文件名
        img_path (str): 存储图像的路径，为None时则存到默认目录
        pos (tuple or list): 将坐标绘制在图像上
        pos_list (list): 将一组坐标绘制在图像上
    Returns:
        str: 图像存储路径
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "screenshot",
            "label": "截图自定义名称",
            "img_path": "/path/to/save/your/picture",
            "pos": [0.45, 0.55]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.screenshot(label=label, img_path=img_path, pos=pos, pos_list=pos_list)


def exitfunc():
    """【Deprecated】退出测试.

    Args:
        无
    Returns:
        无

    """
    global GL_DEVICE
    return GL_DEVICE.exitfunc()


def stop_driver():
    """结束驱动.

    脚本运行结束后调用，会释放相关驱动，生成报告等.

    Args:
        无
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "stop_driver"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.stop_driver()


def get_driver() -> any:
    """返回具体类型的驱动，以便于调用该框架的原生API.
    只有在init_driver之后才具备实际意义

    Args:
        无
    Returns:
        Android和鸿蒙时，返回的u2.device实例
        ios时，返回的IOSDriver实例
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "get_driver"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.get_driver()


def app_list() -> list:
    """返回设备内所有的三方应用的列表

    Args:
        无
    Returns:
        list: android和鸿蒙对应的package name的列表，ios对应的bundleId列表
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "app_list"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.app_list()


def app_list_info() -> list:
    """返回设备内所有的三方应用的信息列表

    Args:
        无
    Returns:
        list: {
            "label": "app name",
            "icon": "app icon base64",
            "packageName": "app packageName",
            "versionName": "app version name",
            "versionCode": "app version code"
        }
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "app_list_info"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.app_list_info()


def touch_down(pos: Union[tuple, list], id: int = 0, pressure: int = 50):
    """仅Android，按下操作.

    Args:
        pos (tuple or list): 按下位置的坐标
        id (int): 操作id，不同id以实现多点操作
        pressure (int): 操作压力
    Returns:
        bool: 点击是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "touch_down",
            "pos": [0.12, 0.32]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.touch_down(pos, id=id, pressure=pressure)


def touch_move(pos: Union[tuple, list], id: int = 0, pressure: int = 50):
    """仅Android，移动操作.

    Args:
        pos (tuple or list): 移动到的位置坐标
        id (int): 操作id，不同id以实现多点操作
        pressure (int): 操作压力
    Returns:
        bool: 移动是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "touch_move",
            "pos": [0.12, 0.32]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.touch_move(pos, id=id, pressure=pressure)


def touch_up(pos: Union[tuple, list] = None, id: int = 0, pressure: int = 50):
    """仅Android，抬起操作.

    Args:
        pos (tuple or list): 抬起的位置坐标
        id (int): 操作id，不同id以实现多点操作
        pressure (int): 操作压力
    Returns:
        bool: 抬起是否成功
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "touch_up",
            "pos": [0.12, 0.32]
        }

    """
    global GL_DEVICE
    return GL_DEVICE.touch_up(pos=pos, id=id, pressure=pressure)


def current_activity() -> str:
    """仅android和鸿蒙，获取当前activity.

    Args:
        无
    Returns:
        str: 当前activity
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "current_activity"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.current_activity()


def cmd_adb(cmd: Union[str, list], timeout: int = 10):
    """仅android和鸿蒙, 执行adb或hdb命令.

    Args:
        cmd: str 具体的adb或者hdb命令
        timeout: int 执行命令的超时时间，默认为-1，即不设置超时
    Returns:
        str: 当前activity
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "cmd_adb",
            "cmd": "adb shell -s your_device_id"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.cmd_adb(cmd, timeout=timeout)


def screen_size() -> List[int]:
    """获取屏幕分辨率.

    Args:
        无
    Returns:
        list: 设备屏幕的物理分辨率
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "screen_size"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.screen_size()


def load_default_handler(rule: list):
    """[自动处理相关] 批量加载事件自动处理规则.

    Args:
        rule (list): 事件正则规则，list元素可为str、list、tuple，预设参数如下，使用预设请直接调用start_event_handler()
        rule = [
            '^(完成|关闭|关闭应用|好|允许|始终允许|好的|确定|确认|安装|下次再说|知道了|同意)$',
            r'^((?<!不)(忽略|允(\s){0,2}许|同(\s){0,2}意)|继续|清理|稍后|稍后处理|暂不|暂不设置|强制|下一步)$',
            '^((?i)allow|Sure|SURE|accept|install|done|ok)$',
            ('(建议.*清理)', '(取消|以后再说|下次再说)'),
            ('(发送错误报告|截取您的屏幕|是否删除)', '取消'),
            ('(隐私)', '同意并继续'),
            ('(隐私)', '同意'),
            ('(残留文件占用|网络延迟)', '取消'),
            ('(更新|游戏模式)', '取消'),
            ('(账号密码存储)', '取消'),
            ('(出现在其他应用上)', '关闭'),
            ('(申请获取以下权限)', '(允许|同意)'),
            ('(获取此设备)', '(仅在使用该应用时允许|允许|同意)'),
            ('(以下权限|暂不使用)', '^同[\s]{0,2}意'),
            ('(立即体验|立即升级)', '稍后处理'),
            ('(前往设置)', '暂不设置'),
            ('(我知道了)', '我知道了'),
            ('(去授权)', '去授权'),
            ('(看看手机通讯录里谁在使用微信.*)', '是'),
            ('(默认已允许以下所有权限|以下不提示|退出)', '确定'),
            ('(仅充电|仅限充电|传输文件)', '取消')
        ]
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "load_default_handler"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.load_default_handler(rule)


def start_event_handler():
    """[自动处理相关] 启动预设事件自动处理

    Args:
        无
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "start_event_handler"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.start_event_handler()


def add_event_handler(match_element: str, action_element: str = None):
    """[自动处理相关] 添加事件自动处理规则，并运行.

    Args:
        match_element (str): 判断目标的正则匹配，存在则进行action_elem匹配并点击
        action_element (str): 点击目标的正则匹配，为None时则点击match_elem规则匹配结果
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "add_event_handler"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.add_event_handler(match_element, action_element=action_element)


def sync_event_handler():
    """[自动处理相关] 事件自动处理立即处理一次

    Args:
        无
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "sync_event_handler"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.sync_event_handler()


def clear_event_handler():
    """[自动处理相关] 清除事件自动处理规则

    Args:
        无
    Returns:
        无
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "clear_event_handler"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.clear_event_handler()


def device_info() -> dict:
    """获取设备信息.

    Args:
        无
    Returns:
        dict:
        {
            display:{
                width:0,
                height:0,
            },
            model:"",
            version:"",
            cpu:{
                cores:""
            },
            memory:{
                total:0
            }
        }
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "device_info"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.device_info()


def pkg_version_name(pkg_name: str) -> str:
    """获取app version name.

    Args:
        pkg_name: str Android和鸿蒙里的package Name, ios里的bundleId
    Returns:
        str: version name
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "pkg_version_name",
            "pkg_name": "com.your.app.name"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.pkg_version_name(pkg_name)


def pkg_version_code(pkg_name: str) -> str:
    """获取app version code.

    Args:
        pkg_name: str Android和鸿蒙里的package Name, ios里的bundleId
    Returns:
        str: version code
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "pkg_version_code",
            "pkg_name": "com.your.app.name"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.pkg_version_code(pkg_name)


def installed_package_list() -> list:
    """获取已安装app 列表.

    Args:
        无
    Returns:
        list: android和鸿蒙的app的包名列表，ios的bundleId列表
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "installed_package_list"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.installed_package_list()


def push(src, dst: str):
    """[仅Android和鸿蒙] 推送文件到设备.

    Args:
        src: 被推送的文件路径
        dst: 文件的推送目标路径
    Returns:
        str: 推送动作的返回信息
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "push",
            "src": "/path/to/the/file/on/your/pc/xxx.bat",
            "dst": "/path/on/the/device"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.push(src, dst)


def pull(src, dst: str):
    """[仅Android和鸿蒙] 从设备上拉去文件到PC.

    Args:
        src: 被拉取的设备内文件路径
        dst: 文件的存放位置
    Returns:
        str: 拉取动作的返回信息
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "push",
            "src": "/path/on/the/device/xxx.bat",
            "dst": "/path/to/the/file/on/your/pc"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.pull(src, dst)


def app_list_running() -> list:
    """正在运行的app

    Args:
        无
    Returns:
        list: 正在运行的app的包名list
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "app_list_running"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.app_list_running()


def record_start(video_path: str, **kwargs) -> bool:
    """开始录制屏幕

    Args:
        video_path: str 录屏的输出文件路径
        **kwargs: 扩展参数
    Returns:
        bool: 启动录屏是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "record_start",
            "video_path": "/path/to/my/mp4file/xxx.mp4"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.record_start(video_path, **kwargs)


def record_stop(**kwargs) -> bool:
    """停止录制屏幕

    Args:
        **kwargs: 扩展参数
    Returns:
        bool: 停止录屏是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "record_stop"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.record_stop(**kwargs)


def perf_start(container_bundle_identifier: str, sub_process_name: str,
               sub_window: str, output_directory: str, case_name: str, log_output_file: str) -> bool:
    """开始采集性能数据

    Args:
        container_bundle_identifier: str 应用包名
        sub_process_name: str 进程名
        sub_window: str window名
        output_directory: str 数据输出文件目录
        case_name: str Case名
        log_output_file: str log文件名
    Returns:
        bool 启动采集是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "perf_start",
            "container_bundle_identifier": "com.tencent.mqq",
            "sub_process_name": "",
            "sub_window": "",
            "output_directory": "/path/to/myfile",
            "case_name": "mycase",
            "log_output_file": "perf.log"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.perf_start(container_bundle_identifier, sub_process_name, sub_window,
                                output_directory, case_name, log_output_file)


def perf_stop() -> bool:
    """停止采集性能数据

    Args:
        无
    Returns:
        bool 启动采集是否成功
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "perf_stop"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.perf_stop()


def perf_save_data(output_directory: str = '', case_name: str = '') -> bool:
    """导出性能数据

    Args:
        output_directory: str log文件名
        case_name: str Case名
    Returns:
        bool 是否成功导出
    Example for jsonRpc:
        {
            "os_type": "ios",
            "udid": "your_device_id",
            "method": "perf_save_data",
            "case_name": "mycase",
            "output_directory": "/path/to/my/output"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.perf_save_data(output_directory=output_directory, case_name=case_name)


def logcat(
        file: Union[str, pathlib.Path] = None,
        clear: bool = False,
        re_filter: typing.Union[str, re.Pattern] = None,
) -> StopEvent:
    """[仅android和鸿蒙] 读取logcat日志

    Args:
        file (str): file path to save logcat
        clear (bool): clear logcat before start
        re_filter (str | re.Pattern): regex pattern to filter logcat
    Returns:
        event: haitest.utils.StopEvent
    Example usage:
        >>> evt = d.logcat("logcat.txt", clear=True, re_filter=".*python.*")
        >>> time.sleep(10)
        >>> evt.stop()
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "logcat",
            "file": "logcat.txt",
            "clear": True,
            "re_filter": ".*python.*"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.logcat(file=file, clear=clear, re_filter=re_filter)


def get_app_info(app_path: str) -> AppInfo:
    """
    Args:
        app_path (str): app file path
    Returns:
        appinfo: haitest.utils.params.AppInfo, 包含以下key:'package', 'version_name', 'version_code'
    Example usage:
        >>> info = d.get_app_info("path/to/app/file")
        >>> info.version_name
        >>> info.version_code
    Example for jsonRpc:
        {
            "os_type": "android",
            "udid": "your_device_id",
            "method": "get_app_info",
            "app_path": "/path/to/app/file"
        }

    """
    global GL_DEVICE
    return GL_DEVICE.get_app_info(app_path)


def ios_wda_session():
    """仅ios可用，获取当前sessionId
    Args:
        无

    Returns:
        str: session id
    """
    global GL_DEVICE
    return GL_DEVICE.ios_wda_session()


def ios_get_request_wda(request_uri, time_out=60):
    """仅ios可用
    Args:
        request_uri (str)
        timeout (int)
    """
    global GL_DEVICE
    return GL_DEVICE.ios_get_request_wda(request_uri, time_out)


def ios_post_request_wda(request_uri, json_body=None, time_out=60):
    """仅ios可用
    Args:
        request_uri (str)
        json_body (json object)
        timeout (int)
    """
    global GL_DEVICE
    return GL_DEVICE.ios_post_request_wda(request_uri, json_body, time_out)


def start_cloudphone():
    """获取云手机视频流、操作流url
    Args:
        无

    Returns:
        json
        {
            "screen":"ws://localhost:xxxx/scrcpy/screen/middle",
            "control":"ws://localhost:xxxx/scrcpy/control/middle"
        }
    """
    global GL_DEVICE
    return GL_DEVICE.start_cloudphone()


def stop_cloudphone():
    """关闭云手机视频流、操作流
           Args:
               无

           Returns:
           """
    global GL_DEVICE
    return GL_DEVICE.stop_cloudphone()


def set_clipboard(text: str):
    """设置clipboard
           Args:
               text: 设置的文本

           Returns:
           """
    global GL_DEVICE
    return GL_DEVICE.set_clipboard(text)


def get_clipboard():
    """获取clipboard
           Args:

           Returns:
               文本
           """
    global GL_DEVICE
    return GL_DEVICE.get_clipboard()


def set_http_global_proxy(host, port, username, password):
    """设置全局代理
           Args:
                host:ip
                port:端口
                username:用户名
                password:密码
           Returns:
               文本
           """
    global GL_DEVICE
    return GL_DEVICE.set_http_global_proxy(host, port, username, password)


def get_http_global_proxy():
    """获取全局代理
           Args:
           Returns:
               文本
           """
    global GL_DEVICE
    return GL_DEVICE.get_http_global_proxy()


def clear_http_global_proxy():
    """清除全局代理
           Args:
           Returns:
               文本
           """
    global GL_DEVICE
    return GL_DEVICE.clear_http_global_proxy()


def get_file_path_info(path: str):
    """获取文件属性
           Args:
               path: 文件路径
           Returns:
               {
                'isDirectory': True,
                 'mode': 'drwxrwx--x',
                 'modifyTime': 1741923210944,
                 'name': 'tmp',
                 'path': '/data/local/tmp',
                 'size': 4096,
                 'files':[     //目录下文件
                    {
                    'isDirectory': True,
                   'mode': 'drwxr-xr-x',
                   'modifyTime': 1663229880198,
                   'name': '.config',
                   'path': '/data/local/tmp/.config',
                   'size': 4096
                    }
                 ]
                }
           """
    global GL_DEVICE
    return GL_DEVICE.get_file_path_info(path)


def wait_for_idle(idle_time: float = 0.5, timeout: float = 10):
    """等待页面进入空闲状态
           Args:
               idle_time: UI界面处于空闲状态的持续时间，当UI空闲时间>=idle_time时，该函数返回.默认0.5秒
               timeout: 等待超时时间，如果经过timeout秒后UI空闲时间仍然不满足，则返回。默认10秒
           Returns:
               True: 页面进入idle状态; False: 在timeout时间内，页面未进入idle状态
           """
    global GL_DEVICE
    return GL_DEVICE.wait_for_idle(idle_time, timeout)
