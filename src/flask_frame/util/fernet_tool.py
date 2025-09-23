from cryptography.fernet import Fernet
import base64
import hashlib


def _get_fernet_key(key: str = None) -> str:
    """
    获取用于Fernet加解密的密钥
    优先使用参数key，其次ENCRYPTION_KEY，最后PPRODUCT_KEY
    自动将普通字符串转换为合法Fernet密钥
    """
    from flask import current_app
    if key is not None:
        raw_key = key
    else:
        raw_key = current_app.config.get("ENCRYPTION_KEY")
        if not raw_key:
            raw_key = current_app.config.get("PRODUCT_KEY")
    # Fernet key 必须为32字节的url-safe base64编码
    if isinstance(raw_key, str):
        # 通过sha256哈希后base64编码，确保长度和格式
        hashed = hashlib.sha256(raw_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(hashed)
        return fernet_key
    return raw_key


def encrypt(data: str, key: str = None) -> str:
    """
    使用Fernet进行加密
    :param data: 待加密的字符串
    :param key: base64编码的Fernet密钥字符串，为空时自动从flask配置获取
    :return: 加密后的字符串（base64编码）
    """
    key = _get_fernet_key(key)
    f = Fernet(key)
    token = f.encrypt(data.encode("utf-8"))
    return token.decode("utf-8")


def decrypt(token: str, key: str = None) -> str:
    """
    使用Fernet进行解密
    :param token: 加密后的字符串（base64编码）
    :param key: base64编码的Fernet密钥字符串，为空时自动从flask配置获取
    :return: 解密后的字符串
    """
    key = _get_fernet_key(key)
    f = Fernet(key)
    data = f.decrypt(token.encode("utf-8"))
    return data.decode("utf-8")


if __name__ == "__main__":
    # 测试加解密功能
    import os

    test_key = "digital_sign"
    test_data = ""
    print("原文:", test_data)
    enc = encrypt(test_data, test_key)
    print("加密:", enc)
    dec = decrypt(enc, test_key)
    print("解密:", dec)
