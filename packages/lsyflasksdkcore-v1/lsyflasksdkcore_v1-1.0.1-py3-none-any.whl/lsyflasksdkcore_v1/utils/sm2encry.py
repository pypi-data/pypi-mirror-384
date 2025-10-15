import base64
from base64 import b64encode, b64decode

from gmssl import sm2


class Sm2Encrypt(object):
    def __init__(self, public_key: str, private_key: str):
        self.sm2_crypt = sm2.CryptSM2(public_key=public_key, private_key=private_key)

    def encrypt(self, info):
        """
        加密
        :param info: str
        :return: base64 str
        """
        encode_info = self.sm2_crypt.encrypt(info.encode(encoding="utf-8"))
        encode_info = b64encode(encode_info).decode()  # 将二进制bytes通过base64编码
        return encode_info

    def decrypt(self, info):
        """
        解密
        :param info: bese64 str
        :return: str
        """
        decode_info = b64decode(info.encode())  # 通过base64解码成二进制bytes
        decode_info = self.sm2_crypt.decrypt(decode_info).decode(encoding="utf-8")
        return decode_info


def base64ToStr(s):
    """
    将base64字符串转换为字符串
    :param s:
    :return:
    """
    strDecode = base64.b64decode(bytes(s, encoding='utf-8'))
    return str(strDecode, encoding='utf-8')


def hex_to_base64(payload_hex2):
    """
    将16进制转换为base64
    :param payload_hex2: hex
    :return:
    """
    bytes_out = bytes.fromhex(payload_hex2)
    str_out = base64.b64encode(bytes_out)
    return str_out


def base64_to_hex(payload_base64):
    """
    将base64转换为hex
    :param payload_base64:
    :return:
    """
    bytes_out = base64.b64decode(payload_base64)
    str_out = bytes_out.hex()
    return str_out


if __name__ == "__main__":
    origin_pwd = '123456'

    # sm2的公私钥
    private_key = 'f07cd81cacc728c562ff18eb51563574af35b9c95877a05c04a994ebe764c180'
    public_key = '95779161c06dd4ccf782da9180fd9bfd0b40160b9122706a9afac117e3a53747514e985ac02763e8ba3ea8698e4bef45f113777bd636b96fa6ba765b3d201512'

    sm2 = Sm2Encrypt(public_key, private_key)

    encrypy_pwd = sm2.encrypt(origin_pwd)
    print(f"加密的密码：{encrypy_pwd}")
    decrypt_pwd = sm2.decrypt(encrypy_pwd)
    print(f"解密的密码：{decrypt_pwd}")

    con = '3ff1effce19dd22d107840e272fe7bb688790fa93bf470cf0c8a3dfe39cf3f0159c8a51c458e29d71d1d5c320bf6e36f23efa7c8f860341a6233bee8076bf633575c9e94c3d27daa55b93eb19ae4c613a1b3453959db78b5e751e3b204642b9e610a54be65'
    hex_con = hex_to_base64(con)
    print(f"hex_con:{hex_con}")

    str_hex_con = hex_con.decode("utf-8")
    a = sm2.decrypt(str_hex_con)
    print(f"解密后：{a}")
