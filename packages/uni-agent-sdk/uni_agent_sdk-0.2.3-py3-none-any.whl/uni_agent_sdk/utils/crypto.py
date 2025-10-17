"""加密和签名工具"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Union


def sign_data(data: Union[str, Dict[str, Any]], secret: str) -> str:
    """对数据进行HMAC-SHA256签名

    Args:
        data: 要签名的数据，可以是字符串或字典
        secret: 签名密钥

    Returns:
        十六进制签名字符串
    """
    if isinstance(data, dict):
        # 字典需要序列化为JSON字符串
        data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        data_str = str(data)

    signature = hmac.new(
        secret.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return signature


def verify_signature(
    data: Union[str, Dict[str, Any]], signature: str, secret: str
) -> bool:
    """验证签名

    Args:
        data: 原始数据
        signature: 要验证的签名
        secret: 签名密钥

    Returns:
        签名是否有效
    """
    expected_signature = sign_data(data, secret)
    return hmac.compare_digest(signature, expected_signature)


def sign_with_timestamp(
    data: Union[str, Dict[str, Any]], secret: str
) -> Dict[str, str]:
    """带时间戳的签名

    Args:
        data: 要签名的数据
        secret: 签名密钥

    Returns:
        包含签名和时间戳的字典
    """
    timestamp = str(int(time.time()))

    if isinstance(data, dict):
        data_with_timestamp = {**data, "timestamp": timestamp}
    else:
        data_with_timestamp = {"data": str(data), "timestamp": timestamp}

    signature = sign_data(data_with_timestamp, secret)

    return {"signature": signature, "timestamp": timestamp}


def verify_signature_with_timestamp(
    data: Union[str, Dict[str, Any]],
    signature: str,
    timestamp: str,
    secret: str,
    expire_time: int = 300,
) -> bool:
    """验证带时间戳的签名

    Args:
        data: 原始数据
        signature: 要验证的签名
        timestamp: 时间戳
        secret: 签名密钥
        expire_time: 过期时间（秒），默认5分钟

    Returns:
        签名是否有效且未过期
    """
    try:
        # 检查时间戳是否过期
        current_time = int(time.time())
        timestamp_int = int(timestamp)

        if current_time - timestamp_int > expire_time:
            return False

        # 重构带时间戳的数据
        if isinstance(data, dict):
            data_with_timestamp = {**data, "timestamp": timestamp}
        else:
            data_with_timestamp = {"data": str(data), "timestamp": timestamp}

        # 验证签名
        return verify_signature(data_with_timestamp, signature, secret)

    except (ValueError, TypeError):
        return False


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """计算字符串哈希值

    Args:
        text: 要哈希的字符串
        algorithm: 哈希算法，支持 md5, sha1, sha256, sha512

    Returns:
        十六进制哈希值
    """
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha1":
        hasher = hashlib.sha1()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")

    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def generate_request_id() -> str:
    """生成请求ID

    Returns:
        唯一的请求ID
    """
    import uuid

    return str(uuid.uuid4()).replace("-", "")


def mask_sensitive_data(
    data: str, start: int = 4, end: int = 4, mask_char: str = "*"
) -> str:
    """遮蔽敏感数据

    Args:
        data: 敏感数据字符串
        start: 开始保留的字符数
        end: 结尾保留的字符数
        mask_char: 遮蔽字符

    Returns:
        遮蔽后的字符串
    """
    if len(data) <= start + end:
        return mask_char * len(data)

    return data[:start] + mask_char * (len(data) - start - end) + data[-end:]
