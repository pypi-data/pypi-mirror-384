
class KeyConverter:
    """
    键名转换工具类
    提供字典和列表中键名的转换功能

    设计说明:
    1. 所有方法都是静态方法(@staticmethod)，无需实例化即可使用
    2. 类本身不维护任何状态，只提供纯功能方法
    3. 支持基本字典转换、列表转换、深度转换等多种场景

    使用示例:
        >>> data = {"first_name": "Alice", "last_name": "Smith"}
        >>> KeyConverter.convert_dict_keys(data, {"first_name": "firstName"})
        {"firstName": "Alice", "last_name": "Smith"}
    """

    @staticmethod
    def convert_dict_keys(
            data: dict,
            key_mapping: dict,
            keep_unmapped: bool = True
    ) -> dict:
        """
        转换单个字典的键名

        参数:
            data: 要转换的原始字典
            key_mapping: 键名映射规则 {旧键: 新键}
            keep_unmapped: 是否保留未映射的键(默认True)

        返回:
            转换后的新字典

        示例:
            >>> data = {"name": "Alice", "age": 30}
            >>> KeyConverter.convert_dict_keys(data, {"name": "full_name"})
            {"full_name": "Alice", "age": 30}
        """
        result = {}
        for key, value in data.items():
            if key in key_mapping:
                result[key_mapping[key]] = value
            elif keep_unmapped:
                result[key] = value
        return result

    @staticmethod
    def convert_list_keys(
            data_list: list[dict],
            key_mapping: dict,
            keep_unmapped: bool = True
    ) -> list[dict]:
        """
        转换字典列表中所有字典的键名

        参数:
            data_list: 字典列表
            key_mapping: 键名映射规则 {旧键: 新键}
            keep_unmapped: 是否保留未映射的键(默认True)

        返回:
            转换后的字典列表

        示例:
            >>> data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
            >>> KeyConverter.convert_list_keys(data, {"id": "identifier"})
            [{"identifier": 1, "name": "A"}, {"identifier": 2, "name": "B"}]
        """
        return [
            KeyConverter.convert_dict_keys(item, key_mapping, keep_unmapped)
            for item in data_list
        ]

    @staticmethod
    def deep_convert_keys(
            data,
            key_mapping: dict,
            keep_unmapped: bool = True
    ):
        """
        深度转换键名(支持嵌套字典和列表)

        参数:
            data: 要转换的数据(可以是dict/list/基本类型)
            key_mapping: 键名映射规则
            keep_unmapped: 是否保留未映射的键

        返回:
            转换后的数据

        示例:
            >>> data = {"user": {"first_name": "Alice"}, "items": [{"item_id": 1}]}
            >>> mapping = {"first_name": "firstName", "item_id": "id"}
            >>> KeyConverter.deep_convert_keys(data, mapping)
            {"user": {"firstName": "Alice"}, "items": [{"id": 1}]}
        """
        if isinstance(data, dict):
            converted = {}
            for key, value in data.items():
                new_key = key_mapping.get(key, key) if keep_unmapped or key in key_mapping else None
                new_value = KeyConverter.deep_convert_keys(value, key_mapping, keep_unmapped)
                if new_key is not None:
                    converted[new_key] = new_value
            return converted

        elif isinstance(data, list):
            return [KeyConverter.deep_convert_keys(item, key_mapping, keep_unmapped) for item in data]

        else:
            return data

    @staticmethod
    def reverse_mapping(mapping: dict) -> dict:
        """
        反转键名映射规则

        参数:
            mapping: 原始映射规则 {旧键: 新键}

        返回:
            反转后的映射规则 {新键: 旧键}

        示例:
            >>> KeyConverter.reverse_mapping({"id": "identifier"})
            {"identifier": "id"}
        """
        return {new_key: old_key for old_key, new_key in mapping.items()}

    @staticmethod
    def convert_keys_with_callback(
            data: dict,
            key_callback: callable,
            keep_unmapped: bool = True
    ) -> dict:
        """
        使用回调函数转换键名

        参数:
            data: 要转换的字典
            key_callback: 键名转换函数(接受旧键名，返回新键名)
            keep_unmapped: 是否保留未处理的键

        返回:
            转换后的字典

        示例:
            >>> def to_upper(key): return key.upper()
            >>> KeyConverter.convert_keys_with_callback({"name": "Alice"}, to_upper)
            {"NAME": "Alice"}
        """
        result = {}
        for key, value in data.items():
            new_key = key_callback(key)
            if keep_unmapped or new_key != key:
                result[new_key] = value
        return result

    @staticmethod
    def transform_data(
            data,
            key_mapping: dict = None,
            value_transformer: callable = None,
            key_formatter: callable = None
    ) -> dict:
        """
        综合转换方法(键名和值都可以转换)

        参数:
            data: 要转换的数据
            key_mapping: 键名映射规则(可选)
            value_transformer: 值转换函数(可选)
            key_formatter: 键名格式化函数(可选)

        返回:
            转换后的数据

        示例:
            >>> data = {"first_name": "alice", "age": "30"}
            >>> KeyConverter.transform_data(
            ...     data,
            ...     key_mapping={"first_name": "firstName"},
            ...     value_transformer=lambda v: v.capitalize() if isinstance(v, str) else v,
            ...     key_formatter=str.lower
            ... )
            {"firstname": "Alice", "age": "30"}
        """
        # 首先转换键名
        if key_mapping:
            data = KeyConverter.deep_convert_keys(data, key_mapping)

        # 然后格式化键名
        if key_formatter:
            data = KeyConverter.convert_keys_with_callback(data, key_formatter)

        # 最后转换值
        if value_transformer:
            if isinstance(data, dict):
                return {k: value_transformer(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [value_transformer(item) for item in data]

        return data