"""
B_RandomTool.py - 高级随机数生成工具
封装Python随机数库的常用功能，支持多线程安全操作
"""

import random
import string
import threading
from typing import Any, List, Tuple, Dict, Union, Sequence, Optional


class RandomTool:
    """
    随机数生成工具类，封装Python random模块的常用功能
    支持多线程安全操作，每个线程有独立的随机状态

    多线程使用注意事项:
        1. 每个线程使用独立的RandomTool实例
        2. 避免跨线程共享同一个实例
        3. 使用线程局部存储确保随机状态隔离
        4. 对于关键应用，考虑使用更安全的secrets模块
    """

    def __init__(self, seed: Any = None):
        """
        初始化随机工具

        :param seed: 随机种子 (可选)

        示例:
            # 创建随机工具实例
            rand = RandomTool()

            # 使用种子创建可复现的随机序列
            seeded_rand = RandomTool(42)
            num1 = seeded_rand.randint(1, 100)
            num2 = seeded_rand.randint(1, 100)
            print(f"可复现的随机数: {num1}, {num2}")
        """
        self._local = threading.local()
        self.seed = seed

    @property
    def random(self) -> random.Random:
        """获取当前线程的随机数生成器"""
        if not hasattr(self._local, "random"):
            self._local.random = random.Random(self.seed)
        return self._local.random

    def randint(self, a: int, b: int) -> int:
        """
        生成指定范围内的随机整数 [a, b]

        :param a: 最小值 (整数)
        :param b: 最大值 (整数)
        :return: 随机整数

        示例:
            # 生成1到100之间的随机整数
            random_num = rand.randint(1, 100)
            print(f"随机整数: {random_num}")
        """
        return self.random.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        """
        生成指定范围内的随机浮点数 [a, b]

        :param a: 最小值 (浮点数)
        :param b: 最大值 (浮点数)
        :return: 随机浮点数

        示例:
            # 生成0.0到1.0之间的随机浮点数
            random_float = rand.uniform(0.0, 1.0)
            print(f"随机浮点数: {random_float:.4f}")
        """
        return self.random.uniform(a, b)

    def choice(self, seq: Sequence[Any]) -> Any:
        """
        从序列中随机选择一个元素

        :param seq: 序列 (列表/元组/字符串等)
        :return: 随机选择的元素

        示例:
            # 从列表中随机选择一项
            fruits = ['apple', 'banana', 'cherry', 'date']
            selected = rand.choice(fruits)
            print(f"随机选择的水果: {selected}")
        """
        return self.random.choice(seq)

    def choices(self, seq: Sequence[Any], k: int = 1, weights: Optional[List[float]] = None) -> List[Any]:
        """
        从序列中随机选择k个元素（可重复）

        :param seq: 序列
        :param k: 选择数量 (整数)
        :param weights: 权重列表 (可选)
        :return: 随机选择的元素列表

        示例:
            # 从列表中随机选择3个元素（可重复）
            colors = ['red', 'green', 'blue']
            selected = rand.choices(colors, k=3)
            print(f"随机选择的颜色: {selected}")

            # 带权重的随机选择
            weighted_choices = rand.choices(
                ['prize1', 'prize2', 'prize3'],
                weights=[0.1, 0.3, 0.6],
                k=5
            )
            print(f"带权重的随机奖品: {weighted_choices}")
        """
        return self.random.choices(seq, k=k, weights=weights)

    def sample(self, seq: Sequence[Any], k: int) -> List[Any]:
        """
        从序列中随机选择k个不重复的元素

        :param seq: 序列
        :param k: 选择数量 (整数)
        :return: 随机选择的元素列表

        示例:
            # 从1到100中选择5个不重复的数字
            numbers = list(range(1, 101))
            selected = rand.sample(numbers, 5)
            print(f"随机选择的5个不重复数字: {selected}")
        """
        return self.random.sample(seq, k)

    def shuffle(self, seq: List[Any]) -> None:
        """
        随机打乱序列（原地修改）

        :param seq: 序列 (列表)

        示例:
            # 打乱一副牌
            deck = list(range(1, 53))
            rand.shuffle(deck)
            print(f"洗牌后的前5张: {deck[:5]}")
        """
        self.random.shuffle(seq)

    def random_string(self, length: int = 8,
                      chars: str = string.ascii_letters + string.digits) -> str:
        """
        生成随机字符串

        :param length: 字符串长度 (整数)
        :param chars: 可选字符集 (字符串)
        :return: 随机字符串

        示例:
            # 生成10个字符的随机字符串
            rand_str = rand.random_string(10)
            print(f"随机字符串: {rand_str}")

            # 生成只包含数字的随机字符串
            numeric_str = rand.random_string(6, string.digits)
            print(f"随机数字字符串: {numeric_str}")
        """
        return ''.join(self.random.choices(chars, k=length))

    def random_hex(self, length: int = 16) -> str:
        """
        生成随机十六进制字符串

        :param length: 字符串长度 (整数)
        :return: 十六进制字符串

        示例:
            # 生成32位十六进制字符串
            hex_str = rand.random_hex(32)
            print(f"随机十六进制字符串: {hex_str}")
        """
        return ''.join(self.random.choices(string.hexdigits.lower(), k=length))

    def random_bool(self, probability: float = 0.5) -> bool:
        """
        生成随机布尔值

        :param probability: True的概率 (0.0到1.0之间)
        :return: 随机布尔值

        示例:
            # 有70%概率返回True
            result = rand.random_bool(0.7)
            print(f"随机布尔值: {result}")
        """
        return self.random.random() < probability

    def gauss(self, mu: float, sigma: float) -> float:
        """
        生成符合高斯分布（正态分布）的随机数

        :param mu: 均值
        :param sigma: 标准差
        :return: 符合正态分布的随机数

        示例:
            # 生成均值为100，标准差为15的随机数
            score = rand.gauss(100, 15)
            print(f"智商测试分数: {score:.1f}")
        """
        return self.random.gauss(mu, sigma)

    def random_color(self, format: str = 'hex') -> Union[str, Tuple[int, int, int]]:
        """
        生成随机颜色

        :param format: 返回格式 ('hex' 或 'rgb')
        :return: 十六进制颜色字符串或RGB元组

        示例:
            # 生成随机十六进制颜色
            hex_color = rand.random_color()
            print(f"随机十六进制颜色: {hex_color}")

            # 生成RGB颜色
            rgb_color = rand.random_color(format='rgb')
            print(f"随机RGB颜色: {rgb_color}")
        """
        r = self.random.randint(0, 255)
        g = self.random.randint(0, 255)
        b = self.random.randint(0, 255)

        if format.lower() == 'hex':
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            return (r, g, b)

    def weighted_choice(self, items: Dict[Any, float]) -> Any:
        """
        根据权重随机选择一个键

        :param items: 键值对字典 {项: 权重}
        :return: 随机选择的键

        示例:
            # 根据权重随机选择奖励
            rewards = {
                "gold": 50,
                "silver": 30,
                "bronze": 20
            }
            selected = rand.weighted_choice(rewards)
            print(f"随机选择的奖励: {selected}")
        """
        choices = list(items.keys())
        weights = list(items.values())
        return self.random.choices(choices, weights=weights, k=1)[0]

    def random_date(self, start_date: Tuple[int, int, int],
                    end_date: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        生成随机日期 (年, 月, 日)

        :param start_date: 起始日期 (年, 月, 日)
        :param end_date: 结束日期 (年, 月, 日)
        :return: 随机日期 (年, 月, 日)

        示例:
            # 生成2000年到2023年之间的随机日期
            random_date = rand.random_date((2000, 1, 1), (2023, 12, 31))
            print(f"随机日期: {random_date[0]}-{random_date[1]}-{random_date[2]}")
        """
        start_year, start_month, start_day = start_date
        end_year, end_month, end_day = end_date

        # 计算起始和结束日期的序数
        start_ord = (start_year * 365) + (start_month * 31) + start_day
        end_ord = (end_year * 365) + (end_month * 31) + end_day

        # 生成随机序数
        random_ord = self.random.randint(start_ord, end_ord)

        # 转换回日期
        year = random_ord // 365
        remainder = random_ord % 365
        month = (remainder // 31) + 1
        day = (remainder % 31) + 1

        # 确保日期有效
        month = min(month, 12)
        day = min(day, 31)

        return (year, month, day)

    def reseed(self, seed: Any = None) -> None:
        """
        重新设置随机种子（影响当前线程的随机状态）

        :param seed: 新的随机种子

        示例:
            # 重置随机种子
            rand.reseed(123)
            num1 = rand.randint(1, 100)
            num2 = rand.randint(1, 100)

            # 再次重置相同种子应得到相同序列
            rand.reseed(123)
            same_num1 = rand.randint(1, 100)
            same_num2 = rand.randint(1, 100)

            assert num1 == same_num1
            assert num2 == same_num2
        """
        self.seed = seed
        if hasattr(self._local, "random"):
            self._local.random.seed(seed)