"""Ezviz image decryption helper."""
from __future__ import annotations

import logging
from typing import List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

_LOGGER = logging.getLogger(__name__)


def decrypt_ezviz_image_bytes(
    data: bytes,
    verification_codes: List[str],
) -> bytes:
    """Decrypt Ezviz encrypted image bytes using candidate verification codes."""
    if not data or data.startswith(b"\xff\xd8"):
        # 已经是标准解密后的 JPEG 文件头，直接返回
        return data

    for code in verification_codes:
        code = code.strip()
        if not code:
            continue

        # 将验证码使用 \0 补齐为 16 字节密钥
        key = code.encode("utf-8").ljust(16, b"\x00")[:16]

        try:
            # 1. 尝试 AES-128-ECB 全文解密
            cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(data) + decryptor.finalize()

            if decrypted.startswith(b"\xff\xd8"):
                _LOGGER.info("Successfully decrypted image with verification code: %s***", code[:2])
                return decrypted

            # 2. 尝试保留前 16 字节头部，解密后段数据
            if len(data) > 16:
                header = data[:16]
                payload = data[16:]
                decryptor = cipher.decryptor()
                decrypted = header + decryptor.update(payload) + decryptor.finalize()
                if decrypted.startswith(b"\xff\xd8"):
                    _LOGGER.info("Successfully decrypted image (offset header) with code: %s***", code[:2])
                    return decrypted

        except Exception as err:
            _LOGGER.debug("Decryption attempt with code %s failed: %s", code, err)

    _LOGGER.warning("Could not decrypt image with provided verification codes, saving raw data.")
    return data
