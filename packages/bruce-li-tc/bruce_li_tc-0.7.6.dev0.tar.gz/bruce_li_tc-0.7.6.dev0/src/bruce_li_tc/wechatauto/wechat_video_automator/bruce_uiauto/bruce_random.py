import random
class FairSelector:
    def __init__(self, items):
        self.items = items.copy()
        self.pool = []

    def select(self):
        if not self.pool:
            self.pool = self.items.copy()
            random.shuffle(self.pool)  # 打乱顺序
        return self.pool.pop()  # 弹出最后一个元素