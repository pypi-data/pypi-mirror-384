from typing import Union, List, get_origin, get_args
from .通用 import 生成变量Id, toCString, 通用信息
import ctypes


class cpp类型:
    INT8_T = 'int8_t'
    INT16_T = 'int16_t'
    INT32_T = 'int32_t'
    INT64_T = 'int64_t'
    UINT8_T = 'uint8_t'
    UINT16_T = 'uint16_t'
    UINT32_T = 'uint32_t'
    UINT64_T = 'uint64_t'
    HALF = 'half'
    FLOAT = 'float'
    STRING = 'std::string'
    BOOL = 'bool'
    ANY = 'std::any'
    AUTO = 'auto'
    VOID_P = 'void*'


class 指针:
    def __init__(self, 类型) -> None:
        self.基础类型 = 类型

    def __str__(self) -> str:
        return f'{self.基础类型}*'


def 执行额外函数(函数列表: List, *args):
    for fn in 函数列表:
        ret = fn(*args)
        if ret is not None:
            return ret


额外py转ctypes函数 = []
py2ctypes映射表 = {
    int: ctypes.c_int64,
    float: ctypes.c_float,
    str: ctypes.c_char_p,
    bool: ctypes.c_bool,
    指针: ctypes.c_void_p,
}


def py类型转ctypes类型(类型):
    ret = 执行额外函数(额外py转ctypes函数, 类型)
    if ret is not None:
        return ret

    ret = 通用信息.类型映射表.get(类型)
    if ret is not None:
        return ret.对应的ctypes类型

    return py2ctypes映射表.get(类型)


额外py转c函数 = []
py2c类型映射表 = {
    int: cpp类型.INT64_T,
    float: cpp类型.FLOAT,
    str: cpp类型.STRING,
    bool: cpp类型.BOOL,
    指针: cpp类型.VOID_P,
}


def py类型转c类型(类型):
    ret = 执行额外函数(额外py转c函数, 类型)
    if ret is not None:
        return ret

    ret = 通用信息.类型映射表.get(类型)
    if ret is not None:
        return ret.目标类型

    # 基础类型
    ret = py2c类型映射表.get(类型)
    if ret is not None:
        return ret

    origin = get_origin(类型)
    args = get_args(类型)

    if origin is Union:
        return cpp类型.ANY

    # List[...] → 指针(...)
    if origin is list:
        if args:
            elem_type = args[0]
            return 指针(py类型转c类型(elem_type))

    # Dict[K, V] → std::unordered_map<K, V>
    if origin is dict:
        if len(args) == 2:
            key_type = py类型转c类型(args[0])
            val_type = py类型转c类型(args[1])
            return f"std::unordered_map<{key_type}, {val_type}>&"

    # 直接传字符串类型名
    if isinstance(类型, str):
        return 类型

    return cpp类型.ANY


def cpp类型检查(类型, 支持提示: str):
    if 类型 not in [int, float, str, bool]:
        raise Exception(f'{支持提示} 仅支持 [int, float, str, bool]')


class list初始化列表:
    def __init__(
            self,
            代码: str,
            类型列表: Union[List[Union[int, float, bool, str]],
                        int, float, bool, str],
            长度: int) -> None:
        self.代码 = 代码
        self.类型列表 = 类型列表
        self.类型 = py类型转c类型(类型列表)
        self.长度 = 长度

    def __str__(self) -> str:
        return self.代码


def 从list构建初始化列表(value: List):
    数据类型列表 = []
    初始化列表 = []
    for v in value:
        dtype = type(v)
        cpp类型检查(dtype, 'List')
        数据类型列表.append(dtype)
        初始化列表.append(toCString(v))
    # 构建初始化列表
    初始化列表 = '{' + ','.join(初始化列表) + '}'

    # 构建类型列表
    if all(类型 == 数据类型列表[0] for 类型 in 数据类型列表):
        数据类型列表 = 数据类型列表[0]

    return list初始化列表(初始化列表, 数据类型列表, len(value))


class dict初始化列表:
    def __init__(
            self,
            代码: str,
            key类型列表: Union[List[Union[int, float, bool, str]],
                           int, float, bool, str],
            value类型列表: Union[List[Union[int, float, bool, str]],
                             int, float, bool, str]) -> None:
        self.代码 = 代码
        self.key类型列表 = key类型列表
        self.value类型列表 = value类型列表
        self.key类型 = py类型转c类型(key类型列表)
        self.value类型 = py类型转c类型(value类型列表)

    def __str__(self) -> str:
        return self.代码


def 从dict构建初始化列表(value: dict):
    code = []
    key类型列表 = []
    value类型列表 = []
    for k, v in value.items():
        key类型 = type(k)
        cpp类型检查(key类型, 'Map')
        value类型 = type(v)
        cpp类型检查(value类型, 'Map')
        key类型列表.append(key类型)
        value类型列表.append(value类型)
        code.append(f'{{ {toCString(k)}, {v} }}')

    # 构建类型列表
    if all(类型 == key类型列表[0] for 类型 in key类型列表):
        key类型列表 = key类型列表[0]

    if all(类型 == value类型列表[0] for 类型 in value类型列表):
        value类型列表 = value类型列表[0]

    # 构建初始化列表
    初始化列表 = '{' + ','.join(code) + '}'

    return dict初始化列表(初始化列表, key类型列表, value类型列表)


class c变量:
    def __init__(self, 类型: str, 名字: str, 是参数: bool, 默认值=None) -> None:
        self.类型 = 类型
        self.名字 = 名字
        self.c名字 = 生成变量Id(名字)
        self.是参数 = 是参数
        self.默认值 = 默认值

    def __str__(self):
        return self.c名字

    @property
    def decltype(self):
        return f'decltype({self})'

    def 初始化(self, 初始值, 强转类型: str | None = None):
        if 强转类型:
            return f'{self.类型} {self.c名字} = (({强转类型})({初始值}));'
        else:
            return f'{self.类型} {self.c名字} = {初始值};'
