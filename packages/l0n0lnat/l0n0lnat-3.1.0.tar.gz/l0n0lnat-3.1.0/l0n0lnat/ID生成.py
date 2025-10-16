from typing import List, Dict, Any, Union


class 循环ID生成器:
    def __init__(
            self, 最大值: int = 0xFFFFFFFF,
            已经存在的ID: Union[List[int], Dict[int, Any], None] = None) -> None:
        self.当前ID = 0
        self.最大值 = 最大值
        self.已经存在的ID = 已经存在的ID

    def 自增1(self):
        self.当前ID = (self.当前ID + 1) % self.最大值

    def __call__(self, 已经存在的ID: Union[List[int], Dict[int, Any], None] = None):
        已经存在的ID = 已经存在的ID or self.已经存在的ID
        if isinstance(已经存在的ID, list):
            while self.当前ID in 已经存在的ID:
                self.自增1()
        elif isinstance(已经存在的ID, dict):
            while 已经存在的ID.get(self.当前ID) is not None:
                self.自增1()
        ret = self.当前ID
        self.自增1()
        return ret
