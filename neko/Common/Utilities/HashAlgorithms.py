# -*- encoding: UTF-8 -*-


import hashlib


def MD5(data: bytes or memoryview) -> str:
    md5 = hashlib.md5()
    md5.update(data)

    return md5.hexdigest().upper()


def SHA256(data: bytes or memoryview) -> str:
    sha256 = hashlib.sha256()
    sha256.update(data)

    return sha256.hexdigest().upper()
