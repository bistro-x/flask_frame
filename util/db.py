from functools import wraps


def get_enum_values(enum):
    """
    return the enum value
    :param enum:
    :return:
    """
    print('Got:', enum)
    return [e.value for e in enum]


def auto_commit(session):
    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = None

            try:
                result = f(*args, **kwargs)
                session.commit()
            except Exception as err:
                session.rollback()
                raise err

            return result

        return decorated_function

    return decorator
