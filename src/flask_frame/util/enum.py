class EnumMeta(type):
    """自定义枚举元类"""

    def __new__(mcs, name, bases, dict):
        # 打印类属性字典，调试用
        print("dict:" + str(dict))

        scope = []
        # 收集所有非私有属性的值到scope列表
        for key, value in dict.items():
            if not key.startswith("_"):
                scope.append(value)

        # 创建新类，并添加scope属性
        return super(EnumMeta, mcs).__new__(mcs, name, bases, {**dict, "scope": scope})
