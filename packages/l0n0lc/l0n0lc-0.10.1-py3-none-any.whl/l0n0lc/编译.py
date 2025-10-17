from typing import Union, List
import subprocess


class cpp编译器:
    def __init__(self) -> None:
        self.编译器 = '/bin/c++'
        self.include目录列表 = []
        self.库目录列表 = []
        self.链接库 = []
        self.编译选项 = []
        self.输出编译指令 = False

    def 设置编译器(self, 编译器地址: str):
        self.编译器 = 编译器地址

    def 添加include目录(self, 目录: Union[str, List[str]]):
        if isinstance(目录, str):
            self.include目录列表.append(目录)
            return
        self.include目录列表 += 目录

    def 添加库目录(self, 目录: Union[str, List[str]]):
        if isinstance(目录, str):
            self.库目录列表.append(目录)
            return
        self.库目录列表 += 目录

    def 添加链接库(self, 库名: Union[str, List[str]]):
        if isinstance(库名, str):
            self.链接库.append(库名)
            return
        self.链接库 += 库名

    def 添加编译选项(self, 选项: Union[str, List[str]]):
        if isinstance(选项, str):
            self.编译选项.append(选项)
            return
        self.编译选项 += 选项

    def 编译文件(self, 文件路径: Union[List[str], str], 输出路径: str):
        编译指令 = [self.编译器]
        include指令 = [f'-I{目录}' for 目录 in self.include目录列表]
        库目录指令 = [f'-L{目录}' for 目录 in self.库目录列表]
        库链接指令 = [f'-l{库名}' for 库名 in self.链接库]
        编译指令 += include指令 + 库目录指令 + 库链接指令 + self.编译选项
        if isinstance(文件路径, list):
            编译指令 += 文件路径
        else:
            编译指令.append(文件路径)
        编译指令.append('-o')
        编译指令.append(输出路径)
        if self.输出编译指令:
            print(编译指令)
        subprocess.run(编译指令)

    def 编译为动态库(self, 文件路径: Union[List[str], str], 输出路径: str):
        self.添加编译选项('-fPIC')
        self.添加编译选项('--shared')
        self.添加编译选项('-O2')
        self.编译文件(文件路径, 输出路径)
