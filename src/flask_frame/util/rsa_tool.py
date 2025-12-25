import os

from rsa import common, transform, core, PrivateKey, PublicKey

from ..api.exception import ResourceError

# 加载公钥和私钥，异常时抛出业务错误
try:
    current_path = os.path.abspath(__file__)
    grader_father = os.path.abspath(os.path.dirname(current_path) + os.path.sep + "..")
    # 加载公钥文件
    pubkey = PublicKey.load_pkcs1(open("resource/public.pem").read())
    # 加载私钥文件
    privkey = PrivateKey.load_pkcs1(open("resource/private.pem").read())
except:
    raise ResourceError("证书文件路径错误！")


def _pad_for_encryption(message, target_length):
    """
    加密填充，确保消息长度符合要求（PKCS#1 v1.5填充）
    :param message: 待加密的字节串
    :param target_length: 填充后目标长度（字节数，通常为密钥长度）
    :return: 填充后的字节串
    """
    max_msglength = target_length - 11
    msglength = len(message)
    if msglength > max_msglength:
        raise OverflowError(
            "%i bytes needed for message, but there is only"
            " space for %i" % (msglength, max_msglength)
        )
    padding = b""
    padding_length = target_length - msglength - 3

    while len(padding) < padding_length:
        needed_bytes = padding_length - len(padding)
        new_padding = os.urandom(needed_bytes + 5)
        new_padding = new_padding.replace(b"\x00", b"")
        padding = padding + new_padding[:needed_bytes]
    assert len(padding) == padding_length
    return b"".join([b"\x00\x02", padding, b"\x00", message])


def decrypt(data: bytes, d, n):
    """
    解密函数，返回解密后的原始数据
    :param data: 加密后的字节串
    :param d: 私钥或公钥的d参数
    :param n: 公钥或私钥的n参数
    :return: 解密后的字节串
    """
    num = transform.bytes2int(data)
    decrypto = core.decrypt_int(num, d, n)
    out = transform.int2bytes(decrypto)
    sep_idx = out.index(b"\x00", 2)
    out = out[sep_idx + 1:]
    return out


def encrypt(data: bytes, d, n):
    """
    加密函数，返回加密后的数据
    :param data: 待加密的字节串
    :param d: 私钥或公钥的d参数
    :param n: 公钥或私钥的n参数
    :return: 加密后的字节串
    """
    keylength = common.byte_size(n)
    padded = _pad_for_encryption(data, keylength)
    num = transform.bytes2int(padded)
    decrypto = core.encrypt_int(num, d, n)
    out = transform.int2bytes(decrypto)
    return out


# 公钥加密
def pub_encrypt(data2b):
    """
    使用公钥加密
    :param data2b: 待加密的字节串
    :return: 加密后的字节串
    """
    return encrypt(data2b, pubkey.e, pubkey.n)


# 公钥解密
def pub_decrypt(edata):
    """
    使用公钥解密
    :param edata: 加密后的字节串
    :return: 解密后的字节串
    """
    return decrypt(edata, pubkey.e, pubkey.n)


# 私钥加密
def pri_encrypt(data2b):
    """
    使用私钥加密
    :param data2b: 待加密的字节串
    :return: 加密后的字节串
    """
    return encrypt(data2b, privkey.d, privkey.n)


# 私钥解密
def pri_decrypt(edata):
    """
    使用私钥解密
    :param edata: 加密后的字节串
    :return: 解密后的字节串
    """
    return decrypt(edata, privkey.d, privkey.n)


if __name__ == '__main__':
    # 测试代码：加载公钥和私钥
    pubkey = PublicKey.load_pkcs1(open("../resource/public.pem").read())
    privkey = PrivateKey.load_pkcs1(open("../resource/private.pem").read())

    # 示例数据加密解密流程
    s = """{"machineInfo": "C8-5B-76-F4-54-66,00-28-F8-68-92-97,02-28-F8-68-92-96,00-50-56-C0-00-01,00-50-56-C0-00-08,00-FF-3B-1A-15-A2,00-28-F8-68-92-96,00-28-F8-68-92-9A", "registTime": "2019-11-06", "dueTime": "2020-11-11", "customName": "\u6d4b\u8bd5\u516c\u53f8", "productName": "\u4f1a\u8bae\u7cfb\u7edf\uff08z_meeting\uff09"}"""
    print(len(s))
    # 私钥加密
    edata = encrypt(s.encode("utf-8"), privkey.d, privkey.n)
    print(edata)
    # 公钥解密
    ddata = decrypt(edata, pubkey.e, pubkey.n)
    ddata = ddata.decode('utf8')
    print(ddata)
