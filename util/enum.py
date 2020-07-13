class EnumMeta(type):
    """自定义枚举元类"""

    def __new__(mcs, name, bases, dict):
        print("dict:" + str(dict))

        scope = []
        for key, value in dict.items():
            if not key.startswith("_"):
                scope.append(value)

        return super(EnumMeta, mcs).__new__(mcs, name, bases, {**dict, "scope": scope})
