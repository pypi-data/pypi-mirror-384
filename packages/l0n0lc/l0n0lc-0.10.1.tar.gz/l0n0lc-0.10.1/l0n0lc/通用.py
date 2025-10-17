import re
import os
import inspect
from typing import List, Optional, Any, Dict


def 变量名(var):
    frame = inspect.currentframe()
    if frame is None:
        return
    frame = frame.f_back
    if frame is None:
        return
    for name, value in frame.f_locals.items():
        if value is var:
            return name
    for name, value in frame.f_globals.items():
        if value is var:
            return name
    return None


def 上层变量名(var):
    frame = inspect.currentframe()
    if frame is None:
        return
    frame = frame.f_back
    if frame is None:
        return
    counter = 0
    for name, value in frame.f_locals.items():
        if value is var:
            counter += 1
            if counter > 1:
                return name
    for name, value in frame.f_globals.items():
        if value is var:
            counter += 1
            if counter > 1:
                return name
    return None


def 十进制转换为其他进制(数值: int, 进制: int, digits="0123456789ABCDEF"):
    if 数值 == 0:
        return "0"
    result = ""
    is_negative = 数值 < 0
    数值 = abs(数值)
    while 数值 > 0:
        数值, remainder = divmod(数值, 进制)  # 除基取余
        result = digits[remainder] + result  # 余数映射字符
    return ("-" if is_negative else "") + result


class c函数映射:
    def __init__(
            self, 目标函数,
            include目录: Optional[List[str]],
            库列表: Optional[List[str]],
            库目录: Optional[List[str]]) -> None:
        self.目标函数 = 目标函数
        self.include目录 = include目录 or []
        self.库列表 = 库列表 or []
        self.库目录 = 库目录 or []

    def __str__(self) -> str:
        return self.目标函数


class c类型映射:
    def __init__(
            self, 目标类型,
            include目录: Optional[List[str]],
            库列表: Optional[List[str]],
            库目录: Optional[List[str]],
            对应的ctypes类型=None) -> None:
        self.目标类型 = 目标类型
        self.include目录 = include目录 or []
        self.库列表 = 库列表 or []
        self.库目录 = 库目录 or []
        self.对应的ctypes类型 = 对应的ctypes类型

    def __str__(self) -> str:
        return self.目标类型


class 通用信息:
    直接调用函数 = set()
    函数映射表: Dict[Any, c函数映射] = {}
    类型映射表: Dict[Any, c类型映射] = {}
    include表 = set()
    连接库表 = set()
    变量最大ID = 0
    python内置映射 = {}
    使用unicode编程 = True
    工作文件夹地址 = './l0n0lcoutput'

    @staticmethod
    def 缓存接调用函数():
        通用信息.直接调用函数.add(range)

    @staticmethod
    def 添加内置映射(v):
        通用信息.python内置映射[v.__name__] = v

    @staticmethod
    def 内置映射():
        for v in [int, float, str, bool, range, complex, set, tuple, list, dict,
                  print, input, abs, round, pow, divmod, sum, min, max,
                  isinstance, len, open, ]:
            通用信息.添加内置映射(v)


通用信息.内置映射()


def 直接调用函数(fn):
    通用信息.直接调用函数.add(fn)
    return fn


def 映射函数(
        被映射函数,
        include目录: Optional[List[str]] = None,
        链接库列表: Optional[List[str]] = None,
        库目录列表: Optional[List[str]] = None):
    def 装饰器(映射目标):
        通用信息.函数映射表[被映射函数] = c函数映射(映射目标, include目录, 链接库列表, 库目录列表)
        return 映射目标
    return 装饰器


def 映射类型(被映射类型,
         include目录: Optional[List[str]] = None,
         链接库列表: Optional[List[str]] = None,
         库目录列表: Optional[List[str]] = None,
         对应的ctypes类型=None):
    def 装饰器(映射目标):
        通用信息.类型映射表[映射目标] = c类型映射(被映射类型, include目录, 链接库列表, 库目录列表, 对应的ctypes类型)
        return 映射目标
    return 装饰器


def 有非英文变量字符(s):
    return bool(re.search(r'[^A-Za-z0-9_]', s))


def 生成变量Id(原始名字: str | None = None):
    if 原始名字 is not None and (通用信息.使用unicode编程 or not 有非英文变量字符(原始名字)):
        return 原始名字
    ret = f'_{通用信息.变量最大ID}'
    通用信息.变量最大ID += 1
    return ret


def 尝试创建文件夹(文件夹名: str):
    if os.path.exists(文件夹名):
        return
    os.mkdir(文件夹名)


def toCString(v):
    if isinstance(v, str):
        return f'u8"{v}"'
    return str(v)
