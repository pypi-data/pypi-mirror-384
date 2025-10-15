from .default_words import DEFAULT_BANNED_WORDS


class BannedWordsDetector:
    def __init__(self, banned_words:list[str]=None):
        """
        初始化违禁词检测器
        :param banned_words: 初始违禁词列表（可选），默认使用内置违禁词库
        """
        self.dfa_tree = {}
        self.end_flag = "__END__"

        # 使用默认词库或自定义词库
        words_to_add = banned_words if banned_words is not None else DEFAULT_BANNED_WORDS
        if words_to_add:
            self.add_words(words_to_add)

    def add_words(self, words:list[str])->None:
        """
        动态添加新违禁词（支持热更新）
        :param words: 字符串列表，如 ["裸聊", "代开发票"]
        """
        for word in words:
            normalized_word = word.lower()
            node = self.dfa_tree
            for char in normalized_word:
                node = node.setdefault(char, {})
            node[self.end_flag] = word  # 存储原始词

    def scan(self, text:str)->list[tuple[str,int,int]]:
        """
        扫描文本并返回违禁词及其位置
        :return: 列表，格式 [(违禁词, 起始索引, 结束索引)]
        """
        results = []
        text_lower = text.lower()
        i = 0
        while i < len(text_lower):
            char = text_lower[i]
            if char not in self.dfa_tree:
                i += 1
                continue

            node = self.dfa_tree[char]
            j = i + 1
            matched_word = None

            while j < len(text_lower) and text_lower[j] in node:
                node = node[text_lower[j]]
                if self.end_flag in node:
                    matched_word = node[self.end_flag]
                j += 1

            if matched_word:
                end_index = i + len(matched_word) - 1
                results.append((matched_word, i, end_index))
                i = j  # 跳过已匹配部分
            else:
                i += 1

        return results

    def contains_banned_words(self, text:str)->bool:
        """快速检查文本是否包含违禁词"""
        return bool(self.scan(text))