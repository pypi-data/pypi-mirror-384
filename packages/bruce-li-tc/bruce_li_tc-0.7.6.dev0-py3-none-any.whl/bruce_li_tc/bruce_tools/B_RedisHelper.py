"""
B_RedisHelper.py - Redis 操作高级封装
支持连接池管理、多种数据类型操作、事务和发布订阅
"""

import redis
import time
import json


class RedisHelper:
    """
    Redis 操作工具类
    包含连接池管理、多种数据类型操作、事务和发布订阅功能
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None,
                 max_connections=10, decode_responses=True):
        """
        初始化Redis助手

        参数:
            host: Redis主机地址 (默认'localhost')
            port: Redis端口 (默认6379)
            db: 数据库索引 (默认0)
            password: 认证密码 (默认None)
            max_connections: 连接池最大连接数 (默认10)
            decode_responses: 是否解码响应 (默认True)

        示例:
            # 创建Redis助手实例
            redis_helper = RedisHelper(
                host='127.0.0.1',
                port=6379,
                db=0,
                password='your_password',
                max_connections=20
            )

            # 设置键值
            redis_helper.set('test_key', 'Hello Redis')

            # 获取键值
            value = redis_helper.get('test_key')
            print("获取的值:", value)
        """
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        print(f"[RedisHelper] 已创建连接池 (最大连接数: {max_connections})")

    def get_connection(self):
        """
        从连接池获取Redis连接

        返回: Redis连接对象

        示例:
            # 获取Redis连接
            conn = redis_helper.get_connection()

            # 执行操作
            conn.set('temp_key', '临时值')
            value = conn.get('temp_key')
            print("临时值:", value)

            # 删除键
            conn.delete('temp_key')

            # 归还连接 (连接池会自动管理)
        """
        conn = redis.Redis(connection_pool=self.pool)
        print("[RedisHelper] 获取Redis连接")
        return conn

    def close_pool(self):
        """
        关闭连接池

        示例:
            # 程序结束时关闭连接池
            redis_helper.close_pool()
            print("Redis连接池已关闭")
        """
        self.pool.disconnect()
        print("[RedisHelper] Redis连接池已关闭")

    # ==================== 字符串操作 ====================

    def set(self, key, value, ex=None, px=None, nx=False, xx=False):
        """
        设置键值对

        参数:
            key: 键名
            value: 值
            ex: 过期时间(秒)
            px: 过期时间(毫秒)
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置
        返回: 设置是否成功 (bool)

        示例:
            # 设置普通键值
            redis_helper.set('username', 'john_doe')

            # 设置带过期时间的键值 (30秒后过期)
            redis_helper.set('session:123', 'user_data', ex=30)

            # 仅当键不存在时设置
            success = redis_helper.set('unique_id', '12345', nx=True)
            if success:
                print("设置成功")
            else:
                print("键已存在，未设置")
        """
        conn = self.get_connection()
        result = conn.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        print(f"[SET] 设置键: {key} | 值: {value[:20] if isinstance(value, str) else value} | 结果: {bool(result)}")
        return bool(result)

    def get(self, key):
        """
        获取键值

        参数:
            key: 键名
        返回: 键值 (str) 或 None

        示例:
            # 获取键值
            value = redis_helper.get('username')
            if value:
                print("用户名:", value)
            else:
                print("键不存在")
        """
        conn = self.get_connection()
        result = conn.get(key)
        print(f"[GET] 获取键: {key} | 结果: {result[:20] if result else 'None'}")
        return result

    def mset(self, mapping):
        """
        设置多个键值对

        参数:
            mapping: 键值对字典 {key: value}
        返回: 是否成功 (bool)

        示例:
            # 批量设置键值
            data = {
                'user:1:name': 'Alice',
                'user:1:email': 'alice@example.com',
                'user:1:age': 30
            }
            redis_helper.mset(data)
            print("批量设置完成")
        """
        conn = self.get_connection()
        result = conn.mset(mapping)
        print(f"[MSET] 批量设置 {len(mapping)} 个键值对 | 结果: {result}")
        return result

    def mget(self, keys):
        """
        获取多个键值

        参数:
            keys: 键名列表
        返回: 值列表 (包含None)

        示例:
            # 批量获取键值
            keys = ['user:1:name', 'user:1:email', 'user:1:age']
            values = redis_helper.mget(keys)
            print("批量获取结果:", values)
        """
        conn = self.get_connection()
        result = conn.mget(keys)
        print(f"[MGET] 批量获取 {len(keys)} 个键 | 结果: {result}")
        return result

    def incr(self, key, amount=1):
        """
        增加键的整数值

        参数:
            key: 键名
            amount: 增加量 (默认1)
        返回: 增加后的值

        示例:
            # 增加计数器
            count = redis_helper.incr('page_views')
            print("当前访问量:", count)

            # 增加指定值
            new_balance = redis_helper.incr('user:1:balance', 100)
            print("新余额:", new_balance)
        """
        conn = self.get_connection()
        result = conn.incr(key, amount)
        print(f"[INCR] 增加键: {key} | 增加量: {amount} | 新值: {result}")
        return result

    def expire(self, key, seconds):
        """
        设置键的过期时间

        参数:
            key: 键名
            seconds: 过期时间(秒)
        返回: 设置是否成功 (bool)

        示例:
            # 设置键过期
            redis_helper.set('temp_data', '重要数据')
            redis_helper.expire('temp_data', 3600)  # 1小时后过期
            print("已设置过期时间")
        """
        conn = self.get_connection()
        result = conn.expire(key, seconds)
        print(f"[EXPIRE] 设置键过期: {key} | 秒数: {seconds} | 结果: {result}")
        return result

    # ==================== 哈希操作 ====================

    def hset(self, name, key, value):
        """
        设置哈希字段值

        参数:
            name: 哈希名
            key: 字段名
            value: 字段值
        返回: 新创建的字段数量

        示例:
            # 设置用户信息
            redis_helper.hset('user:1', 'name', 'Bob')
            redis_helper.hset('user:1', 'email', 'bob@example.com')
            redis_helper.hset('user:1', 'age', 25)
            print("用户信息已设置")
        """
        conn = self.get_connection()
        result = conn.hset(name, key, value)
        print(f"[HSET] 设置哈希字段: {name}.{key} | 值: {value} | 结果: {result}")
        return result

    def hget(self, name, key):
        """
        获取哈希字段值

        参数:
            name: 哈希名
            key: 字段名
        返回: 字段值 (str) 或 None

        示例:
            # 获取用户邮箱
            email = redis_helper.hget('user:1', 'email')
            print("用户邮箱:", email)
        """
        conn = self.get_connection()
        result = conn.hget(name, key)
        print(f"[HGET] 获取哈希字段: {name}.{key} | 结果: {result}")
        return result

    def hgetall(self, name):
        """
        获取所有哈希字段和值

        参数:
            name: 哈希名
        返回: 字段-值字典

        示例:
            # 获取所有用户信息
            user_data = redis_helper.hgetall('user:1')
            print("用户信息:", user_data)
        """
        conn = self.get_connection()
        result = conn.hgetall(name)
        print(f"[HGETALL] 获取所有哈希字段: {name} | 字段数量: {len(result)}")
        return result

    def hmset(self, name, mapping):
        """
        设置多个哈希字段值 (已弃用，推荐使用hset)

        参数:
            name: 哈希名
            mapping: 字段-值字典
        返回: 是否成功

        示例:
            # 批量设置用户信息
            user_info = {
                'name': 'Charlie',
                'email': 'charlie@example.com',
                'age': 35
            }
            redis_helper.hmset('user:2', user_info)
            print("批量设置完成")
        """
        conn = self.get_connection()
        result = conn.hmset(name, mapping)
        print(f"[HMSET] 批量设置哈希字段: {name} | 字段数量: {len(mapping)} | 结果: {result}")
        return result

    # ==================== 列表操作 ====================

    def lpush(self, name, *values):
        """
        从列表左侧添加元素

        参数:
            name: 列表名
            values: 要添加的值
        返回: 添加后列表的长度

        示例:
            # 添加消息到队列
            redis_helper.lpush('message_queue', '消息1', '消息2', '消息3')
            print("消息已添加到队列")
        """
        conn = self.get_connection()
        result = conn.lpush(name, *values)
        print(f"[LPUSH] 左侧添加列表元素: {name} | 元素数量: {len(values)} | 新长度: {result}")
        return result

    def rpush(self, name, *values):
        """
        从列表右侧添加元素

        参数:
            name: 列表名
            values: 要添加的值
        返回: 添加后列表的长度

        示例:
            # 添加任务到队列
            redis_helper.rpush('task_queue', '任务A', '任务B', '任务C')
            print("任务已添加到队列")
        """
        conn = self.get_connection()
        result = conn.rpush(name, *values)
        print(f"[RPUSH] 右侧添加列表元素: {name} | 元素数量: {len(values)} | 新长度: {result}")
        return result

    def lpop(self, name):
        """
        从列表左侧弹出元素

        参数:
            name: 列表名
        返回: 弹出的元素 (str) 或 None

        示例:
            # 处理队列消息
            message = redis_helper.lpop('message_queue')
            if message:
                print("处理消息:", message)
            else:
                print("队列为空")
        """
        conn = self.get_connection()
        result = conn.lpop(name)
        print(f"[LPOP] 左侧弹出列表元素: {name} | 结果: {result}")
        return result

    def rpop(self, name):
        """
        从列表右侧弹出元素

        参数:
            name: 列表名
        返回: 弹出的元素 (str) 或 None

        示例:
            # 处理任务队列
            task = redis_helper.rpop('task_queue')
            if task:
                print("执行任务:", task)
            else:
                print("没有任务")
        """
        conn = self.get_connection()
        result = conn.rpop(name)
        print(f"[RPOP] 右侧弹出列表元素: {name} | 结果: {result}")
        return result

    def lrange(self, name, start=0, end=-1):
        """
        获取列表指定范围内的元素

        参数:
            name: 列表名
            start: 起始索引 (默认0)
            end: 结束索引 (默认-1表示最后)
        返回: 元素列表

        示例:
            # 获取最近10条消息
            messages = redis_helper.lrange('message_queue', 0, 9)
            print("最近10条消息:", messages)
        """
        conn = self.get_connection()
        result = conn.lrange(name, start, end)
        print(f"[LRANGE] 获取列表范围: {name}[{start}:{end}] | 元素数量: {len(result)}")
        return result

    # ==================== 集合操作 ====================

    def sadd(self, name, *values):
        """
        向集合添加元素

        参数:
            name: 集合名
            values: 要添加的值
        返回: 添加的元素数量

        示例:
            # 添加标签
            redis_helper.sadd('article:1:tags', '技术', 'Redis', '数据库')
            print("标签已添加")
        """
        conn = self.get_connection()
        result = conn.sadd(name, *values)
        print(f"[SADD] 添加集合元素: {name} | 元素数量: {len(values)} | 新元素数: {result}")
        return result

    def smembers(self, name):
        """
        获取集合所有元素

        参数:
            name: 集合名
        返回: 元素集合

        示例:
            # 获取所有标签
            tags = redis_helper.smembers('article:1:tags')
            print("文章标签:", tags)
        """
        conn = self.get_connection()
        result = conn.smembers(name)
        print(f"[SMEMBERS] 获取集合所有元素: {name} | 元素数量: {len(result)}")
        return result

    def sismember(self, name, value):
        """
        检查元素是否在集合中

        参数:
            name: 集合名
            value: 要检查的值
        返回: 是否包含 (bool)

        示例:
            # 检查标签是否存在
            if redis_helper.sismember('article:1:tags', 'Redis'):
                print("包含Redis标签")
            else:
                print("不包含Redis标签")
        """
        conn = self.get_connection()
        result = conn.sismember(name, value)
        print(f"[SISMEMBER] 检查集合元素: {name} 包含 {value}? | 结果: {result}")
        return result

    # ==================== 有序集合操作 ====================

    def zadd(self, name, mapping, nx=False, xx=False, ch=False, incr=False):
        """
        向有序集合添加元素

        参数:
            name: 有序集合名
            mapping: 成员-分值字典 {member: score}
            nx: 仅添加新元素
            xx: 仅更新已存在元素
            ch: 返回变更数量
            incr: 增量模式
        返回: 添加的元素数量

        示例:
            # 添加排行榜数据
            leaderboard = {
                'player1': 1000,
                'player2': 850,
                'player3': 1200
            }
            redis_helper.zadd('game_leaderboard', leaderboard)
            print("排行榜数据已添加")
        """
        conn = self.get_connection()
        result = conn.zadd(name, mapping, nx=nx, xx=xx, ch=ch, incr=incr)
        print(f"[ZADD] 添加有序集合元素: {name} | 元素数量: {len(mapping)} | 结果: {result}")
        return result

    def zrange(self, name, start=0, end=-1, withscores=False, desc=False):
        """
        获取有序集合指定范围的元素

        参数:
            name: 有序集合名
            start: 起始索引
            end: 结束索引
            withscores: 是否返回分值 (默认False)
            desc: 是否降序排序 (默认False)
        返回: 元素列表 (或带分值的元组列表)

        示例:
            # 获取排行榜前10名
            top_players = redis_helper.zrange('game_leaderboard', 0, 9, desc=True, withscores=True)
            print("排行榜前10名:", top_players)
        """
        conn = self.get_connection()
        if desc:
            result = conn.zrevrange(name, start, end, withscores=withscores)
        else:
            result = conn.zrange(name, start, end, withscores=withscores)

        print(f"[ZRANGE] 获取有序集合范围: {name}[{start}:{end}] | 元素数量: {len(result)}")
        return result

    def zrank(self, name, member, reverse=False):
        """
        获取有序集合成员的排名

        参数:
            name: 有序集合名
            member: 成员名
            reverse: 是否按分值降序排名 (默认False)
        返回: 排名 (从0开始) 或 None

        示例:
            # 获取玩家排名
            rank = redis_helper.zrank('game_leaderboard', 'player1', reverse=True)
            if rank is not None:
                print(f"玩家排名: {rank + 1}")
            else:
                print("玩家不在排行榜中")
        """
        conn = self.get_connection()
        if reverse:
            result = conn.zrevrank(name, member)
        else:
            result = conn.zrank(name, member)

        print(f"[ZRANK] 获取成员排名: {name}.{member} | 结果: {result}")
        return result

    # ==================== 发布订阅 ====================

    def publish(self, channel, message):
        """
        发布消息到频道

        参数:
            channel: 频道名
            message: 消息内容
        返回: 收到消息的订阅者数量

        示例:
            # 发布通知
            subscribers = redis_helper.publish('notifications', '系统维护通知')
            print(f"消息已发布给 {subscribers} 个订阅者")
        """
        conn = self.get_connection()
        result = conn.publish(channel, message)
        print(f"[PUBLISH] 发布消息到频道: {channel} | 消息: {message[:20]}... | 订阅者数: {result}")
        return result

    def subscribe(self, channels, callback, timeout=None):
        """
        订阅频道并处理消息

        参数:
            channels: 频道列表
            callback: 消息回调函数 (接收message参数)
            timeout: 超时时间(秒) (默认None)

        示例:
            # 定义消息处理函数
            def handle_message(message):
                print(f"收到消息: 频道={message['channel']}, 内容={message['data']}")

            # 订阅频道
            redis_helper.subscribe(['news', 'updates'], handle_message)
            print("开始监听频道...")

            # 注意: 此方法会阻塞当前线程
        """
        conn = self.get_connection()
        pubsub = conn.pubsub()
        pubsub.subscribe(*channels)

        print(f"[SUBSCRIBE] 订阅频道: {channels}")

        # 处理消息
        for message in pubsub.listen():
            if message['type'] == 'message':
                callback(message)

            # 检查超时
            if timeout is not None and time.time() > start_time + timeout:
                break

    # ==================== 高级功能 ====================

    def pipeline(self):
        """
        创建管道对象

        返回: 管道对象

        示例:
            # 使用管道执行多个命令
            pipe = redis_helper.pipeline()

            # 添加多个操作
            pipe.set('counter', 0)
            pipe.incr('counter')
            pipe.incrby('counter', 5)
            pipe.get('counter')

            # 执行所有操作
            results = pipe.execute()
            print("管道执行结果:", results)
        """
        conn = self.get_connection()
        pipe = conn.pipeline()
        print("[PIPELINE] 创建管道")
        return pipe

    def transaction(self, func, *watches, **kwargs):
        """
        执行事务

        参数:
            func: 事务函数 (接收管道参数)
            watches: 要监视的键
            kwargs: 其他事务选项
        返回: 事务执行结果

        示例:
            # 定义事务函数
            def transfer_funds(pipe):
                # 获取当前余额
                balance = int(pipe.get('account:balance') or 0)

                # 检查余额是否足够
                if balance < 100:
                    raise ValueError("余额不足")

                # 执行转账操作
                pipe.multi()
                pipe.decrby('account:balance', 100)
                pipe.incrby('receiver:balance', 100)

            # 执行事务
            try:
                result = redis_helper.transaction(
                    transfer_funds,
                    'account:balance',
                    'receiver:balance'
                )
                print("转账成功")
            except Exception as e:
                print("转账失败:", str(e))
        """
        conn = self.get_connection()
        print(f"[TRANSACTION] 开始事务 | 监视键: {watches}")

        try:
            result = conn.transaction(func, *watches, **kwargs)
            print("[TRANSACTION] 事务执行成功")
            return result
        except Exception as e:
            print(f"[TRANSACTION] 事务执行失败: {str(e)}")
            raise

    def json_set(self, key, obj, ex=None):
        """
        将Python对象存储为JSON字符串

        参数:
            key: 键名
            obj: Python对象
            ex: 过期时间(秒)
        返回: 是否成功

        示例:
            # 存储用户信息
            user = {
                'id': 1,
                'name': 'David',
                'email': 'david@example.com',
                'preferences': {'theme': 'dark', 'notifications': True}
            }
            redis_helper.json_set('user:1', user)
            print("用户信息已存储")
        """
        json_str = json.dumps(obj)
        result = self.set(key, json_str, ex=ex)
        print(f"[JSON_SET] 存储JSON对象: {key} | 类型: {type(obj)} | 结果: {result}")
        return result

    def json_get(self, key):
        """
        获取并解析JSON字符串为Python对象

        参数:
            key: 键名
        返回: Python对象 或 None

        示例:
            # 获取用户信息
            user = redis_helper.json_get('user:1')
            if user:
                print("用户信息:", user)
                print("用户主题偏好:", user['preferences']['theme'])
        """
        json_str = self.get(key)
        if json_str is None:
            return None

        try:
            obj = json.loads(json_str)
            print(f"[JSON_GET] 解析JSON对象: {key} | 类型: {type(obj)}")
            return obj
        except json.JSONDecodeError:
            print(f"[JSON_GET] 错误: 无法解析JSON数据 (键: {key})")
            return None

    # ==================== 键管理 ====================

    def delete(self, *keys):
        """
        删除一个或多个键

        参数:
            keys: 键名列表
        返回: 删除的键数量

        示例:
            # 删除单个键
            deleted = redis_helper.delete('temp_key')
            print(f"删除了 {deleted} 个键")

            # 删除多个键
            deleted = redis_helper.delete('key1', 'key2', 'key3')
            print(f"删除了 {deleted} 个键")
        """
        conn = self.get_connection()
        result = conn.delete(*keys)
        print(f"[DELETE] 删除键: {keys} | 删除数量: {result}")
        return result

    def exists(self, *keys):
        """
        检查一个或多个键是否存在

        参数:
            keys: 键名列表
        返回: 存在的键数量

        示例:
            # 检查键是否存在
            count = redis_helper.exists('user:1', 'user:2', 'user:3')
            print(f"{count} 个用户存在")
        """
        conn = self.get_connection()
        result = conn.exists(*keys)
        print(f"[EXISTS] 检查键是否存在: {keys} | 存在数量: {result}")
        return result

    def keys(self, pattern='*'):
        """
        查找匹配模式的键

        参数:
            pattern: 匹配模式 (默认'*')
        返回: 匹配的键列表

        示例:
            # 查找所有用户键
            user_keys = redis_helper.keys('user:*')
            print("用户键列表:", user_keys)
        """
        conn = self.get_connection()
        result = conn.keys(pattern)
        print(f"[KEYS] 查找键模式: {pattern} | 匹配数量: {len(result)}")
        return result


# 示例使用
# if __name__ == "__main__":
#     # 创建Redis助手实例 (使用示例配置)
#     redis_helper = RedisHelper(
#         host='localhost',
#         port=6379,
#         db=0,
#         password=None,
#         max_connections=5
#     )
#
#     try:
#         # 1. 字符串操作示例
#         print("\n=== 字符串操作示例 ===")
#         redis_helper.set('test_key', 'Hello Redis')
#         value = redis_helper.get('test_key')
#         print("获取的值:", value)
#
#         # 2. 哈希操作示例
#         print("\n=== 哈希操作示例 ===")
#         redis_helper.hset('user:1001', 'name', 'Alice')
#         redis_helper.hset('user:1001', 'email', 'alice@example.com')
#         user_email = redis_helper.hget('user:1001', 'email')
#         print("用户邮箱:", user_email)
#
#         # 3. 列表操作示例
#         print("\n=== 列表操作示例 ===")
#         redis_helper.lpush('tasks', 'task1', 'task2', 'task3')
#         task = redis_helper.rpop('tasks')
#         print("处理任务:", task)
#
#         # 4. 集合操作示例
#         print("\n=== 集合操作示例 ===")
#         redis_helper.sadd('article:2001:tags', 'Python', 'Redis', 'Database')
#         tags = redis_helper.smembers('article:2001:tags')
#         print("文章标签:", tags)
#
#         # 5. 有序集合示例
#         print("\n=== 有序集合示例 ===")
#         redis_helper.zadd('leaderboard', {'player1': 100, 'player2': 85, 'player3': 120})
#         top_players = redis_helper.zrange('leaderboard', 0, 2, desc=True, withscores=True)
#         print("排行榜前三:", top_players)
#
#         # 6. JSON操作示例
#         print("\n=== JSON操作示例 ===")
#         user_data = {
#             'id': 1001,
#             'name': 'Bob',
#             'preferences': {
#                 'theme': 'dark',
#                 'language': 'en'
#             }
#         }
#         redis_helper.json_set('user:1001:full', user_data)
#         retrieved_data = redis_helper.json_get('user:1001:full')
#         print("用户完整数据:", retrieved_data)
#
#         # 7. 管道操作示例
#         print("\n=== 管道操作示例 ===")
#         pipe = redis_helper.pipeline()
#         pipe.set('counter', 0)
#         pipe.incr('counter')
#         pipe.incrby('counter', 10)
#         pipe.get('counter')
#         results = pipe.execute()
#         print("管道执行结果:", results)
#
#         # 8. 键管理示例
#         print("\n=== 键管理示例 ===")
#         keys = redis_helper.keys('*')
#         print("所有键:", keys)
#
#         # 清理测试数据
#         redis_helper.delete('test_key', 'user:1001', 'tasks', 'article:2001:tags',
#                             'leaderboard', 'user:1001:full', 'counter')
#     finally:
#         # 关闭连接池
#         redis_helper.close_pool()