from functools import wraps


def get_enum_values(enum):
    """
    获取枚举类型的所有值

    该函数接收一个枚举类型（例如Python的Enum类），并返回其所有成员的值列表。
    适用于将枚举类型转换为前端可以使用的选项列表。

    Args:
        enum: 枚举类，例如通过enum.Enum定义的类

    Returns:
        list: 包含所有枚举值的列表

    Example:
        >>> from enum import Enum
        >>> class Color(Enum):
        ...     RED = 'red'
        ...     GREEN = 'green'
        ...     BLUE = 'blue'
        >>> get_enum_values(Color)
        ['red', 'green', 'blue']
    """
    print("Got:", enum)  # 调试信息，输出接收到的枚举类型
    return [e.value for e in enum]  # 使用列表推导式获取所有枚举成员的值


def auto_commit(session):
    """
    创建一个自动提交和回滚数据库会话的装饰器

    该装饰器封装了数据库事务的提交和回滚逻辑，使数据库操作函数更加简洁。
    被装饰的函数执行成功后会自动提交事务，发生异常时会自动回滚事务。

    Args:
        session: SQLAlchemy数据库会话对象

    Returns:
        function: 装饰器函数

    Example:
        >>> @auto_commit(db.session)
        >>> def create_user(name, email):
        ...     user = User(name=name, email=email)
        ...     db.session.add(user)
        ...     return user
    """

    def decorator(f):
        """
        装饰器函数，接收要被装饰的函数

        Args:
            f: 要被装饰的函数，通常是执行数据库操作的函数

        Returns:
            function: 装饰后的函数
        """

        @wraps(f)  # 保留原函数的元数据（如函数名、文档字符串等）
        def decorated_function(*args, **kwargs):
            """
            装饰后的函数，添加了事务管理功能

            Args:
                *args: 原函数的位置参数
                **kwargs: 原函数的关键字参数

            Returns:
                任何类型: 原函数的返回值

            Raises:
                Exception: 原函数抛出的任何异常，在抛出前会回滚事务
            """
            result = None

            try:
                # 执行原函数
                result = f(*args, **kwargs)
                # 提交事务
                session.commit()
            except Exception as err:
                # 发生异常时回滚事务
                session.rollback()
                # 重新抛出异常，便于上层捕获和处理
                raise err

            return result

        return decorated_function

    return decorator


# 当结果为result对象列表时，result有key()方法
def result_to_dict(db_result):
    """将数据库查询结果转换为字典列表

    Args:
        db_result (_engine.Result):  数据库查询结果对象，通常是SQLAlchemy的查询结果
    """
    result = []

    column_names = db_result.keys()  # 获取列名
    res_group = db_result.fetchall()

    # 将查询结果转换为字典列表（可JSON序列化）
    for row in res_group:
        record = {}
        for i, column in enumerate(column_names):
            record[column] = row[i]
        result.append(record)
    
    # 返回
    return result
