from .c基础处理 import c变量, cpp类型, list初始化列表


class StdList(c变量):
    def __init__(
            self,
            初始化列表: list初始化列表,
            名字: str, 是参数: bool) -> None:
        self.初始化列表 = 初始化列表
        if 初始化列表.类型 == cpp类型.ANY:
            super().__init__(f'std::vector<{初始化列表.类型}>', 名字, 是参数)
        else:
            super().__init__(f'{初始化列表.类型}', 名字, 是参数)

    def __getitem__(self, key):
        return f'{self}[{key}]'

    def __setitem__(self, key, value):
        return f'{self}[{key}] = {value};'

    def 初始化(self, 初始值, 强转类型: str | None):
        if self.初始化列表.类型 == cpp类型.ANY:
            return super().初始化(初始值)
        return f'{self.类型} {self.名字}[] = {初始值};'
