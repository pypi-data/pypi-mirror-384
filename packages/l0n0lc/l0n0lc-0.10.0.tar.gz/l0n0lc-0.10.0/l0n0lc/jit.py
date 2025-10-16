import os
import ast
import hashlib
import inspect
from typing import Callable, Any, List, Dict
from .c基础处理 import *
from .StdList import StdList
from .StdMap import StdUnorderedMap
from .通用 import 通用信息, 有非英文变量字符, 尝试创建文件夹, c类型映射
from .编译 import cpp编译器


class 代码异常抛出器:
    def __init__(self, 代码: str) -> None:
        self.代码行 = 代码.split('\n')

    def __call__(self, 错误信息: str, node: ast.stmt | ast.expr | ast.arg) -> Any:
        raise Exception(
            f'{错误信息} {self.代码行[node.lineno][node.col_offset:node.end_col_offset]}')


class 花括号:
    def __init__(self, 编译器) -> None:
        self.编译器: py2cpp编译器 = 编译器

    def __enter__(self, *args, **kwargs):
        self.编译器.添加c代码('{')
        self.编译器.进入新作用域()

    def __exit__(self, *args, **kwargs):
        self.编译器.退出作用域()
        self.编译器.添加c代码('}\n')


class c代码:
    def __init__(self, 代码: str, 层级: int) -> None:
        self.代码 = 代码
        self.层级 = 层级

    def __str__(self) -> str:
        return '  ' * self.层级 + self.代码


class c获取索引项目:
    def __init__(self, 变量, 索引) -> None:
        self.变量 = 变量
        self.索引 = 索引

    def __str__(self) -> str:
        return f'{self.变量}[{toCString(self.索引)}]'


class c获取属性:
    def __init__(self, 变量, 属性) -> None:
        self.变量 = 变量
        self.属性 = 属性

    def __str__(self) -> str:
        if isinstance(self.变量, c变量):
            if self.变量.类型.endswith('*'):
                return f'{self.变量}->{self.属性}'
        return f'{self.变量}.{self.属性}'


class c函数调用:
    def __init__(self, 函数名, 参数字符串) -> None:
        self.函数名 = 函数名
        self.参数字符串 = 参数字符串

    def __str__(self) -> str:
        return f'{self.函数名}({self.参数字符串})'


class c布尔:
    def __init__(self, v) -> None:
        self.v = v

    def __str__(self) -> str:
        if self.v:
            return 'true'
        return 'false'


class py2cpp编译器(ast.NodeVisitor):
    def __init__(self, 被编译的函数: Callable, c编译器, 编译为可执行文件文件名: str | None = None) -> None:
        self.被编译的函数 = 被编译的函数
        self.c编译器: cpp编译器 = c编译器
        self.编译为可执行文件文件名 = 编译为可执行文件文件名
        self.源代码 = inspect.getsource(被编译的函数)
        self.代码哈希值 = hashlib.blake2s(
            self.源代码.encode(), digest_size=8).hexdigest()
        self.代码异常抛出器 = 代码异常抛出器(self.源代码)
        self.全局变量 = 被编译的函数.__globals__
        self.局部变量 = {}
        self.参数变量 = {}
        self.ctypes类型 = []
        self.ctypes返回类型 = ctypes.c_voidp
        self.参数不同c类型前置处理函数 = {}
        self.ascendc变量对应表: List[Dict[str, Any]] = [{}]
        self.当前上下文层级 = 0
        self.依赖函数: List[py2cpp编译器] = []
        self.函数映射表 = {}
        self.代码序列 = []
        self.花括号 = 花括号(self)
        self.正在调用直接函数 = False
        self.正在构建参数 = False
        self.include列表 = set(['<cstdint>', '<string>'])
        self.链接库列表 = set()
        self.库目录 = set()

        # 保存函数名
        self.函数名 = 被编译的函数.__name__
        if 编译为可执行文件文件名:
            self.c函数名 = 'main'
        else:
            if 有非英文变量字符(self.函数名):
                self.c函数名 = f'function_{self.函数名.encode().hex()}'
            else:
                self.c函数名 = self.函数名
        代码文件地址 = inspect.getfile(被编译的函数)
        文件名 = os.path.split(代码文件地址)[1]
        文件名hash = hashlib.blake2s(代码文件地址.encode(), digest_size=8).hexdigest()
        self.文件前缀 = f'{文件名hash}_{文件名}_{self.函数名}_@'

    def 编译(self):
        语法树 = ast.parse(self.源代码)
        self.visit(语法树)
        # 读取依赖函数
        cpps = set([f'{通用信息.工作文件夹地址}/{self.获取cpp文件名()}'])
        for b in self.依赖函数:
            self.include列表.add(f'"{b.获取h文件名()}"')
            cpps.add(f'{通用信息.工作文件夹地址}/{b.获取cpp文件名()}')

        self.将代码保存到文件()
        self.c编译器.库目录列表 = list(self.库目录)
        self.c编译器.链接库 = list(self.链接库列表)
        输出路径 = f'{通用信息.工作文件夹地址}/{self.获取库文件名()}'
        if self.编译为可执行文件文件名:
            self.c编译器.添加编译选项("-O2")
            self.c编译器.编译文件(list(cpps), 输出路径=输出路径)
        else:
            self.c编译器.编译为动态库(list(cpps), 输出路径=输出路径)

    def 添加c代码(self, 代码: str):
        self.代码序列.append(c代码(代码, self.当前上下文层级))

    def 抛出代码异常(self, 错误提示: str, node: ast.stmt | ast.expr | ast.arg):
        self.代码异常抛出器(错误提示, node)

    def 进入新作用域(self):
        self.ascendc变量对应表.append({})
        self.当前上下文层级 += 1

    def 退出作用域(self):
        self.ascendc变量对应表.pop()
        self.当前上下文层级 -= 1

    def 获取c变量(self, 变量名: str):
        for i in range(self.当前上下文层级, -1, -1):
            v = self.ascendc变量对应表[i].get(变量名)
            if v is not None:
                return v

    def 添加c变量(self, 变量: c变量):
        self.ascendc变量对应表[self.当前上下文层级][变量.名字] = 变量

    def 根据值添加c参数变量(self, 值, 名字: str):
        变量 = self.获取c变量(名字)
        if 变量 is not None:
            return 变量
        if isinstance(值, int):
            变量类型 = 'int64_t'
        elif isinstance(值, float):
            变量类型 = 'float'
        变量 = c变量(变量类型, 名字, True)
        self.添加c变量(变量)
        return 变量

    def 获取值(self, value):
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):
                return c布尔(value.value)
            return value.value

        if isinstance(value, ast.Name):
            v = 通用信息.python内置映射.get(value.id)
            if v is not None:
                return v
            v = self.局部变量.get(value.id)
            if v is not None:
                return v
            v = self.获取c变量(value.id)
            if v is not None:
                return v
            v = self.参数变量.get(value.id)
            if v is not None:
                return v
            return self.全局变量.get(value.id)

        if isinstance(value, ast.Attribute):
            对象 = self.获取值(value.value)
            if isinstance(对象, (c变量, c类型映射)):
                return c获取属性(对象, value.attr)
            if 对象 is None:
                self.抛出代码异常(f'没找到{value.value}', value)
            return getattr(对象, value.attr)

        if isinstance(value, ast.UnaryOp):
            operand = self.获取值(value.operand)
            if isinstance(value.op, ast.UAdd):
                return f'(+{operand})'
            if isinstance(value.op, ast.USub):
                return f'(-{operand})'
            if isinstance(value.op, ast.Not):
                return f'(!{operand})'
            if isinstance(value.op, ast.Invert):
                return f'(~{operand})'

        if isinstance(value, ast.BoolOp):
            if isinstance(value.op, ast.And):
                return '&&'.join([f'({self.获取值(v)})' for v in value.values])
            if isinstance(value.op, ast.Or):
                return '||'.join([f'({self.获取值(v)})' for v in value.values])

        if isinstance(value, ast.IfExp):
            test = self.获取值(value.test)
            body = self.获取值(value.body)
            orelse = self.获取值(value.orelse)
            return f'(({test}) ? ({body}) : ({orelse}))'

        if isinstance(value, ast.Compare):
            return self.计算Compare(value)

        if isinstance(value, ast.BinOp):
            return self.计算二元运算(value)

        if isinstance(value, ast.List):
            l = [self.获取值(e) for e in value.elts]
            return 从list构建初始化列表(l)
        if isinstance(value, ast.Tuple):
            l = [self.获取值(e) for e in value.elts]
            if not self.正在构建参数:
                return 从list构建初始化列表(l)
            return tuple(l)
        if isinstance(value, ast.Dict):
            d = {self.获取值(k): self.获取值(v)
                 for k, v in zip(value.keys, value.values)}
            return 从dict构建初始化列表(d)

        if isinstance(value, ast.Call):
            return self.调用Call(value)

        if isinstance(value, ast.Subscript):
            return self.获取Subscript(value)

    def 计算Compare(self, node: ast.Compare) -> Any:
        left = self.获取值(node.left)
        ret = '('
        输出left = True
        for op, comp in zip(node.ops, node.comparators):
            left = left if 输出left else ''
            right = self.获取值(comp)
            if isinstance(op, ast.Eq):
                ret += f'({left} == {right})'
            if isinstance(op, ast.NotEq):
                ret += f'({left} != {right})'
            if isinstance(op, ast.Lt):
                ret += f'({left} < {right})'
            if isinstance(op, ast.LtE):
                ret += f'({left} <= {right})'
            if isinstance(op, ast.Gt):
                ret += f'({left} > {right})'
            if isinstance(op, ast.GtE):
                ret += f'({left} >= {right})'
            left = right
            输出left = False
        # 如果只有一项, 不需要多层括号
        if len(node.ops) == 1:
            return ret[1:]
        return ret + ')'

    def 计算二元运算(self, node: ast.BinOp | ast.AugAssign):
        if isinstance(node, ast.BinOp):
            left = self.获取值(node.left)
            right = self.获取值(node.right)
        elif isinstance(node, ast.AugAssign):
            left = self.获取值(node.target)
            right = self.获取值(node.value)
        op = node.op
        if isinstance(op, ast.Add):
            return f'({left} + {right})'
        if isinstance(op, ast.Sub):
            return f'({left} - {right})'
        if isinstance(op, ast.Mult):
            return f'({left} * {right})'
        if isinstance(op, (ast.Div, ast.FloorDiv)):
            return f'({left} / {right})'
        if isinstance(op, ast.Mod):
            return f'({left} % {right})'
        if isinstance(op, ast.BitAnd):
            return f'({left} & {right})'
        if isinstance(op, ast.BitOr):
            return f'({left} | {right})'
        if isinstance(op, ast.BitXor):
            return f'({left} ^ {right})'
        if isinstance(op, ast.LShift):
            return f'({left} << {right})'
        if isinstance(op, ast.RShift):
            return f'({left} >> {right})'

        self.抛出代码异常(f"暂不支持的运算符: {type(op).__name__}", node)

    def 构建参数列表文本(self, args: List[ast.expr]):
        参数列表 = [str(self.获取值(arg)) for arg in args]
        return ','.join(参数列表)

    def 调用Call(self, node: ast.Call):
        # 获取函数
        fn = self.获取值(node.func)

        # 如果是创建类型
        if inspect.isclass(fn):
            c类型 = 通用信息.类型映射表.get(fn)
            if c类型 is not None:
                for include目录 in c类型.include目录:
                    self.include列表.add(include目录)
                for 链接库 in c类型.库列表:
                    self.链接库列表.add(链接库)
                for 库目录 in c类型.库目录:
                    self.库目录.add(库目录)
                参数文本 = self.构建参数列表文本(node.args)
                return c函数调用(c类型, 参数文本)

        # 直接调用函数
        if fn in 通用信息.直接调用函数:
            参数列表 = [self.获取值(arg) for arg in node.args]
            self.正在调用直接函数 = True
            return fn(*参数列表)

        # python函数对应的c++函数
        映射函数 = 通用信息.函数映射表.get(fn)
        if 映射函数 is not None:
            参数列表 = [self.获取值(arg) for arg in node.args]
            for include目录 in 映射函数.include目录:
                self.include列表.add(include目录)
            for 链接库 in 映射函数.库列表:
                self.链接库列表.add(链接库)
            for 库目录 in 映射函数.库目录:
                self.库目录.add(库目录)

            return 映射函数.目标函数(*参数列表)

        if not isinstance(fn, Callable) and not isinstance(fn, c获取属性):
            self.抛出代码异常(f'{ast.dump(node.func)} 没找到', node)

        if len(node.keywords) > 0:
            self.抛出代码异常('暂不支持 keywords 函数调用', node)

        参数文本 = self.构建参数列表文本(node.args)
        # 是否是编译好的函数
        if isinstance(fn, py2cpp编译器):
            self.依赖函数.append(fn)
            return c函数调用(fn.c函数名, 参数文本)
        elif isinstance(fn, c获取属性):
            return c函数调用(fn, 参数文本)
        # 编译该函数
        else:
            依赖函数编译器 = self.__class__(fn, self.c编译器)
            依赖函数编译器.编译()
            self.依赖函数.append(依赖函数编译器)
            return c函数调用(fn.__name__, 参数文本)

    def 获取Subscript(self, node: ast.Subscript):
        对象 = self.获取值(node.value)
        切片 = node.slice
        if isinstance(切片, ast.Slice):
            self.抛出代码异常('不支持列表切片,请以std::vector为准', node)
        切片 = self.获取值(切片)
        if 对象 is Union:
            return Union[切片]
        if 对象 is List:
            return List[切片]
        if 对象 is Dict:
            return Dict[切片[0], 切片[1]]
        return c获取索引项目(对象, 切片)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        with self.花括号:
            self.visit_核函数所有参数(node.args)
            self.visit_核函数体(node.body)

        # 读取返回类型
        if isinstance(node.returns, ast.Name):
            返回py类型 = self.获取值(node.returns)
            self.返回类型 = py类型转c类型(返回py类型)
            if not self.编译为可执行文件文件名:
                self.ctypes返回类型 = py类型转ctypes类型(返回py类型)
                if self.ctypes返回类型 is None:
                    self.抛出代码异常(f'不支持的返回值类型{返回py类型}', node)
        elif isinstance(node.returns, (tuple)):
            self.抛出代码异常('函数只能有一个返回值', node)
        else:
            self.返回类型 = 'auto'

    def visit_核函数所有参数(self, node: ast.arguments) -> Any:
        self.正在构建参数 = True
        # 支持 *args / **kwargs
        位置参数 = list(node.args)
        if node.vararg:
            位置参数.append(node.vararg)
        for idx, arg_node in enumerate(位置参数):
            默认值 = None
            if idx >= len(node.args) - len(node.defaults):
                默认值 = node.defaults[idx -
                                    (len(node.args) - len(node.defaults))]
            self.visit_核函数参数(idx, arg_node, 默认值)
        self.正在构建参数 = False

    def visit_核函数参数(self, idx: int, node: ast.arg, 默认值=None) -> Any:
        参数名 = node.arg
        参数值 = self.获取值(默认值) if 默认值 is not None else None
        if node.annotation is None:
            self.抛出代码异常('变量必须表明类型', node)
        类型 = self.获取值(node.annotation)
        c类型 = py类型转c类型(类型)
        if c类型 is None:
            self.抛出代码异常(f'不支持的类型{类型}', node)
        参数变量 = c变量(str(c类型), 参数名, True, 参数值)
        self.参数变量[参数名] = 参数变量
        if not self.编译为可执行文件文件名:
            ctypes类型 = py类型转ctypes类型(类型)
            if ctypes类型 is None:
                self.抛出代码异常(f'不支持的参数类型{类型}', node)
            self.ctypes类型.append(ctypes类型)
        前置处理函数 = self.参数不同c类型前置处理函数.get(类型)
        if 前置处理函数 is not None:
            前置处理函数(self, 参数变量, node)

    def visit_核函数体(self, node: List[ast.stmt]):
        for stmt in node:
            self.visit(stmt)

    def visit_Return(self, node: ast.Return) -> Any:
        返回值 = self.获取值(node.value) if node.value is not None else ''
        self.添加c代码(f'return {返回值};')

    def visit_If(self, node: ast.If) -> Any:
        判定 = self.获取值(node.test)
        self.添加c代码(f'if ({判定})')
        if len(node.body) > 0:
            with self.花括号:
                for stmt in node.body:
                    self.visit(stmt)
        else:
            self.添加c代码(';')
        if len(node.orelse) > 0:
            self.添加c代码('else')
            with self.花括号:
                for stmt in node.orelse:
                    self.visit(stmt)

    def 检查for是否支持(self, node: ast.For):
        if not isinstance(node.target, (ast.Name, ast.Tuple, ast.List)):
            self.抛出代码异常("暂不支持复杂for目标", node)

    def visit_For(self, node: ast.For) -> Any:
        self.检查for是否支持(node)
        # 构建for循环
        目标 = self.获取值(node.target)
        if 目标 is None:
            if isinstance(node.target, ast.Name):
                目标 = c变量('auto', node.target.id, False)
                self.添加c变量(目标)
            else:
                self.抛出代码异常('for中target必须是ast.Name', node)

        if isinstance(node.iter, ast.Call):
            fn = self.获取值(node.iter.func)
            if fn is range:
                参数 = [self.获取值(arg) for arg in node.iter.args]
                if len(参数) == 1:
                    代码 = f'for (int64_t {目标} = 0; {目标} < {参数[0]}; ++{目标})'
                elif len(参数) == 2:
                    代码 = f'for (int64_t {目标} = {参数[0]}; {目标} < {参数[1]}; ++{目标})'
                elif len(参数) == 3:
                    代码 = f'for (int64_t {目标} = {参数[0]}; {目标} < {参数[1]}; {目标} += {参数[2]})'
            else:
                调用代码 = self.调用Call(node.iter)
                代码 = f'for (auto {目标} : {调用代码})'
        elif isinstance(node.iter, (ast.List, ast.Tuple)):
            列表内容 = [self.获取值(v) for v in node.iter.elts]
            初始化列表 = 从list构建初始化列表(列表内容)
            代码 = f'for (auto {目标} : {初始化列表.代码})'
        else:
            循环目标 = self.获取值(node.iter)
            代码 = f'for (auto {目标} : {循环目标})'

        # 添加for代码
        self.添加c代码(代码)

        # 访问for循环体
        with self.花括号:
            for stmt in node.body:
                self.visit(stmt)

    def visit_Break(self, node: ast.Break):
        self.添加c代码('break;')

    def visit_Continue(self, node: ast.Continue):
        self.添加c代码('continue;')

    def visit_While(self, node: ast.While) -> Any:
        test = self.获取值(node.test)
        self.添加c代码(f'while ({test})')
        with self.花括号:
            for stmt in node.body:
                self.visit(stmt)

    def visit_Try(self, node: ast.Try) -> Any:
        self.抛出代码异常('不支持try except', node)

    def visit_With(self, node: ast.With) -> Any:
        self.抛出代码异常('不支持with', node)

    def visit_Call(self, node: ast.Call) -> Any:
        代码 = self.调用Call(node)
        self.添加c代码(f'{代码};')

    def _赋值(self, target, 值, node, c强转类型: str | None = None):
        目标 = self.获取值(target)
        if self.正在调用直接函数:
            if isinstance(target, ast.Name):
                self.局部变量[target.id] = 值
            else:
                self.抛出代码异常('对非ast.Name赋值', node)
            self.正在调用直接函数 = False
            return

        if 目标 is None:
            if isinstance(target, ast.Name):
                if isinstance(值, dict初始化列表):
                    目标 = StdUnorderedMap(值, target.id, False)
                    self.include列表.add('<unordered_map>')
                elif isinstance(值, list初始化列表):
                    目标 = StdList(值, target.id, False)
                    if 值.类型 == cpp类型.ANY:
                        self.include列表.add('<any>')
                else:
                    目标 = c变量('auto', target.id, False)
                self.添加c代码(目标.初始化(值, c强转类型))
                self.添加c变量(目标)
            else:
                self.抛出代码异常('for中target必须是ast.Name', node)
        else:
            if c强转类型:
                self.添加c代码(f'{目标} = {c强转类型}({值});')
            else:
                self.添加c代码(f'{目标} = {值};')

    def visit_Assign(self, node: ast.Assign) -> Any:
        值 = self.获取值(node.value)
        for target in node.targets:
            self._赋值(target, 值, node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        值 = self.计算二元运算(node)
        self._赋值(node.target, 值, node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        值 = self.获取值(node.value)
        目标类型 = self.获取值(node.annotation)
        if 目标类型 is None:
            self.抛出代码异常(f'不支持的类型:{node.annotation}', node)
        c类型 = py类型转c类型(目标类型)
        if c类型 is None:
            self.抛出代码异常(f'不支持的类型:{目标类型}', node)
        self._赋值(node.target, 值, node, str(c类型))

    def 获取定义(self):
        参数定义 = []
        for arg in self.参数变量.values():
            if isinstance(arg, c变量):
                参数定义.append(f'{arg.类型} {arg.c名字}')
        参数定义文本 = ', '.join(参数定义)
        if self.c函数名 == self.函数名:
            return f'extern "C" {self.返回类型} {self.c函数名} ({参数定义文本})'
        return f'extern "C" {self.返回类型} /*{self.函数名}*/ {self.c函数名} ({参数定义文本})'

    def 获取includes(self):
        include代码列表 = [f'#include {目录}' for 目录 in sorted(self.include列表)]
        return '\n'.join(include代码列表)

    def 获取h代码(self):
        return '#pragma once\n' + self.获取includes() + '\n' + self.获取定义() + ';'

    def 获取无后缀文件名(self):
        return f'{self.文件前缀}{self.代码哈希值}'

    def 获取h文件名(self):
        return f'{self.获取无后缀文件名()}.h'

    def 获取cpp文件名(self):
        return f'{self.获取无后缀文件名()}.cpp'

    def 获取库文件名(self):
        if self.编译为可执行文件文件名:
            return self.编译为可执行文件文件名
        return f'{self.获取无后缀文件名()}.so'

    def 获取cpp代码(self):
        定义代码 = self.获取定义()
        代码 = [str(code) for code in self.代码序列]
        return f'#include "{self.获取h文件名()}"\n' + 定义代码 + '\n' + '\n'.join(代码)

    def 根据缀删除文件(self):
        if not os.path.exists(通用信息.工作文件夹地址):
            return
        for 文件名 in os.listdir(通用信息.工作文件夹地址):
            if 文件名.startswith(self.文件前缀):
                文件路径 = os.path.join(通用信息.工作文件夹地址, 文件名)
                os.remove(文件路径)
        if self.编译为可执行文件文件名:
            文件路径 = os.path.join(通用信息.工作文件夹地址, self.编译为可执行文件文件名)
            if os.path.exists(文件路径):
                os.remove(文件路径)

    def 将代码保存到文件(self):
        self.根据缀删除文件()
        尝试创建文件夹(通用信息.工作文件夹地址)
        with open(f'{通用信息.工作文件夹地址}/{self.获取h文件名()}', 'w') as fp:
            fp.write(self.获取h代码())
        with open(f'{通用信息.工作文件夹地址}/{self.获取cpp文件名()}', 'w') as fp:
            cpp代码 = self.获取cpp代码()
            fp.write(cpp代码)

    def 加载库(self):
        if self.编译为可执行文件文件名:
            return
        库地址 = f'{通用信息.工作文件夹地址}/{self.获取库文件名()}'
        self.目标库 = ctypes.CDLL(库地址)
        self.cpp函数 = self.目标库[self.c函数名]
        self.cpp函数.argtypes = self.ctypes类型
        self.cpp函数.restype = self.ctypes返回类型

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.编译为可执行文件文件名:
            库文件名 = self.获取库文件名()
            可执行文件地址 = f'{通用信息.工作文件夹地址}/{库文件名}'
            raise Exception(f"请直接在命令行执行[{可执行文件地址}]")
        else:
            return self.cpp函数(*args)


def jit(jit编译器类=None, cpp编译器类=None, 每次运行都重新编译: bool = False, 编译为可执行文件文件名: str | None = None):
    def 编译函数(fn: Callable):
        _c编译器类 = cpp编译器类 or cpp编译器
        _jit编译器类 = jit编译器类 or py2cpp编译器
        c语言函数编译器 = _jit编译器类(fn, _c编译器类(), 编译为可执行文件文件名)
        库文件名 = c语言函数编译器.获取库文件名()
        if 每次运行都重新编译 or not os.path.exists(f'{通用信息.工作文件夹地址}/{库文件名}'):
            c语言函数编译器.编译()
        c语言函数编译器.加载库()
        return c语言函数编译器
    return 编译函数
