"""
B_MySQLHelper.py - MySQL 数据库操作高级封装
支持连接池管理、CRUD操作、事务处理和批量操作
"""

import pymysql
from dbutils.pooled_db import PooledDB
import time


class MySQLHelper:
    """
    MySQL 数据库操作工具类
    包含连接池管理、CRUD操作、事务处理和批量操作
    """

    def __init__(self, host, port, user, password, database,
                 pool_size=5, autocommit=False, charset='utf8mb4'):
        """
        初始化MySQL助手

        参数:
            host: 数据库主机地址
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
            pool_size: 连接池大小 (默认5)
            autocommit: 是否自动提交 (默认False)
            charset: 字符集 (默认'utf8mb4')

        示例:
            # 创建MySQL助手实例
            db = MySQLHelper(
                host='localhost',
                port=3306,
                user='root',
                password='123456',
                database='test_db',
                pool_size=10,
                autocommit=False
            )

            # 执行查询
            result = db.query("SELECT * FROM users WHERE age > %s", (25,))
            print("查询结果:", result)
        """
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=pool_size,
            mincached=2,
            maxcached=5,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            autocommit=autocommit,
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"[MySQLHelper] 已创建连接池 (大小: {pool_size})")

    def get_connection(self):
        """
        从连接池获取数据库连接

        返回: 数据库连接对象

        示例:
            # 获取数据库连接
            conn = db.get_connection()

            # 使用连接执行操作
            with conn.cursor() as cursor:
                cursor.execute("SELECT NOW()")
                result = cursor.fetchone()
                print("当前时间:", result['NOW()'])

            # 归还连接
            conn.close()
        """
        conn = self.pool.connection()
        print("[MySQLHelper] 获取数据库连接")
        return conn

    def query(self, sql, params=None):
        """
        执行查询操作

        参数:
            sql: SQL查询语句
            params: SQL参数 (元组或字典)
        返回: 查询结果列表 (字典形式)

        示例:
            # 查询所有用户
            users = db.query("SELECT * FROM users")

            # 带参数查询
            user = db.query(
                "SELECT * FROM users WHERE id = %s AND status = %s",
                (1, 'active')
            )

            # 命名参数查询
            user = db.query(
                "SELECT * FROM users WHERE id = %(id)s",
                {'id': 1}
            )
        """
        start_time = time.time()
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchall()
                elapsed = time.time() - start_time
                print(f"[Query] 执行查询: {sql[:50]}... | 耗时: {elapsed:.4f}s | 返回行数: {len(result)}")
                return result

    def execute(self, sql, params=None):
        """
        执行单条SQL语句 (INSERT/UPDATE/DELETE)

        参数:
            sql: SQL语句
            params: SQL参数 (元组或字典)
        返回: 影响的行数

        示例:
            # 插入数据
            row_count = db.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                ('John Doe', 'john@example.com')
            )
            print(f"插入了 {row_count} 行")

            # 更新数据
            row_count = db.execute(
                "UPDATE users SET status = %s WHERE id = %s",
                ('inactive', 5)
            )

            # 删除数据
            row_count = db.execute(
                "DELETE FROM users WHERE last_login < %s",
                ('2023-01-01',)
            )
        """
        start_time = time.time()
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                conn.commit()
                elapsed = time.time() - start_time
                print(f"[Execute] 执行SQL: {sql[:50]}... | 耗时: {elapsed:.4f}s | 影响行数: {affected_rows}")
                return affected_rows

    def execute_many(self, sql, params_list):
        """
        批量执行SQL语句

        参数:
            sql: SQL语句
            params_list: 参数列表
        返回: 影响的行数

        示例:
            # 批量插入数据
            users = [
                ('Alice', 'alice@example.com'),
                ('Bob', 'bob@example.com'),
                ('Charlie', 'charlie@example.com')
            ]
            row_count = db.execute_many(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                users
            )
            print(f"批量插入了 {row_count} 行")
        """
        start_time = time.time()
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                conn.commit()
                elapsed = time.time() - start_time
                print(f"[ExecuteMany] 批量执行SQL: {sql[:50]}... | 耗时: {elapsed:.4f}s | 影响行数: {affected_rows}")
                return affected_rows

    def get_one(self, sql, params=None):
        """
        获取单条记录

        参数:
            sql: SQL查询语句
            params: SQL参数
        返回: 单条记录 (字典) 或 None

        示例:
            # 获取单个用户
            user = db.get_one("SELECT * FROM users WHERE id = %s", (1,))
            if user:
                print(f"用户: {user['name']}")
        """
        start_time = time.time()
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()
                elapsed = time.time() - start_time
                print(f"[GetOne] 获取单条记录: {sql[:50]}... | 耗时: {elapsed:.4f}s")
                return result

    def scalar(self, sql, params=None):
        """
        获取单个值

        参数:
            sql: SQL查询语句
            params: SQL参数
        返回: 单个值 或 None

        示例:
            # 获取用户数量
            count = db.scalar("SELECT COUNT(*) FROM users")
            print(f"用户总数: {count}")
        """
        result = self.get_one(sql, params)
        return list(result.values())[0] if result else None

    def transaction(self):
        """
        获取事务上下文管理器

        返回: 事务上下文对象

        示例:
            # 使用事务执行多个操作
            with db.transaction() as conn:
                try:
                    # 在事务中执行操作
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                            (100, 1)
                        )
                        cursor.execute(
                            "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                            (100, 2)
                        )
                    print("事务操作成功")
                except Exception as e:
                    print("事务失败:", str(e))
                    raise
        """
        return TransactionContext(self.pool)

    def close_pool(self):
        """
        关闭连接池

        示例:
            # 程序结束时关闭连接池
            db.close_pool()
            print("数据库连接池已关闭")
        """
        self.pool.close()
        print("[MySQLHelper] 数据库连接池已关闭")


class TransactionContext:
    """
    事务上下文管理器
    """

    def __init__(self, pool):
        self.pool = pool
        self.conn = None

    def __enter__(self):
        self.conn = self.pool.connection()
        self.conn.begin()
        print("[Transaction] 事务开始")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
            print("[Transaction] 事务提交成功")
        else:
            self.conn.rollback()
            print(f"[Transaction] 事务回滚 (原因: {exc_val})")
        self.conn.close()


# 示例使用
# if __name__ == "__main__":
#     # 创建MySQL助手实例 (使用示例配置)
#     db = MySQLHelper(
#         host='localhost',
#         port=3306,
#         user='your_username',
#         password='your_password',
#         database='your_database',
#         pool_size=3
#     )
#
#     # 1. 查询示例
#     users = db.query("SELECT * FROM users LIMIT 5")
#     print("前5个用户:", users)
#
#     # 2. 获取单个用户示例
#     user = db.get_one("SELECT * FROM users WHERE id = %s", (1,))
#     if user:
#         print("用户ID=1:", user)
#
#     # 3. 获取标量值示例
#     user_count = db.scalar("SELECT COUNT(*) FROM users")
#     print(f"用户总数: {user_count}")
#
#     # 4. 执行单条SQL示例
#     # 创建测试表
#     create_table_sql = """
#     CREATE TABLE IF NOT EXISTS test_table (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         name VARCHAR(50) NOT NULL,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     )
#     """
#     db.execute(create_table_sql)
#
#     # 插入数据
#     new_id = db.execute(
#         "INSERT INTO test_table (name) VALUES (%s)",
#         ('测试用户',)
#     )
#     print(f"插入数据，影响行数: {new_id}")
#
#     # 5. 批量执行示例
#     test_data = [
#         ('批量用户1',),
#         ('批量用户2',),
#         ('批量用户3',)
#     ]
#     affected_rows = db.execute_many(
#         "INSERT INTO test_table (name) VALUES (%s)",
#         test_data
#     )
#     print(f"批量插入，影响行数: {affected_rows}")
#
#     # 6. 事务处理示例
#     try:
#         with db.transaction() as conn:
#             # 在事务中执行多个操作
#             with conn.cursor() as cursor:
#                 cursor.execute(
#                     "UPDATE test_table SET name = %s WHERE id = %s",
#                     ('更新后的名称', new_id)
#                 )
#                 cursor.execute(
#                     "INSERT INTO test_table (name) VALUES (%s)",
#                     ('事务中创建的用户',)
#                 )
#             print("事务操作成功")
#     except Exception as e:
#         print("事务执行失败:", str(e))
#
#     # 验证事务结果
#     updated_user = db.get_one("SELECT * FROM test_table WHERE id = %s", (new_id,))
#     print("更新后的用户:", updated_user)
#
#     # 清理测试表
#     db.execute("DROP TABLE IF EXISTS test_table")
#
#     # 关闭连接池
#     db.close_pool()